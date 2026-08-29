'use client';

import React from 'react';
import {
  Area,
  CartesianGrid,
  ComposedChart,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

import { axisDate, num, shortDate } from '@/lib/format';
import type { ForecastPoint } from '@/lib/selectors';

/**
 * Observed cases, continuing into the forecast.
 *
 * Solid line = observed. Dashed line = forecast median, with the 80% interval
 * as a band behind it. The band is not decoration: a median drawn alone reads
 * as a prediction of exactly that many cases, which the model does not claim.
 */
export function ForecastTrend({ data, height = 300 }: { data: ForecastPoint[]; height?: number }) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <ComposedChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: -12 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" vertical={false} />
        <XAxis
          dataKey="week"
          tickFormatter={axisDate}
          tick={{ fontSize: 11, fill: '#6B7280' }}
          minTickGap={40}
          axisLine={{ stroke: '#E5E7EB' }}
          tickLine={false}
        />
        <YAxis
          tick={{ fontSize: 11, fill: '#6B7280' }}
          axisLine={false}
          tickLine={false}
          width={56}
        />
        <Tooltip
          contentStyle={{ borderRadius: 10, border: '1px solid #E5E7EB', fontSize: 12 }}
          labelFormatter={(value) => `Week of ${shortDate(String(value))}`}
          formatter={(value, name) => {
            if (name === 'interval' && Array.isArray(value)) {
              return [`${num(Number(value[0]))} – ${num(Number(value[1]))}`, '80% interval'];
            }
            return [num(value as number), name === 'observed' ? 'Observed' : 'Forecast median'];
          }}
        />
        <Area
          dataKey="interval"
          stroke="none"
          fill="#1D4ED8"
          fillOpacity={0.14}
          isAnimationActive={false}
          connectNulls
        />
        <Line
          dataKey="observed"
          stroke="#111827"
          strokeWidth={2}
          dot={false}
          isAnimationActive={false}
          connectNulls
        />
        <Line
          dataKey="median"
          stroke="#1D4ED8"
          strokeWidth={2}
          strokeDasharray="5 4"
          dot={false}
          isAnimationActive={false}
          connectNulls
        />
      </ComposedChart>
    </ResponsiveContainer>
  );
}

export default ForecastTrend;
