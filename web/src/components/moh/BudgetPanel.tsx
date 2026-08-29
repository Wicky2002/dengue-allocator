'use client';

import React from 'react';
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts';

import { Callout } from '@/components/ui/Callout';
import { lkr, pct } from '@/lib/format';
import type { BudgetRow } from '@/lib/types';

const SLICE_COLOURS = ['#1D4ED8', '#0F766E', '#CA8A04', '#7C3AED', '#DB2777', '#0891B2'];

/** How an annual envelope splits across intervention categories. */
export function BudgetPanel({ rows }: { rows: BudgetRow[] }) {
  const envelopes = React.useMemo(
    () => Array.from(new Set(rows.map((row) => row.budget_lkr))).sort((a, b) => a - b),
    [rows],
  );
  const [index, setIndex] = React.useState(Math.min(3, envelopes.length - 1));
  const envelope = envelopes[index] ?? envelopes[0];
  const split = rows.filter((row) => row.budget_lkr === envelope);

  if (envelopes.length === 0) {
    return (
      <p className="text-sm text-text-600">
        No budget sweep is cached for this deployment. It is precomputed by `make pipeline`
        alongside the allocation sweep — run it, then `make export-web`.
      </p>
    );
  }

  return (
    <div>
      <label className="mb-6 block max-w-xl">
        <span className="flex items-baseline justify-between gap-2">
          <span className="text-sm font-medium text-text-700">Annual envelope</span>
          <span className="num text-lg font-bold text-primary-700">{lkr(envelope)}</span>
        </span>
        <input
          type="range"
          min={0}
          max={Math.max(envelopes.length - 1, 0)}
          step={1}
          value={index}
          onChange={(event) => setIndex(Number(event.target.value))}
          className="mt-3 w-full accent-primary-700"
        />
      </label>

      <div className="grid gap-6 lg:grid-cols-5">
        <div className="rounded-sm border border-border bg-white p-5 shadow-card lg:col-span-2">
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={split}
                dataKey="amount_lkr"
                nameKey="category"
                innerRadius={62}
                outerRadius={104}
                paddingAngle={2}
                isAnimationActive={false}
              >
                {split.map((row, i) => (
                  <Cell key={row.category_key} fill={SLICE_COLOURS[i % SLICE_COLOURS.length]} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{ borderRadius: 10, border: '1px solid #E5E7EB', fontSize: 12 }}
                formatter={(value, name) => [lkr(value as number), String(name)]}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="overflow-x-auto rounded-sm border border-border bg-white shadow-card lg:col-span-3">
          <table className="w-full min-w-[520px] border-collapse text-sm">
            <thead className="border-b border-border bg-bg-100 text-xs uppercase tracking-wide text-text-500">
              <tr>
                <th scope="col" className="px-3 py-3 text-left">Category</th>
                <th scope="col" className="px-3 py-3 text-right">Share</th>
                <th scope="col" className="px-3 py-3 text-right">Amount</th>
                <th scope="col" className="px-3 py-3 text-left">Evidence</th>
              </tr>
            </thead>
            <tbody>
              {split.map((row, i) => (
                <tr key={row.category_key} className="border-b border-border last:border-0">
                  <td className="px-3 py-2.5">
                    <span className="flex items-center gap-2 font-medium text-text-900">
                      <span
                        aria-hidden
                        className="h-2.5 w-2.5 rounded-sm"
                        style={{ background: SLICE_COLOURS[i % SLICE_COLOURS.length] }}
                      />
                      {row.category}
                    </span>
                    <span className="mt-0.5 block text-xs text-text-500">{row.description}</span>
                  </td>
                  <td className="num px-3 py-2.5 text-right font-semibold">{pct(row.share_pct, 1)}</td>
                  <td className="num px-3 py-2.5 text-right">{lkr(row.amount_lkr)}</td>
                  <td className="px-3 py-2.5 text-xs text-text-600">{row.evidence}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <Callout tone="warning" title="Only the vector-control curve is anchored to a model" className="mt-6">
        The other categories use assumed cost-effectiveness elasticities, not measured Sri
        Lankan data. Read this as a structured argument about trade-offs, not as an
        evidence-based funding instruction.
      </Callout>
    </div>
  );
}

export default BudgetPanel;
