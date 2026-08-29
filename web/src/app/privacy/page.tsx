import type { Metadata } from 'next';

import { Container } from '@/components/ui/Container';
import { Card } from '@/components/ui/Card';
import { Callout } from '@/components/ui/Callout';
import { PageHeader } from '@/components/layout/PageHeader';
import { SectionHeading } from '@/components/ui/SectionHeading';
import { getT } from '@/lib/i18n/server';

export const metadata: Metadata = {
  title: 'Data protection notice',
  description:
    'What DengueSentinel collects, why, how long it is kept, and how to exercise your rights under Sri Lanka\'s Personal Data Protection Act No. 9 of 2022.',
};

/**
 * The PDPA 2022 transparency notice.
 *
 * This is the one piece of PDPA compliance that is actually a publishable
 * document rather than an internal policy: Sri Lanka's Personal Data
 * Protection Act requires a controller to state, in plain terms, what it
 * collects, on what legal basis, for how long, and who to contact about it.
 * Everything else the Act requires -- a designated point of contact, a
 * retention schedule enforced in practice, a breach procedure -- is
 * organisational, not a page; this page is where that policy is stated for
 * the public to read, and it has to stay in sync with what the platform
 * actually does, not describe an aspiration.
 */
export default async function PrivacyPage() {
  const t = await getT();

  return (
    <>
      <PageHeader
        crumbs={[{ label: t('nav.privacy') }]}
        eyebrow={t('privacy.eyebrow')}
        title={t('nav.privacy')}
        description={t('privacy.description')}
      />

      <Container className="max-w-3xl py-12">
        <Callout tone="info" className="mb-10">
          {t('privacy.notice')}
        </Callout>

        <section className="mb-10">
          <SectionHeading eyebrow={t('privacy.controllerEyebrow')} title={t('privacy.controllerTitle')} />
          <p className="leading-relaxed text-text-600">{t('privacy.controllerBody')}</p>
        </section>

        <section className="mb-10">
          <SectionHeading
            eyebrow={t('privacy.collectedEyebrow')}
            title={t('privacy.collectedTitle')}
          />
          <div className="grid gap-5 md:grid-cols-2">
            <Card padding="lg" accent="navy">
              <h3 className="text-h3">{t('privacy.publicDataTitle')}</h3>
              <p className="mt-2 text-sm leading-relaxed text-text-600">
                {t('privacy.publicDataBody')}
              </p>
            </Card>
            <Card padding="lg" accent="navy">
              <h3 className="text-h3">{t('privacy.staffDataTitle')}</h3>
              <p className="mt-2 text-sm leading-relaxed text-text-600">
                {t('privacy.staffDataBody')}
              </p>
            </Card>
          </div>
        </section>

        <section className="mb-10">
          <SectionHeading
            eyebrow={t('privacy.legalBasisEyebrow')}
            title={t('privacy.legalBasisTitle')}
          />
          <p className="leading-relaxed text-text-600">{t('privacy.legalBasisBody')}</p>
        </section>

        <section className="mb-10">
          <SectionHeading eyebrow={t('privacy.auditEyebrow')} title={t('privacy.auditTitle')} />
          <p className="leading-relaxed text-text-600">{t('privacy.auditBody')}</p>
        </section>

        <section className="mb-10">
          <SectionHeading
            eyebrow={t('privacy.retentionEyebrow')}
            title={t('privacy.retentionTitle')}
          />
          <dl className="space-y-4">
            <div className="rounded-sm border border-border bg-white p-4 shadow-card">
              <dt className="font-semibold text-text-900">{t('privacy.retentionStaffTitle')}</dt>
              <dd className="mt-1 text-sm text-text-600">{t('privacy.retentionStaffBody')}</dd>
            </div>
            <div className="rounded-sm border border-border bg-white p-4 shadow-card">
              <dt className="font-semibold text-text-900">{t('privacy.retentionAuditTitle')}</dt>
              <dd className="mt-1 text-sm text-text-600">
                {t('privacy.retentionAuditBodyPrefix')}
                <code className="font-mono text-xs">supabase/audit_log_retention.sql</code>
                {t('privacy.retentionAuditBodySuffix')}
              </dd>
            </div>
            <div className="rounded-sm border border-border bg-white p-4 shadow-card">
              <dt className="font-semibold text-text-900">{t('privacy.retentionAggTitle')}</dt>
              <dd className="mt-1 text-sm text-text-600">{t('privacy.retentionAggBody')}</dd>
            </div>
          </dl>
        </section>

        <section className="mb-10">
          <SectionHeading eyebrow={t('privacy.rightsEyebrow')} title={t('privacy.rightsTitle')} />
          <p className="leading-relaxed text-text-600">{t('privacy.rightsBody')}</p>
        </section>

        <Callout tone="warning" title={t('privacy.notCoveredTitle')}>
          {t('privacy.notCoveredBody')}
        </Callout>
      </Container>
    </>
  );
}
