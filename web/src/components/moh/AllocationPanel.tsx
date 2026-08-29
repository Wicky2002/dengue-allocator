'use client';

import React from 'react';
import { Bar, BarChart, CartesianGrid, Cell, LabelList, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

import { Callout } from '@/components/ui/Callout';
import { StatTile } from '@/components/ui/StatTile';
import { num, pct } from '@/lib/format';
import { isInScope } from '@/lib/rbac';
import type { AllocationRow, AllocationSummary } from '@/lib/types';

/**
 * Stage 3: where the teams go.
 *
 * The budget slider and posture switch **index a precomputed sweep** — they do
 * not re-solve the integer programme. Every combination on offer was solved by
 * `make pipeline` and written to `allocation_sweep.parquet`; a dashboard that
 * re-solved an ILP on slider drag would be unusable in the week it matters.
 */
export function AllocationPanel({
  sweep,
  summary,
  districtNames,
  inScope,
}: {
  sweep: AllocationRow[];
  summary: AllocationSummary[];
  districtNames: Record<string, string>;
  inScope: string[] | null;
}) {
  const budgets = React.useMemo(
    () => Array.from(new Set(sweep.map((row) => row.budget))).sort((a, b) => a - b),
    [sweep],
  );
  const [budgetIndex, setBudgetIndex] = React.useState(Math.floor(budgets.length / 2));
  const [posture, setPosture] = React.useState<0.5 | 0.9>(0.5);

  const budget = budgets[budgetIndex] ?? budgets[0];

  const plan = React.useMemo(
    () =>
      sweep
        .filter(
          (row) =>
            row.budget === budget &&
            row.risk_quantile === posture &&
            row.strategy === 'ilp' &&
            row.team_weeks > 0 &&
            isInScope(row.district_id, inScope),
        )
        .map((row) => ({
          ...row,
          district: districtNames[row.district_id] ?? row.district_id,
        }))
        .sort((a, b) => b.team_weeks - a.team_weeks),
    [sweep, budget, posture, inScope, districtNames],
  );

  const totals = summary.find(
    (row) => row.budget === budget && row.risk_quantile === posture && row.strategy === 'ilp',
  );
  const greedy = summary.find(
    (row) => row.budget === budget && row.risk_quantile === posture && row.strategy === 'greedy',
  );

  return (
    <div>
      <div className="mb-6 grid gap-6 lg:grid-cols-3">
        <div className="rounded-sm border border-border bg-white p-5 shadow-card lg:col-span-2">
          <label className="block">
            <span className="flex items-baseline justify-between gap-2">
              <span className="text-sm font-medium text-text-700">Weekly team-week budget</span>
              <span className="num text-lg font-bold text-primary-700">{budget}</span>
            </span>
            <input
              type="range"
              min={0}
              max={Math.max(budgets.length - 1, 0)}
              step={1}
              value={budgetIndex}
              onChange={(event) => setBudgetIndex(Number(event.target.value))}
              className="mt-3 w-full accent-primary-700"
            />
            <span className="num mt-1 flex justify-between text-[11px] text-text-400">
              <span>{budgets[0]}</span>
              <span>{budgets.at(-1)}</span>
            </span>
          </label>
          <p className="mt-3 text-xs text-text-500">
            Precomputed by <code className="font-mono">make pipeline</code> — this slider indexes
            cached solutions rather than re-solving the programme.
          </p>
        </div>

        <div className="rounded-sm border border-border bg-white p-5 shadow-card">
          <p className="text-sm font-medium text-text-700">Posture</p>
          <div className="mt-3 flex flex-col gap-2">
            {(
              [
                [0.5, 'Median', 'Plan against the central forecast.'],
                [0.9, 'Risk-averse', 'Plan against the 90th percentile — more teams to districts with wide intervals.'],
              ] as [0.5 | 0.9, string, string][]
            ).map(([value, label, hint]) => (
              <button
                key={value}
                type="button"
                onClick={() => setPosture(value)}
                aria-pressed={posture === value}
                className={`rounded-sm border p-3 text-left transition-colors ${
                  posture === value
                    ? 'border-primary-700 bg-primary-50'
                    : 'border-border hover:bg-bg-100'
                }`}
              >
                <span className="block text-sm font-semibold text-text-900">{label}</span>
                <span className="block text-xs text-text-600">{hint}</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="mb-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatTile
          label="Expected cases averted"
          value={num(totals?.expected_cases_averted ?? null)}
          tier="modelled"
          hint="Nationwide, this budget"
        />
        <StatTile
          label="Districts served"
          value={num(totals?.districts_served ?? null)}
          tier="modelled"
        />
        <StatTile
          label="Uplift vs greedy"
          value={pct(totals?.uplift_pct ?? null, 1)}
          tier="modelled"
          hint={greedy ? `Greedy averts ${num(greedy.expected_cases_averted)}` : undefined}
        />
        <StatTile
          label="Shadow price"
          value={num(totals?.shadow_price_budget ?? null, 2)}
          unit="cases / team-week"
          tier="modelled"
          hint="Value of one more team-week"
        />
      </div>

      {plan.length === 0 ? (
        <Callout tone="info">
          No teams are allocated to your districts at this budget. At a tighter envelope the
          programme concentrates teams where the marginal return is highest — which can mean
          nothing here at all.
        </Callout>
      ) : (
        <div className="rounded-sm border border-border bg-white p-5 shadow-card">
          <h3 className="text-h3 mb-4">Team-weeks by district</h3>
          <ResponsiveContainer width="100%" height={Math.max(220, 34 * plan.length)}>
            <BarChart data={plan} layout="vertical" margin={{ top: 4, right: 40, bottom: 0, left: 8 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" horizontal={false} />
              <XAxis type="number" tick={{ fontSize: 11, fill: '#6B7280' }} axisLine={false} tickLine={false} />
              <YAxis
                type="category"
                dataKey="district"
                width={132}
                tick={{ fontSize: 12, fill: '#374151' }}
                axisLine={false}
                tickLine={false}
              />
              <Tooltip
                cursor={{ fill: '#F3F4F6' }}
                contentStyle={{ borderRadius: 10, border: '1px solid #E5E7EB', fontSize: 12 }}
                formatter={(value, _name, entry) => [
                  `${value} team-weeks · ${num((entry?.payload as { expected_cases_averted: number })?.expected_cases_averted)} cases averted`,
                  'Allocation',
                ]}
              />
              <Bar dataKey="team_weeks" radius={[0, 4, 4, 0]} isAnimationActive={false}>
                {plan.map((row) => (
                  <Cell key={row.district_id} fill="#1D4ED8" />
                ))}
                <LabelList dataKey="team_weeks" position="right" className="num" fontSize={11} fill="#374151" />
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}

export default AllocationPanel;
