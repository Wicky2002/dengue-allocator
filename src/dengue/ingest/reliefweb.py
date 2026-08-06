"""Ingest Sri Lanka dengue situation reports from the ReliefWeb API.

ReliefWeb republishes National Dengue Control Unit (NDCU), Ministry of Health,
WHO and IFRC bulletins. Its value here is twofold: it carries the **high-risk
MOH area** designations that Stage 3 allocates against, and it provides an
independent cross-check on district case counts parsed from the Epidemiology
Unit PDFs.

API status (verified 2026-08)
-----------------------------
* **v1 is decommissioned** -- ``https://api.reliefweb.int/v1/reports`` returns
  ``HTTP 410 Gone``.
* **v2 is current** -- ``https://api.reliefweb.int/v2/reports``.
* Since 2025-11-01 ReliefWeb requires a **pre-approved** ``appname``. An
  unregistered value returns ``HTTP 403 Forbidden``. Request one at
  https://reliefweb.int/contact (subject: "API appname") and set
  ``RELIEFWEB_APPNAME`` in ``.env``.

When the API is unavailable this module raises
:class:`~dengue.utils.io.IngestError` with the remediation spelled out. It never
falls back to invented counts; the caller decides whether to proceed with the
other sources.

Licence
-------
ReliefWeb content is redistributed under the terms of the originating
organisation. NDCU / Ministry of Health material is Sri Lankan government
publication. See https://reliefweb.int/terms-conditions.
"""

from __future__ import annotations

import json
import re
from typing import Any

import pandas as pd

from dengue import config
from dengue.utils.io import IngestError, http_get
from dengue.utils.logging import get_logger

log = get_logger(__name__)

#: ReliefWeb's numeric id for Sri Lanka.
SRI_LANKA_ISO3 = "LKA"

REPORT_FIELDS = (
    "id",
    "title",
    "date.created",
    "date.original",
    "source.name",
    "source.shortname",
    "url",
    "body",
    "file.url",
    "file.filename",
    "file.mimetype",
    "theme.name",
    "disaster_type.name",
)

#: Matches "137 high-risk MOH areas", "high risk MOH areas: 137",
#: "137 high risk MOH area(s)" and similar phrasings used in NDCU bulletins.
_HIGH_RISK_PATTERNS = (
    re.compile(
        r"(?P<count>\d{1,4})\s+high[\s-]*risk\s+MOH\s+(?:areas?|divisions?)",
        re.IGNORECASE,
    ),
    re.compile(
        r"high[\s-]*risk\s+MOH\s+(?:areas?|divisions?)\D{0,20}?(?P<count>\d{1,4})",
        re.IGNORECASE,
    ),
)

#: A district name followed by a case count, as it appears in flattened HTML
#: tables in report bodies, e.g. "Colombo 1,234" or "Gampaha | 987".
_DISTRICT_ROW = re.compile(
    r"^\s*(?P<name>[A-Za-z][A-Za-z\s\.'-]{2,30}?)\s*[\|:\t]?\s*(?P<count>\d[\d,]{0,7})\s*$",
    re.MULTILINE,
)


def query_reports(
    *,
    limit: int = 100,
    offset: int = 0,
    query: str = "dengue",
    appname: str | None = None,
) -> dict[str, Any]:
    """Query the ReliefWeb v2 reports endpoint for Sri Lanka dengue reports.

    Raises
    ------
    IngestError
        On any API failure, with the ``appname`` remediation included for the
        403 case that unregistered clients hit.
    """
    appname = appname or config.RELIEFWEB_APPNAME
    url = f"{config.RELIEFWEB_BASE_URL}/reports"

    params: dict[str, Any] = {
        "appname": appname,
        "limit": limit,
        "offset": offset,
        "profile": "list",
        "query[value]": query,
        "query[operator]": "AND",
        "filter[field]": "country.iso3",
        "filter[value]": SRI_LANKA_ISO3.lower(),
        "sort[]": "date.created:desc",
    }
    for i, field in enumerate(REPORT_FIELDS):
        params[f"fields[include][{i}]"] = field

    try:
        response = http_get(url, params=params, expect_json=True, retries=2)
    except IngestError as exc:
        if "403" in str(exc):
            raise IngestError(
                "ReliefWeb API returned 403 Forbidden. Since 2025-11-01 the API "
                f"requires a PRE-APPROVED appname; {appname!r} is not registered. "
                "Request one at https://reliefweb.int/contact (subject: 'API appname') "
                "and set RELIEFWEB_APPNAME in .env. "
                "The pipeline can proceed without this source; high_risk_flag will "
                "remain null."
            ) from exc
        if "410" in str(exc):
            raise IngestError(
                "ReliefWeb API v1 is decommissioned (410 Gone). Set "
                "RELIEFWEB_BASE_URL=https://api.reliefweb.int/v2 in .env."
            ) from exc
        raise

    return response.json()


def fetch_all_reports(
    *, max_reports: int = 400, page_size: int = 100, query: str = "dengue"
) -> list[dict[str, Any]]:
    """Page through the reports endpoint and persist raw JSON to ``data/raw/``."""
    config.ensure_dirs()
    collected: list[dict[str, Any]] = []
    offset = 0

    while len(collected) < max_reports:
        payload = query_reports(limit=page_size, offset=offset, query=query)
        page = payload.get("data", [])
        if not page:
            break

        raw_path = config.RAW_RELIEFWEB / f"reports_offset{offset:05d}.json"
        raw_path.write_text(json.dumps(payload), encoding="utf-8")

        collected.extend(page)
        total = payload.get("totalCount", len(collected))
        log.info(
            "reliefweb: fetched %d reports (offset=%d, total available=%s) -> %s",
            len(page),
            offset,
            total,
            raw_path.name,
        )

        offset += page_size
        if offset >= int(total):
            break

    log.info("reliefweb: %d reports collected", len(collected))
    return collected


def parse_high_risk_moh_count(text: str) -> int | None:
    """Extract the count of high-risk MOH areas from report text.

    Returns ``None`` when the text does not state one -- which is the common
    case, and must never be filled in with a guess.

    Examples
    --------
    >>> parse_high_risk_moh_count("A total of 137 high-risk MOH areas were identified.")
    137
    >>> parse_high_risk_moh_count("No figure here.") is None
    True
    """
    if not text:
        return None
    for pattern in _HIGH_RISK_PATTERNS:
        match = pattern.search(text)
        if match:
            value = int(match.group("count"))
            # Sri Lanka has ~354 MOH areas; anything larger is a mis-parse.
            if 0 < value <= 400:
                return value
    return None


def parse_district_counts(text: str) -> dict[str, int]:
    """Extract district case counts from flattened report body text.

    Only lines whose leading token resolves to a known district via
    :func:`dengue.config.normalise_district` are kept, so prose numbers and
    unrelated tables are ignored. Where a district appears more than once (for
    instance a cumulative table after a weekly one) the **first** occurrence
    wins, matching document order.

    Returns
    -------
    dict
        ``district_id -> count``. Empty when nothing parses -- an empty result
        is a legitimate outcome, not an error to paper over.
    """
    counts: dict[str, int] = {}
    if not text:
        return counts

    for match in _DISTRICT_ROW.finditer(text):
        raw_name = match.group("name").strip()
        district_id = config.normalise_district(raw_name, strict=False)
        if district_id is None or district_id in counts:
            continue
        try:
            counts[district_id] = int(match.group("count").replace(",", ""))
        except ValueError:  # pragma: no cover - regex guarantees digits
            continue

    return counts


def _strip_html(body: str) -> str:
    """Crude HTML/markdown flattening adequate for ReliefWeb bodies."""
    text = re.sub(r"<[^>]+>", "\n", body)
    text = text.replace("&nbsp;", " ").replace("&amp;", "&")
    text = re.sub(r"[ \t]+", " ", text)
    return text


def reports_to_frame(reports: list[dict[str, Any]]) -> pd.DataFrame:
    """Flatten raw report records into a tidy metadata frame.

    Columns: ``report_id``, ``title``, ``source``, ``date_original``,
    ``date_created``, ``url``, ``pdf_urls``, ``high_risk_moh_count``,
    ``n_districts_parsed``, ``body_chars``.
    """
    rows: list[dict[str, Any]] = []

    for report in reports:
        fields = report.get("fields", report)
        body = fields.get("body", "") or ""
        text = _strip_html(body)

        files = fields.get("file", []) or []
        pdf_urls = [
            f.get("url", "")
            for f in files
            if str(f.get("mimetype", "")).endswith("pdf") or str(f.get("url", "")).endswith(".pdf")
        ]

        sources = fields.get("source", []) or []
        source_names = [s.get("shortname") or s.get("name", "") for s in sources]

        date_block = fields.get("date", {}) or {}
        district_counts = parse_district_counts(text)

        rows.append(
            {
                "report_id": fields.get("id", report.get("id")),
                "title": fields.get("title", ""),
                "source": "; ".join(filter(None, source_names)),
                "date_original": date_block.get("original"),
                "date_created": date_block.get("created"),
                "url": fields.get("url", ""),
                "pdf_urls": "; ".join(pdf_urls),
                "high_risk_moh_count": parse_high_risk_moh_count(text),
                "n_districts_parsed": len(district_counts),
                "district_counts_json": json.dumps(district_counts) if district_counts else None,
                "body_chars": len(text),
            }
        )

    frame = pd.DataFrame(rows)
    if not frame.empty:
        for col in ("date_original", "date_created"):
            frame[col] = pd.to_datetime(frame[col], errors="coerce", utc=True)
        frame = frame.sort_values("date_original", ascending=False).reset_index(drop=True)
    return frame


def load(*, max_reports: int = 400) -> pd.DataFrame:
    """Fetch, persist and parse ReliefWeb Sri Lanka dengue reports.

    Returns
    -------
    pandas.DataFrame
        Report metadata with parsed high-risk MOH counts and district counts.

    Raises
    ------
    IngestError
        If the API is unreachable or the appname is not approved.
    """
    log.info(
        "reliefweb: querying %s (appname=%s)", config.RELIEFWEB_BASE_URL, config.RELIEFWEB_APPNAME
    )
    reports = fetch_all_reports(max_reports=max_reports)
    frame = reports_to_frame(reports)

    if frame.empty:
        log.warning("reliefweb: no reports parsed")
        return frame

    n_with_high_risk = int(frame["high_risk_moh_count"].notna().sum())
    n_with_districts = int((frame["n_districts_parsed"] > 0).sum())
    log.info(
        "reliefweb: rows=%d  dates=[%s .. %s]  with_high_risk_count=%d  with_district_counts=%d",
        len(frame),
        frame["date_original"].min(),
        frame["date_original"].max(),
        n_with_high_risk,
        n_with_districts,
    )

    out = config.RAW_RELIEFWEB / "reports_metadata.parquet"
    frame.to_parquet(out, index=False)
    log.info("reliefweb: wrote %s", out)
    return frame


def main() -> None:  # pragma: no cover - CLI entry point
    config.ensure_dirs()
    load()


if __name__ == "__main__":  # pragma: no cover
    main()
