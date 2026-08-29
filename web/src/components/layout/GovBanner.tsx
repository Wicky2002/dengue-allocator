'use client';

import React from 'react';
import { ChevronDownIcon, LockClosedIcon, BuildingLibraryIcon } from '@heroicons/react/24/outline';
import { Container } from '@/components/ui/Container';
import { LanguageSwitcher } from './LanguageSwitcher';
import { useT, useLocale } from '@/components/i18n/LocaleProvider';

/**
 * The official-site banner.
 *
 * Modelled on the identification banner every national digital service carries:
 * it states which state body operates the site and, expanded, how a visitor can
 * verify that for themselves. On a public health page that people are asked to
 * act on, saying who is speaking comes before saying anything else.
 */
export function GovBanner() {
  const [open, setOpen] = React.useState(false);
  const t = useT();
  const locale = useLocale();

  return (
    <div className="border-b border-border bg-bg-200 text-text-700">
      <Container className="py-1.5">
        <div className="flex flex-wrap items-center gap-x-3 gap-y-1.5 text-[12px] leading-tight">
          <Emblem className="h-4 w-4 shrink-0 text-state-600" />
          <p>
            {t('banner.official')}{' '}
            <span className="font-semibold">{t('banner.government')}</span>
          </p>
          <button
            type="button"
            onClick={() => setOpen((value) => !value)}
            aria-expanded={open}
            className="inline-flex items-center gap-1 font-semibold text-primary-600 underline underline-offset-2 hover:text-primary-800"
          >
            {t('banner.howYouKnow')}
            <ChevronDownIcon
              className={`h-3.5 w-3.5 transition-transform ${open ? 'rotate-180' : ''}`}
              aria-hidden
            />
          </button>
          <div className="ms-auto">
            <LanguageSwitcher current={locale} />
          </div>
        </div>

        {open ? (
          <div className="grid gap-5 pb-4 pt-3 md:grid-cols-2">
            <p className="flex gap-3 text-[13px] leading-relaxed">
              <BuildingLibraryIcon className="mt-0.5 h-5 w-5 shrink-0 text-primary-600" aria-hidden />
              <span>
                <strong className="block text-text-900">{t('banner.operatedTitle')}</strong>
                {t('banner.operatedBody')}
              </span>
            </p>
            <p className="flex gap-3 text-[13px] leading-relaxed">
              <LockClosedIcon className="mt-0.5 h-5 w-5 shrink-0 text-primary-600" aria-hidden />
              <span>
                <strong className="block text-text-900">{t('banner.accessTitle')}</strong>
                {t('banner.accessBody')}
              </span>
            </p>
          </div>
        ) : null}
      </Container>
    </div>
  );
}

/** A simple state emblem mark. Not the national arms — a neutral civic device. */
export function Emblem({ className = '' }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" className={className} aria-hidden fill="none">
      <path
        d="M12 1.8 21 6v6.3c0 5-3.8 8.9-9 10-5.2-1.1-9-5-9-10V6l9-4.2Z"
        fill="currentColor"
        fillOpacity="0.14"
        stroke="currentColor"
        strokeWidth="1.4"
      />
      <path d="M12 7.4v8.4M8.4 11.6h7.2" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
    </svg>
  );
}

export default GovBanner;
