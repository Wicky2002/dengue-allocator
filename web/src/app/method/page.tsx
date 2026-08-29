import type { Metadata } from 'next';

import { Container } from '@/components/ui/Container';
import { Card } from '@/components/ui/Card';
import { Callout } from '@/components/ui/Callout';
import { Badge } from '@/components/ui/Badge';
import { SectionHeading } from '@/components/ui/SectionHeading';
import { PageHeader } from '@/components/layout/PageHeader';
import { ProvenanceChip } from '@/components/ui/ProvenanceChip';
import { num, shortDate } from '@/lib/format';
import { RISK_BANDS } from '@/lib/risk';
import { TIERS } from '@/lib/provenance';
import { ROLES } from '@/lib/rbac';
import { getMeta, getScores } from '@/lib/data';
import { modelComparison } from '@/lib/selectors';
import { getT } from '@/lib/i18n/server';

export const metadata: Metadata = {
  title: 'How it works',
  description:
    'The three-stage engine behind DengueSentinel: probabilistic forecasting, mechanistic effect estimation, and constrained allocation.',
};

export default async function MethodPage() {
  const [meta, scores] = await Promise.all([getMeta(), getScores()]);
  const t = await getT();
  const metric = scores.some((row) => row.metric === 'pinball_loss') ? 'pinball_loss' : 'mae';
  const horizon = meta?.effect_horizon_weeks ?? 2;
  const comparison = modelComparison(scores, metric, 2).slice(0, 3);

  const stage1Detail = comparison.length
    ? t('method.stage1DetailTemplate')
        .replace('{metric}', metric.replace('_', ' '))
        .replace(
          '{list}',
          comparison.map((row) => `${row.model} (${row.value.toFixed(3)})`).join(', '),
        )
    : undefined;
  const stage2Detail = t('method.stage2DetailTemplate').replace('{horizon}', String(horizon));

  return (
    <>
      <PageHeader
        crumbs={[{ label: t('method.crumb') }]}
        eyebrow={t('method.eyebrow')}
        title={t('method.title')}
        description={t('method.description')}
        meta={[
          { label: t('method.metaPanel'), value: meta?.panel_source ?? '—' },
          { label: t('method.metaDistrictWeeks'), value: num(meta?.panel_rows ?? null) },
          { label: t('method.metaLastRun'), value: shortDate(meta?.generated_at ?? null) },
        ]}
      />

      <Container className="py-12">
        {/* Stages ------------------------------------------------------ */}
        <SectionHeading
          eyebrow={t('method.engineEyebrow')}
          title={t('method.engineTitle')}
          description={t('method.engineDescription')}
        />

        <ol className="space-y-6">
          {[
            {
              stage: t('method.stage1'),
              title: t('method.stage1Title'),
              body: t('method.stage1Body'),
              detail: stage1Detail,
              tier: 'modelled' as const,
            },
            {
              stage: t('method.stage2'),
              title: t('method.stage2Title'),
              body: t('method.stage2Body'),
              detail: stage2Detail,
              tier: 'modelled' as const,
            },
            {
              stage: t('method.stage3'),
              title: t('method.stage3Title'),
              body: t('method.stage3Body'),
              detail: t('method.stage3Detail'),
              tier: 'modelled' as const,
            },
          ].map((step) => (
            <li key={step.stage}>
              <Card padding="lg">
                <div className="flex flex-wrap items-center gap-3">
                  <Badge tone="brand">{step.stage}</Badge>
                  <h3 className="text-h3">{step.title}</h3>
                  <ProvenanceChip tier={step.tier} className="ml-auto" />
                </div>
                <p className="mt-4 leading-relaxed text-text-600">{step.body}</p>
                {step.detail ? (
                  <p className="mt-3 border-t border-border pt-3 text-sm text-text-500">
                    {step.detail}
                  </p>
                ) : null}
              </Card>
            </li>
          ))}
        </ol>

        {/* Why two weeks ---------------------------------------------- */}
        <section className="mt-14">
          <SectionHeading
            eyebrow={t('method.whyForecastEyebrow')}
            title={t('method.whyForecastTitle')}
          />
          <Card padding="lg">
            <p className="leading-relaxed text-text-600">{t('method.whyForecastBody1')}</p>
            <p className="mt-4 leading-relaxed text-text-600">{t('method.whyForecastBody2')}</p>
          </Card>
        </section>

        {/* Risk bands -------------------------------------------------- */}
        <section className="mt-14">
          <SectionHeading
            eyebrow={t('method.riskBandsEyebrow')}
            title={t('method.riskBandsTitle')}
            description={t('method.riskBandsDescription')}
          />
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {RISK_BANDS.map((band) => (
              <Card key={band.key} padding="lg">
                <span
                  aria-hidden
                  className="block h-1.5 w-10 rounded-full"
                  style={{ background: band.colour }}
                />
                <h3 className="mt-3 text-h3">{band.label}</h3>
                <p className="num mt-1 text-sm text-text-600">
                  {band.threshold === 0
                    ? t('method.riskBandBelow')
                    : t('method.riskBandAndAboveTemplate').replace(
                        '{threshold}',
                        String(band.threshold),
                      )}{' '}
                  {t('method.riskBandPerWeek')}
                </p>
              </Card>
            ))}
          </div>
          <Callout tone="warning" className="mt-5">
            {t('method.riskBandsCalloutPrefix')}
            <strong>{t('method.riskBandsCalloutBold')}</strong>
            {t('method.riskBandsCalloutSuffix')}
          </Callout>
        </section>

        {/* Provenance -------------------------------------------------- */}
        <section className="mt-14">
          <SectionHeading
            eyebrow={t('method.provenanceEyebrow')}
            title={t('method.provenanceTitle')}
            description={t('method.provenanceDescription')}
          />
          <div className="grid gap-4 md:grid-cols-2">
            {TIERS.map((tier) => (
              <Card key={tier.key} padding="lg">
                <ProvenanceChip
                  tier={tier.key}
                  basis={tier.key === 'assumed' ? tier.description : undefined}
                />
                <p className="mt-3 leading-relaxed text-text-600">{tier.description}</p>
              </Card>
            ))}
          </div>
          <Callout tone="info" className="mt-5">
            <span className="font-semibold">{t('method.provenanceCalloutBold')}</span>
            {t('method.provenanceCalloutSuffix')}
          </Callout>
        </section>

        {/* Access ------------------------------------------------------ */}
        <section className="mt-14">
          <SectionHeading
            eyebrow={t('method.accessEyebrow')}
            title={t('method.accessTitle')}
            description={t('method.accessDescription')}
          />
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {ROLES.map((role) => (
              <Card key={role.key} padding="lg">
                <h3 className="text-h3">{role.label}</h3>
                <p className="mt-2 text-sm leading-relaxed text-text-600">{role.description}</p>
                <p className="mt-4 border-t border-border pt-3 text-xs text-text-500">
                  {t('method.permissionsCountTemplate').replace(
                    '{n}',
                    String(role.permissions.length),
                  )}
                </p>
              </Card>
            ))}
          </div>
          <Callout tone="success" className="mt-5">
            {t('method.accessCalloutPrefix')}
            <strong>{t('method.accessCalloutBold')}</strong>
            {t('method.accessCalloutSuffix')}
          </Callout>
        </section>

        <Callout tone="warning" title={t('method.decisionSupportTitle')} className="mt-14">
          {t('method.decisionSupportBody')}
        </Callout>
      </Container>
    </>
  );
}
