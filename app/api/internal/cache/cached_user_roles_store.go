package cache

import (
	"fmt"
	"time"

	"github.com/clockwise/clockwise/backend/internal/database"
	"github.com/google/uuid"
)

const (
	// User permissions/roles, accessed frequently for auth checks
	UserRolesCacheTTL = 5 * time.Minute
)

type CachedUserRolesStore struct {
	store database.UserRolesStore
	cache *CacheService
}

func NewCachedUserRolesStore(store database.UserRolesStore, cache *CacheService) database.UserRolesStore {
	return &CachedUserRolesStore{
		store: store,
		cache: cache,
	}
}

// GetUserRoles retrieves the roles for a user
// Cache key: user:{uuid}:org:{uuid}:roles
func (curs *CachedUserRolesStore) GetUserRoles(userID uuid.UUID, orgID uuid.UUID) ([]string, error) {
	key := fmt.Sprintf("user:%s:org:%s:roles", userID, orgID)

	var roles []string
	if err := curs.cache.Get(key, &roles); err == nil {
		return roles, nil
	}

	roles, err := curs.store.GetUserRoles(userID, orgID)
	if err != nil {
		return nil, err
	}

	_ = curs.cache.Set(key, roles, UserRolesCacheTTL)
	return roles, nil
}

// SetUserRoles invalidates the user's roles cache
func (curs *CachedUserRolesStore) SetUserRoles(userID uuid.UUID, orgID uuid.UUID, roles []string) error {
	err := curs.store.SetUserRoles(userID, orgID, roles)
	if err != nil {
		return err
	}

	_ = curs.cache.Delete(fmt.Sprintf("user:%s:org:%s:roles", userID, orgID))
	return nil
}

// AddUserRole invalidates the user's roles cache
func (curs *CachedUserRolesStore) AddUserRole(userID uuid.UUID, orgID uuid.UUID, role string) error {
	err := curs.store.AddUserRole(userID, orgID, role)
	if err != nil {
		return err
	}

	_ = curs.cache.Delete(fmt.Sprintf("user:%s:org:%s:roles", userID, orgID))
	return nil
}

// RemoveUserRole invalidates the user's roles cache
func (curs *CachedUserRolesStore) RemoveUserRole(userID uuid.UUID, orgID uuid.UUID, role string) error {
	err := curs.store.RemoveUserRole(userID, orgID, role)
	if err != nil {
		return err
	}

	_ = curs.cache.Delete(fmt.Sprintf("user:%s:org:%s:roles", userID, orgID))
	return nil
}

// DeleteAllUserRoles invalidates the user's roles cache
func (curs *CachedUserRolesStore) DeleteAllUserRoles(userID uuid.UUID, orgID uuid.UUID) error {
	err := curs.store.DeleteAllUserRoles(userID, orgID)
	if err != nil {
		return err
	}

	_ = curs.cache.Delete(fmt.Sprintf("user:%s:org:%s:roles", userID, orgID))
	return nil
}
