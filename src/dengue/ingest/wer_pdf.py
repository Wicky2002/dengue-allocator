"""Parse Epidemiology Unit Weekly Epidemiological Report (WER) PDFs.

The WER (https://www.epid.gov.lk/weekly-epidemiological-report/) is the
authoritative source for notified dengue cases in Sri Lanka. Each issue carries
"Table 1: Distribution of Notified Diseases reported by Medical Officers of
Health", a dense grid confirmed unchanged across real issues from 2022, 2023
and 2026:

* **Rows are diseases**, each as an adjacent pair -- a "B" row (year-to-date
  cumulative) followed by an "A" row (current week). Dengue Fever is one of
  ~15 disease blocks; its row position varies by issue (diseases are added
  over time), so it is found by name, never by a hardcoded index.
* **Columns are the 26 RDHS reporting divisions** (25 districts, with
  Kalmunai listed separately from Ampara) plus a "SRILANKA" total column, in
  a header row that is the table's **last** row, not its first.
* **Every cell's text is reversed, one character per line.** The table
  renders district/disease names and every digit-run rotated; pdfplumber
  extracts each cell as e.g. ``"y\\ns\\no\\nrp\\ne\\nL"`` for "Leprosy" or
  ``"8\\n3\\n1\\n1"`` for the number 1138. :func:`_decode_wer_cell` undoes
  this (strip newlines, reverse the string) -- confirmed exactly on real
  extracted cells, not assumed.
* **Table 1's own printed date range is the authoritative week**, not the
  WER issue's cover date shown on the report index -- the two differ by one
  week (the issue is published the week after the week it reports on).
  :func:`_extract_report_week` reads it directly from the page text.

Why the parser was rewritten mid-project: an earlier version assumed the
simpler, opposite layout (rows=divisions, columns=diseases, no rotation) --
plausible from the WER's own prose description, but wrong for every real PDF
checked. It had only ever been exercised against a synthetic fixture that
encoded the same wrong assumption, so the mismatch went undetected until
real PDFs were downloaded and parsed for the first time.

Validation
----------
Every parsed week is checked with :func:`validate_against_national_total`: the
26 division rows must sum to the printed national total within 1%. Weeks that
fail are flagged and, by default, **excluded** rather than silently accepted.

If epid.gov.lk is unreachable the parser is still fully exercised by
``tests/test_wer_pdf.py`` against a synthetic fixture shaped like the real
table (rotated cell text included). No case data is ever fabricated to stand
in for a failed download.

Licence
-------
Sri Lanka Ministry of Health / Epidemiology Unit publication. Public health
information published for public use; cite the Epidemiology Unit.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from dengue import config
from dengue.utils.io import IngestError, download_binary, http_get
from dengue.utils.logging import get_logger

log = get_logger(__name__)

#: Tolerance for the district-sum vs national-total cross-check.
NATIONAL_TOTAL_TOLERANCE = 0.01

_NUMBER = re.compile(r"^-?[\d,]+$")

#: The WER index page (https://www.epid.gov.lk/weekly-epidemiological-report/)
#: renders every issue back to ~2007 in one static, unpaginated HTML page --
#: confirmed live: 1,014 <li class="product"> entries, zero unparseable dates.
#: No JS, no login. Each entry carries a title, a "Week NN" label, a printed
#: date range, and a direct PDF download link.
_INDEX_PATH = "/weekly-epidemiological-report/"

#: The index page's own "Week NN" / date range is the *issue's* Saturday-to-
#: Friday cover date, not the ISO week its data covers -- those are two
#: different things a full week apart in practice (see _extract_report_week,
#: which reads the authoritative date directly off Table 1 inside the PDF).
#: This offset only produces a same-issue-cycle approximation, good enough
#: for cache filenames and the `since` cutoff in download_recent -- it is
#: never used as the final label on parsed data.
_MIDPOINT_OFFSET_DAYS = 3

_DATE_RANGE = re.compile(r"(\d{4})\.(\d{2})\.(\d{2})\s*-\s*(\d{4})\.(\d{2})\.(\d{2})")


@dataclass(frozen=True)
class ReportListing:
    """One discovered WER issue: which week it covers and where to fetch it."""

    iso_week: pd.Period
    url: str
    title: str


@dataclass(frozen=True)
class WeekValidation:
    """Outcome of the national-total cross-check for one week.

    Attributes
    ----------
    iso_week:
        The week validated.
    district_sum:
        Sum over the 26 RDHS division rows.
    national_total:
        The total printed in the report.
    relative_error:
        ``|district_sum - national_total| / national_total``.
    passed:
        Whether ``relative_error`` is within
        :data:`NATIONAL_TOTAL_TOLERANCE`.
    n_rows:
        Number of division rows parsed (should be 26).
    """

    iso_week: pd.Period
    district_sum: int
    national_total: int | None
    relative_error: float | None
    passed: bool
    n_rows: int

    def describe(self) -> str:
        # relative_error is None both when no total was printed and when the
        # printed total was zero, so branch on it rather than on national_total.
        if self.relative_error is None:
            return (
                f"{self.iso_week}: no usable national total "
                f"(printed={self.national_total}); district_sum={self.district_sum} "
                f"across {self.n_rows} rows (UNVERIFIED)"
            )
        status = "OK" if self.passed else "FAIL"
        return (
            f"{self.iso_week}: {status}  district_sum={self.district_sum}  "
            f"national_total={self.national_total}  "
            f"rel_err={self.relative_error:.4f}  rows={self.n_rows}"
        )


def _to_int(token: Any) -> int | None:
    """Parse a table cell to int, returning None for blanks and non-numerics."""
    if token is None:
        return None
    text = str(token).strip().replace(",", "").replace(" ", "")
    if not text or text in {"-", "--", "*", "NA", "N/A"}:
        return None
    if not _NUMBER.match(text.replace(",", "")):
        return None
    try:
        return int(text)
    except ValueError:
        return None


#: Minimum shape to consider a table "Table 1" rather than one of the WER's
#: several small ones (a water-quality-surveillance table came out 30x4 in
#: testing, a vaccine-preventable-disease table 17x15; Table 1 itself is
#: comfortably larger on both axes in every issue checked).
_MIN_TABLE_1_ROWS = 20
_MIN_TABLE_1_COLS = 20

#: Row-2 label marking the current-week ("A") half of a disease's row pair.
#: The cumulative half is unlabelled here (any other non-empty label, "B" in
#: the common case) -- checking for "A" specifically is more robust than
#: checking the label is exactly "B", since a couple of rows use non-A/B
#: markers for unrelated metadata (e.g. "T*"/"C**" for the WRCD row).
_WEEKLY_ROW_LABEL = re.compile(r"^a\*?$", re.IGNORECASE)


def _decode_wer_cell(cell: Any) -> str:
    """Undo Table 1's rotated-text rendering.

    Every cell -- district names, disease names, digit runs -- is extracted
    by pdfplumber as one character (occasionally two, when two glyphs land on
    the same line) per line, in reverse reading order. Stripping the
    newlines and reversing the resulting string recovers the true text.
    Confirmed exactly against real extracted cells: ``"8\\n3\\n1\\n1"`` ->
    ``"1138"``, ``"y\\ns\\no\\nrp\\ne\\nL"`` -> ``"Leprosy"``,
    ``"o\\nb\\nm\\no\\nlo\\nC"`` -> ``"Colombo"``.
    """
    if not cell:
        return ""
    return str(cell).replace("\n", "")[::-1]


def _find_dengue_row_pair(table: list[list[Any]]) -> tuple[int, int] | None:
    """Locate the (cumulative, weekly) row-index pair for Dengue Fever.

    Every disease occupies two adjacent rows: the first carries the decoded
    disease name in column 0 (cumulative count in the data columns), the
    second has an empty name cell and label "A" (current-week count). Found
    by name -- never a hardcoded row index -- because the row position
    varies by issue as diseases are added over the years (confirmed: row 24
    in a 2022/2023 issue, row 28 in a 2026 issue).
    """
    for i in range(len(table) - 1):
        row = table[i]
        if not row or not row[0]:
            continue
        name = _decode_wer_cell(row[0]).replace(" ", "").lower()
        if name != "denguefever":
            continue
        next_row = table[i + 1]
        next_label = _decode_wer_cell(next_row[1]) if len(next_row) > 1 else ""
        if _WEEKLY_ROW_LABEL.match(next_label):
            return i, i + 1
        log.warning("wer: found a 'Dengue Fever' row at %d but its pair isn't labelled 'A'", i)
        return i, i + 1  # still usable -- most issues label it plainly "A"
    return None


def _find_district_columns(header_row: list[Any]) -> tuple[dict[int, str], int | None]:
    """Map column index -> district_id from Table 1's header row, plus the
    index of the "SRILANKA" total column.

    The header is the table's **last** row (confirmed on every real issue
    checked), not its first -- Table 1 has no separate header at the top;
    column identity is only ever printed once, after all the data rows.
    """
    columns: dict[int, str] = {}
    total_index: int | None = None
    # Columns 0 (row-label) and 1 (A/B indicator) never carry a district name;
    # skipping them avoids "RDHS" itself being mis-normalised.
    for idx in range(2, len(header_row)):
        name = _decode_wer_cell(header_row[idx]).replace(" ", "").lower()
        if not name:
            continue
        if name == "srilanka":
            total_index = idx
            continue
        district_id = config.normalise_district(name, strict=False)
        if district_id is not None:
            columns[idx] = district_id
    return columns, total_index


def parse_table(table: list[list[Any]]) -> tuple[dict[str, int], int | None]:
    """Parse one extracted WER "Table 1" into division counts and the national total.

    Parameters
    ----------
    table:
        A table as returned by ``pdfplumber``'s ``extract_table()`` with
        ``table_settings={"vertical_strategy": "lines", "horizontal_strategy":
        "lines"}`` (the default word/line-gap strategy fragments this table's
        thin, colour-filled cell borders into the wrong grid).

    Returns
    -------
    tuple
        ``(counts, national_total)`` where ``counts`` maps ``district_id`` to
        the current-week count (Kalmunai already folded into Ampara), and
        ``national_total`` is the printed all-island figure or ``None``.
    """
    if len(table) < _MIN_TABLE_1_ROWS or (table and len(table[0]) < _MIN_TABLE_1_COLS):
        return {}, None

    row_pair = _find_dengue_row_pair(table)
    if row_pair is None:
        return {}, None
    _cumulative_row, weekly_row_idx = row_pair
    weekly_row = table[weekly_row_idx]

    header_row = table[-1]
    columns, total_index = _find_district_columns(header_row)
    if not columns:
        return {}, None

    counts: dict[str, int] = {}
    for idx, district_id in columns.items():
        if idx >= len(weekly_row):
            continue
        value = _to_int(_decode_wer_cell(weekly_row[idx]))
        if value is None:
            continue
        # Kalmunai folds into Ampara: accumulate rather than overwrite.
        counts[district_id] = counts.get(district_id, 0) + value

    national_total = None
    if total_index is not None and total_index < len(weekly_row):
        national_total = _to_int(_decode_wer_cell(weekly_row[total_index]))

    return counts, national_total


def validate_against_national_total(
    counts: dict[str, int],
    national_total: int | None,
    iso_week: pd.Period,
    *,
    n_rows: int | None = None,
    tolerance: float = NATIONAL_TOTAL_TOLERANCE,
) -> WeekValidation:
    """Check that district rows sum to the reported national total within 1%.

    This is the parser's primary correctness guard. It catches the failure modes
    that matter: reading the cumulative ``B`` column instead of the weekly ``A``
    column, dropping rows when a page break splits the table, and mis-aligned
    columns after a layout change upstream.

    Parameters
    ----------
    counts:
        ``district_id -> weekly count``, as returned by :func:`parse_table`.
    national_total:
        The all-island total printed in the report, or ``None`` if absent.
    iso_week:
        Week being validated, for the log message.
    n_rows:
        Number of division rows parsed; defaults to ``len(counts)``.
    tolerance:
        Maximum acceptable relative error. Defaults to 1%.

    Returns
    -------
    WeekValidation
        Structured outcome. ``passed`` is False when the check fails, and also
        when no national total was printed and therefore nothing could be
        verified.
    """
    district_sum = int(sum(counts.values()))
    n_rows = n_rows if n_rows is not None else len(counts)

    if national_total is None or national_total == 0:
        result = WeekValidation(iso_week, district_sum, national_total, None, False, n_rows)
        log.warning("wer: %s", result.describe())
        return result

    relative_error = abs(district_sum - national_total) / national_total
    passed = relative_error <= tolerance
    result = WeekValidation(iso_week, district_sum, national_total, relative_error, passed, n_rows)

    if passed:
        log.info("wer: %s", result.describe())
    else:
        log.error(
            "wer: %s -- district rows do not reconcile with the national total. "
            "Likely causes: the cumulative (B) column was read instead of the weekly (A) "
            "column, or rows were lost to a page break.",
            result.describe(),
        )
    return result


#: Table 1's own printed date range, e.g. "15th <dash> 21st June 2026 (25th
#: Week)" -- the dash renders as a mangled/unmatchable glyph in extracted
#: text in some fonts, so it is deliberately not part of the pattern.
_REPORT_WEEK = re.compile(
    r"Table\s*1\s*:.{0,120}?(\d{1,2})(?:st|nd|rd|th)\D{0,3}"
    r"(\d{1,2})(?:st|nd|rd|th)\s+([A-Za-z]+)\s+(\d{4})",
    re.IGNORECASE | re.DOTALL,
)


def _extract_report_week(page_text: str) -> pd.Period | None:
    """Read the week Table 1 itself claims to cover, straight off the page.

    This is deliberately **not** the WER issue's cover date (shown on the
    report index): the issue is published the week after the week its data
    covers, confirmed on real issues (Vol. 53 No. 26, cover "22nd-28th June
    2026", Table 1 date "15th-21st June 2026"). Using the cover date would
    silently mislabel every week by one.
    """
    match = _REPORT_WEEK.search(page_text)
    if match is None:
        return None
    start_day, end_day, month_name, year = match.groups()
    try:
        end_date = pd.Timestamp(f"{year}-{month_name}-{end_day}")
    except ValueError:
        return None
    start_day_int = int(start_day)
    if start_day_int > int(end_day):
        # The range crosses a month boundary (e.g. "28th - 03rd June"): the
        # start day belongs to the previous month.
        start_date = (end_date - pd.DateOffset(months=1)).replace(day=start_day_int)
    else:
        start_date = end_date.replace(day=start_day_int)
    return pd.Period(start_date, freq=config.WEEK_FREQ)


#: Table 1 is reliably found with an explicit lines-based grid strategy.
#: pdfplumber's default (gap/whitespace-based) strategy fragments this
#: table's thin, colour-filled cell borders into the wrong shape entirely --
#: confirmed by comparing both against a real issue.
_TABLE_SETTINGS = {"vertical_strategy": "lines", "horizontal_strategy": "lines"}


def extract_tables_from_pdf(path: Path) -> list[list[list[Any]]]:
    """Extract every table from a WER PDF using pdfplumber."""
    try:
        import pdfplumber
    except ImportError as exc:  # pragma: no cover - dependency is pinned
        raise IngestError("pdfplumber is required to parse WER PDFs") from exc

    tables: list[list[list[Any]]] = []
    with pdfplumber.open(path) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            for table in page.extract_tables(table_settings=_TABLE_SETTINGS):
                if table and len(table) > 3:
                    tables.append(table)
            log.debug("wer: page %d yielded %d tables", page_number, len(tables))
    return tables


def parse_pdf(
    path: Path, iso_week: pd.Period, *, strict: bool = True
) -> tuple[pd.DataFrame, WeekValidation]:
    """Parse one WER PDF into a district-week frame plus its validation result.

    Parameters
    ----------
    path:
        Local path to the PDF.
    iso_week:
        Fallback week label, used only if :func:`_extract_report_week` cannot
        find Table 1's own printed date range on the page (normally derived
        from the report index that linked to this PDF -- see
        :class:`ReportListing`). When the page's own date is found, it wins:
        it is the authoritative source, the index date is an approximation.
    strict:
        If True, raise on a failed national-total check. If False, return the
        frame with the failure recorded in the returned
        :class:`WeekValidation`, leaving the decision to the caller.

    Returns
    -------
    tuple
        ``(frame, validation)``. ``frame`` has columns ``district_id``,
        ``iso_week``, ``cases``.

    Raises
    ------
    IngestError
        If no dengue table can be located, or if ``strict`` and validation fails.
    """
    import pdfplumber

    with pdfplumber.open(path) as pdf:
        page_text = "\n".join(page.extract_text() or "" for page in pdf.pages)
    extracted_week = _extract_report_week(page_text)
    if extracted_week is not None and extracted_week != iso_week:
        log.info(
            "wer: %s's own Table 1 date (%s) overrides the caller-supplied week (%s)",
            path.name,
            extracted_week,
            iso_week,
        )
    resolved_week = extracted_week if extracted_week is not None else iso_week

    tables = extract_tables_from_pdf(path)
    if not tables:
        raise IngestError(f"No tables extracted from {path}")

    best_counts: dict[str, int] = {}
    best_total: int | None = None
    for table in tables:
        counts, total = parse_table(table)
        # The real Table 1 is the one covering the most districts.
        if len(counts) > len(best_counts):
            best_counts, best_total = counts, total

    if not best_counts:
        raise IngestError(
            f"Could not locate a dengue district table in {path}. "
            "The WER layout may have changed; inspect the PDF and update "
            "_find_dengue_row_pair() / _find_district_columns()."
        )

    if len(best_counts) < config.N_DISTRICTS:
        log.warning(
            "wer: parsed only %d of %d districts from %s",
            len(best_counts),
            config.N_DISTRICTS,
            path.name,
        )

    validation = validate_against_national_total(
        best_counts, best_total, resolved_week, n_rows=len(best_counts)
    )
    if strict and not validation.passed:
        raise IngestError(
            f"WER national-total validation failed for {resolved_week}: {validation.describe()}"
        )

    frame = pd.DataFrame(
        {
            "district_id": list(best_counts.keys()),
            "iso_week": resolved_week,
            "cases": list(best_counts.values()),
        }
    )
    return frame, validation


def download_wer_pdf(url: str, iso_week: pd.Period, *, refresh: bool = False) -> Path:
    """Download a WER PDF into ``data/raw/wer/``."""
    config.ensure_dirs()
    dest = config.RAW_WER / f"wer_{iso_week.start_time:%Y-%m-%d}.pdf"
    return download_binary(url, dest, refresh=refresh)


def discover_reports(html: str | None = None) -> list[ReportListing]:
    """Enumerate every WER issue linked from the report index.

    Parameters
    ----------
    html:
        Pre-fetched index page markup, for tests. When omitted, fetches
        ``config.EPID_BASE_URL`` + :data:`_INDEX_PATH` live.

    Returns
    -------
    list of ReportListing
        Sorted oldest to newest. Empty if the page's markup no longer matches
        the structure this was written against -- callers should treat an
        empty result as "index layout changed, needs investigation", not as
        "no reports exist".
    """
    from bs4 import BeautifulSoup

    if html is None:
        response = http_get(config.EPID_BASE_URL + _INDEX_PATH)
        html = response.text

    soup = BeautifulSoup(html, "html.parser")
    listings: list[ReportListing] = []

    for product in soup.select("li.product"):
        texts = [p.get_text(strip=True) for p in product.select(".product-name p")]
        link = product.select_one("a.btn")
        if link is None or not link.get("href", "").lower().endswith(".pdf"):
            continue

        match = next((m for t in texts if (m := _DATE_RANGE.search(t))), None)
        if match is None:
            continue

        start_year, start_month, start_day = (int(g) for g in match.groups()[:3])
        start = pd.Timestamp(start_year, start_month, start_day)
        iso_week = pd.Period(
            start + pd.Timedelta(days=_MIDPOINT_OFFSET_DAYS), freq=config.WEEK_FREQ
        )
        title = texts[0] if texts else ""
        listings.append(ReportListing(iso_week=iso_week, url=link["href"], title=title))

    listings.sort(key=lambda r: r.iso_week)
    log.info("wer: discovered %d issues on the report index", len(listings))
    return listings


def download_recent(
    since: pd.Period,
    *,
    refresh: bool = False,
    max_reports: int | None = None,
    polite_delay_seconds: float = 0.5,
) -> dict[pd.Period, Path]:
    """Discover and download every WER issue from ``since`` onward.

    Returns exactly the ``dict[iso_week, path]`` shape :func:`load` already
    accepts, so this is purely an additional layer above the existing
    download/parse pipeline -- ``load()`` itself is unchanged.

    A small delay between downloads is deliberate: this hits a live
    government site serving public-interest data, and there is no reason to
    hammer it just because a multi-year backfill involves many files.
    Already-downloaded PDFs are skipped via :func:`download_binary`'s own
    on-disk cache, so a repeated/resumed backfill makes zero redundant
    requests.
    """
    listings = [r for r in discover_reports() if r.iso_week >= since]
    if max_reports is not None:
        listings = listings[-max_reports:]

    log.info("wer: downloading %d issues from %s onward", len(listings), since)
    paths: dict[pd.Period, Path] = {}
    for listing in listings:
        dest = config.RAW_WER / f"wer_{listing.iso_week.start_time:%Y-%m-%d}.pdf"
        already_cached = dest.exists() and dest.stat().st_size > 0 and not refresh
        try:
            paths[listing.iso_week] = download_wer_pdf(
                listing.url, listing.iso_week, refresh=refresh
            )
        except IngestError as exc:
            log.error("wer: failed to download %s (%s): %s", listing.iso_week, listing.url, exc)
            continue
        if not already_cached:
            time.sleep(polite_delay_seconds)

    return paths


def load(pdf_paths: dict[pd.Period, Path], *, strict: bool = False) -> pd.DataFrame:
    """Parse several WER PDFs into one long district-week frame.

    Parameters
    ----------
    pdf_paths:
        ``iso_week -> local PDF path``.
    strict:
        Passed through to :func:`parse_pdf`. Defaults to False here so that one
        malformed issue does not abort a multi-year backfill; failures are
        logged and the affected weeks dropped.

    Returns
    -------
    pandas.DataFrame
        Columns ``district_id``, ``iso_week``, ``cases`` for every week that
        passed validation.
    """
    frames: list[pd.DataFrame] = []
    validations: list[WeekValidation] = []

    for iso_week, path in sorted(pdf_paths.items()):
        try:
            frame, validation = parse_pdf(path, iso_week, strict=strict)
        except IngestError as exc:
            log.error("wer: failed to parse %s for %s: %s", path.name, iso_week, exc)
            continue

        validations.append(validation)
        if validation.passed:
            frames.append(frame)
        else:
            log.warning("wer: excluding %s from the panel (validation failed)", iso_week)

    n_pass = sum(1 for v in validations if v.passed)
    log.info(
        "wer: parsed %d PDFs, %d weeks passed validation, %d excluded",
        len(pdf_paths),
        n_pass,
        len(validations) - n_pass,
    )

    if not frames:
        raise IngestError(
            "No WER weeks passed the national-total validation. Refusing to emit "
            "unverified case data."
        )

    combined = pd.concat(frames, ignore_index=True)
    log.info(
        "wer: combined rows=%d  districts=%d  weeks=[%s .. %s]  cases_total=%d",
        len(combined),
        combined["district_id"].nunique(),
        combined["iso_week"].min(),
        combined["iso_week"].max(),
        int(combined["cases"].sum()),
    )
    return combined


def main() -> None:  # pragma: no cover - CLI entry point
    config.ensure_dirs()
    since = pd.Period(config.WER_BACKFILL_START, freq=config.WEEK_FREQ)
    paths = download_recent(since=since)
    if not paths:
        log.error("wer: discovered/downloaded nothing; nothing to parse")
        return

    panel = load(paths, strict=False)
    out = config.INTERIM_DIR / "wer_panel.parquet"
    to_write = panel.copy()
    to_write["iso_week"] = to_write["iso_week"].dt.start_time.dt.strftime("%Y-%m-%d")
    to_write.to_parquet(out, index=False)
    log.info("wer: wrote %s", out)


if __name__ == "__main__":  # pragma: no cover
    main()
