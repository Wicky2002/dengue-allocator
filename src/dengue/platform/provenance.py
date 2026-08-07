"""Provenance tiers -- what every number on the platform is actually based on.

The problem this solves
-----------------------
This platform mixes three very different kinds of number on the same screen:

* **Notified dengue cases** -- an observation, from the Epidemiology Unit.
* **Forecast cases in three weeks** -- a model output, with a stated interval.
* **Platelet units needed next week** -- a *planning estimate*, derived by
  applying published clinical ratios to a forecast. No one measured it.

Rendered identically, the third borrows the credibility of the first. That is
how a decision-support tool ends up causing a bad decision: a planner reads
"platelet units: 65" as a measurement and orders against it.

So every quantity the platform surfaces carries a :class:`ProvenanceTier`, and
:class:`Quantity` refuses to be constructed without one. Making the tier a
required constructor argument -- rather than a convention -- is the point: it
cannot be forgotten under deadline pressure.

Tiers
-----
``OBSERVED``
    Measured and published by a named authority. Traceable to a source document.
``MODELLED``
    Produced by a model in this repo from observed inputs, with quantified
    uncertainty. Reproducible via ``make pipeline``.
``ASSUMED``
    Derived by applying a literature parameter or a stated assumption to a
    modelled or observed quantity. **Not measured for Sri Lanka**, and only as
    good as its assumption -- which is why the assumption travels with it.
``USER_INPUT``
    Supplied by the operator (e.g. a hospital entering its own bed count).
    Authoritative for that user, unverifiable by us.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class ProvenanceTier(str, Enum):
    """Where a number came from. Ordered from most to least trustworthy."""

    OBSERVED = "observed"
    MODELLED = "modelled"
    ASSUMED = "assumed"
    USER_INPUT = "user_input"

    @property
    def label(self) -> str:
        return {
            ProvenanceTier.OBSERVED: "Observed",
            ProvenanceTier.MODELLED: "Modelled",
            ProvenanceTier.ASSUMED: "Planning estimate",
            ProvenanceTier.USER_INPUT: "Entered by you",
        }[self]

    @property
    def description(self) -> str:
        return {
            ProvenanceTier.OBSERVED: "Measured and published by a named authority.",
            ProvenanceTier.MODELLED: (
                "Produced by a model in this repository from observed inputs, "
                "with quantified uncertainty."
            ),
            ProvenanceTier.ASSUMED: (
                "Derived by applying a published parameter to a modelled quantity. "
                "Not measured for Sri Lanka -- only as good as its assumption."
            ),
            ProvenanceTier.USER_INPUT: "Supplied by the operator; not verified by this system.",
        }[self]

    @property
    def badge(self) -> str:
        """Short marker for dense table cells."""
        return {
            ProvenanceTier.OBSERVED: "OBS",
            ProvenanceTier.MODELLED: "MOD",
            ProvenanceTier.ASSUMED: "EST",
            ProvenanceTier.USER_INPUT: "YOU",
        }[self]

    @property
    def requires_caveat(self) -> bool:
        """Whether the UI must show the basis alongside the number."""
        return self in (ProvenanceTier.ASSUMED, ProvenanceTier.USER_INPUT)


@dataclass(frozen=True)
class Quantity:
    """A number that knows what it is based on.

    Attributes
    ----------
    value:
        The number itself.
    tier:
        Provenance tier. **Required** -- there is no default, deliberately.
    unit:
        Unit for display, e.g. ``"cases"``, ``"beds"``, ``"units"``.
    basis:
        One-line statement of what the number rests on. Required for
        ``ASSUMED``: an unexplained planning estimate is the exact failure mode
        this module exists to prevent.
    source:
        Citation or dataset name for ``OBSERVED``.
    lower, upper:
        Optional interval bounds.

    Examples
    --------
    >>> q = Quantity(180.0, ProvenanceTier.ASSUMED, "admissions",
    ...              basis="12% hospitalisation rate applied to the median forecast")
    >>> q.render()
    '180 admissions (Planning estimate)'
    """

    value: float
    tier: ProvenanceTier
    unit: str = ""
    basis: str = ""
    source: str = ""
    lower: float | None = None
    upper: float | None = None

    def __post_init__(self) -> None:
        if self.tier is ProvenanceTier.ASSUMED and not self.basis:
            raise ValueError(
                "A Quantity tagged ASSUMED must state its basis. An unexplained "
                "planning estimate is indistinguishable from a fabricated number."
            )
        if self.tier is ProvenanceTier.OBSERVED and not self.source:
            raise ValueError("A Quantity tagged OBSERVED must name its source.")

    def render(self, digits: int = 0) -> str:
        """Human-readable value with its tier."""
        number = f"{self.value:,.{digits}f}"
        unit = f" {self.unit}" if self.unit else ""
        return f"{number}{unit} ({self.tier.label})"

    def caveat(self) -> str:
        """The line the UI must show beneath the number, or empty."""
        if self.tier is ProvenanceTier.ASSUMED:
            return f"Estimate — {self.basis}"
        if self.tier is ProvenanceTier.USER_INPUT:
            return "Entered by you; not verified by this system."
        if self.tier is ProvenanceTier.OBSERVED and self.source:
            return f"Source: {self.source}"
        return ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "value": self.value,
            "tier": self.tier.value,
            "unit": self.unit,
            "basis": self.basis,
            "source": self.source,
            "lower": self.lower,
            "upper": self.upper,
        }


#: Provenance of every data source the platform uses, for the UI's data page.
SOURCE_REGISTRY: dict[str, dict[str, str]] = {
    "colmozzie": {
        "tier": ProvenanceTier.OBSERVED.value,
        "name": "colmozzie (CRAN)",
        "licence": "CC0-1.0",
        "url": "https://cran.r-project.org/package=colmozzie",
        "covers": "Weekly notified dengue cases, Colombo, 2008-W52 to 2014-W21",
    },
    "epid_wer": {
        "tier": ProvenanceTier.OBSERVED.value,
        "name": "Epidemiology Unit Weekly Epidemiological Report",
        "licence": "Sri Lanka MoH publication",
        "url": "https://www.epid.gov.lk/weekly-epidemiological-report/",
        "covers": "District notified cases, 26 RDHS divisions",
    },
    "openmeteo": {
        "tier": ProvenanceTier.OBSERVED.value,
        "name": "Open-Meteo Archive (ERA5)",
        "licence": "CC-BY-4.0",
        "url": "https://archive-api.open-meteo.com/v1/archive",
        "covers": "Daily rainfall, temperature, humidity per district centroid",
    },
    "hdx_boundaries": {
        "tier": ProvenanceTier.OBSERVED.value,
        "name": "OCHA administrative boundaries (cod-ab-lka)",
        "licence": "CC-BY-IGO",
        "url": "https://data.humdata.org/dataset/cod-ab-lka",
        "covers": "District polygons for the choropleth maps",
    },
    "osm_facilities": {
        "tier": ProvenanceTier.OBSERVED.value,
        "name": "OpenStreetMap health facilities",
        "licence": "ODbL-1.0",
        "url": "https://www.openstreetmap.org/copyright",
        "covers": "Hospital and clinic locations. Bed tagging is sparse.",
    },
    "worldbank_beds": {
        "tier": ProvenanceTier.OBSERVED.value,
        "name": "World Bank — hospital beds per 1,000",
        "licence": "CC-BY-4.0",
        "url": "https://data.worldbank.org/indicator/SH.MED.BEDS.ZS",
        "covers": "National bed density; district split is estimated",
    },
    "forecast": {
        "tier": ProvenanceTier.MODELLED.value,
        "name": "Stage 1 quantile forecast",
        "licence": "this repository",
        "url": "src/dengue/models/",
        "covers": "District case forecasts at 2-4 weeks with 80% intervals",
    },
    "sei_sir": {
        "tier": ProvenanceTier.MODELLED.value,
        "name": "Stage 2 SEI-SIR intervention effects",
        "licence": "this repository",
        "url": "src/dengue/causal/sei_sir.py",
        "covers": "Cases averted per team-week, per district",
    },
    "clinical_ratios": {
        "tier": ProvenanceTier.ASSUMED.value,
        "name": "Clinical planning ratios (literature)",
        "licence": "see citations in platform/hospital.py",
        "url": "src/dengue/platform/hospital.py",
        "covers": (
            "Hospitalisation rate, ICU fraction, length of stay, platelet demand. "
            "NOT measured for Sri Lanka — published ranges applied to forecasts."
        ),
    },
}


def unavailable_reason(what: str) -> str:
    """Standard message for a capability with no public data behind it.

    Used instead of rendering a plausible-looking placeholder.
    """
    return (
        f"**{what} is not available.** No public data source publishes it for "
        "Sri Lanka. Connect an authoritative feed (HIMS export, MoH data-sharing "
        "agreement) to enable this panel. This platform will not display an "
        "invented figure in its place."
    )
