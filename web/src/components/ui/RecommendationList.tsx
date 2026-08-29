'use client';

import React from 'react';
import {
  ExclamationTriangleIcon,
  ArrowUpCircleIcon,
  CheckCircleIcon,
} from '@heroicons/react/24/outline';
import type { Recommendation } from '@/lib/types';
import { recommendationKey } from '@/lib/i18n/dictionaries';
import { useT } from '@/components/i18n/LocaleProvider';

const urgencyStyles = {
  urgent: { wrap: 'border-red-200 bg-red-50', icon: ExclamationTriangleIcon, tint: 'text-red-600', label: 'Urgent' },
  elevated: { wrap: 'border-amber-200 bg-amber-50', icon: ArrowUpCircleIcon, tint: 'text-amber-600', label: 'Elevated' },
  routine: { wrap: 'border-border bg-white', icon: CheckCircleIcon, tint: 'text-teal-600', label: 'Routine' },
} as const;

/**
 * What to do about the forecast, most urgent first.
 *
 * Each action is shown with its rationale, never alone: an unexplained
 * instruction produced by a model is not actionable, and a reader who cannot
 * see why cannot judge whether it applies to their situation.
 */
export function RecommendationList({
  items,
  limit,
}: {
  items: Recommendation[];
  /** Hotspot cards show only the most urgent few; the full list has its own page. */
  limit?: number;
}) {
  const t = useT();
  const shown = limit ? items.slice(0, limit) : items;
  if (items.length === 0) {
    return <p className="text-sm text-text-500">No specific actions at this risk level.</p>;
  }
  return (
    <ol className="space-y-3">
      {shown.map((item, index) => {
        const style = urgencyStyles[item.urgency] ?? urgencyStyles.routine;
        const Icon = style.icon;
        return (
          <li key={`${item.action}-${index}`} className={`flex gap-3 rounded-sm border p-4 ${style.wrap}`}>
            <Icon className={`h-5 w-5 shrink-0 ${style.tint}`} aria-hidden />
            <div className="min-w-0">
              <p className="font-medium text-text-900">
                {t(`${recommendationKey(item.action)}.action`) === `${recommendationKey(item.action)}.action`
                  ? item.action
                  : t(`${recommendationKey(item.action)}.action`)}
              </p>
              <p className="mt-1 text-sm leading-relaxed text-text-600">
                {t(`${recommendationKey(item.action)}.rationale`) ===
                `${recommendationKey(item.action)}.rationale`
                  ? item.rationale
                  : t(`${recommendationKey(item.action)}.rationale`)}
              </p>
            </div>
          </li>
        );
      })}
      {limit && items.length > limit ? (
        <li className="pl-1 text-[13px] text-text-500">
          + {items.length - limit} further action{items.length - limit === 1 ? '' : 's'} at this
          risk level.
        </li>
      ) : null}
    </ol>
  );
}

export default RecommendationList;
