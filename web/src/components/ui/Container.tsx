import React from 'react';

const sizes = {
  sm: 'max-w-screen-sm',
  md: 'max-w-screen-md',
  lg: 'max-w-screen-lg',
  xl: 'max-w-screen-xl',
  full: 'max-w-[1600px]',
} as const;

interface ContainerProps extends React.HTMLAttributes<HTMLDivElement> {
  size?: keyof typeof sizes;
}

export function Container({ size = 'xl', className = '', children, ...rest }: ContainerProps) {
  return (
    <div className={`${sizes[size]} mx-auto px-4 sm:px-6 lg:px-8 ${className}`} {...rest}>
      {children}
    </div>
  );
}

export default Container;
