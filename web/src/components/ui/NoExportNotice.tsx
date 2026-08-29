import React from 'react';
import { Container } from './Container';
import { Card } from './Card';

/** Rendered when `make export-web` has never run. Actionable, not a dead end. */
export function NoExportNotice() {
  return (
    <Container className="py-24">
      <Card padding="lg" className="mx-auto max-w-2xl text-center">
        <h1 className="text-h1">No pipeline data yet</h1>
        <p className="mt-3 text-text-600">
          This app renders artifacts written by the Python pipeline. Build them, then export
          them for the browser:
        </p>
        <pre className="mt-5 overflow-x-auto rounded-sm bg-primary-900 p-4 text-left font-mono text-sm text-primary-100">
          make pipeline{'\n'}make export-web
        </pre>
        <p className="mt-4 text-sm text-text-500">
          Both run fully offline against the synthetic panel.
        </p>
      </Card>
    </Container>
  );
}

export default NoExportNotice;
