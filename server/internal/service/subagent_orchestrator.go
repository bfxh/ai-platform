package service

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"log/slog"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgconn"
	"github.com/jackc/pgx/v5/pgtype"
	"github.com/multica-ai/multica/server/internal/events"
	"github.com/multica-ai/multica/server/internal/realtime"
	"github.com/multica-ai/multica/server/internal/util"
)

type dbExecutor interface {
	Exec(ctx context.Context, sql string, arguments ...any) (pgconn.CommandTag, error)
	Query(ctx context.Context, sql string, args ...any) (pgx.Rows, error)
	QueryRow(ctx context.Context, sql string, args ...any) pgx.Row
}

type SubAgentOrchestrator struct {
	db  dbExecutor
	hub *realtime.Hub
	bus *events.Bus
}

func NewSubAgentOrchestrator(db dbExecutor, hub *realtime.Hub, bus *events.Bus) *SubAgentOrchestrator {
	return &SubAgentOrchestrator{db: db, hub: hub, bus: bus}
}

type SubAgentWorkspace struct {
	ID                     string    `json:"id"`
	WorkspaceID            string    `json:"workspace_id"`
	ParentAgentID          *string   `json:"parent_agent_id"`
	Name                   string    `json:"name"`
	BasePath               string    `json:"base_path"`
	SnapshotRetentionCount int32     `json:"snapshot_retention_count"`
	IsolationMode          string    `json:"isolation_mode"`
	Status                 string    `json:"status"`
	CreatedAt              time.Time `json:"created_at"`
	UpdatedAt              time.Time `json:"updated_at"`
}

type SubAgentSpawn struct {
	ID            string     `json:"id"`
	WorkspaceID   string     `json:"workspace_id"`
	ParentTaskID  *string    `json:"parent_task_id"`
	SubAgentType  string     `json:"sub_agent_type"`
	SpawnConfig   string     `json:"spawn_config"`
	ContainerID   *string    `json:"container_id"`
	SandboxStatus string     `json:"sandbox_status"`
	StartedAt     *time.Time `json:"started_at"`
	CompletedAt   *time.Time `json:"completed_at"`
	ExitCode      *int32     `json:"exit_code"`
	CreatedAt     time.Time  `json:"created_at"`
	UpdatedAt     time.Time  `json:"updated_at"`
}

func (s *SubAgentOrchestrator) CreateWorkspace(ctx context.Context, workspaceID, parentAgentID, name, basePath, isolationMode string) (*SubAgentWorkspace, error) {
	var w SubAgentWorkspace
	err := s.db.QueryRow(ctx,
		`INSERT INTO sub_agent_workspace (workspace_id, parent_agent_id, name, base_path, isolation_mode)
         VALUES ($1, $2, $3, $4, $5)
         RETURNING id, workspace_id, parent_agent_id, name, base_path, snapshot_retention_count, isolation_mode, status, created_at, updated_at`,
		util.MustParseUUID(workspaceID), util.MustParseUUID(parentAgentID), name, basePath, isolationMode,
	).Scan(&w.ID, &w.WorkspaceID, &w.ParentAgentID, &w.Name, &w.BasePath,
		&w.SnapshotRetentionCount, &w.IsolationMode, &w.Status, &w.CreatedAt, &w.UpdatedAt)
	if err != nil {
		return nil, fmt.Errorf("create sub-agent workspace: %w", err)
	}
	slog.Info("sub-agent workspace created", "sub_workspace_id", w.ID, "parent_agent_id", w.ParentAgentID)
	return &w, nil
}

func (s *SubAgentOrchestrator) GetWorkspace(ctx context.Context, id string) (*SubAgentWorkspace, error) {
	var w SubAgentWorkspace
	err := s.db.QueryRow(ctx,
		`SELECT id, workspace_id, parent_agent_id, name, base_path, snapshot_retention_count, isolation_mode, status, created_at, updated_at
         FROM sub_agent_workspace WHERE id = $1`,
		util.MustParseUUID(id),
	).Scan(&w.ID, &w.WorkspaceID, &w.ParentAgentID, &w.Name, &w.BasePath,
		&w.SnapshotRetentionCount, &w.IsolationMode, &w.Status, &w.CreatedAt, &w.UpdatedAt)
	if err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			return nil, fmt.Errorf("sub-agent workspace not found")
		}
		return nil, fmt.Errorf("get sub-agent workspace: %w", err)
	}
	return &w, nil
}

func (s *SubAgentOrchestrator) ListWorkspacesByAgent(ctx context.Context, parentAgentID string) ([]SubAgentWorkspace, error) {
	rows, err := s.db.Query(ctx,
		`SELECT id, workspace_id, parent_agent_id, name, base_path, snapshot_retention_count, isolation_mode, status, created_at, updated_at
         FROM sub_agent_workspace WHERE parent_agent_id = $1 AND status = 'active'
         ORDER BY created_at DESC`,
		util.MustParseUUID(parentAgentID),
	)
	if err != nil {
		return nil, fmt.Errorf("list sub-agent workspaces: %w", err)
	}
	defer rows.Close()

	var workspaces []SubAgentWorkspace
	for rows.Next() {
		var w SubAgentWorkspace
		if err := rows.Scan(&w.ID, &w.WorkspaceID, &w.ParentAgentID, &w.Name, &w.BasePath,
			&w.SnapshotRetentionCount, &w.IsolationMode, &w.Status, &w.CreatedAt, &w.UpdatedAt); err != nil {
			return nil, fmt.Errorf("scan workspace: %w", err)
		}
		workspaces = append(workspaces, w)
	}
	return workspaces, rows.Err()
}

func (s *SubAgentOrchestrator) SpawnSubAgent(ctx context.Context, workspaceID, parentTaskID, subAgentType string, spawnConfig map[string]any) (*SubAgentSpawn, error) {
	configJSON, err := json.Marshal(spawnConfig)
	if err != nil {
		return nil, fmt.Errorf("marshal spawn config: %w", err)
	}

	var spawn SubAgentSpawn
	var cid pgtype.Text
	var taskID pgtype.UUID
	var startedAt, completedAt pgtype.Timestamptz
	var exitCode pgtype.Int4

	if parentTaskID != "" {
		taskID = util.MustParseUUID(parentTaskID)
	}

	err = s.db.QueryRow(ctx,
		`INSERT INTO sub_agent_spawn (workspace_id, parent_task_id, sub_agent_type, spawn_config)
         VALUES ($1, $2, $3, $4::jsonb)
         RETURNING id, workspace_id, parent_task_id, sub_agent_type, spawn_config::text, container_id, sandbox_status, started_at, completed_at, exit_code, created_at, updated_at`,
		util.MustParseUUID(workspaceID), taskID, subAgentType, string(configJSON),
	).Scan(&spawn.ID, &spawn.WorkspaceID, &spawn.ParentTaskID, &spawn.SubAgentType, &spawn.SpawnConfig,
		&cid, &spawn.SandboxStatus, &startedAt, &completedAt, &exitCode, &spawn.CreatedAt, &spawn.UpdatedAt)
	if err != nil {
		return nil, fmt.Errorf("create sub-agent spawn: %w", err)
	}

	if cid.Valid {
		spawn.ContainerID = &cid.String
	}
	if startedAt.Valid {
		t := startedAt.Time
		spawn.StartedAt = &t
	}
	if completedAt.Valid {
		t := completedAt.Time
		spawn.CompletedAt = &t
	}
	if exitCode.Valid {
		code := exitCode.Int32
		spawn.ExitCode = &code
	}

	slog.Info("sub-agent spawned", "spawn_id", spawn.ID, "type", subAgentType, "workspace_id", workspaceID)
	return &spawn, nil
}

func (s *SubAgentOrchestrator) ListSpawns(ctx context.Context, workspaceID string) ([]SubAgentSpawn, error) {
	rows, err := s.db.Query(ctx,
		`SELECT id, workspace_id, parent_task_id, sub_agent_type, spawn_config::text, container_id, sandbox_status, started_at, completed_at, exit_code, created_at, updated_at
         FROM sub_agent_spawn WHERE workspace_id = $1
         ORDER BY created_at DESC`,
		util.MustParseUUID(workspaceID),
	)
	if err != nil {
		return nil, fmt.Errorf("list sub-agent spawns: %w", err)
	}
	defer rows.Close()

	var spawns []SubAgentSpawn
	for rows.Next() {
		var sp SubAgentSpawn
		var cid pgtype.Text
		var startedAt, completedAt pgtype.Timestamptz
		var exitCode pgtype.Int4
		if err := rows.Scan(&sp.ID, &sp.WorkspaceID, &sp.ParentTaskID, &sp.SubAgentType, &sp.SpawnConfig,
			&cid, &sp.SandboxStatus, &startedAt, &completedAt, &exitCode, &sp.CreatedAt, &sp.UpdatedAt); err != nil {
			return nil, fmt.Errorf("scan spawn: %w", err)
		}
		if cid.Valid {
			sp.ContainerID = &cid.String
		}
		if startedAt.Valid {
			t := startedAt.Time
			sp.StartedAt = &t
		}
		if completedAt.Valid {
			t := completedAt.Time
			sp.CompletedAt = &t
		}
		if exitCode.Valid {
			code := exitCode.Int32
			sp.ExitCode = &code
		}
		spawns = append(spawns, sp)
	}
	return spawns, rows.Err()
}

func (s *SubAgentOrchestrator) GetSpawnStatus(ctx context.Context, spawnID string) (*SubAgentSpawn, error) {
	var sp SubAgentSpawn
	var cid pgtype.Text
	var startedAt, completedAt pgtype.Timestamptz
	var exitCode pgtype.Int4
	err := s.db.QueryRow(ctx,
		`SELECT id, workspace_id, parent_task_id, sub_agent_type, spawn_config::text, container_id, sandbox_status, started_at, completed_at, exit_code, created_at, updated_at
         FROM sub_agent_spawn WHERE id = $1`,
		util.MustParseUUID(spawnID),
	).Scan(&sp.ID, &sp.WorkspaceID, &sp.ParentTaskID, &sp.SubAgentType, &sp.SpawnConfig,
		&cid, &sp.SandboxStatus, &startedAt, &completedAt, &exitCode, &sp.CreatedAt, &sp.UpdatedAt)
	if err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			return nil, fmt.Errorf("sub-agent spawn not found")
		}
		return nil, fmt.Errorf("get spawn status: %w", err)
	}
	if cid.Valid {
		sp.ContainerID = &cid.String
	}
	if startedAt.Valid {
		t := startedAt.Time
		sp.StartedAt = &t
	}
	if completedAt.Valid {
		t := completedAt.Time
		sp.CompletedAt = &t
	}
	if exitCode.Valid {
		code := exitCode.Int32
		sp.ExitCode = &code
	}
	return &sp, nil
}

func (s *SubAgentOrchestrator) UpdateSpawnStatus(ctx context.Context, spawnID, sandboxStatus string, exitCode *int32) error {
	tag, err := s.db.Exec(ctx,
		`UPDATE sub_agent_spawn SET sandbox_status = $2, exit_code = $3,
         started_at = CASE WHEN $2 = 'running' AND started_at IS NULL THEN now() ELSE started_at END,
         completed_at = CASE WHEN $2 IN ('completed', 'failed', 'timeout', 'cancelled') THEN now() ELSE completed_at END,
         updated_at = now()
         WHERE id = $1`,
		util.MustParseUUID(spawnID), sandboxStatus, exitCode,
	)
	if err != nil {
		return fmt.Errorf("update spawn status: %w", err)
	}
	if tag.RowsAffected() == 0 {
		return fmt.Errorf("sub-agent spawn not found: %s", spawnID)
	}
	slog.Info("sub-agent spawn status updated", "spawn_id", spawnID, "status", sandboxStatus)
	return nil
}
