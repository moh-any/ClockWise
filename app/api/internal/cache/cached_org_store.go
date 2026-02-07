package cache

import (
	"fmt"
	"time"

	"github.com/clockwise/clockwise/backend/internal/database"
	"github.com/google/uuid"
)

const (
	// Organization details rarely change
	OrgCacheTTL = 60 * time.Minute
	// Profile includes employee count, so shorter TTL to reflect user additions
	OrgProfileCacheTTL = 15 * time.Minute
	// Lists of specific role emails (config-like data)
	OrgEmailsCacheTTL = 30 * time.Minute
)

type CachedOrgStore struct {
	store database.OrgStore
	cache *CacheService
}

func NewCachedOrgStore(store database.OrgStore, cache *CacheService) database.OrgStore {
	return &CachedOrgStore{
		store: store,
		cache: cache,
	}
}

// CreateOrgWithAdmin creates new data - no cache interaction needed
func (cos *CachedOrgStore) CreateOrgWithAdmin(org *database.Organization, adminUser *database.User, password string) error {
	return cos.store.CreateOrgWithAdmin(org, adminUser, password)
}

// GetOrganizationByID retrieves static org details
// Cache key: org:{uuid}
func (cos *CachedOrgStore) GetOrganizationByID(id uuid.UUID) (*database.Organization, error) {
	key := fmt.Sprintf("org:%s", id)

	var org database.Organization
	if err := cos.cache.Get(key, &org); err == nil {
		return &org, nil
	}

	orgPtr, err := cos.store.GetOrganizationByID(id)
	if err != nil {
		return nil, err
	}

	_ = cos.cache.Set(key, orgPtr, OrgCacheTTL)
	return orgPtr, nil
}

// GetOrganizationProfile retrieves org details + employee count
// Cache key: org:{uuid}:profile
func (cos *CachedOrgStore) GetOrganizationProfile(id uuid.UUID) (*database.OrganizationProfile, error) {
	key := fmt.Sprintf("org:%s:profile", id)

	var profile database.OrganizationProfile
	if err := cos.cache.Get(key, &profile); err == nil {
		return &profile, nil
	}

	profilePtr, err := cos.store.GetOrganizationProfile(id)
	if err != nil {
		return nil, err
	}

	_ = cos.cache.Set(key, profilePtr, OrgProfileCacheTTL)
	return profilePtr, nil
}

// GetManagerEmailsByOrgID retrieves list of manager emails
// Cache key: org:{uuid}:emails:managers
func (cos *CachedOrgStore) GetManagerEmailsByOrgID(orgID uuid.UUID) ([]string, error) {
	key := fmt.Sprintf("org:%s:emails:managers", orgID)

	var emails []string
	if err := cos.cache.Get(key, &emails); err == nil {
		return emails, nil
	}

	emails, err := cos.store.GetManagerEmailsByOrgID(orgID)
	if err != nil {
		return nil, err
	}

	_ = cos.cache.Set(key, emails, OrgEmailsCacheTTL)
	return emails, nil
}

// GetAdminEmailsByOrgID retrieves list of admin emails
// Cache key: org:{uuid}:emails:admins
func (cos *CachedOrgStore) GetAdminEmailsByOrgID(orgID uuid.UUID) ([]string, error) {
	key := fmt.Sprintf("org:%s:emails:admins", orgID)

	var emails []string
	if err := cos.cache.Get(key, &emails); err == nil {
		return emails, nil
	}

	emails, err := cos.store.GetAdminEmailsByOrgID(orgID)
	if err != nil {
		return nil, err
	}

	_ = cos.cache.Set(key, emails, OrgEmailsCacheTTL)
	return emails, nil
}
