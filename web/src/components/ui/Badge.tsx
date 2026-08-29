import React from 'react';

export type BadgeTone = 'info' | 'success' | 'warning' | 'danger' | 'neutral' | 'brand' | 'onDark';

const tones: Record<BadgeTone, string> = {
  info: 'bg-primary-50 text-primary-800 ring-primary-200',
  success: 'bg-green-50 text-green-900 ring-green-200',
  warning: 'bg-amber-50 text-amber-900 ring-amber-200',
  danger: 'bg-red-50 text-red-900 ring-red-200',
  neutral: 'bg-bg-200 text-text-700 ring-border',
  brand: 'bg-state-50 text-state-700 ring-state-100',
  onDark: 'bg-white/10 text-white ring-white/30',
};

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  tone?: BadgeTone;
}

export function Badge({ tone = 'neutral', className = '', children, ...rest }: BadgeProps) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-sm px-2.5 py-1 text-[12px] font-semibold ring-1 ${tones[tone]} ${className}`.trim()}
      {...rest}
    >
      {children}
    </span>
  );
}

export default Badge;
