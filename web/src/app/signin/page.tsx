import type { Metadata } from 'next';
import Link from 'next/link';
import { redirect } from 'next/navigation';
import { LockClosedIcon } from '@heroicons/react/24/outline';

import { Container } from '@/components/ui/Container';
import { Card } from '@/components/ui/Card';
import { Callout } from '@/components/ui/Callout';
import { SignInForm } from '@/components/auth/SignInForm';
import { getSession, isAuthConfigured } from '@/lib/session';
import { ROLES } from '@/lib/rbac';

/**
 * Never prerendered.
 *
 * What this page shows depends on who is asking. With Supabase configured the
 * `cookies()` read already forces this, but on a deployment with auth switched
 * off the page would otherwise be statically cached — and a cached shell is one
 * configuration change away from being served to a signed-in user.
 */
export const dynamic = 'force-dynamic';

export const metadata: Metadata = { title: 'Staff sign in' };

export default async function SignInPage() {
  const session = await getSession();
  if (session.signedIn && !session.configurationError) redirect('/national');

  return (
    <Container className="py-16">
      <div className="mx-auto grid max-w-5xl gap-10 lg:grid-cols-2">
        <div>
          <span className="grid h-12 w-12 place-items-center rounded-sm bg-primary-50 text-primary-700">
            <LockClosedIcon className="h-6 w-6" aria-hidden />
          </span>
          <h1 className="text-h1 mt-5">Staff sign in</h1>
          <p className="mt-3 leading-relaxed text-text-600">
            Public risk information needs no account —{' '}
            <Link href="/public" className="font-medium text-primary-700 hover:underline">
              check your district
            </Link>{' '}
            without signing in. An account is for hospital, MOH and Ministry staff, and
            determines both what you can do and which districts you can see.
          </p>

          <dl className="mt-8 space-y-4">
            {ROLES.filter((role) => role.key !== 'public').map((role) => (
              <div key={role.key} className="rounded-sm border border-border bg-white p-4 shadow-card">
                <dt className="font-semibold text-text-900">{role.label}</dt>
                <dd className="mt-1 text-sm text-text-600">{role.description}</dd>
              </div>
            ))}
          </dl>
        </div>

        <div>
          <Card padding="lg">
            {!isAuthConfigured() ? (
              <Callout tone="warning" title="Sign-in is not configured here" className="mb-6">
                This deployment has no Supabase credentials. Set{' '}
                <code className="font-mono text-xs">NEXT_PUBLIC_SUPABASE_URL</code> and{' '}
                <code className="font-mono text-xs">NEXT_PUBLIC_SUPABASE_ANON_KEY</code> in{' '}
                <code className="font-mono text-xs">web/.env.local</code>, and create the
                profiles table from <code className="font-mono text-xs">supabase/schema.sql</code>.
              </Callout>
            ) : null}

            {session.configurationError ? (
              <Callout tone="danger" title="Account needs configuration" className="mb-6">
                {session.configurationError}
              </Callout>
            ) : null}

            <SignInForm />

            <p className="mt-6 border-t border-border pt-4 text-xs leading-relaxed text-text-500">
              Accounts are created by a national administrator, not by self-registration.
              Access is scoped to your own facility or district — signing in does not widen
              what the platform will show you beyond that.
            </p>
          </Card>
        </div>
      </div>
    </Container>
  );
}
