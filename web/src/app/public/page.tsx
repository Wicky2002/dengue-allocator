import type { Metadata } from 'next';
import { Suspense } from 'react';
import {
  PhoneIcon,
  ShieldExclamationIcon,
  BeakerIcon,
  HomeModernIcon,
} from '@heroicons/react/24/outline';

import { Container } from '@/components/ui/Container';
import { Card } from '@/components/ui/Card';
import { Callout } from '@/components/ui/Callout';
import { StatTile } from '@/components/ui/StatTile';
import { RiskPill } from '@/components/ui/RiskPill';
import { SectionHeading } from '@/components/ui/SectionHeading';
import { HorizonTabs } from '@/components/ui/HorizonTabs';
import { DistrictPicker } from '@/components/ui/DistrictPicker';
import { RecommendationList } from '@/components/ui/RecommendationList';
import { NoExportNotice } from '@/components/ui/NoExportNotice';
import { PageHeader } from '@/components/layout/PageHeader';
import { ChartFrame } from '@/components/charts/ChartFrame';
import { DistrictCases, DistrictRainfall } from '@/components/charts/DistrictHistory';
import { MythVsFact } from '@/components/public/MythVsFact';
import { AlertPreferences } from '@/components/public/AlertPreferences';
import { num, signedPct } from '@/lib/format';
import {
  getAssessment,
  getDistrictRisk,
  getDistricts,
  getFacilities,
  getHorizons,
  getPanel,
  hasData,
} from '@/lib/data';
import { districtTrend, rankDistricts } from '@/lib/selectors';
import { getT } from '@/lib/i18n/server';

export const metadata: Metadata = {
  title: 'Dengue risk where you live',
  description:
    'Check the dengue forecast for your district in Sri Lanka, what it means, and what to do about it.',
};

export default async function PublicPage({
  searchParams,
}: {
  searchParams: Promise<{ district?: string; horizon?: string }>;
}) {
  if (!(await hasData())) return <NoExportNotice />;

  const t = await getT();
  const params = await searchParams;
  const [districts, risk, panel, facilities, horizons] = await Promise.all([
    getDistricts(),
    getDistrictRisk(),
    getPanel(),
    getFacilities(),
    getHorizons(),
  ]);

  // This is the one page on the platform that needs no account -- it has to
  // degrade to a clear message rather than crash if the district registry
  // itself is ever empty, the same way every other panel here explains a
  // missing artifact instead of failing on it.
  if (districts.length === 0) return <NoExportNotice />;

  const requestedHorizon = Number(params.horizon);
  const horizon = horizons.includes(requestedHorizon) ? requestedHorizon : (horizons[0] ?? 1);

  const ranked = rankDistricts(risk, districts, horizon);
  const known = new Set(districts.map((d) => d.district_id));
  const districtId =
    params.district && known.has(params.district) ? params.district : districts[0].district_id;

  const district = districts.find((d) => d.district_id === districtId)!;
  const assessment = await getAssessment(districtId, horizon, 'public');
  const history = districtTrend(panel, districtId, 78);
  const rank = ranked.find((row) => row.district_id === districtId);
  const localFacilities = facilities.filter((f) => f.district_id === districtId);
  const hospitals = localFacilities.filter((f) => f.facility_type === 'hospital');

  const sortedDistricts = [...districts].sort((a, b) => a.name.localeCompare(b.name));

  return (
    <>
      <PageHeader
        crumbs={[{ label: t('crumb.public') }]}
        eyebrow={t('public.eyebrow')}
        title={t('public.title')}
        description={t('public.lede')}
      />

      <Container className="py-10">
        <div className="mb-8 flex flex-wrap items-center justify-between gap-4">
          <Suspense fallback={<div className="h-10" />}>
            <DistrictPicker
              districts={sortedDistricts}
              selected={districtId}
              basePath="/public"
            />
          </Suspense>
          <HorizonTabs
            horizons={horizons}
            active={horizon}
            basePath="/public"
            extraParams={{ district: districtId }}
          />
        </div>

        {/* ------------------------------------------------------------ */}
        {/* The district's own forecast                                   */}
        {/* ------------------------------------------------------------ */}
        <div className="grid gap-6 lg:grid-cols-3">
          <Card padding="lg" className="lg:col-span-1">
            <div className="flex items-start justify-between gap-3">
              <div>
                <h2 className="text-h2">{district.name}</h2>
                <p className="text-sm text-text-500">{district.province} Province</p>
              </div>
              <RiskPill incidence={rank?.incidence} />
            </div>

            <div className="num mt-6">
              <p className="text-xs uppercase tracking-wide text-text-500">
                {t('public.forecastCases')}, {horizon} {t('public.weeksAhead')}
              </p>
              <p className="mt-1 text-4xl font-bold text-text-900">
                {num(assessment?.forecast_median ?? rank?.median ?? null)}
              </p>
              <p className="mt-2 text-sm text-text-600">
                {t('public.likelyRange')} {num(assessment?.forecast_lower ?? rank?.lower ?? null)}–
                {num(assessment?.forecast_upper ?? rank?.upper ?? null)} {t('public.cases')} ({t('public.interval')})
              </p>
            </div>

            {assessment?.change_pct != null ? (
              <p className="mt-4 inline-flex items-center gap-2 rounded-sm bg-bg-100 px-3 py-2 text-sm">
                <span
                  className={`num font-semibold ${
                    assessment.change_pct > 0 ? 'text-red-700' : 'text-teal-700'
                  }`}
                >
                  {assessment.change_pct > 0 ? '▲' : '▼'} {signedPct(assessment.change_pct)}
                </span>
                <span className="text-text-600">{t('public.vsAverage')}</span>
              </p>
            ) : null}

            <dl className="mt-6 space-y-2 border-t border-border pt-4 text-sm">
              <div className="flex justify-between gap-4">
                <dt className="text-text-500">{t('public.weeklyIncidence')}</dt>
                <dd className="num font-medium text-text-900">
                  {rank?.incidence != null
                    ? `${rank.incidence.toFixed(1)} ${t('public.per100k')}`
                    : '—'}
                </dd>
              </div>
              <div className="flex justify-between gap-4">
                <dt className="text-text-500">{t('public.rankNationally')}</dt>
                <dd className="num font-medium text-text-900">
                  {rank ? `${rank.rank} ${t('public.of')} ${ranked.length}` : '—'}
                </dd>
              </div>
              <div className="flex justify-between gap-4">
                <dt className="text-text-500">{t('public.population')}</dt>
                <dd className="num font-medium text-text-900">{num(district.population)}</dd>
              </div>
              <div className="flex justify-between gap-4">
                <dt className="text-text-500">{t('public.facilities')}</dt>
                <dd className="num font-medium text-text-900">
                  {num(localFacilities.length)}{' '}
                  <span className="text-text-500">
                    ({num(hospitals.length)} {t('public.hospitals')})
                  </span>
                </dd>
              </div>
            </dl>
          </Card>

          <div className="lg:col-span-2">
            <h2 className="text-h2 mb-4">{t('public.whatToDo')}</h2>
            <RecommendationList items={assessment?.recommendations ?? []} />
          </div>
        </div>

        {/* ------------------------------------------------------------ */}
        {/* History                                                       */}
        {/* ------------------------------------------------------------ */}
        <div className="mt-10 grid gap-6 lg:grid-cols-2">
          <ChartFrame
            title={`${t('public.weeklyCasesIn')} ${district.name}`}
            tier="observed"
            caption={t('public.casesCaption')}
          >
            <DistrictCases data={history} />
          </ChartFrame>
          <ChartFrame
            title={t('public.rainfallTitle')}
            tier="observed"
            caption={t('public.rainfallCaption')}
          >
            <DistrictRainfall data={history} />
          </ChartFrame>
        </div>

        {/* ------------------------------------------------------------ */}
        {/* Protect yourself                                              */}
        {/* ------------------------------------------------------------ */}
        <section className="mt-14">
          <SectionHeading
            eyebrow={t('public.protectEyebrow')}
            title={t('public.protectTitle')}
          />

          <div className="grid gap-6 lg:grid-cols-3">
            <Card padding="lg">
              <span className="grid h-10 w-10 place-items-center rounded-sm bg-red-50 text-red-600">
                <ShieldExclamationIcon className="h-5 w-5" aria-hidden />
              </span>
              <h3 className="mt-4 text-h3">{t('public.symptoms')}</h3>
              <ul className="mt-3 space-y-2 text-sm text-text-600">
                <li>{t('public.symptom1')}</li>
                <li>{t('public.symptom2')}</li>
                <li>{t('public.symptom3')}</li>
              </ul>
              <Callout tone="danger" title={t('public.warningTitle')} className="mt-5">
                {t('public.warningBody')}
              </Callout>
            </Card>

            <Card padding="lg">
              <span className="grid h-10 w-10 place-items-center rounded-sm bg-teal-50 text-teal-700">
                <HomeModernIcon className="h-5 w-5" aria-hidden />
              </span>
              <h3 className="mt-4 text-h3">{t('public.prevention')}</h3>
              <ul className="mt-3 space-y-2 text-sm text-text-600">
                <li>{t('public.prevent1')}</li>
                <li>{t('public.prevent2')}</li>
                <li>{t('public.prevent3')}</li>
                <li>{t('public.prevent4')}</li>
                <li>{t('public.prevent5')}</li>
              </ul>
            </Card>

            <Card padding="lg">
              <span className="grid h-10 w-10 place-items-center rounded-sm bg-primary-50 text-primary-700">
                <PhoneIcon className="h-5 w-5" aria-hidden />
              </span>
              <h3 className="mt-4 text-h3">{t('public.emergency')}</h3>
              <ul className="mt-3 space-y-3 text-sm text-text-600">
                <li>
                  <span className="block text-xs uppercase tracking-wide text-text-500">
                    {t('footer.ambulance')}
                  </span>
                  <a href="tel:1990" className="num text-lg font-bold text-primary-700">
                    1990
                  </a>
                </li>
                <li>
                  <span className="block text-xs uppercase tracking-wide text-text-500">
                    {t('footer.ndcu')}
                  </span>
                  <a href="tel:+94112889871" className="num font-semibold text-primary-700">
                    +94 11 288 9871
                  </a>
                </li>
                <li>{t('public.reportBreeding')}</li>
              </ul>
            </Card>
          </div>

          <div className="mt-6 space-y-4">
            <MythVsFact />
            <AlertPreferences districts={sortedDistricts} />
          </div>
        </section>

        <Callout tone="info" className="mt-10">
          <span className="font-semibold">{t('public.disclaimerTitle')}</span>{' '}
          {t('public.disclaimerBody')}
        </Callout>
      </Container>
    </>
  );
}
