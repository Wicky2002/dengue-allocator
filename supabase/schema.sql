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
