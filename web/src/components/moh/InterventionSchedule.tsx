'use client';

import React from 'react';

import { Callout } from '@/components/ui/Callout';
import { isInScope } from '@/lib/rbac';
import type { AllocationRow } from '@/lib/types';

const ACTIVITIES = [
  'Source reduction',
  'House inspection',
  'School inspection',
  'Community clean-up',
  'Space spraying',
];
const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'];

/**
 * A weekly schedule derived from the Stage 3 allocation.
 *
 * Districts with more team-weeks get more activity days. Activity types are
 * ordered by how far ahead of the peak they act — source reduction first,
 * because it removes breeding sites weeks before adults emerge; space spraying
 * last, because it only kills adults already flying.
 */
export function InterventionSchedule({
  sweep,
  districtNames,
  inScope,
}: {
  sweep: AllocationRow[];
  districtNames: Record<string, string>;
  inScope: string[] | null;
}) {
  const budgets = React.useMemo(
    () => Array.from(new Set(sweep.map((row) => row.budget))).sort((a, b) => a - b),
    [sweep],
  );
  const budget = budgets[Math.floor(budgets.length / 2)];

  const plan = sweep
    .filter(
      (row) =>
        row.budget === budget &&
        row.risk_quantile === 0.5 &&
        row.strategy === 'ilp' &&
        row.team_weeks > 0 &&
        isInScope(row.district_id, inScope),
    )
    .sort((a, b) => b.team_weeks - a.team_weeks);

  const rows = plan.flatMap((row, districtIndex) =>
    DAYS.slice(0, Math.min(Math.floor(row.team_weeks), 5)).map((day, dayIndex) => ({
      key: `${row.district_id}-${day}`,
      day,
      district: districtNames[row.district_id] ?? row.district_id,
      activity: ACTIVITIES[(districtIndex + dayIndex) % ACTIVITIES.length],
      teams: Math.max(1, Math.floor(row.team_weeks / 5)),
    })),
  );

  if (rows.length === 0) {
    return <Callout tone="info">No activity is scheduled for your districts at this budget.</Callout>;
  }

  return (
    <div>
      <p className="mb-4 max-w-3xl text-sm leading-relaxed text-text-600">
        Derived from the Stage 3 allocation at a {budget} team-week budget: districts with more
        team-weeks get more activity days. Activity types are ordered by how far ahead of the
        peak they act — source reduction first, spraying last.
      </p>
      <div className="overflow-x-auto rounded-sm border border-border bg-white shadow-card">
        <table className="w-full min-w-[560px] border-collapse text-sm">
          <thead className="border-b border-border bg-bg-100 text-xs uppercase tracking-wide text-text-500">
            <tr>
              <th scope="col" className="px-3 py-3 text-left">Day</th>
              <th scope="col" className="px-3 py-3 text-left">District</th>
              <th scope="col" className="px-3 py-3 text-left">Activity</th>
              <th scope="col" className="px-3 py-3 text-right">Teams</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.key} className="border-b border-border last:border-0 hover:bg-bg-100">
                <td className="px-3 py-2.5 font-medium text-text-900">{row.day}</td>
                <td className="px-3 py-2.5">{row.district}</td>
                <td className="px-3 py-2.5 text-text-600">{row.activity}</td>
                <td className="num px-3 py-2.5 text-right">{row.teams}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default InterventionSchedule;
