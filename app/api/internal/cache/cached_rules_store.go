package cache

import (
	"fmt"
	"time"

	"github.com/clockwise/clockwise/backend/internal/database"
	"github.com/google/uuid"
)

const (
	// Rules are configuration data that changes rarely
	RulesCacheTTL = 60 * time.Minute
)

type CachedRulesStore struct {
	store database.RulesStore
	cache *CacheService
}

func NewCachedRulesStore(store database.RulesStore, cache *CacheService) database.RulesStore {
	return &CachedRulesStore{
		store: store,
		cache: cache,
	}
}

// CreateRules writes to DB and invalidates cache
func (crs *CachedRulesStore) CreateRules(rules *database.OrganizationRules) error {
	err := crs.store.CreateRules(rules)
	if err != nil {
		return err
	}

	_ = crs.cache.Delete(fmt.Sprintf("org:%s:rules", rules.OrganizationID))
	return nil
}

// GetRulesByOrganizationID retrieves rules with caching
// Cache key: org:{uuid}:rules
func (crs *CachedRulesStore) GetRulesByOrganizationID(orgID uuid.UUID) (*database.OrganizationRules, error) {
	key := fmt.Sprintf("org:%s:rules", orgID)

	var rules database.OrganizationRules
	if err := crs.cache.Get(key, &rules); err == nil {
		return &rules, nil
	}

	rulesPtr, err := crs.store.GetRulesByOrganizationID(orgID)
	if err != nil {
		return nil, err
	}

	// Handle case where no rules exist
	if rulesPtr == nil {
		return nil, nil
	}

	_ = crs.cache.Set(key, rulesPtr, RulesCacheTTL)
	return rulesPtr, nil
}

// UpdateRules updates DB and invalidates cache
func (crs *CachedRulesStore) UpdateRules(rules *database.OrganizationRules) error {
	err := crs.store.UpdateRules(rules)
	if err != nil {
		return err
	}

	_ = crs.cache.Delete(fmt.Sprintf("org:%s:rules", rules.OrganizationID))
	return nil
}

// UpsertRules updates DB and invalidates cache
func (crs *CachedRulesStore) UpsertRules(rules *database.OrganizationRules) error {
	err := crs.store.UpsertRules(rules)
	if err != nil {
		return err
	}

	_ = crs.cache.Delete(fmt.Sprintf("org:%s:rules", rules.OrganizationID))
	return nil
}
