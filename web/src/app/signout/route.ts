import { NextResponse } from 'next/server';

import { getSupabaseServerClient } from '@/lib/supabase/server';
import { logAuditEvent } from '@/lib/audit';

/** Sign out and return to the public landing page. */
export async function GET(request: Request) {
  const supabase = await getSupabaseServerClient();
  // Logged before signing out, while the session used to attribute the event
  // is still live -- this is the route the header's "Sign out" link actually
  // points to, separate from the sign-in form's own signOut action.
  await logAuditEvent('sign_out');
  await supabase?.auth.signOut();
  return NextResponse.redirect(new URL('/', request.url));
}
