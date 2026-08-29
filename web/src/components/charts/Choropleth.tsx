'use client';

import React from 'react';
import { geoMercator, geoPath } from 'd3-geo';
import type { GeoPermissibleObjects } from 'd3-geo';

import { RISK_BANDS, classify } from '@/lib/risk';
import { num } from '@/lib/format';
import type { DistrictGeometry } from '@/lib/types';

export interface ChoroplethDatum {
  district_id: string;
  name: string;
  incidence: number | null;
  median: number | null;
}

/**
 * District risk map.
 *
 * Drawn as inline SVG from the bundled OCHA geometry rather than through a tile
 * map: there is no basemap to load, nothing leaves the browser, and the whole
 * map is 25 `<path>` elements that print and screen-read cleanly. Fill comes
 * from the same four bands the engine defines -- see `lib/risk`.
 */
export function Choropleth({
  geometry: provided = null,
  data,
  selected,
  onSelect,
  height = 520,
  maxHeightClass = 'max-h-[540px]',
  showLegend = true,
  emptyMessage,
}: {
  /** Pass the geometry to render server-side; omit it to fetch the static copy.
   *  Omitting matters when several maps share a page: the outlines are ~180 KB,
   *  and embedding them once per map triples the payload for nothing. */
  geometry?: DistrictGeometry | null;
  data: ChoroplethDatum[];
  selected?: string | null;
  onSelect?: (districtId: string) => void;
  height?: number;
  /** Caps the rendered height; paired maps need a smaller cap than a solo one. */
  maxHeightClass?: string;
  /** Suppressed on paired maps, which share one legend between them. */
  showLegend?: boolean;
  /** Shown instead of the map when there is nothing to colour. */
  emptyMessage?: string;
}) {
  const [hovered, setHovered] = React.useState<string | null>(null);
  const [fetched, setFetched] = React.useState<DistrictGeometry | null>(null);
  const width = 420;

  React.useEffect(() => {
    if (provided) return;
    let cancelled = false;
    fetch('/data/districts.geojson')
      .then((response) => (response.ok ? response.json() : null))
      .then((value) => {
        if (!cancelled) setFetched(value as DistrictGeometry | null);
      })
      .catch(() => {
        // The ranked list and the week figures stand on their own, so a failed
        // geometry fetch degrades this map rather than the page.
      });
    return () => {
      cancelled = true;
    };
  }, [provided]);

  const geometry = provided ?? fetched;

  const byId = React.useMemo(
    () => new Map(data.map((row) => [row.district_id, row])),
    [data],
  );

  const paths = React.useMemo(() => {
    if (!geometry || geometry.features.length === 0) return [];
    const projection = geoMercator().fitExtent(
      [
        [12, 12],
        [width - 12, height - 12],
      ],
      geometry as unknown as GeoPermissibleObjects,
    );
    const path = geoPath(projection);
    return geometry.features.map((feature) => ({
      id: String((feature.properties.district_id as string) ?? ''),
      name: String((feature.properties.name as string) ?? ''),
      d: path(feature as unknown as GeoPermissibleObjects) ?? '',
    }));
  }, [geometry, height]);

  if (paths.length === 0 || (data.length === 0 && emptyMessage)) {
    return (
      <div className="grid h-full min-h-[240px] place-items-center rounded-sm border border-dashed border-border bg-bg-100 p-6 text-center text-sm text-text-600">
        {data.length === 0 && emptyMessage
          ? emptyMessage
          : 'Map geometry unavailable — the ranked list beside this map shows every district, so nothing is hidden by its absence.'}
      </div>
    );
  }

  const active = hovered ?? selected ?? null;
  const activeRow = active ? byId.get(active) : null;

  return (
    <div className="relative">
      {/* Sri Lanka is tall and narrow, so a width-filling SVG grows far taller
          than the ranked list beside it and leaves the row half empty. Cap the
          height and centre it instead: the aspect ratio is preserved and the
          two columns finish level. */}
      <svg
        viewBox={`0 0 ${width} ${height}`}
        className={`mx-auto block h-auto w-auto max-w-full ${maxHeightClass}`}
        role="img"
        aria-label="Forecast dengue risk by district"
      >
        {paths.map((feature) => {
          const row = byId.get(feature.id);
          const band = classify(row?.incidence);
          const isActive = active === feature.id;
          const dimmed = selected != null && selected !== feature.id && hovered == null;
          return (
            <path
              key={feature.id}
              d={feature.d}
              fill={band.colour}
              stroke={isActive ? '#111827' : '#ffffff'}
              strokeWidth={isActive ? 1.6 : 0.7}
              opacity={dimmed ? 0.45 : 1}
              className={onSelect ? 'cursor-pointer transition-opacity' : 'transition-opacity'}
              onMouseEnter={() => setHovered(feature.id)}
              onMouseLeave={() => setHovered(null)}
              onClick={() => onSelect?.(feature.id)}
              tabIndex={onSelect ? 0 : -1}
              onKeyDown={(event) => {
                if (onSelect && (event.key === 'Enter' || event.key === ' ')) {
                  event.preventDefault();
                  onSelect(feature.id);
                }
              }}
            >
              <title>
                {`${feature.name}: ${
                  row?.incidence != null
                    ? `${row.incidence.toFixed(1)} per 100,000`
                    : 'no forecast'
                }`}
              </title>
            </path>
          );
        })}
      </svg>

      {activeRow ? (
        <div className="pointer-events-none absolute left-3 top-3 rounded-sm border border-border bg-white/95 px-3 py-2 text-xs shadow-card backdrop-blur">
          <p className="font-semibold text-text-900">{activeRow.name}</p>
          <p className="num mt-0.5 text-text-600">
            {activeRow.incidence != null ? `${activeRow.incidence.toFixed(1)} per 100,000/week` : 'No forecast'}
          </p>
          <p className="num text-text-500">{num(activeRow.median)} cases forecast</p>
        </div>
      ) : null}

      {showLegend ? (
      <ul className="mt-4 grid grid-cols-2 gap-x-4 gap-y-2 sm:grid-cols-4">
        {RISK_BANDS.map((band) => (
          <li key={band.key} className="flex items-start gap-2">
            <span
              aria-hidden
              className="mt-1 h-3 w-3 shrink-0 rounded-sm"
              style={{ background: band.colour }}
            />
            <span className="text-xs leading-tight">
              <span className="block font-semibold text-text-800">{band.label}</span>
              <span className="num block text-text-500">
                {band.threshold === 0 ? 'under 1.5' : `${band.threshold}+`} per 100k/wk
              </span>
            </span>
          </li>
        ))}
      </ul>
      ) : null}
    </div>
  );
}

export default Choropleth;
