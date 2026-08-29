import React from 'react';
import Link from 'next/link';
import { LockClosedIcon } from '@heroicons/react/24/outline';

import { Container } from '@/components/ui/Container';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Callout } from '@/components/ui/Callout';

/**
 * Rendered in place of a staff portal when the viewer may not see it.
 *
 * Says which role the page needs and offers the public view, rather than
 * redirecting: a citizen who followed a link here should land somewhere useful,
 * not be bounced to a login they have no account for.
 */
export function AccessNotice({
  portal,
  requiredRoles,
  signedIn,
  configurationError,
}: {
  portal: string;
  requiredRoles: string;
  signedIn: boolean;
  configurationError?: string | null;
}) {
  return (
    <Container className="py-20">
      <Card padding="lg" className="mx-auto max-w-xl text-center">
        <span className="mx-auto grid h-12 w-12 place-items-center rounded-sm bg-bg-200 text-text-600">
          <LockClosedIcon className="h-6 w-6" aria-hidden />
        </span>
        <h1 className="text-h1 mt-5">{portal} is staff-only</h1>
        <p className="mt-3 text-text-600">
          This portal is available to {requiredRoles}. Public risk information for every
          district needs no account at all.
        </p>

        {configurationError ? (
          <Callout tone="warning" title="Account needs configuration" className="mt-6 text-left">
            {configurationError}
          </Callout>
        ) : null}

        <div className="mt-7 flex flex-wrap justify-center gap-3">
          {!signedIn ? <Button href="/signin">Staff sign in</Button> : null}
          <Button href="/public" variant="outline">
            Check a district instead
          </Button>
        </div>

        <p className="mt-6 text-xs text-text-500">
          Public data here is a deny-by-default subset, not a redaction — these pages are
          built from the permissions a role actually holds, so a bug shows missing
          information rather than exposing hospital occupancy.{' '}
          <Link href="/method" className="text-primary-700 hover:underline">
            How access works
          </Link>
        </p>
      </Card>
    </Container>
  );
}

export default AccessNotice;
