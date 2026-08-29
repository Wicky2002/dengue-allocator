'use client';

import React from 'react';
import { geoMercator, geoPath } from 'd3-geo';
import type { GeoPermissibleObjects } from 'd3-geo';

import { pct } from '@/lib/format';
import type { DistrictGeometry } from '@/lib/types';
import type { Readiness } from '@/lib/readiness';

/**
 * Projected bed pressure by district.
 *
 * Four capacity bands rather than a continuous scale, because the decision this
 * map supports is discrete: whether a district needs help, not whether it sits
 * at 71% or 74%. Districts outside the viewer's scope are drawn as outlines
 * only — the shape of the country stays legible without implying data the
 * account may not see.
 */
const STATUS_COLOURS: Record<Readiness['capacityStatus'], string> = {
  Comfortable: '#0f766e',
  Stretched: '#ca8a04',
  Critical: '#ea580c',
  'Over capacity': '#b91c1c',
};

export function CapacityMap({
  rows,
  highlight,
  height = 460,
}: {
  rows: Readiness[];
  highlight?: string | null;
  height?: number;
}) {
  const [geometry, setGeometry] = React.useState<DistrictGeometry | null>(null);
  const [hovered, setHovered] = React.useState<string | null>(null);
  const width = 420;

  React.useEffect(() => {
    let cancelled = false;
    fetch('/data/districts.geojson')
      .then((response) => (response.ok ? response.json() : null))
      .then((value) => {
        if (!cancelled) setGeometry(value as DistrictGeometry | null);
      })
      .catch(() => {
        // The readiness table carries the same figures, so a failed geometry
        // fetch degrades this panel rather than the page.
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const byId = React.useMemo(() => new Map(rows.map((row) => [row.district_id, row])), [rows]);

  const paths = React.useMemo(() => {
    if (!geometry) return [];
    const projection = geoMercator().fitExtent(
      [
        [12, 12],
        [width - 12, height - 12],
      ],
      geometry as unknown as GeoPermissibleObjects,
    );
    const path = geoPath(projection);
    return geometry.features.map((feature) => ({
      id: String(feature.properties.district_id ?? ''),
      name: String(feature.properties.name ?? ''),
      d: path(feature as unknown as GeoPermissibleObjects) ?? '',
    }));
  }, [geometry, height]);

  if (paths.length === 0) {
    return (
      <div className="grid min-h-[240px] place-items-center rounded-sm border border-dashed border-border bg-bg-100 p-6 text-center text-sm text-text-600">
        Map geometry unavailable — the readiness table above carries the same figures.
      </div>
    );
  }

  const active = hovered ?? highlight ?? null;
  const activeRow = active ? byId.get(active) : null;

  return (
    <div className="relative">
      <svg
        viewBox={`0 0 ${width} ${height}`}
        className="mx-auto block h-auto max-h-[420px] w-auto max-w-full"
        role="img"
        aria-label="Projected bed occupancy by district"
      >
        {paths.map((feature) => {
          const row = byId.get(feature.id);
          const isActive = active === feature.id;
          return (
            <path
              key={feature.id}
              d={feature.d}
              fill={row ? STATUS_COLOURS[row.capacityStatus] : '#EDEFF3'}
              stroke={isActive ? '#111A27' : '#ffffff'}
              strokeWidth={isActive ? 1.6 : 0.7}
              onMouseEnter={() => setHovered(feature.id)}
              onMouseLeave={() => setHovered(null)}
            >
              <title>
                {`${feature.name}: ${
                  row ? `${row.capacityStatus}, ${row.occupancyPct.toFixed(0)}% occupancy` : 'outside your scope'
                }`}
              </title>
            </path>
          );
        })}
      </svg>

      {activeRow ? (
        <div className="pointer-events-none absolute left-2 top-2 rounded-sm border border-border bg-white/95 px-3 py-2 text-xs shadow-card">
          <p className="font-semibold text-text-900">{activeRow.district}</p>
          <p className="num mt-0.5 text-text-600">
            {pct(activeRow.occupancyPct, 0)} occupancy · {activeRow.capacityStatus}
          </p>
        </div>
      ) : null}

      <ul className="mt-4 grid grid-cols-2 gap-x-4 gap-y-2 sm:grid-cols-4">
        {(Object.keys(STATUS_COLOURS) as Readiness['capacityStatus'][]).map((status) => (
          <li key={status} className="flex items-center gap-2 text-[12px]">
            <span aria-hidden className="h-3 w-3 shrink-0" style={{ background: STATUS_COLOURS[status] }} />
            <span className="font-medium text-text-700">{status}</span>
          </li>
        ))}
      </ul>
      <p className="mt-3 text-[12px] leading-relaxed text-text-500">
        Bands are projected occupancy against district dengue beds: comfortable below 60%,
        stretched to 85%, critical to 100%, over capacity above. Grey districts are outside your
        account&rsquo;s scope.
      </p>
    </div>
  );
}

export default CapacityMap;
