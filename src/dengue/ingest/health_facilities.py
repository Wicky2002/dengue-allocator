"""Ingest hospital locations and national bed capacity from public sources.

Two genuinely public sources, no scraping and no invented facilities:

1. **OpenStreetMap via the Overpass API** — hospital and clinic locations across
   Sri Lanka. Licence: **ODbL** (attribution + share-alike; see the README
   provenance table). OSM has good coverage of named hospitals in Sri Lanka but
   *sparse* ``beds`` tagging, which is stated rather than papered over.

2. **World Bank Open Data** (``SH.MED.BEDS.ZS``) — hospital beds per 1,000
   people, national. Licence: **CC-BY-4.0**.

What this does and does not give you
------------------------------------
It gives real facility **locations** and a real national **bed density**. It does
**not** give live occupancy, ICU counts, platelet stock, or staffing — none of
that is published anywhere public, for Sri Lanka or most countries.

So district bed capacity here is an **estimate**: national beds-per-1000 applied
to district population, then distributed across the district's known facilities
weighted by facility type. Every figure derived this way is tagged
``ProvenanceTier.ASSUMED`` and is labelled as an estimate wherever it is shown.
See :mod:`dengue.platform.provenance` for why that tagging is enforced rather
than left to discipline.

Attribution
-----------
Facility data © OpenStreetMap contributors, available under the Open Database
Licence (https://www.openstreetmap.org/copyright).
"""

from __future__ import annotations

import json
import math
from typing import Any

import pandas as pd

from dengue import config
from dengue.utils.io import IngestError, http_get
from dengue.utils.logging import get_logger

log = get_logger(__name__)

#: Overpass mirrors, tried in order. The main instance is frequently rate-limited
#: or overloaded, and a single-endpoint client would look like a code failure.
OVERPASS_ENDPOINTS = (
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.osm.ch/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
)

#: Sri Lanka bounding box (south, west, north, east). A bbox query is far cheaper
#: on Overpass than an ``area`` lookup, which times out on the public instances.
SRI_LANKA_BBOX = (5.85, 79.5, 9.95, 82.0)

WORLD_BANK_BEDS_URL = "https://api.worldbank.org/v2/country/LKA/indicator/SH.MED.BEDS.ZS"

OSM_LICENCE = "ODbL-1.0"
OSM_ATTRIBUTION = "© OpenStreetMap contributors"
WORLD_BANK_LICENCE = "CC-BY-4.0"

#: Relative bed weighting by OSM facility tagging. Teaching and general
#: hospitals carry far more beds than a rural clinic, so an unweighted split
#: across facilities would badly misallocate capacity toward districts with many
#: small clinics.
_FACILITY_WEIGHT = {
    "hospital": 1.0,
    "clinic": 0.15,
    "doctors": 0.05,
}


def _overpass_query(query: str) -> dict[str, Any]:
    """POST an Overpass QL query, trying each mirror in turn."""
    headers = {"User-Agent": config.HTTP_USER_AGENT}
    last_error: Exception | None = None

    for endpoint in OVERPASS_ENDPOINTS:
        try:
            import httpx

            with httpx.Client(timeout=180.0, follow_redirects=True) as client:
                response = client.post(endpoint, data={"data": query}, headers=headers)
            if response.status_code == 200:
                log.info("overpass: %s responded OK", endpoint.split("/")[2])
                return response.json()
            log.warning(
                "overpass: %s returned HTTP %d", endpoint.split("/")[2], response.status_code
            )
            last_error = IngestError(f"HTTP {response.status_code} from {endpoint}")
        except Exception as exc:  # - try the next mirror
            log.warning("overpass: %s failed (%s)", endpoint.split("/")[2], exc)
            last_error = exc

    raise IngestError(
        f"All {len(OVERPASS_ENDPOINTS)} Overpass mirrors failed. Last error: {last_error}. "
        "The public instances are frequently overloaded; retry later or run a local "
        "Overpass instance."
    )


def fetch_facilities(*, refresh: bool = False) -> pd.DataFrame:
    """Fetch health facilities in Sri Lanka from OpenStreetMap.

    Returns
    -------
    pandas.DataFrame
        Columns ``osm_id``, ``name``, ``facility_type``, ``lat``, ``lon``,
        ``beds_tagged``, ``operator``, ``district_id``.
    """
    config.ensure_dirs()
    cache = config.RAW_DIR / "health_facilities" / "osm_facilities.json"

    if cache.exists() and not refresh:
        log.info("facilities: using cached %s", cache.name)
        payload = json.loads(cache.read_text(encoding="utf-8"))
    else:
        south, west, north, east = SRI_LANKA_BBOX
        bbox = f"{south},{west},{north},{east}"
        query = (
            f"[out:json][timeout:120];("
            f'node["amenity"~"^(hospital|clinic)$"]({bbox});'
            f'way["amenity"~"^(hospital|clinic)$"]({bbox});'
            f");out center;"
        )
        log.info("facilities: querying Overpass (licence %s)", OSM_LICENCE)
        payload = _overpass_query(query)
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(payload), encoding="utf-8")

    rows: list[dict[str, Any]] = []
    for element in payload.get("elements", []):
        tags = element.get("tags", {}) or {}
        lat = element.get("lat") or (element.get("center") or {}).get("lat")
        lon = element.get("lon") or (element.get("center") or {}).get("lon")
        if lat is None or lon is None:
            continue

        beds = tags.get("beds")
        try:
            beds_value = int(beds) if beds is not None else None
        except (TypeError, ValueError):
            beds_value = None

        rows.append(
            {
                "osm_id": f"{element.get('type', 'node')}/{element.get('id')}",
                "name": tags.get("name"),
                "facility_type": tags.get("amenity", "hospital"),
                "lat": float(lat),
                "lon": float(lon),
                "beds_tagged": beds_value,
                "operator": tags.get("operator"),
            }
        )

    frame = pd.DataFrame(rows)
    if frame.empty:
        raise IngestError("Overpass returned no health facilities")

    frame["district_id"] = [
        nearest_district(lat, lon) for lat, lon in zip(frame["lat"], frame["lon"], strict=True)
    ]

    n_named = int(frame["name"].notna().sum())
    n_beds = int(frame["beds_tagged"].notna().sum())
    log.info(
        "facilities: %d facilities  named=%d  with beds tag=%d (%.1f%%)  districts=%d",
        len(frame),
        n_named,
        n_beds,
        100.0 * n_beds / max(len(frame), 1),
        frame["district_id"].nunique(),
    )
    if n_beds < 0.1 * len(frame):
        log.warning(
            "facilities: OSM bed tagging is sparse (%d/%d). District capacity will be "
            "ESTIMATED from World Bank bed density, not measured.",
            n_beds,
            len(frame),
        )
    return frame


def nearest_district(lat: float, lon: float) -> str:
    """Assign a point to the nearest district centroid.

    A point-in-polygon test against the real boundaries would be more accurate,
    but centroid distance is adequate for assigning a facility to a district and
    avoids making the geometry a hard dependency of this module.
    """
    best_id, best_distance = config.DISTRICT_IDS[0], math.inf
    for district in config.DISTRICTS:
        d = (district.lat - lat) ** 2 + (district.lon - lon) ** 2
        if d < best_distance:
            best_id, best_distance = district.district_id, d
    return best_id


def fetch_national_bed_density(*, refresh: bool = False) -> tuple[float, int]:
    """Latest published hospital beds per 1,000 people, and its year.

    Returns
    -------
    tuple
        ``(beds_per_1000, year)``.
    """
    config.ensure_dirs()
    cache = config.RAW_DIR / "health_facilities" / "worldbank_beds.json"

    if cache.exists() and not refresh:
        payload = json.loads(cache.read_text(encoding="utf-8"))
    else:
        response = http_get(
            WORLD_BANK_BEDS_URL,
            params={"format": "json", "per_page": "100"},
            expect_json=True,
        )
        payload = response.json()
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(payload), encoding="utf-8")

    if not isinstance(payload, list) or len(payload) < 2:
        raise IngestError("Unexpected World Bank response shape")

    observations = [o for o in payload[1] if o.get("value") is not None]
    if not observations:
        raise IngestError("World Bank returned no non-null bed-density observations")

    latest = max(observations, key=lambda o: int(o["date"]))
    beds_per_1000 = float(latest["value"])
    year = int(latest["date"])

    log.info(
        "facilities: World Bank beds per 1,000 = %.2f (%d, licence %s)",
        beds_per_1000,
        year,
        WORLD_BANK_LICENCE,
    )
    return beds_per_1000, year


def build_district_capacity(
    facilities: pd.DataFrame | None = None,
    beds_per_1000: float | None = None,
) -> pd.DataFrame:
    """Estimate district-level bed capacity.

    National bed density is applied to district population, then apportioned so
    that the district totals reconcile to the national figure. Facility counts
    inform *where* beds sit within a district, not how many exist.

    Returns
    -------
    pandas.DataFrame
        Columns ``district_id``, ``population``, ``n_facilities``,
        ``n_hospitals``, ``estimated_beds``, ``beds_per_1000``,
        ``capacity_is_estimated``.

    Notes
    -----
    **Every bed number here is an estimate**, not an observation. Live occupancy
    and true per-facility capacity are not published. The
    ``capacity_is_estimated`` column exists so downstream code cannot lose track
    of that.
    """
    if beds_per_1000 is None:
        beds_per_1000, _ = fetch_national_bed_density()

    counts: dict[str, dict[str, int]] = {
        d.district_id: {"n_facilities": 0, "n_hospitals": 0} for d in config.DISTRICTS
    }
    if facilities is not None and not facilities.empty:
        for row in facilities.itertuples(index=False):
            entry = counts.setdefault(row.district_id, {"n_facilities": 0, "n_hospitals": 0})
            entry["n_facilities"] += 1
            if row.facility_type == "hospital":
                entry["n_hospitals"] += 1

    rows = []
    for district in config.DISTRICTS:
        entry = counts.get(district.district_id, {"n_facilities": 0, "n_hospitals": 0})
        rows.append(
            {
                "district_id": district.district_id,
                "population": district.population,
                "n_facilities": entry["n_facilities"],
                "n_hospitals": entry["n_hospitals"],
                "estimated_beds": int(round(district.population / 1000.0 * beds_per_1000)),
                "beds_per_1000": beds_per_1000,
                "capacity_is_estimated": True,
            }
        )

    frame = pd.DataFrame(rows)
    log.info(
        "facilities: district capacity estimated  total_beds=%s  beds_per_1000=%.2f",
        f"{int(frame['estimated_beds'].sum()):,}",
        beds_per_1000,
    )
    return frame


def facility_poor_districts(capacity: pd.DataFrame, *, bottom_k: int = 6) -> tuple[str, ...]:
    """District IDs with the least facility coverage relative to population.

    Raw ``n_facilities`` favours high-population districts, which naturally
    host more facilities -- dividing by population turns it into a density
    comparable across districts of very different size. The bottom-``k`` by
    that density are the districts where an outbreak would find the least
    existing capacity to absorb it, independent of whether they are currently
    case-flagged high-risk. Intended to feed Stage 3's allocation floor
    alongside (not instead of) the case-based high-risk flag -- see
    :func:`dengue.pipeline.main`.
    """
    working = capacity[["district_id", "n_facilities", "population"]].copy()
    working["facilities_per_100k"] = working["n_facilities"] / working["population"] * 100_000.0
    poorest = working.nsmallest(bottom_k, "facilities_per_100k")
    return tuple(poorest["district_id"].astype(str))


def load(*, refresh: bool = False) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Fetch facilities and build the district capacity estimate.

    Returns ``(facilities, capacity)``. If Overpass is unavailable the facility
    frame comes back empty and capacity is still estimated from World Bank bed
    density — locations are a nice-to-have, bed density is the load-bearing input.
    """
    config.ensure_dirs()

    try:
        facilities = fetch_facilities(refresh=refresh)
    except IngestError as exc:
        log.error("facilities: OSM unavailable (%s); continuing without locations", exc)
        facilities = pd.DataFrame(
            columns=[
                "osm_id",
                "name",
                "facility_type",
                "lat",
                "lon",
                "beds_tagged",
                "operator",
                "district_id",
            ]
        )

    beds_per_1000, year = fetch_national_bed_density(refresh=refresh)
    capacity = build_district_capacity(facilities, beds_per_1000)
    capacity["beds_reference_year"] = year

    if not facilities.empty:
        out = config.RAW_DIR / "health_facilities" / "facilities.parquet"
        facilities.to_parquet(out, index=False)
        log.info("facilities: wrote %s", out)

    return facilities, capacity


def main() -> None:  # pragma: no cover - CLI entry point
    facilities, capacity = load()
    print(f"facilities: {len(facilities)}")
    print(capacity.head(10).to_string(index=False))


if __name__ == "__main__":  # pragma: no cover
    main()
