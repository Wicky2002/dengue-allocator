/** Number, date and unit formatting. One place, so a figure reads the same everywhere. */

const NUMBER = new Intl.NumberFormat('en-LK');
const COMPACT = new Intl.NumberFormat('en-LK', { notation: 'compact', maximumFractionDigits: 1 });

/**
 * Format a count.
 *
 * A null renders as an em dash, never as 0: a missing forecast and a forecast of
 * zero cases mean opposite things to whoever is reading the table.
 */
export function num(value: number | null | undefined, digits = 0): string {
  if (value == null || Number.isNaN(value)) return '—';
  return digits === 0
    ? NUMBER.format(Math.round(value))
    : value.toLocaleString('en-LK', { minimumFractionDigits: digits, maximumFractionDigits: digits });
}

export function compact(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return '—';
  return COMPACT.format(value);
}

export function pct(value: number | null | undefined, digits = 0): string {
  if (value == null || Number.isNaN(value)) return '—';
  return `${value.toFixed(digits)}%`;
}

export function signedPct(value: number | null | undefined, digits = 0): string {
  if (value == null || Number.isNaN(value)) return '—';
  const sign = value > 0 ? '+' : '';
  return `${sign}${value.toFixed(digits)}%`;
}

/** LKR, compacted -- budget figures here run to hundreds of millions. */
export function lkr(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return '—';
  if (Math.abs(value) >= 1e9) return `LKR ${(value / 1e9).toFixed(2)} bn`;
  if (Math.abs(value) >= 1e6) return `LKR ${(value / 1e6).toFixed(1)} M`;
  return `LKR ${NUMBER.format(Math.round(value))}`;
}

/** An ISO date as "12 Aug 2026". */
export function shortDate(value: string | null | undefined): string {
  if (!value) return '—';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '—';
  return date.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
}

/** An ISO date as "12 Aug" -- for dense chart axes. */
export function axisDate(value: string | null | undefined): string {
  if (!value) return '';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '';
  return date.toLocaleDateString('en-GB', { day: 'numeric', month: 'short' });
}

export function isoWeekLabel(value: string | null | undefined): string {
  if (!value) return '—';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '—';
  return `week of ${shortDate(value)}`;
}
