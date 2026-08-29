'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Bars3Icon, XMarkIcon, UserCircleIcon } from '@heroicons/react/24/outline';
import { Container } from '@/components/ui/Container';
import { Emblem } from './GovBanner';
import { useT } from '@/components/i18n/LocaleProvider';
import { can, PUBLIC_PRINCIPAL, type RoleKey } from '@/lib/rbac';

export interface NavItem {
  labelKey: string;
  href: string;
  /** Gated on this permission rather than just "signed in" -- a hospital_staff
   *  account has no reason to see "District operations" in its own nav if
   *  clicking it only leads to an access-denied page. */
  requiresPermission?: string;
}

const NAV: NavItem[] = [
  { labelKey: 'nav.national', href: '/national' },
  { labelKey: 'nav.public', href: '/public' },
  { labelKey: 'nav.hospital', href: '/hospital', requiresPermission: 'view_hospital_readiness' },
  { labelKey: 'nav.moh', href: '/moh', requiresPermission: 'view_district_operations' },
  { labelKey: 'nav.admin', href: '/admin', requiresPermission: 'view_national_operations' },
  { labelKey: 'nav.method', href: '/method' },
];

export function Header({
  signedInAs = null,
  roleLabel = null,
  role = null,
}: {
  signedInAs?: string | null;
  roleLabel?: string | null;
  /** The signed-in account's role, used only to filter staff nav items to what
   *  it actually has permission to open -- never to grant access itself. */
  role?: RoleKey | null;
}) {
  const pathname = usePathname();
  const t = useT();
  const [open, setOpen] = React.useState(false);
  const principal = role ? { ...PUBLIC_PRINCIPAL, role } : PUBLIC_PRINCIPAL;
  const items = NAV.filter((item) => !item.requiresPermission || can(principal, item.requiresPermission));

  return (
    <header className="sticky top-0 z-40 bg-white">
      {/* Institutional identity band. Ministry first, product second: the
          masthead of a state publication names the issuing body. */}
      <div className="band-navy">
        <Container className="flex items-center justify-between gap-4 py-3">
          <Link href="/" className="flex items-center gap-3">
            <Emblem className="h-9 w-9 shrink-0 text-gold-400" />
            <span className="leading-tight">
              <span className="block font-heading text-[19px] font-semibold tracking-tight text-white">
                DengueSentinel
              </span>
              <span className="block text-[11px] uppercase tracking-[0.1em] text-primary-200">
                {t('site.ministry')}
              </span>
            </span>
          </Link>

          <div className="flex items-center gap-3">
            {/* "Staff sign in" is deliberately absent here for a signed-out
                visitor -- this header renders on every public page, so a
                link here would advertise the login form to every anonymous
                visitor and automated scanner. It's still one click away for
                anyone who is actual staff: the footer keeps a plain-text
                link (see Footer.tsx), which is enough for someone who
                already knows to look and doesn't put it in front of a
                casual visitor or a bot walking the nav. The route itself
                (`/signin`) isn't secret -- rate limiting and the account
                boundary are the real protection, not the link's absence --
                this only trims the easiest, laziest way to find it. */}
            {signedInAs ? (
              <>
                <span className="hidden text-right sm:block">
                  <span className="block text-[13px] font-semibold text-white">{signedInAs}</span>
                  <span className="block text-[11px] text-primary-200">{roleLabel}</span>
                </span>
                <Link
                  href="/signout"
                  className="hidden rounded border border-white/30 px-3 py-1.5 text-[13px] font-medium text-white hover:bg-white/10 sm:block"
                >
                  {t('nav.signOut')}
                </Link>
              </>
            ) : null}
            <button
              type="button"
              onClick={() => setOpen((value) => !value)}
              className="rounded p-2 text-white hover:bg-white/10 lg:hidden"
              aria-expanded={open}
              aria-label={open ? t('nav.menuClose') : t('nav.menuOpen')}
            >
              {open ? <XMarkIcon className="h-6 w-6" /> : <Bars3Icon className="h-6 w-6" />}
            </button>
          </div>
        </Container>
      </div>

      {/* National gold hairline, as on a printed circular. */}
      <div className="h-0.5 bg-gold-500" aria-hidden />

      {/* Primary navigation, as a tab rail rather than floating pills. */}
      <nav className="hidden border-b border-border bg-white lg:block" aria-label="Primary">
        <Container>
          <ul className="flex flex-wrap">
            {items.map((item) => {
              const active = pathname === item.href || pathname?.startsWith(`${item.href}/`);
              return (
                <li key={item.href}>
                  <Link
                    href={item.href}
                    aria-current={active ? 'page' : undefined}
                    className={`-mb-px inline-block border-b-[3px] px-4 py-3.5 text-[14px] font-medium transition-colors ${
                      active
                        ? 'border-state-600 text-primary-800'
                        : 'border-transparent text-text-600 hover:border-border hover:text-primary-800'
                    }`}
                  >
                    {t(item.labelKey)}
                  </Link>
                </li>
              );
            })}
          </ul>
        </Container>
      </nav>

      {open ? (
        <nav className="border-b border-border bg-white lg:hidden" aria-label="Primary mobile">
          <Container className="flex flex-col py-1">
            {items.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setOpen(false)}
                className="border-b border-border px-1 py-3 text-sm font-medium text-text-700 last:border-0 hover:text-primary-800"
              >
                {t(item.labelKey)}
              </Link>
            ))}
            {signedInAs ? (
              <Link
                href="/signout"
                onClick={() => setOpen(false)}
                className="inline-flex items-center gap-2 px-1 py-3 text-sm font-semibold text-primary-700"
              >
                <UserCircleIcon className="h-4 w-4" aria-hidden />
                {t('nav.signOut')}
              </Link>
            ) : null}
          </Container>
        </nav>
      ) : null}
    </header>
  );
}

export default Header;
