"""Target-leakage tests for the feature pipeline.

The central test is :func:`test_truncation_invariance`. Rather than eyeballing
shift directions, it exercises the property that actually matters:

    Rebuilding features on a panel truncated at week ``T`` must reproduce, for
    every row at or before ``T``, exactly what the full-panel build produced.

If any feature reads even one week into the future, the truncated build cannot
reproduce it, and the test fails. That holds for features added later too, which
is why it is written this way instead of asserting on specific columns.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from dengue import config
from dengue.features.build_panel import (
    TARGET_PREFIX,
    build_features,
    feature_columns,
    monsoon_phase,
)
from dengue.utils.synthetic import make_synthetic_panel


@pytest.fixture(scope="module")
def panel() -> pd.DataFrame:
    return make_synthetic_panel(n_districts=8, n_weeks=160, seed=5)


def test_truncation_invariance(panel):
    """No feature may change when future weeks are removed.

    This is the strongest available leakage check: it treats the pipeline as a
    black box and tests the causality property directly.
    """
    full = build_features(panel)

    weeks = pd.PeriodIndex(sorted(panel["iso_week"].unique()), freq=config.WEEK_FREQ)
    cutoff = weeks[int(len(weeks) * 0.7)]

    truncated = build_features(panel[panel["iso_week"] <= cutoff])

    features = feature_columns(full)
    key = ["district_id", "iso_week"]
    # district_id is both a key and a feature; keep it once.
    columns = key + [c for c in features if c not in key]

    full_slice = full[full["iso_week"] <= cutoff].sort_values(key).reset_index(drop=True)[columns]
    truncated_slice = truncated.sort_values(key).reset_index(drop=True)[columns]

    assert len(full_slice) == len(truncated_slice)

    for column in features:
        a, b = full_slice[column], truncated_slice[column]
        if pd.api.types.is_numeric_dtype(a):
            np.testing.assert_allclose(
                a.astype("float64").to_numpy(),
                b.astype("float64").to_numpy(),
                rtol=1e-9,
                atol=1e-9,
                equal_nan=True,
                err_msg=(
                    f"Feature {column!r} changed when future data was removed -- "
                    "it reads ahead of the forecast origin."
                ),
            )
        else:
            pd.testing.assert_series_equal(
                a.reset_index(drop=True),
                b.reset_index(drop=True),
                check_names=False,
                obj=f"Feature {column!r} changed under truncation",
            )


def test_lag_features_equal_manual_shift(panel):
    """Spot-check that lag k really is the value k weeks earlier."""
    matrix = build_features(panel)
    district = matrix["district_id"].astype("string").iloc[0]

    observed = (
        panel[panel["district_id"] == district].sort_values("iso_week").reset_index(drop=True)
    )
    built = (
        matrix[matrix["district_id"].astype("string") == district]
        .sort_values("iso_week")
        .reset_index(drop=True)
    )

    for lag in (1, 4, 8):
        expected = np.log1p(observed["cases"].astype("float64")).shift(lag)
        np.testing.assert_allclose(
            built[f"log_cases_lag{lag}"].astype("float64").to_numpy(),
            expected.to_numpy(),
            equal_nan=True,
            err_msg=f"log_cases_lag{lag} is misaligned",
        )


def test_no_feature_correlates_perfectly_with_its_target(panel):
    """A feature that is the target in disguise would show |r| ~= 1."""
    matrix = build_features(panel, dropna_targets=True)
    features = feature_columns(matrix)
    target = matrix[f"{TARGET_PREFIX}2"].astype("float64")

    for column in features:
        series = matrix[column]
        if not pd.api.types.is_numeric_dtype(series):
            continue
        values = series.astype("float64")
        if values.notna().sum() < 30 or values.nunique(dropna=True) < 3:
            continue
        r = np.corrcoef(values.fillna(values.mean()), target)[0, 1]
        assert abs(r) < 0.999, f"Feature {column!r} is almost identical to the target (r={r:.4f})"


def test_targets_are_the_future_and_features_are_not(panel):
    """y_h{h} must equal log1p(cases) exactly h weeks ahead."""
    matrix = build_features(panel)
    district = matrix["district_id"].astype("string").iloc[0]

    observed = (
        panel[panel["district_id"] == district].sort_values("iso_week").reset_index(drop=True)
    )
    built = (
        matrix[matrix["district_id"].astype("string") == district]
        .sort_values("iso_week")
        .reset_index(drop=True)
    )

    for h in config.HORIZONS:
        expected = np.log1p(observed["cases"].astype("float64")).shift(-h)
        np.testing.assert_allclose(
            built[f"{TARGET_PREFIX}{h}"].astype("float64").to_numpy(),
            expected.to_numpy(),
            equal_nan=True,
            err_msg=f"Target {TARGET_PREFIX}{h} is misaligned",
        )


def test_target_columns_are_excluded_from_features(panel):
    matrix = build_features(panel)
    features = feature_columns(matrix)
    assert not [c for c in features if c.startswith(TARGET_PREFIX)]
    assert not [c for c in features if c.startswith("target_cases_h")]
    # Contemporaneous observations are not inputs either.
    for column in ("cases", "log_cases", "rain_mm", "tmax", "tmin", "rh", "high_risk_flag"):
        assert column not in features, f"{column} at time t must not be a feature"


def test_neighbour_feature_uses_only_lagged_incidence(panel):
    """The spatial feature must be built from neighbours' PAST incidence."""
    matrix = build_features(panel)
    assert "neighbour_log_incidence_lag1" in matrix.columns

    # First week of every district has no lag-1 neighbour data.
    first_weeks = matrix.groupby("district_id", observed=True)["iso_week"].transform("min")
    first_rows = matrix[matrix["iso_week"] == first_weeks]
    assert first_rows["neighbour_log_incidence_lag1"].isna().all()


def test_monsoon_phase_covers_every_iso_week():
    phases = {monsoon_phase(w) for w in range(1, 54)}
    assert "southwest_monsoon" in phases
    assert "northeast_monsoon" in phases
    for week in range(1, 54):
        assert isinstance(monsoon_phase(week), str)
