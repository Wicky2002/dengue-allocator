import type { Metadata } from 'next';

import { Container } from '@/components/ui/Container';
import { HorizonTabs } from '@/components/ui/HorizonTabs';
import { NoExportNotice } from '@/components/ui/NoExportNotice';
import { PageHeader } from '@/components/layout/PageHeader';
import { AccessNotice } from '@/components/auth/AccessNotice';
import { MohWorkspace } from '@/components/moh/MohWorkspace';
import { getSession } from '@/lib/session';
import { logAuditEvent } from '@/lib/audit';
import { can, filterToScope, role as roleDef, scopeLabel } from '@/lib/rbac';
import {
  getAllocation,
  getAllocationSummary,
  getAssessments,
  getBudgetSweep,
  getDistrictCapacity,
  getDistricts,
  getHorizons,
  getScenarios,
  hasData,
} from '@/lib/data';

/**
 * Never prerendered.
 *
 * What this page shows depends on who is asking. With Supabase configured the
 * `cookies()` read already forces this, but on a deployment with auth switched
 * off the page would otherwise be statically cached — and a cached shell is one
 * configuration change away from being served to a signed-in user.
 */
export const dynamic = 'force-dynamic';

export const metadata: Metadata = { title: 'District operations' };

export default async function MohPage({
  searchParams,
}: {
  searchParams: Promise<{ horizon?: string }>;
}) {
  const session = await getSession();
  if (!can(session.principal, 'view_district_operations')) {
    return (
      <AccessNotice
        portal="District operations"
        requiredRoles="MOH officers, regional health officers and national administrators"
        signedIn={session.signedIn}
        configurationError={session.configurationError}
      />
    );
  }
  await logAuditEvent('view_district_operations', { path: '/moh' });
  if (!(await hasData())) return <NoExportNotice />;

  const [districts, assessments, sweep, summary, scenarios, budget, horizons, capacity] =
    await Promise.all([
      getDistricts(),
      getAssessments(),
      getAllocation(),
      getAllocationSummary(),
      getScenarios(),
      getBudgetSweep(),
      getHorizons(),
      getDistrictCapacity(),
    ]);

  const requested = Number((await searchParams).horizon);
  const horizon = horizons.includes(requested) ? requested : (horizons[0] ?? 1);

  const districtNames = Object.fromEntries(districts.map((d) => [d.district_id, d.name]));
  const facilitiesById = new Map(capacity.map((row) => [row.district_id, row.n_facilities]));
  const hotspotDistricts = districts
    .map((d) => ({
      district_id: d.district_id,
      name: d.name,
      facilities: facilitiesById.get(d.district_id) ?? null,
      facilityPoor: d.facility_poor,
    }))
    .sort((a, b) => a.name.localeCompare(b.name));
  const inScope = session.principal.districts.length === 0 ? null : session.principal.districts;

  // Every district's assessment is passed to the hotspot panel, which chooses
  // what to display. That is a viewing choice, not a scope change -- the
  // allocation, plan and budget panels below stay filtered to the account's own
  // districts, and the panel labels anything outside them.
  const hotspots = assessments
    .filter((row) => row.horizon === horizon && row.audience === 'moh')
    .sort((a, b) => (b.incidence_per_100k ?? 0) - (a.incidence_per_100k ?? 0));
  const inScopeHotspots = filterToScope(hotspots, session.principal);

  return (
    <>
      <PageHeader
        crumbs={[{ label: 'District operations' }]}
        eyebrow={roleDef(session.principal.role).label}
        title="District operations"
        description="Where the teams go this week, what each deployment is expected to avert, and how the picture changes under a different climate or a different budget."
        meta={[
          { label: 'Scope', value: scopeLabel(session.principal) },
          { label: 'Horizon', value: `${horizon} weeks ahead` },
          { label: 'Districts in scope', value: String(inScopeHotspots.length) },
        ]}
      />

      <Container className="py-10">
        <div className="mb-8">
          <HorizonTabs horizons={horizons} active={horizon} basePath="/moh" />
        </div>

        <MohWorkspace
          assessments={hotspots}
          sweep={sweep}
          summary={summary}
          scenarios={filterToScope(scenarios, session.principal)}
          budget={budget}
          districtNames={districtNames}
          hotspotDistricts={hotspotDistricts}
          ownDistricts={session.principal.districts}
          inScope={inScope}
          canRunScenarios={can(session.principal, 'run_scenario')}
          canSeeBudget={can(session.principal, 'view_budget_optimiser')}
        />
      </Container>
    </>
  );
}
