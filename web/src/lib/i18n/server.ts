import { cookies } from 'next/headers';
import { cache } from 'react';

import { DEFAULT_LOCALE, LOCALE_COOKIE, isLocale, type Locale } from './config';
import { DICTIONARIES, translate, type Dictionary } from './dictionaries';

/**
 * The viewer's language.
 *
 * Read from a cookie rather than a URL prefix. That keeps the eight existing
 * routes as they are, at the cost of a language choice that is not linkable —
 * see the note in the web README about moving to `/si/...` prefixes if
 * shareable per-language URLs become a requirement.
 */
export const getLocale = cache(async (): Promise<Locale> => {
  const value = (await cookies()).get(LOCALE_COOKIE)?.value;
  return isLocale(value) ? value : DEFAULT_LOCALE;
});

export const getDictionary = cache(async (): Promise<Dictionary> => {
  const locale = await getLocale();
  // Merged over English so a key missing from si/ta renders the English
  // sentence rather than a blank space or a raw key.
  return { ...DICTIONARIES.en, ...DICTIONARIES[locale] };
});

/** Server-side translator. */
export async function getT() {
  const locale = await getLocale();
  return (key: string) => translate(locale, key);
}
