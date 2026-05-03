import React, { useState, useEffect } from 'react';

interface PendingDeletion {
  id: string;
  file_path: string;
  file_size: number;
  requested_by_agent: string;
  reason?: string;
  status: string;
  requested_at: string;
}

export default function PendingDeletionPanel() {
  const [deletions, setDeletions] = useState<PendingDeletion[]>([]);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);

  const fetchDeletions = async () => {
    try {
      const wsId = '0c2af6d5-f809-4b97-8d8a-df17924a0c94';
      const res = await fetch(`/api/pending-deletions?workspace_id=${wsId}`);
      if (res.ok) {
        const data = await res.json();
        setDeletions(data);
      }
    } catch (err) {
      console.error('Failed to fetch deletions:', err);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchDeletions();
    const interval = setInterval(fetchDeletions, 10000);
    return () => clearInterval(interval);
  }, []);

  const handleApprove = async (id: string) => {
    try {
      await fetch(`/api/pending-deletions/${id}/approve`, { method: 'POST' });
      fetchDeletions();
    } catch (err) {
      console.error('Failed to approve:', err);
    }
  };

  const handleReject = async (id: string) => {
    try {
      await fetch(`/api/pending-deletions/${id}/reject`, { method: 'POST' });
      fetchDeletions();
    } catch (err) {
      console.error('Failed to reject:', err);
    }
  };

  const handleBulkApprove = async () => {
    try {
      await fetch('/api/pending-deletions/bulk-approve', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ deletion_ids: Array.from(selected) }),
      });
      setSelected(new Set());
      fetchDeletions();
    } catch (err) {
      console.error('Failed to bulk approve:', err);
    }
  };

  const toggleSelect = (id: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  if (loading) {
    return <div className="p-4 text-center text-slate-400">Loading...</div>;
  }

  return (
    <div className="p-4">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-bold text-slate-900 dark:text-white">
          Pending Deletions
          {deletions.length > 0 && (
            <span className="ml-2 text-sm bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300 px-2 py-0.5 rounded-full">
              {deletions.length}
            </span>
          )}
        </h2>
        {selected.size > 0 && (
          <button
            onClick={handleBulkApprove}
            className="px-3 py-1.5 bg-emerald-600 text-white text-sm rounded-lg hover:bg-emerald-700 transition-colors"
          >
            Approve Selected ({selected.size})
          </button>
        )}
      </div>

      {deletions.length === 0 ? (
        <div className="text-center py-8 text-slate-400">
          No pending deletions to review.
        </div>
      ) : (
        <div className="space-y-2">
          {deletions.map((d) => (
            <div
              key={d.id}
              className="flex items-center gap-3 p-3 bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700"
            >
              <input
                type="checkbox"
                checked={selected.has(d.id)}
                onChange={() => toggleSelect(d.id)}
                className="w-4 h-4 rounded border-slate-300"
              />
              <div className="flex-1 min-w-0">
                <div className="font-mono text-sm text-slate-900 dark:text-white truncate">
                  {d.file_path}
                </div>
                <div className="flex items-center gap-3 mt-1 text-xs text-slate-500">
                  <span>{formatSize(d.file_size)}</span>
                  <span>by {d.requested_by_agent}</span>
                  {d.reason && <span className="text-slate-400">{d.reason}</span>}
                </div>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => handleApprove(d.id)}
                  className="px-3 py-1 bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300 text-sm rounded-lg hover:bg-emerald-200 dark:hover:bg-emerald-900/50 transition-colors"
                >
                  Approve
                </button>
                <button
                  onClick={() => handleReject(d.id)}
                  className="px-3 py-1 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 text-sm rounded-lg hover:bg-red-200 dark:hover:bg-red-900/50 transition-colors"
                >
                  Reject
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
