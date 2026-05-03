package service

import (
	"context"
	"errors"
	"fmt"
	"log/slog"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgtype"
	"github.com/multica-ai/multica/server/internal/util"
)

type LearnedRuleService struct {
	db dbExecutor
}

func NewLearnedRuleService(db dbExecutor) *LearnedRuleService {
	return &LearnedRuleService{db: db}
}

type LearnedRule struct {
	ID             string    `json:"id"`
	WorkspaceID    string    `json:"workspace_id"`
	ErrorPattern   string    `json:"error_pattern"`
	FixStrategy    string    `json:"fix_strategy"`
	SourceTaskType *string   `json:"source_task_type"`
	SuccessCount   int32     `json:"success_count"`
	TotalAttempts  int32     `json:"total_attempts"`
	Confidence     float64   `json:"confidence"`
	AutoApply      bool      `json:"auto_apply"`
	CreatedAt      time.Time `json:"created_at"`
	UpdatedAt      time.Time `json:"updated_at"`
}

func (s *LearnedRuleService) LearnFromFailure(ctx context.Context, workspaceID, errorPattern, fixStrategy, sourceTaskType string) (*LearnedRule, error) {
	// Try to find existing rule with same error pattern
	var r LearnedRule
	var stt pgtype.Text
	err := s.db.QueryRow(ctx,
		`SELECT id, workspace_id, error_pattern, fix_strategy, source_task_type, success_count, total_attempts, confidence, auto_apply, created_at, updated_at
         FROM learned_rule WHERE workspace_id = $1 AND error_pattern = $2`,
		util.MustParseUUID(workspaceID), errorPattern,
	).Scan(&r.ID, &r.WorkspaceID, &r.ErrorPattern, &r.FixStrategy, &stt,
		&r.SuccessCount, &r.TotalAttempts, &r.Confidence, &r.AutoApply, &r.CreatedAt, &r.UpdatedAt)

	if err == nil {
		// Update existing rule
		newAttempts := r.TotalAttempts + 1
		newConfidence := float64(r.SuccessCount) / float64(newAttempts)
		autoApply := newConfidence >= 0.8

		err = s.db.QueryRow(ctx,
			`UPDATE learned_rule SET fix_strategy = $3, source_task_type = $4, total_attempts = $5, confidence = $6, auto_apply = $7, updated_at = now()
             WHERE id = $1
             RETURNING id, workspace_id, error_pattern, fix_strategy, source_task_type, success_count, total_attempts, confidence, auto_apply, created_at, updated_at`,
			util.MustParseUUID(r.ID), fixStrategy, sourceTaskType, newAttempts, newConfidence, autoApply,
		).Scan(&r.ID, &r.WorkspaceID, &r.ErrorPattern, &r.FixStrategy, &stt,
			&r.SuccessCount, &r.TotalAttempts, &r.Confidence, &r.AutoApply, &r.CreatedAt, &r.UpdatedAt)
		if err != nil {
			return nil, fmt.Errorf("update learned rule: %w", err)
		}
		slog.Info("learned rule updated", "rule_id", r.ID, "confidence", r.Confidence, "auto_apply", r.AutoApply)
	} else if errors.Is(err, pgx.ErrNoRows) {
		// Create new rule
		stt = pgtype.Text{String: sourceTaskType, Valid: sourceTaskType != ""}
		err = s.db.QueryRow(ctx,
			`INSERT INTO learned_rule (workspace_id, error_pattern, fix_strategy, source_task_type, total_attempts, confidence, auto_apply)
             VALUES ($1, $2, $3, $4, 1, 0, FALSE)
             RETURNING id, workspace_id, error_pattern, fix_strategy, source_task_type, success_count, total_attempts, confidence, auto_apply, created_at, updated_at`,
			util.MustParseUUID(workspaceID), errorPattern, fixStrategy, stt,
		).Scan(&r.ID, &r.WorkspaceID, &r.ErrorPattern, &r.FixStrategy, &stt,
			&r.SuccessCount, &r.TotalAttempts, &r.Confidence, &r.AutoApply, &r.CreatedAt, &r.UpdatedAt)
		if err != nil {
			return nil, fmt.Errorf("create learned rule: %w", err)
		}
		slog.Info("learned rule created", "rule_id", r.ID, "error_pattern", errorPattern)
	} else {
		return nil, fmt.Errorf("lookup learned rule: %w", err)
	}

	if stt.Valid {
		r.SourceTaskType = &stt.String
	}
	return &r, nil
}

func (s *LearnedRuleService) MarkSuccess(ctx context.Context, ruleID string) (*LearnedRule, error) {
	var r LearnedRule
	var stt pgtype.Text
	err := s.db.QueryRow(ctx,
		`UPDATE learned_rule SET success_count = success_count + 1, total_attempts = total_attempts + 1,
         confidence = CASE WHEN total_attempts + 1 > 0 THEN (success_count + 1)::float / (total_attempts + 1)::float ELSE 0 END,
         auto_apply = CASE WHEN (success_count + 1)::float / (total_attempts + 1)::float >= 0.8 THEN TRUE ELSE FALSE END,
         updated_at = now()
         WHERE id = $1
         RETURNING id, workspace_id, error_pattern, fix_strategy, source_task_type, success_count, total_attempts, confidence, auto_apply, created_at, updated_at`,
		util.MustParseUUID(ruleID),
	).Scan(&r.ID, &r.WorkspaceID, &r.ErrorPattern, &r.FixStrategy, &stt,
		&r.SuccessCount, &r.TotalAttempts, &r.Confidence, &r.AutoApply, &r.CreatedAt, &r.UpdatedAt)
	if err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			return nil, fmt.Errorf("learned rule not found")
		}
		return nil, fmt.Errorf("mark learned rule success: %w", err)
	}
	if stt.Valid {
		r.SourceTaskType = &stt.String
	}
	return &r, nil
}

func (s *LearnedRuleService) MatchRule(ctx context.Context, workspaceID, errorStr string) (*LearnedRule, error) {
	// Find the highest-confidence auto-apply rule that matches
	rows, err := s.db.Query(ctx,
		`SELECT id, workspace_id, error_pattern, fix_strategy, source_task_type, success_count, total_attempts, confidence, auto_apply, created_at, updated_at
         FROM learned_rule WHERE workspace_id = $1 AND auto_apply = TRUE AND $2 ILIKE '%' || error_pattern || '%'
         ORDER BY confidence DESC LIMIT 1`,
		util.MustParseUUID(workspaceID), errorStr,
	)
	if err != nil {
		return nil, fmt.Errorf("match learned rule: %w", err)
	}
	defer rows.Close()

	if !rows.Next() {
		return nil, fmt.Errorf("no matching learned rule")
	}

	var r LearnedRule
	var stt pgtype.Text
	if err := rows.Scan(&r.ID, &r.WorkspaceID, &r.ErrorPattern, &r.FixStrategy, &stt,
		&r.SuccessCount, &r.TotalAttempts, &r.Confidence, &r.AutoApply, &r.CreatedAt, &r.UpdatedAt); err != nil {
		return nil, fmt.Errorf("scan matched rule: %w", err)
	}
	if stt.Valid {
		r.SourceTaskType = &stt.String
	}
	return &r, nil
}

func (s *LearnedRuleService) ListAutoApplyRules(ctx context.Context, workspaceID string) ([]LearnedRule, error) {
	rows, err := s.db.Query(ctx,
		`SELECT id, workspace_id, error_pattern, fix_strategy, source_task_type, success_count, total_attempts, confidence, auto_apply, created_at, updated_at
         FROM learned_rule WHERE workspace_id = $1 AND auto_apply = TRUE
         ORDER BY confidence DESC`,
		util.MustParseUUID(workspaceID),
	)
	if err != nil {
		return nil, fmt.Errorf("list auto-apply rules: %w", err)
	}
	defer rows.Close()

	var rules []LearnedRule
	for rows.Next() {
		var r LearnedRule
		var stt pgtype.Text
		if err := rows.Scan(&r.ID, &r.WorkspaceID, &r.ErrorPattern, &r.FixStrategy, &stt,
			&r.SuccessCount, &r.TotalAttempts, &r.Confidence, &r.AutoApply, &r.CreatedAt, &r.UpdatedAt); err != nil {
			return nil, fmt.Errorf("scan learned rule: %w", err)
		}
		if stt.Valid {
			r.SourceTaskType = &stt.String
		}
		rules = append(rules, r)
	}
	return rules, rows.Err()
}
