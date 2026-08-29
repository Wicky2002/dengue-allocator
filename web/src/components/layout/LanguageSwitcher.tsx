'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import { GlobeAltIcon } from '@heroicons/react/24/outline';

import { LOCALES, type Locale } from '@/lib/i18n/config';
import { setLocale } from '@/app/actions/locale';
import { useT } from '@/components/i18n/LocaleProvider';

/**
 * Sinhala / English / Tamil.
 *
 * Each option is labelled in its own script, never in English — someone who
 * reads only Tamil should not have to recognise the word "Tamil" to find their
 * language. The three sit side by side rather than in a dropdown for the same
 * reason: no interaction is needed to discover that the other two exist.
 */
export function LanguageSwitcher({ current }: { current: Locale }) {
  const router = useRouter();
  const t = useT();
  const [pending, startTransition] = React.useTransition();

  const choose = (code: Locale) => {
    if (code === current) return;
    startTransition(async () => {
      await setLocale(code);
      router.refresh();
    });
  };

  return (
    <div className="flex items-center gap-1.5">
      <GlobeAltIcon className="h-3.5 w-3.5 shrink-0 text-text-500" aria-hidden />
      <span className="sr-only" id="language-label">
        {t('banner.language')}
      </span>
      <div
        role="group"
        aria-labelledby="language-label"
        className={`flex overflow-hidden rounded-sm border border-border bg-white ${
          pending ? 'opacity-60' : ''
        }`}
      >
        {LOCALES.map((locale) => {
          const active = locale.code === current;
          return (
            <button
              key={locale.code}
              type="button"
              lang={locale.code}
              onClick={() => choose(locale.code)}
              aria-current={active ? 'true' : undefined}
              title={locale.label}
              className={`border-r border-border px-2 py-0.5 text-[12px] font-semibold leading-5 transition-colors last:border-r-0 ${
                active
                  ? 'bg-primary-800 text-white'
                  : 'text-text-600 hover:bg-bg-200 hover:text-primary-800'
              }`}
            >
              {locale.native}
            </button>
          );
        })}
      </div>
    </div>
  );
}

export default LanguageSwitcher;
