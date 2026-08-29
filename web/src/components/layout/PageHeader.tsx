import React from 'react';
import Link from 'next/link';
import { ChevronRightIcon } from '@heroicons/react/24/outline';
import { Container } from '@/components/ui/Container';
import { getT } from '@/lib/i18n/server';

export interface Crumb {
  label: string;
  href?: string;
}

/**
 * The banner every portal page opens with.
 *
 * Carries the same three things a printed departmental notice does: where this
 * sits in the hierarchy, what it is, and the provenance of the run behind it.
 */
export async function PageHeader({
  eyebrow,
  title,
  description,
  meta = [],
  crumbs = [],
  children,
}: {
  eyebrow?: string;
  title: string;
  description?: string;
  meta?: { label: string; value: string }[];
  crumbs?: Crumb[];
  children?: React.ReactNode;
}) {
  const t = await getT();
  return (
    <div className="band-navy border-b-2 border-gold-500">
      <Container className="py-8 lg:py-11">
        <nav aria-label="Breadcrumb" className="mb-5">
          <ol className="flex flex-wrap items-center gap-1 text-[12px] text-primary-200">
            <li>
              <Link href="/" className="hover:text-white hover:underline">
                {t('nav.home')}
              </Link>
            </li>
            {crumbs.map((crumb) => (
              <li key={crumb.label} className="flex items-center gap-1">
                <ChevronRightIcon className="h-3 w-3 text-primary-400" aria-hidden />
                {crumb.href ? (
                  <Link href={crumb.href} className="hover:text-white hover:underline">
                    {crumb.label}
                  </Link>
                ) : (
                  <span className="text-white">{crumb.label}</span>
                )}
              </li>
            ))}
          </ol>
        </nav>

        {eyebrow ? (
          <p className="text-eyebrow uppercase text-gold-400">{eyebrow}</p>
        ) : null}
        <h1 className="text-h1 mt-2 max-w-4xl text-white">{title}</h1>
        {description ? (
          <p className="mt-3 max-w-3xl leading-relaxed text-primary-100">{description}</p>
        ) : null}

        {meta.length > 0 ? (
          <dl className="mt-7 flex flex-wrap gap-x-10 gap-y-4 border-t border-white/15 pt-5">
            {meta.map((item) => (
              <div key={item.label}>
                <dt className="text-[11px] uppercase tracking-[0.1em] text-primary-300">
                  {item.label}
                </dt>
                <dd className="num mt-0.5 text-[14px] font-semibold text-white">{item.value}</dd>
              </div>
            ))}
          </dl>
        ) : null}

        {children ? <div className="mt-6">{children}</div> : null}
      </Container>
    </div>
  );
}

export default PageHeader;
