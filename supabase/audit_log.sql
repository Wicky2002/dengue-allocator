-- DengueSentinel audit log.
--
-- Run this once, after schema.sql, in the Supabase project's SQL editor. It
-- creates an append-only record of privileged actions -- who did what, when,
-- and under which role/scope -- closing the gap the admin portal's "Audit
-- log" tab used to describe as simply absent.
--
-- Design decisions worth stating:
--
-- Writes go through a SECURITY DEFINER function, not a client INSERT policy.
-- A row is stamped with `auth.uid()` and the caller's *current* role/districts
-- looked up server-side inside the function -- never with values the client
-- supplies -- so a compromised or modified client cannot forge an entry
-- attributed to someone else, or claim a role/scope it doesn't currently hold.
--
-- Reads are restricted to national_admin. Nobody else, including the account
-- whose own actions are logged, can query this table through the anon/
-- authenticated key -- an audit log a subject can edit or read selectively
-- to check "am I being watched right now" is a weaker control than one they
-- cannot see at all.
--
-- No UPDATE or DELETE grant exists for any client role. The only way to
-- remove a row is a service-role operation run outside this application,
-- which is what "append-only" means in practice on Postgres + RLS.

create table if not exists public.audit_log (
    id bigint generated always as identity primary key,
    occurred_at timestamptz not null default now(),
    user_id uuid not null references auth.users (id) on delete set null,
    email text not null,
    role text not null,
    -- Snapshot of the account's district scope *at the time of the event* --
    -- deliberately not a join to the live `profiles` row, so a later scope
    -- change (or the account being deleted) never rewrites what an old log
    -- entry says access looked like when it happened.
    districts text[] not null default '{}',
    event_type text not null,
    path text,
    metadata jsonb not null default '{}'::jsonb
);

alter table public.audit_log enable row level security;

create index if not exists audit_log_occurred_at_idx on public.audit_log (occurred_at desc);

create policy "audit_log: national_admin reads all rows"
    on public.audit_log
    for select
    using (
        exists (
            select 1 from public.profiles
            where profiles.id = auth.uid() and profiles.role = 'national_admin'
        )
    );

-- No insert/update/delete policy for anon/authenticated -- see the
-- SECURITY DEFINER function below, which is the only write path.

create or replace function public.log_audit_event(
    p_event_type text,
    p_path text default null,
    p_metadata jsonb default '{}'::jsonb
)
returns void
language plpgsql
security definer
set search_path = public
as $$
declare
    v_email text;
    v_role text;
    v_districts text[];
begin
    if auth.uid() is null then
        raise exception 'log_audit_event: no authenticated user';
    end if;

    select coalesce(role, 'public'), coalesce(districts, '{}')
        into v_role, v_districts
        from public.profiles
        where id = auth.uid();

    select email into v_email from auth.users where id = auth.uid();

    insert into public.audit_log (user_id, email, role, districts, event_type, path, metadata)
    values (auth.uid(), coalesce(v_email, 'unknown'), coalesce(v_role, 'public'), coalesce(v_districts, '{}'), p_event_type, p_path, p_metadata);
end;
$$;

-- Only signed-in accounts may call this -- there is no anonymous logging path.
revoke all on function public.log_audit_event(text, text, jsonb) from public;
grant execute on function public.log_audit_event(text, text, jsonb) to authenticated;
