/**
 * Selections over the exported artifacts.
 *
 * Everything here is a filter, a join, a sort or a sum over rows the pipeline
 * already wrote. No epidemiological quantity is derived: incidence, quantiles,
 * cases averted and readiness figures all arrive precomputed, because a number
 * computed in the browser has no provenance tier attached to it and no test
 * covering it.
 */

import { classify, type RiskBand } from './risk';
import type { DistrictRisk, District, PanelRow, PredictionHistory, ScoreRow } from './types';

export interface RankedDistrict {
  district_id: string;
  name: string;
  province: string;
  population: number;
  median: number | null;
  lower: number | null;
  upper: number | null;
  incidence: number | null;
  intervalWidth: number | null;
  band: RiskBand;
  rank: number;
}

/**
 * Every district at one horizon, ranked by forecast incidence.
 *
 * Ranked on incidence per 100,000, never on raw case counts: Colombo has 2.48 M
 * residents and Mullaitivu ~100 k, so a count ranking would paint Colombo worst
 * every week of the year and hide a genuine Mullaitivu outbreak.
 */
export function rankDistricts(
  risk: DistrictRisk[],
  districts: District[],
  horizon: number,
): RankedDistrict[] {
  const byId = new Map(districts.map((d) => [d.district_id, d]));
  return risk
    .filter((row) => row.horizon === horizon)
    .map((row) => {
      const district = byId.get(row.district_id);
      return {
        district_id: row.district_id,
        name: district?.name ?? row.district_id,
        province: district?.province ?? '—',
        population: district?.population ?? row.population ?? 0,
        median: row['q0.5'],
        lower: row['q0.1'],
        upper: row['q0.9'],
        incidence: row.incidence_per_100k,
        intervalWidth: row.interval_width,
        band: classify(row.incidence_per_100k),
      };
    })
    .sort((a, b) => (b.incidence ?? -1) - (a.incidence ?? -1))
    .map((row, index) => ({ ...row, rank: index + 1 }));
}

export interface NationalSummary {
  nDistricts: number;
  nElevated: number;
  totalForecastCases: number;
  worst: RankedDistrict | null;
  targetWeek: string | null;
  bandCounts: Record<string, number>;
}

/** The four headline figures shared by the landing page and the overview. */
export function nationalSummary(
  ranked: RankedDistrict[],
  risk: DistrictRisk[],
  horizon: number,
): NationalSummary {
  const bandCounts: Record<string, number> = { low: 0, moderate: 0, high: 0, severe: 0 };
  for (const row of ranked) bandCounts[row.band.key] += 1;

  const targetWeek =
    risk.find((row) => row.horizon === horizon && row.target_week)?.target_week ?? null;

  return {
    nDistricts: ranked.length,
    nElevated: bandCounts.high + bandCounts.severe,
    totalForecastCases: ranked.reduce((sum, row) => sum + (row.median ?? 0), 0),
    worst: ranked[0] ?? null,
    targetWeek,
    bandCounts,
  };
}

export interface WeeklyPoint {
  week: string;
  cases: number;
}

/** Nationwide observed weekly cases, most recent `weeks` first-to-last. */
export function nationalTrend(panel: PanelRow[], weeks = 52): WeeklyPoint[] {
  const totals = new Map<string, number>();
  for (const row of panel) {
    if (!row.iso_week || row.cases == null) continue;
    totals.set(row.iso_week, (totals.get(row.iso_week) ?? 0) + row.cases);
  }
  return Array.from(totals.entries())
    .map(([week, cases]) => ({ week, cases }))
    .sort((a, b) => a.week.localeCompare(b.week))
    .slice(-weeks);
}

/** One district's observed weekly history, oldest first. */
export function districtTrend(
  panel: PanelRow[],
  districtId: string,
  weeks = 52,
): (WeeklyPoint & { rain: number | null; tmax: number | null })[] {
  return panel
    .filter((row) => row.district_id === districtId && row.iso_week)
    .sort((a, b) => (a.iso_week ?? '').localeCompare(b.iso_week ?? ''))
    .slice(-weeks)
    .map((row) => ({
      week: row.iso_week as string,
      cases: row.cases ?? 0,
      rain: row.rain_mm,
      tmax: row.tmax,
    }));
}

/** Week-over-week change in observed national cases, as a fraction. */
export function weekOverWeekChange(trend: WeeklyPoint[]): number | null {
  if (trend.length < 2) return null;
  const previous = trend[trend.length - 2].cases;
  const latest = trend[trend.length - 1].cases;
  if (previous === 0) return null;
  return (latest - previous) / previous;
}

export interface ForecastPoint {
  week: string;
  observed: number | null;
  median: number | null;
  /** Recharts stacks an area from a [low, high] tuple -- the 80% interval. */
  interval: [number, number] | null;
}

/**
 * Nationwide observed history joined to the forecast, for one continuous chart.
 *
 * The forecast is summed across districts. That sum is deliberately shown with
 * its interval rather than as a single line: adding 25 medians together gives a
 * number no district-level median guarantees, and the band is what stops it
 * being read as a precise national prediction.
 */
export function nationalForecastSeries(
  trend: WeeklyPoint[],
  forecasts: { target_week: string | null; 'q0.5': number | null; 'q0.1': number | null; 'q0.9': number | null; horizon: number }[],
  horizons: number[],
): ForecastPoint[] {
  const byWeek = new Map<string, { median: number; lower: number; upper: number }>();
  for (const row of forecasts) {
    if (!row.target_week) continue;
    const entry = byWeek.get(row.target_week) ?? { median: 0, lower: 0, upper: 0 };
    entry.median += row['q0.5'] ?? 0;
    entry.lower += row['q0.1'] ?? 0;
    entry.upper += row['q0.9'] ?? 0;
    byWeek.set(row.target_week, entry);
  }

  const points: ForecastPoint[] = trend.map((point) => ({
    week: point.week,
    observed: point.cases,
    median: null,
    interval: null,
  }));

  // Join the forecast onto the last observed week so the two lines meet instead
  // of leaving a visual gap the reader has to bridge themselves.
  const lastObserved = points.at(-1);
  if (lastObserved) {
    lastObserved.median = lastObserved.observed;
    lastObserved.interval = [lastObserved.observed ?? 0, lastObserved.observed ?? 0];
  }

  for (const [week, entry] of Array.from(byWeek.entries()).sort((a, b) => a[0].localeCompare(b[0]))) {
    points.push({
      week,
      observed: null,
      median: entry.median,
      interval: [entry.lower, entry.upper],
    });
  }
  return points;
}

export interface RainfallPoint {
  week: string;
  cases: number;
  rain: number | null;
}

/** Nationwide weekly cases beside mean rainfall, for the lag chart. */
export function rainfallSeries(panel: PanelRow[], weeks = 104): RainfallPoint[] {
  const byWeek = new Map<string, { cases: number; rainSum: number; rainCount: number }>();
  for (const row of panel) {
    if (!row.iso_week) continue;
    const entry = byWeek.get(row.iso_week) ?? { cases: 0, rainSum: 0, rainCount: 0 };
    entry.cases += row.cases ?? 0;
    if (row.rain_mm != null) {
      entry.rainSum += row.rain_mm;
      entry.rainCount += 1;
    }
    byWeek.set(row.iso_week, entry);
  }
  return Array.from(byWeek.entries())
    .sort((a, b) => a[0].localeCompare(b[0]))
    .slice(-weeks)
    .map(([week, entry]) => ({
      week,
      cases: entry.cases,
      rain: entry.rainCount > 0 ? entry.rainSum / entry.rainCount : null,
    }));
}

export interface ModelScore {
  model: string;
  value: number;
  folds: number;
}

/**
 * Mean score per model at one horizon, for one metric, best first.
 *
 * Averaged across backtest folds, which is what the comparison table in
 * `make baseline` reports -- a single fold's winner is noise.
 */
export function modelComparison(
  scores: ScoreRow[],
  metric: string,
  horizon: number,
  lowerIsBetter = true,
): ModelScore[] {
  const byModel = new Map<string, number[]>();
  for (const row of scores) {
    if (row.metric !== metric || row.horizon !== horizon || row.value == null) continue;
    byModel.set(row.model, [...(byModel.get(row.model) ?? []), row.value]);
  }
  return Array.from(byModel.entries())
    .map(([model, values]) => ({
      model,
      value: values.reduce((sum, value) => sum + value, 0) / values.length,
      folds: values.length,
    }))
    .sort((a, b) => (lowerIsBetter ? a.value - b.value : b.value - a.value));
}

export interface HistoryCell {
  district_id: string;
  incidence: number | null;
  cases: number | null;
}

export interface HistorySeries {
  /** Every week the scrubber can land on, ascending. */
  weeks: string[];
  byWeek: Record<string, HistoryCell[]>;
}

/**
 * Observed incidence per district, week by week.
 *
 * Incidence is derived here from the cases and population the panel already
 * carries — the same `cases / population * 100,000` the engine uses to band a
 * district. It is arithmetic on two observed columns, not a new estimate, so
 * the result stays in the observed tier.
 */
export function observedHistory(panel: PanelRow[]): HistorySeries {
  const byWeek: Record<string, HistoryCell[]> = {};

  for (const row of panel) {
    if (!row.iso_week) continue;
    const population = row.population ?? 0;
    (byWeek[row.iso_week] ??= []).push({
      district_id: row.district_id,
      incidence: population > 0 && row.cases != null ? (row.cases / population) * 100_000 : null,
      cases: row.cases,
    });
  }

  return { weeks: Object.keys(byWeek).sort(), byWeek };
}

/**
 * What the model predicted for each week, at one horizon.
 *
 * Keyed on the **target** week — the week being described — not the origin the
 * model was standing at when it made the call. That is what makes the two maps
 * comparable: both answer a question about the same week, one with hindsight
 * and one with only the data available a fortnight earlier.
 */
export function predictedHistory(history: PredictionHistory[], horizon: number): HistorySeries {
  const byWeek: Record<string, HistoryCell[]> = {};

  for (const row of history) {
    if (row.horizon !== horizon || !row.target_week) continue;
    (byWeek[row.target_week] ??= []).push({
      district_id: row.district_id,
      incidence: row.predicted_incidence_per_100k,
      cases: row['q0.5'],
    });
  }

  return { weeks: Object.keys(byWeek).sort(), byWeek };
}

/** Total cases and worst district for one week of either series. */
export function weekSummary(cells: HistoryCell[] | undefined, names: Record<string, string>) {
  if (!cells || cells.length === 0) return null;
  const total = cells.reduce((sum, cell) => sum + (cell.cases ?? 0), 0);
  const worst = [...cells].sort((a, b) => (b.incidence ?? -1) - (a.incidence ?? -1))[0];
  return { total, worst, worstName: names[worst.district_id] ?? worst.district_id };
}
