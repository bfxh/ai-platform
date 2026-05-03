import React from 'react';

interface ContainerStatusIndicatorProps {
  containerId?: string;
  status?: string;
  memoryUsedMB?: number;
  memoryLimitMB?: number;
}

export default function ContainerStatusIndicator({
  containerId,
  status = 'unknown',
  memoryUsedMB = 0,
  memoryLimitMB = 512,
}: ContainerStatusIndicatorProps) {
  const statusMap: Record<string, { color: string; label: string }> = {
    running: { color: 'bg-emerald-500', label: 'Running' },
    exited: { color: 'bg-slate-400', label: 'Exited' },
    paused: { color: 'bg-amber-500', label: 'Paused' },
    dead: { color: 'bg-red-500', label: 'Dead' },
    unknown: { color: 'bg-slate-300', label: 'Unknown' },
  };

  const current = statusMap[status] || statusMap.unknown;
  const memoryPercent = Math.min((memoryUsedMB / memoryLimitMB) * 100, 100);

  return (
    <div className="flex items-center gap-3 p-2 rounded-lg bg-slate-50 dark:bg-slate-800/50">
      <div className={`w-3 h-3 rounded-full ${current.color} animate-pulse`} />
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-slate-700 dark:text-slate-300">{current.label}</span>
          {containerId && (
            <span className="text-xs text-slate-400 font-mono">{containerId}</span>
          )}
        </div>
        {(status === 'running' || status === 'paused') && (
          <div className="mt-1">
            <div className="h-1.5 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all ${
                  memoryPercent > 80 ? 'bg-red-500' : memoryPercent > 50 ? 'bg-amber-500' : 'bg-emerald-500'
                }`}
                style={{ width: `${memoryPercent}%` }}
              />
            </div>
            <div className="text-xs text-slate-400 mt-0.5">
              {memoryUsedMB} / {memoryLimitMB} MB
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
