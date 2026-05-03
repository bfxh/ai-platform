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
	"github.com/multica-ai/multica/server/internal/events"
	"github.com/multica-ai/multica/server/internal/realtime"
	"github.com/multica-ai/multica/server/internal/util"
)

// dbExecutor is defined in subagent_orchestrator.go; this file reuses it.

type SnapshotService struct {
	db  dbExecutor
	hub *realtime.Hub
	bus *events.Bus
}

func NewSnapshotService(db dbExecutor, hub *realtime.Hub, bus *events.Bus) *SnapshotService {
	return &SnapshotService{db: db, hub: hub, bus: bus}
}

type TaskSnapshot struct {
	ID             string    `json:"id"`
	WorkspaceID    string    `json:"workspace_id"`
	TaskID         *string   `json:"task_id"`
	SpawnID        *string   `json:"spawn_id"`
	SnapshotType   string    `json:"snapshot_type"`
	Label          *string   `json:"label"`
	FileDiff       string    `json:"file_diff"`
	StoragePath    string    `json:"storage_path"`
	TotalSizeBytes int64     `json:"total_size_bytes"`
	FileCount      int32     `json:"file_count"`
	CreatedAt      time.Time `json:"created_at"`
}

type SnapshotDiff struct {
	Added     []string `json:"added"`
	Modified  []string `json:"modified"`
	Deleted   []string `json:"deleted"`
	Unchanged []string `json:"unchanged"`
}

func (s *SnapshotService) CreateSnapshot(ctx context.Context, workspaceID, snapshotType, label, storagePath string, taskID, spawnID *string, fileDiff SnapshotDiff) (*TaskSnapshot, error) {
	diffJSON, err := json.Marshal(fileDiff)
	if err != nil {
		return nil, fmt.Errorf("marshal file diff: %w", err)
	}

	var snap TaskSnapshot
	var tID, spID pgtype.UUID
	var lbl pgtype.Text
	if taskID != nil {
		tID = util.MustParseUUID(*taskID)
		tID.Valid = true
	}
	if spawnID != nil {
		spID = util.MustParseUUID(*spawnID)
		spID.Valid = true
	}
	if label != "" {
		lbl = pgtype.Text{String: label, Valid: true}
	}

	err = s.db.QueryRow(ctx,
		`INSERT INTO task_snapshot (workspace_id, task_id, spawn_id, snapshot_type, label, file_diff, storage_path)
         VALUES ($1, $2, $3, $4, $5, $6::jsonb, $7)
         RETURNING id, workspace_id, task_id, spawn_id, snapshot_type, label, file_diff::text, storage_path, total_size_bytes, file_count, created_at`,
		util.MustParseUUID(workspaceID), tID, spID, snapshotType, lbl, string(diffJSON), storagePath,
	).Scan(&snap.ID, &snap.WorkspaceID, &tID, &spID, &snap.SnapshotType, &lbl,
		&snap.FileDiff, &snap.StoragePath, &snap.TotalSizeBytes, &snap.FileCount, &snap.CreatedAt)
	if err != nil {
		return nil, fmt.Errorf("create snapshot: %w", err)
	}

	if tID.Valid {
		s := util.UUIDToString(tID)
		snap.TaskID = &s
	}
	if spID.Valid {
		s := util.UUIDToString(spID)
		snap.SpawnID = &s
	}
	if lbl.Valid {
		snap.Label = &lbl.String
	}

	slog.Info("snapshot created", "snapshot_id", snap.ID, "type", snapshotType, "workspace_id", workspaceID)
	return &snap, nil
}

func (s *SnapshotService) GetSnapshot(ctx context.Context, id string) (*TaskSnapshot, error) {
	var snap TaskSnapshot
	var tID, spID pgtype.UUID
	var lbl pgtype.Text
	err := s.db.QueryRow(ctx,
		`SELECT id, workspace_id, task_id, spawn_id, snapshot_type, label, file_diff::text, storage_path, total_size_bytes, file_count, created_at
         FROM task_snapshot WHERE id = $1`,
		util.MustParseUUID(id),
	).Scan(&snap.ID, &snap.WorkspaceID, &tID, &spID, &snap.SnapshotType, &lbl,
		&snap.FileDiff, &snap.StoragePath, &snap.TotalSizeBytes, &snap.FileCount, &snap.CreatedAt)
	if err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			return nil, fmt.Errorf("snapshot not found")
		}
		return nil, fmt.Errorf("get snapshot: %w", err)
	}
	if tID.Valid {
		s := util.UUIDToString(tID)
		snap.TaskID = &s
	}
	if spID.Valid {
		s := util.UUIDToString(spID)
		snap.SpawnID = &s
	}
	if lbl.Valid {
		snap.Label = &lbl.String
	}
	return &snap, nil
}

func (s *SnapshotService) ListSnapshots(ctx context.Context, workspaceID string) ([]TaskSnapshot, error) {
	rows, err := s.db.Query(ctx,
		`SELECT id, workspace_id, task_id, spawn_id, snapshot_type, label, file_diff::text, storage_path, total_size_bytes, file_count, created_at
         FROM task_snapshot WHERE workspace_id = $1
         ORDER BY created_at DESC`,
		util.MustParseUUID(workspaceID),
	)
	if err != nil {
		return nil, fmt.Errorf("list snapshots: %w", err)
	}
	defer rows.Close()

	var snapshots []TaskSnapshot
	for rows.Next() {
		var snap TaskSnapshot
		var tID, spID pgtype.UUID
		var lbl pgtype.Text
		if err := rows.Scan(&snap.ID, &snap.WorkspaceID, &tID, &spID, &snap.SnapshotType, &lbl,
			&snap.FileDiff, &snap.StoragePath, &snap.TotalSizeBytes, &snap.FileCount, &snap.CreatedAt); err != nil {
			return nil, fmt.Errorf("scan snapshot: %w", err)
		}
		if tID.Valid {
			s := util.UUIDToString(tID)
			snap.TaskID = &s
		}
		if spID.Valid {
			s := util.UUIDToString(spID)
			snap.SpawnID = &s
		}
		if lbl.Valid {
			snap.Label = &lbl.String
		}
		snapshots = append(snapshots, snap)
	}
	return snapshots, rows.Err()
}

func (s *SnapshotService) DeleteSnapshot(ctx context.Context, id string) error {
	tag, err := s.db.Exec(ctx, `DELETE FROM task_snapshot WHERE id = $1`, util.MustParseUUID(id))
	if err != nil {
		return fmt.Errorf("delete snapshot: %w", err)
	}
	if tag.RowsAffected() == 0 {
		return fmt.Errorf("snapshot not found")
	}
	slog.Info("snapshot deleted", "snapshot_id", id)
	return nil
}

func (s *SnapshotService) CleanupOldSnapshots(ctx context.Context, workspaceID string, retentionCount int32) (int64, error) {
	tag, err := s.db.Exec(ctx,
		`DELETE FROM task_snapshot WHERE workspace_id = $1 AND id NOT IN (
            SELECT id FROM task_snapshot WHERE workspace_id = $1
            ORDER BY created_at DESC LIMIT $2
        )`,
		util.MustParseUUID(workspaceID), retentionCount,
	)
	if err != nil {
		return 0, fmt.Errorf("cleanup old snapshots: %w", err)
	}
	deleted := tag.RowsAffected()
	if deleted > 0 {
		slog.Info("old snapshots cleaned up", "workspace_id", workspaceID, "deleted", deleted)
	}
	return deleted, nil
}
