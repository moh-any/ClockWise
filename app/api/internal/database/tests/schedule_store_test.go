package database

import (
	"database/sql"
	"fmt"
	"regexp"
	"testing"
	"time"

	"github.com/DATA-DOG/go-sqlmock"
	"github.com/clockwise/clockwise/backend/internal/database"
	"github.com/google/uuid"
	"github.com/stretchr/testify/assert"
)

func TestStoreScheduleForUser(t *testing.T) {
	db, mock := NewTestDB(t)
	logger := NewTestLogger()
	store := database.NewPostgresScheduleStore(db, logger)

	orgID := uuid.New()
	userID := uuid.New()
	scheduleDate := time.Date(2024, 6, 17, 0, 0, 0, 0, time.UTC)
	startTime := time.Date(0, 1, 1, 9, 0, 0, 0, time.UTC)
	endTime := time.Date(0, 1, 1, 17, 0, 0, 0, time.UTC)

	schedule := &database.Schedule{
		Date:      scheduleDate,
		Day:       "Monday",
		StartTime: startTime,
		EndTime:   endTime,
	}

	checkQuery := regexp.QuoteMeta(`SELECT EXISTS(SELECT 1 FROM users WHERE id = $1 AND organization_id = $2)`)
	insertQuery := regexp.QuoteMeta(`INSERT INTO schedules (schedule_date, day, start_hour, end_hour, employee_id) VALUES ($1, $2, $3, $4, $5) ON CONFLICT (schedule_date, start_hour, end_hour, employee_id) DO NOTHING`)

	t.Run("Success", func(t *testing.T) {
		mock.ExpectQuery(checkQuery).WithArgs(userID, orgID).WillReturnRows(NewRow(true))
		mock.ExpectExec(insertQuery).
			WithArgs(schedule.Date, schedule.Day, schedule.StartTime, schedule.EndTime, userID).
			WillReturnResult(sqlmock.NewResult(1, 1))

		err := store.StoreScheduleForUser(orgID, userID, schedule)
		assert.NoError(t, err)
		AssertExpectations(t, mock)
	})

	t.Run("UserNotInOrganization", func(t *testing.T) {
		mock.ExpectQuery(checkQuery).WithArgs(userID, orgID).WillReturnRows(NewRow(false))

		err := store.StoreScheduleForUser(orgID, userID, schedule)
		assert.Error(t, err)
		assert.Equal(t, sql.ErrNoRows, err)
		AssertExpectations(t, mock)
	})

	t.Run("VerifyError", func(t *testing.T) {
		mock.ExpectQuery(checkQuery).WithArgs(userID, orgID).WillReturnError(fmt.Errorf("db error"))

		err := store.StoreScheduleForUser(orgID, userID, schedule)
		assert.Error(t, err)
		AssertExpectations(t, mock)
	})

	t.Run("InsertError", func(t *testing.T) {
		mock.ExpectQuery(checkQuery).WithArgs(userID, orgID).WillReturnRows(NewRow(true))
		mock.ExpectExec(insertQuery).WillReturnError(fmt.Errorf("insert failed"))

		err := store.StoreScheduleForUser(orgID, userID, schedule)
		assert.Error(t, err)
		AssertExpectations(t, mock)
	})
}

// Note: GetFullScheduleForSevenDays uses PostgreSQL ARRAY_AGG which requires pgx array scanning.
// This cannot be fully tested with go-sqlmock as it uses database/sql which doesn't support
// scanning PostgreSQL arrays into Go slices. This method should be covered by integration tests.

func TestGetScheduleForEmployeeForSevenDays(t *testing.T) {
	db, mock := NewTestDB(t)
	logger := NewTestLogger()
	store := database.NewPostgresScheduleStore(db, logger)

	orgID := uuid.New()
	userID := uuid.New()
	scheduleDate := time.Date(2024, 6, 17, 0, 0, 0, 0, time.UTC)
	startTime := time.Date(0, 1, 1, 9, 0, 0, 0, time.UTC)
	endTime := time.Date(0, 1, 1, 17, 0, 0, 0, time.UTC)

	checkQuery := regexp.QuoteMeta(`SELECT EXISTS(SELECT 1 FROM users WHERE id = $1 AND organization_id = $2)`)
	scheduleQuery := regexp.QuoteMeta(`SELECT schedule_date, day, start_hour, end_hour, employee_id FROM schedules WHERE employee_id = $1 AND schedule_date >= CURRENT_DATE AND schedule_date < CURRENT_DATE + INTERVAL '7 days' ORDER BY schedule_date, start_hour`)

	t.Run("Success", func(t *testing.T) {
		mock.ExpectQuery(checkQuery).WithArgs(userID, orgID).WillReturnRows(NewRow(true))

		rows := sqlmock.NewRows([]string{"schedule_date", "day", "start_hour", "end_hour", "employee_id"}).
			AddRow(scheduleDate, "Monday", startTime, endTime, userID).
			AddRow(scheduleDate.Add(24*time.Hour), "Tuesday", startTime, endTime, userID)

		mock.ExpectQuery(scheduleQuery).WithArgs(userID).WillReturnRows(rows)

		schedules, err := store.GetScheduleForEmployeeForSevenDays(orgID, userID)
		assert.NoError(t, err)
		assert.Len(t, schedules, 2)
		assert.Equal(t, "Monday", schedules[0].Day)
		assert.Equal(t, []string{userID.String()}, schedules[0].Employees)
		assert.Equal(t, "Tuesday", schedules[1].Day)
		AssertExpectations(t, mock)
	})

	t.Run("UserNotInOrganization", func(t *testing.T) {
		mock.ExpectQuery(checkQuery).WithArgs(userID, orgID).WillReturnRows(NewRow(false))

		schedules, err := store.GetScheduleForEmployeeForSevenDays(orgID, userID)
		assert.Error(t, err)
		assert.Equal(t, sql.ErrNoRows, err)
		assert.Nil(t, schedules)
		AssertExpectations(t, mock)
	})

	t.Run("EmptyResult", func(t *testing.T) {
		mock.ExpectQuery(checkQuery).WithArgs(userID, orgID).WillReturnRows(NewRow(true))

		rows := sqlmock.NewRows([]string{"schedule_date", "day", "start_hour", "end_hour", "employee_id"})
		mock.ExpectQuery(scheduleQuery).WithArgs(userID).WillReturnRows(rows)

		schedules, err := store.GetScheduleForEmployeeForSevenDays(orgID, userID)
		assert.NoError(t, err)
		assert.Nil(t, schedules)
		AssertExpectations(t, mock)
	})

	t.Run("DBError", func(t *testing.T) {
		mock.ExpectQuery(checkQuery).WithArgs(userID, orgID).WillReturnRows(NewRow(true))
		mock.ExpectQuery(scheduleQuery).WithArgs(userID).WillReturnError(fmt.Errorf("db error"))

		schedules, err := store.GetScheduleForEmployeeForSevenDays(orgID, userID)
		assert.Error(t, err)
		assert.Nil(t, schedules)
		AssertExpectations(t, mock)
	})
}
