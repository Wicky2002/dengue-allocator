'use client';

import React from 'react';

export interface TabDef {
  key: string;
  label: string;
}

/** Simple tab strip for portal sections. */
export function Tabs({
  tabs,
  active,
  onChange,
}: {
  tabs: TabDef[];
  active: string;
  onChange: (key: string) => void;
}) {
  return (
    <div className="mb-6 overflow-x-auto border-b border-border">
      <div className="inline-flex" role="tablist">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            type="button"
            role="tab"
            aria-selected={active === tab.key}
            onClick={() => onChange(tab.key)}
            className={`-mb-px whitespace-nowrap border-b-[3px] px-4 py-2.5 text-[14px] font-semibold transition-colors ${
              active === tab.key
                ? 'border-state-600 text-primary-800'
                : 'border-transparent text-text-600 hover:border-border hover:text-primary-800'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>
    </div>
  );
}

export default Tabs;
