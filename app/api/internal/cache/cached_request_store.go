package cache

import (
	"fmt"
	"time"

	"github.com/clockwise/clockwise/backend/internal/database"
	"github.com/google/uuid"
)

const (
	// Request status changes occasionally
	RequestCacheTTL = 5 * time.Minute
)

type CachedRequestStore struct {
	store database.RequestStore
	cache *CacheService
}

func NewCachedRequestStore(store database.RequestStore, cache *CacheService) database.RequestStore {
	return &CachedRequestStore{
		store: store,
		cache: cache,
	}
}

// CreateRequest is a write operation - no cache interaction needed
// (Lists are not cached, so no invalidation required)
func (crs *CachedRequestStore) CreateRequest(req *database.Request) error {
	return crs.store.CreateRequest(req)
}

// GetRequestByID retrieves a single request
// Cache key: request:{uuid}
func (crs *CachedRequestStore) GetRequestByID(id uuid.UUID) (*database.Request, error) {
	key := fmt.Sprintf("request:%s", id)

	var req database.Request
	if err := crs.cache.Get(key, &req); err == nil {
		return &req, nil
	}

	reqPtr, err := crs.store.GetRequestByID(id)
	if err != nil {
		return nil, err
	}

	_ = crs.cache.Set(key, reqPtr, RequestCacheTTL)
	return reqPtr, nil
}

// GetRequestsByEmployee is a list operation - DON'T CACHE
func (crs *CachedRequestStore) GetRequestsByEmployee(employeeID uuid.UUID) ([]*database.Request, error) {
	return crs.store.GetRequestsByEmployee(employeeID)
}

// GetRequestsByOrganization is a list operation - DON'T CACHE
func (crs *CachedRequestStore) GetRequestsByOrganization(orgID uuid.UUID) ([]*database.RequestWithEmployee, error) {
	return crs.store.GetRequestsByOrganization(orgID)
}

// UpdateRequestStatus invalidates the specific request cache
func (crs *CachedRequestStore) UpdateRequestStatus(id uuid.UUID, status string) error {
	err := crs.store.UpdateRequestStatus(id, status)
	if err != nil {
		return err
	}

	_ = crs.cache.Delete(fmt.Sprintf("request:%s", id))
	return nil
}
