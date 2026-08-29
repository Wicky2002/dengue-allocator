# Compliance posture

This is an honest map, not a certificate. None of the three frameworks below
are something a codebase "has" — PDPA is a law, ISO/IEC 27001 is a certified
management system audited over time, and the ICTA/CERT baseline is a set of
published circulars this document does not reproduce or cite verbatim. What
follows is: what the platform's code actually does today that maps to each
one, and what is explicitly still missing — mostly organisational work no
merge can complete.

Written 2026-08. Keep it in sync with the code, or delete the claim.

## Sri Lanka PDPA No. 9 of 2022

The only PDPA-relevant document a codebase can *be* is the public transparency
notice — [`/privacy`](../web/src/app/privacy/page.tsx) — which states what is
collected, on what basis, and for how long. Everything below it is either a
technical control or an acknowledged gap.

| Requirement | Status | Where |
|---|---|---|
| Transparency notice (what's collected, legal basis, retention) | Done | `/privacy` |
| Data minimisation | Done by design | Staff accounts hold email, display name, role, district scope — nothing more. Public pages need no account. |
| Access control over personal data | Done | Supabase RLS restricts a `profiles` row to its own owner; `audit_log` reads restricted to `national_admin` (`supabase/audit_log.sql`) |
| Account lifecycle management | Done | Administration → Users & roles: create, edit and deactivate staff accounts (`web/src/app/admin/accounts/actions.ts`). Deactivation revokes access and ends any live session without deleting the account's history — see `supabase/account_management.sql`. |
| Accountability record (who accessed what) | Done | Append-only audit log, written by a `SECURITY DEFINER` function that stamps the caller's own session identity — see `supabase/audit_log.sql` |
| Retention schedule | Available, not yet enabled by default | `supabase/audit_log_retention.sql` defines a 365-day purge via `pg_cron` — run it once per deployment. `/privacy` reflects the same "not active until enabled" honesty. |
| **Designated point of contact for data-subject requests** | **Missing** | The notice points to "the Ministry through the footer" — there is no dedicated intake process or named officer yet. |
| Breach notification procedure | Done | `docs/incident-response.md` — containment steps, how to establish scope from the audit log, and when PDPA notification applies. Still depends on a named contact point (next row) to be more than "tell whoever is available." |
| **Data Protection Officer designation** | **Organisational** | Outside what a codebase can satisfy. |

## ISO/IEC 27001 (Annex A control mapping, informal)

Not a Statement of Applicability — a working note on which controls already
have a technical answer in this codebase, for whoever eventually writes one.

| Annex A area | What exists | Gap |
|---|---|---|
| A.5 Access control | RBAC (`src/lib/rbac.ts` / `dengue.platform.rbac`), Supabase RLS, permission checks at every data read | No periodic access review process; no offboarding checklist |
| A.8 Asset management | — | No formal asset/data inventory exists as a document |
| A.9 Cryptography | HTTPS assumed at the hosting layer; no in-app encryption-at-rest beyond Supabase's own | Not verified against a specific hosting provider's config |
| A.12 Operations security | Audit logging with a defined retention policy (`supabase/audit_log.sql`, `supabase/audit_log_retention.sql`); rate limiting on sign-in (`src/lib/rate-limit.ts`) | Rate limiter is in-process memory — correct for a single `next start` process, wrong the moment this runs as multiple instances (documented in the file itself). Retention purge depends on `pg_cron` being enabled on the Supabase project. |
| A.13 Communications security | CSP, HSTS, X-Frame-Options, etc. — **production builds only**, deliberately absent in `next dev` (see `src/middleware.ts`'s docstring for why) | Headers not yet verified against the actual hosting provider's edge/proxy layer |
| A.14 System acquisition/development | Provenance-tagged data model (`ProvenanceTier`) prevents conflating measured, modelled, and assumed figures at the type level; a full-codebase review (2026-08-29) found no privilege-escalation or cross-district leak in the RBAC/session/audit-log path | No formal SDLC/change-management policy document |
| A.16 Incident management | `docs/incident-response.md` | Not exercised — no drill or tabletop test has been run against it |
| A.17 Business continuity | Artifacts are static, pre-computed files, not a live database dependency for reads | No documented backup/restore procedure for the Supabase project itself |
| A.18 Compliance | This document | No legal review has been performed against PDPA or any sector-specific health-data rule |

## National CERT / ICTA guidelines

No specific circular is cited here because this session had no way to fetch
and verify the current published text — citing one without checking it would
be worse than not citing it. What's implemented follows the general baseline
any government-facing service is expected to meet:

- HTTPS-only posture asserted via HSTS in production (`src/middleware.ts`)
- No inline script execution without a per-request nonce in production (CSP)
- Government identification banner stating who operates the platform, on
  every page (`src/components/layout/GovBanner.tsx`)
- Trilingual (Sinhala/English/Tamil) public-facing content

**Before relying on this section for an actual compliance review**, get the
current ICTA/CERT circular from an authoritative source and check this list
against it directly — this document does not substitute for that.

## What this document is not

It is not a certification, an audit result, or a legal opinion. Treat every
"Done" above as "the code does this," not as "a lawyer or an auditor has
confirmed this is sufficient." The organisational items marked "Missing" are
the actual blockers to any of the three frameworks being satisfied in full,
and none of them are closed by writing more code.
