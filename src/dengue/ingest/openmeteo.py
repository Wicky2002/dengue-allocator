"""Ingest daily reanalysis weather from the Open-Meteo Archive API.

One point query per district centroid, daily variables, aggregated to ISO weeks.
No API key is required for the free non-commercial tier.

Source
------
https://archive-api.open-meteo.com/v1/archive -- ERA5 / ERA5-Land reanalysis.
Licence: CC-BY-4.0 (attribution required; see README provenance table).

Weekly aggregation
------------------
============================  ==========  =================================
daily variable                panel       weekly aggregation
============================  ==========  =================================
``precipitation_sum``         ``rain_mm``  **sum** -- total water input over
                                           the week is what creates breeding
                                           habitat
``temperature_2m_max``        ``tmax``     **mean of daily maxima**
``temperature_2m_min``        ``tmin``     **mean of daily minima**
``relative_humidity_2m_mean`` ``rh``       **mean**
============================  ==========  =================================

Mean-of-daily-extremes (rather than the week's single hottest hour) matches how
``colmozzie`` encodes ``TMAX``/``Tm``, so the two sources are directly
comparable when they overlap. Partial weeks at either end of the requested range
are dropped rather than emitted with an under-counted rainfall sum -- a
half-observed week would look like a drought.
"""

from __future__ import annotations

import datetime as dt
import time
from pathlib import Path

import pandas as pd

from dengue import config
from dengue.utils.io import IngestError, fetch_json_cached
from dengue.utils.logging import get_logger, log_frame

log = get_logger(__name__)

DAILY_VARIABLES = (
    "precipitation_sum",
    "temperature_2m_max",
    "temperature_2m_min",
    "relative_humidity_2m_mean",
)

#: Rename map from Open-Meteo daily variables to panel column names.
_RENAME = {
    "precipitation_sum": "rain_mm",
    "temperature_2m_max": "tmax",
    "temperature_2m_min": "tmin",
    "relative_humidity_2m_mean": "rh",
}

#: Weekly aggregation rule per panel column. See module docstring.
_WEEKLY_AGG = {"rain_mm": "sum", "tmax": "mean", "tmin": "mean", "rh": "mean"}

DEFAULT_START = "2010-01-01"

#: ERA5 reanalysis lags real time by roughly five days. Requesting closer than
#: this returns nulls, which would otherwise look like missing weather.
ARCHIVE_LAG_DAYS = 6

OPENMETEO_LICENCE = "CC-BY-4.0"

#: Pause between per-district requests. Confirmed empirically: 16 sequential,
#: unpaced district requests triggered a 429 on the 17th -- the free tier
#: rate-limits bursts, not just sustained volume.
_REQUEST_DELAY_SECONDS = 1.0


def default_end_date() -> str:
    """Latest date the archive can be expected to have, as ``YYYY-MM-DD``."""
    return (dt.date.today() - dt.timedelta(days=ARCHIVE_LAG_DAYS)).isoformat()


def fetch_district_daily(
    district_id: str,
    start_date: str = DEFAULT_START,
    end_date: str | None = None,
    *,
    refresh: bool = False,
) -> pd.DataFrame:
    """Fetch the daily series for one district centroid.

    The raw JSON response is cached under ``data/raw/openmeteo/``, keyed on the
    full request URL, so re-runs with identical arguments make no network calls.

    Returns
    -------
    pandas.DataFrame
        Columns ``date``, ``rain_mm``, ``tmax``, ``tmin``, ``rh``.
    """
    district = config.get_district(district_id)
    end_date = end_date or default_end_date()

    params = {
        "latitude": district.lat,
        "longitude": district.lon,
        "start_date": start_date,
        "end_date": end_date,
        "daily": ",".join(DAILY_VARIABLES),
        "timezone": "Asia/Colombo",
    }
    payload = fetch_json_cached(
        config.OPENMETEO_BASE_URL,
        params=params,
        cache_dir=config.RAW_OPENMETEO,
        refresh=refresh,
    )

    if "daily" not in payload:
        reason = payload.get("reason", payload)
        raise IngestError(f"Open-Meteo returned no daily block for {district_id}: {reason}")

    daily = payload["daily"]
    missing = [v for v in ("time", *DAILY_VARIABLES) if v not in daily]
    if missing:
        raise IngestError(
            f"Open-Meteo response for {district_id} is missing variables {missing}. "
            "The API's daily variable names may have changed."
        )

    frame = pd.DataFrame(
        {
            "date": pd.to_datetime(daily["time"]),
            **{_RENAME[v]: daily[v] for v in DAILY_VARIABLES},
        }
    )
    frame.insert(0, "district_id", district_id)
    return frame


def to_iso_weeks(daily: pd.DataFrame, *, drop_partial: bool = True) -> pd.DataFrame:
    """Aggregate a daily frame to complete ISO weeks.

    Parameters
    ----------
    daily:
        Output of :func:`fetch_district_daily` (may span several districts).
    drop_partial:
        If True (default), drop weeks that do not have all 7 days present. A
        partial week would understate ``rain_mm``, which is a summed quantity.
    """
    frame = daily.copy()
    frame["iso_week"] = pd.PeriodIndex(frame["date"], freq=config.WEEK_FREQ)

    grouped = frame.groupby(["district_id", "iso_week"], observed=True)
    weekly = grouped.agg(**{col: (col, how) for col, how in _WEEKLY_AGG.items()}).reset_index()
    weekly["n_days"] = grouped.size().to_numpy()

    if drop_partial:
        n_partial = int((weekly["n_days"] < 7).sum())
        if n_partial:
            log.info("open-meteo: dropping %d partial ISO weeks (<7 days observed)", n_partial)
        weekly = weekly[weekly["n_days"] == 7]

    return weekly.drop(columns=["n_days"]).reset_index(drop=True)


def load(
    district_ids: list[str] | None = None,
    start_date: str = DEFAULT_START,
    end_date: str | None = None,
    *,
    refresh: bool = False,
) -> pd.DataFrame:
    """Fetch and weekly-aggregate weather for every district.

    Returns
    -------
    pandas.DataFrame
        Columns ``district_id``, ``iso_week``, ``rain_mm``, ``tmax``, ``tmin``,
        ``rh``. This is a *weather* frame, not a full panel -- it carries no
        ``cases``. ``features.build_panel`` joins it to the case data.

    Raises
    ------
    IngestError
        If any district fails. Weather is a covariate for every district, so a
        partial fetch would silently bias the panel toward whichever districts
        happened to succeed.
    """
    config.ensure_dirs()
    district_ids = district_ids or list(config.DISTRICT_IDS)
    end_date = end_date or default_end_date()

    log.info(
        "open-meteo: fetching %d districts  range=[%s .. %s]  licence=%s",
        len(district_ids),
        start_date,
        end_date,
        OPENMETEO_LICENCE,
    )

    frames: list[pd.DataFrame] = []
    for i, district_id in enumerate(district_ids, start=1):
        frame = fetch_district_daily(district_id, start_date, end_date, refresh=refresh)
        frames.append(frame)
        log.debug(
            "open-meteo: [%2d/%d] %-14s days=%d", i, len(district_ids), district_id, len(frame)
        )
        if i < len(district_ids):
            time.sleep(_REQUEST_DELAY_SECONDS)

    daily = pd.concat(frames, ignore_index=True)
    log.info(
        "open-meteo: daily rows=%d  districts=%d  dates=[%s .. %s]",
        len(daily),
        daily["district_id"].nunique(),
        daily["date"].min().date(),
        daily["date"].max().date(),
    )

    weekly = to_iso_weeks(daily)
    log_frame(log, weekly, "open-meteo:weekly")

    n_null = int(weekly[["rain_mm", "tmax", "tmin", "rh"]].isna().sum().sum())
    if n_null:
        log.warning("open-meteo: %d null weather values remain after aggregation", n_null)

    return weekly


def main(out: Path | None = None) -> Path:  # pragma: no cover - CLI entry point
    config.ensure_dirs()
    weekly = load()
    out = out or config.INTERIM_DIR / "weather_weekly.parquet"
    to_write = weekly.copy()
    to_write["iso_week"] = to_write["iso_week"].dt.start_time.dt.strftime("%Y-%m-%d")
    to_write.to_parquet(out, index=False)
    log.info("open-meteo: wrote %s", out)
    return out


if __name__ == "__main__":  # pragma: no cover
    main()
