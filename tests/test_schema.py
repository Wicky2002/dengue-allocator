"""Schema-contract tests.

The panel schema is the interface between every workstream, so it gets tested
like an API, not like an implementation detail.
"""

from __future__ import annotations

import pandas as pd
import pytest

from dengue import config
from dengue.utils.io import coerce_panel_schema, read_panel, write_panel
from dengue.utils.synthetic import make_synthetic_panel


@pytest.fixture(scope="module")
def panel() -> pd.DataFrame:
    return make_synthetic_panel(n_districts=6, n_weeks=120, seed=11)


def test_registry_invariants():
    """25 districts, 26 RDHS divisions, connected adjacency graph."""
    config.validate_registry()
    assert config.N_DISTRICTS == 25
    assert config.N_RDHS_DIVISIONS == 26
    # Kalmunai is the sole reason 26 != 25.
    assert "Kalmunai" in config.RDHS_DIVISIONS
    assert config.get_district("ampara").rdhs_divisions == ("Ampara", "Kalmunai")


def test_panel_has_exact_schema_columns(panel):
    assert list(panel.columns) == list(config.PANEL_COLUMNS)


def test_panel_dtypes_match_contract(panel):
    for column, expected in config.PANEL_DTYPES.items():
        assert (
            str(panel[column].dtype) == expected
        ), f"{column} has dtype {panel[column].dtype}, contract requires {expected}"


def test_panel_is_unique_on_district_week(panel):
    assert not panel.duplicated(subset=["district_id", "iso_week"]).any()


def test_panel_district_ids_are_canonical(panel):
    assert set(panel["district_id"]).issubset(set(config.DISTRICT_IDS))


def test_panel_values_are_physically_plausible(panel):
    assert (panel["cases"] >= 0).all(), "negative case counts"
    assert (panel["population"] > 0).all()
    assert (panel["rain_mm"] >= 0).all(), "negative rainfall"
    assert (panel["tmin"] <= panel["tmax"]).all(), "tmin exceeds tmax"
    assert panel["rh"].between(0, 100).all(), "relative humidity outside 0-100%"


def test_high_risk_flag_is_nullable_boolean(panel):
    """Null must be representable and distinct from False."""
    assert str(panel["high_risk_flag"].dtype) == "boolean"
    assert panel["high_risk_flag"].isna().any(), "generator should emit some unknown weeks"
    assert panel["high_risk_flag"].notna().any()


def test_panel_roundtrips_through_parquet(panel, tmp_path):
    """iso_week is a Period, which Parquet cannot hold natively."""
    path = tmp_path / "panel.parquet"
    write_panel(panel, path)
    restored = read_panel(path)

    assert list(restored.columns) == list(config.PANEL_COLUMNS)
    assert str(restored["iso_week"].dtype) == config.PANEL_DTYPES["iso_week"]
    pd.testing.assert_frame_equal(panel, restored)


def test_coerce_schema_rejects_missing_columns_when_strict():
    frame = pd.DataFrame({"district_id": ["colombo"], "iso_week": ["2024-01-01"]})
    with pytest.raises(ValueError, match="missing required columns"):
        coerce_panel_schema(frame, strict=True)


def test_coerce_schema_fills_missing_columns_when_not_strict():
    frame = pd.DataFrame(
        {
            "district_id": ["colombo"],
            "iso_week": ["2024-01-01"],
            "cases": [10],
            "population": [2_477_000],
        }
    )
    out = coerce_panel_schema(frame, strict=False)
    assert list(out.columns) == list(config.PANEL_COLUMNS)
    assert out["high_risk_flag"].isna().all()


def test_synthetic_panel_is_reproducible():
    a = make_synthetic_panel(n_districts=4, n_weeks=60, seed=99)
    b = make_synthetic_panel(n_districts=4, n_weeks=60, seed=99)
    pd.testing.assert_frame_equal(a, b)


def test_synthetic_panel_refuses_to_invent_districts():
    """Guard against fabricating administrative units that do not exist."""
    with pytest.raises(ValueError, match="Refusing to invent districts"):
        make_synthetic_panel(n_districts=40, n_weeks=60)


def test_synthetic_panel_has_bimodal_seasonality():
    """Two monsoon-aligned peaks, not one."""
    panel = make_synthetic_panel(n_districts=25, n_weeks=520, seed=3)
    weeks = panel["iso_week"].dt.start_time.dt.isocalendar().week
    by_week = panel.assign(woy=weeks.to_numpy()).groupby("woy")["cases"].mean()

    # Mid-year (southwest monsoon) and year-end (northeast monsoon) both need to
    # sit clearly above the shoulder season between them.
    mid_year = by_week.loc[22:32].mean()
    year_end = pd.concat([by_week.loc[48:52], by_week.loc[1:3]]).mean()
    shoulder = by_week.loc[36:44].mean()

    assert mid_year > shoulder, "no southwest-monsoon peak"
    assert year_end > shoulder, "no northeast-monsoon peak"
