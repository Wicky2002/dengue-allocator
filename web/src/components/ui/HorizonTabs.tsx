'use client';

import React from 'react';
import Link from 'next/link';

import { useT } from '@/components/i18n/LocaleProvider';

/**
 * Forecast-horizon switcher.
 *
 * Plain links with a query parameter, not client state: the horizon is part of
 * what a page *is*, so a shared or bookmarked URL has to reproduce the same
 * screen. Every horizon is precomputed in the artifacts -- switching indexes a
 * sweep, it never re-solves anything.
 */
export function HorizonTabs({
  horizons,
  active,
  basePath,
  extraParams = {},
}: {
  horizons: number[];
  active: number;
  basePath: string;
  extraParams?: Record<string, string | undefined>;
}) {
  const t = useT();
  if (horizons.length < 2) return null;

  const href = (horizon: number) => {
    const params = new URLSearchParams();
    for (const [key, value] of Object.entries(extraParams)) {
      if (value) params.set(key, value);
    }
    params.set('horizon', String(horizon));
    return `${basePath}?${params.toString()}`;
  };

  return (
    <div className="flex flex-wrap items-center gap-3">
      <span className="text-sm font-medium text-text-600">{t('public.horizon')}</span>
      <div className="inline-flex rounded-sm border border-border bg-white" role="tablist">
        {horizons.map((horizon) => (
          <Link
            key={horizon}
            href={href(horizon)}
            scroll={false}
            role="tab"
            aria-selected={horizon === active}
            className={`rounded-md px-3.5 py-1.5 text-sm font-medium transition-colors ${
              horizon === active
                ? 'bg-primary-700 text-white'
                : 'text-text-600 hover:bg-bg-100 hover:text-text-900'
            }`}
          >
            {horizon} {t('public.weeks')}
          </Link>
        ))}
      </div>
    </div>
  );
}

export default HorizonTabs;
