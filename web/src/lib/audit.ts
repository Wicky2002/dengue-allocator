/**
 * The append-only audit log.
 *
 * Writes go through `log_audit_event`, a SECURITY DEFINER Postgres function
 * (see `supabase/audit_log.sql`) that stamps a row with the caller's *current*
 * session identity and role, looked up server-side -- never with a value this
 * code supplies -- so a bug here cannot forge an entry attributed to someone
 * else. Reads are restricted by the same migration to `national_admin`
 * accounts; everyone else's call simply returns no rows.
 *
 * Both functions fail silently rather than throwing: a page that renders
 * without a log line is a smaller problem than a page that errors out because
 * the audit table hasn't been created yet on this deployment. `hasAuditLog()`
 * is how the admin portal tells "no events yet" apart from "not set up".
 */

import { cache } from 'react';

import { getSupabaseServerClient } from './supabase/server';

export interface AuditEvent {
  id: number;
  occurred_at: string;
  email: string;
  role: string;
  districts: string[];
  event_type: string;
  path: string | null;
  metadata: Record<string, unknown>;
}

/**
 * Record one privileged action against the signed-in user's own identity.
 *
 * Call this from a Server Component or Server Action, after `getSession()`
 * has already confirmed who is asking -- it re-derives that identity from the
 * database rather than trusting whatever the caller passes in.
 */
export async function logAuditEvent(
  eventType: string,
  options: { path?: string; metadata?: Record<string, unknown> } = {},
): Promise<void> {
  try {
    const supabase = await getSupabaseServerClient();
    if (!supabase) return;
    await supabase.rpc('log_audit_event', {
      p_event_type: eventType,
      p_path: options.path ?? null,
      p_metadata: options.metadata ?? {},
    });
  } catch {
    // Missing table/function on a deployment that hasn't run
    // supabase/audit_log.sql yet, or no active session -- either way, the
    // action the log line was meant to describe has already happened and
    // must not be blocked by its own audit trail failing to write.
  }
}

/** The most recent audit events, newest first. Empty if none, unset up, or unauthorised. */
export const getRecentAuditEvents = cache(async (limit = 200): Promise<AuditEvent[]> => {
  try {
    const supabase = await getSupabaseServerClient();
    if (!supabase) return [];
    const { data, error } = await supabase
      .from('audit_log')
      .select('id, occurred_at, email, role, districts, event_type, path, metadata')
      .order('occurred_at', { ascending: false })
      .limit(limit);
    if (error || !data) return [];
    return data as AuditEvent[];
  } catch {
    return [];
  }
});

/** Whether the audit_log table is reachable at all, to distinguish "empty" from "not set up". */
export const hasAuditLog = cache(async (): Promise<boolean> => {
  try {
    const supabase = await getSupabaseServerClient();
    if (!supabase) return false;
    // Deliberately not `{ head: true, count: 'exact' }`: PostgREST's response
    // to a HEAD request against a table that doesn't exist came back as a
    // bare 204 with no error, in testing against this exact project, rather
    // than the 404/PGRST205 a normal GET correctly surfaces -- which made this
    // check silently report "available" against a project that had never run
    // supabase/audit_log.sql. A plain `select().limit(1)` costs one extra row
    // fetch but gets the existence check right.
    const { error } = await supabase.from('audit_log').select('id').limit(1);
    return !error;
  } catch {
    return false;
  }
});
