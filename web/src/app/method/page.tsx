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

export const metadata: Metadata = {
  title: 'How it works',
  description:
    'The three-stage engine behind DengueSentinel: probabilistic forecasting, mechanistic effect estimation, and constrained allocation.',
};

export default async function MethodPage() {
  const [meta, scores] = await Promise.all([getMeta(), getScores()]);
  const metric = scores.some((row) => row.metric === 'pinball_loss') ? 'pinball_loss' : 'mae';
  const horizon = meta?.effect_horizon_weeks ?? 2;
  const comparison = modelComparison(scores, metric, 2).slice(0, 3);

  return (
    <>
      <PageHeader
        crumbs={[{ label: 'How it works' }]}
        eyebrow="Method"
        title="How this platform decides anything"
        description="Three stages, each answering a question the previous one cannot. Knowing which district will have the most cases is not the same as knowing where a team averts the most."
        meta={[
          { label: 'Panel', value: meta?.panel_source ?? '—' },
          { label: 'District-weeks', value: num(meta?.panel_rows ?? null) },
          { label: 'Last run', value: shortDate(meta?.generated_at ?? null) },
        ]}
      />

      <Container className="py-12">
        {/* Stages ------------------------------------------------------ */}
        <SectionHeading
          eyebrow="The engine"
          title="Forecast → causal effect → allocation"
          description="Each stage writes an artifact. The dashboard reads those artifacts and never recomputes them, which is why moving a slider here is instant during an outbreak."
        />

        <ol className="space-y-6">
          {[
            {
              stage: 'Stage 1',
              title: 'Probabilistic district forecasts',
              body: 'A quantile model produces a median and an 80% interval for each district, two to four weeks ahead. Every baseline — seasonal naive, SARIMA, gradient boosting — is refit at each rolling-origin fold, so no model ever sees data from after the week it is predicting. The comparison table on the national overview is that backtest, not a claim.',
              detail: comparison.length
                ? `Best on ${metric.replace('_', ' ')} at 2 weeks: ${comparison
                    .map((row) => `${row.model} (${row.value.toFixed(3)})`)
                    .join(', ')}.`
                : undefined,
              tier: 'modelled' as const,
            },
            {
              stage: 'Stage 2',
              title: 'Mechanistic intervention effect',
              body: 'A compartmental SEI-SIR model is fitted per district against that district’s own history, then re-integrated with vector control applied. The difference between the two integrations is the cases averted for a given number of team-weeks — a causal quantity, not a correlation read off the forecast.',
              detail: `Effects are computed over a ${horizon}-week horizon and cached as a curve per district, which is what makes the marginal return of the next team-week available instantly.`,
              tier: 'modelled' as const,
            },
            {
              stage: 'Stage 3',
              title: 'Constrained allocation',
              body: 'An integer programme distributes a fixed weekly team budget to maximise total expected cases averted, subject to the effect curves from Stage 2 and an equity floor for facility-poor districts. The floor is what stops the optimiser from writing off small, under-served districts whose absolute case counts can never compete with Colombo’s.',
              detail: 'The whole budget sweep is solved offline and cached, so the budget slider indexes solutions rather than re-solving.',
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
            eyebrow="Why forecast at all"
            title="Reacting to notifications is reacting to a fortnight-old picture"
          />
          <Card padding="lg">
            <p className="leading-relaxed text-text-600">
              By the time a surge appears in weekly notification data, transmission has already
              been running for two to three weeks: a mosquito acquires the virus, the extrinsic
              incubation period passes, a person is infected, the intrinsic incubation period
              passes, they seek care, and the case is notified. Teams dispatched at that point
              are treating a wave that has already broken.
            </p>
            <p className="mt-4 leading-relaxed text-text-600">
              Rainfall is what makes an earlier signal possible. Rain fills containers, larvae
              develop, adults emerge, and only then does transmission rise — a lag of roughly
              six to eight weeks that the forecast exploits.
            </p>
          </Card>
        </section>

        {/* Risk bands -------------------------------------------------- */}
        <section className="mt-14">
          <SectionHeading
            eyebrow="Risk bands"
            title="Why incidence, not case counts"
            description="Colombo has 2.48 million residents and Mullaitivu around 100,000. Ranking districts by raw counts would paint Colombo red every week of the year and leave a genuine Mullaitivu outbreak green."
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
                    ? 'Below 1.5'
                    : `${band.threshold} and above`}{' '}
                  per 100,000 per week
                </p>
              </Card>
            ))}
          </div>
          <Callout tone="warning" className="mt-5">
            These are <strong>operational planning thresholds, not a clinical standard</strong>.
            No internationally agreed incidence cut-off defines a dengue outbreak — published
            thresholds are endemicity-specific and usually derived per country. They were
            recalibrated against the real district-week distribution, and they are exposed as
            constants so they can be recalibrated again.
          </Callout>
        </section>

        {/* Provenance -------------------------------------------------- */}
        <section className="mt-14">
          <SectionHeading
            eyebrow="Provenance"
            title="Every quantity states what it is"
            description="Enforced in code, not by discipline: a quantity tagged as a planning estimate cannot be constructed in the engine without stating its basis."
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
            <span className="font-semibold">Where no public data exists, the platform says so.</span>{' '}
            Live bed occupancy, ICU census, platelet stock, staffing rosters and ambulance
            positions are not published for Sri Lanka. Those panels render an explanation and
            name the feed that would enable them, rather than a number that looks plausible.
          </Callout>
        </section>

        {/* Access ------------------------------------------------------ */}
        <section className="mt-14">
          <SectionHeading
            eyebrow="Access"
            title="Permissions are additive; scope is separate"
            description="A hospital administrator and an MOH officer can hold overlapping permissions while seeing entirely different rows — one is scoped to a facility, the other to a district. Collapsing the two into a single level is the usual way a health dashboard leaks data across regions."
          />
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {ROLES.map((role) => (
              <Card key={role.key} padding="lg">
                <h3 className="text-h3">{role.label}</h3>
                <p className="mt-2 text-sm leading-relaxed text-text-600">{role.description}</p>
                <p className="mt-4 border-t border-border pt-3 text-xs text-text-500">
                  {role.permissions.length} permissions
                </p>
              </Card>
            ))}
          </div>
          <Callout tone="success" className="mt-5">
            The public pages are a <strong>deny-by-default subset, not a redaction</strong>. They
            are built from permissions the public role actually holds, rather than by computing
            the full picture and hiding parts of it — so a bug here shows missing information
            rather than exposing hospital occupancy.
          </Callout>
        </section>

        <Callout tone="warning" title="Decision support, not a clinical tool" className="mt-14">
          Nothing on this platform diagnoses a patient or prescribes treatment. It describes
          district-level risk and resource implications to help allocate finite public health
          capacity — and every figure it shows is only as good as the assumption stated beside it.
        </Callout>
      </Container>
    </>
  );
}
