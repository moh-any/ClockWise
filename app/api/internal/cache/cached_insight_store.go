package cache

import (
	"fmt"
	"time"

	"github.com/clockwise/clockwise/backend/internal/database"
	"github.com/google/uuid"
)

const (
	// Heavy aggregations with real-time components (current shift, tables)
	// Short TTL to keep "current" status reasonably accurate
	InsightCacheTTL = 2 * time.Minute
)

type CachedInsightStore struct {
	store database.InsightStore
	cache *CacheService
}

func NewCachedInsightStore(store database.InsightStore, cache *CacheService) database.InsightStore {
	return &CachedInsightStore{
		store: store,
		cache: cache,
	}
}

// GetInsightsForAdmin retrieves aggregated stats for the organization
// Cache key: org:{uuid}:insights:admin
func (cis *CachedInsightStore) GetInsightsForAdmin(org_id uuid.UUID) ([]database.Insight, error) {
	key := fmt.Sprintf("org:%s:insights:admin", org_id)

	var insights []database.Insight
	if err := cis.cache.Get(key, &insights); err == nil {
		return insights, nil
	}

	insights, err := cis.store.GetInsightsForAdmin(org_id)
	if err != nil {
		return nil, err
	}

	_ = cis.cache.Set(key, insights, InsightCacheTTL)
	return insights, nil
}

// GetInsightsForManager retrieves personalized stats for a manager
// Cache key: org:{uuid}:insights:manager:{uuid}
func (cis *CachedInsightStore) GetInsightsForManager(org_id, manager_id uuid.UUID) ([]database.Insight, error) {
	// Personalized cache key including manager_id
	key := fmt.Sprintf("org:%s:insights:manager:%s", org_id, manager_id)

	var insights []database.Insight
	if err := cis.cache.Get(key, &insights); err == nil {
		return insights, nil
	}

	insights, err := cis.store.GetInsightsForManager(org_id, manager_id)
	if err != nil {
		return nil, err
	}

	_ = cis.cache.Set(key, insights, InsightCacheTTL)
	return insights, nil
}

// GetInsightsForEmployee retrieves personalized stats for an employee
// Cache key: org:{uuid}:insights:employee:{uuid}
func (cis *CachedInsightStore) GetInsightsForEmployee(org_id, employee_id uuid.UUID) ([]database.Insight, error) {
	// Personalized cache key including employee_id
	key := fmt.Sprintf("org:%s:insights:employee:%s", org_id, employee_id)

	var insights []database.Insight
	if err := cis.cache.Get(key, &insights); err == nil {
		return insights, nil
	}

	insights, err := cis.store.GetInsightsForEmployee(org_id, employee_id)
	if err != nil {
		return nil, err
	}

	_ = cis.cache.Set(key, insights, InsightCacheTTL)
	return insights, nil
}
