"""WER PDF parser tests, against a synthetic fixture shaped like the real table.

epid.gov.lk may be unreachable, and real WER PDFs cannot be committed to the
repo. The parser is therefore exercised against a **synthetic table** built to
match the real "Table 1" structure exactly, confirmed against real 2022, 2023
and 2026 issues while building this parser:

* rows are disease pairs (cumulative "B" row, then current-week "A" row);
* columns are the 26 RDHS divisions plus a "SRILANKA" total, in a header row
  that is the table's **last** row, not its first;
* every cell's text is reversed with one character per line -- an artifact of
  how pdfplumber extracts this table's rotated rendering. :func:`_encode`
  simulates it; :func:`~dengue.ingest.wer_pdf._decode_wer_cell` (exercised
  indirectly through every test here) undoes it.

The numbers in the fixture are invented and labelled as such. They test parser
mechanics only -- no real case count is ever fabricated.
"""

from __future__ import annotations

import pandas as pd
import pytest

from dengue import config
from dengue.ingest.wer_pdf import (
    NATIONAL_TOTAL_TOLERANCE,
    _decode_wer_cell,
    _find_dengue_row_pair,
    _find_district_columns,
    parse_table,
    validate_against_national_total,
)
from dengue.utils.io import IngestError


def _week() -> pd.Period:
    return pd.Period("2026-07-27", freq=config.WEEK_FREQ)


def _encode(text: str) -> str:
    """Simulate Table 1's rotated-text extraction: reversed, one char/line."""
    return "\n".join(reversed(text))


#: Filler diseases before Dengue Fever, so tests exercise the dynamic row
#: search rather than assuming Dengue Fever is the first disease pair (in
#: real issues its row position varies as diseases are added over time).
#: Nine decoys, each two rows, plus Dengue Fever's two rows plus the header
#: clears parse_table's real-Table-1 shape gate (>=20 rows) the same way an
#: actual issue's ~15 disease blocks do.
_DECOY_DISEASES = (
    "Dysentery",
    "Encephalitis",
    "Meningitis",
    "Chickenpox",
    "Typhus",
    "Leptospirosis",
    "Tuberculosis",
    "Leprosy",
    "Rabies",
)


def make_wer_table(
    *, weekly_by_division: dict[str, int] | None = None, national_total: int | None = None
) -> list[list[str]]:
    """Build a synthetic WER-Table-1-shaped table.

    Layout mirrors the real table: several decoy disease row-pairs, then the
    Dengue Fever row-pair, then the district/total header row last. All
    counts are SYNTHETIC.
    """
    divisions = list(config.RDHS_DIVISIONS)
    if weekly_by_division is None:
        weekly_by_division = {division: 10 + 3 * i for i, division in enumerate(divisions)}

    total = national_total if national_total is not None else sum(weekly_by_division.values())

    rows: list[list[str]] = []
    for disease in _DECOY_DISEASES:
        rows.append(
            [_encode(disease), _encode("B"), *[_encode("1") for _ in divisions], _encode("1"), ""]
        )
        rows.append([None, _encode("A"), *[_encode("0") for _ in divisions], _encode("0"), ""])

    weekly_values = [weekly_by_division[d] for d in divisions]
    rows.append(
        [
            _encode("Dengue Fever"),
            _encode("B"),
            *[_encode(str(w * 30)) for w in weekly_values],
            _encode(str(total * 30)),
            "",
        ]
    )
    rows.append(
        [None, _encode("A"), *[_encode(str(w)) for w in weekly_values], _encode(str(total)), ""]
    )

    header = [
        _encode("RDHS"),
        "",
        *[_encode(d) for d in divisions],
        _encode("SRILANKA"),
        "",
    ]
    rows.append(header)
    return rows


# --------------------------------------------------------------------------
# _decode_wer_cell
# --------------------------------------------------------------------------


def test_decode_wer_cell_reverses_rotated_text():
    assert _decode_wer_cell(_encode("Colombo")) == "Colombo"
    assert _decode_wer_cell(_encode("1138")) == "1138"
    assert _decode_wer_cell(_encode("Dengue Fever")) == "Dengue Fever"


def test_decode_wer_cell_handles_blank_and_none():
    assert _decode_wer_cell(None) == ""
    assert _decode_wer_cell("") == ""


# --------------------------------------------------------------------------
# _find_dengue_row_pair / _find_district_columns
# --------------------------------------------------------------------------


def test_find_dengue_row_pair_locates_it_past_decoy_diseases():
    table = make_wer_table()
    pair = _find_dengue_row_pair(table)
    assert pair is not None
    b_row, a_row = pair
    assert a_row == b_row + 1
    # Not the first disease -- the decoys must actually have been skipped.
    assert b_row == len(_DECOY_DISEASES) * 2


def test_find_dengue_row_pair_returns_none_when_absent():
    table = [[_encode("Malaria"), _encode("B"), "1", ""], [None, _encode("A"), "0", ""]]
    assert _find_dengue_row_pair(table) is None


def test_find_district_columns_maps_header_row_and_total():
    table = make_wer_table()
    header = table[-1]
    columns, total_index = _find_district_columns(header)

    assert set(columns.values()) == set(config.DISTRICT_IDS)
    assert total_index == len(header) - 2  # last real column before the trailing blank


# --------------------------------------------------------------------------
# parse_table
# --------------------------------------------------------------------------


def test_parse_table_reads_the_weekly_row_not_the_cumulative():
    """Reading the B (cumulative) row instead of A would inflate everything ~30x."""
    weekly = {division: 10 for division in config.RDHS_DIVISIONS}
    table = make_wer_table(weekly_by_division=weekly)

    counts, national_total = parse_table(table)
    assert national_total == 10 * len(config.RDHS_DIVISIONS)
    # Every division is 10, except Ampara which absorbs Kalmunai and so is 20.
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

    # Overwrite Colombo's weekly cell with a comma-thousands-separated value.
    a_row_index = len(_DECOY_DISEASES) * 2 + 1
    table[a_row_index][2] = _encode("1,234")

    counts, _ = parse_table(table)
    assert counts["colombo"] == 1234


def test_parse_table_ignores_blank_and_dashed_cells():
    table = make_wer_table()
    a_row_index = len(_DECOY_DISEASES) * 2 + 1
    table[a_row_index][2] = _encode("-")

    counts, _ = parse_table(table)
    assert "colombo" not in counts


def test_parse_table_returns_empty_without_a_dengue_row():
    # Same shape as a real Table 1 (clears the row/column minimums) but no
    # disease pair is named "Dengue Fever".
    table = make_wer_table()
    for row in table[:-1]:
        if row[0]:
            row[0] = _encode("Not Dengue")
    assert parse_table(table) == ({}, None)


def test_parse_table_returns_empty_below_the_shape_minimum():
    """A small table (e.g. one of the WER's other tables) must not be mistaken
    for Table 1, even if it happens to contain a row that decodes to a
    disease name."""
    tiny = [[_encode("Dengue Fever"), _encode("B"), "1", ""], [None, _encode("A"), "0", ""]]
    assert parse_table(tiny) == ({}, None)


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


def test_validation_catches_the_cumulative_row_mistake():
    """The failure mode this check exists for: reading the cumulative (B)
    row's values as if they were the current-week (A) counts."""
    weekly = {division: 10 for division in config.RDHS_DIVISIONS}
    table = make_wer_table(weekly_by_division=weekly)

    b_row_index = len(_DECOY_DISEASES) * 2  # the Dengue Fever cumulative row
    header = table[-1]
    columns, _ = _find_district_columns(header)
    cumulative_counts = {
        district_id: int(_decode_wer_cell(table[b_row_index][idx]))
        for idx, district_id in columns.items()
    }
    real_weekly_total = 10 * len(config.RDHS_DIVISIONS)

    result = validate_against_national_total(cumulative_counts, real_weekly_total, _week())
    assert not result.passed, "reading the cumulative row must be caught"


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


# --------------------------------------------------------------------------
# _extract_report_week
# --------------------------------------------------------------------------


def test_extract_report_week_reads_table_1s_own_date_range():
    from dengue.ingest.wer_pdf import _extract_report_week

    text = (
        "Table 1: Distribution of Notified Diseases reported by Medical "
        "Officers of Health 15th – 21st June 2026 (25th Week)"
    )
    week = _extract_report_week(text)
    assert week == pd.Period("2026-06-15", freq=config.WEEK_FREQ)


def test_extract_report_week_handles_a_month_boundary():
    from dengue.ingest.wer_pdf import _extract_report_week

    text = "Table 1: ... 28th – 03rd Jun 2022 (22nd Week)"
    week = _extract_report_week(text)
    assert week == pd.Period("2022-05-28", freq=config.WEEK_FREQ)


def test_extract_report_week_returns_none_without_a_match():
    from dengue.ingest.wer_pdf import _extract_report_week

    assert _extract_report_week("no table here") is None
