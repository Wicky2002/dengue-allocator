'use client';

import React from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { MapPinIcon } from '@heroicons/react/24/outline';

import { useT } from '@/components/i18n/LocaleProvider';

/**
 * District selector that writes to the URL.
 *
 * The selected district is in the query string rather than in component state
 * so that a link to "risk in Batticaloa" is a link someone can send —
 * which is the whole point of a public risk page.
 */
export function DistrictPicker({
  districts,
  selected,
  basePath,
}: {
  districts: { district_id: string; name: string }[];
  selected: string;
  basePath: string;
}) {
  const router = useRouter();
  const params = useSearchParams();
  const t = useT();

  return (
    <label className="flex flex-wrap items-center gap-3">
      <span className="inline-flex items-center gap-1.5 text-sm font-medium text-text-700">
        <MapPinIcon className="h-4 w-4 text-primary-700" aria-hidden />
        {t('public.yourDistrict')}
      </span>
      <select
        value={selected}
        onChange={(event) => {
          const next = new URLSearchParams(params.toString());
          next.set('district', event.target.value);
          router.push(`${basePath}?${next.toString()}`, { scroll: false });
        }}
        className="rounded-sm border border-border bg-white px-3 py-2 text-sm font-medium text-text-900 shadow-card focus:border-primary-700"
      >
        {districts.map((district) => (
          <option key={district.district_id} value={district.district_id}>
            {district.name}
          </option>
        ))}
      </select>
    </label>
  );
}

export default DistrictPicker;
