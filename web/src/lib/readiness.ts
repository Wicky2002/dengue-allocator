/**
 * Hospital readiness arithmetic.
 *
 * A mirror of `dengue.platform.hospital.project_readiness`, kept here because
 * the ratios are adjustable in the browser and the table has to follow the
 * slider without a round trip. The default ratio values are *not* duplicated:
 * they come from `src/generated/constants.json`, published by the engine.
 *
 * Every quantity this produces is a **planning estimate** — a published
 * clinical ratio applied to a model forecast, not a measurement of Sri Lankan
 * practice. Each carries its basis string, and the UI is required to render
 * both together (see `ProvenanceChip`).
 *
 * This is multiplication over 25 rows, not a model refit, so it does not breach
 * the platform's rule against computing at request time — that rule exists to
 * stop a page re-solving Stage 1 or Stage 3, which this does not touch.
 */

import constants from '@/generated/constants.json';

export interface ClinicalRatios {
  hospitalisation_rate: number;
  severe_fraction_of_admitted: number;
  icu_fraction_of_admitted: number;
  paediatric_fraction: number;
  mean_length_of_stay_days: number;
  severe_length_of_stay_days: number;
  platelet_units_per_severe_case: number;
  iv_fluid_litres_per_admission: number;
  nurses_per_occupied_bed: number;
  doctors_per_occupied_bed: number;
  diagnostic_tests_per_notified_case: number;
}

export const DEFAULT_RATIOS: ClinicalRatios = constants.clinicalRatios as ClinicalRatios;
export const DENGUE_BED_SHARE: number = constants.dengueBedShare;

/** Mirrors `ClinicalRatios.validate`, including the ICU ⊆ severe constraint. */
export function validateRatios(ratios: ClinicalRatios): string | null {
  const fractions: (keyof ClinicalRatios)[] = [
    'hospitalisation_rate',
    'severe_fraction_of_admitted',
    'icu_fraction_of_admitted',
    'paediatric_fraction',
  ];
  for (const key of fractions) {
    const value = ratios[key];
    if (value < 0 || value > 1) return `${key} must be between 0 and 1.`;
  }
  if (ratios.icu_fraction_of_admitted > ratios.severe_fraction_of_admitted) {
    return 'ICU fraction cannot exceed the severe fraction: ICU care is a subset of severe disease.';
  }
  if (ratios.mean_length_of_stay_days <= 0 || ratios.severe_length_of_stay_days <= 0) {
    return 'Length of stay must be positive.';
  }
  return null;
}

export interface Readiness {
  district_id: string;
  district: string;
  forecastCases: number;
  admissions: number;
  admissionsUpper: number;
  severeCases: number;
  icuPatients: number;
  paediatricAdmissions: number;
  bedDays: number;
  peakOccupiedBeds: number;
  dengueBedCapacity: number;
  occupancyPct: number;
  plateletUnits: number;
  ivFluidLitres: number;
  diagnosticTests: number;
  additionalNurses: number;
  additionalDoctors: number;
  capacityStatus: 'Over capacity' | 'Critical' | 'Stretched' | 'Comfortable';
  nHospitals: number;
  nFacilities: number;
  facilitiesPer100k: number;
}

function capacityStatus(occupancyPct: number): Readiness['capacityStatus'] {
  if (occupancyPct > 100) return 'Over capacity';
  if (occupancyPct > 85) return 'Critical';
  if (occupancyPct > 60) return 'Stretched';
  return 'Comfortable';
}

export function projectReadiness(
  input: {
    district_id: string;
    district: string;
    forecastCases: number;
    forecastUpper: number | null;
    estimatedBeds: number;
    nHospitals: number;
    nFacilities: number;
    population: number;
  },
  ratios: ClinicalRatios = DEFAULT_RATIOS,
): Readiness {
  const upper = input.forecastUpper ?? input.forecastCases * 1.5;

  const admissions = input.forecastCases * ratios.hospitalisation_rate;
  const severe = admissions * ratios.severe_fraction_of_admitted;
  const icu = admissions * ratios.icu_fraction_of_admitted;

  // Routine admissions at the mean stay, severe at the longer one. Severe cases
  // are subtracted from routine so a bed-day is never counted twice.
  const routine = Math.max(admissions - severe, 0);
  const bedDays =
    routine * ratios.mean_length_of_stay_days + severe * ratios.severe_length_of_stay_days;
  const peakBeds = bedDays / 7;

  const dengueCapacity = Math.max(input.estimatedBeds * DENGUE_BED_SHARE, 1);
  const occupancyPct = (100 * peakBeds) / dengueCapacity;

  return {
    district_id: input.district_id,
    district: input.district,
    forecastCases: input.forecastCases,
    admissions,
    admissionsUpper: upper * ratios.hospitalisation_rate,
    severeCases: severe,
    icuPatients: icu,
    paediatricAdmissions: admissions * ratios.paediatric_fraction,
    bedDays,
    peakOccupiedBeds: peakBeds,
    dengueBedCapacity: Math.floor(dengueCapacity),
    occupancyPct,
    plateletUnits: severe * ratios.platelet_units_per_severe_case,
    ivFluidLitres: admissions * ratios.iv_fluid_litres_per_admission,
    diagnosticTests: input.forecastCases * ratios.diagnostic_tests_per_notified_case,
    additionalNurses: Math.ceil(peakBeds * ratios.nurses_per_occupied_bed),
    additionalDoctors: Math.ceil(peakBeds * ratios.doctors_per_occupied_bed),
    capacityStatus: capacityStatus(occupancyPct),
    nHospitals: input.nHospitals,
    nFacilities: input.nFacilities,
    facilitiesPer100k: input.population > 0 ? (input.nFacilities / input.population) * 100_000 : 0,
  };
}

/** The basis line every readiness figure must be rendered with. */
export function ratioBasis(ratios: ClinicalRatios, customised: boolean): string {
  return (
    `${(ratios.hospitalisation_rate * 100).toFixed(0)}% hospitalisation rate, ` +
    `${(ratios.severe_fraction_of_admitted * 100).toFixed(0)}% severe, ` +
    `${(ratios.icu_fraction_of_admitted * 100).toFixed(1)}% ICU, ` +
    `${ratios.mean_length_of_stay_days.toFixed(0)}-day mean stay ` +
    `(${customised ? 'your ratios' : 'defaults'}). Occupancy is against district beds ` +
    'estimated from World Bank national bed density, assuming 15% are available for dengue.'
  );
}
