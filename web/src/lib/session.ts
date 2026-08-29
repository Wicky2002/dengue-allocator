/**
 * Who is viewing, and what they may see.
 *
 * Resolves the Supabase session into the same `Principal` the Python engine
 * builds — role plus district scope, loaded from the `profiles` table whose
 * schema lives in `supabase/schema.sql`. The two must agree: a role string this
 * app does not recognise is treated as no access at all, never as a default.
 */

import { cache } from 'react';

import { getSupabaseServerClient, isAuthConfigured } from './supabase/server';
import { PUBLIC_PRINCIPAL, isDistrictScopedRole, type Principal, type RoleKey } from './rbac';
import constants from '@/generated/constants.json';

const KNOWN_ROLES = new Set(constants.roles.map((role) => role.key));

export interface SessionState {
  principal: Principal;
  signedIn: boolean;
  /** Set when an account exists but its profile row is missing or malformed. */
  configurationError: string | null;
}

/**
 * A development-only role override.
 *
 * The Streamlit app deliberately removed its free role switcher: browsing as an
 * MOH officer is real staff access, not a display preference. This is not that
 * switcher — it is an explicit, server-side, `NODE_ENV`-guarded escape hatch so
 * the staff portals can be reviewed on a checkout with no Supabase project. It
 * refuses to do anything in a production build.
 */
function devPrincipal(): Principal | null {
  const role = process.env.DENGUE_DEV_ROLE;
  if (!role || process.env.NODE_ENV === 'production') return null;
  if (!KNOWN_ROLES.has(role)) return null;

  const districts = (process.env.DENGUE_DEV_DISTRICTS ?? '')
    .split(',')
    .map((value) => value.trim())
    .filter(Boolean);

  return {
    role: role as RoleKey,
    displayName: 'Development preview',
    districts,
    email: 'dev@localhost',
  };
}

export const getSession = cache(async (): Promise<SessionState> => {
  const preview = devPrincipal();
  if (preview) {
    return { principal: preview, signedIn: true, configurationError: null };
  }

  const supabase = await getSupabaseServerClient();
  if (!supabase) {
    return { principal: PUBLIC_PRINCIPAL, signedIn: false, configurationError: null };
  }

  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) {
    return { principal: PUBLIC_PRINCIPAL, signedIn: false, configurationError: null };
  }

  const { data: rows } = await supabase
    .from('profiles')
    .select('*')
    .eq('id', user.id)
    .limit(1);

  const row = rows?.[0];
  if (!row) {
    return {
      principal: PUBLIC_PRINCIPAL,
      signedIn: true,
      configurationError: `No access profile is set up for ${user.email}. Ask an administrator to create one (see supabase/schema.sql) before this account can be used.`,
    };
  }
  if (!KNOWN_ROLES.has(row.role)) {
    return {
      principal: PUBLIC_PRINCIPAL,
      signedIn: true,
      configurationError: `Account ${user.email} has an unrecognised role "${row.role}".`,
    };
  }
  // `active` defaults true at the database level (supabase/account_management.sql);
  // `row.active !== false` only matters for a project that hasn't run that
  // migration yet, where the column is absent from the row entirely.
  if (row.active === false) {
    return {
      principal: PUBLIC_PRINCIPAL,
      signedIn: true,
      configurationError: `Account ${user.email} has been deactivated. Ask an administrator to reactivate it if this is unexpected.`,
    };
  }

  const districts: string[] = Array.isArray(row.districts) ? row.districts : [];
  // A scoped role with no districts would otherwise fall through to nationwide
  // scope -- the exact failure the Python Principal refuses to construct.
  if (isDistrictScopedRole(row.role as RoleKey) && districts.length === 0) {
    return {
      principal: PUBLIC_PRINCIPAL,
      signedIn: true,
      configurationError: `Account ${user.email} has role "${row.role}" but no districts assigned, so it has no scope to view.`,
    };
  }

  return {
    principal: {
      role: row.role as RoleKey,
      displayName: row.display_name || user.email || 'Staff user',
      districts,
      facility: row.facility ?? null,
      email: user.email ?? null,
    },
    signedIn: true,
    configurationError: null,
  };
});

export { isAuthConfigured };
