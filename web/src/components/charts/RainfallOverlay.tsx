'use client';

import React from 'react';
import {
  Bar,
  CartesianGrid,
  ComposedChart,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

import { axisDate, num, shortDate } from '@/lib/format';
import type { RainfallPoint } from '@/lib/selectors';

/** Weekly rainfall behind weekly cases, on independent axes. */
export function RainfallOverlay({ data, height = 280 }: { data: RainfallPoint[]; height?: number }) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <ComposedChart data={data} margin={{ top: 8, right: 4, bottom: 0, left: -12 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" vertical={false} />
        <XAxis
          dataKey="week"
          tickFormatter={axisDate}
          tick={{ fontSize: 11, fill: '#6B7280' }}
          minTickGap={44}
          axisLine={{ stroke: '#E5E7EB' }}
          tickLine={false}
        />
        <YAxis yAxisId="rain" orientation="right" tick={{ fontSize: 11, fill: '#60A5FA' }} axisLine={false} tickLine={false} width={40} />
        <YAxis yAxisId="cases" tick={{ fontSize: 11, fill: '#6B7280' }} axisLine={false} tickLine={false} width={52} />
        <Tooltip
          contentStyle={{ borderRadius: 10, border: '1px solid #E5E7EB', fontSize: 12 }}
          labelFormatter={(value) => `Week of ${shortDate(String(value))}`}
          formatter={(value, name) =>
            name === 'rain'
              ? [`${(value as number | null)?.toFixed(1) ?? '—'} mm`, 'Mean rainfall']
              : [num(value as number), 'Cases']
          }
        />
        <Bar yAxisId="rain" dataKey="rain" fill="#BFDBFE" isAnimationActive={false} />
        <Line
          yAxisId="cases"
          dataKey="cases"
          stroke="#B91C1C"
          strokeWidth={2}
          dot={false}
          isAnimationActive={false}
        />
      </ComposedChart>
    </ResponsiveContainer>
  );
}

export default RainfallOverlay;
