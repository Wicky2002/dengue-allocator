/**
 * Row shapes of the exported artifacts.
 *
 * These mirror the Parquet schemas written by `make pipeline` and serialised by
 * `dengue.export_web`. Numeric fields are `number | null`: the exporter turns
 * NaN into null rather than emitting invalid JSON, so every consumer has to
 * handle a missing value explicitly instead of rendering "NaN" to a user.
 */

export interface PipelineMeta {
  generated_at: string;
  panel_source: string;
  is_synthetic: boolean;
  panel_rows: number;
  n_districts: number;
  panel_start: string;
  panel_end: string;
  forecast_origin: string;
  forecast_model: string;
  max_team_weeks: number;
  effect_horizon_weeks: number;
  runtime_seconds: number;
}

export interface District {
  district_id: string;
  name: string;
  province: string;
  lat: number;
  lon: number;
  population: number;
  area_km2: number;
  density_per_km2: number;
  /** Qualifies for Stage 3's allocation floor -- least facility coverage per head. */
  facility_poor: boolean;
}

export interface DistrictRisk {
  district_id: string;
  iso_week: string | null;
  target_week: string | null;
  horizon: number;
  'q0.1': number | null;
  'q0.5': number | null;
  'q0.9': number | null;
  model: string;
  population: number | null;
  incidence_per_100k: number | null;
  interval_width: number | null;
  risk_rank: number | null;
}

export interface PanelRow {
  district_id: string;
  iso_week: string | null;
  cases: number | null;
  population: number | null;
  rain_mm: number | null;
  tmax: number | null;
  tmin: number | null;
  rh: number | null;
  high_risk_flag: number | null;
}

export interface HospitalReadiness {
  district_id: string;
  district: string;
  forecast_cases: number | null;
  admissions: number | null;
  admissions_upper: number | null;
  severe_cases: number | null;
  icu_patients: number | null;
  paediatric_admissions: number | null;
  peak_occupied_beds: number | null;
  dengue_bed_capacity: number | null;
  occupancy_pct: number | null;
  capacity_status: string | null;
  horizon?: number;
  [key: string]: unknown;
}

export interface DistrictCapacity {
  district_id: string;
  population: number;
  n_facilities: number;
  n_hospitals: number;
  estimated_beds: number | null;
  beds_per_1000: number | null;
  capacity_is_estimated: boolean;
  beds_reference_year: number | null;
}

export interface EffectRow {
  district_id: string;
  team_weeks: number;
  cases_averted_mean: number | null;
  cases_averted_lower: number | null;
  cases_averted_upper: number | null;
  marginal_cases_averted_per_team_week: number | null;
  coverage: number | null;
  baseline_cases: number | null;
}

export interface AllocationRow {
  budget: number;
  risk_quantile: number;
  strategy: string;
  district_id: string;
  team_weeks: number;
  expected_cases_averted: number | null;
  shadow_price_budget: number | null;
  solver_status: string;
}

export interface AllocationSummary {
  budget: number;
  risk_quantile: number;
  strategy: string;
  expected_cases_averted: number | null;
  shadow_price_budget: number | null;
  budget_used: number | null;
  districts_served: number | null;
  uplift_pct: number | null;
}

export interface ScoreRow {
  model: string;
  fold: number;
  horizon: number;
  metric: string;
  value: number | null;
}

export interface ScenarioRow {
  district_id: string;
  district: string;
  scenario_key: string;
  scenario: string;
  description: string;
  total_cases: number | null;
  baseline_total: number | null;
  change_pct: number | null;
  horizon_weeks: number;
  weekly_cases: unknown;
}

export interface BudgetRow {
  budget_lkr: number;
  category_key: string;
  category: string;
  description: string;
  amount_lkr: number | null;
  share_pct: number | null;
  category_effect: number | null;
  total_effect: number | null;
  evidence: string;
}

export interface HealthFacility {
  osm_id: number | string;
  name: string | null;
  facility_type: string | null;
  lat: number | null;
  lon: number | null;
  beds_tagged: number | null;
  operator: string | null;
  district_id: string | null;
}

export interface PredictionHistory {
  district_id: string;
  iso_week: string | null;
  target_week: string | null;
  horizon: number;
  'q0.1': number | null;
  'q0.5': number | null;
  'q0.9': number | null;
  model: string;
  fold: number;
  actual_cases: number | null;
  population: number | null;
  predicted_incidence_per_100k: number | null;
}

export interface SeiSirParams {
  district_id: string;
  r0_base: number | null;
  rain_elasticity: number | null;
  init_susceptible: number | null;
  reporting_fraction: number | null;
  r0_mean: number | null;
  log_likelihood: number | null;
  n_observations: number | null;
  converged: boolean;
}

/** GeoJSON, narrowed to what the choropleth actually uses. */
export interface DistrictFeature {
  type: 'Feature';
  properties: Record<string, unknown>;
  geometry: { type: string; coordinates: unknown };
}

export interface DistrictGeometry {
  type: 'FeatureCollection';
  features: DistrictFeature[];
}

export interface Recommendation {
  action: string;
  rationale: string;
  urgency: 'routine' | 'elevated' | 'urgent';
}

export interface Assessment {
  district_id: string;
  district: string;
  horizon: number;
  audience: 'public' | 'hospital' | 'moh';
  risk_level: 'low' | 'moderate' | 'high' | 'severe';
  risk_label: string;
  incidence_per_100k: number | null;
  forecast_median: number | null;
  forecast_lower: number | null;
  forecast_upper: number | null;
  change_pct: number | null;
  is_rising_fast: boolean;
  recommendations: Recommendation[];
}
