'use client';

import React from 'react';
import { BuildingOffice2Icon } from '@heroicons/react/24/outline';

import { Card } from '@/components/ui/Card';
import { Callout } from '@/components/ui/Callout';
import { RiskPill } from '@/components/ui/RiskPill';
import { RecommendationList } from '@/components/ui/RecommendationList';
import { num, signedPct } from '@/lib/format';
import type { Assessment } from '@/lib/types';

export interface HotspotDistrict {
  district_id: string;
  name: string;
  facilities: number | null;
  facilityPoor: boolean;
}

/**
 * Hotspot cards, with a chooser for which districts appear.
 *
 * Which districts get a card is a **viewing convenience, not a scope change**.
 * Team deployment, the intervention plan and the budget below all run against
 * the account's real districts, so what an officer can act on is unaffected by
 * what they choose to look at here. Districts outside their own scope are
 * marked as such, so the distinction stays visible rather than implied.
 */
export function HotspotPanel({
  assessments,
  districts,
  ownDistricts,
}: {
  assessments: Assessment[];
  districts: HotspotDistrict[];
  /** The account's real scope. Empty means nationwide. */
  ownDistricts: string[];
}) {
  const nationwide = ownDistricts.length === 0;
  const [selected, setSelected] = React.useState<string[]>(
    nationwide ? districts.slice(0, 6).map((d) => d.district_id) : ownDistricts,
  );

  const byId = React.useMemo(
    () => new Map(districts.map((d) => [d.district_id, d])),
    [districts],
  );
  const own = React.useMemo(() => new Set(ownDistricts), [ownDistricts]);

  const shown = assessments
    .filter((item) => selected.includes(item.district_id))
    .sort((a, b) => (b.incidence_per_100k ?? -1) - (a.incidence_per_100k ?? -1));

  const toggle = (districtId: string) =>
    setSelected((current) =>
      current.includes(districtId)
        ? current.filter((value) => value !== districtId)
        : [...current, districtId],
    );

  return (
    <div>
      <fieldset className="mb-6 rounded-sm border border-border bg-white p-4 shadow-card">
        <legend className="px-1 text-[13px] font-semibold text-text-700">Districts shown</legend>
        <div className="mt-1 flex flex-wrap gap-1.5">
          {districts.map((district) => {
            const active = selected.includes(district.district_id);
            const isOwn = nationwide || own.has(district.district_id);
            return (
              <button
                key={district.district_id}
                type="button"
                onClick={() => toggle(district.district_id)}
                aria-pressed={active}
                className={`rounded-sm border px-2.5 py-1 text-[12.5px] font-medium transition-colors ${
                  active
                    ? 'border-primary-700 bg-primary-700 text-white'
                    : 'border-border bg-white text-text-600 hover:border-primary-300'
                }`}
              >
                {district.name}
                {!isOwn ? (
                  <span className={active ? 'text-primary-200' : 'text-text-400'}> · outside scope</span>
                ) : null}
              </button>
            );
          })}
        </div>
        <p className="mt-3 text-[12px] leading-relaxed text-text-500">
          Viewing only. Team deployment, the intervention plan and the budget below stay scoped to
          your account&rsquo;s own districts regardless of what is selected here.
        </p>
      </fieldset>

      <div className="space-y-4">
        {shown.length === 0 ? (
          <Callout tone="info">Select a district above to see its assessment.</Callout>
        ) : (
          shown.map((item) => {
            const district = byId.get(item.district_id);
            return (
              <Card key={item.district_id} padding="lg" accent="navy">
                <div className="grid gap-5 md:grid-cols-[minmax(0,15rem)_1fr]">
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <RiskPill incidence={item.incidence_per_100k} />
                      {item.is_rising_fast ? (
                        <span className="rounded-sm bg-state-50 px-2 py-0.5 text-[11px] font-bold uppercase tracking-wide text-state-700 ring-1 ring-state-100">
                          Rising fast
                        </span>
                      ) : null}
                    </div>
                    <h3 className="text-h3 mt-2">{item.district}</h3>
                    <p className="num mt-1 text-[13px] text-text-600">
                      {num(item.forecast_median)} cases ·{' '}
                      {item.incidence_per_100k?.toFixed(1)}/100k ·{' '}
                      <span className={(item.change_pct ?? 0) > 0 ? 'text-state-600' : 'text-teal-700'}>
                        {signedPct(item.change_pct)}
                      </span>
                      {district?.facilities != null ? ` · ${district.facilities} facilities` : ''}
                    </p>
                    {district?.facilityPoor ? (
                      <p className="mt-3 flex items-start gap-1.5 border-t border-border pt-3 text-[12px] leading-snug text-text-600">
                        <BuildingOffice2Icon className="mt-0.5 h-4 w-4 shrink-0 text-state-600" aria-hidden />
                        <span>
                          <strong className="text-text-900">Facility-poor.</strong> Least facility
                          coverage per head — qualifies for the allocation floor.
                        </span>
                      </p>
                    ) : null}
                  </div>
                  <RecommendationList items={item.recommendations} limit={3} />
                </div>
              </Card>
            );
          })
        )}
      </div>
    </div>
  );
}

export default HotspotPanel;
