"""Central configuration: paths, district registry, and frozen constants.

Everything that another workstream needs to agree on lives here. In particular
the *administrative* facts about Sri Lankan dengue reporting, which are subtle
enough to be worth stating once, loudly:

* There are **25 administrative districts**.
* There are **26 RDHS (Regional Director of Health Services) reporting
  divisions**: Kalmunai reports separately from the rest of Ampara district.
  Every Epidemiology Unit / NDCU weekly table therefore has 26 data rows, not
  25. Folding 26 rows down to 25 districts means summing Kalmunai back into
  Ampara -- see :func:`rdhs_to_district`.
* **Colombo Municipal Council (CMC)** is reported separately *inside* Colombo
  district in several NDCU products. CMC is not a 27th row of the standard WER
  district table, but it does appear as a distinct line in some NDCU bulletins
  and in high-risk MOH area designations. Where a source reports CMC
  separately, it must be **added into** Colombo, never treated as a peer
  district -- otherwise Colombo is systematically undercounted.

The canonical key used everywhere downstream is ``district_id``: a lowercase,
underscore-separated slug of the district name (e.g. ``"nuwara_eliya"``).
"""

from __future__ import annotations

import os
import re
import unicodedata
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Final

import networkx as nx

# --------------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------------

PACKAGE_ROOT: Final[Path] = Path(__file__).resolve().parent
REPO_ROOT: Final[Path] = PACKAGE_ROOT.parent.parent

_data_override = os.environ.get("DENGUE_DATA_DIR")
DATA_DIR: Final[Path] = Path(_data_override).resolve() if _data_override else REPO_ROOT / "data"

RAW_DIR: Final[Path] = DATA_DIR / "raw"
INTERIM_DIR: Final[Path] = DATA_DIR / "interim"
PROCESSED_DIR: Final[Path] = DATA_DIR / "processed"
ARTIFACTS_DIR: Final[Path] = REPO_ROOT / "artifacts"

PANEL_PATH: Final[Path] = PROCESSED_DIR / "panel.parquet"

#: Winning hyperparameters from `make tune` (dengue.tuning.runner). A small
#: derived config file the pipeline reads, not something the dashboard
#: renders -- so it lives beside PANEL_PATH in data/processed/, not in
#: artifacts/, which is documented as app-facing-only.
TUNED_PARAMS_PATH: Final[Path] = PROCESSED_DIR / "tuned_hyperparams.json"

RAW_COLMOZZIE: Final[Path] = RAW_DIR / "colmozzie"
RAW_OPENMETEO: Final[Path] = RAW_DIR / "openmeteo"
RAW_RELIEFWEB: Final[Path] = RAW_DIR / "reliefweb"
RAW_WER: Final[Path] = RAW_DIR / "wer"


def ensure_dirs() -> None:
    """Create every directory the pipeline writes to. Idempotent."""
    for d in (
        RAW_DIR,
        INTERIM_DIR,
        PROCESSED_DIR,
        ARTIFACTS_DIR,
        RAW_COLMOZZIE,
        RAW_OPENMETEO,
        RAW_RELIEFWEB,
        RAW_WER,
    ):
        d.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------------------------------
# Endpoints (overridable via .env)
# --------------------------------------------------------------------------

OPENMETEO_BASE_URL: Final[str] = os.environ.get(
    "OPENMETEO_BASE_URL", "https://archive-api.open-meteo.com/v1/archive"
)
# NOTE: ReliefWeb API v1 was decommissioned (HTTP 410 Gone). v2 is current, and
# from 2025-11-01 it expects a pre-approved ``appname``.
RELIEFWEB_BASE_URL: Final[str] = os.environ.get(
    "RELIEFWEB_BASE_URL", "https://api.reliefweb.int/v2"
)
RELIEFWEB_APPNAME: Final[str] = os.environ.get("RELIEFWEB_APPNAME", "dengue-allocator")
EPID_BASE_URL: Final[str] = os.environ.get("EPID_BASE_URL", "https://www.epid.gov.lk")
CRAN_BASE_URL: Final[str] = os.environ.get("CRAN_BASE_URL", "https://cran.r-project.org")

HTTP_TIMEOUT_SECONDS: Final[float] = float(os.environ.get("HTTP_TIMEOUT_SECONDS", "60"))
HTTP_USER_AGENT: Final[str] = "dengue-allocator/0.1 (research; AI Challenge Sri Lanka 2026)"


# --------------------------------------------------------------------------
# Panel schema -- THE CONTRACT. Do not change without updating every workstream.
# --------------------------------------------------------------------------

PANEL_COLUMNS: Final[tuple[str, ...]] = (
    "district_id",
    "iso_week",
    "cases",
    "population",
    "rain_mm",
    "tmax",
    "tmin",
    "rh",
    "high_risk_flag",
)

#: pandas dtypes for the panel. ``iso_week`` is a weekly ``Period`` anchored so
#: that each period starts on the ISO Monday; ``high_risk_flag`` uses the
#: nullable boolean so "unknown" is representable and distinct from False.
PANEL_DTYPES: Final[dict[str, str]] = {
    "district_id": "string",
    "iso_week": "period[W-SUN]",
    "cases": "Int64",
    "population": "Int64",
    "rain_mm": "float64",
    "tmax": "float64",
    "tmin": "float64",
    "rh": "float64",
    "high_risk_flag": "boolean",
}

#: Weekly period frequency. ``W-SUN`` means "week ending Sunday", i.e. periods
#: run Monday..Sunday, which is exactly the ISO-8601 week.
WEEK_FREQ: Final[str] = "W-SUN"

#: Forecast horizons in weeks (Stage 1 deliverable).
HORIZONS: Final[tuple[int, ...]] = (2, 3, 4)

#: Quantiles produced by every Stage 1 model.
QUANTILES: Final[tuple[float, ...]] = (0.1, 0.5, 0.9)

#: Nominal prediction-interval coverage implied by QUANTILES.
PI_NOMINAL_COVERAGE: Final[float] = 0.80

RANDOM_SEED: Final[int] = 20260809

# Default rolling-origin fold boundaries (see eval/backtest.py).
TRAIN_END_DEFAULT: Final[str] = "2023-12-31"
VAL_END_DEFAULT: Final[str] = "2024-12-31"

#: How far back `wer_pdf.download_recent` backfills by default. ~4 years gives
#: a full year of pure training history before TRAIN_END_DEFAULT, so a
#: WER-sourced panel lines up with the fold boundaries above instead of
#: starting mid-fold.
WER_BACKFILL_START: Final[str] = "2022-01-01"


# --------------------------------------------------------------------------
# District registry
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class District:
    """One Sri Lankan administrative district.

    Attributes
    ----------
    district_id:
        Canonical slug key used as the join key everywhere downstream.
    name:
        Display name in the Epidemiology Unit's preferred spelling.
    province:
        Province the district belongs to.
    lat, lon:
        Approximate population-weighted centroid, used for the Open-Meteo point
        query. Deliberately not a geometric centroid: in elongated districts the
        weather at the geometric centre can be unrepresentative of where people
        (and therefore *Aedes* breeding sites) actually are.
    population:
        Mid-year population estimate (persons), Department of Census &
        Statistics projections. Used for incidence normalisation and density
        features only -- this is not case data.
    area_km2:
        Land area in square kilometres.
    rdhs_divisions:
        RDHS reporting divisions that roll up into this district. Exactly one
        for every district except Ampara, which has two.
    """

    district_id: str
    name: str
    province: str
    lat: float
    lon: float
    population: int
    area_km2: float
    rdhs_divisions: tuple[str, ...]

    @property
    def density_per_km2(self) -> float:
        return self.population / self.area_km2


DISTRICTS: Final[tuple[District, ...]] = (
    District("colombo", "Colombo", "Western", 6.9271, 79.8612, 2_477_000, 699.0, ("Colombo",)),
    District("gampaha", "Gampaha", "Western", 7.0840, 80.0098, 2_499_000, 1387.0, ("Gampaha",)),
    District("kalutara", "Kalutara", "Western", 6.5854, 79.9607, 1_310_000, 1598.0, ("Kalutara",)),
    District("kandy", "Kandy", "Central", 7.2906, 80.6337, 1_508_000, 1940.0, ("Kandy",)),
    District("matale", "Matale", "Central", 7.4675, 80.6234, 524_000, 1993.0, ("Matale",)),
    District(
        "nuwara_eliya",
        "Nuwara Eliya",
        "Central",
        6.9497,
        80.7891,
        796_000,
        1741.0,
        ("Nuwara Eliya",),
    ),
    District("galle", "Galle", "Southern", 6.0535, 80.2210, 1_115_000, 1652.0, ("Galle",)),
    District("matara", "Matara", "Southern", 5.9549, 80.5550, 838_000, 1283.0, ("Matara",)),
    District(
        "hambantota", "Hambantota", "Southern", 6.1429, 81.1212, 673_000, 2609.0, ("Hambantota",)
    ),
    District("jaffna", "Jaffna", "Northern", 9.6615, 80.0255, 616_000, 1025.0, ("Jaffna",)),
    District(
        "kilinochchi", "Kilinochchi", "Northern", 9.3803, 80.3770, 129_000, 1279.0, ("Kilinochchi",)
    ),
    District("mannar", "Mannar", "Northern", 8.9810, 79.9044, 106_000, 1996.0, ("Mannar",)),
    District("vavuniya", "Vavuniya", "Northern", 8.7514, 80.4971, 190_000, 1967.0, ("Vavuniya",)),
    District(
        "mullaitivu", "Mullaitivu", "Northern", 9.2671, 80.8142, 100_000, 2617.0, ("Mullaitivu",)
    ),
    District(
        "batticaloa", "Batticaloa", "Eastern", 7.7102, 81.6924, 616_000, 2854.0, ("Batticaloa",)
    ),
    # Ampara district covers TWO RDHS reporting divisions: Ampara and Kalmunai.
    District(
        "ampara", "Ampara", "Eastern", 7.2917, 81.6747, 733_000, 4415.0, ("Ampara", "Kalmunai")
    ),
    District(
        "trincomalee",
        "Trincomalee",
        "Eastern",
        8.5874,
        81.2152,
        452_000,
        2727.0,
        ("Trincomalee",),
    ),
    District(
        "kurunegala",
        "Kurunegala",
        "North Western",
        7.4863,
        80.3647,
        1_759_000,
        4816.0,
        ("Kurunegala",),
    ),
    District(
        "puttalam", "Puttalam", "North Western", 8.0362, 79.8283, 838_000, 3072.0, ("Puttalam",)
    ),
    District(
        "anuradhapura",
        "Anuradhapura",
        "North Central",
        8.3114,
        80.4037,
        948_000,
        7179.0,
        ("Anuradhapura",),
    ),
    District(
        "polonnaruwa",
        "Polonnaruwa",
        "North Central",
        7.9403,
        81.0188,
        450_000,
        3293.0,
        ("Polonnaruwa",),
    ),
    District("badulla", "Badulla", "Uva", 6.9895, 81.0550, 903_000, 2861.0, ("Badulla",)),
    District("monaragala", "Monaragala", "Uva", 6.8728, 81.3510, 500_000, 5639.0, ("Monaragala",)),
    District(
        "ratnapura", "Ratnapura", "Sabaragamuwa", 6.6828, 80.3992, 1_182_000, 3275.0, ("Ratnapura",)
    ),
    District("kegalle", "Kegalle", "Sabaragamuwa", 7.2513, 80.3464, 872_000, 1693.0, ("Kegalle",)),
)


#: Number of administrative districts.
N_DISTRICTS: Final[int] = len(DISTRICTS)

#: RDHS reporting divisions, in Epidemiology Unit table order.
#: 26 entries: 25 districts plus Kalmunai.
RDHS_DIVISIONS: Final[tuple[str, ...]] = tuple(div for d in DISTRICTS for div in d.rdhs_divisions)
N_RDHS_DIVISIONS: Final[int] = len(RDHS_DIVISIONS)

#: Colombo Municipal Council is reported separately *within* Colombo district by
#: some NDCU products. Consumers must ADD it into Colombo, never treat it as a
#: peer district. See module docstring.
CMC_PARENT_DISTRICT: Final[str] = "colombo"

DISTRICT_BY_ID: Final[dict[str, District]] = {d.district_id: d for d in DISTRICTS}
DISTRICT_IDS: Final[tuple[str, ...]] = tuple(d.district_id for d in DISTRICTS)


def get_district(district_id: str) -> District:
    """Look up a district by canonical id, raising a helpful error if unknown."""
    try:
        return DISTRICT_BY_ID[district_id]
    except KeyError:
        raise KeyError(
            f"Unknown district_id {district_id!r}. Expected one of: {', '.join(DISTRICT_IDS)}"
        ) from None


def centroids() -> dict[str, tuple[float, float]]:
    """``district_id -> (lat, lon)`` for every district."""
    return {d.district_id: (d.lat, d.lon) for d in DISTRICTS}


def populations() -> dict[str, int]:
    """``district_id -> population`` for every district."""
    return {d.district_id: d.population for d in DISTRICTS}


def densities() -> dict[str, float]:
    """``district_id -> persons per km^2`` for every district."""
    return {d.district_id: d.density_per_km2 for d in DISTRICTS}


# --------------------------------------------------------------------------
# Name normalisation
# --------------------------------------------------------------------------

#: Spelling and transliteration variants seen across sources (Epidemiology Unit
#: WER PDFs, NDCU bulletins, ReliefWeb narrative text, HDX/GADM shapefiles,
#: colmozzie). Keys are pre-normalised by :func:`_squash` (lowercase,
#: punctuation stripped, whitespace collapsed).
_NAME_VARIANTS: Final[dict[str, str]] = {
    # Kalmunai is an RDHS division, not a district: it folds into Ampara.
    "kalmunai": "ampara",
    "ampara kalmunai": "ampara",
    "amparai": "ampara",
    "ampare": "ampara",
    # WER Table 1's narrow rotated-header column truncates some names --
    # confirmed on real 2022/2023 issues (2026's wider columns don't).
    "kalmune": "ampara",
    # Colombo Municipal Council folds into Colombo.
    "cmc": "colombo",
    "colombo mc": "colombo",
    "colombo municipal council": "colombo",
    "colombo municipality": "colombo",
    # Nuwara Eliya: spacing and hyphenation vary widely.
    "nuwaraeliya": "nuwara_eliya",
    "nuwara eliya": "nuwara_eliya",
    "nuwara elia": "nuwara_eliya",
    "nuweraeliya": "nuwara_eliya",
    # Northern districts: heavy transliteration variance.
    "killinochchi": "kilinochchi",
    "kilinochi": "kilinochchi",
    "killinochi": "kilinochchi",
    "mullaittivu": "mullaitivu",
    "mulaitivu": "mullaitivu",
    "mullativu": "mullaitivu",
    "mullaithivu": "mullaitivu",
    "vavunia": "vavuniya",
    "wavuniya": "vavuniya",
    "manner": "mannar",
    "mannar island": "mannar",
    # Eastern and other common variants.
    "batticoloa": "batticaloa",
    "batticalo": "batticaloa",
    "baticaloa": "batticaloa",
    "trincomallee": "trincomalee",
    "trinco": "trincomalee",
    "trincomalie": "trincomalee",
    "moneragala": "monaragala",
    "monoragala": "monaragala",
    "polonnaruva": "polonnaruwa",
    "polonaruwa": "polonnaruwa",
    "anuradhapure": "anuradhapura",
    "anuradapura": "anuradhapura",
    "anuradhapur": "anuradhapura",
    "kegalla": "kegalle",
    "kegale": "kegalle",
    "kagalle": "kegalle",
    "rathnapura": "ratnapura",
    "ratnapure": "ratnapura",
    "puttalama": "puttalam",
    "putlam": "puttalam",
    "chilaw": "puttalam",  # Chilaw is an MOH area within Puttalam district.
    "kurunagala": "kurunegala",
    "kurunegela": "kurunegala",
    "gampha": "gampaha",
    "kaluthara": "kalutara",
    "hambanthota": "hambantota",
    "hambantote": "hambantota",
    "mathale": "matale",
    "mathara": "matara",
}


def _squash(raw: str) -> str:
    """Aggressively normalise a raw name for lookup.

    Lowercases, strips accents, removes punctuation, drops reporting-structure
    words ("rdhs", "division"), and collapses whitespace. Idempotent.
    """
    s = unicodedata.normalize("NFKD", str(raw))
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = s.lower().strip()
    s = re.sub(r"[^a-z0-9\s]+", " ", s)
    s = re.sub(r"\b(rdhs|division|dist|distirct)\b", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


@lru_cache(maxsize=2048)
def normalise_district(raw: str, *, strict: bool = True) -> str | None:
    """Map a source-specific district/division name to a canonical ``district_id``.

    Handles spelling variants, RDHS divisions that are not districts (Kalmunai
    to Ampara), and Colombo Municipal Council (to Colombo).

    Parameters
    ----------
    raw:
        Name as it appears in the source.
    strict:
        If True (default), raise ``KeyError`` on an unrecognised name; if False,
        return ``None``. Ingest code should prefer ``strict=True`` so an upstream
        table-format change fails loudly rather than silently dropping a
        district.

    Returns
    -------
    The canonical ``district_id``, or ``None`` when ``strict=False`` and the name
    is unrecognised.

    Examples
    --------
    >>> normalise_district("Nuwara-Eliya District")
    'nuwara_eliya'
    >>> normalise_district("Kalmunai")
    'ampara'
    >>> normalise_district("CMC")
    'colombo'
    """
    if raw is None:
        if strict:
            raise KeyError("Cannot normalise district name: got None")
        return None

    squashed = _squash(raw)
    if not squashed:
        if strict:
            raise KeyError(f"Cannot normalise empty district name from {raw!r}")
        return None

    # 1. Explicit variant table.
    if squashed in _NAME_VARIANTS:
        return _NAME_VARIANTS[squashed]

    # 2. Direct match against canonical ids / display names.
    underscored = squashed.replace(" ", "_")
    if underscored in DISTRICT_BY_ID:
        return underscored

    # 3. Strip a trailing administrative suffix and retry once.
    stripped = re.sub(r"\b(district|municipal council|municipality|mc)\b", " ", squashed)
    stripped = re.sub(r"\s+", " ", stripped).strip()
    if stripped and stripped != squashed:
        if stripped in _NAME_VARIANTS:
            return _NAME_VARIANTS[stripped]
        cand = stripped.replace(" ", "_")
        if cand in DISTRICT_BY_ID:
            return cand

    if strict:
        raise KeyError(
            f"Unrecognised district name {raw!r} (normalised to {squashed!r}). "
            "Add it to _NAME_VARIANTS in dengue/config.py if it is a real variant."
        )
    return None


def rdhs_to_district(rdhs_name: str) -> str:
    """Map an RDHS reporting division name to its parent ``district_id``.

    This is what collapses the 26-row Epidemiology Unit table into the
    25-district panel: ``rdhs_to_district("Kalmunai") == "ampara"``.
    """
    result = normalise_district(rdhs_name, strict=True)
    assert result is not None  # strict=True never returns None
    return result


# --------------------------------------------------------------------------
# District adjacency graph
# --------------------------------------------------------------------------

#: Land-border adjacency between districts. Declared one-directionally and made
#: symmetric in :func:`district_graph`. Used for the neighbour-weighted
#: incidence feature and, later, for the STGNN's message-passing graph.
_ADJACENCY: Final[dict[str, tuple[str, ...]]] = {
    "colombo": ("gampaha", "kalutara", "ratnapura", "kegalle"),
    "gampaha": ("colombo", "kurunegala", "kegalle", "puttalam"),
    "kalutara": ("colombo", "ratnapura", "galle"),
    "kandy": ("matale", "nuwara_eliya", "badulla", "kegalle", "kurunegala"),
    "matale": ("kandy", "kurunegala", "anuradhapura", "polonnaruwa"),
    "nuwara_eliya": ("kandy", "badulla", "ratnapura"),
    "galle": ("kalutara", "matara", "ratnapura"),
    "matara": ("galle", "hambantota", "ratnapura"),
    "hambantota": ("matara", "ratnapura", "monaragala"),
    "jaffna": ("kilinochchi",),
    "kilinochchi": ("jaffna", "mullaitivu", "mannar", "vavuniya"),
    "mannar": ("kilinochchi", "vavuniya", "anuradhapura", "puttalam", "mullaitivu"),
    "vavuniya": ("kilinochchi", "mullaitivu", "mannar", "anuradhapura"),
    "mullaitivu": ("kilinochchi", "vavuniya", "anuradhapura", "trincomalee", "mannar"),
    "batticaloa": ("ampara", "polonnaruwa", "trincomalee"),
    "ampara": ("batticaloa", "monaragala", "badulla", "polonnaruwa"),
    "trincomalee": ("mullaitivu", "anuradhapura", "polonnaruwa", "batticaloa"),
    "kurunegala": ("gampaha", "puttalam", "anuradhapura", "matale", "kandy", "kegalle"),
    "puttalam": ("gampaha", "kurunegala", "anuradhapura", "mannar"),
    "anuradhapura": (
        "puttalam",
        "kurunegala",
        "matale",
        "polonnaruwa",
        "trincomalee",
        "mullaitivu",
        "vavuniya",
        "mannar",
    ),
    "polonnaruwa": ("anuradhapura", "matale", "batticaloa", "trincomalee", "ampara", "badulla"),
    "badulla": ("kandy", "nuwara_eliya", "monaragala", "ampara", "ratnapura", "polonnaruwa"),
    "monaragala": ("badulla", "ampara", "hambantota", "ratnapura"),
    "ratnapura": (
        "kalutara",
        "colombo",
        "kegalle",
        "nuwara_eliya",
        "badulla",
        "monaragala",
        "hambantota",
        "matara",
        "galle",
    ),
    "kegalle": ("colombo", "gampaha", "kurunegala", "kandy", "ratnapura"),
}


@lru_cache(maxsize=1)
def district_graph() -> nx.Graph:
    """Undirected district adjacency graph over all 25 districts.

    Every district is a node (even Jaffna, which has a single land neighbour),
    and the edge set is forced symmetric so ``_ADJACENCY`` only needs each
    border declared once.
    """
    g = nx.Graph()
    for d in DISTRICTS:
        g.add_node(
            d.district_id,
            name=d.name,
            province=d.province,
            lat=d.lat,
            lon=d.lon,
            population=d.population,
            density=d.density_per_km2,
        )
    for src, neighbours in _ADJACENCY.items():
        for dst in neighbours:
            if src not in DISTRICT_BY_ID or dst not in DISTRICT_BY_ID:
                raise ValueError(f"Adjacency references unknown district: {src} -> {dst}")
            g.add_edge(src, dst)
    return g


@lru_cache(maxsize=1)
def adjacency_map() -> dict[str, tuple[str, ...]]:
    """``district_id -> sorted tuple of neighbouring district_ids`` (symmetric)."""
    g = district_graph()
    return {node: tuple(sorted(g.neighbors(node))) for node in sorted(g.nodes)}


def validate_registry() -> None:
    """Assert the registry's internal invariants. Exercised by the test suite."""
    if len(DISTRICTS) != 25:
        raise ValueError(f"Expected 25 districts, found {len(DISTRICTS)}")
    if len(RDHS_DIVISIONS) != 26:
        raise ValueError(f"Expected 26 RDHS divisions, found {len(RDHS_DIVISIONS)}")
    if len(set(DISTRICT_IDS)) != len(DISTRICT_IDS):
        raise ValueError("Duplicate district_id in registry")
    g = district_graph()
    if g.number_of_nodes() != 25:
        raise ValueError(f"Adjacency graph has {g.number_of_nodes()} nodes, expected 25")
    isolated = [n for n in g.nodes if g.degree(n) == 0]
    if isolated:
        raise ValueError(f"Districts with no neighbours: {isolated}")
    for d in DISTRICTS:
        if not (5.8 <= d.lat <= 10.0) or not (79.5 <= d.lon <= 82.0):
            raise ValueError(f"Centroid for {d.district_id} is outside Sri Lanka's bounding box")
