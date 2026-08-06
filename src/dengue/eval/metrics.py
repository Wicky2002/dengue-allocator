"""Forecast evaluation metrics.

Covers three things a decision system has to get right, which are not the same
thing:

1. **Calibration of the whole predictive distribution** -- :func:`pinball_loss`.
   This is the primary metric. A forecast that is usually close but occasionally
   catastrophically overconfident is worse for allocation than one that is
   consistently honest about its uncertainty, and only a proper scoring rule
   penalises that correctly.
2. **Interval reliability** -- :func:`interval_coverage`. An 80% interval that
   covers 55% of outcomes is not an 80% interval, and Stage 3's risk-averse
   variant would silently under-allocate if it trusted one.
3. **Point accuracy** -- :func:`mae` and :func:`mape` on the median, for
   comparability with the published dengue-forecasting literature, which is
   almost entirely point-based.

Plus operational detection metrics -- :func:`high_risk_metrics` -- because what
NDCU actually acts on is "which districts need teams next month", and **lead
time** is the quantity that determines whether a forecast is useful at all. A
perfectly accurate forecast delivered the same week as the outbreak has zero
operational value.

All functions accept and return plain numpy/pandas and are null-safe: missing
observations are excluded pairwise rather than imputed.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from dengue import config
from dengue.utils.logging import get_logger

log = get_logger(__name__)


def _aligned(y_true: np.ndarray, y_pred: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Drop pairs where either side is null or non-finite."""
    y_true = np.asarray(y_true, dtype="float64")
    y_pred = np.asarray(y_pred, dtype="float64")
    if y_true.shape != y_pred.shape:
        raise ValueError(f"Shape mismatch: y_true {y_true.shape} vs y_pred {y_pred.shape}")
    mask = np.isfinite(y_true) & np.isfinite(y_pred)
    return y_true[mask], y_pred[mask]


def pinball_loss(y_true: np.ndarray, y_pred: np.ndarray, quantile: float) -> float:
    """Mean pinball (quantile) loss.

    .. math::
        L_\\tau(y, \\hat{y}) = \\begin{cases}
            \\tau (y - \\hat{y}) & y \\ge \\hat{y} \\\\
            (1 - \\tau)(\\hat{y} - y) & y < \\hat{y}
        \\end{cases}

    This is the proper scoring rule for a single quantile: it is minimised in
    expectation exactly when :math:`\\hat{y}` is the true :math:`\\tau`-quantile.
    Averaging it across quantiles approximates the CRPS, which is why it is the
    headline metric here.

    Lower is better. Units are cases.

    Examples
    --------
    >>> round(pinball_loss(np.array([10.0]), np.array([8.0]), 0.5), 3)
    1.0
    """
    if not 0.0 < quantile < 1.0:
        raise ValueError(f"quantile must be in (0, 1), got {quantile}")
    y_true, y_pred = _aligned(y_true, y_pred)
    if y_true.size == 0:
        return float("nan")
    delta = y_true - y_pred
    return float(np.mean(np.maximum(quantile * delta, (quantile - 1.0) * delta)))


def mean_pinball_across_quantiles(
    y_true: np.ndarray, predictions: dict[float, np.ndarray]
) -> float:
    """Mean pinball loss averaged over quantiles -- a CRPS approximation."""
    losses = [pinball_loss(y_true, pred, q) for q, pred in predictions.items()]
    finite = [x for x in losses if np.isfinite(x)]
    return float(np.mean(finite)) if finite else float("nan")


def interval_coverage(y_true: np.ndarray, lower: np.ndarray, upper: np.ndarray) -> float:
    """Empirical coverage of a prediction interval, in ``[0, 1]``.

    Compare against :data:`dengue.config.PI_NOMINAL_COVERAGE` (0.80). Materially
    below nominal means overconfident intervals; materially above means the model
    is hedging and the intervals are uninformative.
    """
    y_true = np.asarray(y_true, dtype="float64")
    lower = np.asarray(lower, dtype="float64")
    upper = np.asarray(upper, dtype="float64")
    mask = np.isfinite(y_true) & np.isfinite(lower) & np.isfinite(upper)
    if mask.sum() == 0:
        return float("nan")
    inside = (y_true[mask] >= lower[mask]) & (y_true[mask] <= upper[mask])
    return float(np.mean(inside))


def interval_width(lower: np.ndarray, upper: np.ndarray) -> float:
    """Mean prediction-interval width, in cases.

    Reported alongside coverage because coverage alone is trivially gamed: an
    interval of ``[0, inf)`` has perfect coverage and no value.
    """
    lower = np.asarray(lower, dtype="float64")
    upper = np.asarray(upper, dtype="float64")
    mask = np.isfinite(lower) & np.isfinite(upper)
    if mask.sum() == 0:
        return float("nan")
    return float(np.mean(upper[mask] - lower[mask]))


def mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Mean absolute error on the median forecast, in cases."""
    y_true, y_pred = _aligned(y_true, y_pred)
    if y_true.size == 0:
        return float("nan")
    return float(np.mean(np.abs(y_true - y_pred)))


def mape(y_true: np.ndarray, y_pred: np.ndarray, *, epsilon: float = 1.0) -> float:
    """Mean absolute percentage error on the median, as a percentage.

    Parameters
    ----------
    epsilon:
        Added to the denominator so weeks with zero notified cases do not make
        the metric infinite. Low-burden districts have genuine zero weeks, so
        dropping them instead would bias MAPE toward the high-burden districts
        that are easiest to predict.

    Notes
    -----
    MAPE is reported for comparability with the literature, but it is
    asymmetric -- it punishes over-prediction more than under-prediction. For
    outbreak response, under-prediction is the more costly error, so MAPE's bias
    runs the wrong way. Prefer the pinball loss when the two disagree.
    """
    y_true, y_pred = _aligned(y_true, y_pred)
    if y_true.size == 0:
        return float("nan")
    return float(np.mean(np.abs(y_true - y_pred) / (np.abs(y_true) + epsilon)) * 100.0)


def rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Root mean squared error on the median, in cases."""
    y_true, y_pred = _aligned(y_true, y_pred)
    if y_true.size == 0:
        return float("nan")
    return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))


def high_risk_metrics(
    predictions: pd.DataFrame,
    actuals: pd.DataFrame,
    *,
    top_k: int = 6,
    quantile_column: str = "q0.5",
) -> dict[str, float]:
    """Precision, recall and mean lead time for high-risk district detection.

    A district-week is *predicted* high-risk when its forecast incidence ranks in
    the top ``top_k`` for that target week -- mirroring how NDCU designates a
    fixed number of priority areas rather than applying an absolute threshold.

    **Lead time** is measured against outbreak *onsets*: weeks where a district
    becomes high-risk having not been so the week before. For each onset, the
    lead time is the longest horizon at which the model already flagged it. Onsets
    never flagged at any horizon count as misses against recall and contribute no
    lead time. This is the operationally meaningful definition: it answers "how
    much warning did we get before this district became a problem?", not "how
    often were we right about a district that was already obviously in trouble?".

    Parameters
    ----------
    predictions:
        Long frame with ``district_id``, ``target_week``, ``horizon`` and the
        quantile column.
    actuals:
        Panel with ``district_id``, ``iso_week``, ``cases``, ``population`` and
        ``high_risk_flag``.
    top_k:
        Number of districts designated high-risk per week.
    quantile_column:
        Which forecast quantile drives the designation. The median is the neutral
        choice; ``q0.9`` would give a more precautionary designation.

    Returns
    -------
    dict
        ``high_risk_precision``, ``high_risk_recall``, ``high_risk_f1``,
        ``mean_lead_time_weeks``, ``n_onsets``, ``n_onsets_detected``. Values are
        ``nan`` when the panel carries no high-risk labels at all, which is the
        case for colmozzie-only data.
    """
    empty = {
        "high_risk_precision": float("nan"),
        "high_risk_recall": float("nan"),
        "high_risk_f1": float("nan"),
        "mean_lead_time_weeks": float("nan"),
        "n_onsets": 0.0,
        "n_onsets_detected": 0.0,
    }

    if predictions.empty or actuals.empty or "high_risk_flag" not in actuals.columns:
        return empty

    truth = actuals[["district_id", "iso_week", "high_risk_flag"]].copy()
    truth = truth[truth["high_risk_flag"].notna()]
    if truth.empty:
        log.debug("high_risk_metrics: panel carries no high-risk labels")
        return empty

    truth["high_risk_flag"] = truth["high_risk_flag"].astype(bool)
    truth = truth.rename(columns={"iso_week": "target_week"})

    populations = actuals.drop_duplicates("district_id").set_index("district_id")["population"]

    predicted = predictions.copy()
    predicted["_pop"] = predicted["district_id"].map(populations).astype("float64")
    predicted["_incidence"] = predicted[quantile_column] / predicted["_pop"] * 100_000.0

    # Rank within (target_week, horizon): each horizon designates its own top-k.
    predicted["_rank"] = predicted.groupby(["target_week", "horizon"], observed=True)[
        "_incidence"
    ].rank(ascending=False, method="first")
    predicted["predicted_high_risk"] = predicted["_rank"] <= top_k

    merged = predicted.merge(truth, on=["district_id", "target_week"], how="inner")
    if merged.empty:
        return empty

    tp = int(((merged["predicted_high_risk"]) & (merged["high_risk_flag"])).sum())
    fp = int(((merged["predicted_high_risk"]) & (~merged["high_risk_flag"])).sum())
    fn = int(((~merged["predicted_high_risk"]) & (merged["high_risk_flag"])).sum())

    precision = tp / (tp + fp) if (tp + fp) else float("nan")
    recall = tp / (tp + fn) if (tp + fn) else float("nan")
    if np.isfinite(precision) and np.isfinite(recall) and (precision + recall) > 0:
        f1 = 2 * precision * recall / (precision + recall)
    else:
        f1 = float("nan")

    # ---- lead time on onsets ---------------------------------------------
    onset_source = truth.sort_values(["district_id", "target_week"]).copy()
    previous = onset_source.groupby("district_id", observed=True)["high_risk_flag"].shift(1)
    # A district's first observed week counts as an onset if it is high-risk:
    # there is no prior week to have been high-risk in. Cast to bool explicitly
    # rather than relying on fillna's deprecated object-dtype downcasting.
    previous = previous.astype("boolean").fillna(False).astype(bool)
    onset_source["is_onset"] = onset_source["high_risk_flag"].to_numpy(dtype=bool) & ~previous
    onsets = onset_source[onset_source["is_onset"]][["district_id", "target_week"]]

    lead_times: list[int] = []
    n_detected = 0
    if not onsets.empty:
        flagged = merged[merged["predicted_high_risk"]]
        by_key = flagged.groupby(["district_id", "target_week"], observed=True)["horizon"].max()
        for row in onsets.itertuples(index=False):
            key = (row.district_id, row.target_week)
            if key in by_key.index:
                lead_times.append(int(by_key.loc[key]))
                n_detected += 1

    mean_lead = float(np.mean(lead_times)) if lead_times else float("nan")

    return {
        "high_risk_precision": precision,
        "high_risk_recall": recall,
        "high_risk_f1": f1,
        "mean_lead_time_weeks": mean_lead,
        "n_onsets": float(len(onsets)),
        "n_onsets_detected": float(n_detected),
    }


def evaluate_predictions(
    predictions: pd.DataFrame,
    actuals: pd.DataFrame,
    *,
    include_high_risk: bool = True,
    top_k: int = 6,
) -> dict[str, float]:
    """Compute the full metric suite for one (model, horizon) slice.

    Parameters
    ----------
    predictions:
        Frame with ``district_id``, ``target_week``, ``horizon`` and quantile
        columns ``q0.1`` / ``q0.5`` / ``q0.9``.
    actuals:
        Panel with ``district_id``, ``iso_week``, ``cases``.
    include_high_risk:
        Whether to compute detection metrics.
    top_k:
        Districts designated high-risk per week.

    Returns
    -------
    dict
        Metric name to value. Always includes ``n_predictions`` so that a metric
        computed on a handful of rows is visible as such.
    """
    if predictions.empty:
        return {"n_predictions": 0.0}

    truth = actuals[["district_id", "iso_week", "cases"]].rename(
        columns={"iso_week": "target_week", "cases": "y_true"}
    )
    merged = predictions.merge(truth, on=["district_id", "target_week"], how="inner")

    if merged.empty:
        log.warning("evaluate_predictions: no predictions aligned to observed weeks")
        return {"n_predictions": 0.0}

    y_true = merged["y_true"].astype("float64").to_numpy()
    quantile_predictions = {
        q: merged[f"q{q}"].astype("float64").to_numpy() for q in config.QUANTILES
    }
    median = quantile_predictions[0.5]
    lower, upper = quantile_predictions[0.1], quantile_predictions[0.9]

    results: dict[str, float] = {
        "n_predictions": float(len(merged)),
        "pinball_mean": mean_pinball_across_quantiles(y_true, quantile_predictions),
        "coverage_80": interval_coverage(y_true, lower, upper),
        "interval_width": interval_width(lower, upper),
        "mae": mae(y_true, median),
        "mape": mape(y_true, median),
        "rmse": rmse(y_true, median),
    }
    for q in config.QUANTILES:
        results[f"pinball_q{q}"] = pinball_loss(y_true, quantile_predictions[q], q)

    if include_high_risk:
        results.update(high_risk_metrics(predictions, actuals, top_k=top_k))

    return results


#: Metric direction, for pretty-printing and for picking a winner.
#: True means lower is better.
LOWER_IS_BETTER: dict[str, bool] = {
    "pinball_mean": True,
    "pinball_q0.1": True,
    "pinball_q0.5": True,
    "pinball_q0.9": True,
    "mae": True,
    "mape": True,
    "rmse": True,
    "interval_width": True,
    "coverage_80": False,
    "high_risk_precision": False,
    "high_risk_recall": False,
    "high_risk_f1": False,
    "mean_lead_time_weeks": False,
}
