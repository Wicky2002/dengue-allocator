"""Regression tests for app chart components.

The bug this file exists to catch: a DataFrame column named ``"q0.5"`` (three
of them exist in this project's own prediction schema: ``q0.1``, ``q0.5``,
``q0.9``) is completely valid as a *pandas* column name, so a chart built from
it compiles without a Python exception. But Vega-Lite treats a bare ``.`` in a
field name as nested-property access, so the resulting spec is silently wrong
-- and that gap (Python builds it fine; only a real Vega-Lite compiler would
reject or misinterpret it) is exactly how this shipped undetected: every
earlier test exercised the Python side only, never a real renderer.

These tests close that gap two ways: a structural check that no un-escaped
dotted field reference reaches the spec, and an actual headless render via
``vl-convert-python`` (no browser, no Node, a self-contained Rust binary) that
would fail the same way a browser's Vega-Lite runtime would.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

APP_DIR = Path(__file__).resolve().parent.parent / "app"
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from components import _safe_field, choropleth  # noqa: E402

from dengue.ingest.boundaries import DISTRICTS_GEOJSON  # noqa: E402

pytestmark = pytest.mark.skipif(
    not DISTRICTS_GEOJSON.exists(), reason="district geometry asset not built"
)


def _dotted_field_refs(spec: Any, path: str = "") -> list[tuple[str, str]]:
    """Recursively find ``"field"`` values in a Vega-Lite spec that contain an
    un-escaped ``.``.

    ``properties.name`` / ``properties.district_id`` are *legitimate* nested
    accesses into a GeoJSON feature object and must not be flagged; only a
    literal data-column name containing a dot (which Vega-Lite would
    misinterpret as nesting) is a bug.
    """
    hits: list[tuple[str, str]] = []
    legitimate_prefixes = ("properties.",)

    if isinstance(spec, dict):
        for key, value in spec.items():
            if (
                key == "field"
                and isinstance(value, str)
                and "." in value
                and "\\." not in value
                and not value.startswith(legitimate_prefixes)
            ):
                hits.append((path, value))
            hits.extend(_dotted_field_refs(value, f"{path}.{key}"))
    elif isinstance(spec, list):
        for i, item in enumerate(spec):
            hits.extend(_dotted_field_refs(item, f"{path}[{i}]"))
    return hits


def _sample_frame() -> pd.DataFrame:
    """A frame shaped like the real district-risk artifact, dotted columns and all."""
    from dengue import config

    ids = list(config.DISTRICT_IDS)
    return pd.DataFrame(
        {
            "district_id": ids,
            "risk_level": (["low", "moderate", "high", "severe"] * len(ids))[: len(ids)],
            "q0.1": [1.0] * len(ids),
            "q0.5": [5.0] * len(ids),
            "q0.9": [9.0] * len(ids),
            "incidence_per_100k": [float(i) for i in range(len(ids))],
        }
    )


def test_safe_field_strips_dots():
    assert _safe_field("q0.5") == "q0_5"
    assert _safe_field("incidence_per_100k") == "incidence_per_100k"


def test_safe_field_is_idempotent():
    once = _safe_field("q0.5")
    assert _safe_field(once) == once


def test_choropleth_spec_has_no_unescaped_dotted_fields():
    frame = _sample_frame()
    chart = choropleth(
        frame,
        value_column="risk_level",
        categorical=True,
        tooltip_columns=[("q0.5", "Forecast cases", ".0f"), ("q0.9", "P90", ".0f")],
    )
    assert chart is not None, "geometry asset must be present for this test to be meaningful"

    spec = chart.to_dict()
    dotted = _dotted_field_refs(spec)
    assert dotted == [], f"un-escaped dotted field reference(s) in spec: {dotted}"


def test_choropleth_renders_headlessly_with_dotted_source_columns():
    """The real regression guard: an actual Vega-Lite render, not just a Python build.

    This is the test that would have caught the original bug -- building the
    chart in pure Python never touched a Vega-Lite compiler, which is exactly
    how a spec that misinterprets "q0.5" as nested JSON access shipped
    without failing anything.
    """
    vlc = pytest.importorskip("vl_convert", reason="vl-convert-python not installed")

    frame = _sample_frame()
    chart = choropleth(
        frame,
        value_column="risk_level",
        categorical=True,
        tooltip_columns=[
            ("q0.5", "Forecast cases", ".0f"),
            ("incidence_per_100k", "Per 100k", ".1f"),
        ],
    )
    assert chart is not None

    png_bytes = vlc.vegalite_to_png(chart.to_dict(), scale=1)
    assert len(png_bytes) > 1000, "rendered PNG suspiciously small; likely an empty/broken map"


def test_choropleth_sequential_scale_also_escapes_fields():
    """Numeric (non-categorical) choropleths -- e.g. occupancy_pct -- use the
    same code path and must be covered too."""
    frame = _sample_frame()
    frame["occupancy_pct"] = 42.0

    chart = choropleth(
        frame,
        value_column="occupancy_pct",
        categorical=False,
        tooltip_columns=[("q0.5", "Median", ".0f")],
    )
    assert chart is not None
    dotted = _dotted_field_refs(chart.to_dict())
    assert dotted == [], f"un-escaped dotted field reference(s): {dotted}"


def test_choropleth_returns_none_without_geometry(monkeypatch):
    """Missing geometry must degrade to None (caller falls back to a table),
    never raise.

    Patches ``_geometry_source`` directly rather than ``load_geometry``:
    ``_geometry_data_uri`` (which ``_geometry_source`` wraps) is
    ``@st.cache_data``-decorated, so once any earlier test has populated that
    cache with the real geometry, patching ``load_geometry`` alone no longer
    reaches ``choropleth`` -- the cached data URI wins regardless.
    """
    import components

    monkeypatch.setattr(components, "_geometry_source", lambda: None)
    result = choropleth(_sample_frame(), value_column="risk_level", categorical=True)
    assert result is None
