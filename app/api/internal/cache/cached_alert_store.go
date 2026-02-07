package cache

import (
	"fmt"
	"time"

	"github.com/clockwise/clockwise/backend/internal/database"
	"github.com/google/uuid"
)

const (
	// Insights are computed aggregations, cache for short duration
	AlertInsightsCacheTTL = 2 * time.Minute
)

type CachedAlertStore struct {
	store database.AlertStore
	cache *CacheService
}

func NewCachedAlertStore(store database.AlertStore, cache *CacheService) database.AlertStore {
	return &CachedAlertStore{
		store: store,
		cache: cache,
	}
}

// StoreAlert writes to DB and invalidates insights cache
func (cas *CachedAlertStore) StoreAlert(org_id uuid.UUID, alert *database.Alert) error {
	// Update database first
	err := cas.store.StoreAlert(org_id, alert)
	if err != nil {
		return err
	}

	// Invalidate computed insights for this organization
	// We do not cache the list of alerts, so no other keys to delete
	key := fmt.Sprintf("org:%s:alert_insights", org_id)
	_ = cas.cache.Delete(key)

	return nil
}

// GetAllAlerts is a list operation - DON'T CACHE
func (cas *CachedAlertStore) GetAllAlerts(org_id uuid.UUID) ([]database.Alert, error) {
	return cas.store.GetAllAlerts(org_id)
}

// GetAllAlertsForLastWeek is a filtered list operation - DON'T CACHE
func (cas *CachedAlertStore) GetAllAlertsForLastWeek(org_id uuid.UUID) ([]database.Alert, error) {
	return cas.store.GetAllAlertsForLastWeek(org_id)
}

// GetAlertInsights is computed/aggregated data - CACHE IT
// Cache key: org:{uuid}:alert_insights
func (cas *CachedAlertStore) GetAlertInsights(org_id uuid.UUID) ([]database.Insight, error) {
	key := fmt.Sprintf("org:%s:alert_insights", org_id)

	// Try cache first
	var insights []database.Insight
	err := cas.cache.Get(key, &insights)
	if err == nil {
		return insights, nil
	}

	// Cache miss - query database
	insights, err = cas.store.GetAlertInsights(org_id)
	if err != nil {
		return nil, err
	}

	// Cache the results
	_ = cas.cache.Set(key, insights, AlertInsightsCacheTTL)

	return insights, nil
}
