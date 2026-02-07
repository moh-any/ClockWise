package cache

import (
	"fmt"
	"time"

	"github.com/clockwise/clockwise/backend/internal/database"
	"github.com/google/uuid"
)

const (
	// Roles are static configuration data that rarely changes
	RoleCacheTTL = 1 * time.Hour
)

type CachedRolesStore struct {
	store database.RolesStore
	cache *CacheService
}

func NewCachedRolesStore(store database.RolesStore, cache *CacheService) database.RolesStore {
	return &CachedRolesStore{
		store: store,
		cache: cache,
	}
}

// CreateRole invalidates the role list for the organization
func (crs *CachedRolesStore) CreateRole(role *database.OrganizationRole) error {
	err := crs.store.CreateRole(role)
	if err != nil {
		return err
	}

	// Invalidate the list of roles
	// Also invalidate the specific key to prevent race conditions
	_ = crs.cache.Delete(
		fmt.Sprintf("org:%s:roles", role.OrganizationID),
		fmt.Sprintf("org:%s:role:%s", role.OrganizationID, role.Role),
	)

	return nil
}

// GetRolesByOrganizationID retrieves the full list of roles
// Cache key: org:{uuid}:roles
func (crs *CachedRolesStore) GetRolesByOrganizationID(orgID uuid.UUID) ([]database.OrganizationRole, error) {
	key := fmt.Sprintf("org:%s:roles", orgID)

	var roles []database.OrganizationRole
	if err := crs.cache.Get(key, roles); err == nil {
		return roles, nil
	}

	roles, err := crs.store.GetRolesByOrganizationID(orgID)
	if err != nil {
		return nil, err
	}

	_ = crs.cache.Set(key, roles, RoleCacheTTL)
	return roles, nil
}

// GetRoleByName retrieves a single role
// Cache key: org:{uuid}:role:{role_name}
func (crs *CachedRolesStore) GetRoleByName(orgID uuid.UUID, roleName string) (*database.OrganizationRole, error) {
	key := fmt.Sprintf("org:%s:role:%s", orgID, roleName)

	var role database.OrganizationRole
	if err := crs.cache.Get(key, &role); err == nil {
		return &role, nil
	}

	rolePtr, err := crs.store.GetRoleByName(orgID, roleName)
	if err != nil {
		return nil, err
	}

	// Handle nil result
	if rolePtr == nil {
		return nil, nil
	}

	_ = crs.cache.Set(key, rolePtr, RoleCacheTTL)
	return rolePtr, nil
}

// UpdateRole invalidates the specific role and the list
func (crs *CachedRolesStore) UpdateRole(role *database.OrganizationRole) error {
	err := crs.store.UpdateRole(role)
	if err != nil {
		return err
	}

	_ = crs.cache.Delete(
		fmt.Sprintf("org:%s:roles", role.OrganizationID),
		fmt.Sprintf("org:%s:role:%s", role.OrganizationID, role.Role),
	)

	return nil
}

// DeleteRole invalidates the specific role and the list
func (crs *CachedRolesStore) DeleteRole(orgID uuid.UUID, roleName string) error {
	err := crs.store.DeleteRole(orgID, roleName)
	if err != nil {
		return err
	}

	_ = crs.cache.Delete(
		fmt.Sprintf("org:%s:roles", orgID),
		fmt.Sprintf("org:%s:role:%s", orgID, roleName),
	)

	return nil
}
