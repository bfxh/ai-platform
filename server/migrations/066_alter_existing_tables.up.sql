-- Add sub-agent orchestration columns to existing tables.
-- agent_task_queue: sub_workspace_id links tasks to sub-agent workspaces;
--   resource_profile_id links to resource estimation profiles;
--   parent_spawn_id tracks which sub-agent spawn created this task.
-- agent_runtime: container_id and sandbox_type for container-based isolation.
-- skill: auto_generated and source_task_pattern for auto-skill creation.

-- agent_task_queue additions
ALTER TABLE agent_task_queue
    ADD COLUMN sub_workspace_id UUID REFERENCES sub_agent_workspace(id) ON DELETE SET NULL,
    ADD COLUMN resource_profile_id UUID REFERENCES task_resource_profile(id) ON DELETE SET NULL,
    ADD COLUMN parent_spawn_id UUID REFERENCES sub_agent_spawn(id) ON DELETE SET NULL;

CREATE INDEX idx_agent_task_queue_sub_workspace ON agent_task_queue(sub_workspace_id);
CREATE INDEX idx_agent_task_queue_parent_spawn ON agent_task_queue(parent_spawn_id);

-- agent_runtime additions
ALTER TABLE agent_runtime
    ADD COLUMN container_id TEXT,
    ADD COLUMN sandbox_type TEXT NOT NULL DEFAULT 'none'
        CHECK (sandbox_type IN ('none', 'process', 'container', 'vm'));

CREATE INDEX idx_agent_runtime_container ON agent_runtime(container_id) WHERE container_id IS NOT NULL;

-- skill additions for auto-generated skill tracking
ALTER TABLE skill
    ADD COLUMN auto_generated BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN source_task_pattern TEXT;
