package service

import (
	"context"
	"testing"
)

func TestSubAgentOrchestrator_CreateWorkspace(t *testing.T) {
	// Integration test — requires running PostgreSQL
	t.Skip("requires database")

	_ = context.Background()
	// orchestrator := NewSubAgentOrchestrator(db, hub, bus)
	// ws, err := orchestrator.CreateWorkspace(ctx, wsID, agentID, "test-ws", "/tmp/test", "process")
	// assert.NoError(t, err)
	// assert.Equal(t, "test-ws", ws.Name)
}

func TestSubAgentOrchestrator_SpawnSubAgent(t *testing.T) {
	t.Skip("requires database")
}

func TestSubAgentOrchestrator_UpdateSpawnStatus(t *testing.T) {
	t.Skip("requires database")
}

func TestLearnedRuleService_LearnFromFailure(t *testing.T) {
	t.Skip("requires database")
}

func TestLearnedRuleService_MatchRule(t *testing.T) {
	t.Skip("requires database")
}
