'use server';

/**
 * Account management — the server actions behind Administration → Users & roles.
 *
 * Every action here starts the same way: re-derive the caller's identity from
 * their own session (`getSession()`, bound to their auth cookie) and check
 * `national_admin` before touching the service-role client at all. This is
 * not redundant with the page-level `can()` check in `admin/page.tsx` — a
 * Server Action is a directly callable endpoint on its own, independent of
 * which page happened to render the button that called it, so it has to
 * enforce its own authorisation rather than trust that some page already did.
 *
 * Every action also writes to the audit log before returning, using the same
 * `logAuditEvent` the rest of the app uses — account changes are exactly the
 * kind of privileged action that log exists to record.
 */

import { revalidatePath } from 'next/cache';

import { getSession } from '@/lib/session';
import { getSupabaseAdminClient } from '@/lib/supabase/admin';
import { logAuditEvent } from '@/lib/audit';
import { ROLES, isDistrictScopedRole, type RoleKey } from '@/lib/rbac';

export interface AccountActionState {
  error: string | null;
  success: string | null;
  /** Only set once, by createAccount, so the admin can copy it before it's gone. */
  temporaryPassword?: string;
}

const EMPTY: AccountActionState = { error: null, success: null };

// Every real role except `public` -- an account is never *created* as
// public, since a public "account" is just an unauthenticated visitor. The
// Postgres CHECK constraint on `profiles.role` is the actual backstop; this
// check exists so a bad value is rejected with a clear message instead of a
// raw database error.
const ASSIGNABLE_ROLES: Set<RoleKey> = new Set(
  ROLES.map((r) => r.key).filter((key) => key !== 'public'),
);

async function requireNationalAdmin(): Promise<{ error: string } | { email: string }> {
  const session = await getSession();
  if (session.principal.role !== 'national_admin') {
    return { error: 'Only a national administrator may manage accounts.' };
  }
  return { email: session.principal.email ?? 'unknown' };
}

/** A random temporary password the admin copies once and hands to the new account holder out of band. */
function generateTemporaryPassword(): string {
  const bytes = crypto.getRandomValues(new Uint8Array(18));
  return Buffer.from(bytes).toString('base64url');
}

export async function createAccount(
  _prev: AccountActionState,
  formData: FormData,
): Promise<AccountActionState> {
  const auth = await requireNationalAdmin();
  if ('error' in auth) return { ...EMPTY, error: auth.error };

  const admin = getSupabaseAdminClient();
  if (!admin) {
    return {
      ...EMPTY,
      error:
        'Account management is not configured on this deployment. Set SUPABASE_SERVICE_ROLE_KEY (see web/.env.example).',
    };
  }

  const email = String(formData.get('email') ?? '').trim();
  const displayName = String(formData.get('display_name') ?? '').trim();
  const role = String(formData.get('role') ?? '') as RoleKey;
  const districts = formData
    .getAll('districts')
    .map((value) => String(value))
    .filter(Boolean);
  const facility = String(formData.get('facility') ?? '').trim();

  if (!email || !displayName || !role) {
    return { ...EMPTY, error: 'Email, display name and role are required.' };
  }
  if (!ASSIGNABLE_ROLES.has(role)) {
    return { ...EMPTY, error: `"${role}" is not a role an account can be created with.` };
  }
  if (isDistrictScopedRole(role) && districts.length === 0) {
    return {
      ...EMPTY,
      error: `${role === 'hospital_staff' ? 'Hospital staff' : 'MOH officer'} accounts need at least one district — an account with this role and no district would otherwise see nothing, or (if that check were skipped) everything.`,
    };
  }

  const password = generateTemporaryPassword();

  const { data: created, error: createError } = await admin.auth.admin.createUser({
    email,
    password,
    email_confirm: true,
  });
  if (createError || !created.user) {
    return { ...EMPTY, error: `Could not create the account: ${createError?.message ?? 'unknown error'}` };
  }

  const { error: profileError } = await admin.from('profiles').insert({
    id: created.user.id,
    role,
    districts,
    facility: facility || null,
    display_name: displayName,
  });
  if (profileError) {
    // The auth user now exists with no profile row -- the same "orphaned
    // account" state schema.sql already warns about for the manual process.
    // Surfacing the exact error (rather than silently rolling back a user we
    // have no transaction spanning both tables to roll back safely) tells
    // the admin what to fix by hand.
    return {
      ...EMPTY,
      error: `Account created, but its profile could not be saved: ${profileError.message}. The auth user exists (${created.user.id}) — add its profile row manually, or delete the user and retry.`,
    };
  }

  await logAuditEvent('create_account', {
    path: '/admin',
    metadata: { created_email: email, role, districts },
  });

  revalidatePath('/admin');
  return {
    error: null,
    success: `Account created for ${email}.`,
    temporaryPassword: password,
  };
}

export async function updateAccount(
  _prev: AccountActionState,
  formData: FormData,
): Promise<AccountActionState> {
  const auth = await requireNationalAdmin();
  if ('error' in auth) return { ...EMPTY, error: auth.error };

  const admin = getSupabaseAdminClient();
  if (!admin) return { ...EMPTY, error: 'Account management is not configured on this deployment.' };

  const id = String(formData.get('id') ?? '');
  const displayName = String(formData.get('display_name') ?? '').trim();
  const role = String(formData.get('role') ?? '') as RoleKey;
  const districts = formData
    .getAll('districts')
    .map((value) => String(value))
    .filter(Boolean);
  const facility = String(formData.get('facility') ?? '').trim();

  if (!id || !displayName || !role) {
    return { ...EMPTY, error: 'Display name and role are required.' };
  }
  if (!ASSIGNABLE_ROLES.has(role)) {
    return { ...EMPTY, error: `"${role}" is not a role an account can be assigned.` };
  }
  if (isDistrictScopedRole(role) && districts.length === 0) {
    return { ...EMPTY, error: 'This role needs at least one district.' };
  }

  const { error } = await admin
    .from('profiles')
    .update({ role, districts, facility: facility || null, display_name: displayName })
    .eq('id', id);
  if (error) return { ...EMPTY, error: `Could not update the account: ${error.message}` };

  await logAuditEvent('update_account', {
    path: '/admin',
    metadata: { account_id: id, role, districts },
  });

  revalidatePath('/admin');
  return { error: null, success: 'Account updated.' };
}

export async function setAccountActive(
  id: string,
  active: boolean,
): Promise<AccountActionState> {
  const auth = await requireNationalAdmin();
  if ('error' in auth) return { ...EMPTY, error: auth.error };

  const admin = getSupabaseAdminClient();
  if (!admin) return { ...EMPTY, error: 'Account management is not configured on this deployment.' };

  const { error } = await admin.from('profiles').update({ active }).eq('id', id);
  if (error) return { ...EMPTY, error: `Could not update the account: ${error.message}` };

  // Revoking access also ends any session the account currently holds --
  // otherwise a deactivated account stays signed in until its token expires
  // on its own.
  if (!active) {
    await admin.auth.admin.signOut(id, 'global').catch(() => {
      // Best-effort: the profile flag is what every read-path in this app
      // actually checks (see src/lib/session.ts and dengue.platform.auth),
      // so access is revoked regardless of whether this call succeeds.
    });
  }

  await logAuditEvent(active ? 'reactivate_account' : 'deactivate_account', {
    path: '/admin',
    metadata: { account_id: id },
  });

  revalidatePath('/admin');
  return { error: null, success: active ? 'Account reactivated.' : 'Account deactivated.' };
}

export interface AccountRow {
  id: string;
  email: string;
  display_name: string;
  role: RoleKey;
  districts: string[];
  facility: string | null;
  active: boolean;
  created_at: string;
  last_sign_in_at: string | null;
}

export async function listAccounts(): Promise<AccountRow[] | { error: string }> {
  const auth = await requireNationalAdmin();
  if ('error' in auth) return { error: auth.error };

  const admin = getSupabaseAdminClient();
  if (!admin) return { error: 'Account management is not configured on this deployment.' };

  const [{ data: authUsers, error: authError }, { data: profiles, error: profileError }] =
    await Promise.all([
      admin.auth.admin.listUsers({ perPage: 1000 }),
      admin.from('profiles').select('*'),
    ]);
  if (authError) return { error: `Could not list accounts: ${authError.message}` };
  if (profileError) return { error: `Could not list account profiles: ${profileError.message}` };

  const profileById = new Map((profiles ?? []).map((row) => [row.id, row]));

  return (authUsers?.users ?? [])
    .map((user) => {
      const profile = profileById.get(user.id);
      if (!profile) return null;
      return {
        id: user.id,
        email: user.email ?? '(no email)',
        display_name: profile.display_name ?? user.email ?? 'Staff user',
        role: profile.role as RoleKey,
        districts: Array.isArray(profile.districts) ? profile.districts : [],
        facility: profile.facility ?? null,
        active: profile.active !== false,
        created_at: user.created_at,
        last_sign_in_at: user.last_sign_in_at ?? null,
      };
    })
    .filter((row): row is AccountRow => row !== null)
    .sort((a, b) => a.email.localeCompare(b.email));
}

export async function deleteAccount(id: string): Promise<AccountActionState> {
  const auth = await requireNationalAdmin();
  if ('error' in auth) return { ...EMPTY, error: auth.error };

  const admin = getSupabaseAdminClient();
  if (!admin) return { ...EMPTY, error: 'Account management is not configured on this deployment.' };

  // Deactivation (setAccountActive) is the recommended path — this exists
  // for the rarer case of removing an account created by mistake, and it is
  // genuinely irreversible: the auth user and its profile row are both gone,
  // unlike deactivation which keeps both intact.
  const { error } = await admin.auth.admin.deleteUser(id);
  if (error) return { ...EMPTY, error: `Could not delete the account: ${error.message}` };

  await logAuditEvent('delete_account', { path: '/admin', metadata: { account_id: id } });

  revalidatePath('/admin');
  return { error: null, success: 'Account deleted.' };
}
