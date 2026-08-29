'use server';

/**
 * Alert subscription — the server action behind the public portal's
 * "Get alerts for your district" panel.
 *
 * Mirrors `dengue.platform.alerts.save_subscription` exactly: same RPC
 * (`subscribe_to_alerts`, a SECURITY DEFINER function — see
 * `supabase/schema.sql` for why a plain anon-key insert isn't used), same
 * anon-key client, same validation, same insert-only semantics (there is no
 * update path; resubmitting supersedes an earlier row, since the weekly
 * sender reads the most recent row per email).
 *
 * Deliberately has no `getSession()`/permission check the way the admin
 * actions do — subscribing needs no account at all, the same way viewing the
 * public portal doesn't. `Permission.SUBSCRIBE_ALERTS` is granted to the
 * public role for exactly this reason.
 */

import { headers } from 'next/headers';

import { getSupabaseServerClient, isAuthConfigured } from '@/lib/supabase/server';
import { isRateLimited } from '@/lib/rate-limit';

export interface AlertSubscribeState {
  error: string | null;
  success: boolean;
}

const EMPTY: AlertSubscribeState = { error: null, success: false };

// A public, unauthenticated write endpoint with no rate limit of its own on
// the Python/Streamlit side (the DB's CHECK constraints are the only guard
// there). Adding one here is a deliberate step beyond parity: 10 submissions
// per IP per hour is generous for a real subscriber changing their mind a
// few times, and blunt enough to slow a script from filling the table.
const MAX_ATTEMPTS = 10;
const WINDOW_MS = 60 * 60 * 1000;

async function clientIp(): Promise<string> {
  const h = await headers();
  const forwarded = h.get('x-forwarded-for');
  if (forwarded) return forwarded.split(',')[0].trim();
  return h.get('x-real-ip') ?? 'unknown';
}

export async function subscribeToAlerts(
  _prev: AlertSubscribeState,
  formData: FormData,
): Promise<AlertSubscribeState> {
  const email = String(formData.get('email') ?? '').trim();
  const districts = formData
    .getAll('districts')
    .map((value) => String(value))
    .filter(Boolean);
  const weeklySummary = formData.get('weekly') === 'on';
  const outbreakOnly = formData.get('outbreakOnly') === 'on';

  // Same validation as save_subscription's own checks, run here first so a
  // bad request never reaches the network call at all -- the table's CHECK
  // constraints are the real backstop, this is just a clearer message than
  // the constraint-violation error they'd otherwise surface as.
  if (!email || !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) {
    return { ...EMPTY, error: 'Enter a valid email address.' };
  }
  if (districts.length === 0) {
    return { ...EMPTY, error: 'Choose at least one district.' };
  }

  const ip = await clientIp();
  if (
    (await isRateLimited(`alerts:email:${email.toLowerCase()}`, MAX_ATTEMPTS, WINDOW_MS)) ||
    (await isRateLimited(`alerts:ip:${ip}`, MAX_ATTEMPTS, WINDOW_MS))
  ) {
    return { ...EMPTY, error: 'Too many attempts. Wait a while and try again.' };
  }

  if (!isAuthConfigured()) {
    return {
      ...EMPTY,
      error: 'Alerts aren’t configured yet. Set NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY.',
    };
  }

  const supabase = await getSupabaseServerClient();
  if (!supabase) return { ...EMPTY, error: 'Alerts aren’t configured on this deployment.' };

  const { error } = await supabase.rpc('subscribe_to_alerts', {
    p_email: email,
    p_districts: districts,
    p_weekly_summary: weeklySummary,
    p_outbreak_only: outbreakOnly,
  });
  if (error) {
    // Detail goes to the server log, same reason sign-in's error handling
    // does this: the client only ever sees a message safe to show, never
    // the raw database error.
    console.error(`[alerts] subscription insert failed for ${email}: ${error.message}`);
    return { ...EMPTY, error: 'Could not save your subscription. Please try again shortly.' };
  }

  return { error: null, success: true };
}
