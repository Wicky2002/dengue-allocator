"""Tests for facility_poor_districts: the bottom-k-by-density helper that
feeds Stage 3's allocation floor alongside the case-based high-risk flag."""

from __future__ import annotations

import pandas as pd

from dengue.ingest.health_facilities import facility_poor_districts


def _capacity(rows: list[tuple[str, int, int]]) -> pd.DataFrame:
    """Build a minimal capacity frame from (district_id, n_facilities, population)."""
    return pd.DataFrame(rows, columns=["district_id", "n_facilities", "population"])


def test_ranks_by_density_not_raw_facility_count():
    # "big" has more facilities in absolute terms than "small", but a much
    # larger population, so its density is actually the worse of the two.
    capacity = _capacity(
        [
            ("big", 10, 2_000_000),  # 0.5 per 100k -- worst
            ("small", 3, 200_000),  # 1.5 per 100k
            ("mid", 5, 250_000),  # 2.0 per 100k -- best
        ]
    )
    assert facility_poor_districts(capacity, bottom_k=1) == ("big",)
    assert facility_poor_districts(capacity, bottom_k=2) == ("big", "small")


def test_bottom_k_respects_the_requested_count():
    capacity = _capacity([(f"d{i}", i + 1, 100_000) for i in range(10)])
    result = facility_poor_districts(capacity, bottom_k=3)
    assert len(result) == 3
    # d0 has the fewest facilities (1) for equal population, so it is poorest.
    assert result[0] == "d0"


def test_returns_district_ids_as_strings():
    capacity = _capacity([("colombo", 20, 500_000), ("mannar", 1, 100_000)])
    result = facility_poor_districts(capacity, bottom_k=1)
    assert result == ("mannar",)
    assert all(isinstance(d, str) for d in result)
