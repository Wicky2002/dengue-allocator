'use client';

import React from 'react';

import { DEFAULT_LOCALE, type Locale } from '@/lib/i18n/config';
import type { Dictionary } from '@/lib/i18n/dictionaries';

interface LocaleContextValue {
  locale: Locale;
  dictionary: Dictionary;
}

const LocaleContext = React.createContext<LocaleContextValue>({
  locale: DEFAULT_LOCALE,
  dictionary: {},
});

/**
 * Makes the resolved dictionary available to client components.
 *
 * The server resolves the language once per request and hands the merged
 * dictionary down, so no client component fetches translations or decides
 * which language it is in.
 */
export function LocaleProvider({
  locale,
  dictionary,
  children,
}: {
  locale: Locale;
  dictionary: Dictionary;
  children: React.ReactNode;
}) {
  const value = React.useMemo(() => ({ locale, dictionary }), [locale, dictionary]);
  return <LocaleContext.Provider value={value}>{children}</LocaleContext.Provider>;
}

/** Translator for client components. Falls back to the key if nothing matches. */
export function useT() {
  const { dictionary } = React.useContext(LocaleContext);
  return React.useCallback((key: string) => dictionary[key] ?? key, [dictionary]);
}

export function useLocale(): Locale {
  return React.useContext(LocaleContext).locale;
}
