-- Pending deletion: review queue for file deletions requested by sub-agents.
-- Instead of deleting files directly, sub-agents submit deletion requests that
-- await human approval via the pending deletions review panel.
-- Status lifecycle: pending → approved / rejected / expired.

CREATE TABLE pending_deletion (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES sub_agent_workspace(id) ON DELETE CASCADE,
    spawn_id UUID REFERENCES sub_agent_spawn(id) ON DELETE SET NULL,
    file_path TEXT NOT NULL,
    file_size BIGINT NOT NULL DEFAULT 0,
    file_hash TEXT NOT NULL DEFAULT '',
    requested_by_agent TEXT NOT NULL,
    reason TEXT,
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'approved', 'rejected', 'expired')),
    reviewed_by UUID REFERENCES "user"(id),
    reviewed_at TIMESTAMPTZ,
    requested_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_pending_deletion_workspace ON pending_deletion(workspace_id);
CREATE INDEX idx_pending_deletion_status ON pending_deletion(workspace_id, status);
CREATE INDEX idx_pending_deletion_requested_at ON pending_deletion(workspace_id, requested_at DESC);
