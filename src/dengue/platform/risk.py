"""Risk levels and the recommendation engine.

Turns a quantile forecast into the four-band risk level the maps use, and into
concrete actions per audience.

Why incidence, not case counts
------------------------------
Bands are set on **cases per 100,000 people**, not raw counts. Colombo has 2.48 M
residents and Mullaitivu 100 k; ranking by raw counts would paint Colombo red
every week of the year and leave a genuine Mullaitivu outbreak green. Incidence
is what makes districts comparable, and it is what the WHO outbreak thresholds
are expressed in.

Where the thresholds come from
------------------------------
The bands below are **operational planning thresholds**, not a clinical
standard. There is no internationally agreed incidence cut-off that defines a
dengue "outbreak" — thresholds in the literature are endemicity-specific and
usually derived per country. These are calibrated so that, on Sri Lanka's
historical district-week incidence distribution, roughly the top decile lands in
HIGH or above. They are exposed as constants and are meant to be re-calibrated
against real WER history before operational use.

Trend matters as much as level
------------------------------
A district at moderate incidence and rising fast needs a different response from
one at the same level and falling. :func:`assess_district` therefore combines the
band with the forecast trajectory, and the recommendations differ accordingly.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

import pandas as pd

from dengue import config
from dengue.platform.provenance import ProvenanceTier, Quantity


class RiskLevel(str, Enum):
    """Four-band risk level used across the maps and alerts."""

    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    SEVERE = "severe"

    @property
    def label(self) -> str:
        return {
            RiskLevel.LOW: "Low",
            RiskLevel.MODERATE: "Moderate",
            RiskLevel.HIGH: "High",
            RiskLevel.SEVERE: "Very high",
        }[self]

    @property
    def colour(self) -> str:
        """Map fill. Reserved status colours -- never reused as a series colour."""
        return {
            RiskLevel.LOW: "#0ca30c",
            RiskLevel.MODERATE: "#fab219",
            RiskLevel.HIGH: "#ec835a",
            RiskLevel.SEVERE: "#d03b3b",
        }[self]

    @property
    def rank(self) -> int:
        return {
            RiskLevel.LOW: 0,
            RiskLevel.MODERATE: 1,
            RiskLevel.HIGH: 2,
            RiskLevel.SEVERE: 3,
        }[self]


#: Weekly incidence per 100,000 at which each band begins. See module docstring:
#: operational planning thresholds, not a clinical standard.
RISK_THRESHOLDS: dict[RiskLevel, float] = {
    RiskLevel.LOW: 0.0,
    RiskLevel.MODERATE: 3.0,
    RiskLevel.HIGH: 8.0,
    RiskLevel.SEVERE: 16.0,
}

#: Week-over-week growth in the median forecast above which a district counts as
#: "rising fast" regardless of its band.
RAPID_GROWTH_THRESHOLD = 0.20


def classify(incidence_per_100k: float) -> RiskLevel:
    """Map weekly incidence per 100,000 to a risk band.

    Examples
    --------
    >>> classify(1.2).label
    'Low'
    >>> classify(20.0).label
    'Very high'
    """
    if incidence_per_100k >= RISK_THRESHOLDS[RiskLevel.SEVERE]:
        return RiskLevel.SEVERE
    if incidence_per_100k >= RISK_THRESHOLDS[RiskLevel.HIGH]:
        return RiskLevel.HIGH
    if incidence_per_100k >= RISK_THRESHOLDS[RiskLevel.MODERATE]:
        return RiskLevel.MODERATE
    return RiskLevel.LOW


@dataclass(frozen=True)
class Recommendation:
    """One recommended action.

    Attributes
    ----------
    action:
        Imperative statement of what to do.
    rationale:
        Why this follows from the forecast. Shown alongside the action, because
        an unexplained instruction from a model is not actionable.
    audience:
        Which role this is aimed at.
    urgency:
        ``routine`` | ``elevated`` | ``urgent``.
    """

    action: str
    rationale: str
    audience: str
    urgency: str = "routine"


@dataclass(frozen=True)
class DistrictAssessment:
    """Risk assessment for one district at one horizon.

    Attributes
    ----------
    district_id, district_name:
        Identity.
    risk_level:
        The band.
    incidence_per_100k:
        Forecast weekly incidence driving the band.
    forecast_median, forecast_lower, forecast_upper:
        Case forecast and its 80% interval.
    change_pct:
        Percentage change against the recent observed 4-week mean.
    is_rising_fast:
        Whether growth exceeds :data:`RAPID_GROWTH_THRESHOLD`.
    horizon_weeks:
        Forecast lead time.
    recommendations:
        Actions, ordered most urgent first.
    """

    district_id: str
    district_name: str
    risk_level: RiskLevel
    incidence_per_100k: float
    forecast_median: float
    forecast_lower: float
    forecast_upper: float
    change_pct: float
    is_rising_fast: bool
    horizon_weeks: int
    recommendations: tuple[Recommendation, ...] = field(default_factory=tuple)

    @property
    def headline(self) -> str:
        direction = "rising" if self.change_pct > 0 else "falling"
        return (
            f"{self.district_name}: {self.risk_level.label} risk, "
            f"{abs(self.change_pct):.0f}% {direction} over {self.horizon_weeks} weeks"
        )

    def as_quantity(self) -> Quantity:
        return Quantity(
            self.forecast_median,
            ProvenanceTier.MODELLED,
            "cases",
            basis=f"Stage 1 quantile forecast, {self.horizon_weeks}-week horizon",
            lower=self.forecast_lower,
            upper=self.forecast_upper,
        )


# --------------------------------------------------------------------------
# Recommendations
# --------------------------------------------------------------------------

_PUBLIC_ALWAYS = (
    Recommendation(
        "Remove standing water around your home weekly",
        "Aedes aegypti breeds in clean water in containers — tyres, tanks, plant "
        "trays, gutters. Removing habitat is the single most effective household action.",
        "public",
    ),
    Recommendation(
        "Seek medical care for fever lasting more than two days",
        "Early presentation is what prevents dengue haemorrhagic fever; severe "
        "disease is largely a complication of late fluid management.",
        "public",
    ),
)

_PUBLIC_ELEVATED = (
    Recommendation(
        "Use repellent and cover arms and legs during the day",
        "Aedes bites in daylight, peaking early morning and late afternoon — "
        "unlike the night-biting malaria vector, so bed nets alone are not enough.",
        "public",
        "elevated",
    ),
    Recommendation(
        "Fit window screens and use mosquito coils indoors",
        "Transmission in Sri Lanka is largely peri-domestic; most exposure happens "
        "in and around the home.",
        "public",
        "elevated",
    ),
)

_PUBLIC_SEVERE = (
    Recommendation(
        "Go to hospital immediately for warning signs",
        "Severe abdominal pain, persistent vomiting, bleeding gums, or lethargy "
        "indicate progression to severe dengue and need same-day assessment.",
        "public",
        "urgent",
    ),
    Recommendation(
        "Join or organise a neighbourhood clean-up",
        "Household-level source reduction only works at scale — a single treated "
        "property is re-colonised from neighbouring breeding sites within weeks.",
        "public",
        "urgent",
    ),
)


def _clinical_recommendations(assessment_level: RiskLevel, rising: bool) -> list[Recommendation]:
    out: list[Recommendation] = []
    if assessment_level.rank >= RiskLevel.HIGH.rank:
        out.append(
            Recommendation(
                "Review ward and fluid-management staffing for the coming fortnight",
                "Admissions track notified cases with roughly a one-week lag, so the "
                "forecast horizon is also the preparation window.",
                "hospital",
                "elevated",
            )
        )
        out.append(
            Recommendation(
                "Confirm platelet and IV fluid stock against projected demand",
                "Platelet demand is driven by the minority of admissions that progress "
                "to severe disease, so it scales faster than the admission count.",
                "hospital",
                "elevated",
            )
        )
    if assessment_level is RiskLevel.SEVERE:
        out.append(
            Recommendation(
                "Prepare overflow capacity and brief triage staff",
                "At this incidence, peak weekly occupancy is likely to exceed routine "
                "dengue-ward capacity.",
                "hospital",
                "urgent",
            )
        )
    if rising and assessment_level.rank >= RiskLevel.MODERATE.rank:
        out.append(
            Recommendation(
                "Bring forward elective admissions where clinically reasonable",
                "Creating headroom before the peak is cheaper than opening overflow "
                "capacity during it.",
                "hospital",
            )
        )
    return out


def _moh_recommendations(assessment_level: RiskLevel, rising: bool) -> list[Recommendation]:
    out: list[Recommendation] = []
    if assessment_level.rank >= RiskLevel.MODERATE.rank:
        out.append(
            Recommendation(
                "Prioritise this district in the weekly vector-team allocation",
                "Stage 3 places teams where the marginal cases averted per team-week "
                "is highest; a rising district's marginal return rises with it.",
                "moh",
                "elevated" if rising else "routine",
            )
        )
    if assessment_level.rank >= RiskLevel.HIGH.rank:
        out.extend(
            [
                Recommendation(
                    "Schedule source reduction in the highest-incidence MOH areas",
                    "Larval source reduction acts on carrying capacity — slower than "
                    "adulticiding but durable, so it is the right lever this far ahead "
                    "of the peak.",
                    "moh",
                    "elevated",
                ),
                Recommendation(
                    "Issue a public advisory for the district",
                    "Household source reduction needs several weeks of lead time to "
                    "affect the adult vector population.",
                    "moh",
                    "elevated",
                ),
            ]
        )
    if assessment_level is RiskLevel.SEVERE:
        out.append(
            Recommendation(
                "Deploy space spraying in confirmed transmission foci",
                "Adulticiding cuts the infectious adult population immediately. It is "
                "short-lived, so it is worth spending only when transmission is "
                "already high.",
                "moh",
                "urgent",
            )
        )
        out.append(
            Recommendation(
                "Coordinate with hospitals on referral and surge pathways",
                "At this level the constraint shifts from prevention to clinical " "capacity.",
                "moh",
                "urgent",
            )
        )
    return out


def recommend(
    risk_level: RiskLevel, *, rising_fast: bool = False, audience: str = "public"
) -> tuple[Recommendation, ...]:
    """Recommendations for a risk level and audience.

    Parameters
    ----------
    risk_level:
        The district's band.
    rising_fast:
        Whether growth exceeds :data:`RAPID_GROWTH_THRESHOLD`.
    audience:
        ``"public"``, ``"hospital"``, or ``"moh"``.
    """
    if audience == "public":
        items = list(_PUBLIC_ALWAYS)
        if risk_level.rank >= RiskLevel.MODERATE.rank or rising_fast:
            items.extend(_PUBLIC_ELEVATED)
        if risk_level is RiskLevel.SEVERE:
            items.extend(_PUBLIC_SEVERE)
    elif audience == "hospital":
        items = _clinical_recommendations(risk_level, rising_fast)
    elif audience == "moh":
        items = _moh_recommendations(risk_level, rising_fast)
    else:
        raise ValueError(f"Unknown audience {audience!r}")

    order = {"urgent": 0, "elevated": 1, "routine": 2}
    return tuple(sorted(items, key=lambda r: order.get(r.urgency, 3)))


def assess_district(
    row: pd.Series, *, horizon_weeks: int, audience: str = "public"
) -> DistrictAssessment:
    """Build a :class:`DistrictAssessment` from one row of the district-risk frame."""
    district_id = str(row["district_id"])
    incidence = float(row.get("incidence_per_100k", 0.0) or 0.0)
    change_pct = float(row.get("change_vs_recent_pct", 0.0) or 0.0)

    level = classify(incidence)
    rising = change_pct / 100.0 > RAPID_GROWTH_THRESHOLD

    return DistrictAssessment(
        district_id=district_id,
        district_name=config.get_district(district_id).name
        if district_id in config.DISTRICT_BY_ID
        else district_id,
        risk_level=level,
        incidence_per_100k=incidence,
        forecast_median=float(row.get("q0.5", 0.0) or 0.0),
        forecast_lower=float(row.get("q0.1", 0.0) or 0.0),
        forecast_upper=float(row.get("q0.9", 0.0) or 0.0),
        change_pct=change_pct,
        is_rising_fast=rising,
        horizon_weeks=horizon_weeks,
        recommendations=recommend(level, rising_fast=rising, audience=audience),
    )


def assess_all(
    district_risk: pd.DataFrame, *, horizon_weeks: int, audience: str = "public"
) -> list[DistrictAssessment]:
    """Assess every district in a district-risk frame, worst first."""
    subset = district_risk[district_risk["horizon"] == horizon_weeks]
    assessments = [
        assess_district(row, horizon_weeks=horizon_weeks, audience=audience)
        for _, row in subset.iterrows()
    ]
    return sorted(assessments, key=lambda a: (-a.risk_level.rank, -a.incidence_per_100k))


def national_summary(assessments: list[DistrictAssessment]) -> dict[str, object]:
    """Roll district assessments up to a national picture."""
    if not assessments:
        return {"total_forecast_cases": 0.0, "n_districts": 0}

    counts = {level: 0 for level in RiskLevel}
    for a in assessments:
        counts[a.risk_level] += 1

    return {
        "total_forecast_cases": sum(a.forecast_median for a in assessments),
        "n_districts": len(assessments),
        "n_severe": counts[RiskLevel.SEVERE],
        "n_high": counts[RiskLevel.HIGH],
        "n_moderate": counts[RiskLevel.MODERATE],
        "n_low": counts[RiskLevel.LOW],
        "n_rising_fast": sum(1 for a in assessments if a.is_rising_fast),
        "worst_district": assessments[0].district_name,
        "worst_level": assessments[0].risk_level.label,
    }
