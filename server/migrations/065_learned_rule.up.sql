-- Learned rules: auto-retry rules extracted from task failure patterns.
-- When a task fails 3+ times with the same error pattern, a learned rule is created
-- or updated. Rules with confidence >= 0.8 are auto-applied to matching failures.
-- Each rule tracks success/failure statistics for ongoing confidence adjustment.

CREATE TABLE learned_rule (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspace(id) ON DELETE CASCADE,
    error_pattern TEXT NOT NULL,
    fix_strategy TEXT NOT NULL,
    source_task_type TEXT,
    success_count INT NOT NULL DEFAULT 0,
    total_attempts INT NOT NULL DEFAULT 0,
    confidence FLOAT NOT NULL DEFAULT 0
        CHECK (confidence >= 0 AND confidence <= 1),
    auto_apply BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_learned_rule_workspace ON learned_rule(workspace_id);
CREATE INDEX idx_learned_rule_task_type ON learned_rule(workspace_id, source_task_type);
CREATE INDEX idx_learned_rule_confidence ON learned_rule(workspace_id, confidence DESC) WHERE auto_apply = TRUE;
