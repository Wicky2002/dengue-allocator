'use client';

import React from 'react';
import {
  Area,
  AreaChart,
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

export interface DistrictPoint {
  week: string;
  cases: number;
  rain: number | null;
  tmax: number | null;
}

/** One district's observed weekly cases. */
export function DistrictCases({ data, height = 220 }: { data: DistrictPoint[]; height?: number }) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: -16 }}>
        <defs>
          <linearGradient id="casesFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#1D4ED8" stopOpacity={0.35} />
            <stop offset="100%" stopColor="#1D4ED8" stopOpacity={0.02} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" vertical={false} />
        <XAxis
          dataKey="week"
          tickFormatter={axisDate}
          tick={{ fontSize: 11, fill: '#6B7280' }}
          minTickGap={40}
          axisLine={{ stroke: '#E5E7EB' }}
          tickLine={false}
        />
        <YAxis tick={{ fontSize: 11, fill: '#6B7280' }} axisLine={false} tickLine={false} width={48} />
        <Tooltip
          contentStyle={{ borderRadius: 10, border: '1px solid #E5E7EB', fontSize: 12 }}
          labelFormatter={(value) => `Week of ${shortDate(String(value))}`}
          formatter={(value) => [num(value as number), 'Cases']}
        />
        <Area
          dataKey="cases"
          stroke="#1D4ED8"
          strokeWidth={2}
          fill="url(#casesFill)"
          isAnimationActive={false}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}

/** Rainfall behind that district's cases, to show the 6–8 week lag locally. */
export function DistrictRainfall({ data, height = 200 }: { data: DistrictPoint[]; height?: number }) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <ComposedChart data={data} margin={{ top: 8, right: 4, bottom: 0, left: -16 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" vertical={false} />
        <XAxis
          dataKey="week"
          tickFormatter={axisDate}
          tick={{ fontSize: 11, fill: '#6B7280' }}
          minTickGap={40}
          axisLine={{ stroke: '#E5E7EB' }}
          tickLine={false}
        />
        <YAxis yAxisId="rain" orientation="right" tick={{ fontSize: 11, fill: '#60A5FA' }} axisLine={false} tickLine={false} width={36} />
        <YAxis yAxisId="cases" tick={{ fontSize: 11, fill: '#6B7280' }} axisLine={false} tickLine={false} width={44} />
        <Tooltip
          contentStyle={{ borderRadius: 10, border: '1px solid #E5E7EB', fontSize: 12 }}
          labelFormatter={(value) => `Week of ${shortDate(String(value))}`}
          formatter={(value, name) =>
            name === 'rain'
              ? [`${(value as number)?.toFixed(1)} mm`, 'Rainfall']
              : [num(value as number), 'Cases']
          }
        />
        <Bar yAxisId="rain" dataKey="rain" fill="#BFDBFE" isAnimationActive={false} />
        <Line yAxisId="cases" dataKey="cases" stroke="#B91C1C" strokeWidth={2} dot={false} isAnimationActive={false} />
      </ComposedChart>
    </ResponsiveContainer>
  );
}
