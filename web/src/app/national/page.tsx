import type { Metadata } from 'next';

import { Container } from '@/components/ui/Container';
import { Callout } from '@/components/ui/Callout';
import { StatTile } from '@/components/ui/StatTile';
import { SectionHeading } from '@/components/ui/SectionHeading';
import { PageHeader } from '@/components/layout/PageHeader';
import { HorizonTabs } from '@/components/ui/HorizonTabs';
import { RiskExplorer } from '@/components/charts/RiskExplorer';
import { HistoryCompare } from '@/components/charts/HistoryCompare';
import { ChartFrame } from '@/components/charts/ChartFrame';
import { ForecastTrend } from '@/components/charts/ForecastTrend';
import { RainfallOverlay } from '@/components/charts/RainfallOverlay';
import { ModelScores } from '@/components/charts/ModelScores';
import { DistrictTable } from '@/components/tables/DistrictTable';
import { ReportDownload } from '@/components/ui/ReportDownload';
import { num, shortDate } from '@/lib/format';
import {
  getDistrictCapacity,
  getDistrictRisk,
  getDistricts,
  getGeometry,
  getHorizons,
  getMeta,
  getPanel,
  getPredictionHistory,
  getScores,
  hasData,
} from '@/lib/data';
import { readJson } from '@/lib/data';
import {
  modelComparison,
  observedHistory,
  predictedHistory,
  nationalForecastSeries,
  nationalSummary,
  nationalTrend,
  rainfallSeries,
  rankDistricts,
  weekOverWeekChange,
} from '@/lib/selectors';
import { NoExportNotice } from '@/components/ui/NoExportNotice';
import { getT } from '@/lib/i18n/server';

export const metadata: Metadata = {
  title: 'National overview',
  description: 'Forecast dengue risk across all 25 districts of Sri Lanka.',
};

export default async function NationalPage({
  searchParams,
}: {
  searchParams: Promise<{ horizon?: string }>;
}) {
  if (!(await hasData())) return <NoExportNotice />;

  const t = await getT();
  const [meta, risk, districts, geometry, panel, scores, capacity, horizons, history] =
    await Promise.all([
      getMeta(),
      getDistrictRisk(),
      getDistricts(),
      getGeometry(),
      getPanel(),
      getScores(),
      getDistrictCapacity(),
      getHorizons(),
      getPredictionHistory(),
    ]);

  const requested = Number((await searchParams).horizon);
  const horizon = horizons.includes(requested) ? requested : (horizons[0] ?? 1);

  const ranked = rankDistricts(risk, districts, horizon);
  const summary = nationalSummary(ranked, risk, horizon);
  const trend = nationalTrend(panel, 78);
  const change = weekOverWeekChange(trend);
  const forecasts = await readJson<{
    target_week: string | null;
    'q0.5': number | null;
    'q0.1': number | null;
    'q0.9': number | null;
    horizon: number;
  }>('forecasts');
  const series = nationalForecastSeries(trend, forecasts, horizons);
  const rainfall = rainfallSeries(panel);
  const bestMetric = scores.some((row) => row.metric === 'pinball_loss') ? 'pinball_loss' : 'mae';
  const comparison = modelComparison(scores, bestMetric, horizon);
  const capacityById = new Map(capacity.map((row) => [row.district_id, row]));
  const observed = observedHistory(panel);
  const predicted = predictedHistory(history, horizon);
  const districtNames = Object.fromEntries(districts.map((d) => [d.district_id, d.name]));

  return (
    <>
      <PageHeader
        crumbs={[{ label: t('nat.crumb') }]}
        eyebrow={t('nat.eyebrow')}
        title={t('nat.title')}
        description={t('nat.description').replace('{week}', shortDate(summary.targetWeek))}
        meta={[
          { label: t('nat.metaModel'), value: meta?.forecast_model ?? '—' },
          { label: t('nat.metaPanel'), value: meta?.panel_source ?? '—' },
          { label: t('nat.metaPipelineRun'), value: shortDate(meta?.generated_at ?? null) },
        ]}
      />

      <Container className="py-10">
        {meta?.is_synthetic ? (
          <Callout tone="simulated" title={t('nat.simulatedTitle')} className="mb-8">
            {t('nat.simulatedBody')}
          </Callout>
        ) : null}

        <HorizonTabs horizons={horizons} active={horizon} basePath="/national" />

        <div className="mb-8 mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
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
            hint={`${summary.bandCounts.severe} ${t('nat.veryHigh')} · ${summary.bandCounts.high} ${t('nat.high')}`}
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

        <section className="mt-12">
          <SectionHeading
            eyebrow={t('nat.hindsightEyebrow')}
            title={t('nat.hindsightTitle')}
            description={t('nat.hindsightDescription').replace('{h}', String(horizon))}
          />
          <HistoryCompare
            observed={observed}
            predicted={predicted}
            districtNames={districtNames}
            horizon={horizon}
          />
        </section>

        <div className="mt-12 grid gap-6 lg:grid-cols-2">
          <ChartFrame
            title={t('nat.chartObservedForecast')}
            tier="modelled"
            caption={t('nat.chartObservedForecastCaption')}
          >
            <ForecastTrend data={series} />
          </ChartFrame>

          <ChartFrame
            title={t('nat.chartRainfall')}
            tier="observed"
            caption={t('nat.chartRainfallCaption')}
          >
            <RainfallOverlay data={rainfall} />
          </ChartFrame>
        </div>

        <section className="mt-12">
          <SectionHeading
            eyebrow={t('nat.backtestEyebrow')}
            title={t('nat.backtestTitle')}
            description={t('nat.backtestDescription')
              .replace('{metric}', bestMetric.replace('_', ' '))
              .replace('{h}', String(horizon))}
          />
          <div className="grid gap-6 lg:grid-cols-2">
            <ChartFrame title={`${t('nat.modelComparison')} (${bestMetric.replace('_', ' ')})`} tier="modelled">
              {comparison.length > 0 ? (
                <ModelScores data={comparison} metricLabel={bestMetric.replace('_', ' ')} />
              ) : (
                <p className="py-10 text-center text-sm text-text-500">
                  {t('nat.noBacktestScores')}
                </p>
              )}
            </ChartFrame>
            <div className="rounded-sm border border-border bg-white p-5 shadow-card">
              <h3 className="text-h3">{t('nat.intervalMeaningTitle')}</h3>
              <p className="mt-3 text-sm leading-relaxed text-text-600">
                {t('nat.intervalMeaningBody')}
              </p>
              <dl className="mt-5 space-y-3 border-t border-border pt-4 text-sm">
                <div className="flex justify-between gap-4">
                  <dt className="text-text-500">{t('nat.widestInterval')}</dt>
                  <dd className="num font-medium text-text-900">
                    {(() => {
                      const widest = [...ranked].sort(
                        (a, b) => (b.intervalWidth ?? 0) - (a.intervalWidth ?? 0),
                      )[0];
                      return widest ? `${widest.name} (${num(widest.intervalWidth)} cases)` : '—';
                    })()}
                  </dd>
                </div>
                <div className="flex justify-between gap-4">
                  <dt className="text-text-500">{t('nat.backtestFolds')}</dt>
                  <dd className="num font-medium text-text-900">{comparison[0]?.folds ?? '—'}</dd>
                </div>
                <div className="flex justify-between gap-4">
                  <dt className="text-text-500">{t('nat.panelWindow')}</dt>
                  <dd className="num font-medium text-text-900">
                    {meta ? `${meta.panel_start.slice(0, 4)}–${meta.panel_end.slice(0, 4)}` : '—'}
                  </dd>
                </div>
                <div className="flex justify-between gap-4">
                  <dt className="text-text-500">{t('nat.districtWeeks')}</dt>
                  <dd className="num font-medium text-text-900">{num(meta?.panel_rows ?? null)}</dd>
                </div>
              </dl>
            </div>
          </div>
        </section>

        <section className="mt-12">
          <SectionHeading
            eyebrow={t('nat.detailEyebrow')}
            title={t('nat.detailTitle')}
            description={t('nat.detailDescription')}
          />
          <DistrictTable ranked={ranked} capacity={capacityById} />
        </section>

        <section className="mt-12">
          <SectionHeading
            eyebrow={t('nat.reportEyebrow')}
            title={t('nat.reportTitle')}
            description={t('nat.reportDescription')}
          />
          <ReportDownload horizon={horizon} generatedAt={meta?.generated_at ?? null} />
        </section>
      </Container>
    </>
  );
}
