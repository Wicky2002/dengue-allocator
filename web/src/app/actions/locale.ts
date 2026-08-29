'use server';

import { cookies } from 'next/headers';
import { revalidatePath } from 'next/cache';

import { LOCALE_COOKIE, isLocale } from '@/lib/i18n/config';

/** Persist the viewer's language choice for a year. */
export async function setLocale(value: string): Promise<void> {
  if (!isLocale(value)) return;

  (await cookies()).set(LOCALE_COOKIE, value, {
    path: '/',
    maxAge: 60 * 60 * 24 * 365,
    sameSite: 'lax',
  });
  revalidatePath('/', 'layout');
}
