"""Build the model matrix from the district-week panel.

Leakage policy
--------------
**Every feature for district *d* at week *t* is computed only from observations
at weeks <= t.** Concretely, every derived column is produced by a
``groupby("district_id")`` followed by a ``shift(k >= 1)`` and, where a window is
involved, a *trailing* window over already-shifted values. No centred windows,
no ``bfill``, no whole-series statistics (means, scalers) computed across the
train/test boundary.

The property this buys is testable, and ``tests/test_no_leakage.py`` tests it
directly: truncating the panel at any week ``T`` and rebuilding must reproduce
the full-panel features exactly for every row at or before ``T``. If a feature
peeked ahead, the truncated rebuild would differ. That test is stronger than
inspecting shifts by eye, because it catches leakage introduced anywhere in the
pipeline, including in code added later.

Targets are the only forward-looking columns, which is what they are for:
``y_h{h} = log1p(cases)`` at ``t + h``. They are named with a ``y_`` prefix and
must never be fed back in as features.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from dengue import config
from dengue.utils.io import IngestError, write_panel
from dengue.utils.logging import get_logger, log_frame

log = get_logger(__name__)

# --- feature-generation constants ----------------------------------------

CASE_LAGS = tuple(range(1, 9))  # log1p case lags 1..8
ROLLING_WINDOWS = (4, 8)  # rolling mean/std windows, in weeks
RAIN_LAGS = tuple(range(2, 11))  # rainfall lags 2..10
RAIN_CUM_WINDOW = 4  # trailing cumulative rainfall, weeks
CLIMATE_LAGS = tuple(range(2, 9))  # tmax/tmin/rh lags 2..8
CLIMATE_VARS = ("tmax", "tmin", "rh")
NEIGHBOUR_LAG = 1  # lag on neighbours' incidence

#: Prefix marking forward-looking target columns. Never use as a feature.
TARGET_PREFIX = "y_h"

#: Monsoon phases by ISO week. Sri Lanka's four-season convention.
MONSOON_PHASES = {
    "first_inter_monsoon": range(9, 19),  # Mar-Apr
    "southwest_monsoon": range(19, 40),  # May-Sep (Yala)
    "second_inter_monsoon": range(40, 49),  # Oct-Nov
    # Northeast monsoon (Maha, Dec-Feb) is the wrap-around remainder.
}


def monsoon_phase(week_of_year: int) -> str:
    """Return the monsoon phase for an ISO week number."""
    for phase, weeks in MONSOON_PHASES.items():
        if week_of_year in weeks:
            return phase
    return "northeast_monsoon"


def _neighbour_matrix(district_ids: list[str]) -> pd.DataFrame:
    """Row-normalised adjacency matrix restricted to ``district_ids``.

    Row-normalising turns the matrix product into a *mean* over neighbours, so
    districts with many borders (Anuradhapura has eight) are not systematically
    scaled up relative to districts with one (Jaffna).
    """
    adjacency = config.adjacency_map()
    index = {d: i for i, d in enumerate(district_ids)}
    matrix = np.zeros((len(district_ids), len(district_ids)), dtype=float)

    for district, neighbours in adjacency.items():
        if district not in index:
            continue
        present = [n for n in neighbours if n in index]
        if not present:
            continue
        weight = 1.0 / len(present)
        for neighbour in present:
            matrix[index[district], index[neighbour]] = weight

    return pd.DataFrame(matrix, index=district_ids, columns=district_ids)


def _add_neighbour_features(frame: pd.DataFrame) -> pd.DataFrame:
    """Add the neighbour-weighted mean of lagged log incidence.

    Built from the *lagged* incidence of adjacent districts, so it encodes "my
    neighbours were rising last week" without ever touching week ``t``.
    """
    out = frame.copy()
    district_ids = sorted(out["district_id"].unique())

    # Cast off nullable extension dtypes (Int64) immediately: they propagate
    # into object-dtype numpy arrays, where the matrix arithmetic below silently
    # misbehaves and LightGBM refuses the resulting features outright.
    cases = out["cases"].astype("float64")
    population = out["population"].astype("float64")
    incidence = cases / population * 100_000.0
    out["_log_incidence"] = np.log1p(incidence)
    out["_log_incidence_lag"] = out.groupby("district_id", observed=True)["_log_incidence"].shift(
        NEIGHBOUR_LAG
    )

    wide = out.pivot_table(
        index="iso_week", columns="district_id", values="_log_incidence_lag", observed=True
    )
    wide = wide.reindex(columns=district_ids)

    weights = _neighbour_matrix(district_ids)
    # Treat an unobserved neighbour as absent rather than as zero incidence:
    # fill with 0 but renormalise by the weight actually present.
    present = wide.notna().astype(float)
    weight_matrix = weights.to_numpy(dtype=float).T
    numerator = wide.fillna(0.0).to_numpy(dtype=float) @ weight_matrix
    denominator = present.to_numpy(dtype=float) @ weight_matrix
    with np.errstate(invalid="ignore", divide="ignore"):
        neighbour_mean = np.where(denominator > 0, numerator / denominator, np.nan)

    neighbour_frame = pd.DataFrame(neighbour_mean, index=wide.index, columns=district_ids).stack(
        future_stack=True
    )
    neighbour_frame.index.names = ["iso_week", "district_id"]
    neighbour_frame = neighbour_frame.rename("neighbour_log_incidence_lag1").reset_index()

    out = out.merge(neighbour_frame, on=["iso_week", "district_id"], how="left")
    return out.drop(columns=["_log_incidence", "_log_incidence_lag"])


def build_features(
    panel: pd.DataFrame,
    *,
    horizons: tuple[int, ...] = config.HORIZONS,
    dropna_targets: bool = False,
) -> pd.DataFrame:
    """Build the leakage-safe model matrix from a district-week panel.

    Parameters
    ----------
    panel:
        A frame conforming to :data:`dengue.config.PANEL_DTYPES`.
    horizons:
        Forecast horizons in weeks. One ``y_h{h}`` target column per horizon.
    dropna_targets:
        If True, drop rows where any target is null (the final ``max(horizons)``
        weeks). Leave False for inference, where those rows are exactly the ones
        being predicted.

    Returns
    -------
    pandas.DataFrame
        The panel columns plus engineered features and ``y_h*`` targets, sorted
        by ``(district_id, iso_week)``.

    Notes
    -----
    Rows near the start of each district's series carry nulls for the longer
    lags. They are deliberately kept: LightGBM handles nulls natively, and
    dropping them would discard the earliest weeks of every district.
    """
    required = {"district_id", "iso_week", "cases", "population"}
    missing = required - set(panel.columns)
    if missing:
        raise ValueError(f"Panel is missing columns required for features: {sorted(missing)}")

    frame = panel.sort_values(["district_id", "iso_week"]).reset_index(drop=True).copy()

    # ---- case history -----------------------------------------------------
    frame["log_cases"] = np.log1p(frame["cases"].astype("float64"))
    log_cases = frame.groupby("district_id", observed=True)["log_cases"]

    for lag in CASE_LAGS:
        frame[f"log_cases_lag{lag}"] = log_cases.shift(lag)

    # Rolling statistics over ALREADY-LAGGED values: the window ends at t-1.
    lag1 = frame.groupby("district_id", observed=True)["log_cases"].shift(1)
    frame["_log_cases_lag1"] = lag1
    for window in ROLLING_WINDOWS:
        rolled = frame.groupby("district_id", observed=True)["_log_cases_lag1"].rolling(
            window, min_periods=max(2, window // 2)
        )
        frame[f"log_cases_roll{window}_mean"] = rolled.mean().reset_index(level=0, drop=True)
        frame[f"log_cases_roll{window}_std"] = rolled.std().reset_index(level=0, drop=True)

    # Week-over-week growth ratio, on counts at t-1 vs t-2. The +1 keeps it
    # defined through zero-case weeks, which are common in low-burden districts.
    cases_lag1 = frame.groupby("district_id", observed=True)["cases"].shift(1).astype("float64")
    cases_lag2 = frame.groupby("district_id", observed=True)["cases"].shift(2).astype("float64")
    frame["growth_ratio_wow"] = (cases_lag1 + 1.0) / (cases_lag2 + 1.0)
    frame["log_growth_ratio_wow"] = np.log(frame["growth_ratio_wow"])

    # ---- climate ----------------------------------------------------------
    rain = frame.groupby("district_id", observed=True)["rain_mm"]
    for lag in RAIN_LAGS:
        frame[f"rain_lag{lag}"] = rain.shift(lag)

    # Trailing cumulative rainfall over weeks t-1 .. t-RAIN_CUM_WINDOW.
    frame["_rain_lag1"] = frame.groupby("district_id", observed=True)["rain_mm"].shift(1)
    frame[f"rain_cum{RAIN_CUM_WINDOW}"] = (
        frame.groupby("district_id", observed=True)["_rain_lag1"]
        .rolling(RAIN_CUM_WINDOW, min_periods=1)
        .sum()
        .reset_index(level=0, drop=True)
    )

    for var in CLIMATE_VARS:
        series = frame.groupby("district_id", observed=True)[var]
        for lag in CLIMATE_LAGS:
            frame[f"{var}_lag{lag}"] = series.shift(lag)

    # ---- seasonality ------------------------------------------------------
    week_of_year = frame["iso_week"].dt.start_time.dt.isocalendar().week.astype(int)
    frame["week_of_year"] = week_of_year
    frame["sin_week"] = np.sin(2 * np.pi * week_of_year / 52.0)
    frame["cos_week"] = np.cos(2 * np.pi * week_of_year / 52.0)
    frame["monsoon_phase"] = pd.Categorical(
        [monsoon_phase(w) for w in week_of_year],
        categories=[*MONSOON_PHASES.keys(), "northeast_monsoon"],
    )

    # ---- static district attributes --------------------------------------
    densities = config.densities()
    frame["log_pop_density"] = np.log(frame["district_id"].map(densities).astype("float64"))
    frame["log_population"] = np.log(frame["population"].astype("float64"))
    frame["district_id"] = frame["district_id"].astype("category")

    # ---- spatial ----------------------------------------------------------
    frame["district_id"] = frame["district_id"].astype("string")
    frame = _add_neighbour_features(frame)
    frame["district_id"] = frame["district_id"].astype("category")

    # ---- targets (the ONLY forward-looking columns) -----------------------
    for h in horizons:
        frame[f"{TARGET_PREFIX}{h}"] = frame.groupby("district_id", observed=True)[
            "log_cases"
        ].shift(-h)
        frame[f"target_cases_h{h}"] = frame.groupby("district_id", observed=True)["cases"].shift(-h)

    frame = frame.drop(columns=["_log_cases_lag1", "_rain_lag1"])

    # Normalise every numeric feature to plain float64. pandas' nullable dtypes
    # (Int64, Float64, boolean) propagate through arithmetic and end up as
    # object arrays in numpy, which LightGBM rejects with an opaque "pandas
    # dtypes must be int, float or bool". Doing it once here means no model has
    # to defend against it. Categoricals and the panel's own columns are left
    # alone -- the schema contract owns those.
    for column in feature_columns(frame):
        series = frame[column]
        if isinstance(series.dtype, pd.CategoricalDtype):
            continue
        if pd.api.types.is_numeric_dtype(series) or pd.api.types.is_bool_dtype(series):
            frame[column] = pd.to_numeric(series, errors="coerce").astype("float64")

    if dropna_targets:
        target_columns = [f"{TARGET_PREFIX}{h}" for h in horizons]
        before = len(frame)
        frame = frame.dropna(subset=target_columns)
        log.info("features: dropped %d rows with null targets", before - len(frame))

    frame = frame.sort_values(["district_id", "iso_week"]).reset_index(drop=True)
    log.info(
        "features: built matrix  rows=%d  features=%d  horizons=%s",
        len(frame),
        len(feature_columns(frame)),
        list(horizons),
    )
    return frame


def feature_columns(frame: pd.DataFrame) -> list[str]:
    """Return the model-input columns: everything that is not a target or raw.

    Excludes the raw contemporaneous observations (``cases``, ``rain_mm``, ...)
    because those describe week ``t`` itself. Only their lagged derivatives are
    legitimate inputs for predicting ``t + h``.
    """
    excluded = {
        "iso_week",
        "cases",
        "log_cases",
        "population",
        "rain_mm",
        "tmax",
        "tmin",
        "rh",
        "high_risk_flag",
        "growth_ratio_wow",  # keep only the log version; they are redundant
    }
    return [
        c
        for c in frame.columns
        if c not in excluded
        and not c.startswith(TARGET_PREFIX)
        and not c.startswith("target_cases_h")
    ]


def categorical_columns(frame: pd.DataFrame) -> list[str]:
    """Categorical feature columns, for LightGBM's native categorical handling."""
    return [c for c in ("district_id", "monsoon_phase") if c in frame.columns]


# --------------------------------------------------------------------------
# Panel assembly
# --------------------------------------------------------------------------


def assemble_panel(*, use_synthetic: bool = False, refresh: bool = False) -> pd.DataFrame:
    """Assemble ``data/processed/panel.parquet`` from the real sources.

    Joins case data to Open-Meteo weather on ``(district_id, iso_week)``.

    Parameters
    ----------
    use_synthetic:
        Skip ingest entirely and generate the synthetic panel.
    refresh:
        Bypass the raw HTTP caches.

    Notes
    -----
    On ingest failure this logs the error loudly and falls back to the synthetic
    panel, clearly labelled. It never fabricates case numbers: the fallback is a
    wholly simulated panel, not real data with gaps filled in.
    """
    from dengue.utils.synthetic import make_synthetic_panel

    if use_synthetic:
        log.warning("panel: building from SYNTHETIC data (--synthetic requested)")
        return make_synthetic_panel()

    try:
        from dengue.ingest import colmozzie, openmeteo

        cases = colmozzie.load(refresh=refresh)
        log_frame(log, cases, "panel:cases(colmozzie)")

        districts = sorted(cases["district_id"].unique())
        start = cases["iso_week"].min().start_time.strftime("%Y-%m-%d")
        weather = openmeteo.load(district_ids=districts, start_date=start, refresh=refresh)

        merged = cases.merge(
            weather,
            on=["district_id", "iso_week"],
            how="left",
            suffixes=("", "_om"),
        )
        # Prefer Open-Meteo's reanalysis where colmozzie's station data is null.
        for column in ("rain_mm", "tmax", "tmin", "rh"):
            om_column = f"{column}_om"
            if om_column in merged.columns:
                merged[column] = merged[column].fillna(merged[om_column])
                merged = merged.drop(columns=[om_column])

        from dengue.utils.io import coerce_panel_schema

        panel = coerce_panel_schema(merged)
        log_frame(log, panel, "panel:assembled")

        if len(panel) < 100:
            raise IngestError(f"Assembled panel has only {len(panel)} rows; refusing to proceed")
        return panel

    except IngestError as exc:
        log.error("panel: ingest FAILED (%s)", exc)
        log.warning(
            "panel: falling back to the SYNTHETIC panel. These are simulated "
            "numbers, not observations -- do not report them as results."
        )
        return make_synthetic_panel()


def main(argv: list[str] | None = None) -> Path:
    """CLI: build the panel and write it to ``data/processed/panel.parquet``."""
    parser = argparse.ArgumentParser(description="Build the dengue district-week panel.")
    parser.add_argument(
        "--synthetic",
        action="store_true",
        help="Generate a synthetic panel instead of running ingest (fully offline).",
    )
    parser.add_argument(
        "--refresh", action="store_true", help="Bypass raw HTTP caches during ingest."
    )
    parser.add_argument(
        "--features",
        action="store_true",
        help="Also write the engineered model matrix to data/processed/features.parquet.",
    )
    args = parser.parse_args(argv)

    config.ensure_dirs()
    panel = assemble_panel(use_synthetic=args.synthetic, refresh=args.refresh)
    path = write_panel(panel)

    if args.features:
        matrix = build_features(panel)
        feature_path = config.PROCESSED_DIR / "features.parquet"
        to_write = matrix.copy()
        to_write["iso_week"] = to_write["iso_week"].dt.start_time.dt.strftime("%Y-%m-%d")
        to_write.to_parquet(feature_path, index=False)
        log.info("features: wrote %s  rows=%d", feature_path, len(to_write))

    return path


if __name__ == "__main__":  # pragma: no cover
    main()
