'use client';

import React, { useState, useEffect, useCallback } from 'react';
import SpawnModal from '@/components/sub-agent/SpawnModal';
import SubAgentCard from '@/components/sub-agent/SubAgentCard';
import PendingDeletionPanel from '@/components/deletion/PendingDeletionPanel';
import ContainerStatusIndicator from '@/components/resource/ContainerStatusIndicator';
import TRAEStatusPanel from '@/components/sub-agent/TRAEStatusPanel';

const WORKSPACE_ID = '0c2af6d5-f809-4b97-8d8a-df17924a0c94';

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
  const [showCreateWs, setShowCreateWs] = useState(false);
  const [newWsName, setNewWsName] = useState('');
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'spawns' | 'deletions' | 'trae'>('spawns');

  const headers = { 'X-Workspace-ID': WORKSPACE_ID };

  const fetchWorkspaces = useCallback(async () => {
    try {
      const res = await fetch('/api/sub-agent-workspaces?agent_id=current');
      if (res.ok) {
        const data = await res.json();
        setWorkspaces(data || []);
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
        setSpawns(data || []);
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

  const handleCreateWorkspace = async () => {
    try {
      const res = await fetch('/api/sub-agent-workspaces', {
        method: 'POST',
        headers: { ...headers, 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: newWsName,
          base_path: `D:/workspaces/${newWsName}`,
          isolation_mode: 'process',
        }),
      });
      if (res.ok) {
        setNewWsName('');
        setShowCreateWs(false);
        fetchWorkspaces();
      }
    } catch (err) {
      console.error('Failed to create workspace:', err);
    }
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
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Management Panel</h1>
        <div className="flex gap-2">
          <button
            onClick={() => setShowCreateWs(true)}
            className="px-4 py-2 bg-slate-600 text-white rounded-lg hover:bg-slate-700 transition-colors text-sm"
          >
            + Workspace
          </button>
          <button
            onClick={() => setShowSpawnModal(true)}
            disabled={!selectedWs}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm"
          >
            Spawn Agent
          </button>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="flex gap-1 mb-6 border-b border-slate-200 dark:border-slate-700">
        {(['spawns', 'deletions', 'trae'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 text-sm font-medium border-b-2 -mb-[1px] transition-colors ${
              activeTab === tab
                ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                : 'border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
            }`}
          >
            {tab === 'spawns' ? 'Sub-Agents' : tab === 'deletions' ? 'Pending Deletions' : 'TRAE Status'}
          </button>
        ))}
      </div>

      {activeTab === 'spawns' && (
        <>
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
                <div className="col-span-full text-center py-12 text-slate-400 border-2 border-dashed border-slate-300 dark:border-slate-700 rounded-xl">
                  <p>No sub-agent workspaces yet.</p>
                  <button
                    onClick={() => setShowCreateWs(true)}
                    className="text-blue-500 hover:text-blue-600 text-sm mt-2 underline"
                  >
                    Create your first workspace
                  </button>
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
                  <div className="text-center py-8 text-slate-400 border-2 border-dashed border-slate-300 dark:border-slate-700 rounded-xl">
                    No sub-agents spawned in this workspace.
                  </div>
                )}
              </div>
            </div>
          )}
        </>
      )}

      {activeTab === 'deletions' && <PendingDeletionPanel />}

      {activeTab === 'trae' && (
        <div className="max-w-lg">
          <TRAEStatusPanel />
        </div>
      )}

      {/* Create Workspace Modal */}
      {showCreateWs && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-slate-800 rounded-xl p-6 w-full max-w-md shadow-xl">
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">Create Workspace</h3>
            <input
              type="text"
              value={newWsName}
              onChange={(e) => setNewWsName(e.target.value)}
              placeholder="Workspace name"
              className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-white mb-4 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <div className="flex gap-2 justify-end">
              <button
                onClick={() => { setShowCreateWs(false); setNewWsName(''); }}
                className="px-4 py-2 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleCreateWorkspace}
                disabled={!newWsName.trim()}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
              >
                Create
              </button>
            </div>
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
