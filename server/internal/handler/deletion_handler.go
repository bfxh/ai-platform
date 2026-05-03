package handler

import (
	"encoding/json"
	"log/slog"
	"net/http"

	"github.com/go-chi/chi/v5"
)

type RequestDeletionRequest struct {
	FilePath string  `json:"file_path"`
	FileSize int64   `json:"file_size"`
	FileHash string  `json:"file_hash"`
	Reason   string  `json:"reason"`
	SpawnID  *string `json:"spawn_id"`
}

type BulkApproveRequest struct {
	DeletionIDs []string `json:"deletion_ids"`
}

func (h *Handler) ListPendingDeletions(w http.ResponseWriter, r *http.Request) {
	_, ok := requireUserID(w, r)
	if !ok {
		return
	}

	workspaceID := workspaceIDFromURL(r, "id")
	if workspaceID == "" {
		writeError(w, http.StatusBadRequest, "workspace_id is required")
		return
	}

	deletions, err := h.DeletionReviewService.ListPendingDeletions(r.Context(), workspaceID)
	if err != nil {
		slog.Error("failed to list pending deletions", "error", err, "workspace_id", workspaceID)
		writeError(w, http.StatusInternalServerError, "failed to list pending deletions")
		return
	}

	writeJSON(w, http.StatusOK, deletions)
}

func (h *Handler) ApproveDeletion(w http.ResponseWriter, r *http.Request) {
	userID, ok := requireUserID(w, r)
	if !ok {
		return
	}

	deletionID := chi.URLParam(r, "id")
	if _, ok := parseUUIDOrBadRequest(w, deletionID, "deletion_id"); !ok {
		return
	}

	result, err := h.DeletionReviewService.ApproveDeletion(r.Context(), deletionID, userID)
	if err != nil {
		writeError(w, http.StatusNotFound, "deletion request not found")
		return
	}

	writeJSON(w, http.StatusOK, result)
}

func (h *Handler) RejectDeletion(w http.ResponseWriter, r *http.Request) {
	userID, ok := requireUserID(w, r)
	if !ok {
		return
	}

	deletionID := chi.URLParam(r, "id")
	if _, ok := parseUUIDOrBadRequest(w, deletionID, "deletion_id"); !ok {
		return
	}

	result, err := h.DeletionReviewService.RejectDeletion(r.Context(), deletionID, userID)
	if err != nil {
		writeError(w, http.StatusNotFound, "deletion request not found")
		return
	}

	writeJSON(w, http.StatusOK, result)
}

func (h *Handler) BulkApproveDeletions(w http.ResponseWriter, r *http.Request) {
	userID, ok := requireUserID(w, r)
	if !ok {
		return
	}

	workspaceID := workspaceIDFromURL(r, "id")
	if workspaceID == "" {
		writeError(w, http.StatusBadRequest, "workspace_id is required")
		return
	}

	var req BulkApproveRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "invalid request body")
		return
	}

	if len(req.DeletionIDs) == 0 {
		writeError(w, http.StatusBadRequest, "deletion_ids is required")
		return
	}

	if _, ok := parseUUIDSliceOrBadRequest(w, req.DeletionIDs, "deletion_ids"); !ok {
		return
	}

	count, err := h.DeletionReviewService.BulkApprove(r.Context(), req.DeletionIDs, userID)
	if err != nil {
		slog.Error("failed to bulk approve deletions", "error", err, "workspace_id", workspaceID)
		writeError(w, http.StatusInternalServerError, "failed to bulk approve deletions")
		return
	}

	writeJSON(w, http.StatusOK, map[string]int64{"approved_count": count})
}
