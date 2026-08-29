import React from 'react';
import Link from 'next/link';

export type ButtonVariant = 'primary' | 'secondary' | 'outline' | 'ghost' | 'onDark';
export type ButtonSize = 'sm' | 'md' | 'lg';

const base =
  'inline-flex items-center justify-center gap-2 rounded-sm font-semibold tracking-tight transition-colors ' +
  'focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-primary-600 ' +
  'disabled:opacity-60 disabled:cursor-not-allowed';

const sizes: Record<ButtonSize, string> = {
  sm: 'text-[13px] px-3 py-1.5',
  md: 'text-[14px] px-4 py-2.5',
  lg: 'text-[15px] px-6 py-3',
};

const variants: Record<ButtonVariant, string> = {
  primary: 'bg-primary-700 text-white hover:bg-primary-800',
  // Flag maroon for the single most important action on a page.
  secondary: 'bg-state-600 text-white hover:bg-state-700',
  outline: 'border border-primary-700 text-primary-700 hover:bg-primary-50',
  ghost: 'text-primary-700 underline underline-offset-4 hover:text-primary-900',
  onDark: 'border border-white/40 text-white hover:bg-white/10',
};

interface CommonProps {
  className?: string;
  children: React.ReactNode;
  variant?: ButtonVariant;
  size?: ButtonSize;
  leadingIcon?: React.ReactNode;
  trailingIcon?: React.ReactNode;
}

type ButtonProps = CommonProps &
  (
    | ({ href: string } & Omit<React.AnchorHTMLAttributes<HTMLAnchorElement>, 'children'>)
    | ({ href?: undefined } & Omit<React.ButtonHTMLAttributes<HTMLButtonElement>, 'children'>)
  );

export function Button({
  href,
  className = '',
  children,
  variant = 'primary',
  size = 'md',
  leadingIcon,
  trailingIcon,
  ...rest
}: ButtonProps) {
  const cls = `${base} ${sizes[size]} ${variants[variant]} ${className}`.trim();
  const inner = (
    <>
      {leadingIcon}
      <span>{children}</span>
      {trailingIcon}
    </>
  );

  if (href) {
    return (
      <Link href={href} className={cls} {...(rest as React.AnchorHTMLAttributes<HTMLAnchorElement>)}>
        {inner}
      </Link>
    );
  }
  return (
    <button className={cls} {...(rest as React.ButtonHTMLAttributes<HTMLButtonElement>)}>
      {inner}
    </button>
  );
}

export default Button;
