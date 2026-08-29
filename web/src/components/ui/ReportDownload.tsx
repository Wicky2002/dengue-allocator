'use client';

import React from 'react';
import { DocumentArrowDownIcon } from '@heroicons/react/24/outline';

import { shortDate } from '@/lib/format';
import { useT } from '@/components/i18n/LocaleProvider';

/**
 * The National overview as a PDF.
 *
 * The file is not generated here. `make export-web` runs the same
 * `build_report_pdf` the Streamlit app calls and writes one PDF per horizon to
 * `public/data/`, so the document a user downloads comes from the tested Python
 * generator rather than from a second PDF writer in TypeScript that would drift
 * from it — and generating it at request time would breach the rule this whole
 * platform is built on.
 */
export function ReportDownload({
  horizon,
  generatedAt,
}: {
  horizon: number;
  generatedAt: string | null;
}) {
  const t = useT();
  const href = `/data/national-overview-${horizon}w.pdf`;
  return (
    <div className="flex flex-wrap items-center justify-between gap-5 rounded-sm border border-border border-l-4 border-l-primary-700 bg-white p-5 shadow-card">
      <div className="flex min-w-0 items-start gap-3">
        <DocumentArrowDownIcon className="mt-0.5 h-6 w-6 shrink-0 text-primary-700" aria-hidden />
        <div className="min-w-0">
          <p className="font-semibold text-text-900">
            {t('nat.report.filePrefix')} {horizon} {t('home.weeksAhead')}
          </p>
          <p className="mt-1 text-[13px] text-text-600">
            {t('nat.report.desc')}
            {generatedAt ? ` · ${t('nat.report.pipelineRun')} ${shortDate(generatedAt)}` : ''}
          </p>
        </div>
      </div>
      <a
        href={href}
        download
        className="inline-flex shrink-0 items-center gap-2 rounded-sm bg-primary-700 px-4 py-2.5 text-[14px] font-semibold text-white hover:bg-primary-800"
      >
        <DocumentArrowDownIcon className="h-4 w-4" aria-hidden />
        {t('nat.report.download')}
      </a>
    </div>
  );
}

export default ReportDownload;
