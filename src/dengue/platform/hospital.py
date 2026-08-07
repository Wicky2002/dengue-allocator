"""Hospital readiness planning from case forecasts.

Read this before trusting any number out of this module
--------------------------------------------------------
**Nothing here is a measurement.** No public source publishes Sri Lankan
hospital occupancy, ICU census, platelet stock, or staffing rosters. This module
takes the Stage 1 case forecast and applies **published clinical ratios** to
produce a *planning estimate*, in exactly the way a hospital planner would do it
on paper.

Every output is tagged :attr:`~dengue.platform.provenance.ProvenanceTier.ASSUMED`
and carries the ratio it used. The ratios are constructor parameters, not
hardcoded constants, so a hospital that knows its own case mix can substitute
real values and get an estimate grounded in its own data.

The ratios, and where they come from
------------------------------------
============================  =======  =========================================
Parameter                     Default  Basis
============================  =======  =========================================
Hospitalisation rate          0.55     Sri Lanka admits a high share of notified
                                       dengue: notification is largely
                                       hospital-driven, so the notified
                                       denominator is already skewed toward
                                       presenting cases. WHO 2009 guidance
                                       drives admission on warning signs.
Severe fraction (of admitted) 0.06     WHO 2009 severe-dengue classification;
                                       reported 2-10% of admissions in endemic
                                       Asian settings.
ICU fraction (of admitted)    0.02     Subset of severe cases needing organ
                                       support or shock management.
Paediatric fraction           0.30     Sri Lankan surveillance consistently
                                       shows a substantial paediatric share,
                                       though the adult share has risen.
Mean length of stay (days)    4.0      Typical uncomplicated dengue admission;
                                       severe cases run longer and are counted
                                       separately.
Platelet units per severe     4.0      Transfusion is indicated for a minority
                                       of severe cases; this is a *demand
                                       planning* figure, not a protocol.
IV fluid litres per admission 12.0     Fluid management is the mainstay of
                                       dengue care across a multi-day stay.
Nurses per occupied bed       0.25     ~1:4 nurse-to-bed on a general ward.
Doctors per occupied bed      0.05     ~1:20 doctor-to-bed on a general ward.
============================  =======  =========================================

These are **planning defaults for an endemic setting**, not Sri Lankan
measurements, and not a clinical protocol. They are the weakest link in this
module and are surfaced in the UI as editable inputs for that reason.

What this module deliberately does not do
------------------------------------------
It does not invent live occupancy, current stock levels, or staff rosters. Where
the platform would need those, it says the data is unavailable rather than
displaying a plausible number. See
:func:`dengue.platform.provenance.unavailable_reason`.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, replace

import pandas as pd

from dengue import config
from dengue.platform.provenance import ProvenanceTier, Quantity
from dengue.utils.logging import get_logger

log = get_logger(__name__)


@dataclass(frozen=True)
class ClinicalRatios:
    """Planning ratios converting notified cases into resource demand.

    Every field is a literature planning value, not a Sri Lankan measurement.
    See the module docstring for provenance of each default.
    """

    hospitalisation_rate: float = 0.55
    severe_fraction_of_admitted: float = 0.06
    icu_fraction_of_admitted: float = 0.02
    paediatric_fraction: float = 0.30
    mean_length_of_stay_days: float = 4.0
    severe_length_of_stay_days: float = 7.0
    platelet_units_per_severe_case: float = 4.0
    iv_fluid_litres_per_admission: float = 12.0
    nurses_per_occupied_bed: float = 0.25
    doctors_per_occupied_bed: float = 0.05
    diagnostic_tests_per_notified_case: float = 2.5

    def validate(self) -> None:
        """Raise if the ratio set is internally inconsistent."""
        if not 0.0 <= self.hospitalisation_rate <= 1.0:
            raise ValueError("hospitalisation_rate must be a fraction in [0, 1]")
        for name in (
            "severe_fraction_of_admitted",
            "icu_fraction_of_admitted",
            "paediatric_fraction",
        ):
            value = getattr(self, name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be a fraction in [0, 1]")
        if self.icu_fraction_of_admitted > self.severe_fraction_of_admitted:
            raise ValueError(
                "icu_fraction_of_admitted cannot exceed severe_fraction_of_admitted: "
                "ICU care is a subset of severe disease."
            )
        if self.mean_length_of_stay_days <= 0 or self.severe_length_of_stay_days <= 0:
            raise ValueError("Length of stay must be positive")


@dataclass(frozen=True)
class ReadinessEstimate:
    """Projected resource demand for one district-week.

    Every field is a **planning estimate**, not a measurement.
    """

    district_id: str
    district_name: str
    iso_week: pd.Period
    horizon_weeks: int

    forecast_cases: float
    forecast_cases_upper: float

    admissions: float
    admissions_upper: float
    severe_cases: float
    icu_patients: float
    paediatric_admissions: float

    bed_days: float
    peak_occupied_beds: float
    estimated_bed_capacity: int
    occupancy_pct: float

    platelet_units: float
    iv_fluid_litres: float
    diagnostic_tests: float

    additional_nurses: float
    additional_doctors: float

    ratios: ClinicalRatios

    @property
    def is_over_capacity(self) -> bool:
        return self.occupancy_pct > 100.0

    @property
    def capacity_status(self) -> str:
        """Four-band status for the hospital map."""
        if self.occupancy_pct > 100:
            return "over_capacity"
        if self.occupancy_pct > 85:
            return "near_capacity"
        if self.occupancy_pct > 60:
            return "busy"
        return "normal"

    def as_quantities(self) -> dict[str, Quantity]:
        """Every headline number, tagged with its provenance and basis."""
        r = self.ratios
        return {
            "admissions": Quantity(
                self.admissions,
                ProvenanceTier.ASSUMED,
                "admissions",
                basis=(
                    f"{r.hospitalisation_rate:.0%} hospitalisation rate applied to the "
                    f"{self.horizon_weeks}-week median case forecast"
                ),
                upper=self.admissions_upper,
            ),
            "icu_patients": Quantity(
                self.icu_patients,
                ProvenanceTier.ASSUMED,
                "patients",
                basis=f"{r.icu_fraction_of_admitted:.1%} of projected admissions",
            ),
            "peak_occupied_beds": Quantity(
                self.peak_occupied_beds,
                ProvenanceTier.ASSUMED,
                "beds",
                basis=(
                    f"{r.mean_length_of_stay_days:.0f}-day mean stay over projected "
                    "admissions, spread across the week"
                ),
            ),
            "occupancy_pct": Quantity(
                self.occupancy_pct,
                ProvenanceTier.ASSUMED,
                "%",
                basis=(
                    "Projected dengue bed-days against district capacity estimated from "
                    "World Bank national bed density — not live occupancy"
                ),
            ),
            "platelet_units": Quantity(
                self.platelet_units,
                ProvenanceTier.ASSUMED,
                "units",
                basis=(
                    f"{r.platelet_units_per_severe_case:.0f} units per severe case, "
                    f"severe = {r.severe_fraction_of_admitted:.0%} of admissions"
                ),
            ),
            "iv_fluid_litres": Quantity(
                self.iv_fluid_litres,
                ProvenanceTier.ASSUMED,
                "litres",
                basis=f"{r.iv_fluid_litres_per_admission:.0f} L per admission",
            ),
            "additional_nurses": Quantity(
                self.additional_nurses,
                ProvenanceTier.ASSUMED,
                "nurses",
                basis=f"{r.nurses_per_occupied_bed:.2f} nurses per occupied bed",
            ),
            "additional_doctors": Quantity(
                self.additional_doctors,
                ProvenanceTier.ASSUMED,
                "doctors",
                basis=f"{r.doctors_per_occupied_bed:.2f} doctors per occupied bed",
            ),
        }


def estimate_readiness(
    district_id: str,
    forecast_cases: float,
    *,
    iso_week: pd.Period,
    horizon_weeks: int,
    bed_capacity: int,
    forecast_cases_upper: float | None = None,
    ratios: ClinicalRatios | None = None,
    dengue_bed_share: float = 0.15,
) -> ReadinessEstimate:
    """Project resource demand for one district-week.

    Parameters
    ----------
    district_id:
        Canonical district key.
    forecast_cases:
        Median notified cases forecast for the target week.
    iso_week:
        Target week.
    horizon_weeks:
        Forecast lead time.
    bed_capacity:
        Estimated total beds in the district.
    forecast_cases_upper:
        Upper forecast bound, propagated to an upper admissions figure so
        planners can size against the bad case rather than the central one.
    ratios:
        Clinical planning ratios.
    dengue_bed_share:
        Fraction of district beds realistically available for dengue. Total beds
        overstate dengue capacity badly -- most are committed to surgery,
        obstetrics, and other medicine. Occupancy is computed against this share.

    Returns
    -------
    ReadinessEstimate
    """
    ratios = ratios or ClinicalRatios()
    ratios.validate()

    upper = forecast_cases_upper if forecast_cases_upper is not None else forecast_cases * 1.5

    admissions = forecast_cases * ratios.hospitalisation_rate
    admissions_upper = upper * ratios.hospitalisation_rate
    severe = admissions * ratios.severe_fraction_of_admitted
    icu = admissions * ratios.icu_fraction_of_admitted
    paediatric = admissions * ratios.paediatric_fraction

    # Bed-days: routine admissions at the mean stay, severe cases at the longer
    # one. Counting severe cases only once means subtracting them from routine.
    routine = max(admissions - severe, 0.0)
    bed_days = (
        routine * ratios.mean_length_of_stay_days + severe * ratios.severe_length_of_stay_days
    )
    # Concurrent beds occupied, averaged over the week.
    peak_beds = bed_days / 7.0

    dengue_capacity = max(bed_capacity * dengue_bed_share, 1.0)
    occupancy_pct = 100.0 * peak_beds / dengue_capacity

    return ReadinessEstimate(
        district_id=district_id,
        district_name=config.get_district(district_id).name
        if district_id in config.DISTRICT_BY_ID
        else district_id,
        iso_week=iso_week,
        horizon_weeks=horizon_weeks,
        forecast_cases=forecast_cases,
        forecast_cases_upper=upper,
        admissions=admissions,
        admissions_upper=admissions_upper,
        severe_cases=severe,
        icu_patients=icu,
        paediatric_admissions=paediatric,
        bed_days=bed_days,
        peak_occupied_beds=peak_beds,
        estimated_bed_capacity=int(dengue_capacity),
        occupancy_pct=occupancy_pct,
        platelet_units=severe * ratios.platelet_units_per_severe_case,
        iv_fluid_litres=admissions * ratios.iv_fluid_litres_per_admission,
        diagnostic_tests=forecast_cases * ratios.diagnostic_tests_per_notified_case,
        additional_nurses=math.ceil(peak_beds * ratios.nurses_per_occupied_bed),
        additional_doctors=math.ceil(peak_beds * ratios.doctors_per_occupied_bed),
        ratios=ratios,
    )


def build_readiness_table(
    district_risk: pd.DataFrame,
    capacity: pd.DataFrame,
    *,
    horizon_weeks: int,
    ratios: ClinicalRatios | None = None,
    dengue_bed_share: float = 0.15,
) -> pd.DataFrame:
    """Readiness estimates for every district at one horizon.

    Returns
    -------
    pandas.DataFrame
        One row per district with projected admissions, ICU, occupancy, supply
        demand and staffing. **All values are planning estimates.**
    """
    ratios = ratios or ClinicalRatios()
    beds_by_district = dict(zip(capacity["district_id"], capacity["estimated_beds"], strict=False))

    subset = district_risk[district_risk["horizon"] == horizon_weeks]
    rows: list[dict[str, object]] = []

    for _, row in subset.iterrows():
        district_id = str(row["district_id"])
        estimate = estimate_readiness(
            district_id,
            float(row.get("q0.5", 0.0) or 0.0),
            iso_week=row.get("target_week"),
            horizon_weeks=horizon_weeks,
            bed_capacity=int(beds_by_district.get(district_id, 500)),
            forecast_cases_upper=float(row.get("q0.9", 0.0) or 0.0),
            ratios=ratios,
            dengue_bed_share=dengue_bed_share,
        )
        rows.append(
            {
                "district_id": estimate.district_id,
                "district": estimate.district_name,
                "forecast_cases": estimate.forecast_cases,
                "admissions": estimate.admissions,
                "admissions_upper": estimate.admissions_upper,
                "severe_cases": estimate.severe_cases,
                "icu_patients": estimate.icu_patients,
                "paediatric_admissions": estimate.paediatric_admissions,
                "peak_occupied_beds": estimate.peak_occupied_beds,
                "dengue_bed_capacity": estimate.estimated_bed_capacity,
                "occupancy_pct": estimate.occupancy_pct,
                "capacity_status": estimate.capacity_status,
                "platelet_units": estimate.platelet_units,
                "iv_fluid_litres": estimate.iv_fluid_litres,
                "diagnostic_tests": estimate.diagnostic_tests,
                "additional_nurses": estimate.additional_nurses,
                "additional_doctors": estimate.additional_doctors,
                "horizon_weeks": horizon_weeks,
                "all_values_are_estimates": True,
            }
        )

    frame = pd.DataFrame(rows).sort_values("occupancy_pct", ascending=False).reset_index(drop=True)
    log.info(
        "hospital: readiness for %d districts at h=%d  total_admissions=%.0f  "
        "districts_over_capacity=%d",
        len(frame),
        horizon_weeks,
        frame["admissions"].sum() if not frame.empty else 0.0,
        int((frame["occupancy_pct"] > 100).sum()) if not frame.empty else 0,
    )
    return frame


def supply_shortfalls(
    readiness: pd.DataFrame, stock_on_hand: dict[str, dict[str, float]] | None = None
) -> pd.DataFrame:
    """Compare projected demand against stock, where stock is known.

    ``stock_on_hand`` maps ``district_id -> {"platelet_units": …, …}`` and would
    normally come from an inventory system. **Without it this returns demand
    only**, with the shortfall columns null — rather than inventing a stock level
    so a shortfall can be computed.
    """
    frame = readiness[
        ["district_id", "district", "platelet_units", "iv_fluid_litres", "diagnostic_tests"]
    ].copy()

    for column in ("platelet_units", "iv_fluid_litres", "diagnostic_tests"):
        if stock_on_hand:
            have = frame["district_id"].map(
                lambda d, c=column: (stock_on_hand.get(d, {}) or {}).get(c)
            )
            frame[f"{column}_on_hand"] = have
            frame[f"{column}_shortfall"] = (frame[column] - have).clip(lower=0)
        else:
            frame[f"{column}_on_hand"] = pd.NA
            frame[f"{column}_shortfall"] = pd.NA

    frame["stock_data_available"] = bool(stock_on_hand)
    return frame


def with_ratio_overrides(base: ClinicalRatios, **overrides: float) -> ClinicalRatios:
    """Return a copy of ``base`` with validated overrides applied."""
    updated = replace(base, **overrides)
    updated.validate()
    return updated
