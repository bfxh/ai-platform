-- Sub-agent spawn record: tracks each spawned sub-agent instance.
-- Links a parent task to a workspace, records the sub-agent type (qoder/trae/claude),
-- container metadata, and sandbox lifecycle status from pending through completion.

CREATE TABLE sub_agent_spawn (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES sub_agent_workspace(id) ON DELETE CASCADE,
    parent_task_id UUID NOT NULL REFERENCES agent_task_queue(id) ON DELETE CASCADE,
    sub_agent_type TEXT NOT NULL CHECK (sub_agent_type IN ('qoder', 'trae', 'claude')),
    spawn_config JSONB NOT NULL DEFAULT '{}',
    container_id TEXT,
    sandbox_status TEXT NOT NULL DEFAULT 'pending'
        CHECK (sandbox_status IN ('pending', 'starting', 'running', 'completed', 'failed', 'timeout', 'cancelled')),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    exit_code INT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_sub_agent_spawn_workspace ON sub_agent_spawn(workspace_id);
CREATE INDEX idx_sub_agent_spawn_parent_task ON sub_agent_spawn(parent_task_id);
CREATE INDEX idx_sub_agent_spawn_container ON sub_agent_spawn(container_id) WHERE container_id IS NOT NULL;
CREATE INDEX idx_sub_agent_spawn_status ON sub_agent_spawn(workspace_id, sandbox_status);
