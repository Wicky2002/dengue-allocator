import React from 'react';
import {
  CheckCircleIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
  BeakerIcon,
} from '@heroicons/react/24/outline';

export type CalloutTone = 'info' | 'warning' | 'danger' | 'success' | 'simulated';

/** Official notices: a heavy left rule and a flat tint, as on a printed form. */
const tones: Record<CalloutTone, { wrap: string; icon: React.ElementType; iconClass: string }> = {
  info: { wrap: 'border-l-primary-700 bg-primary-50 text-primary-900', icon: InformationCircleIcon, iconClass: 'text-primary-700' },
  warning: { wrap: 'border-l-amber-600 bg-amber-50 text-amber-950', icon: ExclamationTriangleIcon, iconClass: 'text-amber-700' },
  danger: { wrap: 'border-l-state-600 bg-state-50 text-state-700', icon: ExclamationTriangleIcon, iconClass: 'text-state-600' },
  success: { wrap: 'border-l-teal-700 bg-teal-50 text-teal-950', icon: CheckCircleIcon, iconClass: 'text-teal-700' },
  simulated: { wrap: 'border-l-violet-700 bg-violet-50 text-violet-950', icon: BeakerIcon, iconClass: 'text-violet-700' },
};

export function Callout({
  tone = 'info',
  title,
  children,
  className = '',
}: {
  tone?: CalloutTone;
  title?: string;
  children: React.ReactNode;
  className?: string;
}) {
  const { wrap, icon: Icon, iconClass } = tones[tone];
  return (
    <div className={`flex gap-3 rounded-sm border border-border border-l-4 p-4 ${wrap} ${className}`.trim()}>
      <Icon className={`h-5 w-5 shrink-0 ${iconClass}`} aria-hidden />
      <div className="min-w-0 text-[14px] leading-relaxed">
        {title ? <p className="mb-1 font-bold">{title}</p> : null}
        {children}
      </div>
    </div>
  );
}

export default Callout;
