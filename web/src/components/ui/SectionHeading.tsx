import React from 'react';

/**
 * A section head in the register of an official document: a short rule, a
 * small-caps eyebrow, then a serif title — rather than a centred marketing
 * headline.
 */
export function SectionHeading({
  eyebrow,
  title,
  description,
  align = 'left',
  action,
}: {
  eyebrow?: string;
  title: string;
  description?: string;
  align?: 'left' | 'center';
  action?: React.ReactNode;
}) {
  const centred = align === 'center';
  return (
    <div
      className={`mb-6 flex flex-col gap-4 sm:mb-8 ${
        centred ? 'items-center text-center' : 'sm:flex-row sm:items-end sm:justify-between'
      }`}
    >
      <div className={centred ? 'max-w-3xl' : 'max-w-3xl'}>
        <span
          aria-hidden
          className={`block h-0.5 w-14 bg-state-600 ${centred ? 'mx-auto' : ''}`}
        />
        {eyebrow ? <p className="eyebrow mt-3">{eyebrow}</p> : null}
        <h2 className="text-h2 mt-1.5">{title}</h2>
        {description ? (
          <p className="mt-2.5 leading-relaxed text-text-600">{description}</p>
        ) : null}
      </div>
      {action ? <div className="shrink-0">{action}</div> : null}
    </div>
  );
}

export default SectionHeading;
