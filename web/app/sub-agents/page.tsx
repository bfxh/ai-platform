'use client';

import React, { useState, useEffect, useCallback } from 'react';
import SpawnModal from '@/components/sub-agent/SpawnModal';
import SubAgentCard from '@/components/sub-agent/SubAgentCard';
import ContainerStatusIndicator from '@/components/resource/ContainerStatusIndicator';

interface SubAgentWorkspace {
  id: string;
  name: string;
  isolation_mode: string;
  status: string;
  created_at: string;
}

interface SubAgentSpawn {
  id: string;
  sub_agent_type: string;
  sandbox_status: string;
  container_id?: string;
  created_at: string;
}

export default function SubAgentsDashboard() {
  const [workspaces, setWorkspaces] = useState<SubAgentWorkspace[]>([]);
  const [selectedWs, setSelectedWs] = useState<string | null>(null);
  const [spawns, setSpawns] = useState<SubAgentSpawn[]>([]);
  const [showSpawnModal, setShowSpawnModal] = useState(false);
  const [loading, setLoading] = useState(true);

  const fetchWorkspaces = useCallback(async () => {
    try {
      const res = await fetch('/api/sub-agent-workspaces?agent_id=current');
      if (res.ok) {
        const data = await res.json();
        setWorkspaces(data);
      }
    } catch (err) {
      console.error('Failed to fetch workspaces:', err);
    }
    setLoading(false);
  }, []);

  const fetchSpawns = useCallback(async (wsId: string) => {
    try {
      const res = await fetch(`/api/sub-agent-workspaces/${wsId}/spawns`);
      if (res.ok) {
        const data = await res.json();
        setSpawns(data);
      }
    } catch (err) {
      console.error('Failed to fetch spawns:', err);
    }
  }, []);

  useEffect(() => {
    fetchWorkspaces();
  }, [fetchWorkspaces]);

  useEffect(() => {
    if (selectedWs) {
      fetchSpawns(selectedWs);
      const interval = setInterval(() => fetchSpawns(selectedWs), 5000);
      return () => clearInterval(interval);
    }
  }, [selectedWs, fetchSpawns]);

  const handleSpawnCreated = () => {
    setShowSpawnModal(false);
    if (selectedWs) fetchSpawns(selectedWs);
  };

  const statusColor = (status: string) => {
    switch (status) {
      case 'running': return 'bg-emerald-500';
      case 'completed': return 'bg-blue-500';
      case 'failed': case 'timeout': return 'bg-red-500';
      case 'pending': case 'starting': return 'bg-amber-500';
      default: return 'bg-slate-400';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500" />
      </div>
    );
  }

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Sub-Agents</h1>
        <button
          onClick={() => setShowSpawnModal(true)}
          disabled={!selectedWs}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          Spawn Sub-Agent
        </button>
      </div>

      {/* Workspace Selection */}
      <div className="mb-6">
        <h2 className="text-sm font-semibold text-slate-500 uppercase tracking-wide mb-3">Workspaces</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {workspaces.map((ws) => (
            <button
              key={ws.id}
              onClick={() => setSelectedWs(ws.id)}
              className={`p-4 rounded-xl border-2 text-left transition-all ${
                selectedWs === ws.id
                  ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                  : 'border-slate-200 dark:border-slate-700 hover:border-slate-300 dark:hover:border-slate-600'
              }`}
            >
              <div className="font-medium text-slate-900 dark:text-white">{ws.name}</div>
              <div className="text-sm text-slate-500 mt-1">
                {ws.isolation_mode} · {ws.status}
              </div>
            </button>
          ))}
          {workspaces.length === 0 && (
            <div className="col-span-full text-center py-12 text-slate-400">
              <p>No sub-agent workspaces yet.</p>
              <p className="text-sm mt-2">Create one from the workspace settings page.</p>
            </div>
          )}
        </div>
      </div>

      {/* Spawns List */}
      {selectedWs && (
        <div>
          <h2 className="text-sm font-semibold text-slate-500 uppercase tracking-wide mb-3">Active Spawns</h2>
          <div className="space-y-3">
            {spawns.map((spawn) => (
              <SubAgentCard
                key={spawn.id}
                spawn={spawn}
                statusColor={statusColor(spawn.sandbox_status)}
              />
            ))}
            {spawns.length === 0 && (
              <div className="text-center py-8 text-slate-400">
                No sub-agents spawned in this workspace.
              </div>
            )}
          </div>
        </div>
      )}

      {/* Spawn Modal */}
      {showSpawnModal && selectedWs && (
        <SpawnModal
          workspaceId={selectedWs}
          onClose={() => setShowSpawnModal(false)}
          onCreated={handleSpawnCreated}
        />
      )}
    </div>
  );
}
