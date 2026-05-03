package handler

import (
	"encoding/json"
	"log/slog"
	"net/http"

	"github.com/go-chi/chi/v5"
	"github.com/multica-ai/multica/server/internal/middleware"
	"github.com/multica-ai/multica/server/internal/service"
)

type CreateSnapshotRequest struct {
	SnapshotType string               `json:"snapshot_type"`
	Label        string               `json:"label"`
	FileDiff     service.SnapshotDiff `json:"file_diff"`
	TaskID       *string              `json:"task_id"`
	SpawnID      *string              `json:"spawn_id"`
}

func (h *Handler) CreateSnapshot(w http.ResponseWriter, r *http.Request) {
	_, ok := requireUserID(w, r)
	if !ok {
		return
	}

	workspaceID := middleware.ResolveWorkspaceIDFromRequest(r, h.Queries)
	if workspaceID == "" {
		writeError(w, http.StatusBadRequest, "workspace_id is required (set X-Workspace-ID header)")
		return
	}

	var req CreateSnapshotRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "invalid request body")
		return
	}

	if req.SnapshotType != "pre" && req.SnapshotType != "post" && req.SnapshotType != "manual" {
		writeError(w, http.StatusBadRequest, "snapshot_type must be one of: pre, post, manual")
		return
	}

	// storage_path is generated based on workspace and timestamp
	storagePath := workspaceID + "/snapshots/" + req.SnapshotType

	snapshot, err := h.SnapshotService.CreateSnapshot(r.Context(), workspaceID, req.SnapshotType, req.Label, storagePath, req.TaskID, req.SpawnID, req.FileDiff)
	if err != nil {
		slog.Error("failed to create snapshot", "error", err, "workspace_id", workspaceID)
		writeError(w, http.StatusInternalServerError, "failed to create snapshot")
		return
	}

	writeJSON(w, http.StatusCreated, snapshot)
}

func (h *Handler) GetSnapshot(w http.ResponseWriter, r *http.Request) {
	_, ok := requireUserID(w, r)
	if !ok {
		return
	}

	snapshotID := chi.URLParam(r, "id")
	if _, ok := parseUUIDOrBadRequest(w, snapshotID, "snapshot_id"); !ok {
		return
	}

	snapshot, err := h.SnapshotService.GetSnapshot(r.Context(), snapshotID)
	if err != nil {
		writeError(w, http.StatusNotFound, "snapshot not found")
		return
	}

	writeJSON(w, http.StatusOK, snapshot)
}

func (h *Handler) ListSnapshots(w http.ResponseWriter, r *http.Request) {
	_, ok := requireUserID(w, r)
	if !ok {
		return
	}

	workspaceID := workspaceIDFromURL(r, "id")
	if workspaceID == "" {
		writeError(w, http.StatusBadRequest, "workspace_id is required")
		return
	}

	snapshots, err := h.SnapshotService.ListSnapshots(r.Context(), workspaceID)
	if err != nil {
		slog.Error("failed to list snapshots", "error", err, "workspace_id", workspaceID)
		writeError(w, http.StatusInternalServerError, "failed to list snapshots")
		return
	}

	writeJSON(w, http.StatusOK, snapshots)
}

func (h *Handler) DeleteSnapshot(w http.ResponseWriter, r *http.Request) {
	_, ok := requireUserID(w, r)
	if !ok {
		return
	}

	snapshotID := chi.URLParam(r, "id")
	if _, ok := parseUUIDOrBadRequest(w, snapshotID, "snapshot_id"); !ok {
		return
	}

	if err := h.SnapshotService.DeleteSnapshot(r.Context(), snapshotID); err != nil {
		writeError(w, http.StatusNotFound, "snapshot not found")
		return
	}

	w.WriteHeader(http.StatusNoContent)
}
