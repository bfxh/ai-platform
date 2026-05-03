package service

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"log/slog"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgtype"
	"github.com/multica-ai/multica/server/internal/util"
)

type ResourceProfileService struct {
	db dbExecutor
}

func NewResourceProfileService(db dbExecutor) *ResourceProfileService {
	return &ResourceProfileService{db: db}
}

type TaskResourceProfile struct {
	ID                string    `json:"id"`
	WorkspaceID       string    `json:"workspace_id"`
	TaskType          string    `json:"task_type"`
	EstimatedGPUMemMB int32     `json:"estimated_gpu_memory_mb"`
	EstimatedCPUCores int32     `json:"estimated_cpu_cores"`
	EstimatedMemMB    int32     `json:"estimated_memory_mb"`
	PriorityTier      string    `json:"priority_tier"`
	TypicalDurationMs *int64    `json:"typical_duration_ms"`
	MaxRetries        int32     `json:"max_retries"`
	PreCheckRules     string    `json:"pre_check_rules"`
	RerouteTarget     *string   `json:"reroute_target"`
	CreatedAt         time.Time `json:"created_at"`
	UpdatedAt         time.Time `json:"updated_at"`
}

func (s *ResourceProfileService) CreateProfile(ctx context.Context, workspaceID, taskType, priorityTier string, gpuMemMB, cpuCores, memMB, maxRetries int32, preCheckRules []string, rerouteTarget *string) (*TaskResourceProfile, error) {
	rulesJSON, err := json.Marshal(preCheckRules)
	if err != nil {
		return nil, fmt.Errorf("marshal pre-check rules: %w", err)
	}

	var p TaskResourceProfile
	var rt pgtype.Text
	var dur pgtype.Int8
	if rerouteTarget != nil {
		rt = pgtype.Text{String: *rerouteTarget, Valid: true}
	}

	err = s.db.QueryRow(ctx,
		`INSERT INTO task_resource_profile (workspace_id, task_type, estimated_gpu_memory_mb, estimated_cpu_cores, estimated_memory_mb, priority_tier, max_retries, pre_check_rules, reroute_target)
         VALUES ($1, $2, $3, $4, $5, $6, $7, $8::jsonb, $9)
         ON CONFLICT (workspace_id, task_type) DO UPDATE SET
             estimated_gpu_memory_mb = EXCLUDED.estimated_gpu_memory_mb,
             estimated_cpu_cores = EXCLUDED.estimated_cpu_cores,
             estimated_memory_mb = EXCLUDED.estimated_memory_mb,
             priority_tier = EXCLUDED.priority_tier,
             max_retries = EXCLUDED.max_retries,
             pre_check_rules = EXCLUDED.pre_check_rules,
             reroute_target = EXCLUDED.reroute_target,
             updated_at = now()
         RETURNING id, workspace_id, task_type, estimated_gpu_memory_mb, estimated_cpu_cores, estimated_memory_mb, priority_tier, typical_duration_ms, max_retries, pre_check_rules::text, reroute_target, created_at, updated_at`,
		util.MustParseUUID(workspaceID), taskType, gpuMemMB, cpuCores, memMB, priorityTier, maxRetries, string(rulesJSON), rt,
	).Scan(&p.ID, &p.WorkspaceID, &p.TaskType, &p.EstimatedGPUMemMB, &p.EstimatedCPUCores, &p.EstimatedMemMB,
		&p.PriorityTier, &dur, &p.MaxRetries, &p.PreCheckRules, &rt, &p.CreatedAt, &p.UpdatedAt)
	if err != nil {
		return nil, fmt.Errorf("create resource profile: %w", err)
	}
	if dur.Valid {
		p.TypicalDurationMs = &dur.Int64
	}
	if rt.Valid {
		p.RerouteTarget = &rt.String
	}
	slog.Info("resource profile upserted", "profile_id", p.ID, "task_type", taskType, "tier", priorityTier)
	return &p, nil
}

func (s *ResourceProfileService) GetProfile(ctx context.Context, profileID string) (*TaskResourceProfile, error) {
	var p TaskResourceProfile
	var rt pgtype.Text
	var dur pgtype.Int8
	err := s.db.QueryRow(ctx,
		`SELECT id, workspace_id, task_type, estimated_gpu_memory_mb, estimated_cpu_cores, estimated_memory_mb, priority_tier, typical_duration_ms, max_retries, pre_check_rules::text, reroute_target, created_at, updated_at
         FROM task_resource_profile WHERE id = $1`,
		util.MustParseUUID(profileID),
	).Scan(&p.ID, &p.WorkspaceID, &p.TaskType, &p.EstimatedGPUMemMB, &p.EstimatedCPUCores, &p.EstimatedMemMB,
		&p.PriorityTier, &dur, &p.MaxRetries, &p.PreCheckRules, &rt, &p.CreatedAt, &p.UpdatedAt)
	if err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			return nil, fmt.Errorf("resource profile not found")
		}
		return nil, fmt.Errorf("get resource profile: %w", err)
	}
	if dur.Valid {
		p.TypicalDurationMs = &dur.Int64
	}
	if rt.Valid {
		p.RerouteTarget = &rt.String
	}
	return &p, nil
}

func (s *ResourceProfileService) MatchProfile(ctx context.Context, workspaceID, taskType string) (*TaskResourceProfile, error) {
	var p TaskResourceProfile
	var rt pgtype.Text
	var dur pgtype.Int8
	err := s.db.QueryRow(ctx,
		`SELECT id, workspace_id, task_type, estimated_gpu_memory_mb, estimated_cpu_cores, estimated_memory_mb, priority_tier, typical_duration_ms, max_retries, pre_check_rules::text, reroute_target, created_at, updated_at
         FROM task_resource_profile WHERE workspace_id = $1 AND task_type = $2`,
		util.MustParseUUID(workspaceID), taskType,
	).Scan(&p.ID, &p.WorkspaceID, &p.TaskType, &p.EstimatedGPUMemMB, &p.EstimatedCPUCores, &p.EstimatedMemMB,
		&p.PriorityTier, &dur, &p.MaxRetries, &p.PreCheckRules, &rt, &p.CreatedAt, &p.UpdatedAt)
	if err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			return nil, fmt.Errorf("no resource profile for task type: %s", taskType)
		}
		return nil, fmt.Errorf("match resource profile: %w", err)
	}
	if dur.Valid {
		p.TypicalDurationMs = &dur.Int64
	}
	if rt.Valid {
		p.RerouteTarget = &rt.String
	}
	return &p, nil
}

func (s *ResourceProfileService) ListProfiles(ctx context.Context, workspaceID string) ([]TaskResourceProfile, error) {
	rows, err := s.db.Query(ctx,
		`SELECT id, workspace_id, task_type, estimated_gpu_memory_mb, estimated_cpu_cores, estimated_memory_mb, priority_tier, typical_duration_ms, max_retries, pre_check_rules::text, reroute_target, created_at, updated_at
         FROM task_resource_profile WHERE workspace_id = $1
         ORDER BY task_type`,
		util.MustParseUUID(workspaceID),
	)
	if err != nil {
		return nil, fmt.Errorf("list resource profiles: %w", err)
	}
	defer rows.Close()

	var profiles []TaskResourceProfile
	for rows.Next() {
		var p TaskResourceProfile
		var rt pgtype.Text
		var dur pgtype.Int8
		if err := rows.Scan(&p.ID, &p.WorkspaceID, &p.TaskType, &p.EstimatedGPUMemMB, &p.EstimatedCPUCores, &p.EstimatedMemMB,
			&p.PriorityTier, &dur, &p.MaxRetries, &p.PreCheckRules, &rt, &p.CreatedAt, &p.UpdatedAt); err != nil {
			return nil, fmt.Errorf("scan resource profile: %w", err)
		}
		if dur.Valid {
			p.TypicalDurationMs = &dur.Int64
		}
		if rt.Valid {
			p.RerouteTarget = &rt.String
		}
		profiles = append(profiles, p)
	}
	return profiles, rows.Err()
}

func (s *ResourceProfileService) UpdateProfileStats(ctx context.Context, profileID string, actualDurationMs int64) error {
	tag, err := s.db.Exec(ctx,
		`UPDATE task_resource_profile SET typical_duration_ms = $2, updated_at = now() WHERE id = $1`,
		util.MustParseUUID(profileID), actualDurationMs,
	)
	if err != nil {
		return fmt.Errorf("update profile stats: %w", err)
	}
	if tag.RowsAffected() == 0 {
		return fmt.Errorf("resource profile not found")
	}
	return nil
}
