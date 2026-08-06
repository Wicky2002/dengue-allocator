"""I/O helpers: HTTP with retries, raw-file caching, and panel read/write.

The panel round-trip is the important part. ``iso_week`` is a pandas ``Period``,
which Parquet cannot represent natively, so :func:`write_panel` serialises it to
an ISO date string (the week's Monday) and :func:`read_panel` restores the
Period dtype. Everything else in the codebase can then assume the schema in
:data:`dengue.config.PANEL_DTYPES` holds.
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

import httpx
import pandas as pd

from dengue import config
from dengue.utils.logging import get_logger

log = get_logger(__name__)


class IngestError(RuntimeError):
    """Raised when a data source fails.

    Deliberately not caught inside ingest modules: a failed source must surface,
    never be papered over with invented numbers. Callers that need resilience
    (e.g. ``make panel``) catch this at the top level and fall back to the
    synthetic panel, logging loudly that they have done so.
    """


# --------------------------------------------------------------------------
# HTTP
# --------------------------------------------------------------------------


def http_get(
    url: str,
    *,
    params: dict[str, Any] | None = None,
    timeout: float | None = None,
    retries: int = 3,
    backoff: float = 2.0,
    expect_json: bool = False,
) -> httpx.Response:
    """GET with bounded exponential-backoff retries.

    Retries on transport errors and on 5xx / 429. Does not retry other 4xx --
    those indicate a bad request, and hammering the endpoint will not fix it.

    Raises
    ------
    IngestError
        If every attempt fails.
    """
    timeout = timeout if timeout is not None else config.HTTP_TIMEOUT_SECONDS
    headers = {"User-Agent": config.HTTP_USER_AGENT}
    if expect_json:
        headers["Accept"] = "application/json"

    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            with httpx.Client(timeout=timeout, follow_redirects=True) as client:
                response = client.get(url, params=params, headers=headers)

            if response.status_code < 400:
                return response

            retryable = response.status_code >= 500 or response.status_code == 429
            message = f"HTTP {response.status_code} from {url}"
            if not retryable:
                raise IngestError(f"{message} (not retryable)")
            last_error = IngestError(message)
            log.warning("%s - attempt %d/%d", message, attempt, retries)

        except httpx.HTTPError as exc:
            last_error = exc
            log.warning("Transport error for %s: %s - attempt %d/%d", url, exc, attempt, retries)

        if attempt < retries:
            time.sleep(backoff ** (attempt - 1))

    raise IngestError(f"GET {url} failed after {retries} attempts: {last_error}") from last_error


def cache_path_for(url: str, directory: Path, *, suffix: str = ".json") -> Path:
    """Deterministic cache path for a URL inside ``directory``.

    Uses a short hash of the full URL so query-string variants (different date
    ranges, different districts) do not collide.
    """
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]
    return directory / f"{digest}{suffix}"


def fetch_json_cached(
    url: str,
    *,
    params: dict[str, Any] | None = None,
    cache_dir: Path,
    refresh: bool = False,
) -> dict[str, Any]:
    """Fetch JSON, caching the raw response body under ``cache_dir``.

    The cache is keyed on the fully-resolved URL including params, so re-running
    an ingest with identical arguments makes zero network calls -- which is what
    lets the pipeline be re-run offline after one successful fetch.
    """
    cache_dir.mkdir(parents=True, exist_ok=True)
    resolved = str(httpx.URL(url, params=params or {}))
    path = cache_path_for(resolved, cache_dir)

    if path.exists() and not refresh:
        log.debug("cache hit  %s", path.name)
        return json.loads(path.read_text(encoding="utf-8"))

    response = http_get(url, params=params, expect_json=True)
    try:
        payload = response.json()
    except json.JSONDecodeError as exc:
        raise IngestError(f"Response from {resolved} was not valid JSON: {exc}") from exc

    path.write_text(json.dumps(payload, indent=None), encoding="utf-8")
    log.debug("cached     %s  (%d bytes)", path.name, path.stat().st_size)
    return payload


def download_binary(url: str, dest: Path, *, refresh: bool = False) -> Path:
    """Download a binary file (tarball, PDF) to ``dest``, caching on disk."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 0 and not refresh:
        log.debug("cache hit  %s (%d bytes)", dest.name, dest.stat().st_size)
        return dest

    response = http_get(url)
    dest.write_bytes(response.content)
    log.info("downloaded %s -> %s (%d bytes)", url, dest.name, dest.stat().st_size)
    return dest


# --------------------------------------------------------------------------
# Panel round-trip
# --------------------------------------------------------------------------


def coerce_panel_schema(df: pd.DataFrame, *, strict: bool = True) -> pd.DataFrame:
    """Coerce a frame to the frozen panel schema.

    Applies :data:`dengue.config.PANEL_DTYPES`, orders columns per
    :data:`dengue.config.PANEL_COLUMNS`, and sorts by ``(district_id,
    iso_week)``.

    Parameters
    ----------
    strict:
        If True, raise on missing columns. If False, fill missing optional
        columns with nulls (useful when a source genuinely lacks a field, e.g.
        colmozzie has no ``high_risk_flag``).
    """
    out = df.copy()
    missing = [c for c in config.PANEL_COLUMNS if c not in out.columns]
    if missing:
        if strict:
            raise ValueError(f"Panel is missing required columns: {missing}")
        for col in missing:
            out[col] = pd.NA

    extra = [c for c in out.columns if c not in config.PANEL_COLUMNS]
    if extra:
        log.debug("Dropping non-schema columns: %s", extra)

    out = out[list(config.PANEL_COLUMNS)]

    # iso_week may arrive as a Period, a Timestamp, or a string.
    if not isinstance(out["iso_week"].dtype, pd.PeriodDtype):
        out["iso_week"] = pd.PeriodIndex(pd.to_datetime(out["iso_week"]), freq=config.WEEK_FREQ)

    for col, dtype in config.PANEL_DTYPES.items():
        if col == "iso_week":
            continue
        if dtype in ("float64", "Int64"):
            # An all-pd.NA column arrives as object dtype, and object -> float64
            # raises rather than producing NaN. to_numeric handles both that and
            # numeric-looking strings from CSV-derived sources.
            out[col] = pd.to_numeric(out[col], errors="coerce")
        out[col] = out[col].astype(dtype)

    out = out.sort_values(["district_id", "iso_week"]).reset_index(drop=True)
    return out


def write_panel(df: pd.DataFrame, path: Path | None = None) -> Path:
    """Write the panel to Parquet, serialising ``iso_week`` to a date string."""
    path = path or config.PANEL_PATH
    path.parent.mkdir(parents=True, exist_ok=True)

    out = coerce_panel_schema(df)
    serialisable = out.copy()
    # Period -> the week's Monday, as an ISO date string. Parquet has no Period.
    serialisable["iso_week"] = out["iso_week"].dt.start_time.dt.strftime("%Y-%m-%d")
    serialisable.to_parquet(path, index=False, engine="pyarrow", compression="snappy")

    log.info(
        "wrote panel -> %s  rows=%d  districts=%d  weeks=[%s .. %s]",
        path,
        len(out),
        out["district_id"].nunique(),
        out["iso_week"].min(),
        out["iso_week"].max(),
    )
    return path


def read_panel(path: Path | None = None) -> pd.DataFrame:
    """Read the panel from Parquet, restoring the ``iso_week`` Period dtype."""
    path = path or config.PANEL_PATH
    if not path.exists():
        raise FileNotFoundError(
            f"No panel at {path}. Run `make panel` (real ingest) or "
            "`python -m dengue.features.build_panel --synthetic` first."
        )
    df = pd.read_parquet(path, engine="pyarrow")
    return coerce_panel_schema(df)


def write_artifact(df: pd.DataFrame, name: str) -> Path:
    """Write a DataFrame to ``artifacts/<name>.parquet`` for the Streamlit app.

    The app reads only these cached artifacts -- it must never invoke a model at
    request time.
    """
    config.ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    path = config.ARTIFACTS_DIR / f"{name}.parquet"

    out = df.copy()
    # Serialise any Period columns; Parquet cannot hold them.
    for col in out.columns:
        if isinstance(out[col].dtype, pd.PeriodDtype):
            out[col] = out[col].dt.start_time.dt.strftime("%Y-%m-%d")

    out.to_parquet(path, index=False, engine="pyarrow")
    log.info("wrote artifact -> %s  rows=%d", path, len(out))
    return path
