"""Structured-ish logging with ingest provenance helpers.

Every ingest step must log row counts and date ranges so that a silent parse
failure (a table format change upstream, a renamed column) shows up as an
obvious anomaly in the log rather than as a quietly truncated panel.
"""

from __future__ import annotations

import logging
import os
import sys
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # pragma: no cover - typing only
    import pandas as pd

_CONFIGURED = False

_FORMAT = "%(asctime)s | %(levelname)-7s | %(name)-28s | %(message)s"
_DATEFMT = "%Y-%m-%d %H:%M:%S"


def configure_logging(level: str | int | None = None, *, force: bool = False) -> None:
    """Configure root logging once, idempotently.

    Level resolution order: explicit ``level`` argument, then ``$LOG_LEVEL``,
    then ``INFO``.
    """
    global _CONFIGURED
    if _CONFIGURED and not force:
        return

    resolved = level if level is not None else os.environ.get("LOG_LEVEL", "INFO")
    if isinstance(resolved, str):
        resolved = getattr(logging, resolved.upper(), logging.INFO)

    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setFormatter(logging.Formatter(_FORMAT, datefmt=_DATEFMT))

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(resolved)

    # These are chatty at DEBUG and drown out our own provenance lines.
    for noisy in ("httpx", "httpcore", "urllib3", "matplotlib", "pdfminer", "PIL"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """Return a module logger, configuring logging on first use."""
    configure_logging()
    return logging.getLogger(name)


def log_frame(
    logger: logging.Logger,
    df: pd.DataFrame,
    label: str,
    *,
    date_col: str | None = "iso_week",
    group_col: str | None = "district_id",
    level: int = logging.INFO,
) -> None:
    """Log row count, date range, and group count for an ingested frame.

    This is the provenance line that makes parse failures obvious. Call it after
    every ingest and transform step.

    Parameters
    ----------
    logger:
        Logger to emit on.
    df:
        Frame to describe.
    label:
        Short human label, e.g. ``"colmozzie:normalised"``.
    date_col:
        Column to derive the date range from. Ignored if absent from ``df``.
    group_col:
        Column to count distinct values of. Ignored if absent from ``df``.
    """
    parts: list[str] = [f"rows={len(df):,}", f"cols={df.shape[1]}"]

    if date_col and date_col in df.columns and len(df):
        try:
            lo, hi = df[date_col].min(), df[date_col].max()
            parts.append(f"{date_col}=[{lo} .. {hi}]")
        except (TypeError, ValueError):  # unorderable column - not fatal
            pass

    if group_col and group_col in df.columns and len(df):
        parts.append(f"n_{group_col}={df[group_col].nunique()}")

    if "cases" in df.columns and len(df):
        total = df["cases"].sum()
        n_missing = int(df["cases"].isna().sum())
        parts.append(f"cases_total={total:,}")
        if n_missing:
            parts.append(f"cases_missing={n_missing:,}")

    logger.log(level, "%-34s %s", label, "  ".join(parts))


def log_step(logger: logging.Logger, message: str, **fields: Any) -> None:
    """Log a step with trailing ``key=value`` fields."""
    if fields:
        rendered = "  ".join(f"{k}={v}" for k, v in fields.items())
        logger.info("%s  %s", message, rendered)
    else:
        logger.info("%s", message)
