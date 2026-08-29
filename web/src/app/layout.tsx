import type { Metadata, Viewport } from 'next';
import {
  Source_Serif_4,
  Public_Sans,
  IBM_Plex_Mono,
  Noto_Sans_Sinhala,
  Noto_Sans_Tamil,
} from 'next/font/google';

import './globals.css';
import { GovBanner } from '@/components/layout/GovBanner';
import { Header } from '@/components/layout/Header';
import { Footer } from '@/components/layout/Footer';
import { getSession } from '@/lib/session';
import { getDictionary, getLocale } from '@/lib/i18n/server';
import { LocaleProvider } from '@/components/i18n/LocaleProvider';
import { role as roleDef } from '@/lib/rbac';

// Source Serif for headings and Public Sans for the interface. Public Sans is
// the US Web Design System's face -- drawn for government interfaces, legible
// at small sizes on poor screens, and with the tabular figures every ranked
// table here depends on. The serif carries the authority of a printed circular
// without making body copy harder to read at density.
const heading = Source_Serif_4({
  subsets: ['latin'],
  weight: ['400', '600', '700'],
  variable: '--font-heading',
  display: 'swap',
});
const body = Public_Sans({
  subsets: ['latin'],
  weight: ['400', '500', '600', '700'],
  variable: '--font-body',
  display: 'swap',
});
// Public Sans and Source Serif carry no Sinhala or Tamil glyphs. Without these
// the other two official languages fall back to whatever the operating system
// happens to have, which on many machines is nothing at all. Each face declares
// its own unicode-range, so an English page never downloads either file.
const sinhala = Noto_Sans_Sinhala({
  subsets: ['sinhala'],
  weight: ['400', '500', '600', '700'],
  variable: '--font-sinhala',
  display: 'swap',
});
const tamil = Noto_Sans_Tamil({
  subsets: ['tamil'],
  weight: ['400', '500', '600', '700'],
  variable: '--font-tamil',
  display: 'swap',
});

const mono = IBM_Plex_Mono({
  subsets: ['latin'],
  weight: ['400', '500'],
  variable: '--font-mono',
  display: 'swap',
});

export const metadata: Metadata = {
  title: {
    default: 'DengueSentinel — national dengue decision support, Sri Lanka',
    template: '%s · DengueSentinel',
  },
  description:
    'District dengue forecasts, intervention effects and vector-control team allocation for Sri Lanka. Every figure states whether it is observed, modelled, or a planning estimate.',
};

export const viewport: Viewport = {
  themeColor: '#0F2440',
};

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  const [session, locale, dictionary] = await Promise.all([
    getSession(),
    getLocale(),
    getDictionary(),
  ]);
  const signedIn = session.signedIn && session.principal.role !== 'public';
  const t = (key: string) => dictionary[key] ?? key;
  return (
    <html lang={locale} className={`${heading.variable} ${body.variable} ${mono.variable} ${sinhala.variable} ${tamil.variable}`}>
      <body className="flex min-h-screen flex-col">
        <LocaleProvider locale={locale} dictionary={dictionary}>
        <a
          href="#main"
          className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-sm focus:bg-primary-800 focus:px-4 focus:py-2 focus:text-white"
        >
          {t('nav.skip')}
        </a>
        <GovBanner />
        <Header
          signedInAs={signedIn ? session.principal.displayName : null}
          roleLabel={signedIn ? roleDef(session.principal.role).label : null}
          role={signedIn ? session.principal.role : null}
        />
        <main id="main" className="flex-1">
          {children}
        </main>
        <Footer />
        </LocaleProvider>
      </body>
    </html>
  );
}
