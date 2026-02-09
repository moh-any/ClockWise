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

func TestUpsertPreference(t *testing.T) {
	db, mock := NewTestDB(t)
	logger := NewTestLogger()
	store := database.NewPostgresPreferencesStore(db, logger)

	pref := &database.EmployeePreference{
		EmployeeID:         uuid.New(),
		Day:                "monday",
		PreferredStartTime: func() *string { s := "09:00"; return &s }(),
		PreferredEndTime:   func() *string { s := "17:00"; return &s }(),
	}

	query := regexp.QuoteMeta(`INSERT INTO employees_preferences (employee_id, day, preferred_start_time, preferred_end_time, available_start_time, available_end_time) VALUES ($1, $2, $3, $4, $5, $6) ON CONFLICT (employee_id, day) DO UPDATE SET preferred_start_time = EXCLUDED.preferred_start_time, preferred_end_time = EXCLUDED.preferred_end_time, available_start_time = EXCLUDED.available_start_time, available_end_time = EXCLUDED.available_end_time`)

	t.Run("Success", func(t *testing.T) {
		mock.ExpectExec(query).
			WithArgs(pref.EmployeeID, pref.Day, pref.PreferredStartTime, pref.PreferredEndTime, pref.AvailableStartTime, pref.AvailableEndTime).
			WillReturnResult(sqlmock.NewResult(1, 1))

		err := store.UpsertPreference(pref)
		assert.NoError(t, err)
		AssertExpectations(t, mock)
	})

	t.Run("DBError", func(t *testing.T) {
		mock.ExpectExec(query).WillReturnError(fmt.Errorf("db error"))
		err := store.UpsertPreference(pref)
		assert.Error(t, err)
		AssertExpectations(t, mock)
	})
}

func TestUpsertPreferences(t *testing.T) {
	db, mock := NewTestDB(t)
	logger := NewTestLogger()
	store := database.NewPostgresPreferencesStore(db, logger)

	empID := uuid.New()
	prefs := []database.EmployeePreference{
		{Day: "monday"},
		{Day: "tuesday"},
	}

	query := regexp.QuoteMeta(`INSERT INTO employees_preferences (employee_id, day, preferred_start_time, preferred_end_time, available_start_time, available_end_time) VALUES ($1, $2, $3, $4, $5, $6) ON CONFLICT (employee_id, day) DO UPDATE SET preferred_start_time = EXCLUDED.preferred_start_time, preferred_end_time = EXCLUDED.preferred_end_time, available_start_time = EXCLUDED.available_start_time, available_end_time = EXCLUDED.available_end_time`)

	t.Run("Success", func(t *testing.T) {
		mock.ExpectBegin()
		for _, p := range prefs {
			mock.ExpectExec(query).
				WithArgs(empID, p.Day, p.PreferredStartTime, p.PreferredEndTime, p.AvailableStartTime, p.AvailableEndTime).
				WillReturnResult(sqlmock.NewResult(1, 1))
		}
		mock.ExpectCommit()

		err := store.UpsertPreferences(empID, prefs)
		assert.NoError(t, err)
		AssertExpectations(t, mock)
	})

	t.Run("TransactionRollback", func(t *testing.T) {
		mock.ExpectBegin()
		mock.ExpectExec(query).WillReturnError(fmt.Errorf("db error"))
		mock.ExpectRollback()

		err := store.UpsertPreferences(empID, prefs)
		assert.Error(t, err)
		AssertExpectations(t, mock)
	})
}

func TestGetPreferencesByEmployeeID(t *testing.T) {
	db, mock := NewTestDB(t)
	logger := NewTestLogger()
	store := database.NewPostgresPreferencesStore(db, logger)

	empID := uuid.New()
	query := regexp.QuoteMeta(`SELECT employee_id, day, preferred_start_time, preferred_end_time, available_start_time, available_end_time FROM employees_preferences WHERE employee_id = $1 ORDER BY CASE day WHEN 'sunday' THEN 0 WHEN 'monday' THEN 1 WHEN 'tuesday' THEN 2 WHEN 'wednesday' THEN 3 WHEN 'thursday' THEN 4 WHEN 'friday' THEN 5 WHEN 'saturday' THEN 6 END`)

	t.Run("Success", func(t *testing.T) {
		rows := sqlmock.NewRows([]string{"employee_id", "day", "preferred_start_time", "preferred_end_time", "available_start_time", "available_end_time"}).
			AddRow(empID, "monday", "09:00", "17:00", nil, nil).
			AddRow(empID, "tuesday", "09:00", "17:00", nil, nil)

		mock.ExpectQuery(query).WithArgs(empID).WillReturnRows(rows)

		prefs, err := store.GetPreferencesByEmployeeID(empID)
		assert.NoError(t, err)
		assert.Len(t, prefs, 2)
		assert.Equal(t, "monday", prefs[0].Day)
		AssertExpectations(t, mock)
	})
}

func TestGetPreferenceByDay(t *testing.T) {
	db, mock := NewTestDB(t)
	logger := NewTestLogger()
	store := database.NewPostgresPreferencesStore(db, logger)

	empID := uuid.New()
	day := "monday"
	query := regexp.QuoteMeta(`SELECT employee_id, day, preferred_start_time, preferred_end_time, available_start_time, available_end_time FROM employees_preferences WHERE employee_id = $1 AND day = $2`)

	t.Run("Success", func(t *testing.T) {
		rows := sqlmock.NewRows([]string{"employee_id", "day", "preferred_start_time", "preferred_end_time", "available_start_time", "available_end_time"}).
			AddRow(empID, day, "09:00", "17:00", nil, nil)

		mock.ExpectQuery(query).WithArgs(empID, day).WillReturnRows(rows)

		pref, err := store.GetPreferenceByDay(empID, day)
		assert.NoError(t, err)
		assert.Equal(t, "monday", pref.Day)
		AssertExpectations(t, mock)
	})

	t.Run("NotFound", func(t *testing.T) {
		mock.ExpectQuery(query).WithArgs(empID, day).WillReturnError(sql.ErrNoRows)
		pref, err := store.GetPreferenceByDay(empID, day)
		assert.NoError(t, err)
		assert.Nil(t, pref)
		AssertExpectations(t, mock)
	})
}

func TestDeletePreferences(t *testing.T) {
	db, mock := NewTestDB(t)
	logger := NewTestLogger()
	store := database.NewPostgresPreferencesStore(db, logger)

	empID := uuid.New()
	query := regexp.QuoteMeta(`DELETE FROM employees_preferences WHERE employee_id = $1`)

	t.Run("Success", func(t *testing.T) {
		mock.ExpectExec(query).WithArgs(empID).WillReturnResult(sqlmock.NewResult(0, 1))
		err := store.DeletePreferences(empID)
		assert.NoError(t, err)
		AssertExpectations(t, mock)
	})
}

func TestDeletePreferenceByDay(t *testing.T) {
	db, mock := NewTestDB(t)
	logger := NewTestLogger()
	store := database.NewPostgresPreferencesStore(db, logger)

	empID := uuid.New()
	day := "monday"
	query := regexp.QuoteMeta(`DELETE FROM employees_preferences WHERE employee_id = $1 AND day = $2`)

	t.Run("Success", func(t *testing.T) {
		mock.ExpectExec(query).WithArgs(empID, day).WillReturnResult(sqlmock.NewResult(0, 1))
		err := store.DeletePreferenceByDay(empID, day)
		assert.NoError(t, err)
		AssertExpectations(t, mock)
	})

	t.Run("NotFound", func(t *testing.T) {
		mock.ExpectExec(query).WithArgs(empID, day).WillReturnResult(sqlmock.NewResult(0, 0))
		err := store.DeletePreferenceByDay(empID, day)
		assert.Error(t, err)
		assert.Equal(t, "no preference found to delete", err.Error())
		AssertExpectations(t, mock)
	})
}
