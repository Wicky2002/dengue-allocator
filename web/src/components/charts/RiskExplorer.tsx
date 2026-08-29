'use client';

import React from 'react';
import Link from 'next/link';
import { ArrowTopRightOnSquareIcon } from '@heroicons/react/24/outline';

import { Choropleth } from './Choropleth';
import { RiskPill } from '@/components/ui/RiskPill';
import { num } from '@/lib/format';
import type { RankedDistrict } from '@/lib/selectors';
import type { DistrictGeometry } from '@/lib/types';
import { useT } from '@/components/i18n/LocaleProvider';

/**
 * Map and ranked list, sharing one selection.
 *
 * The list is not a fallback for a failed map -- it renders alongside it
 * always, so "every district, always visible" holds even if the geometry is
 * missing, and so a reader who prefers a list to a map is never stuck with the
 * map alone.
 */
export function RiskExplorer({
  geometry,
  ranked,
  horizon,
  linkToDistrict = true,
}: {
  geometry: DistrictGeometry | null;
  ranked: RankedDistrict[];
  horizon: number;
  linkToDistrict?: boolean;
}) {
  const t = useT();
  const [selected, setSelected] = React.useState<string | null>(null);
  const rowRefs = React.useRef<Record<string, HTMLLIElement | null>>({});

  const select = (districtId: string) => {
    setSelected((current) => (current === districtId ? null : districtId));
    rowRefs.current[districtId]?.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
  };

  const maxIncidence = Math.max(...ranked.map((row) => row.incidence ?? 0), 1);

  return (
    <div className="grid gap-6 lg:grid-cols-5">
      <div className="rounded-sm border border-border bg-white p-4 shadow-card lg:col-span-3">
        <div className="mb-3 flex items-baseline justify-between gap-3">
          <h3 className="text-h3">{t('nat.riskMap')}</h3>
          <p className="text-xs text-text-500">
            {horizon} {t('nat.weeksAheadClick')}
          </p>
        </div>
        <Choropleth
          geometry={geometry}
          data={ranked.map((row) => ({
            district_id: row.district_id,
            name: row.name,
            incidence: row.incidence,
            median: row.median,
          }))}
          selected={selected}
          onSelect={select}
        />
      </div>

      <div className="rounded-sm border border-border bg-white p-4 shadow-card lg:col-span-2">
        <div className="mb-3 flex items-baseline justify-between gap-3">
          <h3 className="text-h3">{t('nat.everyDistrictRanked')}</h3>
          <p className="text-xs text-text-500">{t('nat.per100kWeekUnit')}</p>
        </div>
        <ol className="max-h-[560px] space-y-0.5 overflow-y-auto pr-1">
          {ranked.map((row) => {
            const isSelected = selected === row.district_id;
            return (
              <li
                key={row.district_id}
                ref={(element) => {
                  rowRefs.current[row.district_id] = element;
                }}
              >
                <button
                  type="button"
                  onClick={() => select(row.district_id)}
                  aria-pressed={isSelected}
                  className={`w-full rounded-sm px-2.5 py-2 text-left transition-colors ${
                    isSelected ? 'bg-primary-50 ring-1 ring-primary-200' : 'hover:bg-bg-100'
                  }`}
                >
                  <div className="flex items-baseline justify-between gap-3">
                    <span className="flex min-w-0 items-baseline gap-2">
                      <span className="num w-5 shrink-0 text-xs text-text-400">{row.rank}</span>
                      <span className="truncate text-sm font-medium text-text-900">{row.name}</span>
                    </span>
                    <span className="num shrink-0 text-sm font-semibold text-text-900">
                      {row.incidence != null ? row.incidence.toFixed(1) : '—'}
                    </span>
                  </div>
                  <div className="mt-1.5 flex items-center gap-2">
                    <span className="h-1.5 flex-1 overflow-hidden rounded-full bg-bg-200">
                      <span
                        className="block h-full rounded-full"
                        style={{
                          width: `${((row.incidence ?? 0) / maxIncidence) * 100}%`,
                          background: row.band.colour,
                        }}
                      />
                    </span>
                    <span className="num shrink-0 text-[11px] text-text-500">
                      {num(row.median)} {t('public.cases')}
                    </span>
                  </div>
                  {isSelected ? (
                    <div className="mt-2 flex flex-wrap items-center gap-2 border-t border-border pt-2">
                      <RiskPill incidence={row.incidence} />
                      <span className="num text-xs text-text-600">
                        {t('nat.col.interval80')} {num(row.lower)}–{num(row.upper)} {t('public.cases')}
                      </span>
                      {linkToDistrict ? (
                        <Link
                          href={`/public?district=${row.district_id}`}
                          className="ml-auto inline-flex items-center gap-1 text-xs font-medium text-primary-700 hover:underline"
                        >
                          {t('nat.openDistrict')}
                          <ArrowTopRightOnSquareIcon className="h-3.5 w-3.5" aria-hidden />
                        </Link>
                      ) : null}
                    </div>
                  ) : null}
                </button>
              </li>
            );
          })}
        </ol>
      </div>
    </div>
  );
}

export default RiskExplorer;
