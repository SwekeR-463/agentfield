package services

import (
	"sync"
	"testing"
	"time"

	"github.com/Agent-Field/agentfield/control-plane/internal/storage"

	"github.com/stretchr/testify/require"
)

func setupPresenceManagerTest(t *testing.T) (*PresenceManager, storage.StorageProvider) {
	t.Helper()

	provider, ctx := setupTestStorage(t)

	// Create a minimal status manager for testing
	statusConfig := StatusManagerConfig{
		ReconcileInterval: 30 * time.Second,
	}
	statusManager := NewStatusManager(provider, statusConfig, nil, nil)

	config := PresenceManagerConfig{
		HeartbeatTTL:  5 * time.Second,
		SweepInterval: 1 * time.Second,
		HardEvictTTL:  10 * time.Second,
	}

	presenceManager := NewPresenceManager(statusManager, config)

	t.Cleanup(func() {
		presenceManager.Stop()
		_ = provider.Close(ctx)
	})

	return presenceManager, provider
}

func TestPresenceManager_NewPresenceManager(t *testing.T) {
	provider, ctx := setupTestStorage(t)
	statusConfig := StatusManagerConfig{
		ReconcileInterval: 30 * time.Second,
	}
	statusManager := NewStatusManager(provider, statusConfig, nil, nil)

	config := PresenceManagerConfig{
		HeartbeatTTL:  10 * time.Second,
		SweepInterval: 2 * time.Second,
		HardEvictTTL:  30 * time.Second,
	}

	pm := NewPresenceManager(statusManager, config)
	require.NotNil(t, pm)
	require.Equal(t, 10*time.Second, pm.config.HeartbeatTTL)
	require.Equal(t, 2*time.Second, pm.config.SweepInterval)
	require.Equal(t, 30*time.Second, pm.config.HardEvictTTL)

	_ = ctx
}

func TestPresenceManager_NewPresenceManager_Defaults(t *testing.T) {
	provider, ctx := setupTestStorage(t)
	statusConfig := StatusManagerConfig{
		ReconcileInterval: 30 * time.Second,
	}
	statusManager := NewStatusManager(provider, statusConfig, nil, nil)

	// Test with zero values (should use defaults)
	config := PresenceManagerConfig{}
	pm := NewPresenceManager(statusManager, config)
	require.NotNil(t, pm)
	require.Equal(t, 15*time.Second, pm.config.HeartbeatTTL)
	require.Greater(t, pm.config.SweepInterval, time.Duration(0))
	require.Equal(t, 5*time.Minute, pm.config.HardEvictTTL)

	_ = ctx
}

func TestPresenceManager_Touch(t *testing.T) {
	pm, _ := setupPresenceManagerTest(t)

	nodeID := "node-touch-1"
	now := time.Now()

	pm.Touch(nodeID, now)

	// Verify lease exists
	require.True(t, pm.HasLease(nodeID))
}

func TestPresenceManager_Touch_UpdateExisting(t *testing.T) {
	pm, _ := setupPresenceManagerTest(t)

	nodeID := "node-touch-update"
	now1 := time.Now()
	pm.Touch(nodeID, now1)

	time.Sleep(10 * time.Millisecond)
	now2 := time.Now()
	pm.Touch(nodeID, now2)

	// Verify lease still exists
	require.True(t, pm.HasLease(nodeID))
}

func TestPresenceManager_Forget(t *testing.T) {
	pm, _ := setupPresenceManagerTest(t)

	nodeID := "node-forget-1"
	pm.Touch(nodeID, time.Now())
	require.True(t, pm.HasLease(nodeID))

	pm.Forget(nodeID)
	require.False(t, pm.HasLease(nodeID))
}

func TestPresenceManager_HasLease(t *testing.T) {
	pm, _ := setupPresenceManagerTest(t)

	nodeID := "node-lease-1"
	require.False(t, pm.HasLease(nodeID))

	pm.Touch(nodeID, time.Now())
	require.True(t, pm.HasLease(nodeID))

	pm.Forget(nodeID)
	require.False(t, pm.HasLease(nodeID))
}

func TestPresenceManager_SetExpireCallback(t *testing.T) {
	pm, _ := setupPresenceManagerTest(t)

	var callbackInvoked bool
	var callbackNodeID string

	callback := func(nodeID string) {
		callbackInvoked = true
		callbackNodeID = nodeID
	}

	pm.SetExpireCallback(callback)
	require.NotNil(t, pm.expireCallback)

	// Start the presence manager to trigger expiration
	pm.Start()

	// Touch a node
	nodeID := "node-callback-1"
	pm.Touch(nodeID, time.Now().Add(-10*time.Second)) // Touch in the past

	// Wait for expiration
	time.Sleep(2 * time.Second)

	pm.Stop()

	// Callback should have been invoked
	require.True(t, callbackInvoked)
	require.Equal(t, nodeID, callbackNodeID)
}

func TestPresenceManager_ExpirationDetection(t *testing.T) {
	pm, _ := setupPresenceManagerTest(t)

	// Set shorter TTL for testing
	pm.config.HeartbeatTTL = 500 * time.Millisecond
	pm.config.SweepInterval = 100 * time.Millisecond

	pm.Start()

	nodeID := "node-expire-1"
	pm.Touch(nodeID, time.Now())
	require.True(t, pm.HasLease(nodeID))

	// Wait for expiration
	time.Sleep(700 * time.Millisecond)

	// Node should be marked offline
	require.False(t, pm.HasLease(nodeID))

	pm.Stop()
}

func TestPresenceManager_ConcurrentAccess(t *testing.T) {
	pm, _ := setupPresenceManagerTest(t)

	var wg sync.WaitGroup
	numGoroutines := 10
	numNodes := 5

	// Concurrent touches
	for i := 0; i < numGoroutines; i++ {
		wg.Add(1)
		go func(id int) {
			defer wg.Done()
			for j := 0; j < numNodes; j++ {
				nodeID := "node-concurrent-" + string(rune('0'+j))
				pm.Touch(nodeID, time.Now())
				_ = pm.HasLease(nodeID)
			}
		}(i)
	}

	wg.Wait()

	// Verify all nodes have leases
	for j := 0; j < numNodes; j++ {
		nodeID := "node-concurrent-" + string(rune('0'+j))
		require.True(t, pm.HasLease(nodeID))
	}
}

func TestPresenceManager_StartStop(t *testing.T) {
	pm, _ := setupPresenceManagerTest(t)

	pm.Start()

	// Verify it's running
	nodeID := "node-start-stop"
	pm.Touch(nodeID, time.Now())
	require.True(t, pm.HasLease(nodeID))

	pm.Stop()

	// Stop should be idempotent
	pm.Stop()
}

func TestPresenceManager_HardEviction(t *testing.T) {
	pm, _ := setupPresenceManagerTest(t)

	// Set shorter hard evict TTL
	pm.config.HardEvictTTL = 1 * time.Second
	pm.config.HeartbeatTTL = 500 * time.Millisecond
	pm.config.SweepInterval = 100 * time.Millisecond

	pm.Start()

	nodeID := "node-hard-evict"
	pm.Touch(nodeID, time.Now().Add(-2*time.Second)) // Touch in the past beyond hard evict TTL

	// Wait for hard eviction
	time.Sleep(1 * time.Second)

	// Node should be removed
	require.False(t, pm.HasLease(nodeID))

	pm.Stop()
}

func TestPresenceManager_MultipleNodes(t *testing.T) {
	pm, _ := setupPresenceManagerTest(t)

	nodeIDs := []string{"node-1", "node-2", "node-3"}

	for _, nodeID := range nodeIDs {
		pm.Touch(nodeID, time.Now())
		require.True(t, pm.HasLease(nodeID))
	}

	// Forget one node
	pm.Forget("node-2")
	require.False(t, pm.HasLease("node-2"))
	require.True(t, pm.HasLease("node-1"))
	require.True(t, pm.HasLease("node-3"))
}
