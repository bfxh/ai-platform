import React from 'react';

interface SubAgentCardProps {
  spawn: {
    id: string;
    sub_agent_type: string;
    sandbox_status: string;
    container_id?: string;
    created_at: string;
  };
  statusColor: string;
}

export default function SubAgentCard({ spawn, statusColor }: SubAgentCardProps) {
  const typeIcons: Record<string, string> = {
    qoder: 'Q',
    trae: 'T',
    claude: 'C',
  };

  return (
    <div className="flex items-center gap-4 p-4 bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700">
      <div className={`w-10 h-10 rounded-lg flex items-center justify-center text-white font-bold text-sm ${
        spawn.sub_agent_type === 'qoder' ? 'bg-violet-500' :
        spawn.sub_agent_type === 'trae' ? 'bg-emerald-500' : 'bg-orange-500'
      }`}>
        {typeIcons[spawn.sub_agent_type] || '?'}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="font-medium text-slate-900 dark:text-white">
            {spawn.sub_agent_type.toUpperCase()}
          </span>
          <span className="text-xs text-slate-400 font-mono">{spawn.id.slice(0, 8)}</span>
        </div>
        <div className="flex items-center gap-2 mt-1">
          <span className={`inline-block w-2 h-2 rounded-full ${statusColor}`} />
          <span className="text-sm text-slate-500">{spawn.sandbox_status}</span>
        </div>
      </div>
      <div className="text-xs text-slate-400">
        {new Date(spawn.created_at).toLocaleTimeString()}
      </div>
    </div>
  );
}
