-- DengueSentinel access-control schema.
--
-- Run this once in the Supabase project's SQL editor (Dashboard -> SQL
-- Editor -> New query -> paste -> Run). It creates the one table
-- src/dengue/platform/auth.py reads: `profiles`, one row per real account,
-- mirroring the fields on dengue.platform.rbac.Principal (role, districts,
-- facility, display_name).
--
-- There is no self-signup here. Every non-public role is scoped staff
-- access, so accounts are created by an administrator, not by users
-- registering themselves. To add someone:
--   1. Dashboard -> Authentication -> Users -> Add user (set their email +
--      a temporary password).
--   2. Copy the new user's UUID.
--   3. Run an INSERT into `profiles` below with that UUID.

create table if not exists public.profiles (
    id uuid primary key references auth.users (id) on delete cascade,
    -- Matches dengue.platform.rbac.Role's values exactly.
    role text not null check (
        role in ('public', 'hospital_staff', 'moh_officer', 'national_admin')
    ),
    -- District slugs from src/dengue/config.py's DISTRICTS registry, e.g.
    -- 'colombo', 'gampaha', 'mannar'. Empty/null is only valid for
    -- national_admin -- Principal.__post_init__ (rbac.py) rejects an empty
    -- list for hospital_staff/moh_officer at load time, not silently
    -- granting nationwide access.
    districts text[] not null default '{}',
    facility text,
    display_name text not null,
    created_at timestamptz not null default now()
);

alter table public.profiles enable row level security;

-- Each account may read only its own profile row -- the anon key used by
-- the app can never enumerate or read anyone else's role/scope, even
-- though the query itself is unfiltered in auth.py (RLS does the filtering
-- at the database level, not the application level).
create policy "profiles: read own row"
    on public.profiles
    for select
    using (auth.uid() = id);

-- No insert/update/delete policy for anon/authenticated on purpose:
-- accounts are provisioned by an administrator via the Dashboard (which
-- uses the service-role key, bypassing RLS), not by end users.

-- ---------------------------------------------------------------------
-- Example seed rows -- replace the UUIDs with real ones from step 2 above,
-- then uncomment and run.
-- ---------------------------------------------------------------------
-- insert into public.profiles (id, role, districts, facility, display_name) values
--     ('00000000-0000-0000-0000-000000000001', 'hospital_staff', array['colombo'], 'National Hospital, Colombo', 'Dr. A'),
--     ('00000000-0000-0000-0000-000000000002', 'hospital_staff', array['colombo'], 'National Hospital, Colombo', 'Dr. B'),
--     ('00000000-0000-0000-0000-000000000003', 'moh_officer', array['gampaha','colombo'], null, 'RDHS Gampaha (demo)'),
--     ('00000000-0000-0000-0000-000000000004', 'national_admin', '{}', null, 'MoH administrator (demo)');

-- ---------------------------------------------------------------------
-- Public alert subscriptions -- src/dengue/platform/alerts.py reads/writes
-- this table. Unlike `profiles`, this one IS meant to be written by
-- anonymous public visitors: the public portal has no login, on purpose
-- (see streamlit_app.py), so "subscribe with your email" has to work
-- without an account.
-- ---------------------------------------------------------------------

create table if not exists public.alert_subscriptions (
    id uuid primary key default gen_random_uuid(),
    email text not null check (email ~ '^[^@\s]+@[^@\s]+\.[^@\s]+$'),
    -- District slugs from src/dengue/config.py's DISTRICTS registry.
    districts text[] not null check (cardinality(districts) > 0),
    weekly_summary boolean not null default true,
    outbreak_only boolean not null default false,
    created_at timestamptz not null default now()
);

alter table public.alert_subscriptions enable row level security;

-- Anyone (including an anonymous public visitor) may create a subscription
-- -- that is the entire point of this table -- but no select/update/delete
-- policy exists for anon/authenticated, so a submitted row can never be
-- read back, enumerated, or edited from the client. Changing your
-- preferences means submitting again: dengue.platform.alerts.
-- fetch_active_subscriptions() reads the most recent row per email, so a
-- later submission supersedes an earlier one without needing update
-- permission at all.
create policy "alert_subscriptions: anyone may subscribe"
    on public.alert_subscriptions
    for insert
    to anon, authenticated
    with check (true);

-- The weekly sender (dengue.platform.alerts, run from GitHub Actions) reads
-- this table with the service-role key, which bypasses RLS entirely -- the
-- same privilege model `profiles`' seeding already relies on. No read
-- policy is granted to anon/authenticated here either.

-- ---------------------------------------------------------------------
-- subscribe_to_alerts -- the actual path the app writes through.
--
-- The INSERT policy above is correct (INSERT, {anon,authenticated},
-- with check true) and works on a normal Supabase project. Some projects
-- -- notably ones provisioned under Supabase's newer publishable/secret API
-- key rollout -- have been seen rejecting a plain anon-key table insert
-- with "new row violates row-level security policy" even though the
-- policy is exactly right, which looks like a role-resolution issue on
-- Supabase's side rather than anything wrong with this schema. A
-- SECURITY DEFINER function sidesteps it entirely: it runs as its
-- *owner* (whoever executes this CREATE, typically an elevated role),
-- so the insert never has to pass through anon-role RLS resolution at
-- all -- only the EXECUTE grant below does, which is a much simpler
-- permission check.
-- ---------------------------------------------------------------------

create or replace function public.subscribe_to_alerts(
    p_email text,
    p_districts text[],
    p_weekly_summary boolean,
    p_outbreak_only boolean
) returns void
language sql
security definer
set search_path = public
as $$
    insert into public.alert_subscriptions (email, districts, weekly_summary, outbreak_only)
    values (p_email, p_districts, p_weekly_summary, p_outbreak_only);
$$;

-- The table's own CHECK constraints (valid email shape, at least one
-- district) still apply here -- SECURITY DEFINER changes whose
-- privileges the insert runs with, not which constraints the row has to
-- satisfy.
grant execute on function public.subscribe_to_alerts(text, text[], boolean, boolean)
    to anon, authenticated;
