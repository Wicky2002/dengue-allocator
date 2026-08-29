'use client';

import React from 'react';
import { geoMercator, geoPath } from 'd3-geo';
import type { GeoPermissibleObjects } from 'd3-geo';

import type { DistrictGeometry } from '@/lib/types';

export interface FacilityPoint {
  id: string;
  name: string | null;
  type: string | null;
  lat: number | null;
  lon: number | null;
  district_id?: string | null;
}

const TYPE_COLOURS: Record<string, string> = {
  hospital: '#B91C1C',
  clinic: '#1D4ED8',
  doctors: '#0F766E',
  health_post: '#CA8A04',
};

/**
 * Health facilities plotted over the district outlines.
 *
 * Points only — no bed counts, no capacity shading. OpenStreetMap carries the
 * locations for Sri Lanka but almost none of the bed tags, and a map that
 * inferred capacity from a national average would be inventing exactly the
 * figure a hospital planner would most want to trust.
 */
export function FacilityMap({
  geometry: provided = null,
  facilities,
  height = 620,
}: {
  /** Pass the geometry to render it server-side; omit it to fetch the static
   *  copy instead. Omitting is right where the map is secondary content: the
   *  outlines are 109 KB, and fetching them lets the browser cache one copy
   *  across pages rather than embedding them in every server payload. */
  geometry?: DistrictGeometry | null;
  facilities: FacilityPoint[];
  height?: number;
}) {
  const [type, setType] = React.useState<string>('all');
  const [fetched, setFetched] = React.useState<DistrictGeometry | null>(null);
  const width = 460;

  React.useEffect(() => {
    if (provided) return;
    let cancelled = false;
    fetch('/data/districts.geojson')
      .then((response) => (response.ok ? response.json() : null))
      .then((value) => {
        if (!cancelled) setFetched(value as DistrictGeometry | null);
      })
      .catch(() => {
        // The facility counts in the tables above stand on their own, so a
        // failed geometry fetch degrades this panel rather than the page.
      });
    return () => {
      cancelled = true;
    };
  }, [provided]);

  const geometry = provided ?? fetched;

  const types = React.useMemo(() => {
    const counts = new Map<string, number>();
    for (const facility of facilities) {
      const key = facility.type ?? 'other';
      counts.set(key, (counts.get(key) ?? 0) + 1);
    }
    return Array.from(counts.entries()).sort((a, b) => b[1] - a[1]);
  }, [facilities]);

  const { paths, points } = React.useMemo(() => {
    if (!geometry || geometry.features.length === 0) return { paths: [], points: [] };
    const projection = geoMercator().fitExtent(
      [
        [12, 12],
        [width - 12, height - 12],
      ],
      geometry as unknown as GeoPermissibleObjects,
    );
    const path = geoPath(projection);
    return {
      paths: geometry.features.map((feature) => ({
        id: String(feature.properties.district_id ?? ''),
        d: path(feature as unknown as GeoPermissibleObjects) ?? '',
      })),
      points: facilities
        .filter((facility) => facility.lat != null && facility.lon != null)
        .map((facility) => {
          const projected = projection([facility.lon as number, facility.lat as number]);
          return projected ? { ...facility, x: projected[0], y: projected[1] } : null;
        })
        .filter((value): value is FacilityPoint & { x: number; y: number } => value != null),
    };
  }, [geometry, facilities, height]);

  if (paths.length === 0) {
    return (
      <div className="grid min-h-[240px] place-items-center rounded-sm border border-dashed border-border bg-bg-100 p-6 text-center text-sm text-text-600">
        Map geometry unavailable — facility counts are still shown in the tables above.
      </div>
    );
  }

  const visible = type === 'all' ? points : points.filter((p) => (p.type ?? 'other') === type);

  return (
    <div className="rounded-sm border border-border bg-white p-4 shadow-card">
      <div className="mb-3 flex flex-wrap gap-2">
        <FilterChip active={type === 'all'} onClick={() => setType('all')}>
          All ({points.length.toLocaleString()})
        </FilterChip>
        {types.map(([key, count]) => (
          <FilterChip key={key} active={type === key} onClick={() => setType(key)}>
            <span
              aria-hidden
              className="h-2 w-2 rounded-full"
              style={{ background: TYPE_COLOURS[key] ?? '#6B7280' }}
            />
            {key.replace('_', ' ')} ({count.toLocaleString()})
          </FilterChip>
        ))}
      </div>

      <svg
        viewBox={`0 0 ${width} ${height}`}
        className="mx-auto block h-auto max-h-[620px] w-auto max-w-full"
        role="img"
        aria-label="Health facility locations"
      >
        {paths.map((feature) => (
          <path key={feature.id} d={feature.d} fill="#F3F4F6" stroke="#D1D5DB" strokeWidth={0.6} />
        ))}
        {visible.map((facility) => (
          <circle
            key={facility.id}
            cx={facility.x}
            cy={facility.y}
            r={facility.type === 'hospital' ? 3 : 1.8}
            fill={TYPE_COLOURS[facility.type ?? 'other'] ?? '#6B7280'}
            fillOpacity={0.75}
          >
            <title>{`${facility.name ?? 'Unnamed facility'} (${facility.type ?? 'unknown'})`}</title>
          </circle>
        ))}
      </svg>
    </div>
  );
}

function FilterChip({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={active}
      className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-medium capitalize transition-colors ${
        active ? 'bg-primary-700 text-white' : 'bg-bg-200 text-text-700 hover:bg-bg-300'
      }`}
    >
      {children}
    </button>
  );
}

export default FacilityMap;
