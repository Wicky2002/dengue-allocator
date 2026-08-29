'use client';

import React from 'react';
import { bandClasses, classify } from '@/lib/risk';
import { useT } from '@/components/i18n/LocaleProvider';

/** The four-band risk level for one district, from its forecast incidence. */
export function RiskPill({
  incidence,
  className = '',
}: {
  incidence: number | null | undefined;
  className?: string;
}) {
  const t = useT();
  const band = classify(incidence);
  // The band labels come from the engine's constants, in English. Translate at
  // render rather than in the export: the four names are UI text, while the
  // thresholds and colours they belong to are engine facts.
  const label = t(`risk.${band.key}`);
  return (
    <span
      className={`inline-flex items-center gap-1.5 whitespace-nowrap rounded-sm px-2 py-0.5 text-[12px] font-bold uppercase tracking-wide ${bandClasses(band.key)} ${className}`.trim()}
    >
      <span aria-hidden className="h-1.5 w-1.5 rounded-full" style={{ background: band.colour }} />
      {label}
    </span>
  );
}

export default RiskPill;
