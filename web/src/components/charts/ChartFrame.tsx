'use client';

import React from 'react';
import { ProvenanceChip } from '@/components/ui/ProvenanceChip';
import type { TierKey } from '@/lib/provenance';

/** Consistent framing for every chart: title, provenance, and a caption that
 *  says how to read it. A chart with no stated basis is exactly the failure
 *  mode this platform exists to avoid. */
export function ChartFrame({
  title,
  tier,
  basis,
  caption,
  children,
  className = '',
}: {
  title: string;
  tier: TierKey;
  basis?: string;
  caption?: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <figure className={`rounded-sm border border-border bg-white p-5 shadow-card ${className}`.trim()}>
      <figcaption className="mb-4 flex items-start justify-between gap-3">
        <h3 className="text-h3">{title}</h3>
        <ProvenanceChip tier={tier} basis={basis} />
      </figcaption>
      {children}
      {caption ? <p className="mt-3 text-xs leading-relaxed text-text-500">{caption}</p> : null}
    </figure>
  );
}

export default ChartFrame;
