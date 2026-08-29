'use server';

import { redirect } from 'next/navigation';

import { getSupabaseServerClient } from '@/lib/supabase/server';
import { logAuditEvent } from '@/lib/audit';

export interface ChangePasswordState {
  error: string | null;
}

const MIN_LENGTH = 8;

/**
 * Sets a real password in place of a temporary one, from the account's own
 * session -- no admin privilege needed or used, this is exactly what a
 * signed-in user is always allowed to do to their own account.
 *
 * `data: { must_change_password: false }` in the same `updateUser` call is
 * what actually lifts the redirect middleware applies to every route: that
 * flag lives in `user_metadata`, which `updateUser` merges rather than
 * replaces, so this clears it without touching anything else stored there.
 */
export async function changePassword(
  _prev: ChangePasswordState,
  formData: FormData,
): Promise<ChangePasswordState> {
  const password = String(formData.get('password') ?? '');
  const confirm = String(formData.get('confirm') ?? '');

  if (password.length < MIN_LENGTH) {
    return { error: 'changePassword.error.tooShort' };
  }
  if (password !== confirm) {
    return { error: 'changePassword.error.mismatch' };
  }

  const supabase = await getSupabaseServerClient();
  if (!supabase) return { error: 'changePassword.error.notSignedIn' };

  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) return { error: 'changePassword.error.notSignedIn' };

  const { error } = await supabase.auth.updateUser({
    password,
    data: { must_change_password: false },
  });
  if (error) {
    console.error(`[change-password] updateUser failed for ${user.email}: ${error.message}`);
    return { error: 'changePassword.error.generic' };
  }

  await logAuditEvent('password_changed');

  redirect('/national');
}
