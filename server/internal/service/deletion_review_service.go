package service

import (
	"context"
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

type DeletionReviewService struct {
	db  dbExecutor
	hub *realtime.Hub
	bus *events.Bus
}

func NewDeletionReviewService(db dbExecutor, hub *realtime.Hub, bus *events.Bus) *DeletionReviewService {
	return &DeletionReviewService{db: db, hub: hub, bus: bus}
}

type PendingDeletion struct {
	ID               string     `json:"id"`
	WorkspaceID      string     `json:"workspace_id"`
	SpawnID          *string    `json:"spawn_id"`
	FilePath         string     `json:"file_path"`
	FileSize         int64      `json:"file_size"`
	FileHash         string     `json:"file_hash"`
	RequestedByAgent string     `json:"requested_by_agent"`
	Reason           *string    `json:"reason"`
	Status           string     `json:"status"`
	ReviewedBy       *string    `json:"reviewed_by"`
	ReviewedAt       *time.Time `json:"reviewed_at"`
	RequestedAt      time.Time  `json:"requested_at"`
	CreatedAt        time.Time  `json:"created_at"`
}

func (s *DeletionReviewService) RequestDeletion(ctx context.Context, workspaceID, filePath, fileHash, requestedByAgent, reason string, fileSize int64, spawnID *string) (*PendingDeletion, error) {
	var d PendingDeletion
	var spID pgtype.UUID
	var rsn pgtype.Text
	var revBy pgtype.UUID
	var revAt pgtype.Timestamptz
	if spawnID != nil {
		spID = util.MustParseUUID(*spawnID)
		spID.Valid = true
	}
	if reason != "" {
		rsn = pgtype.Text{String: reason, Valid: true}
	}

	err := s.db.QueryRow(ctx,
		`INSERT INTO pending_deletion (workspace_id, spawn_id, file_path, file_size, file_hash, requested_by_agent, reason)
         VALUES ($1, $2, $3, $4, $5, $6, $7)
         RETURNING id, workspace_id, spawn_id, file_path, file_size, file_hash, requested_by_agent, reason, status, reviewed_by, reviewed_at, requested_at, created_at`,
		util.MustParseUUID(workspaceID), spID, filePath, fileSize, fileHash, requestedByAgent, rsn,
	).Scan(&d.ID, &d.WorkspaceID, &spID, &d.FilePath, &d.FileSize, &d.FileHash,
		&d.RequestedByAgent, &rsn, &d.Status, &revBy, &revAt, &d.RequestedAt, &d.CreatedAt)
	if err != nil {
		return nil, fmt.Errorf("request deletion: %w", err)
	}

	if spID.Valid {
		s := util.UUIDToString(spID)
		d.SpawnID = &s
	}
	if rsn.Valid {
		d.Reason = &rsn.String
	}
	if revBy.Valid {
		s := util.UUIDToString(revBy)
		d.ReviewedBy = &s
	}
	if revAt.Valid {
		t := revAt.Time
		d.ReviewedAt = &t
	}

	slog.Info("deletion requested", "deletion_id", d.ID, "file", filePath, "agent", requestedByAgent)
	return &d, nil
}

func (s *DeletionReviewService) ListPendingDeletions(ctx context.Context, workspaceID string) ([]PendingDeletion, error) {
	rows, err := s.db.Query(ctx,
		`SELECT id, workspace_id, spawn_id, file_path, file_size, file_hash, requested_by_agent, reason, status, reviewed_by, reviewed_at, requested_at, created_at
         FROM pending_deletion WHERE workspace_id = $1 AND status = 'pending'
         ORDER BY requested_at DESC`,
		util.MustParseUUID(workspaceID),
	)
	if err != nil {
		return nil, fmt.Errorf("list pending deletions: %w", err)
	}
	defer rows.Close()

	var deletions []PendingDeletion
	for rows.Next() {
		var d PendingDeletion
		var spID pgtype.UUID
		var rsn pgtype.Text
		var revBy pgtype.UUID
		var revAt pgtype.Timestamptz
		if err := rows.Scan(&d.ID, &d.WorkspaceID, &spID, &d.FilePath, &d.FileSize, &d.FileHash,
			&d.RequestedByAgent, &rsn, &d.Status, &revBy, &revAt, &d.RequestedAt, &d.CreatedAt); err != nil {
			return nil, fmt.Errorf("scan pending deletion: %w", err)
		}
		if spID.Valid {
			s := util.UUIDToString(spID)
			d.SpawnID = &s
		}
		if rsn.Valid {
			d.Reason = &rsn.String
		}
		if revBy.Valid {
			s := util.UUIDToString(revBy)
			d.ReviewedBy = &s
		}
		if revAt.Valid {
			t := revAt.Time
			d.ReviewedAt = &t
		}
		deletions = append(deletions, d)
	}
	return deletions, rows.Err()
}

func (s *DeletionReviewService) ApproveDeletion(ctx context.Context, deletionID, reviewedBy string) (*PendingDeletion, error) {
	var d PendingDeletion
	var spID pgtype.UUID
	var rsn pgtype.Text
	var revBy pgtype.UUID
	var revAt pgtype.Timestamptz
	err := s.db.QueryRow(ctx,
		`UPDATE pending_deletion SET status = 'approved', reviewed_by = $2, reviewed_at = now()
         WHERE id = $1
         RETURNING id, workspace_id, spawn_id, file_path, file_size, file_hash, requested_by_agent, reason, status, reviewed_by, reviewed_at, requested_at, created_at`,
		util.MustParseUUID(deletionID), util.MustParseUUID(reviewedBy),
	).Scan(&d.ID, &d.WorkspaceID, &spID, &d.FilePath, &d.FileSize, &d.FileHash,
		&d.RequestedByAgent, &rsn, &d.Status, &revBy, &revAt, &d.RequestedAt, &d.CreatedAt)
	if err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			return nil, fmt.Errorf("deletion request not found")
		}
		return nil, fmt.Errorf("approve deletion: %w", err)
	}
	if spID.Valid {
		s := util.UUIDToString(spID)
		d.SpawnID = &s
	}
	if rsn.Valid {
		d.Reason = &rsn.String
	}
	if revBy.Valid {
		s := util.UUIDToString(revBy)
		d.ReviewedBy = &s
	}
	if revAt.Valid {
		t := revAt.Time
		d.ReviewedAt = &t
	}
	slog.Info("deletion approved", "deletion_id", deletionID, "reviewed_by", reviewedBy)
	return &d, nil
}

func (s *DeletionReviewService) RejectDeletion(ctx context.Context, deletionID, reviewedBy string) (*PendingDeletion, error) {
	var d PendingDeletion
	var spID pgtype.UUID
	var rsn pgtype.Text
	var revBy pgtype.UUID
	var revAt pgtype.Timestamptz
	err := s.db.QueryRow(ctx,
		`UPDATE pending_deletion SET status = 'rejected', reviewed_by = $2, reviewed_at = now()
         WHERE id = $1
         RETURNING id, workspace_id, spawn_id, file_path, file_size, file_hash, requested_by_agent, reason, status, reviewed_by, reviewed_at, requested_at, created_at`,
		util.MustParseUUID(deletionID), util.MustParseUUID(reviewedBy),
	).Scan(&d.ID, &d.WorkspaceID, &spID, &d.FilePath, &d.FileSize, &d.FileHash,
		&d.RequestedByAgent, &rsn, &d.Status, &revBy, &revAt, &d.RequestedAt, &d.CreatedAt)
	if err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			return nil, fmt.Errorf("deletion request not found")
		}
		return nil, fmt.Errorf("reject deletion: %w", err)
	}
	if spID.Valid {
		s := util.UUIDToString(spID)
		d.SpawnID = &s
	}
	if rsn.Valid {
		d.Reason = &rsn.String
	}
	if revBy.Valid {
		s := util.UUIDToString(revBy)
		d.ReviewedBy = &s
	}
	if revAt.Valid {
		t := revAt.Time
		d.ReviewedAt = &t
	}
	slog.Info("deletion rejected", "deletion_id", deletionID, "reviewed_by", reviewedBy)
	return &d, nil
}

func (s *DeletionReviewService) BulkApprove(ctx context.Context, deletionIDs []string, reviewedBy string) (int64, error) {
	uuids := make([]pgtype.UUID, len(deletionIDs))
	for i, id := range deletionIDs {
		uuids[i] = util.MustParseUUID(id)
	}

	tag, err := s.db.Exec(ctx,
		`UPDATE pending_deletion SET status = 'approved', reviewed_by = $2, reviewed_at = now()
         WHERE id = ANY($1) AND status = 'pending'`,
		uuids, util.MustParseUUID(reviewedBy),
	)
	if err != nil {
		return 0, fmt.Errorf("bulk approve deletions: %w", err)
	}
	count := tag.RowsAffected()
	slog.Info("deletions bulk approved", "count", count, "reviewed_by", reviewedBy)
	return count, nil
}
