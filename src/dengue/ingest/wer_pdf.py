"""Parse Epidemiology Unit Weekly Epidemiological Report (WER) PDFs.

The WER (https://www.epid.gov.lk/weekly-epidemiological-report/) is the
authoritative source for notified dengue cases in Sri Lanka. Each issue carries
"Table 1: Selected notifiable diseases reported by Medical Officers of Health",
a grid whose rows are the **26 RDHS reporting divisions** (25 districts, with
Kalmunai listed separately from Ampara) and whose columns are diseases -- Dengue
Fever among them -- each split into a current-week count ``A`` and a
cumulative-for-the-year count ``B``.

Two structural facts drive the parser:

1. **26 rows, not 25.** Kalmunai must be folded into Ampara to reach district
   level. :func:`dengue.config.rdhs_to_district` does this.
2. **A/B column pairing.** Every disease occupies two adjacent numeric columns.
   Taking the wrong one of the pair silently substitutes a year-to-date total
   for a weekly count -- an error that inflates figures by one to two orders of
   magnitude and is easy to miss. :func:`validate_against_national_total` is the
   guard against exactly this class of mistake.

Validation
----------
Every parsed week is checked with :func:`validate_against_national_total`: the
26 division rows must sum to the printed national total within 1%. Weeks that
fail are flagged and, by default, **excluded** rather than silently accepted.

If epid.gov.lk is unreachable the parser is still fully exercised by
``tests/test_wer_pdf.py`` against a synthetic fixture. No case data is ever
fabricated to stand in for a failed download.

Licence
-------
Sri Lanka Ministry of Health / Epidemiology Unit publication. Public health
information published for public use; cite the Epidemiology Unit.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from dengue import config
from dengue.utils.io import IngestError, download_binary
from dengue.utils.logging import get_logger

log = get_logger(__name__)

#: Tolerance for the district-sum vs national-total cross-check.
NATIONAL_TOTAL_TOLERANCE = 0.01

#: Row label used by the WER for the all-island total.
_TOTAL_ROW_PATTERN = re.compile(r"\b(sri\s*lanka|total|grand\s*total)\b", re.IGNORECASE)

#: Column header identifying the dengue block.
_DENGUE_HEADER = re.compile(r"dengue", re.IGNORECASE)

_NUMBER = re.compile(r"^-?[\d,]+$")


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


def find_dengue_columns(header_rows: list[list[Any]]) -> tuple[int, int] | None:
    """Locate the (A, B) column index pair for Dengue Fever in a WER table.

    The WER header spans two physical rows: disease names on one, ``A``/``B``
    sub-headers beneath. Returns ``(a_index, b_index)`` where ``A`` is the
    current-week count and ``B`` the cumulative total, or ``None`` if the dengue
    block cannot be located.
    """
    for row in header_rows:
        for idx, cell in enumerate(row):
            if cell and _DENGUE_HEADER.search(str(cell)):
                # The disease label sits above its A column; B is the next one.
                return idx, idx + 1
    return None


def parse_table(
    table: list[list[Any]], *, dengue_columns: tuple[int, int] | None = None
) -> tuple[dict[str, int], int | None]:
    """Parse one extracted WER table into division counts and the national total.

    Parameters
    ----------
    table:
        A table as returned by ``pdfplumber``'s ``extract_table()``: a list of
        rows, each a list of cell strings.
    dengue_columns:
        ``(a_index, b_index)`` from :func:`find_dengue_columns`. When omitted,
        the function attempts to locate them from the table's own header rows.

    Returns
    -------
    tuple
        ``(counts, national_total)`` where ``counts`` maps ``district_id`` to
        the summed current-week count (Kalmunai already folded into Ampara), and
        ``national_total`` is the printed all-island figure or ``None``.
    """
    if not table:
        return {}, None

    if dengue_columns is None:
        dengue_columns = find_dengue_columns(table[:3])
    if dengue_columns is None:
        return {}, None

    a_index, _b_index = dengue_columns
    counts: dict[str, int] = {}
    national_total: int | None = None

    for row in table:
        if not row or row[0] is None:
            continue
        label = str(row[0]).strip()
        if not label:
            continue

        if a_index >= len(row):
            continue
        value = _to_int(row[a_index])

        if _TOTAL_ROW_PATTERN.search(label):
            if value is not None:
                national_total = value
            continue

        district_id = config.normalise_district(label, strict=False)
        if district_id is None or value is None:
            continue

        # Kalmunai folds into Ampara: accumulate rather than overwrite.
        counts[district_id] = counts.get(district_id, 0) + value

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


def extract_tables_from_pdf(path: Path) -> list[list[list[Any]]]:
    """Extract every table from a WER PDF using pdfplumber."""
    try:
        import pdfplumber
    except ImportError as exc:  # pragma: no cover - dependency is pinned
        raise IngestError("pdfplumber is required to parse WER PDFs") from exc

    tables: list[list[list[Any]]] = []
    with pdfplumber.open(path) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            for table in page.extract_tables():
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
        The week the report covers. The WER does not encode this machine-readably
        in a reliable place, so the caller supplies it (normally derived from the
        filename or the index page that linked to it).
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
            "find_dengue_columns()."
        )

    if len(best_counts) < config.N_DISTRICTS:
        log.warning(
            "wer: parsed only %d of %d districts from %s",
            len(best_counts),
            config.N_DISTRICTS,
            path.name,
        )

    validation = validate_against_national_total(
        best_counts, best_total, iso_week, n_rows=len(best_counts)
    )
    if strict and not validation.passed:
        raise IngestError(
            f"WER national-total validation failed for {iso_week}: {validation.describe()}"
        )

    frame = pd.DataFrame(
        {
            "district_id": list(best_counts.keys()),
            "iso_week": iso_week,
            "cases": list(best_counts.values()),
        }
    )
    return frame, validation


def download_wer_pdf(url: str, iso_week: pd.Period, *, refresh: bool = False) -> Path:
    """Download a WER PDF into ``data/raw/wer/``."""
    config.ensure_dirs()
    dest = config.RAW_WER / f"wer_{iso_week.start_time:%Y-%m-%d}.pdf"
    return download_binary(url, dest, refresh=refresh)


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
    log.info(
        "wer_pdf is a parser library. Supply PDFs via load({iso_week: path}). "
        "Automated discovery of WER issue URLs from %s is future work; the "
        "site's index is paginated HTML with no stable machine-readable feed.",
        config.EPID_BASE_URL,
    )


if __name__ == "__main__":  # pragma: no cover
    main()
