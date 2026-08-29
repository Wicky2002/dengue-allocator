'use client';

import React from 'react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  LabelList,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

import type { ModelScore } from '@/lib/selectors';

/**
 * Backtest comparison. The winning model is the only one coloured.
 *
 * Bars start at zero, as a bar chart must. Scores here cluster in a narrow band
 * (a good model and a poor one can sit at 14 and 22), so the difference the
 * chart exists to show is barely visible as length — each bar therefore carries
 * its value. Truncating the axis to exaggerate the gap would be the other way
 * to solve this, and it would misrepresent the size of the difference.
 */
export function ModelScores({
  data,
  metricLabel,
  height = 260,
}: {
  data: ModelScore[];
  metricLabel: string;
  height?: number;
}) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} layout="vertical" margin={{ top: 4, right: 52, bottom: 0, left: 8 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" horizontal={false} />
        <XAxis type="number" tick={{ fontSize: 11, fill: '#6B7280' }} axisLine={false} tickLine={false} />
        <YAxis
          type="category"
          dataKey="model"
          width={168}
          tick={{ fontSize: 11, fill: '#2E3949' }}
          axisLine={false}
          tickLine={false}
        />
        <Tooltip
          cursor={{ fill: '#F3F4F6' }}
          contentStyle={{ borderRadius: 10, border: '1px solid #E5E7EB', fontSize: 12 }}
          formatter={(value, _name, entry) => [
            `${(value as number).toFixed(3)} (${(entry?.payload as ModelScore)?.folds ?? 0} folds)`,
            metricLabel,
          ]}
        />
        <Bar dataKey="value" radius={[0, 2, 2, 0]} isAnimationActive={false}>
          {data.map((row, index) => (
            <Cell key={row.model} fill={index === 0 ? '#163254' : '#BCCADD'} />
          ))}
          <LabelList
            dataKey="value"
            position="right"
            className="num"
            fontSize={11}
            fill="#2E3949"
            formatter={(value: number) => value.toFixed(2)}
          />
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

export default ModelScores;
