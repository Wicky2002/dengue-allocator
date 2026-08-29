'use server';

import { redirect } from 'next/navigation';
import { headers } from 'next/headers';

import { getSupabaseServerClient, isAuthConfigured } from '@/lib/supabase/server';
import { logAuditEvent } from '@/lib/audit';
import { isRateLimited } from '@/lib/rate-limit';

export interface SignInState {
  error: string | null;
}

// Five attempts per five minutes, tracked separately by email and by client
// IP: an attacker rotating IPs against one account is still capped by the
// email bucket, and one rotating through many accounts from a small number of
// addresses is still capped by the IP bucket.
const MAX_ATTEMPTS = 5;
const WINDOW_MS = 5 * 60 * 1000;

async function clientIp(): Promise<string> {
  const h = await headers();
  // The first hop in X-Forwarded-For is the client as seen by the nearest
  // proxy; behind more than one proxy this is only as trustworthy as that
  // chain, which is the normal caveat for this header everywhere it's used.
  const forwarded = h.get('x-forwarded-for');
  if (forwarded) return forwarded.split(',')[0].trim();
  return h.get('x-real-ip') ?? 'unknown';
}

/**
 * Staff sign-in.
 *
 * Public risk information needs no account, so this is not a gate on the
 * platform — it is the boundary between public information and real staff
 * access. There is no demo role switcher behind it.
 */
export async function signIn(_prev: SignInState, formData: FormData): Promise<SignInState> {
  if (!isAuthConfigured()) {
    return {
      error:
        'Sign-in is not configured on this deployment. Set NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY, and create the profiles table from supabase/schema.sql.',
    };
  }

  const email = String(formData.get('email') ?? '').trim();
  const password = String(formData.get('password') ?? '');
  if (!email || !password) {
    return { error: 'Enter your email address and password.' };
  }

  const ip = await clientIp();
  // Checked before calling Supabase at all: a request that's already over
  // limit gets the generic rejection without spending an auth attempt against
  // the project, and without giving a script anything to distinguish from a
  // wrong password.
  if (
    (await isRateLimited(`signin:email:${email.toLowerCase()}`, MAX_ATTEMPTS, WINDOW_MS)) ||
    (await isRateLimited(`signin:ip:${ip}`, MAX_ATTEMPTS, WINDOW_MS))
  ) {
    console.error(`[auth] rate-limited sign-in attempt for ${email} from ${ip}`);
    return { error: 'Too many attempts. Wait a few minutes and try again.' };
  }

  const supabase = await getSupabaseServerClient();
  if (!supabase) return { error: 'Sign-in is not configured on this deployment.' };

  const { error } = await supabase.auth.signInWithPassword({ email, password });
  if (error) {
    // The viewer is told only that the attempt failed. Distinguishing "no such
    // account" from "wrong password" tells an attacker which addresses are
    // staff accounts -- so the real reason goes to the server log, where an
    // operator can read it and a visitor cannot.
    console.error(
      `[auth] sign-in failed for ${email}: ${error.message} (status ${error.status ?? 'n/a'}, code ${error.code ?? 'n/a'})`,
    );
    return { error: 'Those credentials were not accepted. Check your email and password.' };
  }

  // Logged after the sign-in itself succeeds, using the session it just
  // created -- log_audit_event reads the caller's own identity server-side,
  // so this has to run once a session actually exists.
  await logAuditEvent('sign_in');

  redirect('/national');
}

export async function signOut(): Promise<void> {
  const supabase = await getSupabaseServerClient();
  // Logged before signing out, while the session used to attribute the event
  // is still live.
  await logAuditEvent('sign_out');
  await supabase?.auth.signOut();
  redirect('/');
}
