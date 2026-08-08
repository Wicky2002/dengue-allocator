"""Ingest district boundary geometry for the choropleth maps.

Source
------
**OCHA Common Operational Dataset — Sri Lanka administrative boundaries**
(``cod-ab-lka`` on the Humanitarian Data Exchange). These are the boundaries the
UN and humanitarian responders use operationally, which makes them the right
reference for a public-health tool: they match how districts are actually
administered rather than a cartographic approximation.

Licence: **CC BY-IGO** (attribution required — see the README provenance table).
https://data.humdata.org/dataset/cod-ab-lka

Why the file is simplified before it ships
------------------------------------------
The raw ``lka_admin2.geojson`` (districts) is ~22 MB, inside a 133 MB archive.
That is far too heavy for a web map and far too heavy to commit. This module
simplifies it with a topology-aware Douglas-Peucker pass and truncates coordinate
precision, producing a file two orders of magnitude smaller that is
indistinguishable at national zoom.

Precision is cut to 4 decimal places, which is ~11 m at Sri Lanka's latitude —
far finer than a district boundary needs on a choropleth, and the single biggest
size win because coordinate strings dominate GeoJSON.

The simplified file is committed under ``src/dengue/assets/`` so the dashboard
renders offline. It is static reference geography, not case data, so committing
it does not conflict with the repo's data policy.
"""

from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path
from typing import Any

from dengue import config
from dengue.utils.io import IngestError, http_get
from dengue.utils.logging import get_logger

log = get_logger(__name__)

HDX_DATASET = "cod-ab-lka"
HDX_PACKAGE_URL = "https://data.humdata.org/api/3/action/package_show"
BOUNDARIES_LICENCE = "CC-BY-IGO"
BOUNDARIES_ATTRIBUTION = "OCHA / Humanitarian Data Exchange (cod-ab-lka)"

#: Layer inside the archive holding district (admin level 2) polygons.
ADMIN2_LAYER = "lka_admin2.geojson"

#: Where the shipped, simplified file lives.
ASSETS_DIR = config.PACKAGE_ROOT / "assets"
DISTRICTS_GEOJSON = ASSETS_DIR / "lk_districts.simplified.geojson"

#: Douglas-Peucker tolerance in degrees. ~0.005 deg is ~550 m, invisible at
#: national zoom but removes the great majority of vertices.
SIMPLIFY_TOLERANCE = 0.005

#: Coordinate decimal places retained. 4 dp is ~11 m at this latitude.
COORD_PRECISION = 4


def _resource_url(fmt: str = "GEOJSON") -> str:
    """Resolve the download URL for the requested format from the HDX API."""
    response = http_get(HDX_PACKAGE_URL, params={"id": HDX_DATASET}, expect_json=True)
    result = response.json().get("result", {})
    for resource in result.get("resources", []):
        if (resource.get("format") or "").upper() == fmt.upper():
            return str(resource["url"])
    raise IngestError(f"No {fmt} resource found in HDX dataset {HDX_DATASET}")


def _round_coords(geometry: Any, precision: int) -> Any:
    """Recursively truncate coordinate precision in a GeoJSON geometry."""
    if isinstance(geometry, int | float):
        return round(float(geometry), precision)
    if isinstance(geometry, list):
        return [_round_coords(g, precision) for g in geometry]
    return geometry


def _round_and_validate_geometry(geometry: Any, precision: int) -> dict[str, Any]:
    """Round coordinates, then re-validate and re-repair topology.

    ``geometry.simplify().buffer(0)`` upstream already repairs
    self-intersections at full float precision, but rounding happens *after*
    that -- and truncating coordinates can itself reintroduce the exact
    problem ``buffer(0)`` fixed: two vertices that were distinct at full
    precision can collapse onto the same rounded point, or a rounded edge can
    cross another. Repairing again after rounding is what actually guarantees
    the *shipped* asset is valid, not just the pre-rounding intermediate. If a
    feature is still invalid after a second repair attempt (rare -- a very
    fine coastline detail collapsing under 4 dp rounding), this falls back to
    the unrounded coordinates for that one feature rather than shipping
    invalid geometry, trading a little file size for correctness.
    """
    from shapely.geometry import mapping, shape

    rounded = _round_coords(mapping(geometry), precision)
    candidate = shape(rounded)

    if not candidate.is_valid:
        repaired = candidate.buffer(0)
        if repaired.is_valid and not repaired.is_empty:
            candidate = repaired
        else:
            from shapely.validation import explain_validity

            log.warning(
                "boundaries: rounded geometry still invalid after repair (%s); "
                "keeping full-precision coordinates for this feature",
                explain_validity(candidate),
            )
            candidate = geometry

    return mapping(candidate)


def _district_name_from_properties(properties: dict[str, Any]) -> str | None:
    """Pull the district name out of the COD property bag.

    COD files carry several name fields (``ADM2_EN``, ``admin2Name_en``, …)
    depending on vintage, so this tries the known variants rather than assuming
    one.
    """
    for key in (
        "adm2_name",  # current COD v03 schema
        "ADM2_EN",
        "admin2Name_en",
        "ADM2_NAME",
        "adm2_en",
        "DISTRICT",
        "NAME_2",
        "admin2Name",
    ):
        value = properties.get(key)
        if value:
            return str(value)
    return None


def build_simplified_geojson(
    *, refresh: bool = False, tolerance: float = SIMPLIFY_TOLERANCE
) -> Path:
    """Download, simplify, and write the district GeoJSON asset.

    Each feature is reduced to two properties: ``district_id`` (the canonical
    key, so the map joins straight onto the panel) and ``name``.

    Returns
    -------
    pathlib.Path
        Path to the written asset.
    """
    from shapely.geometry import shape

    config.ensure_dirs()
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)

    cache = config.RAW_DIR / "boundaries" / "lka_admin_boundaries.geojson.zip"
    if cache.exists() and not refresh:
        log.info("boundaries: using cached archive %s", cache.name)
        payload = cache.read_bytes()
    else:
        url = _resource_url("GEOJSON")
        log.info("boundaries: downloading %s (licence %s)", HDX_DATASET, BOUNDARIES_LICENCE)
        payload = http_get(url).content
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_bytes(payload)
        log.info("boundaries: cached %.1f MB -> %s", len(payload) / 1e6, cache.name)

    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        if ADMIN2_LAYER not in archive.namelist():
            raise IngestError(f"{ADMIN2_LAYER} not in archive; found {archive.namelist()}")
        raw = json.loads(archive.read(ADMIN2_LAYER))

    features: list[dict[str, Any]] = []
    unmatched: list[str] = []

    for feature in raw.get("features", []):
        properties = feature.get("properties", {}) or {}
        raw_name = _district_name_from_properties(properties)
        if not raw_name:
            continue

        district_id = config.normalise_district(raw_name, strict=False)
        if district_id is None:
            unmatched.append(raw_name)
            continue

        geometry = shape(feature["geometry"])
        # buffer(0) repairs self-intersections that simplification can expose;
        # without it a handful of coastal polygons render as slivers.
        simplified = geometry.simplify(tolerance, preserve_topology=True).buffer(0)
        if simplified.is_empty:
            simplified = geometry

        features.append(
            {
                "type": "Feature",
                "id": district_id,
                "properties": {
                    "district_id": district_id,
                    "name": config.get_district(district_id).name,
                    # Official OCHA P-code (e.g. LK11). Kept because it is the
                    # join key for other humanitarian datasets.
                    "pcode": properties.get("adm2_pcode"),
                    "province": properties.get("adm1_name"),
                },
                "geometry": _round_and_validate_geometry(simplified, COORD_PRECISION),
            }
        )

    if unmatched:
        log.warning(
            "boundaries: %d unmatched names: %s", len(unmatched), sorted(set(unmatched))[:10]
        )

    # Merge any district split across multiple features (islands, exclaves).
    merged: dict[str, dict[str, Any]] = {}
    for feature in features:
        key = feature["properties"]["district_id"]
        if key in merged:
            from shapely.ops import unary_union

            combined = unary_union([shape(merged[key]["geometry"]), shape(feature["geometry"])])
            merged[key]["geometry"] = _round_and_validate_geometry(combined, COORD_PRECISION)
        else:
            merged[key] = feature

    collection = {
        "type": "FeatureCollection",
        "metadata": {
            "source": BOUNDARIES_ATTRIBUTION,
            "licence": BOUNDARIES_LICENCE,
            "url": f"https://data.humdata.org/dataset/{HDX_DATASET}",
            "simplify_tolerance_deg": tolerance,
            "coordinate_precision": COORD_PRECISION,
        },
        "features": list(merged.values()),
    }

    DISTRICTS_GEOJSON.write_text(json.dumps(collection, separators=(",", ":")), encoding="utf-8")
    size_kb = DISTRICTS_GEOJSON.stat().st_size / 1024

    log.info(
        "boundaries: wrote %s  districts=%d  size=%.0f KB  (from %.1f MB raw)",
        DISTRICTS_GEOJSON.name,
        len(merged),
        size_kb,
        len(payload) / 1e6,
    )

    missing = set(config.DISTRICT_IDS) - set(merged)
    if missing:
        log.error("boundaries: MISSING districts in the map: %s", sorted(missing))

    invalid = _invalid_feature_ids(collection)
    if invalid:
        log.error("boundaries: %d feature(s) failed final validation: %s", len(invalid), invalid)
    else:
        log.info("boundaries: all %d features validated OK", len(merged))

    return DISTRICTS_GEOJSON


def _invalid_feature_ids(collection: dict[str, Any]) -> list[str]:
    """District ids whose geometry in ``collection`` is invalid or degenerate."""
    from shapely.geometry import shape

    bad: list[str] = []
    for feature in collection.get("features", []):
        district_id = feature.get("properties", {}).get("district_id", "?")
        try:
            geom = shape(feature["geometry"])
        except Exception:  # - any parse failure counts as invalid
            bad.append(district_id)
            continue
        if not geom.is_valid or geom.is_empty or geom.area <= 0:
            bad.append(district_id)
    return bad


def validate_geojson_asset(path: Path | None = None) -> dict[str, Any]:
    """Validate the shipped district GeoJSON asset. Raises on any problem.

    Checked, in order: the file parses as JSON; it has exactly the 25
    registry districts, no more, no fewer; every feature's geometry is valid
    (no self-intersections), non-empty, and has plausible non-zero area.
    Exercised by ``tests/test_boundaries.py`` so a future re-generation of the
    asset can't silently ship a broken district.

    Returns
    -------
    dict
        Small summary (``n_features``, ``total_area_deg2``) for logging/tests.
    """
    path = path or DISTRICTS_GEOJSON
    collection = json.loads(path.read_text(encoding="utf-8"))

    feature_ids = {f["properties"]["district_id"] for f in collection["features"]}
    expected = set(config.DISTRICT_IDS)
    if feature_ids != expected:
        raise ValueError(
            f"Geometry asset district set mismatch. "
            f"Missing: {sorted(expected - feature_ids)}. "
            f"Unexpected: {sorted(feature_ids - expected)}."
        )

    invalid = _invalid_feature_ids(collection)
    if invalid:
        raise ValueError(f"Invalid/degenerate geometry for districts: {invalid}")

    from shapely.geometry import shape

    total_area = sum(shape(f["geometry"]).area for f in collection["features"])
    return {"n_features": len(collection["features"]), "total_area_deg2": total_area}


def load_district_geojson() -> dict[str, Any]:
    """Load the shipped district GeoJSON.

    Raises
    ------
    FileNotFoundError
        If the asset has not been built. It is committed to the repo, so this
        normally means the file was deleted rather than that a build is needed.
    """
    if not DISTRICTS_GEOJSON.exists():
        raise FileNotFoundError(
            f"No district geometry at {DISTRICTS_GEOJSON}. "
            "Rebuild it with `python -m dengue.ingest.boundaries`."
        )
    return json.loads(DISTRICTS_GEOJSON.read_text(encoding="utf-8"))


def main() -> None:  # pragma: no cover - CLI entry point
    build_simplified_geojson()


if __name__ == "__main__":  # pragma: no cover
    main()
