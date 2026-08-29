'use client';

import React from 'react';
import { tier, tierClasses, type TierKey } from '@/lib/provenance';
import { useT } from '@/components/i18n/LocaleProvider';

/**
 * The chip that says what kind of number sits next to it.
 *
 * This is the single most important component in the UI. Observed counts,
 * model output and planning estimates appear on the same screen throughout this
 * platform; rendered identically, the planning estimate borrows the credibility
 * of the measurement. The chip is what keeps them distinguishable, and its
 * `title` carries the full definition for anyone who hovers.
 */
export function ProvenanceChip({
  tier: key,
  basis,
  className = '',
}: {
  tier: TierKey;
  /** Required for `assumed`: what published parameter the estimate rests on. */
  basis?: string;
  className?: string;
}) {
  const definition = tier(key);
  const translate = useT();
  // The tier names are UI text; their definitions are engine facts. Only the
  // name is translated -- the hover description stays in the language the
  // engine states it in, which is the language the provenance rule is written
  // in and audited against.
  const label = translate(`prov.${key}`);
  if (key === 'assumed' && !basis) {
    // The engine refuses to construct an ASSUMED Quantity without a basis, for
    // the reason in `dengue.platform.provenance`: an unexplained planning
    // estimate is indistinguishable from a fabricated number. The UI holds the
    // same line rather than rendering a bare "Planning estimate" chip.
    throw new Error('A "Planning estimate" chip must state its basis.');
  }
  return (
    <span
      title={
        basis
          ? `${label}. ${definition.description} Basis: ${basis}`
          : `${label}. ${definition.description}`
      }
      className={`inline-flex cursor-help items-center gap-1 rounded-sm px-1.5 py-0.5 text-[10.5px] font-bold uppercase tracking-[0.06em] ${tierClasses(key)} ${className}`.trim()}
    >
      {label}
    </span>
  );
}

export default ProvenanceChip;
