'use client';

import React from 'react';
import { ChevronDownIcon, BeakerIcon } from '@heroicons/react/24/outline';

import { useT } from '@/components/i18n/LocaleProvider';

const ITEMS = ['1', '2', '3'];

/** Common misconceptions, collapsed by default so the page leads with actions. */
export function MythVsFact() {
  const t = useT();
  const [open, setOpen] = React.useState(false);
  return (
    <div className="rounded-sm border border-border bg-white shadow-card">
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        aria-expanded={open}
        className="flex w-full items-center justify-between gap-3 px-5 py-4 text-left"
      >
        <span className="inline-flex items-center gap-2 font-semibold text-text-900">
          <BeakerIcon className="h-5 w-5 text-primary-700" aria-hidden />
          {t('myth.title')}
        </span>
        <ChevronDownIcon
          className={`h-5 w-5 text-text-500 transition-transform ${open ? 'rotate-180' : ''}`}
          aria-hidden
        />
      </button>
      {open ? (
        <dl className="space-y-4 border-t border-border px-5 py-5">
          {ITEMS.map((n) => (
            <div key={n}>
              <dt className="text-sm font-semibold text-state-600">
                {t('myth.label')}: {t(`myth.${n}`)}
              </dt>
              <dd className="mt-1 text-sm leading-relaxed text-text-600">
                <span className="font-semibold text-teal-700">{t('fact.label')}:</span>{' '}
                {t(`fact.${n}`)}
              </dd>
            </div>
          ))}
        </dl>
      ) : null}
    </div>
  );
}

export default MythVsFact;
