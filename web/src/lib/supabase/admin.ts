import 'server-only';

import { createClient, type SupabaseClient } from '@supabase/supabase-js';

/**
 * A Supabase client authenticated as `service_role`.
 *
 * This bypasses every Row Level Security policy in the project, including
 * the one restricting `profiles` reads to a caller's own row. It exists only
 * for the account-management actions in `src/app/admin/accounts/actions.ts`,
 * and it does the two things nothing else in this app can: create an
 * auth.users row with `auth.admin.createUser`, and list every account for
 * the admin panel's table.
 *
 * `import 'server-only'` makes it a build error to import this module from
 * any file that could end up in a client bundle -- not just a lint warning,
 * a failed build. The `SUPABASE_SERVICE_ROLE_KEY` environment variable this
 * reads deliberately carries no `NEXT_PUBLIC_` prefix (see `.env.example`):
 * that prefix is what tells Next to inline a value into the JavaScript
 * shipped to every visitor's browser, and this key must never be in that
 * bundle.
 *
 * Every caller of this module is responsible for checking, itself, that the
 * request is actually from a `national_admin` session before doing anything
 * with the client this returns -- this function does not and cannot check
 * that for you, the same way `getSupabaseServerClient()` doesn't decide who
 * may sign in.
 */
export function getSupabaseAdminClient(): SupabaseClient | null {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const key = process.env.SUPABASE_SERVICE_ROLE_KEY;
  if (!url || !key) return null;

  return createClient(url, key, {
    auth: {
      autoRefreshToken: false,
      persistSession: false,
    },
  });
}
