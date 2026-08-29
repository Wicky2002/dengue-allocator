/**
 * Server-side access to the exported pipeline artifacts.
 *
 * Reads the JSON written by `make export-web` straight off disk at render time
 * on the server, and caches it for the lifetime of the process. Nothing here
 * computes an epidemiological quantity -- it selects, joins and sorts rows the
 * pipeline already produced. Anything that derives a *new* number belongs in
 * the Python pipeline, where it is tested and where its provenance tier is
 * enforced at construction.
 *
 * Reading from disk rather than fetching over HTTP means the browser never
 * downloads a 1.3 MB bundle to render a 10-row table: pages ship only the rows
 * they actually display.
 */

import { promises as fs } from 'fs';
import path from 'path';
import { cache } from 'react';

import type {
  AllocationRow,
  Assessment,
  AllocationSummary,
  BudgetRow,
  District,
  DistrictCapacity,
  DistrictGeometry,
  DistrictRisk,
  EffectRow,
  HealthFacility,
  HospitalReadiness,
  PanelRow,
  PipelineMeta,
  PredictionHistory,
  ScenarioRow,
  ScoreRow,
  SeiSirParams,
} from './types';

const DATA_DIR = path.join(process.cwd(), 'public', 'data');

/**
 * Load one exported artifact.
 *
 * A missing file is not an error: it degrades the panel that needs it and
 * leaves every other panel intact, matching the Streamlit app's rule. The
 * caller decides what to render in its place, which is always an explanation
 * rather than a zero -- a zero would be indistinguishable from a real count.
 */
export async function readJson<T>(name: string): Promise<T[]> {
  try {
    const raw = await fs.readFile(path.join(DATA_DIR, `${name}.json`), 'utf-8');
    return JSON.parse(raw) as T[];
  } catch (error) {
    const code = (error as NodeJS.ErrnoException).code;
    if (code === 'ENOENT') return [];
    throw error;
  }
}

export const getMeta = cache(async (): Promise<PipelineMeta | null> => {
  const rows = await readJson<PipelineMeta>('pipeline_meta');
  return rows[0] ?? null;
});

export const getDistricts = cache(() => readJson<District>('districts'));
export const getDistrictRisk = cache(() => readJson<DistrictRisk>('district_risk'));
export const getPanel = cache(() => readJson<PanelRow>('panel_recent'));
export const getHospitalReadiness = cache(() => readJson<HospitalReadiness>('hospital_readiness'));
export const getDistrictCapacity = cache(() => readJson<DistrictCapacity>('district_capacity'));
export const getEffects = cache(() => readJson<EffectRow>('effect_table'));
export const getAllocation = cache(() => readJson<AllocationRow>('allocation_sweep'));
export const getAllocationSummary = cache(() => readJson<AllocationSummary>('allocation_summary'));
export const getScores = cache(() => readJson<ScoreRow>('scores'));
export const getScenarios = cache(() => readJson<ScenarioRow>('scenarios'));
export const getBudgetSweep = cache(() => readJson<BudgetRow>('budget_sweep'));
export const getFacilities = cache(() => readJson<HealthFacility>('health_facilities'));
export const getPredictionHistory = cache(() => readJson<PredictionHistory>('predictions_history'));
export const getSeiSirParams = cache(() => readJson<SeiSirParams>('sei_sir_params'));
export const getAssessments = cache(() => readJson<Assessment>('assessments'));

/** One district's assessment for an audience at a horizon, or null. */
export async function getAssessment(
  districtId: string,
  horizon: number,
  audience: Assessment['audience'],
): Promise<Assessment | null> {
  const rows = await getAssessments();
  return (
    rows.find(
      (row) =>
        row.district_id === districtId && row.horizon === horizon && row.audience === audience,
    ) ?? null
  );
}

export const getGeometry = cache(async (): Promise<DistrictGeometry | null> => {
  try {
    const raw = await fs.readFile(path.join(DATA_DIR, 'districts.geojson'), 'utf-8');
    return JSON.parse(raw) as DistrictGeometry;
  } catch {
    return null;
  }
});

/** Whether the export has ever been run. Distinguishes "no data yet" from "no rows". */
export const hasData = cache(async (): Promise<boolean> => {
  try {
    await fs.access(path.join(DATA_DIR, 'district_risk.json'));
    return true;
  } catch {
    return false;
  }
});

/** Every forecast horizon present in the export, ascending. */
export const getHorizons = cache(async (): Promise<number[]> => {
  const risk = await getDistrictRisk();
  return Array.from(new Set(risk.map((r) => r.horizon))).sort((a, b) => a - b);
});

export const getDistrictMap = cache(async (): Promise<Map<string, District>> => {
  const districts = await getDistricts();
  return new Map(districts.map((d) => [d.district_id, d]));
});

/** One district's registry entry, or null if the id is not one of the 25. */
export async function getDistrict(districtId: string): Promise<District | null> {
  return (await getDistrictMap()).get(districtId) ?? null;
}
