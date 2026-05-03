package handler

import (
	"encoding/json"
	"log/slog"
	"net/http"
)

type CreateResourceProfileRequest struct {
	TaskType      string   `json:"task_type"`
	PriorityTier  string   `json:"priority_tier"`
	GPUMemMB      int32    `json:"estimated_gpu_memory_mb"`
	CPUCores      int32    `json:"estimated_cpu_cores"`
	MemMB         int32    `json:"estimated_memory_mb"`
	MaxRetries    int32    `json:"max_retries"`
	PreCheckRules []string `json:"pre_check_rules"`
	RerouteTarget *string  `json:"reroute_target"`
}

func (h *Handler) CreateResourceProfile(w http.ResponseWriter, r *http.Request) {
	_, ok := requireUserID(w, r)
	if !ok {
		return
	}

	workspaceID := workspaceIDFromURL(r, "id")
	if workspaceID == "" {
		writeError(w, http.StatusBadRequest, "workspace_id is required")
		return
	}

	var req CreateResourceProfileRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "invalid request body")
		return
	}

	if req.TaskType == "" {
		writeError(w, http.StatusBadRequest, "task_type is required")
		return
	}
	if req.PriorityTier == "" {
		req.PriorityTier = "normal"
	}
	if req.PriorityTier != "fast" && req.PriorityTier != "normal" && req.PriorityTier != "heavy" && req.PriorityTier != "gpu" {
		writeError(w, http.StatusBadRequest, "priority_tier must be one of: fast, normal, heavy, gpu")
		return
	}

	profile, err := h.ResourceProfileService.CreateProfile(r.Context(), workspaceID, req.TaskType, req.PriorityTier,
		req.GPUMemMB, req.CPUCores, req.MemMB, req.MaxRetries, req.PreCheckRules, req.RerouteTarget)
	if err != nil {
		slog.Error("failed to create resource profile", "error", err, "workspace_id", workspaceID)
		writeError(w, http.StatusInternalServerError, "failed to create resource profile")
		return
	}

	writeJSON(w, http.StatusCreated, profile)
}

func (h *Handler) ListResourceProfiles(w http.ResponseWriter, r *http.Request) {
	_, ok := requireUserID(w, r)
	if !ok {
		return
	}

	workspaceID := workspaceIDFromURL(r, "id")
	if workspaceID == "" {
		writeError(w, http.StatusBadRequest, "workspace_id is required")
		return
	}

	profiles, err := h.ResourceProfileService.ListProfiles(r.Context(), workspaceID)
	if err != nil {
		slog.Error("failed to list resource profiles", "error", err, "workspace_id", workspaceID)
		writeError(w, http.StatusInternalServerError, "failed to list resource profiles")
		return
	}

	writeJSON(w, http.StatusOK, profiles)
}
