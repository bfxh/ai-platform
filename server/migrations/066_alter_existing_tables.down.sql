ALTER TABLE agent_task_queue
    DROP COLUMN IF EXISTS sub_workspace_id,
    DROP COLUMN IF EXISTS resource_profile_id,
    DROP COLUMN IF EXISTS parent_spawn_id;

ALTER TABLE agent_runtime
    DROP COLUMN IF EXISTS container_id,
    DROP COLUMN IF EXISTS sandbox_type;

ALTER TABLE skill
    DROP COLUMN IF EXISTS auto_generated,
    DROP COLUMN IF EXISTS source_task_pattern;
