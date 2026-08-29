# Incident response: suspected data breach

A working runbook, not a compliance artefact for its own sake. If you are
reading this because something is actually happening, skip to **Step 1** —
the rest of the document can wait.

This exists because `docs/compliance.md` flagged its absence as a real gap:
Sri Lanka's PDPA expects a controller to be able to act on a breach promptly
and to notify the Data Protection Authority, and "we'll figure it out when it
happens" is not a plan.

## What counts as an incident here

Given what this platform actually holds (see `/privacy`), the realistic
scenarios are:

- A staff account credential is compromised (phished password, leaked
  session).
- The `audit_log` or `profiles` table is read or modified by someone who
  should not have access — e.g. a service-role key leaks, or an RLS policy
  regression exposes rows across accounts.
- The Supabase project itself is compromised (credential leak, unauthorised
  dashboard access).
- A dependency vulnerability is disclosed for something this app runs in
  production (Next.js, `@supabase/*`, or a direct dependency in
  `web/package.json`).

Public risk data (forecasts, district case counts) is not personal data, so
its exposure is an integrity/availability concern, not a PDPA-notifiable
breach on its own.

## Step 1 — contain

Do this before anything else, in roughly this order:

1. **Compromised staff account**: in the Supabase dashboard, Authentication →
   Users → find the account → revoke its sessions, then reset its password.
   This ends the session immediately; the account holder needs a new
   password before they can sign in again.
2. **Leaked service-role key**: Supabase dashboard → Project Settings → API
   → roll (regenerate) the `service_role` key. Every place that key is used —
   `secrets.toml` locally, any deployment environment variable, `.streamlit/secrets.toml`
   — needs the new value before those integrations work again; treat that as
   expected breakage during containment, not a new incident.
3. **Leaked anon key**: rolling it is more disruptive (every deployed
   instance of the app needs the new value simultaneously) and the anon key
   is meant to be public-facing by design — RLS is what actually protects
   data, not the key's secrecy. Only roll it if RLS itself is suspected to be
   broken; otherwise fix the RLS policy instead.
4. **Suspected RLS/policy regression**: pull the affected table's policies
   (`supabase/schema.sql`, `supabase/audit_log.sql`) and compare against what
   is actually live in the dashboard's Authentication → Policies view — a
   policy edited directly in the dashboard and never written back to these
   files is the most likely cause of a drift like this.
5. **Vulnerable dependency**: `npm audit` in `web/`, or check the advisory
   against the pinned version in `web/package.json`; patch and redeploy
   before doing anything else in this runbook.

## Step 2 — establish what actually happened

Before notifying anyone, know what you're notifying them about:

- Query `audit_log` for the affected account/time window (a `national_admin`
  account can do this from the Administration → Audit log tab, or directly
  via the Supabase SQL editor with the service-role key).
- Check Supabase's own project logs (Dashboard → Logs) for the same window —
  the application's own audit log only records the events listed in
  `src/lib/audit.ts`; it does not see, for example, a direct database
  connection made outside this application.
- Identify: which accounts, which tables/rows, what time window, and whether
  the exposed data was personal data under the PDPA (staff account details)
  or aggregate public data (which does not trigger notification).

## Step 3 — notify, if personal data was actually exposed

If the assessment in Step 2 confirms personal data (not aggregate public
data) was accessed by someone without authorisation:

- Notify the Ministry's own data protection contact point immediately — this
  runbook does not name one, because `docs/compliance.md` already flags that
  no one has been designated yet; that designation has to happen before this
  step is anything more than "tell whoever is available."
- Sri Lanka's PDPA requires notification to the Data Protection Authority.
  Get the current notification process and timeline from the Authority's own
  published guidance at the time of the incident — this document does not
  reproduce that process, since a stale copy of it here would be worse than
  pointing at the source.
- If staff accounts were affected, tell the affected account holders what
  happened and what to do (change password, watch for suspicious activity),
  in plain language.

## Step 4 — fix and record

- Fix the actual vulnerability, not just the symptom — if the cause was a
  code defect, that fix goes through the same review any other code change
  does.
- Write down what happened, when it was noticed, what was done, and when
  each step in this runbook was completed. That record is itself something a
  future audit or a Data Protection Authority inquiry will ask for.
- If the fix changes access control, retention, or logging behaviour, update
  `docs/compliance.md` and `/privacy` to match — the same rule the rest of
  this project holds itself to: those documents describe the system as it
  actually is, not as it was designed to be.

## What this runbook is not

It is not legal advice, and it does not replace the Ministry's own incident
response policy if a broader one exists elsewhere — this covers only what is
specific to operating this platform.
