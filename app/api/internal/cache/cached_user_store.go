package cache

import (
	"fmt"
	"time"

	"github.com/clockwise/clockwise/backend/internal/database"
	"github.com/google/uuid"
)

const (
	UserCacheTTL        = 5 * time.Minute
	UserProfileCacheTTL = 3 * time.Minute
)

// CachedUserStore wraps a database.UserStore with Redis caching
// Implements the database.UserStore interface
type CachedUserStore struct {
	store database.UserStore
	cache *CacheService
}

// NewCachedUserStore creates a new cached user store
func NewCachedUserStore(store database.UserStore, cache *CacheService) database.UserStore {
	return &CachedUserStore{
		store: store,
		cache: cache,
	}
}

type cacheableUser struct {
	ID                    uuid.UUID `json:"id"`
	FullName              string    `json:"full_name"`
	Email                 string    `json:"email"`
	PasswordHash          []byte    `json:"password_hash"` // Cached for authentication
	UserRole              string    `json:"user_role"`
	SalaryPerHour         *float64  `json:"salary_per_hour,omitempty"`
	OrganizationID        uuid.UUID `json:"organization_id"`
	MaxHoursPerWeek       *int      `json:"max_hours_per_week,omitempty"`
	PreferredHoursPerWeek *int      `json:"preferred_hours_per_week,omitempty"`
	MaxConsecSlots        *int      `json:"max_consec_slots,omitempty"`
	OnCall                *bool     `json:"on_call"`
	CreatedAt             time.Time `json:"created_at"`
	UpdatedAt             time.Time `json:"updated_at"`
}

// convertToUser converts cacheableUser back to database.User
func (cu *cacheableUser) toUser() *database.User {
	user := &database.User{
		ID:                    cu.ID,
		FullName:              cu.FullName,
		Email:                 cu.Email,
		UserRole:              cu.UserRole,
		SalaryPerHour:         cu.SalaryPerHour,
		OrganizationID:        cu.OrganizationID,
		MaxHoursPerWeek:       cu.MaxHoursPerWeek,
		PreferredHoursPerWeek: cu.PreferredHoursPerWeek,
		MaxConsecSlots:        cu.MaxConsecSlots,
		OnCall:                cu.OnCall,
		CreatedAt:             cu.CreatedAt,
		UpdatedAt:             cu.UpdatedAt,
	}

	// Reconstruct Password struct with cached hash using helper function
	if len(cu.PasswordHash) > 0 {
		user.PasswordHash = database.NewPasswordFromHash(cu.PasswordHash)
	}

	return user
}

// fromUser converts database.User to cacheableUser
func fromUser(user *database.User) *cacheableUser {
	return &cacheableUser{
		ID:                    user.ID,
		FullName:              user.FullName,
		Email:                 user.Email,
		PasswordHash:          user.PasswordHash.GetHash(), // Cache hash for authentication
		UserRole:              user.UserRole,
		SalaryPerHour:         user.SalaryPerHour,
		OrganizationID:        user.OrganizationID,
		MaxHoursPerWeek:       user.MaxHoursPerWeek,
		PreferredHoursPerWeek: user.PreferredHoursPerWeek,
		MaxConsecSlots:        user.MaxConsecSlots,
		OnCall:                user.OnCall,
		CreatedAt:             user.CreatedAt,
		UpdatedAt:             user.UpdatedAt,
	}
}


func (cus *CachedUserStore) GetUserByID(id uuid.UUID) (*database.User, error) {
	key := fmt.Sprintf("user:%s", id)

	// Try cache first
	var cached cacheableUser
	err := cus.cache.Get(key, &cached)
	if err == nil {
		// Cache hit
		return cached.toUser(), nil
	}

	// Cache miss or error - query database
	user, err := cus.store.GetUserByID(id)
	if err != nil {
		return nil, err
	}

	// Cache the result (don't cache password hash for security)
	cacheable := fromUser(user)
	_ = cus.cache.Set(key, cacheable, UserCacheTTL)

	return user, nil
}

// GetUserByEmail retrieves user by email with caching
// Cache key: user:email:{email}
func (cus *CachedUserStore) GetUserByEmail(email string) (*database.User, error) {
	key := fmt.Sprintf("user:email:%s", email)

	// Try cache first
	var cached cacheableUser
	err := cus.cache.Get(key, &cached)
	if err == nil {
		// Cache hit
		return cached.toUser(), nil
	}

	// Cache miss - query database
	user, err := cus.store.GetUserByEmail(email)
	if err != nil {
		return nil, err
	}

	// Cache by both email and ID
	cacheable := fromUser(user)
	_ = cus.cache.Set(key, cacheable, UserCacheTTL)
	_ = cus.cache.Set(fmt.Sprintf("user:%s", user.ID), cacheable, UserCacheTTL)

	return user, nil
}

// GetProfile retrieves user profile with caching
// Cache key: user:{uuid}:profile
// Cached separately since it's a different data structure with computed fields
func (cus *CachedUserStore) GetProfile(id uuid.UUID) (*database.UserProfile, error) {
	key := fmt.Sprintf("user:%s:profile", id)

	// Try cache first
	var profile database.UserProfile
	err := cus.cache.Get(key, &profile)
	if err == nil {
		// Cache hit
		return &profile, nil
	}

	// Cache miss - query database
	profilePtr, err := cus.store.GetProfile(id)
	if err != nil {
		return nil, err
	}

	// Cache with shorter TTL since it includes computed hours
	_ = cus.cache.Set(key, profilePtr, UserProfileCacheTTL)

	return profilePtr, nil
}


// GetUsersByOrganization is NOT cached (list operation)
func (cus *CachedUserStore) GetUsersByOrganization(orgID uuid.UUID) ([]*database.User, error) {
	return cus.store.GetUsersByOrganization(orgID)
}


// CreateUser is NOT cached (write operation)
// No need to invalidate since the user doesn't exist in cache yet
func (cus *CachedUserStore) CreateUser(user *database.User) error {
	return cus.store.CreateUser(user)
}

// UpdateUser updates database and invalidates cache
func (cus *CachedUserStore) UpdateUser(user *database.User) error {
	// Update database first
	err := cus.store.UpdateUser(user)
	if err != nil {
		return err
	}

	// Invalidate all cache entries for this user
	_ = cus.cache.Delete(
		fmt.Sprintf("user:%s", user.ID),
		fmt.Sprintf("user:email:%s", user.Email),
		fmt.Sprintf("user:%s:profile", user.ID),
	)

	return nil
}

// DeleteUser deletes from database and invalidates cache
func (cus *CachedUserStore) DeleteUser(id uuid.UUID) error {
	// Get user first to know the email for cache invalidation
	user, _ := cus.store.GetUserByID(id)

	// Delete from database
	err := cus.store.DeleteUser(id)
	if err != nil {
		return err
	}

	// Invalidate cache
	keys := []string{
		fmt.Sprintf("user:%s", id),
		fmt.Sprintf("user:%s:profile", id),
	}
	if user != nil {
		keys = append(keys, fmt.Sprintf("user:email:%s", user.Email))
	}
	_ = cus.cache.Delete(keys...)

	return nil
}

// LayoffUser performs layoff and invalidates cache
func (cus *CachedUserStore) LayoffUser(id uuid.UUID, reason string) error {
	// Get user first for cache invalidation
	user, _ := cus.store.GetUserByID(id)

	// Perform layoff (includes deletion)
	err := cus.store.LayoffUser(id, reason)
	if err != nil {
		return err
	}

	// Invalidate cache
	keys := []string{
		fmt.Sprintf("user:%s", id),
		fmt.Sprintf("user:%s:profile", id),
	}
	if user != nil {
		keys = append(keys, fmt.Sprintf("user:email:%s", user.Email))
	}
	_ = cus.cache.Delete(keys...)

	return nil
}

// ChangePassword updates password and invalidates cache
// Note: GetUserByID/Email won't return password hash from cache anyway,
// but we invalidate to be consistent
func (cus *CachedUserStore) ChangePassword(id uuid.UUID, passwordHash []byte) error {
	err := cus.store.ChangePassword(id, passwordHash)
	if err != nil {
		return err
	}

	// Invalidate user cache (even though password isn't cached, be consistent)
	user, _ := cus.store.GetUserByID(id)
	keys := []string{fmt.Sprintf("user:%s", id)}
	if user != nil {
		keys = append(keys, fmt.Sprintf("user:email:%s", user.Email))
	}
	_ = cus.cache.Delete(keys...)

	return nil
}
