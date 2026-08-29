'use client';

import React from 'react';
import { ArrowPathIcon } from '@heroicons/react/24/outline';

import { Callout } from '@/components/ui/Callout';
import { CapacityMap } from './CapacityMap';
import { Card } from '@/components/ui/Card';
import { StatTile } from '@/components/ui/StatTile';
import { NoDataPanel } from '@/components/ui/NoDataPanel';
import { ProvenanceChip } from '@/components/ui/ProvenanceChip';
import { num, pct } from '@/lib/format';
import {
  DEFAULT_RATIOS,
  projectReadiness,
  ratioBasis,
  validateRatios,
  type ClinicalRatios,
  type Readiness,
} from '@/lib/readiness';

export interface ReadinessInput {
  district_id: string;
  district: string;
  forecastCases: number;
  forecastUpper: number | null;
  estimatedBeds: number;
  nHospitals: number;
  nFacilities: number;
  population: number;
}

const SLIDERS: {
  key: keyof ClinicalRatios;
  label: string;
  min: number;
  max: number;
  step: number;
  format: (value: number) => string;
}[] = [
  { key: 'hospitalisation_rate', label: 'Hospitalisation rate', min: 0.1, max: 1, step: 0.05, format: (v) => `${(v * 100).toFixed(0)}%` },
  { key: 'severe_fraction_of_admitted', label: 'Severe fraction', min: 0.01, max: 0.25, step: 0.01, format: (v) => `${(v * 100).toFixed(0)}%` },
  { key: 'icu_fraction_of_admitted', label: 'ICU fraction', min: 0.001, max: 0.1, step: 0.005, format: (v) => `${(v * 100).toFixed(1)}%` },
  { key: 'mean_length_of_stay_days', label: 'Mean stay (days)', min: 1, max: 10, step: 0.5, format: (v) => `${v.toFixed(1)} d` },
  { key: 'platelet_units_per_severe_case', label: 'Platelet units / severe case', min: 0, max: 12, step: 0.5, format: (v) => v.toFixed(1) },
  { key: 'nurses_per_occupied_bed', label: 'Nurses per occupied bed', min: 0.05, max: 0.6, step: 0.05, format: (v) => v.toFixed(2) },
];

type TabKey = 'load' | 'supplies' | 'pressure' | 'ratios';

/**
 * The readiness table, its supply projection, and the ratios behind both.
 *
 * The ratios are the whole point of this screen being interactive: they are
 * planning values from the literature for endemic settings, not Sri Lankan
 * measurements, and an officer who knows their own case mix should be able to
 * see the table under their own assumptions rather than argue with a fixed one.
 */
export function ReadinessWorkspace({
  inputs,
  horizon,
}: {
  inputs: ReadinessInput[];
  horizon: number;
}) {
  const [ratios, setRatios] = React.useState<ClinicalRatios>(DEFAULT_RATIOS);
  const [tab, setTab] = React.useState<TabKey>('load');

  const error = validateRatios(ratios);
  const effective = error ? DEFAULT_RATIOS : ratios;
  const customised = JSON.stringify(effective) !== JSON.stringify(DEFAULT_RATIOS);

  const rows: Readiness[] = React.useMemo(
    () =>
      inputs
        .map((input) => projectReadiness(input, effective))
        .sort((a, b) => b.occupancyPct - a.occupancyPct),
    [inputs, effective],
  );

  const totals = rows.reduce(
    (acc, row) => ({
      admissions: acc.admissions + row.admissions,
      severe: acc.severe + row.severeCases,
      icu: acc.icu + row.icuPatients,
      beds: acc.beds + row.peakOccupiedBeds,
      platelets: acc.platelets + row.plateletUnits,
      nurses: acc.nurses + row.additionalNurses,
    }),
    { admissions: 0, severe: 0, icu: 0, beds: 0, platelets: 0, nurses: 0 },
  );
  const basis = ratioBasis(effective, customised);

  return (
    <div>
      <div className="mb-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        <StatTile
          label="Projected admissions"
          value={num(totals.admissions)}
          tier="assumed"
          basis={basis}
          hint={`Next ${horizon} weeks`}
        />
        <StatTile label="ICU patients" value={num(totals.icu, 1)} tier="assumed" basis={basis} hint="Concurrent" />
        <StatTile
          label="Peak occupied beds"
          value={num(totals.beds)}
          tier="assumed"
          basis={basis}
          hint="Dengue beds"
        />
        <StatTile
          label="Platelet units"
          value={num(totals.platelets)}
          tier="assumed"
          basis={basis}
          hint="Projected demand"
        />
        <StatTile
          label="Additional nurses"
          value={num(totals.nurses)}
          tier="assumed"
          basis={basis}
          hint={`At 1:${Math.round(1 / effective.nurses_per_occupied_bed)} ratio`}
        />
      </div>

      <Callout tone="warning" title="Every figure on this page is a planning estimate, not a measurement" className="mb-6">
        No public source publishes Sri Lankan hospital occupancy, ICU census, platelet stock or
        staffing. These numbers apply published clinical ratios to the case forecast — the same
        arithmetic a planner would do on paper.{' '}
        {customised
          ? 'Recomputed live from the ratios you set under Planning ratios.'
          : 'Adjust the ratios under Planning ratios to match your own case mix.'}
      </Callout>

      <div className="mb-5 flex border-b border-border">
        {(
          [
            ['load', 'Projected load'],
            ['supplies', 'Supplies'],
            ['pressure', 'Bed pressure'],
            ['ratios', 'Planning ratios'],
          ] as [TabKey, string][]
        ).map(([key, label]) => (
          <button
            key={key}
            type="button"
            onClick={() => setTab(key)}
            aria-pressed={tab === key}
            className={`rounded-md px-4 py-2 text-sm font-medium transition-colors ${
              tab === key ? 'bg-primary-700 text-white' : 'text-text-600 hover:bg-bg-100'
            }`}
          >
            {label}
            {key === 'ratios' && customised ? (
              <span className="ml-2 rounded-sm bg-state-600 px-1.5 py-0.5 text-[10px] font-bold text-white">
                edited
              </span>
            ) : null}
          </button>
        ))}
      </div>

      {tab === 'load' ? (
        <>
          <div className="overflow-x-auto rounded-sm border border-border bg-white shadow-card">
            <table className="w-full min-w-[880px] border-collapse text-sm">
              <thead className="border-b border-border bg-bg-100 text-xs uppercase tracking-wide text-text-500">
                <tr>
                  <th scope="col" className="px-3 py-3 text-left">District</th>
                  <th scope="col" className="px-3 py-3 text-right">Forecast cases</th>
                  <th scope="col" className="px-3 py-3 text-right">Admissions</th>
                  <th scope="col" className="px-3 py-3 text-right">Severe</th>
                  <th scope="col" className="px-3 py-3 text-right">ICU</th>
                  <th scope="col" className="px-3 py-3 text-right">Paediatric</th>
                  <th scope="col" className="px-3 py-3 text-right">Peak beds</th>
                  <th scope="col" className="px-3 py-3 text-right">Occupancy</th>
                  <th scope="col" className="px-3 py-3 text-left">Status</th>
                  <th scope="col" className="px-3 py-3 text-right">Hospitals</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row) => (
                  <tr key={row.district_id} className="border-b border-border last:border-0 hover:bg-bg-100">
                    <td className="px-3 py-2.5 font-medium text-text-900">{row.district}</td>
                    <td className="num px-3 py-2.5 text-right">{num(row.forecastCases)}</td>
                    <td className="num px-3 py-2.5 text-right font-semibold">{num(row.admissions)}</td>
                    <td className="num px-3 py-2.5 text-right">{num(row.severeCases, 1)}</td>
                    <td className="num px-3 py-2.5 text-right">{num(row.icuPatients, 1)}</td>
                    <td className="num px-3 py-2.5 text-right">{num(row.paediatricAdmissions)}</td>
                    <td className="num px-3 py-2.5 text-right">{num(row.peakOccupiedBeds)}</td>
                    <td className="num px-3 py-2.5 text-right">{pct(row.occupancyPct, 1)}</td>
                    <td className="px-3 py-2.5">
                      <StatusPill status={row.capacityStatus} />
                    </td>
                    <td className="num px-3 py-2.5 text-right text-text-600">{num(row.nHospitals)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Callout tone="warning" title="Every figure in this table is a planning estimate" className="mt-4">
            {basis}
          </Callout>
          <p className="mt-3 text-xs leading-relaxed text-text-500">
            <strong>Hospitals</strong> is a real OpenStreetMap count (ODbL), not an estimate —
            the same figure that sets the Stage 3 allocation floor for facility-poor districts.
          </p>
        </>
      ) : null}

      {tab === 'supplies' ? (
        <div className="grid gap-6 lg:grid-cols-3">
          <div className="overflow-x-auto rounded-sm border border-border bg-white shadow-card lg:col-span-2">
            <table className="w-full min-w-[520px] border-collapse text-sm">
              <thead className="border-b border-border bg-bg-100 text-xs uppercase tracking-wide text-text-500">
                <tr>
                  <th scope="col" className="px-3 py-3 text-left">District</th>
                  <th scope="col" className="px-3 py-3 text-right">Platelet units</th>
                  <th scope="col" className="px-3 py-3 text-right">IV fluid (L)</th>
                  <th scope="col" className="px-3 py-3 text-right">Diagnostic kits</th>
                  <th scope="col" className="px-3 py-3 text-right">Extra nurses</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row) => (
                  <tr key={row.district_id} className="border-b border-border last:border-0 hover:bg-bg-100">
                    <td className="px-3 py-2.5 font-medium text-text-900">{row.district}</td>
                    <td className="num px-3 py-2.5 text-right">{num(row.plateletUnits)}</td>
                    <td className="num px-3 py-2.5 text-right">{num(row.ivFluidLitres)}</td>
                    <td className="num px-3 py-2.5 text-right">{num(row.diagnosticTests)}</td>
                    <td className="num px-3 py-2.5 text-right">{num(row.additionalNurses)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="space-y-4">
            <Card padding="lg">
              <div className="flex items-center justify-between">
                <h3 className="text-h3">Total demand</h3>
                <ProvenanceChip tier="assumed" basis={basis} />
              </div>
              <dl className="mt-4 space-y-3 text-sm">
                <div className="flex justify-between gap-4">
                  <dt className="text-text-500">Platelet units</dt>
                  <dd className="num font-semibold text-text-900">{num(totals.platelets)}</dd>
                </div>
                <div className="flex justify-between gap-4">
                  <dt className="text-text-500">Peak beds occupied</dt>
                  <dd className="num font-semibold text-text-900">{num(totals.beds)}</dd>
                </div>
              </dl>
            </Card>
            <NoDataPanel
              title="Current stock on hand"
              reason="Platelet inventory, IV fluid stock and consumable levels are not published for Sri Lankan facilities, so this platform cannot show what you already hold — only what the forecast implies you will need."
              enabledBy="A feed from the hospital pharmacy or blood bank management system."
            />
          </div>
        </div>
      ) : null}

      {tab === 'pressure' ? (
        <div className="grid gap-6 lg:grid-cols-2">
          <div className="rounded-sm border border-border bg-white p-5 shadow-card">
            <div className="mb-4 flex items-start justify-between gap-3">
              <h3 className="text-h3">Projected bed pressure</h3>
              <ProvenanceChip tier="assumed" basis={basis} />
            </div>
            <CapacityMap rows={rows} />
          </div>
          <div className="rounded-sm border border-border bg-white p-5 shadow-card">
            <h3 className="text-h3">Districts by pressure</h3>
            <ol className="mt-4 divide-y divide-border">
              {rows.map((row) => (
                <li key={row.district_id} className="flex items-center justify-between gap-4 py-2.5">
                  <span className="min-w-0">
                    <span className="block truncate text-[14px] font-medium text-text-900">
                      {row.district}
                    </span>
                    <span className="num block text-[12px] text-text-500">
                      {num(row.peakOccupiedBeds)} of {num(row.dengueBedCapacity)} dengue beds
                    </span>
                  </span>
                  <span className="flex shrink-0 items-center gap-3">
                    <span className="num text-[14px] font-semibold text-text-900">
                      {pct(row.occupancyPct, 0)}
                    </span>
                    <StatusPill status={row.capacityStatus} />
                  </span>
                </li>
              ))}
            </ol>
          </div>
        </div>
      ) : null}

      {tab === 'ratios' ? (
        <Card padding="lg">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div className="max-w-2xl">
              <h3 className="text-h3">The assumptions behind every number on this page</h3>
              <p className="mt-2 text-sm leading-relaxed text-text-600">
                These are planning values from the literature for endemic settings —{' '}
                <strong>not Sri Lankan measurements</strong>. Change them to match your own
                case mix; the projected load and supply tables recompute immediately. Nothing
                here touches the Stage 1 forecast or the Stage 3 allocation.
              </p>
            </div>
            {customised ? (
              <button
                type="button"
                onClick={() => setRatios(DEFAULT_RATIOS)}
                className="inline-flex items-center gap-2 rounded-sm border border-border px-3 py-2 text-sm font-medium text-text-700 hover:bg-bg-100"
              >
                <ArrowPathIcon className="h-4 w-4" aria-hidden />
                Reset to defaults
              </button>
            ) : null}
          </div>

          {error ? (
            <Callout tone="danger" title="Invalid ratios — showing defaults" className="mt-5">
              {error}
            </Callout>
          ) : null}

          <div className="mt-6 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {SLIDERS.map((slider) => (
              <label key={slider.key} className="block">
                <span className="flex items-baseline justify-between gap-2">
                  <span className="text-sm font-medium text-text-700">{slider.label}</span>
                  <span className="num text-sm font-semibold text-primary-700">
                    {slider.format(ratios[slider.key])}
                  </span>
                </span>
                <input
                  type="range"
                  min={slider.min}
                  max={slider.max}
                  step={slider.step}
                  value={ratios[slider.key]}
                  onChange={(event) =>
                    setRatios((current) => ({
                      ...current,
                      [slider.key]: Number(event.target.value),
                    }))
                  }
                  className="mt-2 w-full accent-primary-700"
                />
                <span className="num mt-1 flex justify-between text-[11px] text-text-400">
                  <span>{slider.format(slider.min)}</span>
                  <span>default {slider.format(DEFAULT_RATIOS[slider.key])}</span>
                  <span>{slider.format(slider.max)}</span>
                </span>
              </label>
            ))}
          </div>
        </Card>
      ) : null}
    </div>
  );
}

function StatusPill({ status }: { status: Readiness['capacityStatus'] }) {
  const tone = {
    'Over capacity': 'bg-red-50 text-red-800 ring-red-600/25',
    Critical: 'bg-orange-50 text-orange-800 ring-orange-600/25',
    Stretched: 'bg-amber-50 text-amber-800 ring-amber-600/20',
    Comfortable: 'bg-teal-50 text-teal-800 ring-teal-600/20',
  }[status];
  return (
    <span className={`inline-flex whitespace-nowrap rounded-full px-2.5 py-1 text-xs font-semibold ring-1 ${tone}`}>
      {status}
    </span>
  );
}

export default ReadinessWorkspace;
