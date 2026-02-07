package database

import (
	"database/sql"
	"errors"
	"log/slog"

	"github.com/google/uuid"
)

// OperatingHours represents the operating hours for a specific day
type OperatingHours struct {
	OrganizationID uuid.UUID `json:"-"`
	Weekday        string    `json:"weekday"`
	OpeningTime    string    `json:"opening_time,omitempty"`
	ClosingTime    string    `json:"closing_time,omitempty"`
	Closed         *bool     `json:"closed,omitempty"`
}

// OperatingHoursStore defines the interface for operating hours data operations
type OperatingHoursStore interface {
	// Get all operating hours for an organization
	GetOperatingHours(orgID uuid.UUID) ([]OperatingHours, error)
	// Get operating hours for a specific day
	GetOperatingHoursByDay(orgID uuid.UUID, weekday string) (*OperatingHours, error)
	// Set operating hours for multiple days (replaces existing)
	SetOperatingHours(orgID uuid.UUID, hours []OperatingHours) error
	// Upsert a single day's operating hours
	UpsertOperatingHours(hours *OperatingHours) error
	// Delete operating hours for a specific day
	DeleteOperatingHoursByDay(orgID uuid.UUID, weekday string) error
	// Delete all operating hours for an organization
	DeleteAllOperatingHours(orgID uuid.UUID) error
}

// PostgresOperatingHoursStore implements OperatingHoursStore using PostgreSQL
type PostgresOperatingHoursStore struct {
	db     *sql.DB
	Logger *slog.Logger
}

// NewPostgresOperatingHoursStore creates a new PostgresOperatingHoursStore
func NewPostgresOperatingHoursStore(db *sql.DB, logger *slog.Logger) *PostgresOperatingHoursStore {
	return &PostgresOperatingHoursStore{
		db:     db,
		Logger: logger,
	}
}

// GetOperatingHours retrieves all operating hours for an organization
func (s *PostgresOperatingHoursStore) GetOperatingHours(orgID uuid.UUID) ([]OperatingHours, error) {
	query := `SELECT organization_id, weekday, opening_time, closing_time
		FROM organizations_operating_hours WHERE organization_id = $1 ORDER BY 
		CASE weekday 
			WHEN 'Sunday' THEN 0 
			WHEN 'Monday' THEN 1 
			WHEN 'Tuesday' THEN 2 
			WHEN 'Wednesday' THEN 3 
			WHEN 'Thursday' THEN 4 
			WHEN 'Friday' THEN 5 
			WHEN 'Saturday' THEN 6 
		END`

	rows, err := s.db.Query(query, orgID)
	if err != nil {
		s.Logger.Error("failed to get operating hours", "error", err, "organization_id", orgID)
		return nil, err
	}
	defer rows.Close()

	// Create a map to store existing operating hours by weekday
	hoursMap := make(map[string]OperatingHours)
	for rows.Next() {
		var h OperatingHours
		if err := rows.Scan(
			&h.OrganizationID,
			&h.Weekday,
			&h.OpeningTime,
			&h.ClosingTime,
		); err != nil {
			s.Logger.Error("failed to scan operating hours", "error", err)
			return nil, err
		}
		hoursMap[h.Weekday] = h
	}

	// Define all weekdays in order
	allWeekdays := []string{"Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"}

	// Build the complete result with all 7 days
	var hours []OperatingHours
	for _, weekday := range allWeekdays {
		if existingHours, found := hoursMap[weekday]; found {
			// Day has operating hours in database
			hours = append(hours, existingHours)
		} else {
			// Day not in database - add with closed flag
			closed := true
			hours = append(hours, OperatingHours{
				OrganizationID: orgID,
				Weekday:        weekday,
				Closed:         &closed,
			})
		}
	}

	return hours, nil
}

// GetOperatingHoursByDay retrieves operating hours for a specific day
func (s *PostgresOperatingHoursStore) GetOperatingHoursByDay(orgID uuid.UUID, weekday string) (*OperatingHours, error) {
	var hours OperatingHours
	var closed bool

	query := `SELECT organization_id, weekday, opening_time, closing_time
		FROM organizations_operating_hours WHERE organization_id = $1 AND weekday = $2`

	err := s.db.QueryRow(query, orgID, weekday).Scan(
		&hours.OrganizationID,
		&hours.Weekday,
		&hours.OpeningTime,
		&hours.ClosingTime,
	)
	if err != nil {
		if errors.Is(err, sql.ErrNoRows) {
			// Day not found - return closed status
			closed := true
			return &OperatingHours{
				OrganizationID: orgID,
				Weekday:        weekday,
				Closed:         &closed,
			}, nil
		}
		s.Logger.Error("failed to get operating hours by day", "error", err, "organization_id", orgID, "weekday", weekday)
		return nil, err
	}

	hours.Closed = &closed
	return &hours, nil
}

// SetOperatingHours replaces all operating hours for an organization
func (s *PostgresOperatingHoursStore) SetOperatingHours(orgID uuid.UUID, hours []OperatingHours) error {
	tx, err := s.db.Begin()
	if err != nil {
		s.Logger.Error("failed to begin transaction", "error", err)
		return err
	}
	defer tx.Rollback()

	// Delete existing operating hours
	deleteQuery := `DELETE FROM organizations_operating_hours WHERE organization_id = $1`
	_, err = tx.Exec(deleteQuery, orgID)
	if err != nil {
		s.Logger.Error("failed to delete existing operating hours", "error", err, "organization_id", orgID)
		return err
	}

	// Insert new operating hours
	insertQuery := `INSERT INTO organizations_operating_hours (organization_id, weekday, opening_time, closing_time) 
		VALUES ($1, $2, $3, $4)`
	for _, h := range hours {
		_, err = tx.Exec(insertQuery, orgID, h.Weekday, h.OpeningTime, h.ClosingTime)
		if err != nil {
			s.Logger.Error("failed to insert operating hours", "error", err, "organization_id", orgID, "weekday", h.Weekday)
			return err
		}
	}

	if err := tx.Commit(); err != nil {
		s.Logger.Error("failed to commit transaction", "error", err)
		return err
	}

	s.Logger.Info("operating hours set", "organization_id", orgID, "count", len(hours))
	return nil
}

// UpsertOperatingHours creates or updates a single day's operating hours
func (s *PostgresOperatingHoursStore) UpsertOperatingHours(hours *OperatingHours) error {
	query := `INSERT INTO organizations_operating_hours (organization_id, weekday, opening_time, closing_time) 
		VALUES ($1, $2, $3, $4)
		ON CONFLICT (organization_id, weekday) DO UPDATE SET 
		opening_time = EXCLUDED.opening_time,
		closing_time = EXCLUDED.closing_time`
	_, err := s.db.Exec(query, hours.OrganizationID, hours.Weekday, hours.OpeningTime, hours.ClosingTime)
	if err != nil {
		s.Logger.Error("failed to upsert operating hours", "error", err, "organization_id", hours.OrganizationID, "weekday", hours.Weekday)
		return err
	}

	s.Logger.Info("operating hours upserted", "organization_id", hours.OrganizationID, "weekday", hours.Weekday)
	return nil
}

// DeleteOperatingHoursByDay removes operating hours for a specific day
func (s *PostgresOperatingHoursStore) DeleteOperatingHoursByDay(orgID uuid.UUID, weekday string) error {
	query := `DELETE FROM organizations_operating_hours WHERE organization_id = $1 AND weekday = $2`

	result, err := s.db.Exec(query, orgID, weekday)
	if err != nil {
		s.Logger.Error("failed to delete operating hours", "error", err, "organization_id", orgID, "weekday", weekday)
		return err
	}

	rowsAffected, _ := result.RowsAffected()
	if rowsAffected == 0 {
		return errors.New("no operating hours found to delete")
	}

	s.Logger.Info("operating hours deleted", "organization_id", orgID, "weekday", weekday)
	return nil
}

// DeleteAllOperatingHours removes all operating hours for an organization
func (s *PostgresOperatingHoursStore) DeleteAllOperatingHours(orgID uuid.UUID) error {
	query := `DELETE FROM organizations_operating_hours WHERE organization_id = $1`

	result, err := s.db.Exec(query, orgID)
	if err != nil {
		s.Logger.Error("failed to delete all operating hours", "error", err, "organization_id", orgID)
		return err
	}

	rowsAffected, _ := result.RowsAffected()
	s.Logger.Info("all operating hours deleted", "organization_id", orgID, "count", rowsAffected)
	return nil
}
