import type { Metadata } from 'next';

import { Container } from '@/components/ui/Container';
import { Callout } from '@/components/ui/Callout';
import { NoExportNotice } from '@/components/ui/NoExportNotice';
import { PageHeader } from '@/components/layout/PageHeader';
import { AccessNotice } from '@/components/auth/AccessNotice';
import { AdminWorkspace } from '@/components/admin/AdminWorkspace';
import { getSession } from '@/lib/session';
import { getRecentAuditEvents, hasAuditLog, logAuditEvent } from '@/lib/audit';
import { can, role as roleDef, scopeLabel } from '@/lib/rbac';
import { readJson, getMeta, getScores, getDistricts, hasData } from '@/lib/data';
import { listAccounts } from '@/app/admin/accounts/actions';

/**
 * Never prerendered.
 *
 * What this page shows depends on who is asking. With Supabase configured the
 * `cookies()` read already forces this, but on a deployment with auth switched
 * off the page would otherwise be statically cached — and a cached shell is one
 * configuration change away from being served to a signed-in user.
 */
export const dynamic = 'force-dynamic';

export const metadata: Metadata = { title: 'Administration' };

/** Artifacts the platform expects to find, in the order the pipeline writes them. */
const EXPECTED = [
  'panel_recent',
  'forecasts',
  'district_risk',
  'effect_table',
  'allocation_sweep',
  'allocation_summary',
  'sei_sir_params',
  'hospital_readiness',
  'district_capacity',
  'health_facilities',
  'scenarios',
  'budget_sweep',
  'scores',
  'predictions_history',
  'assessments',
];

export default async function AdminPage() {
  const session = await getSession();
  if (!can(session.principal, 'view_national_operations')) {
    return (
      <AccessNotice
        portalKey="nav.admin"
        requiredRolesKey="notice.rolesAdmin"
        signedIn={session.signedIn}
        configurationError={session.configurationError}
      />
    );
  }
  await logAuditEvent('view_national_operations', { path: '/admin' });
  if (!(await hasData())) return <NoExportNotice />;

  const [meta, scores, auditLogAvailable] = await Promise.all([
    getMeta(),
    getScores(),
    hasAuditLog(),
  ]);
  const artifacts = await Promise.all(
    EXPECTED.map(async (name) => ({ name, rows: (await readJson(name)).length })),
  );
  // Only fetched once the table is known to exist -- RLS already restricts
  // this to national_admin accounts, but there is no point querying at all
  // on a deployment that hasn't run supabase/audit_log.sql yet.
  const auditEvents = auditLogAvailable ? await getRecentAuditEvents() : [];

  // listAccounts re-checks national_admin itself (see accounts/actions.ts) --
  // this call is not the authorisation boundary, the page's own `can()` check
  // above and the action's internal one both are. It has no data dependency
  // on the district registry, so the two run together rather than in series.
  const [districts, accounts] = await Promise.all([getDistricts(), listAccounts()]);

  return (
    <>
      <PageHeader
        crumbs={[{ label: 'Administration' }]}
        eyebrow={roleDef(session.principal.role).label}
        title="System administration"
        description="Nationwide oversight, configuration and provenance — including what this platform deliberately does not show."
        meta={[
          { label: 'Scope', value: scopeLabel(session.principal) },
          { label: 'Signed in as', value: session.principal.displayName },
          { label: 'Artifacts', value: `${artifacts.filter((a) => a.rows > 0).length}/${artifacts.length}` },
        ]}
      />

      <Container className="py-10">
        {meta?.is_synthetic ? (
          <Callout tone="simulated" title="This run used the synthetic panel" className="mb-8">
            Everything below describes a simulated pipeline run. Run{' '}
            <code className="font-mono text-xs">make pipeline-real &amp;&amp; make export-web</code>{' '}
            before treating any of it as operational.
          </Callout>
        ) : null}

        <AdminWorkspace
          meta={meta}
          artifacts={artifacts}
          scores={scores}
          auditLogAvailable={auditLogAvailable}
          auditEvents={auditEvents}
          districts={districts}
          accounts={accounts}
        />
      </Container>
    </>
  );
}
