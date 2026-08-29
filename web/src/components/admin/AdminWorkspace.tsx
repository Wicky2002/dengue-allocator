'use client';

import React from 'react';
import { CheckCircleIcon, XCircleIcon } from '@heroicons/react/24/outline';

import { Tabs } from '@/components/ui/Tabs';
import { Card } from '@/components/ui/Card';
import { Callout } from '@/components/ui/Callout';
import { Badge } from '@/components/ui/Badge';
import { StatTile } from '@/components/ui/StatTile';
import { NoDataPanel } from '@/components/ui/NoDataPanel';
import { ProvenanceChip } from '@/components/ui/ProvenanceChip';
import { num, shortDate } from '@/lib/format';
import { ROLES } from '@/lib/rbac';
import { TIERS, type TierKey } from '@/lib/provenance';
import constants from '@/generated/constants.json';
import type { PipelineMeta, ScoreRow } from '@/lib/types';
import type { AuditEvent } from '@/lib/audit';
import { AccountManagement } from './AccountManagement';
import type { AccountRow } from '@/app/admin/accounts/actions';

const TABS = [
  { key: 'health', label: 'System health' },
  { key: 'sources', label: 'Data sources' },
  { key: 'models', label: 'Models' },
  { key: 'users', label: 'Users & roles' },
  { key: 'audit', label: 'Audit log' },
];

interface SourceEntry {
  key: string;
  tier: string;
  name: string;
  licence: string;
  url: string;
  covers: string;
}

const SOURCES = constants.sources as SourceEntry[];

export function AdminWorkspace({
  meta,
  artifacts,
  scores,
  auditLogAvailable,
  auditEvents,
  districts,
  accounts,
}: {
  meta: PipelineMeta | null;
  artifacts: { name: string; rows: number }[];
  scores: ScoreRow[];
  auditLogAvailable: boolean;
  auditEvents: AuditEvent[];
  districts: { district_id: string; name: string }[];
  accounts: AccountRow[] | { error: string };
}) {
  const [tab, setTab] = React.useState('health');
  const [config, setConfig] = React.useState({
    model: meta?.forecast_model ?? 'lgbm_quantile',
    horizons: [2, 3, 4],
    retrainWeeks: 4,
    topK: 6,
  });

  return (
    <div>
      <Tabs tabs={TABS} active={tab} onChange={setTab} />

      {tab === 'health' ? (
        <div>
          <div className="mb-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatTile
              label="Last pipeline run"
              value={shortDate(meta?.generated_at ?? null)}
              tier="observed"
              hint={meta ? `${meta.runtime_seconds}s runtime` : undefined}
            />
            <StatTile
              label="Panel source"
              value={(meta?.panel_source ?? '—').toUpperCase()}
              tier="observed"
              hint={meta?.is_synthetic ? 'SIMULATED DATA' : 'Real sources'}
            />
            <StatTile
              label="Districts"
              value={String(meta?.n_districts ?? '—')}
              unit="of 25"
              tier="observed"
            />
            <StatTile
              label="District-weeks in panel"
              value={num(meta?.panel_rows ?? null)}
              tier="observed"
              hint={meta ? `${meta.panel_start.slice(0, 10)} → ${meta.panel_end.slice(0, 10)}` : undefined}
            />
          </div>

          <Card padding="none">
            <div className="border-b border-border px-5 py-4">
              <h3 className="text-h3">Artifact status</h3>
              <p className="mt-1 text-sm text-text-500">
                What the last <code className="font-mono text-xs">make export-web</code> put in
                front of this app.
              </p>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full min-w-[420px] border-collapse text-sm">
                <thead className="border-b border-border bg-bg-100 text-xs uppercase tracking-wide text-text-500">
                  <tr>
                    <th scope="col" className="px-5 py-3 text-left">Artifact</th>
                    <th scope="col" className="px-5 py-3 text-left">Present</th>
                    <th scope="col" className="px-5 py-3 text-right">Rows</th>
                  </tr>
                </thead>
                <tbody>
                  {artifacts.map((artifact) => (
                    <tr key={artifact.name} className="border-b border-border last:border-0">
                      <td className="px-5 py-2.5 font-mono text-xs text-text-700">{artifact.name}</td>
                      <td className="px-5 py-2.5">
                        {artifact.rows > 0 ? (
                          <span className="inline-flex items-center gap-1.5 text-teal-700">
                            <CheckCircleIcon className="h-4 w-4" aria-hidden /> Present
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1.5 text-red-700">
                            <XCircleIcon className="h-4 w-4" aria-hidden /> Missing
                          </span>
                        )}
                      </td>
                      <td className="num px-5 py-2.5 text-right">{num(artifact.rows)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </div>
      ) : null}

      {tab === 'sources' ? (
        <div>
          <div className="overflow-x-auto rounded-sm border border-border bg-white shadow-card">
            <table className="w-full min-w-[760px] border-collapse text-sm">
              <thead className="border-b border-border bg-bg-100 text-xs uppercase tracking-wide text-text-500">
                <tr>
                  <th scope="col" className="px-4 py-3 text-left">Source</th>
                  <th scope="col" className="px-4 py-3 text-left">Tier</th>
                  <th scope="col" className="px-4 py-3 text-left">Licence</th>
                  <th scope="col" className="px-4 py-3 text-left">Covers</th>
                </tr>
              </thead>
              <tbody>
                {SOURCES.map((source) => (
                  <tr key={source.key} className="border-b border-border last:border-0">
                    <td className="px-4 py-3">
                      <a
                        href={source.url}
                        target="_blank"
                        rel="noreferrer noopener"
                        className="font-medium text-primary-700 hover:underline"
                      >
                        {source.name}
                      </a>
                    </td>
                    <td className="px-4 py-3">
                      <ProvenanceChip tier={source.tier as TierKey} basis={source.covers} />
                    </td>
                    <td className="px-4 py-3 text-text-600">{source.licence}</td>
                    <td className="px-4 py-3 text-text-600">{source.covers}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Callout tone="info" title="The Planning estimate tier is the one to watch" className="mt-5">
            Those numbers apply published parameters to model output. They are not measured for
            Sri Lanka, and the platform labels them wherever they appear.
          </Callout>
          <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {TIERS.map((tier) => (
              <Card key={tier.key} padding="md">
                <ProvenanceChip tier={tier.key} basis={tier.key === 'assumed' ? tier.description : undefined} />
                <p className="mt-3 text-sm leading-relaxed text-text-600">{tier.description}</p>
              </Card>
            ))}
          </div>
        </div>
      ) : null}

      {tab === 'models' ? (
        <div>
          <div className="overflow-x-auto rounded-sm border border-border bg-white shadow-card">
            <table className="w-full min-w-[560px] border-collapse text-sm">
              <thead className="border-b border-border bg-bg-100 text-xs uppercase tracking-wide text-text-500">
                <tr>
                  <th scope="col" className="px-4 py-3 text-left">Model</th>
                  <th scope="col" className="px-4 py-3 text-right">Horizon</th>
                  <th scope="col" className="px-4 py-3 text-left">Metric</th>
                  <th scope="col" className="px-4 py-3 text-right">Mean across folds</th>
                  <th scope="col" className="px-4 py-3 text-right">Folds</th>
                </tr>
              </thead>
              <tbody>
                {summariseScores(scores).map((row) => (
                  <tr key={`${row.model}-${row.horizon}-${row.metric}`} className="border-b border-border last:border-0">
                    <td className="px-4 py-2.5 font-medium text-text-900">{row.model}</td>
                    <td className="num px-4 py-2.5 text-right">{row.horizon}w</td>
                    <td className="px-4 py-2.5 text-text-600">{row.metric.replace(/_/g, ' ')}</td>
                    <td className="num px-4 py-2.5 text-right font-semibold">{row.mean.toFixed(3)}</td>
                    <td className="num px-4 py-2.5 text-right text-text-500">{row.folds}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <section className="mt-8">
            <h3 className="text-h3">Configuration</h3>
            <p className="mt-1 max-w-3xl text-[13px] leading-relaxed text-text-600">
              What the next pipeline run would use. These controls describe the intended
              configuration — they do not reach into a running job, because there is no job
              running: the pipeline is invoked from the command line, and this page only ever
              reads what it wrote.
            </p>

            <div className="mt-5 grid gap-6 md:grid-cols-2">
              <label className="block">
                <span className="text-[13px] font-semibold text-text-700">
                  Production forecast model
                </span>
                <select
                  value={config.model}
                  onChange={(event) => setConfig((c) => ({ ...c, model: event.target.value }))}
                  className="mt-1.5 w-full rounded-sm border border-border bg-white px-3 py-2 text-sm"
                >
                  {['lgbm_quantile', 'lgbm_quantile_conformal', 'ensemble', 'sarima', 'seasonal_naive'].map(
                    (option) => (
                      <option key={option} value={option}>
                        {option}
                      </option>
                    ),
                  )}
                </select>
                {meta && config.model !== meta.forecast_model ? (
                  <span className="mt-1.5 block text-[12px] text-state-600">
                    Differs from the last run, which used {meta.forecast_model}.
                  </span>
                ) : null}
              </label>

              <fieldset>
                <legend className="text-[13px] font-semibold text-text-700">Horizons (weeks)</legend>
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {[1, 2, 3, 4, 6, 8].map((weeks) => {
                    const active = config.horizons.includes(weeks);
                    return (
                      <button
                        key={weeks}
                        type="button"
                        onClick={() =>
                          setConfig((c) => ({
                            ...c,
                            horizons: active
                              ? c.horizons.filter((value) => value !== weeks)
                              : [...c.horizons, weeks].sort((a, b) => a - b),
                          }))
                        }
                        aria-pressed={active}
                        className={`num rounded-sm border px-3 py-1.5 text-[13px] font-semibold ${
                          active
                            ? 'border-primary-700 bg-primary-700 text-white'
                            : 'border-border bg-white text-text-600 hover:border-primary-300'
                        }`}
                      >
                        {weeks}
                      </button>
                    );
                  })}
                </div>
              </fieldset>

              <label className="block">
                <span className="flex items-baseline justify-between gap-2">
                  <span className="text-[13px] font-semibold text-text-700">
                    Retrain cadence (weeks)
                  </span>
                  <span className="num text-[13px] font-bold text-primary-700">
                    {config.retrainWeeks}
                  </span>
                </span>
                <input
                  type="range"
                  min={1}
                  max={12}
                  step={1}
                  value={config.retrainWeeks}
                  onChange={(event) =>
                    setConfig((c) => ({ ...c, retrainWeeks: Number(event.target.value) }))
                  }
                  className="mt-2 w-full accent-primary-700"
                />
              </label>

              <label className="block">
                <span className="flex items-baseline justify-between gap-2">
                  <span className="text-[13px] font-semibold text-text-700">
                    High-risk districts designated
                  </span>
                  <span className="num text-[13px] font-bold text-primary-700">{config.topK}</span>
                </span>
                <input
                  type="range"
                  min={3}
                  max={12}
                  step={1}
                  value={config.topK}
                  onChange={(event) => setConfig((c) => ({ ...c, topK: Number(event.target.value) }))}
                  className="mt-2 w-full accent-primary-700"
                />
              </label>
            </div>

            <button
              type="button"
              disabled
              title="Retraining runs from the command line, not from this page."
              className="mt-6 cursor-not-allowed rounded-sm bg-primary-700 px-4 py-2.5 text-[14px] font-semibold text-white opacity-50"
            >
              Trigger retrain
            </button>
          </section>

          <Callout tone="warning" title="Retraining is a pipeline run, not a button" className="mt-6">
            Wiring a “retrain” control into this page would mean the dashboard computes at
            request time — the one thing this platform does not do. Retrain with{' '}
            <code className="font-mono text-xs">make pipeline-real &amp;&amp; make export-web</code>{' '}
            and the new figures appear here.
          </Callout>
        </div>
      ) : null}

      {tab === 'users' ? (
        <div>
          <section className="mb-10">
            <h3 className="text-h3 mb-1">Accounts</h3>
            <p className="mb-4 text-sm text-text-600">
              Create, edit and deactivate staff accounts. Every change here is written to the
              audit log below.
            </p>
            <AccountManagement districts={districts} initialAccounts={accounts} />
          </section>

          <h3 className="text-h3 mb-1">Roles and permissions</h3>
          <p className="mb-4 text-sm text-text-600">Reference — what each role is authorised to do.</p>
          <div className="grid gap-4 sm:grid-cols-2">
            {ROLES.map((role) => (
              <Card key={role.key} padding="lg">
                <div className="flex items-start justify-between gap-3">
                  <h3 className="text-h3">{role.label}</h3>
                  <Badge tone={role.key === 'national_admin' ? 'brand' : 'neutral'}>
                    {role.permissions.length} permissions
                  </Badge>
                </div>
                <p className="mt-2 text-sm text-text-600">{role.description}</p>
                <p className="mt-3 text-xs text-text-500">
                  Scope: {role.key === 'national_admin' ? 'Nationwide' : 'District-scoped'}
                </p>
              </Card>
            ))}
          </div>

          <div className="mt-6 overflow-x-auto rounded-sm border border-border bg-white shadow-card">
            <table className="w-full min-w-[720px] border-collapse text-sm">
              <thead className="border-b border-border bg-bg-100 text-xs uppercase tracking-wide text-text-500">
                <tr>
                  <th scope="col" className="px-4 py-3 text-left">Permission</th>
                  {ROLES.map((role) => (
                    <th key={role.key} scope="col" className="px-4 py-3 text-center">
                      {role.label}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {(constants.permissions as string[]).map((permission) => (
                  <tr key={permission} className="border-b border-border last:border-0">
                    <td className="px-4 py-2.5 font-mono text-xs text-text-700">{permission}</td>
                    {ROLES.map((role) => (
                      <td key={role.key} className="px-4 py-2.5 text-center">
                        {role.permissions.includes(permission) ? (
                          <span className="text-teal-700" aria-label="granted">✓</span>
                        ) : (
                          <span className="text-text-400" aria-label="not granted">—</span>
                        )}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <Callout tone="success" title="Authentication is connected" className="mt-6">
            Accounts are provisioned by an administrator, not self-registered. Each account&rsquo;s
            role and district scope is loaded server-side from a{' '}
            <code className="font-mono text-xs">profiles</code> row — the viewer cannot choose a
            role, only sign into whichever account they hold. This matrix documents what each
            role is authorised to do once authenticated; it is not the login itself.
          </Callout>
        </div>
      ) : null}

      {tab === 'audit' ? (
        auditLogAvailable ? (
          <div>
            <p className="mb-4 max-w-3xl text-sm leading-relaxed text-text-600">
              Every sign-in, sign-out and view of a staff portal, most recent first. Written by a
              database function that stamps each row with the account&rsquo;s own session identity
              — this application code never supplies who an entry belongs to.
            </p>
            {auditEvents.length === 0 ? (
              <Callout tone="info">
                The audit log is set up but has no rows yet — nobody has signed in or viewed a
                staff portal since it was created.
              </Callout>
            ) : (
              <div className="overflow-x-auto rounded-sm border border-border bg-white shadow-card">
                <table className="w-full min-w-[720px] border-collapse text-sm">
                  <thead className="border-b border-border bg-bg-100 text-xs uppercase tracking-wide text-text-500">
                    <tr>
                      <th scope="col" className="px-4 py-3 text-left">When</th>
                      <th scope="col" className="px-4 py-3 text-left">Account</th>
                      <th scope="col" className="px-4 py-3 text-left">Role</th>
                      <th scope="col" className="px-4 py-3 text-left">Event</th>
                      <th scope="col" className="px-4 py-3 text-left">Path</th>
                      <th scope="col" className="px-4 py-3 text-left">Scope at the time</th>
                    </tr>
                  </thead>
                  <tbody>
                    {auditEvents.map((event) => (
                      <tr key={event.id} className="border-b border-border last:border-0">
                        <td className="num px-4 py-2.5 whitespace-nowrap text-text-600">
                          {new Date(event.occurred_at).toLocaleString('en-GB', {
                            day: 'numeric',
                            month: 'short',
                            hour: '2-digit',
                            minute: '2-digit',
                          })}
                        </td>
                        <td className="px-4 py-2.5 font-medium text-text-900">{event.email}</td>
                        <td className="px-4 py-2.5 text-text-600">{event.role}</td>
                        <td className="px-4 py-2.5 font-mono text-xs text-text-700">
                          {event.event_type}
                        </td>
                        <td className="px-4 py-2.5 font-mono text-xs text-text-500">
                          {event.path ?? '—'}
                        </td>
                        <td className="px-4 py-2.5 text-text-600">
                          {event.districts.length === 0 ? 'Nationwide' : event.districts.join(', ')}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        ) : (
          <NoDataPanel
            title="Audit log"
            reason="This deployment authenticates users but has not yet created the audit_log table, so no action history exists to show. Run supabase/audit_log.sql once in the project's SQL editor to enable it."
            enabledBy="Running supabase/audit_log.sql — an append-only table plus the function that writes to it, with reads restricted to national administrators."
          />
        )
      ) : null}
    </div>
  );
}

interface ScoreSummary {
  model: string;
  horizon: number;
  metric: string;
  mean: number;
  folds: number;
}

const HEADLINE_METRICS = ['pinball_mean', 'pinball_loss', 'mae', 'coverage_80', 'mean_lead_time_weeks'];

function summariseScores(scores: ScoreRow[]): ScoreSummary[] {
  const groups = new Map<string, { model: string; horizon: number; metric: string; values: number[] }>();
  for (const row of scores) {
    if (!HEADLINE_METRICS.includes(row.metric) || row.value == null) continue;
    const key = `${row.model}|${row.horizon}|${row.metric}`;
    const entry = groups.get(key) ?? {
      model: row.model,
      horizon: row.horizon,
      metric: row.metric,
      values: [],
    };
    entry.values.push(row.value);
    groups.set(key, entry);
  }
  return Array.from(groups.values())
    .map((entry) => ({
      model: entry.model,
      horizon: entry.horizon,
      metric: entry.metric,
      mean: entry.values.reduce((sum, value) => sum + value, 0) / entry.values.length,
      folds: entry.values.length,
    }))
    .sort(
      (a, b) =>
        a.model.localeCompare(b.model) || a.horizon - b.horizon || a.metric.localeCompare(b.metric),
    );
}

export default AdminWorkspace;
