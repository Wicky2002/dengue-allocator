import React from 'react';
import Link from 'next/link';
import { LockClosedIcon } from '@heroicons/react/24/outline';

import { Container } from '@/components/ui/Container';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Callout } from '@/components/ui/Callout';
import { getT } from '@/lib/i18n/server';

/**
 * Rendered in place of a staff portal when the viewer may not see it.
 *
 * Says which role the page needs and offers the public view, rather than
 * redirecting: a citizen who followed a link here should land somewhere useful,
 * not be bounced to a login they have no account for. Reachable by anyone
 * following an old link or bookmark, so unlike the staff portals themselves
 * this is translated -- `portalKey` and `requiredRolesKey` are dictionary
 * keys, not literal text, resolved here rather than passed pre-translated so
 * every caller stays a plain server component.
 */
export async function AccessNotice({
  portalKey,
  requiredRolesKey,
  signedIn,
  configurationError,
}: {
  portalKey: string;
  requiredRolesKey: string;
  signedIn: boolean;
  configurationError?: string | null;
}) {
  const t = await getT();
  const portal = t(portalKey);

  return (
    <Container className="py-20">
      <Card padding="lg" className="mx-auto max-w-xl text-center">
        <span className="mx-auto grid h-12 w-12 place-items-center rounded-sm bg-bg-200 text-text-600">
          <LockClosedIcon className="h-6 w-6" aria-hidden />
        </span>
        <h1 className="text-h1 mt-5">{t('notice.staffOnlyTemplate').replace('{portal}', portal)}</h1>
        <p className="mt-3 text-text-600">
          {t('notice.availableToTemplate').replace('{roles}', t(requiredRolesKey))}
        </p>

        {configurationError ? (
          <Callout tone="warning" title="Account needs configuration" className="mt-6 text-left">
            {configurationError}
          </Callout>
        ) : null}

        <div className="mt-7 flex flex-wrap justify-center gap-3">
          {!signedIn ? <Button href="/signin">{t('nav.signIn')}</Button> : null}
          <Button href="/public" variant="outline">
            {t('notice.checkDistrict')}
          </Button>
        </div>

        <p className="mt-6 text-xs text-text-500">
          {t('notice.footerPrefix')}
          <strong>{t('notice.footerBold')}</strong>
          {t('notice.footerSuffix')}{' '}
          <Link href="/method" className="text-primary-700 hover:underline">
            {t('notice.howAccessWorks')}
          </Link>
        </p>
      </Card>
    </Container>
  );
}

export default AccessNotice;
