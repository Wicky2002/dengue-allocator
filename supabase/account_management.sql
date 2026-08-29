-- DengueSentinel account management.
--
-- Run this once, after schema.sql, in the Supabase project's SQL editor. It
-- adds the one thing schema.sql's design deliberately left out: a way to
-- revoke an account's access without deleting its history.
--
-- Deactivation is a flag, not a role change. `profiles.role` stays whatever
-- it was -- Principal.__post_init__ (Python) and getSession() (TypeScript)
-- both already reject a scoped role with no districts, so overloading the
-- role column itself to mean "disabled" would mean inventing a fifth role
-- value that ripples into the permission matrix, the generated constants,
-- and both languages' Role enums for no real benefit. A boolean the two
-- session-loading code paths check first is smaller and cannot be confused
-- with an actual role.

alter table public.profiles add column if not exists active boolean not null default true;

comment on column public.profiles.active is
    'False means access is revoked. The row and its role/district scope stay '
    'intact for audit history -- deactivation is not deletion.';

-- No RLS policy change needed: the existing "read own row" policy already
-- lets a deactivated account see that its own row says `active = false`,
-- which is what lets the sign-in path show a clear message rather than a
-- generic failure. Listing and editing *other* accounts happens through the
-- admin panel's service-role client, which bypasses RLS by design -- the
-- authorisation check for that lives in the application layer (every admin
-- action re-verifies the caller is `national_admin` from their own session
-- before touching the service-role client at all), not in a policy here.
