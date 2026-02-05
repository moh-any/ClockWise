package database

import (
	"database/sql"
	"errors"
	"log/slog"
	"time"

	"github.com/google/uuid"
)

// Preferences represents an employee's work preferences
type Preferences struct {
	EmployeeID           uuid.UUID `json:"employee_id"`
	OrganizationID       uuid.UUID `json:"organization_id"`
	PreferredStartTime   string    `json:"preferred_start_time"`
	PreferredEndTime     string    `json:"preferred_end_time"`
	AvailableStartTime   string    `json:"available_start_time"`
	AvailableEndTime     string    `json:"available_end_time"`
	PreferredDaysPerWeek int       `json:"preferred_days_per_week"`
	AvailableDaysPerWeek int       `json:"available_days_per_week"`
	CreatedAt            time.Time `json:"created_at"`
	UpdatedAt            time.Time `json:"updated_at"`
}

// PreferencesStore defines the interface for preferences data operations
type PreferencesStore interface {
	CreatePreferences(prefs *Preferences) error
	GetPreferencesByEmployeeID(employeeID uuid.UUID) (*Preferences, error)
	UpdatePreferences(prefs *Preferences) error
	DeletePreferences(employeeID uuid.UUID) error
	UpsertPreferences(prefs *Preferences) error
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

// CreatePreferences creates a new preferences record for an employee
func (s *PostgresPreferencesStore) CreatePreferences(prefs *Preferences) error {
	now := time.Now()
	prefs.CreatedAt = now
	prefs.UpdatedAt = now

	query := `INSERT INTO preferences 
		(employee_id, organization_id, preferred_start_time, preferred_end_time, 
		 available_start_time, available_end_time, preferred_days_per_week, 
		 available_days_per_week, created_at, updated_at) 
		VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)`

	_, err := s.db.Exec(query,
		prefs.EmployeeID,
		prefs.OrganizationID,
		prefs.PreferredStartTime,
		prefs.PreferredEndTime,
		prefs.AvailableStartTime,
		prefs.AvailableEndTime,
		prefs.PreferredDaysPerWeek,
		prefs.AvailableDaysPerWeek,
		prefs.CreatedAt,
		prefs.UpdatedAt,
	)
	if err != nil {
		s.Logger.Error("failed to create preferences", "error", err, "employee_id", prefs.EmployeeID)
		return err
	}

	s.Logger.Info("preferences created", "employee_id", prefs.EmployeeID)
	return nil
}

// GetPreferencesByEmployeeID retrieves preferences for a specific employee
func (s *PostgresPreferencesStore) GetPreferencesByEmployeeID(employeeID uuid.UUID) (*Preferences, error) {
	var prefs Preferences

	query := `SELECT employee_id, organization_id, preferred_start_time, preferred_end_time, 
		available_start_time, available_end_time, preferred_days_per_week, 
		available_days_per_week, created_at, updated_at 
		FROM preferences WHERE employee_id = $1`

	err := s.db.QueryRow(query, employeeID).Scan(
		&prefs.EmployeeID,
		&prefs.OrganizationID,
		&prefs.PreferredStartTime,
		&prefs.PreferredEndTime,
		&prefs.AvailableStartTime,
		&prefs.AvailableEndTime,
		&prefs.PreferredDaysPerWeek,
		&prefs.AvailableDaysPerWeek,
		&prefs.CreatedAt,
		&prefs.UpdatedAt,
	)
	if err != nil {
		if errors.Is(err, sql.ErrNoRows) {
			return nil, nil // No preferences found
		}
		s.Logger.Error("failed to get preferences", "error", err, "employee_id", employeeID)
		return nil, err
	}

	return &prefs, nil
}

// UpdatePreferences updates an existing preferences record
func (s *PostgresPreferencesStore) UpdatePreferences(prefs *Preferences) error {
	prefs.UpdatedAt = time.Now()

	query := `UPDATE preferences SET 
		preferred_start_time = $2, 
		preferred_end_time = $3, 
		available_start_time = $4, 
		available_end_time = $5, 
		preferred_days_per_week = $6, 
		available_days_per_week = $7, 
		updated_at = $8 
		WHERE employee_id = $1`

	result, err := s.db.Exec(query,
		prefs.EmployeeID,
		prefs.PreferredStartTime,
		prefs.PreferredEndTime,
		prefs.AvailableStartTime,
		prefs.AvailableEndTime,
		prefs.PreferredDaysPerWeek,
		prefs.AvailableDaysPerWeek,
		prefs.UpdatedAt,
	)
	if err != nil {
		s.Logger.Error("failed to update preferences", "error", err, "employee_id", prefs.EmployeeID)
		return err
	}

	rowsAffected, _ := result.RowsAffected()
	if rowsAffected == 0 {
		return errors.New("no preferences found to update")
	}

	s.Logger.Info("preferences updated", "employee_id", prefs.EmployeeID)
	return nil
}

// DeletePreferences removes preferences for an employee
func (s *PostgresPreferencesStore) DeletePreferences(employeeID uuid.UUID) error {
	query := `DELETE FROM preferences WHERE employee_id = $1`

	result, err := s.db.Exec(query, employeeID)
	if err != nil {
		s.Logger.Error("failed to delete preferences", "error", err, "employee_id", employeeID)
		return err
	}

	rowsAffected, _ := result.RowsAffected()
	if rowsAffected == 0 {
		return errors.New("no preferences found to delete")
	}

	s.Logger.Info("preferences deleted", "employee_id", employeeID)
	return nil
}

// UpsertPreferences creates or updates preferences for an employee
func (s *PostgresPreferencesStore) UpsertPreferences(prefs *Preferences) error {
	now := time.Now()
	prefs.UpdatedAt = now

	query := `INSERT INTO preferences 
		(employee_id, organization_id, preferred_start_time, preferred_end_time, 
		 available_start_time, available_end_time, preferred_days_per_week, 
		 available_days_per_week, created_at, updated_at) 
		VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
		ON CONFLICT (employee_id) DO UPDATE SET 
		preferred_start_time = EXCLUDED.preferred_start_time,
		preferred_end_time = EXCLUDED.preferred_end_time,
		available_start_time = EXCLUDED.available_start_time,
		available_end_time = EXCLUDED.available_end_time,
		preferred_days_per_week = EXCLUDED.preferred_days_per_week,
		available_days_per_week = EXCLUDED.available_days_per_week,
		updated_at = EXCLUDED.updated_at`

	_, err := s.db.Exec(query,
		prefs.EmployeeID,
		prefs.OrganizationID,
		prefs.PreferredStartTime,
		prefs.PreferredEndTime,
		prefs.AvailableStartTime,
		prefs.AvailableEndTime,
		prefs.PreferredDaysPerWeek,
		prefs.AvailableDaysPerWeek,
		now, // created_at (only used on insert)
		prefs.UpdatedAt,
	)
	if err != nil {
		s.Logger.Error("failed to upsert preferences", "error", err, "employee_id", prefs.EmployeeID)
		return err
	}

	s.Logger.Info("preferences upserted", "employee_id", prefs.EmployeeID)
	return nil
}
