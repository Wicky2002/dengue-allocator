import React from 'react';
import { ProvenanceChip } from './ProvenanceChip';
import type { TierKey } from '@/lib/provenance';

/**
 * One headline figure, set as a table entry rather than a dashboard card.
 *
 * Every tile carries a provenance chip, with no way to render one without it —
 * that is the point of taking `tier` as a required prop rather than an option.
 */
export function StatTile({
  label,
  value,
  unit,
  tier,
  basis,
  hint,
  trend,
  className = '',
}: {
  label: string;
  value: string;
  unit?: string;
  tier: TierKey;
  basis?: string;
  hint?: string;
  trend?: { value: string; direction: 'up' | 'down' | 'flat' };
  className?: string;
}) {
  const trendClass =
    trend?.direction === 'up'
      ? 'text-red-800 bg-red-50 ring-red-200'
      : trend?.direction === 'down'
        ? 'text-teal-800 bg-teal-50 ring-teal-200'
        : 'text-text-600 bg-bg-200 ring-border';

  return (
    <div
      className={`flex flex-col rounded-sm border border-border border-t-[3px] border-t-primary-700 bg-white p-5 shadow-card ${className}`.trim()}
    >
      <div className="flex items-start justify-between gap-2">
        <p className="text-[12px] font-semibold uppercase tracking-[0.08em] text-text-500">
          {label}
        </p>
        <ProvenanceChip tier={tier} basis={basis} />
      </div>
      <p className="num mt-3 flex items-baseline gap-1.5">
        <span className="text-[2rem] font-bold leading-none tracking-tight text-primary-900">
          {value}
        </span>
        {unit ? <span className="text-[13px] font-medium text-text-500">{unit}</span> : null}
      </p>
      <div className="mt-auto flex flex-wrap items-center gap-2 pt-3">
        {trend ? (
          <span className={`num rounded-sm px-1.5 py-0.5 text-[12px] font-bold ring-1 ${trendClass}`}>
            {trend.direction === 'up' ? '▲' : trend.direction === 'down' ? '▼' : '■'} {trend.value}
          </span>
        ) : null}
        {hint ? <span className="text-[12px] leading-snug text-text-500">{hint}</span> : null}
      </div>
    </div>
  );
}

export default StatTile;
