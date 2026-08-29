import React from 'react';
import { NoSymbolIcon } from '@heroicons/react/24/outline';

/**
 * What renders where no public data exists.
 *
 * Live bed occupancy, ICU census, platelet stock, staffing rosters and
 * ambulance positions are not published for Sri Lanka. The platform says so and
 * names the feed that would enable the panel, rather than filling the space
 * with a plausible number -- a fabricated figure in a bed-planning panel is
 * worse than an empty one.
 */
export function NoDataPanel({
  title,
  reason,
  enabledBy,
}: {
  title: string;
  reason: string;
  enabledBy: string;
}) {
  return (
    <div className="flex h-full flex-col justify-center rounded-sm border border-dashed border-border bg-bg-100 p-6 text-center">
      <NoSymbolIcon className="mx-auto h-7 w-7 text-text-400" aria-hidden />
      <p className="mt-3 font-semibold text-text-700">{title}</p>
      <p className="mx-auto mt-2 max-w-md text-sm text-text-600">{reason}</p>
      <p className="mx-auto mt-3 max-w-md text-xs text-text-500">
        <span className="font-medium">Would be enabled by:</span> {enabledBy}
      </p>
    </div>
  );
}

export default NoDataPanel;
