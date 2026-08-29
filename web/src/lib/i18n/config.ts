/**
 * Trilingual support.
 *
 * Sri Lanka has two official languages, Sinhala and Tamil, with English as a
 * link language — a public health platform that citizens are asked to act on
 * has to speak all three. English is the default here because the staff
 * portals and the whole modelling vocabulary are written in it; the citizen
 * pages are where the other two matter most, and those are translated in full.
 */

export const LOCALES = [
  { code: 'en', label: 'English', native: 'English', dir: 'ltr' },
  { code: 'si', label: 'Sinhala', native: 'සිංහල', dir: 'ltr' },
  { code: 'ta', label: 'Tamil', native: 'தமிழ்', dir: 'ltr' },
] as const;

export type Locale = (typeof LOCALES)[number]['code'];

export const DEFAULT_LOCALE: Locale = 'en';

/** Where the choice is remembered. Readable by the server on the next request. */
export const LOCALE_COOKIE = 'denguesentinel.locale';

export function isLocale(value: string | undefined | null): value is Locale {
  return LOCALES.some((locale) => locale.code === value);
}

export function localeMeta(code: Locale) {
  return LOCALES.find((locale) => locale.code === code) ?? LOCALES[0];
}
