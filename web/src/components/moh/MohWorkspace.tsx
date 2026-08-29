'use client';

import React from 'react';

import { Tabs } from '@/components/ui/Tabs';
import { Card } from '@/components/ui/Card';
import { Callout } from '@/components/ui/Callout';
import { RiskPill } from '@/components/ui/RiskPill';
import { RecommendationList } from '@/components/ui/RecommendationList';
import { AllocationPanel } from './AllocationPanel';
import { HotspotPanel, type HotspotDistrict } from './HotspotPanel';
import { ScenarioPanel } from './ScenarioPanel';
import { BudgetPanel } from './BudgetPanel';
import { InterventionSchedule } from './InterventionSchedule';
import { num, signedPct } from '@/lib/format';
import type { AllocationRow, AllocationSummary, Assessment, BudgetRow, ScenarioRow } from '@/lib/types';

const TABS = [
  { key: 'hotspots', label: 'Hotspots' },
  { key: 'teams', label: 'Team deployment' },
  { key: 'plan', label: 'Intervention plan' },
  { key: 'scenarios', label: 'Scenarios' },
  { key: 'budget', label: 'Budget' },
];

export function MohWorkspace({
  assessments,
  sweep,
  summary,
  scenarios,
  budget,
  districtNames,
  hotspotDistricts,
  ownDistricts,
  inScope,
  canRunScenarios,
  canSeeBudget,
}: {
  assessments: Assessment[];
  sweep: AllocationRow[];
  summary: AllocationSummary[];
  scenarios: ScenarioRow[];
  budget: BudgetRow[];
  districtNames: Record<string, string>;
  hotspotDistricts: HotspotDistrict[];
  ownDistricts: string[];
  inScope: string[] | null;
  canRunScenarios: boolean;
  canSeeBudget: boolean;
}) {
  const [tab, setTab] = React.useState('hotspots');
  const visible = TABS.filter(
    (item) =>
      (item.key !== 'scenarios' || canRunScenarios) && (item.key !== 'budget' || canSeeBudget),
  );

  return (
    <div>
      <Tabs tabs={visible} active={tab} onChange={setTab} />

      {tab === 'hotspots' ? (
        <HotspotPanel
          assessments={assessments}
          districts={hotspotDistricts}
          ownDistricts={ownDistricts}
        />
      ) : null}

      {tab === 'teams' ? (
        <AllocationPanel
          sweep={sweep}
          summary={summary}
          districtNames={districtNames}
          inScope={inScope}
        />
      ) : null}

      {tab === 'plan' ? (
        <InterventionSchedule sweep={sweep} districtNames={districtNames} inScope={inScope} />
      ) : null}

      {tab === 'scenarios' && canRunScenarios ? <ScenarioPanel scenarios={scenarios} /> : null}

      {tab === 'budget' && canSeeBudget ? <BudgetPanel rows={budget} /> : null}
    </div>
  );
}

export default MohWorkspace;
