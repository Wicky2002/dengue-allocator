'use client';

import React from 'react';
import { ChevronLeftIcon, ChevronRightIcon } from '@heroicons/react/24/outline';

import { Choropleth } from './Choropleth';
import { RiskPill } from '@/components/ui/RiskPill';
import { ProvenanceChip } from '@/components/ui/ProvenanceChip';
import { RISK_BANDS } from '@/lib/risk';
import { num, shortDate } from '@/lib/format';
import type { HistorySeries } from '@/lib/selectors';
import { weekSummary } from '@/lib/selectors';
import { useT } from '@/components/i18n/LocaleProvider';

/**
 * What happened, beside what the model said would happen.
 *
 * One scrubber drives both maps. It names a single week, and each map answers a
 * different question about that week: the left shows the notified cases, the
 * right shows what the model predicted for it while standing `horizon` weeks
 * earlier and seeing none of the data in between. A second, independently
 * scrubbed control for the prediction was rejected on the Streamlit build for
 * the obvious reason — the two maps then usually showed different weeks, which
 * is precisely the comparison this panel exists to make.
 *
 * The predicted series covers a shorter span than the observed one, because
 * back-testing every week of history is a pipeline job rather than a dashboard
 * one. Weeks with no prediction say so instead of rendering an empty map.
 */
export function HistoryCompare({
  observed,
  predicted,
  districtNames,
  horizon,
}: {
  observed: HistorySeries;
  predicted: HistorySeries;
  /** The 25-row registry, so 2,600 history cells need not each carry a name. */
  districtNames: Record<string, string>;
  horizon: number;
}) {
  const t = useT();
  const weeks = observed.weeks;

  // Open on the most recent week that has a prediction, so the panel lands on a
  // real comparison rather than on a week where half of it is empty.
  const initialIndex = React.useMemo(() => {
    const lastPredicted = predicted.weeks.at(-1);
    const found = lastPredicted ? weeks.indexOf(lastPredicted) : -1;
    return found >= 0 ? found : Math.max(weeks.length - 1, 0);
  }, [weeks, predicted.weeks]);

  // Resets the scrubber whenever `initialIndex` changes (a new horizon
  // brings a different "most recent week with a prediction"). Adjusted during
  // render rather than in an effect -- React's own recommended pattern for
  // this exact case -- so the reset lands in the same render as the change
  // instead of committing the stale value first and correcting it a render
  // later.
  const [index, setIndex] = React.useState(initialIndex);
  const [priorInitialIndex, setPriorInitialIndex] = React.useState(initialIndex);
  if (initialIndex !== priorInitialIndex) {
    setPriorInitialIndex(initialIndex);
    setIndex(initialIndex);
  }

  const week = weeks[index];
  const observedCells = observed.byWeek[week];
  const predictedCells = predicted.byWeek[week];
  const observedSummary = weekSummary(observedCells, districtNames);
  const predictedSummary = weekSummary(predictedCells, districtNames);

  const predictedWeekSet = React.useMemo(() => new Set(predicted.weeks), [predicted.weeks]);

  if (weeks.length === 0) return null;

  const step = (delta: number) =>
    setIndex((current) => Math.min(Math.max(current + delta, 0), weeks.length - 1));

  return (
    <div className="rounded-sm border border-border bg-white p-5 shadow-card">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h3 className="text-h3">{t('hist.viewPastWeek')}</h3>
          <p className="mt-1 text-[13px] text-text-500">
            {t('hist.description')} {horizon} {t('hist.weeksEarlier')}
          </p>
        </div>
        <p className="num text-right">
          <span className="block text-[11px] uppercase tracking-wide text-text-500">
            {t('hist.weekBeginning')}
          </span>
          <span className="block text-[17px] font-bold text-primary-900">{shortDate(week)}</span>
        </p>
      </div>

      {/* Scrubber. Ticks mark the weeks a prediction exists for, so it is
          obvious where a comparison is available before dragging there. */}
      <div className="mt-5 flex items-center gap-3">
        <button
          type="button"
          onClick={() => step(-1)}
          disabled={index === 0}
          aria-label={t('hist.previousWeek')}
          className="rounded-sm border border-border p-1.5 text-text-600 hover:bg-bg-100 disabled:opacity-40"
        >
          <ChevronLeftIcon className="h-4 w-4" aria-hidden />
        </button>

        <div className="relative flex-1">
          <input
            type="range"
            min={0}
            max={weeks.length - 1}
            step={1}
            value={index}
            onChange={(event) => setIndex(Number(event.target.value))}
            aria-label={t('hist.weekLabel')}
            aria-valuetext={shortDate(week)}
            className="w-full accent-primary-700"
          />
          <div aria-hidden className="pointer-events-none relative mt-1 h-1.5">
            {weeks.map((candidate, position) =>
              predictedWeekSet.has(candidate) ? (
                <span
                  key={candidate}
                  className="absolute top-0 h-1.5 w-0.5 -translate-x-1/2 bg-state-600"
                  style={{ left: `${(position / Math.max(weeks.length - 1, 1)) * 100}%` }}
                />
              ) : null,
            )}
          </div>
          <p className="num mt-1 flex justify-between text-[11px] text-text-400">
            <span>{shortDate(weeks[0])}</span>
            <span className="text-state-600">▎ {t('hist.backtestedTicks')}</span>
            <span>{shortDate(weeks.at(-1) ?? null)}</span>
          </p>
        </div>

        <button
          type="button"
          onClick={() => step(1)}
          disabled={index === weeks.length - 1}
          aria-label={t('hist.nextWeek')}
          className="rounded-sm border border-border p-1.5 text-text-600 hover:bg-bg-100 disabled:opacity-40"
        >
          <ChevronRightIcon className="h-4 w-4" aria-hidden />
        </button>
      </div>

      <div className="mt-6 grid gap-6 md:grid-cols-2">
        <section>
          <header className="mb-3 flex items-center justify-between gap-2 border-b border-border pb-2">
            <h4 className="font-heading text-[15px] font-semibold text-text-900">
              {t('hist.observed')}
            </h4>
            <ProvenanceChip tier="observed" />
          </header>
          {/* No `geometry` prop: these two maps fetch the static outlines
              client-side rather than have them serialised into the page a
              second and third time alongside the risk map above. */}
          <Choropleth
            data={(observedCells ?? []).map((cell) => ({
              district_id: cell.district_id,
              name: districtNames[cell.district_id] ?? cell.district_id,
              incidence: cell.incidence,
              median: cell.cases,
            }))}
            height={430}
            maxHeightClass="max-h-[380px]"
            showLegend={false}
            emptyMessage={t('hist.noNotifiedCases')}
          />
          <WeekFigures
            caseLabel={t('hist.casesThatWeek')}
            total={observedSummary?.total ?? null}
            worstName={observedSummary?.worstName ?? null}
            worstIncidence={observedSummary?.worst.incidence ?? null}
          />
        </section>

        <section>
          <header className="mb-3 flex items-center justify-between gap-2 border-b border-border pb-2">
            <h4 className="font-heading text-[15px] font-semibold text-text-900">
              {t('hist.predictedAhead')} {horizon} {t('home.weeksAhead')}
            </h4>
            <ProvenanceChip tier="modelled" />
          </header>
          <Choropleth
            data={(predictedCells ?? []).map((cell) => ({
              district_id: cell.district_id,
              name: districtNames[cell.district_id] ?? cell.district_id,
              incidence: cell.incidence,
              median: cell.cases,
            }))}
            height={430}
            maxHeightClass="max-h-[380px]"
            showLegend={false}
            emptyMessage={t('hist.noPredictionForWeek')}
          />
          <WeekFigures
            caseLabel={t('hist.predictedCases')}
            total={predictedSummary?.total ?? null}
            worstName={predictedSummary?.worstName ?? null}
            worstIncidence={predictedSummary?.worst.incidence ?? null}
          />
        </section>
      </div>

      <ul className="mt-6 grid grid-cols-2 gap-x-4 gap-y-2 border-t border-border pt-4 sm:grid-cols-4">
        {RISK_BANDS.map((band) => (
          <li key={band.key} className="flex items-start gap-2">
            <span
              aria-hidden
              className="mt-1 h-3 w-3 shrink-0"
              style={{ background: band.colour }}
            />
            <span className="text-[12px] leading-tight">
              <span className="block font-semibold text-text-800">{t(`risk.${band.key}`)}</span>
              <span className="num block text-text-500">
                {band.threshold === 0 ? t('hist.under') + ' 1.5' : `${band.threshold}+`}{' '}
                {t('hist.per100kWkUnit')}
              </span>
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}

function WeekFigures({
  caseLabel,
  total,
  worstName,
  worstIncidence,
}: {
  caseLabel: string;
  total: number | null;
  worstName: string | null;
  worstIncidence: number | null;
}) {
  const t = useT();
  return (
    <dl className="mt-4 grid grid-cols-2 gap-4">
      <div className="border-t-2 border-t-primary-700 bg-bg-100 p-3">
        <dt className="text-[11px] uppercase tracking-wide text-text-500">{caseLabel}</dt>
        <dd className="num mt-1 text-[22px] font-bold leading-none text-primary-900">
          {num(total)}
        </dd>
      </div>
      <div className="border-t-2 border-t-primary-700 bg-bg-100 p-3">
        <dt className="text-[11px] uppercase tracking-wide text-text-500">{t('hist.highestRisk')}</dt>
        <dd className="mt-1">
          <span className="block text-[15px] font-semibold text-text-900">{worstName ?? '—'}</span>
          {worstIncidence != null ? <RiskPill incidence={worstIncidence} className="mt-1" /> : null}
        </dd>
      </div>
    </dl>
  );
}

export default HistoryCompare;
