'use client';

import React from 'react';
import { MagnifyingGlassIcon, ChevronDownIcon } from '@heroicons/react/24/outline';

import { ProvenanceChip } from '@/components/ui/ProvenanceChip';
import { FacilityMap, type FacilityPoint } from '@/components/charts/FacilityMap';
import { num, pct } from '@/lib/format';
import { DEFAULT_RATIOS, projectReadiness, ratioBasis } from '@/lib/readiness';
import type { ReadinessInput } from './ReadinessWorkspace';

/**
 * Look at a district your account is not scoped to.
 *
 * **Preview only — it does not change what the account can act on.** The
 * readiness table, supply projection and bed-pressure map above stay filtered to
 * the account's own districts; this shows the same public planning arithmetic
 * for one other district, at default ratios, so a hospital preparing to receive
 * transfers can see what its neighbour is facing.
 *
 * It is a deliberate, labelled exception rather than a hole in the scope rule:
 * everything it displays is derived from the district forecast and the public
 * facility register, both of which the public portal already shows.
 */
export function DistrictPreview({
  candidates,
  facilities,
}: {
  candidates: ReadinessInput[];
  facilities: FacilityPoint[];
}) {
  const [open, setOpen] = React.useState(false);
  const [districtId, setDistrictId] = React.useState(candidates[0]?.district_id ?? '');

  if (candidates.length === 0) {
    return (
      <p className="rounded-sm border border-border bg-white p-4 text-[13px] text-text-600 shadow-card">
        Your account already covers every district.
      </p>
    );
  }

  const input = candidates.find((c) => c.district_id === districtId) ?? candidates[0];
  const readiness = projectReadiness(input, DEFAULT_RATIOS);
  const basis = ratioBasis(DEFAULT_RATIOS, false);
  const districtFacilities = facilities.filter((f) => f.district_id === input.district_id);

  return (
    <div className="rounded-sm border border-border bg-white shadow-card">
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        aria-expanded={open}
        className="flex w-full items-center justify-between gap-3 px-5 py-4 text-left"
      >
        <span className="inline-flex items-center gap-2 font-semibold text-text-900">
          <MagnifyingGlassIcon className="h-5 w-5 text-primary-700" aria-hidden />
          Preview another district
        </span>
        <ChevronDownIcon
          className={`h-5 w-5 text-text-500 transition-transform ${open ? 'rotate-180' : ''}`}
          aria-hidden
        />
      </button>

      {open ? (
        <div className="border-t border-border p-5">
          <p className="mb-4 text-[13px] text-text-600">
            Preview only — this does not change your account&rsquo;s access. Figures use the
            default planning ratios, not any changes you made under Planning ratios.
          </p>

          <label className="flex flex-wrap items-center gap-3">
            <span className="text-[13px] font-medium text-text-700">District</span>
            <select
              value={input.district_id}
              onChange={(event) => setDistrictId(event.target.value)}
              className="rounded-sm border border-border bg-white px-3 py-2 text-sm font-medium"
            >
              {candidates.map((candidate) => (
                <option key={candidate.district_id} value={candidate.district_id}>
                  {candidate.district}
                </option>
              ))}
            </select>
            <ProvenanceChip tier="assumed" basis={basis} />
          </label>

          <dl className="mt-5 grid grid-cols-2 gap-4 lg:grid-cols-4">
            {[
              ['Forecast cases', num(readiness.forecastCases)],
              ['Admissions', num(readiness.admissions)],
              ['ICU patients', num(readiness.icuPatients, 1)],
              ['Occupancy', pct(readiness.occupancyPct, 0)],
            ].map(([label, value]) => (
              <div key={label} className="border-t-2 border-t-primary-700 bg-bg-100 p-3">
                <dt className="text-[11px] uppercase tracking-wide text-text-500">{label}</dt>
                <dd className="num mt-1 text-[20px] font-bold leading-none text-primary-900">
                  {value}
                </dd>
              </div>
            ))}
          </dl>

          <p className="num mt-4 text-[13px] text-text-600">
            <strong className="text-text-900">Status:</strong> {readiness.capacityStatus}
            {' · '}
            <strong className="text-text-900">Hospitals:</strong> {num(readiness.nHospitals)}
            {' · '}
            <strong className="text-text-900">Facilities:</strong> {num(readiness.nFacilities)}
          </p>

          <div className="mt-5">
            <h4 className="mb-3 font-heading text-[15px] font-semibold text-text-900">
              Facilities in {input.district}
            </h4>
            {districtFacilities.length > 0 ? (
              <FacilityMap facilities={districtFacilities} height={420} />
            ) : (
              <p className="text-[13px] text-text-600">
                No OpenStreetMap facilities are recorded for this district.
              </p>
            )}
          </div>
        </div>
      ) : null}
    </div>
  );
}

export default DistrictPreview;
