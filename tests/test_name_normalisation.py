"""District name-normalisation tests.

Name normalisation is where silent data loss happens. A district whose spelling
drifts in one source gets dropped, and the panel quietly loses a row per week
without anything failing. These tests pin down the cases that actually differ
between the Epidemiology Unit PDFs, NDCU bulletins, and ReliefWeb narrative text.
"""

from __future__ import annotations

import pytest

from dengue import config
from dengue.config import normalise_district, rdhs_to_district


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        # Canonical forms round-trip.
        ("Colombo", "colombo"),
        ("colombo", "colombo"),
        ("COLOMBO", "colombo"),
        # Whitespace, punctuation, administrative suffixes.
        ("  Gampaha  ", "gampaha"),
        ("Gampaha District", "gampaha"),
        ("Kandy district", "kandy"),
        # Multi-word districts and their many spacings.
        ("Nuwara Eliya", "nuwara_eliya"),
        ("Nuwara-Eliya", "nuwara_eliya"),
        ("NuwaraEliya", "nuwara_eliya"),
        ("nuwara eliya", "nuwara_eliya"),
        ("Nuwara Eliya District", "nuwara_eliya"),
        # Transliteration variants seen in the Northern Province.
        ("Killinochchi", "kilinochchi"),
        ("Kilinochi", "kilinochchi"),
        ("Mullaittivu", "mullaitivu"),
        ("Mullativu", "mullaitivu"),
        ("Vavunia", "vavuniya"),
        # Other frequent variants.
        ("Moneragala", "monaragala"),
        ("Rathnapura", "ratnapura"),
        ("Kegalla", "kegalle"),
        ("Batticoloa", "batticaloa"),
        ("Trincomallee", "trincomalee"),
        ("Kaluthara", "kalutara"),
        ("Hambanthota", "hambantota"),
        ("Polonnaruva", "polonnaruwa"),
    ],
)
def test_variants_normalise_to_canonical_ids(raw, expected):
    assert normalise_district(raw) == expected


@pytest.mark.parametrize("raw", ["Kalmunai", "kalmunai", "KALMUNAI", "Ampara/Kalmunai"])
def test_kalmunai_folds_into_ampara(raw):
    """Kalmunai is an RDHS reporting division, not a district.

    Treating it as a 26th district would leave the panel with a phantom row and
    Ampara systematically undercounted.
    """
    assert normalise_district(raw) == "ampara"


@pytest.mark.parametrize(
    "raw", ["CMC", "cmc", "Colombo MC", "Colombo Municipal Council", "Colombo Municipality"]
)
def test_cmc_folds_into_colombo(raw):
    """CMC is reported inside Colombo district and must be added into it."""
    assert normalise_district(raw) == config.CMC_PARENT_DISTRICT == "colombo"


def test_rdhs_divisions_all_map_to_districts():
    """All 26 RDHS divisions must resolve, collapsing to 25 districts."""
    mapped = {rdhs_to_district(division) for division in config.RDHS_DIVISIONS}
    assert len(config.RDHS_DIVISIONS) == 26
    assert mapped == set(config.DISTRICT_IDS)
    assert len(mapped) == 25


def test_every_canonical_name_normalises_to_itself():
    for district in config.DISTRICTS:
        assert normalise_district(district.name) == district.district_id
        assert normalise_district(district.district_id) == district.district_id


def test_unknown_name_raises_when_strict():
    with pytest.raises(KeyError, match="Unrecognised district name"):
        normalise_district("Atlantis")


def test_unknown_name_returns_none_when_not_strict():
    assert normalise_district("Atlantis", strict=False) is None


def test_empty_and_none_are_handled():
    assert normalise_district("", strict=False) is None
    assert normalise_district("   ", strict=False) is None
    assert normalise_district(None, strict=False) is None
    with pytest.raises(KeyError):
        normalise_district("")


def test_normalisation_is_idempotent():
    for district in config.DISTRICTS:
        once = normalise_district(district.name)
        assert normalise_district(once) == once


def test_adjacency_is_symmetric_and_complete():
    adjacency = config.adjacency_map()
    assert set(adjacency) == set(config.DISTRICT_IDS)
    for district, neighbours in adjacency.items():
        for neighbour in neighbours:
            assert (
                district in adjacency[neighbour]
            ), f"Adjacency is asymmetric: {district}-{neighbour}"


def test_known_borders_are_present():
    """Spot-check real geography so a typo in the adjacency table is caught."""
    adjacency = config.adjacency_map()
    assert "gampaha" in adjacency["colombo"]
    assert "kalutara" in adjacency["colombo"]
    assert "kilinochchi" in adjacency["jaffna"]
    # Jaffna is a peninsula: exactly one land neighbour.
    assert len(adjacency["jaffna"]) == 1
    # Anuradhapura is the most-connected district.
    assert len(adjacency["anuradhapura"]) >= 7
