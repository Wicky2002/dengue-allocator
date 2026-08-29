"""Export the dashboard artifacts as JSON for the Next.js front end.

The web UI holds the same invariant the Streamlit app does: **it never computes
at request time**. Every figure it renders comes from a Parquet artifact written
by ``make pipeline``. Next.js cannot read Parquet, so this module is the one
bridge between the two: it serialises each artifact to JSON under
``web/public/data/`` and copies the district geometry alongside it.

Run with ``make export-web`` (after ``make pipeline`` or ``make pipeline-real``).

Nothing here derives new quantities. It reshapes and rounds for transport only,
so a number in the browser is the same number the pipeline wrote -- if this file
ever starts *calculating* something, that calculation belongs in the pipeline
instead, where it is tested and where its provenance tier is enforced.
"""

from __future__ import annotations

import argparse
import json
import logging
import math
import shutil
from importlib import resources
from pathlib import Path
from typing import Any

import pandas as pd

from dengue import config

LOGGER = logging.getLogger(__name__)

#: Every artifact the web app reads. A missing one degrades a panel, never the
#: whole app -- the same rule the Streamlit app follows.
ARTIFACT_NAMES: tuple[str, ...] = (
    "pipeline_meta",
    "district_risk",
    "panel_recent",
    "forecasts",
    "scores",
    "effect_table",
    "allocation_sweep",
    "allocation_summary",
    "sei_sir_params",
    "hospital_readiness",
    "district_capacity",
    "health_facilities",
    "scenarios",
    "budget_sweep",
    "predictions_history",
)

WEB_DATA_DIR: Path = config.REPO_ROOT / "web" / "public" / "data"

#: Constants the front end must agree with the engine on -- risk band cut-offs,
#: the role/permission matrix, the provenance tiers. Written to the app's source
#: tree rather than to public/ because they are compile-time facts the UI is
#: built against, not data it fetches.
#:
#: Generated rather than retyped in TypeScript on purpose: a risk threshold that
#: drifts between the map and the engine paints a district the wrong colour, and
#: nothing in either codebase would fail to make that visible.
WEB_CONSTANTS_PATH: Path = config.REPO_ROOT / "web" / "src" / "generated" / "constants.json"

#: Float columns are rounded before serialisation. Full float64 repr triples the
#: payload for digits no chart can render -- 4 dp is below every quantity's own
#: uncertainty here, so this loses display precision only, never meaning.
FLOAT_DIGITS = 4


def _clean(value: Any) -> Any:
    """Make one cell JSON-safe.

    ``NaN``/``NaT`` become ``null`` rather than the bare ``NaN`` token, which is
    invalid JSON and which ``JSON.parse`` rejects outright.
    """
    if value is None:
        return None
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None
        return round(value, FLOAT_DIGITS)
    if isinstance(value, pd.Timestamp):
        return None if pd.isna(value) else value.date().isoformat()
    if hasattr(value, "item"):  # numpy scalar
        return _clean(value.item())
    if value is pd.NaT:
        return None
    return value


def frame_to_records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    """Serialise a frame to a list of JSON-safe row dicts."""
    frame = frame.copy()
    for column in frame.columns:
        if pd.api.types.is_datetime64_any_dtype(frame[column]):
            frame[column] = pd.to_datetime(frame[column], errors="coerce")
    return [{key: _clean(val) for key, val in row.items()} for row in frame.to_dict("records")]


def district_registry() -> list[dict[str, Any]]:
    """The district reference table, so the browser never has to guess a name.

    Exported from :mod:`dengue.config` rather than from an artifact: it is
    reference data about the country, not model output, and the front end needs
    the display spelling, province, centroid and population to label anything.
    """
    # Which districts qualify for Stage 3's allocation floor. Taken from the
    # same function the pipeline uses to set that floor, rather than
    # recomputed in the browser, so the badge on an MOH hotspot card cannot
    # disagree with the allocation the officer is looking at.
    poor: frozenset[str] = frozenset()
    capacity_path = config.ARTIFACTS_DIR / "district_capacity.parquet"
    if capacity_path.exists():
        from dengue.ingest.health_facilities import facility_poor_districts

        poor = frozenset(facility_poor_districts(pd.read_parquet(capacity_path)))

    return [
        {
            "district_id": d.district_id,
            "name": d.name,
            "province": d.province,
            "lat": d.lat,
            "lon": d.lon,
            "population": d.population,
            "area_km2": d.area_km2,
            "density_per_km2": round(d.density_per_km2, 1),
            "facility_poor": d.district_id in poor,
        }
        for d in config.DISTRICTS
    ]


def reports(out_dir: Path) -> int:
    """Render the National overview PDF for every horizon.

    The Streamlit app builds this on demand through ``st.download_button``. The
    web front end has no Python at request time, so the same generator is run
    here and the results served as static files -- identical bytes from
    identical code, rather than a second PDF writer in TypeScript that would
    drift from this one.

    One file per horizon, labelled for the national scope: the National overview
    renders identically for every role by design, so there is nothing
    role-specific in the report to vary.
    """
    import sys

    # `report.py` lives in app/ beside the Streamlit entry point rather than in
    # the package, so make it importable for the duration of this call.
    app_dir = str(config.REPO_ROOT / "app")
    if app_dir not in sys.path:
        sys.path.insert(0, app_dir)
    from report import build_report_pdf

    risk_path = config.ARTIFACTS_DIR / "district_risk.parquet"
    meta_path = config.ARTIFACTS_DIR / "pipeline_meta.parquet"
    if not risk_path.exists():
        return 0

    district_risk = pd.read_parquet(risk_path)
    meta = pd.read_parquet(meta_path) if meta_path.exists() else None
    meta_row = meta.iloc[0] if meta is not None and not meta.empty else None
    is_synthetic = bool(meta_row["is_synthetic"]) if meta_row is not None else True

    written = 0
    for horizon in sorted(district_risk["horizon"].dropna().unique()):
        pdf = build_report_pdf(
            district_risk,
            horizon=int(horizon),
            role_label="National overview",
            scope_label="All 25 districts",
            is_synthetic=is_synthetic,
            pipeline_meta_row=meta_row,
        )
        (out_dir / f"national-overview-{int(horizon)}w.pdf").write_bytes(pdf)
        written += 1
    return written


def assessments() -> list[dict[str, Any]]:
    """Per-district risk assessments and recommendations, for every audience.

    Exported rather than reimplemented in TypeScript for the same reason the
    risk thresholds are: :func:`dengue.platform.risk.recommend` encodes what a
    citizen, a clinician and an MOH officer should each *do* at a given band,
    and a second copy of that logic in the front end would drift from this one
    silently. The browser renders these strings; it never decides them.
    """
    from dengue.platform.risk import assess_all

    path = config.ARTIFACTS_DIR / "district_risk.parquet"
    if not path.exists():
        return []

    district_risk = pd.read_parquet(path)
    rows: list[dict[str, Any]] = []
    for horizon in sorted(district_risk["horizon"].dropna().unique()):
        for audience in ("public", "hospital", "moh"):
            for item in assess_all(district_risk, horizon_weeks=int(horizon), audience=audience):
                rows.append(
                    {
                        "district_id": item.district_id,
                        "district": item.district_name,
                        "horizon": int(horizon),
                        "audience": audience,
                        "risk_level": item.risk_level.value,
                        "risk_label": item.risk_level.label,
                        "incidence_per_100k": _clean(item.incidence_per_100k),
                        "forecast_median": _clean(item.forecast_median),
                        "forecast_lower": _clean(item.forecast_lower),
                        "forecast_upper": _clean(item.forecast_upper),
                        "change_pct": _clean(item.change_pct),
                        "is_rising_fast": bool(item.is_rising_fast),
                        "recommendations": [
                            {
                                "action": r.action,
                                "rationale": r.rationale,
                                "urgency": r.urgency,
                            }
                            for r in item.recommendations
                        ],
                    }
                )
    return rows


def constants() -> dict[str, Any]:
    """The engine constants the UI is compiled against."""
    from dengue.platform.hospital import ClinicalRatios
    from dengue.platform.provenance import SOURCE_REGISTRY, ProvenanceTier
    from dengue.platform.rbac import ROLE_PERMISSIONS, Permission, Role
    from dengue.platform.risk import RAPID_GROWTH_THRESHOLD, RISK_THRESHOLDS, RiskLevel

    return {
        "riskLevels": [
            {
                "key": level.value,
                "label": level.label,
                "colour": level.colour,
                "threshold": RISK_THRESHOLDS[level],
            }
            for level in RiskLevel
        ],
        "rapidGrowthThreshold": RAPID_GROWTH_THRESHOLD,
        "provenanceTiers": [
            {"key": tier.value, "label": tier.label, "description": tier.description}
            for tier in ProvenanceTier
        ],
        "roles": [
            {
                "key": role.value,
                "label": role.label,
                "description": role.description,
                "permissions": sorted(p.value for p in ROLE_PERMISSIONS[role]),
            }
            for role in Role
        ],
        "permissions": sorted(p.value for p in Permission),
        # The hospital portal recomputes its readiness table live as an officer
        # moves a ratio slider. That is cheap arithmetic over 25 rows, not a
        # model refit -- but the *default* values are literature parameters, so
        # they are published from the engine rather than retyped in the UI.
        "clinicalRatios": {
            field: getattr(ClinicalRatios(), field)
            for field in (
                "hospitalisation_rate",
                "severe_fraction_of_admitted",
                "icu_fraction_of_admitted",
                "paediatric_fraction",
                "mean_length_of_stay_days",
                "severe_length_of_stay_days",
                "platelet_units_per_severe_case",
                "iv_fluid_litres_per_admission",
                "nurses_per_occupied_bed",
                "doctors_per_occupied_bed",
                "diagnostic_tests_per_notified_case",
            )
        },
        "dengueBedShare": 0.15,
        # The administration portal's data-source table. Published from the
        # engine's own registry so a source cannot appear in the UI without a
        # licence and a coverage statement attached to it.
        "sources": [{"key": key, **value} for key, value in SOURCE_REGISTRY.items()],
    }


def _copy_geometry(out_dir: Path) -> bool:
    """Copy the bundled simplified district geometry next to the data."""
    try:
        source = resources.files("dengue.assets").joinpath("lk_districts.simplified.geojson")
        with resources.as_file(source) as path:
            shutil.copyfile(path, out_dir / "districts.geojson")
        return True
    except (FileNotFoundError, ModuleNotFoundError):
        LOGGER.warning("district geometry not found; the choropleth will render empty")
        return False


def export(out_dir: Path = WEB_DATA_DIR) -> dict[str, int]:
    """Write every available artifact to ``out_dir`` as JSON.

    Returns a ``{name: row_count}`` map of what was actually written.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    written: dict[str, int] = {}

    for name in ARTIFACT_NAMES:
        path = config.ARTIFACTS_DIR / f"{name}.parquet"
        if not path.exists():
            LOGGER.warning("skipping %s -- no artifact at %s", name, path)
            continue
        frame = pd.read_parquet(path)
        for column in ("iso_week", "target_week"):
            if column in frame.columns:
                frame[column] = pd.to_datetime(frame[column], errors="coerce")
        records = frame_to_records(frame)
        (out_dir / f"{name}.json").write_text(
            json.dumps(records, separators=(",", ":")), encoding="utf-8"
        )
        written[name] = len(records)

    assessment_rows = assessments()
    (out_dir / "assessments.json").write_text(
        json.dumps(assessment_rows, separators=(",", ":")), encoding="utf-8"
    )
    written["assessments"] = len(assessment_rows)

    districts = district_registry()
    (out_dir / "districts.json").write_text(
        json.dumps(districts, separators=(",", ":")), encoding="utf-8"
    )
    written["districts"] = len(districts)

    if _copy_geometry(out_dir):
        written["districts.geojson"] = 1

    n_reports = reports(out_dir)
    if n_reports:
        written["national-overview PDFs"] = n_reports

    WEB_CONSTANTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    WEB_CONSTANTS_PATH.write_text(json.dumps(constants(), indent=2) + "\n", encoding="utf-8")
    written["constants"] = 1

    # A manifest so the front end can tell "this panel has no data" from "this
    # export never ran" -- the two need different messages on screen.
    (out_dir / "manifest.json").write_text(
        json.dumps({"exported": written}, indent=2), encoding="utf-8"
    )
    return written


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        type=Path,
        default=WEB_DATA_DIR,
        help="output directory (default: web/public/data)",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    written = export(args.out)
    total_bytes = sum(p.stat().st_size for p in args.out.glob("*.json"))
    for name, rows in written.items():
        LOGGER.info("%-22s %6d rows", name, rows)
    LOGGER.info("wrote %d files (%.1f MB) to %s", len(written), total_bytes / 1e6, args.out)


if __name__ == "__main__":
    main()
