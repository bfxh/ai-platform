import React, { useState } from 'react';

interface SpawnModalProps {
  workspaceId: string;
  onClose: () => void;
  onCreated: () => void;
}

export default function SpawnModal({ workspaceId, onClose, onCreated }: SpawnModalProps) {
  const [subAgentType, setSubAgentType] = useState('qoder');
  const [isolationMode, setIsolationMode] = useState('process');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const res = await fetch(`/api/sub-agent-workspaces/${workspaceId}/spawn`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sub_agent_type: subAgentType,
          spawn_config: { isolation_mode: isolationMode },
        }),
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.error || 'Failed to spawn sub-agent');
      }

      onCreated();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 w-full max-w-md shadow-xl">
        <h2 className="text-xl font-bold text-slate-900 dark:text-white mb-4">Spawn Sub-Agent</h2>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
              Agent Type
            </label>
            <select
              value={subAgentType}
              onChange={(e) => setSubAgentType(e.target.value)}
              className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-white"
            >
              <option value="qoder">Qoder</option>
              <option value="trae">TRAE</option>
              <option value="claude">Claude Code</option>
              <option value="claude_orch">Claude Orchestrator</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
              Isolation Mode
            </label>
            <select
              value={isolationMode}
              onChange={(e) => setIsolationMode(e.target.value)}
              className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-white"
            >
              <option value="process">Process</option>
              <option value="container">Container</option>
              <option value="vm">VM</option>
            </select>
          </div>

          {error && (
            <div className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-sm text-red-600 dark:text-red-400">
              {error}
            </div>
          )}

          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
            >
              {loading ? 'Spawning...' : 'Spawn'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
