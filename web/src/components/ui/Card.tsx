import React from 'react';

const paddings = { none: '', sm: 'p-4', md: 'p-5', lg: 'p-6 sm:p-7' } as const;

interface CardProps extends React.HTMLAttributes<HTMLElement> {
  as?: 'div' | 'section' | 'article' | 'aside' | 'li';
  padding?: keyof typeof paddings;
  interactive?: boolean;
  /** A coloured top rule, as on an official notice. */
  accent?: 'none' | 'navy' | 'state' | 'gold';
}

const accents = {
  none: '',
  navy: 'border-t-[3px] border-t-primary-700',
  state: 'border-t-[3px] border-t-state-600',
  gold: 'border-t-[3px] border-t-gold-500',
} as const;

export function Card({
  as: Tag = 'div',
  padding = 'md',
  interactive = false,
  accent = 'none',
  className = '',
  children,
  ...rest
}: CardProps) {
  return (
    <Tag
      className={[
        'rounded-sm border border-border bg-white shadow-card',
        accents[accent],
        paddings[padding],
        interactive ? 'transition-colors hover:border-primary-300 hover:shadow-lift' : '',
        className,
      ]
        .filter(Boolean)
        .join(' ')}
      {...rest}
    >
      {children}
    </Tag>
  );
}

export default Card;
