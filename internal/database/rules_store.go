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
	OrganizationID       uuid.UUID   `json:"organization_id"`
	ShiftMaxHours        int         `json:"shift_max_hours"`
	ShiftMinHours        int         `json:"shift_min_hours"`
	MaxWeeklyHours       int         `json:"max_weekly_hours"`
	MinWeeklyHours       int         `json:"min_weekly_hours"`
	FixedShifts          bool        `json:"fixed_shifts"`
	NumberOfShiftsPerDay *int        `json:"number_of_shifts_per_day"`
	MeetAllDemand        bool        `json:"meet_all_demand"`
	MinRestSlots         int         `json:"min_rest_slots"`
	SlotLenHour          float64     `json:"slot_len_hour"`
	MinShiftLengthSlots  int         `json:"min_shift_length_slots"`
	ShiftTimes           []ShiftTime `json:"shift_times,omitempty"`
}

type ShiftTime struct {
	StartTime time.Time `json:"from"`
	EndTime   time.Time `json:"to"`
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
		(organization_id, shift_max_hours, shift_min_hours, max_weekly_hours, min_weekly_hours, 
		 fixed_shifts, number_of_shifts_per_day, meet_all_demand, min_rest_slots, slot_len_hour, min_shift_length_slots) 
		VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)`

	_, err := s.db.Exec(query,
		rules.OrganizationID,
		rules.ShiftMaxHours,
		rules.ShiftMinHours,
		rules.MaxWeeklyHours,
		rules.MinWeeklyHours,
		rules.FixedShifts,
		rules.NumberOfShiftsPerDay,
		rules.MeetAllDemand,
		rules.MinRestSlots,
		rules.SlotLenHour,
		rules.MinShiftLengthSlots,
	)
	if err != nil {
		s.Logger.Error("failed to create rules", "error", err, "organization_id", rules.OrganizationID)
		return err
	}

	// Handle shift times if fixed_shifts is true
	if rules.FixedShifts && len(rules.ShiftTimes) > 0 {
		if err := s.setShiftTimes(rules.OrganizationID, rules.ShiftTimes); err != nil {
			s.Logger.Error("failed to set shift times", "error", err, "organization_id", rules.OrganizationID)
			return err
		}
	}

	s.Logger.Info("rules created", "organization_id", rules.OrganizationID)
	return nil
}

// GetRulesByOrganizationID retrieves rules for a specific organization
func (s *PostgresRulesStore) GetRulesByOrganizationID(orgID uuid.UUID) (*OrganizationRules, error) {
	var rules OrganizationRules

	query := `SELECT organization_id, shift_max_hours, shift_min_hours, max_weekly_hours, min_weekly_hours,
		fixed_shifts, number_of_shifts_per_day, meet_all_demand, min_rest_slots, slot_len_hour, min_shift_length_slots 
		FROM organizations_rules WHERE organization_id = $1`

	err := s.db.QueryRow(query, orgID).Scan(
		&rules.OrganizationID,
		&rules.ShiftMaxHours,
		&rules.ShiftMinHours,
		&rules.MaxWeeklyHours,
		&rules.MinWeeklyHours,
		&rules.FixedShifts,
		&rules.NumberOfShiftsPerDay,
		&rules.MeetAllDemand,
		&rules.MinRestSlots,
		&rules.SlotLenHour,
		&rules.MinShiftLengthSlots,
	)
	if err != nil {
		if errors.Is(err, sql.ErrNoRows) {
			return nil, nil // No rules found
		}
		s.Logger.Error("failed to get rules", "error", err, "organization_id", orgID)
		return nil, err
	}

	// Fetch shift times if fixed_shifts is true
	if rules.FixedShifts {
		shiftTimes, err := s.getShiftTimes(orgID)
		if err != nil {
			s.Logger.Error("failed to get shift times", "error", err, "organization_id", orgID)
			return nil, err
		}
		rules.ShiftTimes = shiftTimes
	}

	return &rules, nil
}

// UpdateRules updates an existing rules record
func (s *PostgresRulesStore) UpdateRules(rules *OrganizationRules) error {
	query := `UPDATE organizations_rules SET 
		shift_max_hours = $2, 
		shift_min_hours = $3, 
		max_weekly_hours = $4, 
		min_weekly_hours = $5,
		fixed_shifts = $6,
		number_of_shifts_per_day = $7,
		meet_all_demand = $8,
		min_rest_slots = $9,
		slot_len_hour = $10,
		min_shift_length_slots = $11 
		WHERE organization_id = $1`

	result, err := s.db.Exec(query,
		rules.OrganizationID,
		rules.ShiftMaxHours,
		rules.ShiftMinHours,
		rules.MaxWeeklyHours,
		rules.MinWeeklyHours,
		rules.FixedShifts,
		rules.NumberOfShiftsPerDay,
		rules.MeetAllDemand,
		rules.MinRestSlots,
		rules.SlotLenHour,
		rules.MinShiftLengthSlots,
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
		(organization_id, shift_max_hours, shift_min_hours, max_weekly_hours, min_weekly_hours,
		 fixed_shifts, number_of_shifts_per_day, meet_all_demand, min_rest_slots, slot_len_hour, min_shift_length_slots) 
		VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
		ON CONFLICT (organization_id) DO UPDATE SET 
		shift_max_hours = EXCLUDED.shift_max_hours,
		shift_min_hours = EXCLUDED.shift_min_hours,
		max_weekly_hours = EXCLUDED.max_weekly_hours,
		min_weekly_hours = EXCLUDED.min_weekly_hours,
		fixed_shifts = EXCLUDED.fixed_shifts,
		number_of_shifts_per_day = EXCLUDED.number_of_shifts_per_day,
		meet_all_demand = EXCLUDED.meet_all_demand,
		min_rest_slots = EXCLUDED.min_rest_slots,
		slot_len_hour = EXCLUDED.slot_len_hour,
		min_shift_length_slots = EXCLUDED.min_shift_length_slots`

	_, err := s.db.Exec(query,
		rules.OrganizationID,
		rules.ShiftMaxHours,
		rules.ShiftMinHours,
		rules.MaxWeeklyHours,
		rules.MinWeeklyHours,
		rules.FixedShifts,
		rules.NumberOfShiftsPerDay,
		rules.MeetAllDemand,
		rules.MinRestSlots,
		rules.SlotLenHour,
		rules.MinShiftLengthSlots,
	)
	if err != nil {
		s.Logger.Error("failed to upsert rules", "error", err, "organization_id", rules.OrganizationID)
		return err
	}

	// Handle shift times: save if fixed_shifts is true, delete otherwise
	if rules.FixedShifts {
		if err := s.setShiftTimes(rules.OrganizationID, rules.ShiftTimes); err != nil {
			s.Logger.Error("failed to set shift times", "error", err, "organization_id", rules.OrganizationID)
			return err
		}
	} else {
		if err := s.deleteShiftTimes(rules.OrganizationID); err != nil {
			s.Logger.Error("failed to delete shift times", "error", err, "organization_id", rules.OrganizationID)
			return err
		}
	}

	s.Logger.Info("rules upserted", "organization_id", rules.OrganizationID)
	return nil
}

// getShiftTimes retrieves shift times for an organization
func (s *PostgresRulesStore) getShiftTimes(orgID uuid.UUID) ([]ShiftTime, error) {
	query := `SELECT start_time, end_time FROM organization_shift_times WHERE organization_id = $1 ORDER BY start_time`

	rows, err := s.db.Query(query, orgID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var shiftTimes []ShiftTime
	for rows.Next() {
		var st ShiftTime
		if err := rows.Scan(&st.StartTime, &st.EndTime); err != nil {
			return nil, err
		}
		shiftTimes = append(shiftTimes, st)
	}

	return shiftTimes, rows.Err()
}

// setShiftTimes replaces all shift times for an organization
func (s *PostgresRulesStore) setShiftTimes(orgID uuid.UUID, shiftTimes []ShiftTime) error {
	// Delete existing shift times
	if err := s.deleteShiftTimes(orgID); err != nil {
		return err
	}

	// Insert new shift times
	if len(shiftTimes) == 0 {
		return nil
	}

	query := `INSERT INTO organization_shift_times (organization_id, start_time, end_time) VALUES ($1, $2, $3)`
	for _, st := range shiftTimes {
		_, err := s.db.Exec(query, orgID, st.StartTime, st.EndTime)
		if err != nil {
			return err
		}
	}

	return nil
}

// deleteShiftTimes removes all shift times for an organization
func (s *PostgresRulesStore) deleteShiftTimes(orgID uuid.UUID) error {
	query := `DELETE FROM organization_shift_times WHERE organization_id = $1`
	_, err := s.db.Exec(query, orgID)
	return err
}
