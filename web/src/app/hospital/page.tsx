import type { Metadata } from 'next';

import { Container } from '@/components/ui/Container';
import { Callout } from '@/components/ui/Callout';
import { HorizonTabs } from '@/components/ui/HorizonTabs';
import { SectionHeading } from '@/components/ui/SectionHeading';
import { NoExportNotice } from '@/components/ui/NoExportNotice';
import { PageHeader } from '@/components/layout/PageHeader';
import { AccessNotice } from '@/components/auth/AccessNotice';
import { RecommendationList } from '@/components/ui/RecommendationList';
import { ReadinessWorkspace, type ReadinessInput } from '@/components/hospital/ReadinessWorkspace';
import { DistrictPreview } from '@/components/hospital/DistrictPreview';
import { FacilityMap } from '@/components/charts/FacilityMap';
import { getSession } from '@/lib/session';
import { logAuditEvent } from '@/lib/audit';
import { can, filterToScope, scopeLabel, role as roleDef } from '@/lib/rbac';
import {
  getAssessments,
  getDistrictCapacity,
  getDistrictRisk,
  getDistricts,
  getFacilities,
  getHorizons,
  hasData,
} from '@/lib/data';
import { rankDistricts } from '@/lib/selectors';

/**
 * Never prerendered.
 *
 * What this page shows depends on who is asking. With Supabase configured the
 * `cookies()` read already forces this, but on a deployment with auth switched
 * off the page would otherwise be statically cached — and a cached shell is one
 * configuration change away from being served to a signed-in user.
 */
export const dynamic = 'force-dynamic';

export const metadata: Metadata = { title: 'Hospital readiness' };

export default async function HospitalPage({
  searchParams,
}: {
  searchParams: Promise<{ horizon?: string }>;
}) {
  const session = await getSession();
  if (!can(session.principal, 'view_hospital_readiness')) {
    return (
      <AccessNotice
        portal="Hospital readiness"
        requiredRoles="hospital staff, MOH officers and national administrators"
        signedIn={session.signedIn}
        configurationError={session.configurationError}
      />
    );
  }
  await logAuditEvent('view_hospital_readiness', { path: '/hospital' });
  if (!(await hasData())) return <NoExportNotice />;

  // The geometry is deliberately not loaded here: FacilityMap fetches the
  // static copy client-side, which keeps ~110 KB of outlines out of this
  // page's server payload and lets the browser cache one copy across pages.
  const [risk, districts, capacity, facilities, horizons, assessments] = await Promise.all([
    getDistrictRisk(),
    getDistricts(),
    getDistrictCapacity(),
    getFacilities(),
    getHorizons(),
    getAssessments(),
  ]);

  const requested = Number((await searchParams).horizon);
  const horizon = horizons.includes(requested) ? requested : (horizons[0] ?? 1);

  const ranked = rankDistricts(risk, districts, horizon);
  // Scope is applied here, at the read, rather than inside a component: a
  // filter that lives in the rendering layer is one refactor away from being
  // dropped, and dropping it leaks another region's data.
  const inScope = filterToScope(ranked, session.principal);
  const capacityById = new Map(capacity.map((row) => [row.district_id, row]));
  const districtById = new Map(districts.map((row) => [row.district_id, row]));

  const toInput = (row: (typeof ranked)[number]): ReadinessInput => {
    const cap = capacityById.get(row.district_id);
    return {
      district_id: row.district_id,
      district: row.name,
      forecastCases: row.median ?? 0,
      forecastUpper: row.upper,
      estimatedBeds: cap?.estimated_beds ?? 0,
      nHospitals: cap?.n_hospitals ?? 0,
      nFacilities: cap?.n_facilities ?? 0,
      population: districtById.get(row.district_id)?.population ?? cap?.population ?? 0,
    };
  };

  const inputs: ReadinessInput[] = inScope.map(toInput);

  // Districts the account is not scoped to, offered as a labelled preview.
  // Nothing here widens what the account can act on -- see DistrictPreview.
  const previewCandidates: ReadinessInput[] =
    session.principal.districts.length === 0
      ? []
      : ranked
          .filter((row) => !session.principal.districts.includes(row.district_id))
          .map(toInput)
          .sort((a, b) => a.district.localeCompare(b.district));

  const clinicalAdvice = assessments.filter(
    (row) =>
      row.horizon === horizon &&
      row.audience === 'hospital' &&
      (session.principal.districts.length === 0
        ? row.district_id === inScope[0]?.district_id
        : session.principal.districts.includes(row.district_id)),
  );

  const scopedFacilities =
    session.principal.districts.length === 0
      ? facilities
      : facilities.filter(
          (f) => f.district_id != null && session.principal.districts.includes(f.district_id),
        );
  const bedsTagged = scopedFacilities.filter((f) => f.beds_tagged != null).length;

  return (
    <>
      <PageHeader
        crumbs={[{ label: 'Hospital readiness' }]}
        eyebrow={roleDef(session.principal.role).label}
        title="Hospital readiness"
        description="What the forecast implies for admissions, beds and supplies — and, explicitly, what this platform cannot tell you because no one publishes it."
        meta={[
          { label: 'Scope', value: scopeLabel(session.principal) },
          { label: 'Horizon', value: `${horizon} weeks ahead` },
          { label: 'Districts in view', value: String(inScope.length) },
        ]}
      />

      <Container className="py-10">
        <div className="mb-8">
          <HorizonTabs horizons={horizons} active={horizon} basePath="/hospital" />
        </div>

        <ReadinessWorkspace inputs={inputs} horizon={horizon} />

        {previewCandidates.length > 0 ? (
          <div className="mt-8">
            <DistrictPreview
              candidates={previewCandidates}
              facilities={facilities.map((f) => ({
                id: String(f.osm_id),
                name: f.name,
                type: f.facility_type,
                lat: f.lat,
                lon: f.lon,
                district_id: f.district_id,
              }))}
            />
          </div>
        ) : null}

        {clinicalAdvice.length > 0 ? (
          <section className="mt-12">
            <SectionHeading
              eyebrow="Clinical response"
              title={`Recommended actions${
                clinicalAdvice.length === 1 ? ` for ${clinicalAdvice[0].district}` : ''
              }`}
              description="Generated from the district's risk band and its forecast trajectory — the same engine that drives the public advice, at a clinical audience."
            />
            <div className="grid gap-6 lg:grid-cols-2">
              {clinicalAdvice.slice(0, 2).map((item) => (
                <div key={item.district_id}>
                  {clinicalAdvice.length > 1 ? (
                    <h3 className="text-h3 mb-3">{item.district}</h3>
                  ) : null}
                  <RecommendationList items={item.recommendations} />
                </div>
              ))}
            </div>
          </section>
        ) : null}

        <section className="mt-12">
          <SectionHeading
            eyebrow="Facilities"
            title="Where the hospitals are"
            description={`${scopedFacilities.length.toLocaleString()} health facilities from OpenStreetMap (ODbL). Locations are real; bed counts are not tagged for Sri Lanka, so per-facility capacity cannot be shown.`}
          />
          <FacilityMap
            facilities={scopedFacilities.map((f) => ({
              id: String(f.osm_id),
              name: f.name,
              type: f.facility_type,
              lat: f.lat,
              lon: f.lon,
              district_id: f.district_id,
            }))}
          />
          <Callout tone="info" className="mt-4">
            {bedsTagged} of {scopedFacilities.length.toLocaleString()} facilities carry a bed
            count in OpenStreetMap, so facility-level capacity is not shown at all rather than
            being filled in with a national average.
          </Callout>
        </section>
      </Container>
    </>
  );
}
