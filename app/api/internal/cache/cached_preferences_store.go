package cache

import (
	"fmt"
	"time"

	"github.com/clockwise/clockwise/backend/internal/database"
	"github.com/google/uuid"
)

const (
	// User preferences (availability) are configuration data
	PreferencesCacheTTL = 15 * time.Minute
)

type CachedPreferencesStore struct {
	store database.PreferencesStore
	cache *CacheService
}

func NewCachedPreferencesStore(store database.PreferencesStore, cache *CacheService) database.PreferencesStore {
	return &CachedPreferencesStore{
		store: store,
		cache: cache,
	}
}

// UpsertPreference invalidates the specific day and the full list
func (cps *CachedPreferencesStore) UpsertPreference(pref *database.EmployeePreference) error {
	err := cps.store.UpsertPreference(pref)
	if err != nil {
		return err
	}

	_ = cps.cache.Delete(
		fmt.Sprintf("user:%s:preferences", pref.EmployeeID),
		fmt.Sprintf("user:%s:preferences:%s", pref.EmployeeID, pref.Day),
	)

	return nil
}

// UpsertPreferences invalidates the list and all relevant days
func (cps *CachedPreferencesStore) UpsertPreferences(employeeID uuid.UUID, prefs []*database.EmployeePreference) error {
	err := cps.store.UpsertPreferences(employeeID, prefs)
	if err != nil {
		return err
	}

	// Invalidate the main list
	keys := []string{fmt.Sprintf("user:%s:preferences", employeeID)}

	// Invalidate individual days
	for _, p := range prefs {
		keys = append(keys, fmt.Sprintf("user:%s:preferences:%s", employeeID, p.Day))
	}

	_ = cps.cache.Delete(keys...)
	return nil
}

// GetPreferencesByEmployeeID retrieves the full set of preferences
// Cache key: user:{uuid}:preferences
func (cps *CachedPreferencesStore) GetPreferencesByEmployeeID(employeeID uuid.UUID) ([]*database.EmployeePreference, error) {
	key := fmt.Sprintf("user:%s:preferences", employeeID)

	var prefs []*database.EmployeePreference
	if err := cps.cache.Get(key, &prefs); err == nil {
		return prefs, nil
	}

	prefs, err := cps.store.GetPreferencesByEmployeeID(employeeID)
	if err != nil {
		return nil, err
	}

	_ = cps.cache.Set(key, prefs, PreferencesCacheTTL)
	return prefs, nil
}

// GetPreferenceByDay retrieves a single day preference
// Cache key: user:{uuid}:preferences:{day}
func (cps *CachedPreferencesStore) GetPreferenceByDay(employeeID uuid.UUID, day string) (*database.EmployeePreference, error) {
	key := fmt.Sprintf("user:%s:preferences:%s", employeeID, day)

	var pref database.EmployeePreference
	if err := cps.cache.Get(key, &pref); err == nil {
		return &pref, nil
	}

	prefPtr, err := cps.store.GetPreferenceByDay(employeeID, day)
	if err != nil {
		return nil, err
	}

	// Handle nil result (no preference found)
	if prefPtr == nil {
		return nil, nil
	}

	_ = cps.cache.Set(key, prefPtr, PreferencesCacheTTL)
	return prefPtr, nil
}

// DeletePreferences invalidates everything for the user
func (cps *CachedPreferencesStore) DeletePreferences(employeeID uuid.UUID) error {
	err := cps.store.DeletePreferences(employeeID)
	if err != nil {
		return err
	}

	// Invalidate list
	keys := []string{fmt.Sprintf("user:%s:preferences", employeeID)}

	// Invalidate all potential days
	weekdays := []string{"sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday"}
	for _, day := range weekdays {
		keys = append(keys, fmt.Sprintf("user:%s:preferences:%s", employeeID, day))
	}

	_ = cps.cache.Delete(keys...)
	return nil
}

// DeletePreferenceByDay invalidates the list and the specific day
func (cps *CachedPreferencesStore) DeletePreferenceByDay(employeeID uuid.UUID, day string) error {
	err := cps.store.DeletePreferenceByDay(employeeID, day)
	if err != nil {
		return err
	}

	_ = cps.cache.Delete(
		fmt.Sprintf("user:%s:preferences", employeeID),
		fmt.Sprintf("user:%s:preferences:%s", employeeID, day),
	)

	return nil
}
