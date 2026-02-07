package database

import (
	"database/sql"
	"fmt"
	"regexp"
	"testing"

	"github.com/DATA-DOG/go-sqlmock"
	"github.com/clockwise/clockwise/backend/internal/database"
	"github.com/google/uuid"
	"github.com/stretchr/testify/assert"
)

func TestCreateRules(t *testing.T) {
	db, mock := NewTestDB(t)
	logger := NewTestLogger()
	store := database.NewPostgresRulesStore(db, logger)

	rules := &database.OrganizationRules{
		OrganizationID:       uuid.New(),
		ShiftMaxHours:        8,
		ShiftMinHours:        4,
		MaxWeeklyHours:       40,
		MinWeeklyHours:       20,
		FixedShifts:          true,
		NumberOfShiftsPerDay: func() *int { i := 3; return &i }(),
		MeetAllDemand:        true,
		MinRestSlots:         2,
		SlotLenHour:          1.0,
		MinShiftLengthSlots:  4,
		// ShiftTimes is empty, so CreateRules won't execute extra queries
	}

	query := regexp.QuoteMeta(`INSERT INTO organizations_rules (organization_id, shift_max_hours, shift_min_hours, max_weekly_hours, min_weekly_hours, fixed_shifts, number_of_shifts_per_day, meet_all_demand, min_rest_slots, slot_len_hour, min_shift_length_slots) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)`)

	t.Run("Success", func(t *testing.T) {
		mock.ExpectExec(query).
			WithArgs(rules.OrganizationID, rules.ShiftMaxHours, rules.ShiftMinHours, rules.MaxWeeklyHours, rules.MinWeeklyHours, rules.FixedShifts, rules.NumberOfShiftsPerDay, rules.MeetAllDemand, rules.MinRestSlots, rules.SlotLenHour, rules.MinShiftLengthSlots).
			WillReturnResult(sqlmock.NewResult(1, 1))

		err := store.CreateRules(rules)
		assert.NoError(t, err)
		AssertExpectations(t, mock)
	})

	t.Run("DBError", func(t *testing.T) {
		mock.ExpectExec(query).WillReturnError(fmt.Errorf("db error"))
		err := store.CreateRules(rules)
		assert.Error(t, err)
		AssertExpectations(t, mock)
	})
}

func TestGetRulesByOrganizationID(t *testing.T) {
	db, mock := NewTestDB(t)
	logger := NewTestLogger()
	store := database.NewPostgresRulesStore(db, logger)

	orgID := uuid.New()

	// Queries
	qRules := regexp.QuoteMeta(`SELECT organization_id, shift_max_hours, shift_min_hours, max_weekly_hours, min_weekly_hours, fixed_shifts, number_of_shifts_per_day, meet_all_demand, min_rest_slots, slot_len_hour, min_shift_length_slots FROM organizations_rules WHERE organization_id = $1`)
	qShiftTimes := regexp.QuoteMeta(`SELECT start_time, end_time FROM organization_shift_times WHERE organization_id = $1 ORDER BY start_time`)

	t.Run("Success", func(t *testing.T) {
		// Mock Rules Query (FixedShifts = true)
		rows := sqlmock.NewRows([]string{"organization_id", "shift_max_hours", "shift_min_hours", "max_weekly_hours", "min_weekly_hours", "fixed_shifts", "number_of_shifts_per_day", "meet_all_demand", "min_rest_slots", "slot_len_hour", "min_shift_length_slots"}).
			AddRow(orgID, 8, 4, 40, 20, true, 3, true, 2, 1.0, 4)
		mock.ExpectQuery(qRules).WithArgs(orgID).WillReturnRows(rows)

		// Mock Shift Times Query (Required because FixedShifts is true)
		shiftRows := sqlmock.NewRows([]string{"start_time", "end_time"})
		mock.ExpectQuery(qShiftTimes).WithArgs(orgID).WillReturnRows(shiftRows)

		rules, err := store.GetRulesByOrganizationID(orgID)
		assert.NoError(t, err)
		assert.Equal(t, orgID, rules.OrganizationID)
		assert.Equal(t, 8, rules.ShiftMaxHours)
		assert.True(t, rules.FixedShifts)
		AssertExpectations(t, mock)
	})

	t.Run("NotFound", func(t *testing.T) {
		mock.ExpectQuery(qRules).WithArgs(orgID).WillReturnError(sql.ErrNoRows)
		rules, err := store.GetRulesByOrganizationID(orgID)
		assert.NoError(t, err)
		assert.Nil(t, rules)
		AssertExpectations(t, mock)
	})
}

func TestUpdateRules(t *testing.T) {
	db, mock := NewTestDB(t)
	logger := NewTestLogger()
	store := database.NewPostgresRulesStore(db, logger)

	rules := &database.OrganizationRules{
		OrganizationID:       uuid.New(),
		ShiftMaxHours:        10,
		ShiftMinHours:        5,
		MaxWeeklyHours:       50,
		MinWeeklyHours:       25,
		FixedShifts:          false,
		NumberOfShiftsPerDay: nil,
		MeetAllDemand:        false,
		MinRestSlots:         1,
		SlotLenHour:          0.5,
		MinShiftLengthSlots:  8,
	}

	query := regexp.QuoteMeta(`UPDATE organizations_rules SET shift_max_hours = $2, shift_min_hours = $3, max_weekly_hours = $4, min_weekly_hours = $5, fixed_shifts = $6, number_of_shifts_per_day = $7, meet_all_demand = $8, min_rest_slots = $9, slot_len_hour = $10, min_shift_length_slots = $11 WHERE organization_id = $1`)

	t.Run("Success", func(t *testing.T) {
		mock.ExpectExec(query).
			WithArgs(rules.OrganizationID, rules.ShiftMaxHours, rules.ShiftMinHours, rules.MaxWeeklyHours, rules.MinWeeklyHours, rules.FixedShifts, rules.NumberOfShiftsPerDay, rules.MeetAllDemand, rules.MinRestSlots, rules.SlotLenHour, rules.MinShiftLengthSlots).
			WillReturnResult(sqlmock.NewResult(0, 1))

		err := store.UpdateRules(rules)
		assert.NoError(t, err)
		AssertExpectations(t, mock)
	})

	t.Run("NotFound", func(t *testing.T) {
		mock.ExpectExec(query).WillReturnResult(sqlmock.NewResult(0, 0))
		err := store.UpdateRules(rules)
		assert.Error(t, err)
		assert.Equal(t, "no rules found to update", err.Error())
		AssertExpectations(t, mock)
	})
}

func TestUpsertRules(t *testing.T) {
	db, mock := NewTestDB(t)
	logger := NewTestLogger()
	store := database.NewPostgresRulesStore(db, logger)

	rules := &database.OrganizationRules{
		OrganizationID:       uuid.New(),
		ShiftMaxHours:        12,
		ShiftMinHours:        6,
		MaxWeeklyHours:       60,
		MinWeeklyHours:       30,
		FixedShifts:          true,
		NumberOfShiftsPerDay: func() *int { i := 2; return &i }(),
		MeetAllDemand:        true,
		MinRestSlots:         3,
		SlotLenHour:          1.0,
		MinShiftLengthSlots:  6,
		// Empty ShiftTimes
	}

	queryUpsert := regexp.QuoteMeta(`INSERT INTO organizations_rules (organization_id, shift_max_hours, shift_min_hours, max_weekly_hours, min_weekly_hours, fixed_shifts, number_of_shifts_per_day, meet_all_demand, min_rest_slots, slot_len_hour, min_shift_length_slots) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11) ON CONFLICT (organization_id) DO UPDATE SET shift_max_hours = EXCLUDED.shift_max_hours, shift_min_hours = EXCLUDED.shift_min_hours, max_weekly_hours = EXCLUDED.max_weekly_hours, min_weekly_hours = EXCLUDED.min_weekly_hours, fixed_shifts = EXCLUDED.fixed_shifts, number_of_shifts_per_day = EXCLUDED.number_of_shifts_per_day, meet_all_demand = EXCLUDED.meet_all_demand, min_rest_slots = EXCLUDED.min_rest_slots, slot_len_hour = EXCLUDED.slot_len_hour, min_shift_length_slots = EXCLUDED.min_shift_length_slots`)

	// Since FixedShifts is true, setShiftTimes calls deleteShiftTimes
	queryDeleteShiftTimes := regexp.QuoteMeta(`DELETE FROM organization_shift_times WHERE organization_id = $1`)

	t.Run("Success", func(t *testing.T) {
		// 1. Upsert Rules
		mock.ExpectExec(queryUpsert).
			WithArgs(rules.OrganizationID, rules.ShiftMaxHours, rules.ShiftMinHours, rules.MaxWeeklyHours, rules.MinWeeklyHours, rules.FixedShifts, rules.NumberOfShiftsPerDay, rules.MeetAllDemand, rules.MinRestSlots, rules.SlotLenHour, rules.MinShiftLengthSlots).
			WillReturnResult(sqlmock.NewResult(1, 1))

		// 2. Delete existing shift times (triggered by setShiftTimes)
		mock.ExpectExec(queryDeleteShiftTimes).
			WithArgs(rules.OrganizationID).
			WillReturnResult(sqlmock.NewResult(0, 0))

		err := store.UpsertRules(rules)
		assert.NoError(t, err)
		AssertExpectations(t, mock)
	})

	t.Run("DBError", func(t *testing.T) {
		mock.ExpectExec(queryUpsert).WillReturnError(fmt.Errorf("db error"))
		err := store.UpsertRules(rules)
		assert.Error(t, err)
		AssertExpectations(t, mock)
	})
}
