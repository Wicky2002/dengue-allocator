'use client';

import React from 'react';
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

import { num, signedPct } from '@/lib/format';
import type { ScenarioRow } from '@/lib/types';

/**
 * Stage 2 counterfactuals.
 *
 * Each scenario is a **re-integration of the fitted SEI-SIR model** with a
 * perturbed input, precomputed by `make pipeline` — not a lookup table and not
 * arithmetic on the forecast. That is why heavy rain plus a heatwave is worse
 * than the sum of the two on its own: more mosquitoes and a shorter incubation
 * period multiply rather than add.
 */
export function ScenarioPanel({ scenarios }: { scenarios: ScenarioRow[] }) {
  const districts = React.useMemo(
    () => Array.from(new Set(scenarios.map((row) => row.district))).sort(),
    [scenarios],
  );
  const [district, setDistrict] = React.useState(districts[0] ?? '');

  const rows = scenarios
    .filter((row) => row.district === district && row.scenario_key !== 'baseline')
    .sort((a, b) => (b.change_pct ?? 0) - (a.change_pct ?? 0));

  const baseline = scenarios.find(
    (row) => row.district === district && row.scenario_key === 'baseline',
  );

  if (districts.length === 0) {
    return (
      <p className="text-sm text-text-600">
        No scenarios are cached for your districts. They are precomputed when Stage 2 runs —
        they are ODE integrations, so they are never run at request time.
      </p>
    );
  }

  return (
    <div>
      <label className="mb-6 flex flex-wrap items-center gap-3">
        <span className="text-sm font-medium text-text-700">District</span>
        <select
          value={district}
          onChange={(event) => setDistrict(event.target.value)}
          className="rounded-sm border border-border bg-white px-3 py-2 text-sm font-medium shadow-card"
        >
          {districts.map((name) => (
            <option key={name} value={name}>
              {name}
            </option>
          ))}
        </select>
        {baseline ? (
          <span className="num text-sm text-text-500">
            Baseline: {num(baseline.total_cases)} cases over {baseline.horizon_weeks} weeks
          </span>
        ) : null}
      </label>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-sm border border-border bg-white p-5 shadow-card">
          <ResponsiveContainer width="100%" height={Math.max(240, 44 * rows.length)}>
            <BarChart data={rows} layout="vertical" margin={{ top: 4, right: 24, bottom: 0, left: 8 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" horizontal={false} />
              <XAxis
                type="number"
                tick={{ fontSize: 11, fill: '#6B7280' }}
                axisLine={false}
                tickLine={false}
                tickFormatter={(value) => `${value > 0 ? '+' : ''}${value}%`}
              />
              <YAxis
                type="category"
                dataKey="scenario"
                width={168}
                tick={{ fontSize: 12, fill: '#374151' }}
                axisLine={false}
                tickLine={false}
              />
              <Tooltip
                cursor={{ fill: '#F3F4F6' }}
                contentStyle={{ borderRadius: 10, border: '1px solid #E5E7EB', fontSize: 12 }}
                formatter={(value, _name, entry) => [
                  `${signedPct(value as number, 1)} · ${num((entry?.payload as ScenarioRow)?.total_cases)} cases`,
                  'Change vs baseline',
                ]}
              />
              <Bar dataKey="change_pct" radius={[0, 4, 4, 0]} isAnimationActive={false}>
                {rows.map((row) => (
                  <Cell
                    key={row.scenario_key}
                    fill={(row.change_pct ?? 0) > 0 ? '#B91C1C' : '#0F766E'}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        <dl className="space-y-3">
          {rows.map((row) => (
            <div key={row.scenario_key} className="rounded-sm border border-border bg-white p-4 shadow-card">
              <dt className="flex items-baseline justify-between gap-3">
                <span className="font-semibold text-text-900">{row.scenario}</span>
                <span
                  className={`num text-sm font-bold ${
                    (row.change_pct ?? 0) > 0 ? 'text-red-700' : 'text-teal-700'
                  }`}
                >
                  {signedPct(row.change_pct, 0)}
                </span>
              </dt>
              <dd className="mt-1 text-sm leading-relaxed text-text-600">{row.description}</dd>
            </div>
          ))}
        </dl>
      </div>
    </div>
  );
}

export default ScenarioPanel;
