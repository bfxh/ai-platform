-- Sub-agent workspace: isolated execution environment for spawned sub-agents.
-- Each workspace belongs to a parent agent and defines the isolation boundary
-- (process / container / VM), snapshot retention policy, and lifecycle status.

CREATE TABLE sub_agent_workspace (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspace(id) ON DELETE CASCADE,
    parent_agent_id UUID NOT NULL REFERENCES agent(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    base_path TEXT NOT NULL,
    snapshot_retention_count INT NOT NULL DEFAULT 50,
    isolation_mode TEXT NOT NULL DEFAULT 'process'
        CHECK (isolation_mode IN ('process', 'container', 'vm')),
    status TEXT NOT NULL DEFAULT 'active'
        CHECK (status IN ('active', 'archived', 'cleaning')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_sub_agent_workspace_workspace ON sub_agent_workspace(workspace_id);
CREATE INDEX idx_sub_agent_workspace_parent_agent ON sub_agent_workspace(parent_agent_id);
CREATE INDEX idx_sub_agent_workspace_status ON sub_agent_workspace(workspace_id, status);
