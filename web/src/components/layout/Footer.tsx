import React from 'react';
import Link from 'next/link';
import { Container } from '@/components/ui/Container';
import { Emblem } from './GovBanner';
import { getT } from '@/lib/i18n/server';

/** Attribution required by the licence of every source this platform uses. */
const SOURCES = [
  { name: 'District boundaries', detail: 'OCHA / HDX (CC-BY-IGO)', href: 'https://data.humdata.org/dataset/cod-ab-lka' },
  { name: 'Health facilities', detail: '© OpenStreetMap contributors (ODbL)', href: 'https://www.openstreetmap.org/copyright' },
  { name: 'Weather', detail: 'Open-Meteo / ERA5 (CC-BY)', href: 'https://open-meteo.com/' },
  { name: 'Bed density', detail: 'World Bank (CC-BY)', href: 'https://data.worldbank.org/' },
  { name: 'Case notifications', detail: 'Epidemiology Unit · colmozzie (CC0)', href: 'https://www.epid.gov.lk/' },
];

const PLATFORM = [
  { key: 'nav.national', href: '/national' },
  { key: 'public.title', href: '/public' },
  { key: 'nav.method', href: '/method' },
  { key: 'nav.signIn', href: '/signin' },
  { key: 'nav.privacy', href: '/privacy' },
];

const CONTACT = [
  { key: 'footer.ambulance', value: '1990', href: 'tel:1990' },
  { key: 'footer.ndcu', value: '+94 11 288 9871', href: 'tel:+94112889871' },
  { key: 'footer.epid', value: 'epid.gov.lk', href: 'https://www.epid.gov.lk/' },
];

export async function Footer() {
  const t = await getT();
  return (
    <footer className="mt-16">
      <div className="h-0.5 bg-gold-500" aria-hidden />
      <div className="band-navy">
        <Container className="grid gap-10 py-12 md:grid-cols-2 lg:grid-cols-4">
          <div className="lg:col-span-1">
            <div className="flex items-center gap-3">
              <Emblem className="h-10 w-10 text-gold-400" />
              <span className="leading-tight">
                <span className="block font-heading text-lg font-semibold text-white">
                  DengueSentinel
                </span>
                <span className="block text-[11px] uppercase tracking-[0.1em] text-primary-300">
                  {t('site.ministry')}
                </span>
              </span>
            </div>
            <p className="mt-4 text-[13px] leading-relaxed text-primary-200">
              {t('footer.blurb')}
            </p>
          </div>

          <div>
            <h2 className="text-[12px] font-bold uppercase tracking-[0.1em] text-gold-400">
              {t('footer.platform')}
            </h2>
            <ul className="mt-4 space-y-2.5 text-[13px]">
              {PLATFORM.map((link) => (
                <li key={link.href}>
                  <Link href={link.href} className="text-primary-100 hover:text-white hover:underline">
                    {t(link.key)}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h2 className="text-[12px] font-bold uppercase tracking-[0.1em] text-gold-400">
              {t('footer.contact')}
            </h2>
            <ul className="mt-4 space-y-3 text-[13px]">
              {CONTACT.map((item) => (
                <li key={item.key}>
                  <span className="block text-[11px] uppercase tracking-wide text-primary-300">
                    {t(item.key)}
                  </span>
                  <a href={item.href} className="num font-semibold text-white hover:underline">
                    {item.value}
                  </a>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h2 className="text-[12px] font-bold uppercase tracking-[0.1em] text-gold-400">
              {t('footer.sources')}
            </h2>
            <ul className="mt-4 space-y-2.5 text-[13px]">
              {SOURCES.map((source) => (
                <li key={source.name}>
                  <a
                    href={source.href}
                    target="_blank"
                    rel="noreferrer noopener"
                    className="group"
                  >
                    <span className="block font-medium text-primary-100 group-hover:text-white group-hover:underline">
                      {source.name}
                    </span>
                    <span className="block text-[11px] text-primary-300">{source.detail}</span>
                  </a>
                </li>
              ))}
            </ul>
          </div>
        </Container>

        <div className="border-t border-white/15">
          <Container className="flex flex-col gap-2 py-5 text-[12px] text-primary-300 sm:flex-row sm:items-center sm:justify-between">
            <p>
              © {new Date().getFullYear()} {t('footer.rights')}
            </p>
            <p>AI Challenge Sri Lanka 2026</p>
          </Container>
        </div>
      </div>
    </footer>
  );
}

export default Footer;
