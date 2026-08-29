/**
 * Risk bands, mirrored from the engine.
 *
 * The thresholds and colours are not written here -- they are generated from
 * `dengue.platform.risk` into `src/generated/constants.json` by
 * `make export-web`. A band cut-off that drifted between the engine and the map
 * would paint a district the wrong colour with nothing failing anywhere, so
 * there is exactly one place to change it and it is on the Python side.
 */

import constants from '@/generated/constants.json';

export type RiskKey = 'low' | 'moderate' | 'high' | 'severe';

export interface RiskBand {
  key: RiskKey;
  label: string;
  colour: string;
  threshold: number;
}

export const RISK_BANDS: RiskBand[] = constants.riskLevels as RiskBand[];

export const RAPID_GROWTH_THRESHOLD: number = constants.rapidGrowthThreshold;

const DESCENDING = [...RISK_BANDS].sort((a, b) => b.threshold - a.threshold);

/** Weekly incidence per 100,000 -> risk band. Mirrors `risk.classify`. */
export function classify(incidencePer100k: number | null | undefined): RiskBand {
  if (incidencePer100k == null || Number.isNaN(incidencePer100k)) {
    return RISK_BANDS[0];
  }
  return DESCENDING.find((band) => incidencePer100k >= band.threshold) ?? RISK_BANDS[0];
}

/** Tailwind classes for a band, for chips and table cells. */
export function bandClasses(key: RiskKey): string {
  return {
    low: 'bg-teal-50 text-teal-800 ring-1 ring-teal-600/20',
    moderate: 'bg-amber-50 text-amber-800 ring-1 ring-amber-600/20',
    high: 'bg-orange-50 text-orange-800 ring-1 ring-orange-600/25',
    severe: 'bg-red-50 text-red-800 ring-1 ring-red-600/25',
  }[key];
}

/** Whether week-over-week growth counts as "rising fast". */
export function isRisingFast(changeFraction: number | null | undefined): boolean {
  return changeFraction != null && changeFraction > RAPID_GROWTH_THRESHOLD;
}
