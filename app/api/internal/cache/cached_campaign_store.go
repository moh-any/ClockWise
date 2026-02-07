package cache

import (
	"fmt"
	"time"

	"github.com/clockwise/clockwise/backend/internal/database"
	"github.com/google/uuid"
)

const (
	// Campaign insights (aggregations) cache TTL
	CampaignInsightsCacheTTL = 5 * time.Minute
)

type CachedCampaignStore struct {
	store database.CampaignStore
	cache *CacheService
}

func NewCachedCampaignStore(store database.CampaignStore, cache *CacheService) database.CampaignStore {
	return &CachedCampaignStore{
		store: store,
		cache: cache,
	}
}

// StoreCampaign invalidates insights cache
func (ccs *CachedCampaignStore) StoreCampaign(org_id uuid.UUID, campaign database.Campaign) error {
	err := ccs.store.StoreCampaign(org_id, campaign)
	if err != nil {
		return err
	}

	// Invalidate computed insights
	_ = ccs.cache.Delete(fmt.Sprintf("org:%s:campaign_insights", org_id))

	return nil
}

// StoreCampaignItems invalidates insights cache (affects "Most Featured Item")
func (ccs *CachedCampaignStore) StoreCampaignItems(org_id, campaign_id uuid.UUID, Items []database.Item) error {
	err := ccs.store.StoreCampaignItems(org_id, campaign_id, Items)
	if err != nil {
		return err
	}

	// Invalidate computed insights
	_ = ccs.cache.Delete(fmt.Sprintf("org:%s:campaign_insights", org_id))

	return nil
}

// GetAllCampaigns is a list operation - DON'T CACHE
func (ccs *CachedCampaignStore) GetAllCampaigns(org_id uuid.UUID) ([]database.Campaign, error) {
	return ccs.store.GetAllCampaigns(org_id)
}

// GetAllCampaignsFromLastWeek is a filtered list operation - DON'T CACHE
// Note: variable name matches interface definition (org_ud)
func (ccs *CachedCampaignStore) GetAllCampaignsFromLastWeek(org_ud uuid.UUID) ([]database.Campaign, error) {
	return ccs.store.GetAllCampaignsFromLastWeek(org_ud)
}

// GetCampaignInsights is computed/aggregated data - CACHE IT
// Cache key: org:{uuid}:campaign_insights
func (ccs *CachedCampaignStore) GetCampaignInsights(org_id uuid.UUID) ([]database.Insight, error) {
	key := fmt.Sprintf("org:%s:campaign_insights", org_id)

	// Try cache first
	var insights []database.Insight
	err := ccs.cache.Get(key, &insights)
	if err == nil {
		return insights, nil
	}

	// Cache miss - query database
	insights, err = ccs.store.GetCampaignInsights(org_id)
	if err != nil {
		return nil, err
	}

	// Cache the results
	_ = ccs.cache.Set(key, insights, CampaignInsightsCacheTTL)

	return insights, nil
}
