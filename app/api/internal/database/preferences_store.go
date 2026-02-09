package database

import (
	"database/sql"
	"errors"
	"log/slog"

	"github.com/google/uuid"
)

// EmployeePreference represents a single day's preference for an employee
type EmployeePreference struct {
	EmployeeID         uuid.UUID `json:"employee_id"`
	Day                string    `json:"day" binding:"required,oneof=sunday monday tuesday wednesday thursday friday saturday"`
	PreferredStartTime *string   `json:"preferred_start_time"`
	PreferredEndTime   *string   `json:"preferred_end_time"`
	AvailableStartTime *string   `json:"available_start_time"`
	AvailableEndTime   *string   `json:"available_end_time"`
}

// ValidDays is the list of valid day values
var ValidDays = []string{"sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday"}

// IsValidDay checks if a day string is valid
func IsValidDay(day string) bool {
	for _, d := range ValidDays {
		if d == day {
			return true
		}
	}
	return false
}

// PreferencesStore defines the interface for employee preferences data operations
type PreferencesStore interface {
	// Create or update a single day's preference
	UpsertPreference(pref *EmployeePreference) error
	// Create or update multiple day preferences at once
	UpsertPreferences(employeeID uuid.UUID, prefs []EmployeePreference) error
	// Get all preferences for an employee
	GetPreferencesByEmployeeID(employeeID uuid.UUID) ([]EmployeePreference, error)
	// Get preference for a specific day
	GetPreferenceByDay(employeeID uuid.UUID, day string) (*EmployeePreference, error)
	// Delete all preferences for an employee
	DeletePreferences(employeeID uuid.UUID) error
	// Delete preference for a specific day
	DeletePreferenceByDay(employeeID uuid.UUID, day string) error
}

// PostgresPreferencesStore implements PreferencesStore using PostgreSQL
type PostgresPreferencesStore struct {
	db     *sql.DB
	Logger *slog.Logger
}

// NewPostgresPreferencesStore creates a new PostgresPreferencesStore
func NewPostgresPreferencesStore(db *sql.DB, logger *slog.Logger) *PostgresPreferencesStore {
	return &PostgresPreferencesStore{
		db:     db,
		Logger: logger,
	}
}

// UpsertPreference creates or updates a single day's preference
func (s *PostgresPreferencesStore) UpsertPreference(pref *EmployeePreference) error {
	query := `INSERT INTO employees_preferences 
		(employee_id, day, preferred_start_time, preferred_end_time, available_start_time, available_end_time) 
		VALUES ($1, $2, $3, $4, $5, $6)
		ON CONFLICT (employee_id, day) DO UPDATE SET 
		preferred_start_time = EXCLUDED.preferred_start_time,
		preferred_end_time = EXCLUDED.preferred_end_time,
		available_start_time = EXCLUDED.available_start_time,
		available_end_time = EXCLUDED.available_end_time`

	_, err := s.db.Exec(query,
		pref.EmployeeID,
		pref.Day,
		pref.PreferredStartTime,
		pref.PreferredEndTime,
		pref.AvailableStartTime,
		pref.AvailableEndTime,
	)
	if err != nil {
		s.Logger.Error("failed to upsert preference", "error", err, "employee_id", pref.EmployeeID, "day", pref.Day)
		return err
	}

	s.Logger.Info("preference upserted", "employee_id", pref.EmployeeID, "day", pref.Day)
	return nil
}

// UpsertPreferences creates or updates multiple day preferences at once
func (s *PostgresPreferencesStore) UpsertPreferences(employeeID uuid.UUID, prefs []EmployeePreference) error {
	tx, err := s.db.Begin()
	if err != nil {
		s.Logger.Error("failed to begin transaction", "error", err)
		return err
	}
	defer tx.Rollback()

	query := `INSERT INTO employees_preferences 
		(employee_id, day, preferred_start_time, preferred_end_time, available_start_time, available_end_time) 
		VALUES ($1, $2, $3, $4, $5, $6)
		ON CONFLICT (employee_id, day) DO UPDATE SET 
		preferred_start_time = EXCLUDED.preferred_start_time,
		preferred_end_time = EXCLUDED.preferred_end_time,
		available_start_time = EXCLUDED.available_start_time,
		available_end_time = EXCLUDED.available_end_time`

	for _, pref := range prefs {
		_, err := tx.Exec(query,
			employeeID,
			pref.Day,
			pref.PreferredStartTime,
			pref.PreferredEndTime,
			pref.AvailableStartTime,
			pref.AvailableEndTime,
		)
		if err != nil {
			s.Logger.Error("failed to upsert preference in batch", "error", err, "employee_id", employeeID, "day", pref.Day)
			return err
		}
	}

	if err := tx.Commit(); err != nil {
		s.Logger.Error("failed to commit transaction", "error", err)
		return err
	}

	s.Logger.Info("preferences upserted", "employee_id", employeeID, "count", len(prefs))
	return nil
}

// GetPreferencesByEmployeeID retrieves all preferences for an employee
func (s *PostgresPreferencesStore) GetPreferencesByEmployeeID(employeeID uuid.UUID) ([]EmployeePreference, error) {
	query := `SELECT employee_id, day, preferred_start_time, preferred_end_time, available_start_time, available_end_time 
		FROM employees_preferences WHERE employee_id = $1 ORDER BY 
		CASE day 
			WHEN 'sunday' THEN 0 
			WHEN 'monday' THEN 1 
			WHEN 'tuesday' THEN 2 
			WHEN 'wednesday' THEN 3 
			WHEN 'thursday' THEN 4 
			WHEN 'friday' THEN 5 
			WHEN 'saturday' THEN 6 
		END`

	rows, err := s.db.Query(query, employeeID)
	if err != nil {
		s.Logger.Error("failed to get preferences", "error", err, "employee_id", employeeID)
		return nil, err
	}
	defer rows.Close()

	var prefs []EmployeePreference
	for rows.Next() {
		var p EmployeePreference
		if err := rows.Scan(
			&p.EmployeeID,
			&p.Day,
			&p.PreferredStartTime,
			&p.PreferredEndTime,
			&p.AvailableStartTime,
			&p.AvailableEndTime,
		); err != nil {
			s.Logger.Error("failed to scan preference", "error", err)
			return nil, err
		}
		prefs = append(prefs, p)
	}

	return prefs, nil
}

// GetPreferenceByDay retrieves preference for a specific day
func (s *PostgresPreferencesStore) GetPreferenceByDay(employeeID uuid.UUID, day string) (*EmployeePreference, error) {
	var pref EmployeePreference

	query := `SELECT employee_id, day, preferred_start_time, preferred_end_time, available_start_time, available_end_time 
		FROM employees_preferences WHERE employee_id = $1 AND day = $2`

	err := s.db.QueryRow(query, employeeID, day).Scan(
		&pref.EmployeeID,
		&pref.Day,
		&pref.PreferredStartTime,
		&pref.PreferredEndTime,
		&pref.AvailableStartTime,
		&pref.AvailableEndTime,
	)
	if err != nil {
		if errors.Is(err, sql.ErrNoRows) {
			return nil, nil // No preference found
		}
		s.Logger.Error("failed to get preference", "error", err, "employee_id", employeeID, "day", day)
		return nil, err
	}

	return &pref, nil
}

// DeletePreferences removes all preferences for an employee
func (s *PostgresPreferencesStore) DeletePreferences(employeeID uuid.UUID) error {
	query := `DELETE FROM employees_preferences WHERE employee_id = $1`

	result, err := s.db.Exec(query, employeeID)
	if err != nil {
		s.Logger.Error("failed to delete preferences", "error", err, "employee_id", employeeID)
		return err
	}

	rowsAffected, _ := result.RowsAffected()
	s.Logger.Info("preferences deleted", "employee_id", employeeID, "count", rowsAffected)
	return nil
}

// DeletePreferenceByDay removes preference for a specific day
func (s *PostgresPreferencesStore) DeletePreferenceByDay(employeeID uuid.UUID, day string) error {
	query := `DELETE FROM employees_preferences WHERE employee_id = $1 AND day = $2`

	result, err := s.db.Exec(query, employeeID, day)
	if err != nil {
		s.Logger.Error("failed to delete preference", "error", err, "employee_id", employeeID, "day", day)
		return err
	}

	rowsAffected, _ := result.RowsAffected()
	if rowsAffected == 0 {
		return errors.New("no preference found to delete")
	}

	s.Logger.Info("preference deleted", "employee_id", employeeID, "day", day)
	return nil
}
