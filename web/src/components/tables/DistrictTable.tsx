'use client';

import React from 'react';
import Link from 'next/link';
import { ChevronUpDownIcon } from '@heroicons/react/24/outline';

import { RiskPill } from '@/components/ui/RiskPill';
import { num } from '@/lib/format';
import type { RankedDistrict } from '@/lib/selectors';
import type { DistrictCapacity } from '@/lib/types';
import { useT } from '@/components/i18n/LocaleProvider';

type SortKey = 'rank' | 'name' | 'median' | 'incidence' | 'population' | 'facilities';

/**
 * The full district table.
 *
 * Sorting is client-side over 25 rows already in the payload -- no request, no
 * recomputation. Case counts and incidence are shown side by side on purpose:
 * the ranking is on incidence, and a reader who only sees counts will disagree
 * with the ordering without being told why.
 */
export function DistrictTable({
  ranked,
  capacity,
}: {
  ranked: RankedDistrict[];
  capacity: Map<string, DistrictCapacity>;
}) {
  const t = useT();
  const [sort, setSort] = React.useState<{ key: SortKey; desc: boolean }>({
    key: 'rank',
    desc: false,
  });

  const rows = React.useMemo(() => {
    const value = (row: RankedDistrict, key: SortKey): number | string => {
      switch (key) {
        case 'name':
          return row.name;
        case 'median':
          return row.median ?? -1;
        case 'incidence':
          return row.incidence ?? -1;
        case 'population':
          return row.population;
        case 'facilities':
          return capacity.get(row.district_id)?.n_facilities ?? -1;
        default:
          return row.rank;
      }
    };
    return [...ranked].sort((a, b) => {
      const left = value(a, sort.key);
      const right = value(b, sort.key);
      const comparison =
        typeof left === 'string' && typeof right === 'string'
          ? left.localeCompare(right)
          : (left as number) - (right as number);
      return sort.desc ? -comparison : comparison;
    });
  }, [ranked, capacity, sort]);

  const header = (key: SortKey, label: string, alignRight = false) => (
    <th scope="col" className={`px-3 py-3 ${alignRight ? 'text-right' : 'text-left'}`}>
      <button
        type="button"
        onClick={() => setSort((s) => ({ key, desc: s.key === key ? !s.desc : true }))}
        className={`inline-flex items-center gap-1 text-xs font-semibold uppercase tracking-wide transition-colors ${
          sort.key === key ? 'text-primary-700' : 'text-text-500 hover:text-text-900'
        }`}
      >
        {label}
        <ChevronUpDownIcon className="h-3.5 w-3.5" aria-hidden />
      </button>
    </th>
  );

  return (
    <div className="overflow-x-auto rounded-sm border border-border bg-white shadow-card">
      <table className="w-full min-w-[760px] border-collapse text-sm">
        <caption className="sr-only">
          Forecast dengue risk by district, sortable
        </caption>
        <thead className="border-b border-border bg-bg-100">
          <tr>
            {header('rank', '#')}
            {header('name', t('nat.col.district'))}
            <th scope="col" className="px-3 py-3 text-left text-xs font-semibold uppercase tracking-wide text-text-500">
              {t('nat.col.risk')}
            </th>
            {header('median', t('nat.col.forecastCases'), true)}
            <th scope="col" className="px-3 py-3 text-right text-xs font-semibold uppercase tracking-wide text-text-500">
              {t('nat.col.interval80')}
            </th>
            {header('incidence', t('nat.col.per100k'), true)}
            {header('population', t('nat.col.population'), true)}
            {header('facilities', t('nat.col.facilities'), true)}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => {
            const cap = capacity.get(row.district_id);
            return (
              <tr key={row.district_id} className="border-b border-border last:border-0 hover:bg-bg-100">
                <td className="num px-3 py-2.5 text-text-400">{row.rank}</td>
                <td className="px-3 py-2.5">
                  <Link
                    href={`/public?district=${row.district_id}`}
                    className="font-medium text-primary-700 hover:underline"
                  >
                    {row.name}
                  </Link>
                  <span className="block text-xs text-text-500">{row.province}</span>
                </td>
                <td className="px-3 py-2.5">
                  <RiskPill incidence={row.incidence} />
                </td>
                <td className="num px-3 py-2.5 text-right font-semibold text-text-900">
                  {num(row.median)}
                </td>
                <td className="num px-3 py-2.5 text-right text-text-500">
                  {num(row.lower)}–{num(row.upper)}
                </td>
                <td className="num px-3 py-2.5 text-right text-text-700">
                  {row.incidence != null ? row.incidence.toFixed(1) : '—'}
                </td>
                <td className="num px-3 py-2.5 text-right text-text-600">{num(row.population)}</td>
                <td className="num px-3 py-2.5 text-right text-text-600">
                  {num(cap?.n_facilities ?? null)}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

export default DistrictTable;
