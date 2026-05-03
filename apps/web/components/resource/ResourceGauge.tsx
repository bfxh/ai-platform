import React from 'react';

interface ResourceGaugeProps {
  label: string;
  value: number;
  max: number;
  unit: string;
  color?: string;
}

export default function ResourceGauge({
  label,
  value,
  max,
  unit,
  color = 'bg-blue-500',
}: ResourceGaugeProps) {
  const percent = Math.min((value / Math.max(max, 1)) * 100, 100);

  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-sm">
        <span className="text-slate-600 dark:text-slate-400">{label}</span>
        <span className="text-slate-900 dark:text-white font-medium">
          {value} / {max} {unit}
        </span>
      </div>
      <div className="h-2 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-500 ${color}`}
          style={{ width: `${percent}%` }}
        />
      </div>
    </div>
  );
}
