package cache

import (
	"fmt"
	"time"

	"github.com/clockwise/clockwise/backend/internal/database"
	"github.com/google/uuid"
)

const (
	// Computed aggregation for dashboards
	DemandHeatmapCacheTTL = 5 * time.Minute
)

type CachedDemandStore struct {
	store database.DemandStore
	cache *CacheService
}

func NewCachedDemandStore(store database.DemandStore, cache *CacheService) database.DemandStore {
	return &CachedDemandStore{
		store: store,
		cache: cache,
	}
}

// StoreDemandHeatMap writes to DB and invalidates cache
func (cds *CachedDemandStore) StoreDemandHeatMap(org_id uuid.UUID, demand database.DemandPredictResponse) error {
	// Update database first
	err := cds.store.StoreDemandHeatMap(org_id, demand)
	if err != nil {
		return err
	}

	// Invalidate the heatmap cache for this organization
	key := fmt.Sprintf("org:%s:demand_heatmap", org_id)
	_ = cds.cache.Delete(key)

	return nil
}

// GetLatestDemandHeatMap retrieves computed heatmap with caching
// Cache key: org:{uuid}:demand_heatmap
func (cds *CachedDemandStore) GetLatestDemandHeatMap(org_id uuid.UUID) (*database.DemandPredictResponse, error) {
	key := fmt.Sprintf("org:%s:demand_heatmap", org_id)

	// Try cache first
	var response database.DemandPredictResponse
	err := cds.cache.Get(key, &response)
	if err == nil {
		return &response, nil
	}

	// Cache miss - query database
	responsePtr, err := cds.store.GetLatestDemandHeatMap(org_id)
	if err != nil {
		return nil, err
	}

	// Handle case where no data exists (nil response)
	if responsePtr == nil {
		return nil, nil
	}

	// Cache the result
	_ = cds.cache.Set(key, responsePtr, DemandHeatmapCacheTTL)

	return responsePtr, nil
}
