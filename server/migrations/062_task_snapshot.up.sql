-- Task snapshot: pre/post/manual file snapshots for diff, restore, and version tracking.
-- Each snapshot is associated with a workspace and optionally a specific task or spawn.
-- file_diff stores the JSON diff (added, modified, deleted, unchanged file lists).
-- storage_path points to the snapshot archive on disk.

CREATE TABLE task_snapshot (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES sub_agent_workspace(id) ON DELETE CASCADE,
    task_id UUID REFERENCES agent_task_queue(id) ON DELETE SET NULL,
    spawn_id UUID REFERENCES sub_agent_spawn(id) ON DELETE SET NULL,
    snapshot_type TEXT NOT NULL CHECK (snapshot_type IN ('pre', 'post', 'manual')),
    label TEXT,
    file_diff JSONB NOT NULL DEFAULT '{}',
    storage_path TEXT NOT NULL,
    total_size_bytes BIGINT NOT NULL DEFAULT 0,
    file_count INT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_task_snapshot_workspace ON task_snapshot(workspace_id);
CREATE INDEX idx_task_snapshot_task ON task_snapshot(task_id);
CREATE INDEX idx_task_snapshot_type ON task_snapshot(workspace_id, snapshot_type);
CREATE INDEX idx_task_snapshot_created ON task_snapshot(workspace_id, created_at DESC);
