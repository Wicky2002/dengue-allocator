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
    from shapely.geometry import mapping, shape

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
                "geometry": _round_coords(mapping(simplified), COORD_PRECISION),
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
            from shapely.geometry import mapping as _mapping
            from shapely.geometry import shape as _shape
            from shapely.ops import unary_union

            combined = unary_union([_shape(merged[key]["geometry"]), _shape(feature["geometry"])])
            merged[key]["geometry"] = _round_coords(_mapping(combined), COORD_PRECISION)
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

    return DISTRICTS_GEOJSON


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
