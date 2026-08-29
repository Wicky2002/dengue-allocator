-- Audit log retention.
--
-- Run this once, after audit_log.sql, in the Supabase project's SQL editor.
-- It closes the gap `docs/compliance.md` and `/privacy` both used to state
-- plainly: the audit log had no enforced deletion schedule and grew forever.
--
-- Default retention is 365 days. That is a judgement call, not a number PDPA
-- or any other framework hands you directly -- the Act's principle is "kept
-- no longer than necessary for the purpose," and a year is long enough to
-- investigate an access question raised well after the fact, short enough
-- that the log doesn't become an unbounded liability. Change the interval
-- below (and the `select cron.schedule(...)` call's argument) if your
-- ministry's own retention policy sets a different number -- there is no
-- other place in the codebase this needs to match, since the front end never
-- assumes a retention length itself.

create or replace function public.purge_audit_log(retention_days integer default 365)
returns integer
language plpgsql
security definer
set search_path = public
as $$
declare
    v_deleted integer;
begin
    delete from public.audit_log
    where occurred_at < now() - (retention_days || ' days')::interval;
    get diagnostics v_deleted = row_count;
    return v_deleted;
end;
$$;

-- No grant to anon or authenticated, unlike log_audit_event -- this is an
-- operator action, not something the application ever calls on a user's
-- behalf. It runs only via the scheduled job below, or by hand from the SQL
-- editor as a project owner.
revoke all on function public.purge_audit_log(integer) from public;

-- Schedules the purge for 03:00 UTC daily, via pg_cron.
--
-- If this errors with `schema "cron" does not exist`, the extension isn't
-- enabled on this project yet: Dashboard -> Database -> Extensions -> enable
-- "pg_cron" -- then re-run just the block below (the function above is
-- already created and doesn't need repeating).
--
-- Without pg_cron (some project tiers don't offer it), there is no
-- in-database scheduler available, and the fallback is to run
-- `select public.purge_audit_log(365);` by hand on whatever cadence you
-- choose, or trigger it from an external scheduler (e.g. a GitHub Actions
-- cron workflow calling this function via the SQL editor's API) -- either
-- way, this file's function is the thing being called; only the trigger
-- differs.
select cron.schedule(
    'purge-audit-log-daily',
    '0 3 * * *',
    $$select public.purge_audit_log(365)$$
);
