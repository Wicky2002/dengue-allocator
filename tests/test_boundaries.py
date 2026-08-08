"""Tests for the committed district geometry asset.

These guard against a future re-generation of
``src/dengue/assets/lk_districts.simplified.geojson`` silently shipping a
broken district. Coordinate rounding (done to keep the committed file small)
can reintroduce the exact topology problems ``buffer(0)`` upstream was there
to fix -- see ``_round_and_validate_geometry``'s docstring -- so this is
checked directly against the real, shipped file, not a synthetic fixture.
"""

from __future__ import annotations

import json

import pytest

from dengue import config
from dengue.ingest.boundaries import (
    DISTRICTS_GEOJSON,
    _invalid_feature_ids,
    _round_and_validate_geometry,
    validate_geojson_asset,
)

pytestmark = pytest.mark.skipif(
    not DISTRICTS_GEOJSON.exists(), reason="district geometry asset not built"
)


def test_shipped_asset_has_exactly_the_registry_districts():
    summary = validate_geojson_asset()
    assert summary["n_features"] == config.N_DISTRICTS == 25


def test_shipped_asset_has_no_invalid_geometry():
    collection = json.loads(DISTRICTS_GEOJSON.read_text(encoding="utf-8"))
    invalid = _invalid_feature_ids(collection)
    assert invalid == [], f"invalid/degenerate geometry for: {invalid}"


def test_shipped_asset_total_area_is_plausible():
    """Sri Lanka is ~65,610 km^2. At this latitude 1 deg^2 is roughly 12,000
    km^2, so the whole country should land in a wide but sane band -- this
    catches a gross error (e.g. a district duplicated or a unit mistake)
    without being sensitive to the exact simplification tolerance."""
    summary = validate_geojson_asset()
    assert 3.0 < summary["total_area_deg2"] < 8.0


def test_shipped_asset_is_committed_and_small():
    """The whole point of simplifying before committing: it must actually be
    small enough to ship, not just technically present."""
    size_kb = DISTRICTS_GEOJSON.stat().st_size / 1024
    assert size_kb < 500, f"asset is {size_kb:.0f} KB; simplification may have regressed"


def test_every_feature_has_a_canonical_district_id():
    collection = json.loads(DISTRICTS_GEOJSON.read_text(encoding="utf-8"))
    ids = {f["properties"]["district_id"] for f in collection["features"]}
    assert ids == set(config.DISTRICT_IDS)


def test_round_and_validate_repairs_a_self_intersecting_polygon():
    """A bowtie polygon is invalid before repair; the helper must fix it."""
    from shapely.geometry import Polygon

    bowtie = Polygon([(0, 0), (2, 2), (2, 0), (0, 2), (0, 0)])
    assert not bowtie.is_valid

    result = _round_and_validate_geometry(bowtie, precision=4)

    from shapely.geometry import shape

    repaired = shape(result)
    assert repaired.is_valid
    assert not repaired.is_empty


def test_round_and_validate_preserves_a_simple_valid_polygon():
    from shapely.geometry import Polygon, shape

    square = Polygon([(0, 0), (0, 1), (1, 1), (1, 0), (0, 0)])
    result = _round_and_validate_geometry(square, precision=4)
    restored = shape(result)

    assert restored.is_valid
    assert restored.area == pytest.approx(1.0, abs=1e-6)


def test_validate_geojson_asset_raises_on_missing_district(tmp_path):
    collection = json.loads(DISTRICTS_GEOJSON.read_text(encoding="utf-8"))
    collection["features"] = collection["features"][:-1]  # drop one district

    broken = tmp_path / "broken.geojson"
    broken.write_text(json.dumps(collection), encoding="utf-8")

    with pytest.raises(ValueError, match="district set mismatch"):
        validate_geojson_asset(broken)


def test_validate_geojson_asset_raises_on_invalid_geometry(tmp_path):
    collection = json.loads(DISTRICTS_GEOJSON.read_text(encoding="utf-8"))
    # Corrupt one feature into a degenerate (zero-area) geometry.
    collection["features"][0]["geometry"] = {
        "type": "Polygon",
        "coordinates": [[[0, 0], [0, 0], [0, 0], [0, 0]]],
    }

    broken = tmp_path / "broken.geojson"
    broken.write_text(json.dumps(collection), encoding="utf-8")

    with pytest.raises(ValueError, match="Invalid/degenerate geometry"):
        validate_geojson_asset(broken)
