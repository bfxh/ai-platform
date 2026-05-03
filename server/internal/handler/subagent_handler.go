package handler

import (
	"encoding/json"
	"log/slog"
	"net/http"

	"github.com/go-chi/chi/v5"
	"github.com/multica-ai/multica/server/internal/middleware"
)

// --- Request types ---

type CreateSubAgentWorkspaceRequest struct {
	Name          string `json:"name"`
	BasePath      string `json:"base_path"`
	IsolationMode string `json:"isolation_mode"`
}

type SpawnSubAgentRequest struct {
	SubAgentType string         `json:"sub_agent_type"`
	SpawnConfig  map[string]any `json:"spawn_config"`
}

// --- Workspace handlers ---

func (h *Handler) CreateSubAgentWorkspace(w http.ResponseWriter, r *http.Request) {
	userID, ok := requireUserID(w, r)
	if !ok {
		return
	}

	var req CreateSubAgentWorkspaceRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "invalid request body")
		return
	}

	// Try workspace_id from body, then from context, then from query
	workspaceID := middleware.ResolveWorkspaceIDFromRequest(r, h.Queries)
	if workspaceID == "" {
		writeError(w, http.StatusBadRequest, "workspace_id is required (set X-Workspace-ID header or ?workspace_id=...)")
		return
	}

	if req.Name == "" {
		writeError(w, http.StatusBadRequest, "name is required")
		return
	}
	if req.BasePath == "" {
		writeError(w, http.StatusBadRequest, "base_path is required")
		return
	}
	if req.IsolationMode == "" {
		req.IsolationMode = "process"
	}

	// parent_agent_id: use userID as fallback agent ID
	result, err := h.SubAgentOrchestrator.CreateWorkspace(r.Context(), workspaceID, userID, req.Name, req.BasePath, req.IsolationMode)
	if err != nil {
		slog.Error("failed to create sub-agent workspace", "error", err, "user_id", userID)
		writeError(w, http.StatusInternalServerError, "failed to create workspace")
		return
	}

	writeJSON(w, http.StatusCreated, result)
}

func (h *Handler) ListSubAgentWorkspaces(w http.ResponseWriter, r *http.Request) {
	userID, ok := requireUserID(w, r)
	if !ok {
		return
	}

	agentID := r.URL.Query().Get("agent_id")
	if agentID == "" || agentID == "current" {
		agentID = userID
	}

	if _, ok := parseUUIDOrBadRequest(w, agentID, "agent_id"); !ok {
		return
	}

	workspaces, err := h.SubAgentOrchestrator.ListWorkspacesByAgent(r.Context(), agentID)
	if err != nil {
		slog.Error("failed to list sub-agent workspaces", "error", err, "agent_id", agentID)
		writeError(w, http.StatusInternalServerError, "failed to list workspaces")
		return
	}

	writeJSON(w, http.StatusOK, workspaces)
}

// --- Spawn handlers ---

func (h *Handler) SpawnSubAgent(w http.ResponseWriter, r *http.Request) {
	_, ok := requireUserID(w, r)
	if !ok {
		return
	}

	subWorkspaceID := chi.URLParam(r, "subWorkspaceId")
	if subWorkspaceID == "" {
		writeError(w, http.StatusBadRequest, "sub_workspace_id is required")
		return
	}
	if _, ok := parseUUIDOrBadRequest(w, subWorkspaceID, "sub_workspace_id"); !ok {
		return
	}

	var req SpawnSubAgentRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "invalid request body")
		return
	}

	if req.SubAgentType == "" {
		writeError(w, http.StatusBadRequest, "sub_agent_type is required")
		return
	}
	if req.SubAgentType != "qoder" && req.SubAgentType != "trae" && req.SubAgentType != "claude" {
		writeError(w, http.StatusBadRequest, "sub_agent_type must be one of: qoder, trae, claude")
		return
	}

	// parent_task_id: optional, in production this comes from the triggering task context
	parentTaskID := r.URL.Query().Get("parent_task_id")

	if req.SpawnConfig == nil {
		req.SpawnConfig = make(map[string]any)
	}

	spawn, err := h.SubAgentOrchestrator.SpawnSubAgent(r.Context(), subWorkspaceID, parentTaskID, req.SubAgentType, req.SpawnConfig)
	if err != nil {
		slog.Error("failed to spawn sub-agent", "error", err, "sub_workspace_id", subWorkspaceID)
		writeError(w, http.StatusInternalServerError, "failed to spawn sub-agent")
		return
	}

	writeJSON(w, http.StatusCreated, spawn)
}

func (h *Handler) ListSubAgentSpawns(w http.ResponseWriter, r *http.Request) {
	_, ok := requireUserID(w, r)
	if !ok {
		return
	}

	subWorkspaceID := chi.URLParam(r, "subWorkspaceId")
	if subWorkspaceID == "" {
		writeError(w, http.StatusBadRequest, "sub_workspace_id is required")
		return
	}
	if _, ok := parseUUIDOrBadRequest(w, subWorkspaceID, "sub_workspace_id"); !ok {
		return
	}

	spawns, err := h.SubAgentOrchestrator.ListSpawns(r.Context(), subWorkspaceID)
	if err != nil {
		slog.Error("failed to list sub-agent spawns", "error", err, "sub_workspace_id", subWorkspaceID)
		writeError(w, http.StatusInternalServerError, "failed to list spawns")
		return
	}

	writeJSON(w, http.StatusOK, spawns)
}

func (h *Handler) GetSubAgentStatus(w http.ResponseWriter, r *http.Request) {
	_, ok := requireUserID(w, r)
	if !ok {
		return
	}

	spawnID := chi.URLParam(r, "id")
	if _, ok := parseUUIDOrBadRequest(w, spawnID, "spawn_id"); !ok {
		return
	}

	spawn, err := h.SubAgentOrchestrator.GetSpawnStatus(r.Context(), spawnID)
	if err != nil {
		writeError(w, http.StatusNotFound, "sub-agent spawn not found")
		return
	}

	writeJSON(w, http.StatusOK, spawn)
}
