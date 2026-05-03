-- Task resource profile: resource estimation templates for different task types.
-- Used by the dispatcher to route tasks to appropriate runtimes (GPU vs CPU,
-- fast vs heavy) and to determine pre-check rules (localization, rule compliance).
-- priority_tier: fast=immediate CPU, normal=standard, heavy=high CPU/memory, gpu=GPU-accelerated.
-- pre_check_rules: JSON array of pre-execution checks (e.g. ["localization_check", "rule_compliance"]).
-- reroute_target: fallback execution path if the primary one times out (20s default).

CREATE TABLE task_resource_profile (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspace(id) ON DELETE CASCADE,
    task_type TEXT NOT NULL,
    estimated_gpu_memory_mb INT NOT NULL DEFAULT 0,
    estimated_cpu_cores INT NOT NULL DEFAULT 1,
    estimated_memory_mb INT NOT NULL DEFAULT 512,
    priority_tier TEXT NOT NULL DEFAULT 'normal'
        CHECK (priority_tier IN ('fast', 'normal', 'heavy', 'gpu')),
    typical_duration_ms BIGINT,
    max_retries INT NOT NULL DEFAULT 3,
    pre_check_rules JSONB NOT NULL DEFAULT '[]',
    reroute_target TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(workspace_id, task_type)
);

CREATE INDEX idx_task_resource_profile_workspace ON task_resource_profile(workspace_id);
CREATE INDEX idx_task_resource_profile_priority ON task_resource_profile(workspace_id, priority_tier);
