import type { Metadata } from 'next';

import { Container } from '@/components/ui/Container';
import { Card } from '@/components/ui/Card';
import { Callout } from '@/components/ui/Callout';
import { PageHeader } from '@/components/layout/PageHeader';
import { SectionHeading } from '@/components/ui/SectionHeading';

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
export default function PrivacyPage() {
  return (
    <>
      <PageHeader
        crumbs={[{ label: 'Data protection notice' }]}
        eyebrow="Legal"
        title="Data protection notice"
        description="What this platform collects, why, how long it is kept, and how to ask about your own data — under Sri Lanka's Personal Data Protection Act No. 9 of 2022."
      />

      <Container className="max-w-3xl py-12">
        <Callout tone="info" className="mb-10">
          This notice describes the platform as built. If anything below stops matching what the
          running system actually does, the system is wrong and this notice is not — update the
          code, not this page, to bring them back into agreement.
        </Callout>

        <section className="mb-10">
          <SectionHeading eyebrow="Controller" title="Who operates this platform" />
          <p className="leading-relaxed text-text-600">
            The Ministry of Health, Sri Lanka, is the controller for the personal data described
            below. Requests concerning your own data — access, correction, or a question about how
            it is used — should be directed to the Ministry through the contact channels in the
            footer of this site.
          </p>
        </section>

        <section className="mb-10">
          <SectionHeading eyebrow="What is collected" title="The two kinds of data on this platform" />
          <div className="grid gap-5 md:grid-cols-2">
            <Card padding="lg" accent="navy">
              <h3 className="text-h3">Public risk information</h3>
              <p className="mt-2 text-sm leading-relaxed text-text-600">
                District-level forecasts, case counts and risk bands. This is aggregate
                epidemiological data — no individual is identified or identifiable in it, and no
                personal data is collected from a visitor to view it. Choosing a district or
                a language, and any alert preference you set, is stored only in your own browser
                (see &ldquo;Alert preferences&rdquo; below) and never reaches this platform&rsquo;s
                servers.
              </p>
            </Card>
            <Card padding="lg" accent="navy">
              <h3 className="text-h3">Staff accounts</h3>
              <p className="mt-2 text-sm leading-relaxed text-text-600">
                For hospital, district-operations and administration accounts: an email address,
                a display name, an assigned role, and a district or facility scope. Accounts are
                created by an administrator, not by self-registration, and this is the minimum
                needed to authenticate a member of staff and restrict what they can see to their
                own facility or district.
              </p>
            </Card>
          </div>
        </section>

        <section className="mb-10">
          <SectionHeading eyebrow="Legal basis" title="Why this processing is lawful" />
          <p className="leading-relaxed text-text-600">
            Public risk information is published in the exercise of the Ministry&rsquo;s public
            health function — no consent is sought or needed to view it, in the same way a
            weekly epidemiological bulletin needs none. Staff account data is processed under the
            same public function, on the basis that it is necessary to operate a restricted-access
            system for vector-control planning; it is not used for any purpose beyond operating
            this platform.
          </p>
        </section>

        <section className="mb-10">
          <SectionHeading eyebrow="Audit log" title="What is recorded about a staff sign-in" />
          <p className="leading-relaxed text-text-600">
            Signing in, signing out, and viewing a staff portal are recorded — timestamp, account
            email, role, district scope at the time, and which page was viewed. This exists to let
            an administrator answer &ldquo;who looked at what, and when&rdquo; if that is ever
            needed, and is visible only to national-administrator accounts. It does not record
            what any account did on a page beyond which page it opened, and it is never used for
            performance monitoring or any purpose beyond that accountability record.
          </p>
        </section>

        <section className="mb-10">
          <SectionHeading eyebrow="Retention" title="How long data is kept" />
          <dl className="space-y-4">
            <div className="rounded-sm border border-border bg-white p-4 shadow-card">
              <dt className="font-semibold text-text-900">Staff account records</dt>
              <dd className="mt-1 text-sm text-text-600">
                Kept for the lifetime of the account, and removed by an administrator when access
                is withdrawn.
              </dd>
            </div>
            <div className="rounded-sm border border-border bg-white p-4 shadow-card">
              <dt className="font-semibold text-text-900">Audit log entries</dt>
              <dd className="mt-1 text-sm text-text-600">
                Deleted automatically after 365 days, once an operator has enabled the scheduled
                purge (<code className="font-mono text-xs">supabase/audit_log_retention.sql</code>).
                Until that has been run on this deployment, entries are retained indefinitely — ask
                your administrator whether it has been enabled.
              </dd>
            </div>
            <div className="rounded-sm border border-border bg-white p-4 shadow-card">
              <dt className="font-semibold text-text-900">Aggregate epidemiological data</dt>
              <dd className="mt-1 text-sm text-text-600">
                Retained as a historical record — it is never personal data, so PDPA retention
                limits on personal data do not apply to it.
              </dd>
            </div>
          </dl>
        </section>

        <section className="mb-10">
          <SectionHeading eyebrow="Your rights" title="Access, correction, and questions" />
          <p className="leading-relaxed text-text-600">
            Under the PDPA, you may ask what personal data this platform holds about you, ask for
            it to be corrected if it is wrong, and ask questions about how it is used. For a staff
            account, the fastest route is your own administrator; for anything else, use the
            contact details in the footer of this site.
          </p>
        </section>

        <Callout tone="warning" title="What this notice does not cover">
          This page states the platform&rsquo;s own data handling. It does not cover data held by
          the Epidemiology Unit, hospitals, or other bodies whose published statistics this
          platform reads and displays — those bodies are separate controllers for their own
          records, and requests about them should go to them directly.
        </Callout>
      </Container>
    </>
  );
}
