import {
  ArrowRightIcon,
  BeakerIcon,
  ChartBarSquareIcon,
  MapPinIcon,
  ShieldCheckIcon,
} from '@heroicons/react/24/outline';

import { Container } from '@/components/ui/Container';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Callout } from '@/components/ui/Callout';
import { StatTile } from '@/components/ui/StatTile';
import { SectionHeading } from '@/components/ui/SectionHeading';
import { RiskExplorer } from '@/components/charts/RiskExplorer';
import { TIERS } from '@/lib/provenance';
import { num, shortDate } from '@/lib/format';
import {
  getDistrictRisk,
  getDistricts,
  getGeometry,
  getHorizons,
  getMeta,
  getPanel,
  hasData,
} from '@/lib/data';
import { nationalSummary, nationalTrend, rankDistricts, weekOverWeekChange } from '@/lib/selectors';
import { getT } from '@/lib/i18n/server';

export default async function HomePage() {
  if (!(await hasData())) {
    return <NoExport />;
  }

  const t = await getT();
  const [meta, risk, districts, geometry, panel, horizons] = await Promise.all([
    getMeta(),
    getDistrictRisk(),
    getDistricts(),
    getGeometry(),
    getPanel(),
    getHorizons(),
  ]);

  const horizon = horizons[0] ?? 1;
  const ranked = rankDistricts(risk, districts, horizon);
  const summary = nationalSummary(ranked, risk, horizon);
  const trend = nationalTrend(panel);
  const change = weekOverWeekChange(trend);
  const isSynthetic = meta?.is_synthetic ?? true;

  return (
    <>
      {/* ---------------------------------------------------------------- */}
      {/* Statement of purpose                                              */}
      {/* ---------------------------------------------------------------- */}
      <section className="band-navy border-b-2 border-gold-500">
        <Container className="py-14 lg:py-20">
          <div className="grid gap-12 lg:grid-cols-12 lg:gap-16">
            <div className="lg:col-span-7">
              <p className="text-eyebrow uppercase text-gold-400">
                {t('home.eyebrow')}
              </p>
              <span aria-hidden className="mt-4 block h-0.5 w-16 bg-gold-500" />

              <h1 className="text-display mt-6 text-white">
                {t('home.title')}
              </h1>

              <p className="mt-6 max-w-2xl text-[17px] leading-relaxed text-primary-100">
                {t('home.lede')}
              </p>

              <p className="mt-5 max-w-2xl border-l-2 border-white/25 pl-5 text-[15px] leading-relaxed text-primary-200">
                {t('home.reactingQuote')}
              </p>

              <div className="mt-9 flex flex-wrap gap-3">
                <Button href="/national" size="lg" variant="secondary" trailingIcon={<ArrowRightIcon className="h-4 w-4" />}>
                  {t('home.viewNational')}
                </Button>
                <Button href="/public" size="lg" variant="onDark" leadingIcon={<MapPinIcon className="h-4 w-4" />}>
                  {t('home.checkDistrict')}
                </Button>
              </div>
            </div>

            {/* Current position, set as an official summary table. Real figures
                from the current pipeline run -- not a mock-up with placeholders. */}
            <div className="lg:col-span-5">
              <div className="border border-white/20 bg-white/[0.06]">
                <div className="flex items-center justify-between border-b border-white/20 bg-white/[0.06] px-5 py-3">
                  <h2 className="font-heading text-[15px] font-semibold text-white">
                    {t('home.currentForecast')}
                  </h2>
                  <span className="num text-[11px] uppercase tracking-wide text-gold-400">
                    {horizon} {t('home.weeksAhead')}
                  </span>
                </div>

                <dl className="divide-y divide-white/15">
                  <div className="flex items-baseline justify-between gap-4 px-5 py-4">
                    <dt className="text-[13px] text-primary-200">{t('home.targetWeek')}</dt>
                    <dd className="num text-[15px] font-semibold text-white">
                      {shortDate(summary.targetWeek)}
                    </dd>
                  </div>
                  <div className="flex items-baseline justify-between gap-4 px-5 py-4">
                    <dt className="text-[13px] text-primary-200">{t('home.forecastCasesNationwide')}</dt>
                    <dd className="num text-[22px] font-bold leading-none text-white">
                      {num(summary.totalForecastCases)}
                    </dd>
                  </div>
                  <div className="flex items-baseline justify-between gap-4 px-5 py-4">
                    <dt className="text-[13px] text-primary-200">{t('home.districtsHighRisk')}</dt>
                    <dd className="num text-[22px] font-bold leading-none text-gold-400">
                      {summary.nElevated}
                      <span className="ml-1.5 text-[12px] font-medium text-primary-200">
                        {t('public.of')} {summary.nDistricts}
                      </span>
                    </dd>
                  </div>
                  {summary.worst ? (
                    <div className="flex items-baseline justify-between gap-4 px-5 py-4">
                      <dt className="text-[13px] text-primary-200">{t('home.highestRiskDistrict')}</dt>
                      <dd className="text-right">
                        <span className="block text-[15px] font-semibold text-white">
                          {summary.worst.name}
                        </span>
                        <span className="num block text-[12px] text-primary-200">
                          {summary.worst.incidence?.toFixed(1)} {t('home.per100kWeek')}
                        </span>
                      </dd>
                    </div>
                  ) : null}
                </dl>

                <p className="border-t border-white/20 px-5 py-3.5 text-[11.5px] leading-relaxed text-primary-300">
                  {t('home.modelledNote')} {meta?.forecast_model ?? 'ensemble'}{' '}
                  {t('home.modelledNote2')}
                </p>
              </div>
            </div>
          </div>
        </Container>
      </section>

      {/* Data-provenance caveat, before any figure below is read. */}
      <Container className="pt-8">
        {isSynthetic ? (
          <Callout tone="simulated" title={t('home.simulatedTitle')}>
            {t('home.simulatedBody')}{' '}
            <code className="rounded bg-white/60 px-1 py-0.5 font-mono text-xs">make panel &amp;&amp; make pipeline-real &amp;&amp; make export-web</code>{' '}
            {t('home.simulatedBody2')}
          </Callout>
        ) : (
          <Callout tone="success" title={t('home.realTitle')}>
            {t('home.realBody')}{' '}
            {shortDate(meta?.generated_at ?? null)}{t('home.realBody2')}
          </Callout>
        )}
      </Container>

      {/* ---------------------------------------------------------------- */}
      {/* National snapshot                                                 */}
      {/* ---------------------------------------------------------------- */}
      <section className="py-14 sm:py-20">
        <Container>
          <SectionHeading
            eyebrow={t('home.snapshotEyebrow')}
            title={t('home.snapshotTitle')}
            description={t('home.snapshotDescription')
              .replace('{n}', String(summary.nDistricts))
              .replace('{h}', String(horizon))}
            action={
              <Button href="/national" variant="outline" trailingIcon={<ArrowRightIcon className="h-4 w-4" />}>
                {t('home.fullOverview')}
              </Button>
            }
          />

          <div className="mb-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatTile
              label={t('home.districtsForecast')}
              value={String(summary.nDistricts)}
              unit={t('home.ofTwentyFive')}
              tier="modelled"
              hint={`${meta?.forecast_model ?? 'ensemble'} model`}
            />
            <StatTile
              label={t('home.highRiskOrAbove')}
              value={String(summary.nElevated)}
              unit={t('home.districtsUnit')}
              tier="modelled"
              hint={t('home.aboveThreshold')}
            />
            <StatTile
              label={t('home.forecastCases')}
              value={num(summary.totalForecastCases)}
              tier="modelled"
              hint={`${t('home.nationwide')}, ${horizon} ${t('home.weeksAhead')}`}
            />
            <StatTile
              label={t('home.casesLastWeek')}
              value={num(trend.at(-1)?.cases ?? null)}
              tier="observed"
              hint={t('home.notifiedNationwide')}
              trend={
                change != null
                  ? {
                      value: `${Math.abs(change * 100).toFixed(0)}% wk/wk`,
                      direction: change > 0.02 ? 'up' : change < -0.02 ? 'down' : 'flat',
                    }
                  : undefined
              }
            />
          </div>

          <RiskExplorer geometry={geometry} ranked={ranked} horizon={horizon} />
        </Container>
      </section>

      {/* ---------------------------------------------------------------- */}
      {/* Provenance — the platform's central idea                          */}
      {/* ---------------------------------------------------------------- */}
      <section className="border-y border-border bg-white py-14 sm:py-20">
        <Container>
          <SectionHeading
            align="center"
            eyebrow={t('home.readEyebrow')}
            title={t('home.readTitle')}
            description={t('home.readDescription')}
          />

          <div className="grid gap-5 md:grid-cols-3">
            {TIERS.filter((tier) => tier.key !== 'user_input').map((tier, index) => (
              <Card key={tier.key} padding="lg" accent="navy" className="flex flex-col">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold uppercase tracking-widest text-text-400">
                    {t('home.tier')} {index + 1}
                  </span>
                  <Badge tone={index === 0 ? 'neutral' : index === 1 ? 'brand' : 'info'}>
                    {t(`prov.${tier.key}`)}
                  </Badge>
                </div>
                <p className="mt-4 flex-1 text-sm leading-relaxed text-text-600">{tier.description}</p>
                <p className="mt-4 border-t border-border pt-4 text-sm">
                  <span className="font-medium text-text-900">{t('home.example')} </span>
                  <span className="text-text-600">
                    {
                      [
                        t('home.example1'),
                        `${num(summary.worst?.median ?? null)} ${t('home.example2')} ${summary.worst?.name ?? 'a district'} ${t('home.example3')} ${horizon} ${t('home.example3b')}`,
                        t('home.example4'),
                      ][index]
                    }
                  </span>
                </p>
              </Card>
            ))}
          </div>

          <Callout tone="info" className="mt-6">
            <span className="font-semibold">{t('home.noDataTitle')}</span>{' '}
            {t('home.noDataBody')}
          </Callout>
        </Container>
      </section>

      {/* ---------------------------------------------------------------- */}
      {/* Three-stage engine                                                */}
      {/* ---------------------------------------------------------------- */}
      <section className="band-navy border-y-2 border-gold-500 py-14 sm:py-20">
        <Container>
          <SectionHeading
            align="center"
            eyebrow={t('home.engineEyebrow')}
            title={t('home.engineTitle')}
          />
          <p className="mx-auto -mt-4 mb-10 max-w-2xl text-center text-primary-200">
            {t('home.engineLede')}
          </p>

          <ol className="grid gap-5 md:grid-cols-3">
            {[
              {
                stage: 'Stage 1',
                titleKey: 'home.stage1.title',
                icon: ChartBarSquareIcon,
                bodyKey: 'home.stage1.body',
              },
              {
                stage: 'Stage 2',
                titleKey: 'home.stage2.title',
                icon: BeakerIcon,
                bodyKey: 'home.stage2.body',
              },
              {
                stage: 'Stage 3',
                titleKey: 'home.stage3.title',
                icon: ShieldCheckIcon,
                bodyKey: 'home.stage3.body',
              },
            ].map((step) => (
              <li key={step.stage} className="border border-white/20 bg-white/[0.06] p-6">
                <div className="flex items-center gap-3">
                  <span className="grid h-10 w-10 place-items-center border border-gold-500/40 text-gold-400">
                    <step.icon className="h-5 w-5" aria-hidden />
                  </span>
                  <span className="text-xs font-semibold uppercase tracking-widest text-primary-300">
                    {step.stage}
                  </span>
                </div>
                <h3 className="mt-4 text-lg font-semibold text-white">{t(step.titleKey)}</h3>
                <p className="mt-2 text-sm leading-relaxed text-primary-200">{t(step.bodyKey)}</p>
              </li>
            ))}
          </ol>

          <div className="mt-10 text-center">
            <Button href="/method" variant="onDark" size="lg" trailingIcon={<ArrowRightIcon className="h-4 w-4" />}>
              {t('home.howBuilt')}
            </Button>
          </div>
        </Container>
      </section>
    </>
  );
}

/** Shown when `make export-web` has never run — actionable, not a dead end. */
async function NoExport() {
  const t = await getT();
  return (
    <Container className="py-24">
      <Card padding="lg" className="mx-auto max-w-2xl text-center">
        <h1 className="text-h1">{t('home.noDataYetTitle')}</h1>
        <p className="mt-3 text-text-600">{t('home.noDataYetBody')}</p>
        <pre className="mt-5 overflow-x-auto rounded-sm bg-primary-900 p-4 text-left font-mono text-sm text-primary-100">
          make pipeline{'\n'}make export-web
        </pre>
        <p className="mt-4 text-sm text-text-500">{t('home.noDataYetNote')}</p>
      </Card>
    </Container>
  );
}
