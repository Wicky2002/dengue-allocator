"""WER PDF parser tests, against a synthetic fixture.

epid.gov.lk may be unreachable, and real WER PDFs cannot be committed to the
repo. The parser is therefore exercised against a **synthetic table** with the
same structure as the real one: 26 RDHS division rows (Kalmunai separate from
Ampara), paired A/B columns per disease, and a printed national total.

The numbers in the fixture are invented and labelled as such. They test parser
mechanics only -- no real case count is ever fabricated.
"""

from __future__ import annotations

import pandas as pd
import pytest

from dengue import config
from dengue.ingest.wer_pdf import (
    NATIONAL_TOTAL_TOLERANCE,
    find_dengue_columns,
    parse_table,
    validate_against_national_total,
)
from dengue.utils.io import IngestError


def _week() -> pd.Period:
    return pd.Period("2026-07-27", freq=config.WEEK_FREQ)


def make_wer_table(
    *, weekly_by_division: dict[str, int] | None = None, national_total: int | None = None
) -> list[list[str]]:
    """Build a synthetic WER-shaped table.

    Layout mirrors the real "Table 1": a two-row header with disease names above
    paired A (this week) / B (cumulative) columns, then one row per RDHS division,
    then the all-island total.

    All counts are SYNTHETIC.
    """
    if weekly_by_division is None:
        # Arbitrary but deterministic synthetic counts, one per RDHS division.
        weekly_by_division = {
            division: 10 + 3 * i for i, division in enumerate(config.RDHS_DIVISIONS)
        }

    header_1 = ["RDHS Division", "Dengue Fever", "", "Dysentery", "", "Encephalitis", ""]
    header_2 = ["", "A", "B", "A", "B", "A", "B"]

    rows: list[list[str]] = [header_1, header_2]
    for division, weekly in weekly_by_division.items():
        cumulative = weekly * 30
        rows.append([division, str(weekly), f"{cumulative:,}", "2", "40", "0", "3"])

    total = national_total if national_total is not None else sum(weekly_by_division.values())
    rows.append(["Sri Lanka", str(total), "0", "0", "0", "0", "0"])
    return rows


def test_find_dengue_columns_locates_the_a_b_pair():
    table = make_wer_table()
    assert find_dengue_columns(table[:3]) == (1, 2)


def test_find_dengue_columns_returns_none_when_absent():
    assert find_dengue_columns([["Division", "Malaria", "A", "B"]]) is None


def test_parse_table_reads_the_weekly_column_not_the_cumulative():
    """Reading column B instead of A would inflate everything ~30x."""
    weekly = {division: 10 for division in config.RDHS_DIVISIONS}
    table = make_wer_table(weekly_by_division=weekly)

    counts, national_total = parse_table(table)
    assert national_total == 10 * len(config.RDHS_DIVISIONS)
    # Every district is 10, except Ampara which absorbs Kalmunai and so is 20.
    assert counts["colombo"] == 10
    assert counts["ampara"] == 20


def test_parse_table_folds_kalmunai_into_ampara():
    """26 division rows must collapse to 25 districts."""
    table = make_wer_table()
    counts, _ = parse_table(table)

    assert len(counts) == config.N_DISTRICTS == 25
    assert set(counts) == set(config.DISTRICT_IDS)

    ampara_weekly = 10 + 3 * config.RDHS_DIVISIONS.index("Ampara")
    kalmunai_weekly = 10 + 3 * config.RDHS_DIVISIONS.index("Kalmunai")
    assert counts["ampara"] == ampara_weekly + kalmunai_weekly


def test_parse_table_sum_matches_printed_national_total():
    table = make_wer_table()
    counts, national_total = parse_table(table)
    assert sum(counts.values()) == national_total


def test_parse_table_handles_thousands_separators():
    weekly = {division: 0 for division in config.RDHS_DIVISIONS}
    weekly["Colombo"] = 1234
    table = make_wer_table(weekly_by_division=weekly)
    table[2][1] = "1,234"

    counts, _ = parse_table(table)
    assert counts["colombo"] == 1234


def test_parse_table_ignores_blank_and_dashed_cells():
    table = make_wer_table()
    table[2][1] = "-"
    counts, _ = parse_table(table)
    assert "colombo" not in counts


def test_parse_table_returns_empty_without_a_dengue_column():
    assert parse_table([["Division", "Malaria"], ["Colombo", "5"]]) == ({}, None)


def test_parse_table_handles_empty_input():
    assert parse_table([]) == ({}, None)


# --------------------------------------------------------------------------
# validate_against_national_total
# --------------------------------------------------------------------------


def test_validation_passes_when_rows_reconcile():
    counts = {"colombo": 100, "gampaha": 200}
    result = validate_against_national_total(counts, 300, _week())
    assert result.passed
    assert result.relative_error == 0.0
    assert result.district_sum == 300


def test_validation_passes_within_one_percent():
    counts = {"colombo": 100, "gampaha": 200}
    result = validate_against_national_total(counts, 302, _week())  # 0.66% off
    assert result.passed
    assert result.relative_error < NATIONAL_TOTAL_TOLERANCE


def test_validation_fails_beyond_one_percent():
    counts = {"colombo": 100, "gampaha": 200}
    result = validate_against_national_total(counts, 350, _week())  # ~14% off
    assert not result.passed
    assert result.relative_error > NATIONAL_TOTAL_TOLERANCE


def test_validation_catches_the_cumulative_column_mistake():
    """The failure mode this check exists for."""
    weekly = {division: 10 for division in config.RDHS_DIVISIONS}
    table = make_wer_table(weekly_by_division=weekly)

    # Simulate reading column B (cumulative) instead of A.
    counts, national_total = parse_table(table, dengue_columns=(2, 3))
    result = validate_against_national_total(counts, national_total, _week())

    assert not result.passed, "reading the cumulative column must be caught"


def test_validation_flags_missing_national_total_as_unverified():
    result = validate_against_national_total({"colombo": 100}, None, _week())
    assert not result.passed
    assert result.relative_error is None
    assert "UNVERIFIED" in result.describe()


def test_validation_reports_row_count():
    table = make_wer_table()
    counts, national_total = parse_table(table)
    result = validate_against_national_total(counts, national_total, _week(), n_rows=len(counts))
    assert result.n_rows == 25
    assert "rows=25" in result.describe()


def test_ingest_error_is_raised_for_a_non_pdf(tmp_path):
    from dengue.ingest.wer_pdf import parse_pdf

    fake = tmp_path / "not_a.pdf"
    fake.write_bytes(b"this is not a PDF")
    with pytest.raises(Exception):  # noqa: B017 - pdfplumber's error type is not part of our API
        parse_pdf(fake, _week())


def test_load_refuses_to_emit_unvalidated_data(tmp_path, monkeypatch):
    """If nothing passes validation, load() must raise rather than return data."""
    from dengue.ingest import wer_pdf

    def always_fails(path, iso_week, *, strict=False):
        raise IngestError("synthetic parse failure")

    monkeypatch.setattr(wer_pdf, "parse_pdf", always_fails)
    with pytest.raises(IngestError, match="Refusing to emit unverified"):
        wer_pdf.load({_week(): tmp_path / "missing.pdf"})
