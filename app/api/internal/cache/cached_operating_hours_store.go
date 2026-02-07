package cache

import (
	"fmt"
	"time"

	"github.com/clockwise/clockwise/backend/internal/database"
	"github.com/google/uuid"
)

const (
	// Configuration data, changes rarely
	OperatingHoursCacheTTL = 60 * time.Minute
)

type CachedOperatingHoursStore struct {
	store database.OperatingHoursStore
	cache *CacheService
}

func NewCachedOperatingHoursStore(store database.OperatingHoursStore, cache *CacheService) database.OperatingHoursStore {
	return &CachedOperatingHoursStore{
		store: store,
		cache: cache,
	}
}

// GetOperatingHours retrieves the full week schedule
// Cache key: org:{uuid}:operating_hours
func (cs *CachedOperatingHoursStore) GetOperatingHours(orgID uuid.UUID) ([]database.OperatingHours, error) {
	key := fmt.Sprintf("org:%s:operating_hours", orgID)

	var hours []database.OperatingHours
	if err := cs.cache.Get(key, &hours); err == nil {
		return hours, nil
	}

	hours, err := cs.store.GetOperatingHours(orgID)
	if err != nil {
		return nil, err
	}

	_ = cs.cache.Set(key, hours, OperatingHoursCacheTTL)
	return hours, nil
}

// GetOperatingHoursByDay retrieves a single day
// Cache key: org:{uuid}:operating_hours:{weekday}
func (cs *CachedOperatingHoursStore) GetOperatingHoursByDay(orgID uuid.UUID, weekday string) (*database.OperatingHours, error) {
	key := fmt.Sprintf("org:%s:operating_hours:%s", orgID, weekday)

	var hours database.OperatingHours
	if err := cs.cache.Get(key, &hours); err == nil {
		return &hours, nil
	}

	hoursPtr, err := cs.store.GetOperatingHoursByDay(orgID, weekday)
	if err != nil {
		return nil, err
	}

	_ = cs.cache.Set(key, hoursPtr, OperatingHoursCacheTTL)
	return hoursPtr, nil
}

// SetOperatingHours invalidates the full schedule and all individual days
func (cs *CachedOperatingHoursStore) SetOperatingHours(orgID uuid.UUID, hours []database.OperatingHours) error {
	err := cs.store.SetOperatingHours(orgID, hours)
	if err != nil {
		return err
	}

	cs.invalidateAll(orgID)
	return nil
}

// UpsertOperatingHours invalidates the full schedule and the specific day
func (cs *CachedOperatingHoursStore) UpsertOperatingHours(hours *database.OperatingHours) error {
	err := cs.store.UpsertOperatingHours(hours)
	if err != nil {
		return err
	}

	// We must invalidate the full list because one day changed
	cs.invalidateAll(hours.OrganizationID)
	return nil
}

// DeleteOperatingHoursByDay invalidates caches
func (cs *CachedOperatingHoursStore) DeleteOperatingHoursByDay(orgID uuid.UUID, weekday string) error {
	err := cs.store.DeleteOperatingHoursByDay(orgID, weekday)
	if err != nil {
		return err
	}

	cs.invalidateAll(orgID)
	return nil
}

// DeleteAllOperatingHours invalidates all caches
func (cs *CachedOperatingHoursStore) DeleteAllOperatingHours(orgID uuid.UUID) error {
	err := cs.store.DeleteAllOperatingHours(orgID)
	if err != nil {
		return err
	}

	cs.invalidateAll(orgID)
	return nil
}

// Helper to invalidate the main schedule and all possible daily keys
func (cs *CachedOperatingHoursStore) invalidateAll(orgID uuid.UUID) {
	weekdays := []string{"Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"}

	keys := []string{fmt.Sprintf("org:%s:operating_hours", orgID)}
	for _, day := range weekdays {
		keys = append(keys, fmt.Sprintf("org:%s:operating_hours:%s", orgID, day))
	}

	_ = cs.cache.Delete(keys...)
}
