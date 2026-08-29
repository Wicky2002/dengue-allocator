import type { Metadata } from 'next';
import { redirect } from 'next/navigation';

import { Container } from '@/components/ui/Container';
import { Card } from '@/components/ui/Card';
import { ChangePasswordForm } from '@/components/auth/ChangePasswordForm';
import { getSupabaseServerClient } from '@/lib/supabase/server';
import { getT } from '@/lib/i18n/server';

/**
 * Never prerendered, and never reached voluntarily -- middleware redirects
 * here on every request while `user_metadata.must_change_password` is set
 * (a temporary password from account creation or an admin's reset), and
 * away from here otherwise there'd be nothing that could ever clear it.
 * Loading this page directly with no session just bounces to /signin, same
 * as any other staff route.
 */
export const dynamic = 'force-dynamic';

export const metadata: Metadata = {
  title: 'Set a new password',
  robots: { index: false, follow: false },
};

export default async function ChangePasswordPage() {
  const supabase = await getSupabaseServerClient();
  if (!supabase) redirect('/signin');

  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) redirect('/signin');

  const t = await getT();

  return (
    <Container className="py-16">
      <Card padding="lg" className="mx-auto max-w-md">
        <h1 className="text-h1">{t('changePassword.title')}</h1>
        <p className="mt-3 text-sm leading-relaxed text-text-600">
          {t('changePassword.description')}
        </p>
        <div className="mt-6">
          <ChangePasswordForm />
        </div>
      </Card>
    </Container>
  );
}
