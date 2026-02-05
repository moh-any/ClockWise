package database

import (
	"database/sql"
	"errors"
	"log/slog"
	"time"

	"github.com/google/uuid"
)

// OrganizationRules represents the scheduling rules for an organization
type OrganizationRules struct {
	OrganizationID uuid.UUID `json:"organization_id"`
	ShiftMaxHours  int       `json:"shift_max_hours"`
	ShiftMinHours  int       `json:"shift_min_hours"`
	MaxWeeklyHours int       `json:"max_weekly_hours"`
	MinWeeklyHours int       `json:"min_weekly_hours"`
}

// RulesStore defines the interface for organization rules data operations
type RulesStore interface {
	CreateRules(rules *OrganizationRules) error
	GetRulesByOrganizationID(orgID uuid.UUID) (*OrganizationRules, error)
	UpdateRules(rules *OrganizationRules) error
	UpsertRules(rules *OrganizationRules) error
}

// PostgresRulesStore implements RulesStore using PostgreSQL
type PostgresRulesStore struct {
	db     *sql.DB
	Logger *slog.Logger
}

// NewPostgresRulesStore creates a new PostgresRulesStore
func NewPostgresRulesStore(db *sql.DB, logger *slog.Logger) *PostgresRulesStore {
	return &PostgresRulesStore{
		db:     db,
		Logger: logger,
	}
}

// CreateRules creates a new rules record for an organization
func (s *PostgresRulesStore) CreateRules(rules *OrganizationRules) error {
	query := `INSERT INTO organizations_rules 
		(organization_id, shift_max_hours, shift_min_hours, max_weekly_hours, min_weekly_hours) 
		VALUES ($1, $2, $3, $4, $5)`

	_, err := s.db.Exec(query,
		rules.OrganizationID,
		rules.ShiftMaxHours,
		rules.ShiftMinHours,
		rules.MaxWeeklyHours,
		rules.MinWeeklyHours,
	)
	if err != nil {
		s.Logger.Error("failed to create rules", "error", err, "organization_id", rules.OrganizationID)
		return err
	}

	s.Logger.Info("rules created", "organization_id", rules.OrganizationID)
	return nil
}

// GetRulesByOrganizationID retrieves rules for a specific organization
func (s *PostgresRulesStore) GetRulesByOrganizationID(orgID uuid.UUID) (*OrganizationRules, error) {
	var rules OrganizationRules

	query := `SELECT organization_id, shift_max_hours, shift_min_hours, max_weekly_hours, min_weekly_hours 
		FROM organizations_rules WHERE organization_id = $1`

	err := s.db.QueryRow(query, orgID).Scan(
		&rules.OrganizationID,
		&rules.ShiftMaxHours,
		&rules.ShiftMinHours,
		&rules.MaxWeeklyHours,
		&rules.MinWeeklyHours,
	)
	if err != nil {
		if errors.Is(err, sql.ErrNoRows) {
			return nil, nil // No rules found
		}
		s.Logger.Error("failed to get rules", "error", err, "organization_id", orgID)
		return nil, err
	}

	return &rules, nil
}

// UpdateRules updates an existing rules record
func (s *PostgresRulesStore) UpdateRules(rules *OrganizationRules) error {
	query := `UPDATE organizations_rules SET 
		shift_max_hours = $2, 
		shift_min_hours = $3, 
		max_weekly_hours = $4, 
		min_weekly_hours = $5 
		WHERE organization_id = $1`

	result, err := s.db.Exec(query,
		rules.OrganizationID,
		rules.ShiftMaxHours,
		rules.ShiftMinHours,
		rules.MaxWeeklyHours,
		rules.MinWeeklyHours,
	)
	if err != nil {
		s.Logger.Error("failed to update rules", "error", err, "organization_id", rules.OrganizationID)
		return err
	}

	rowsAffected, _ := result.RowsAffected()
	if rowsAffected == 0 {
		return errors.New("no rules found to update")
	}

	s.Logger.Info("rules updated", "organization_id", rules.OrganizationID)
	return nil
}

// UpsertRules creates or updates rules for an organization
func (s *PostgresRulesStore) UpsertRules(rules *OrganizationRules) error {
	query := `INSERT INTO organizations_rules 
		(organization_id, shift_max_hours, shift_min_hours, max_weekly_hours, min_weekly_hours) 
		VALUES ($1, $2, $3, $4, $5)
		ON CONFLICT (organization_id) DO UPDATE SET 
		shift_max_hours = EXCLUDED.shift_max_hours,
		shift_min_hours = EXCLUDED.shift_min_hours,
		max_weekly_hours = EXCLUDED.max_weekly_hours,
		min_weekly_hours = EXCLUDED.min_weekly_hours`

	_, err := s.db.Exec(query,
		rules.OrganizationID,
		rules.ShiftMaxHours,
		rules.ShiftMinHours,
		rules.MaxWeeklyHours,
		rules.MinWeeklyHours,
	)
	if err != nil {
		s.Logger.Error("failed to upsert rules", "error", err, "organization_id", rules.OrganizationID)
		return err
	}

	s.Logger.Info("rules upserted", "organization_id", rules.OrganizationID)
	return nil
}

// OperatingHours represents the operating hours for a specific day
type OperatingHours struct {
	OrganizationID uuid.UUID `json:"organization_id"`
	Weekday        string    `json:"weekday"`
	OpeningTime    time.Time `json:"opening_time"`
	ClosingTime    time.Time `json:"closing_time"`
}

// GetOperatingHoursByOrganizationID retrieves all operating hours for an organization
func (s *PostgresRulesStore) GetOperatingHoursByOrganizationID(orgID uuid.UUID) ([]*OperatingHours, error) {
	query := `SELECT organization_id, weekday, opening_time, closing_time 
		FROM organizations_operating_hours WHERE organization_id = $1 ORDER BY weekday`

	rows, err := s.db.Query(query, orgID)
	if err != nil {
		s.Logger.Error("failed to get operating hours", "error", err, "organization_id", orgID)
		return nil, err
	}
	defer rows.Close()

	var hours []*OperatingHours
	for rows.Next() {
		var h OperatingHours
		if err := rows.Scan(&h.OrganizationID, &h.Weekday, &h.OpeningTime, &h.ClosingTime); err != nil {
			return nil, err
		}
		hours = append(hours, &h)
	}

	return hours, nil
}
