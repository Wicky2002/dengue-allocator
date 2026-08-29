/**
 * Provenance tiers, mirrored from `dengue.platform.provenance`.
 *
 * The platform puts observed counts, model output and planning estimates on the
 * same screen. Rendered identically, a planning estimate borrows the
 * credibility of a measurement -- which is how a decision-support tool causes a
 * bad decision. Every figure in this UI is therefore rendered with a
 * `<ProvenanceChip>` naming which of the three it is.
 */

import constants from '@/generated/constants.json';

export type TierKey = 'observed' | 'modelled' | 'assumed' | 'user_input';

export interface Tier {
  key: TierKey;
  label: string;
  description: string;
}

export const TIERS: Tier[] = constants.provenanceTiers as Tier[];

const BY_KEY = new Map(TIERS.map((t) => [t.key, t]));

export function tier(key: TierKey): Tier {
  const found = BY_KEY.get(key);
  if (!found) throw new Error(`Unknown provenance tier: ${key}`);
  return found;
}

/** Chip styling per tier. Deliberately unlike the risk ramp: provenance is not
 *  a severity, and reusing the risk colours would read as one. */
export function tierClasses(key: TierKey): string {
  return {
    observed: 'bg-slate-100 text-slate-700 ring-1 ring-slate-300',
    modelled: 'bg-primary-50 text-primary-800 ring-1 ring-primary-200',
    assumed: 'bg-violet-50 text-violet-800 ring-1 ring-violet-200',
    user_input: 'bg-bg-200 text-text-600 ring-1 ring-border',
  }[key];
}
