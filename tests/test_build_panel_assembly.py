"""Tests for assemble_panel's real-data source ordering.

WER (current, all-25-district) is tried first, colmozzie (Colombo only,
2008-2014) is the fallback, and the fully synthetic panel is the last
resort. All three tiers are exercised here without any real network access,
by monkeypatching each ingest module's ``load``/``download_recent``.
"""

from __future__ import annotations

import pandas as pd

from dengue import config
from dengue.features.build_panel import _load_cases, assemble_panel
from dengue.ingest import colmozzie, openmeteo, wer_pdf
from dengue.utils.io import IngestError

#: assemble_panel() refuses any assembled panel under 100 rows (guards
#: against silently shipping a near-empty "real" panel), so fixtures used in
#: end-to-end assemble_panel tests must clear that -- not just be non-empty.
_WER_DISTRICTS = ("colombo", "gampaha", "kandy", "galle", "matara", "jaffna")


def _wer_cases() -> pd.DataFrame:
    weeks = pd.period_range("2024-01-01", periods=20, freq=config.WEEK_FREQ)
    rows = [{"district_id": d, "iso_week": w, "cases": 5} for d in _WER_DISTRICTS for w in weeks]
    return pd.DataFrame(rows)


def _colmozzie_cases() -> pd.DataFrame:
    weeks = pd.period_range("2010-01-01", periods=120, freq=config.WEEK_FREQ)
    return pd.DataFrame(
        {
            "district_id": "colombo",
            "iso_week": weeks,
            "cases": 3,
            "population": config.DISTRICT_BY_ID["colombo"].population,
            "rain_mm": 10.0,
            "tmax": 30.0,
            "tmin": 24.0,
            "rh": 80.0,
            "high_risk_flag": pd.NA,
        }
    )


def _weather_for(cases: pd.DataFrame) -> pd.DataFrame:
    keys = cases[["district_id", "iso_week"]].drop_duplicates()
    keys["rain_mm"] = 12.0
    keys["tmax"] = 31.0
    keys["tmin"] = 25.0
    keys["rh"] = 78.0
    return keys


# --------------------------------------------------------------------------
# _load_cases: source ordering + population/high_risk_flag attachment
# --------------------------------------------------------------------------


def test_load_cases_prefers_wer_and_attaches_population_and_flag(monkeypatch):
    monkeypatch.setattr(wer_pdf, "download_recent", lambda *a, **kw: {"fake": "paths"})
    monkeypatch.setattr(wer_pdf, "load", lambda *a, **kw: _wer_cases())

    def _colmozzie_must_not_be_called(*a, **kw):
        raise AssertionError("colmozzie.load should not be called when WER succeeds")

    monkeypatch.setattr(colmozzie, "load", _colmozzie_must_not_be_called)

    cases = _load_cases(refresh=False)

    assert set(cases["district_id"]) == set(_WER_DISTRICTS)
    assert (
        cases["population"]
        == cases["district_id"].map(lambda d: config.DISTRICT_BY_ID[d].population)
    ).all()
    assert cases["high_risk_flag"].isna().all()


def test_load_cases_falls_back_to_colmozzie_when_wer_download_fails(monkeypatch):
    def _wer_fails(*a, **kw):
        raise IngestError("simulated WER outage")

    monkeypatch.setattr(wer_pdf, "download_recent", _wer_fails)
    monkeypatch.setattr(colmozzie, "load", lambda *a, **kw: _colmozzie_cases())

    cases = _load_cases(refresh=False)
    assert set(cases["district_id"]) == {"colombo"}
    assert len(cases) == 120


def test_load_cases_falls_back_to_colmozzie_when_wer_parsing_fails(monkeypatch):
    monkeypatch.setattr(wer_pdf, "download_recent", lambda *a, **kw: {"fake": "paths"})

    def _load_fails(*a, **kw):
        raise IngestError("no WER weeks passed validation")

    monkeypatch.setattr(wer_pdf, "load", _load_fails)
    monkeypatch.setattr(colmozzie, "load", lambda *a, **kw: _colmozzie_cases())

    cases = _load_cases(refresh=False)
    assert set(cases["district_id"]) == {"colombo"}


# --------------------------------------------------------------------------
# assemble_panel: end-to-end tier selection
# --------------------------------------------------------------------------


def test_assemble_panel_builds_from_wer_when_available(monkeypatch):
    wer_cases = _wer_cases()
    monkeypatch.setattr(wer_pdf, "download_recent", lambda *a, **kw: {"fake": "paths"})
    monkeypatch.setattr(wer_pdf, "load", lambda *a, **kw: wer_cases)
    monkeypatch.setattr(openmeteo, "load", lambda *a, **kw: _weather_for(wer_cases))

    panel = assemble_panel(use_synthetic=False)

    assert set(panel["district_id"]) == set(_WER_DISTRICTS)
    assert (panel["cases"] == 5).all()


def test_assemble_panel_falls_back_to_colmozzie_when_wer_fails(monkeypatch):
    def _wer_fails(*a, **kw):
        raise IngestError("simulated WER outage")

    colmozzie_cases = _colmozzie_cases()
    monkeypatch.setattr(wer_pdf, "download_recent", _wer_fails)
    monkeypatch.setattr(colmozzie, "load", lambda *a, **kw: colmozzie_cases)
    monkeypatch.setattr(openmeteo, "load", lambda *a, **kw: _weather_for(colmozzie_cases))

    panel = assemble_panel(use_synthetic=False)

    assert set(panel["district_id"]) == {"colombo"}
    assert (panel["cases"] == 3).all()


def test_assemble_panel_falls_back_to_synthetic_when_everything_fails(monkeypatch):
    def _always_fails(*a, **kw):
        raise IngestError("simulated total outage")

    monkeypatch.setattr(wer_pdf, "download_recent", _always_fails)
    monkeypatch.setattr(colmozzie, "load", _always_fails)

    sentinel = pd.DataFrame({"district_id": ["synthetic_marker"], "iso_week": [pd.NaT]})
    monkeypatch.setattr("dengue.utils.synthetic.make_synthetic_panel", lambda *a, **kw: sentinel)

    panel = assemble_panel(use_synthetic=False)
    pd.testing.assert_frame_equal(panel, sentinel)


def test_assemble_panel_use_synthetic_skips_ingest_entirely(monkeypatch):
    def _must_not_be_called(*a, **kw):
        raise AssertionError("ingest must not run when use_synthetic=True")

    monkeypatch.setattr(wer_pdf, "download_recent", _must_not_be_called)
    monkeypatch.setattr(colmozzie, "load", _must_not_be_called)

    panel = assemble_panel(use_synthetic=True, refresh=False)
    assert not panel.empty
    assert "district_id" in panel.columns


def test_wer_backfill_start_is_a_valid_period():
    """Guards the config constant `_load_cases` depends on."""
    assert pd.Period(config.WER_BACKFILL_START, freq=config.WEEK_FREQ) < pd.Period.now(
        freq=config.WEEK_FREQ
    )
