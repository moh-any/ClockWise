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

func TestGetOperatingHours(t *testing.T) {
	db, mock := NewTestDB(t)
	logger := NewTestLogger()
	store := database.NewPostgresOperatingHoursStore(db, logger)

	orgID := uuid.New()

	query := regexp.QuoteMeta(`SELECT organization_id, weekday, opening_time, closing_time FROM organizations_operating_hours WHERE organization_id = $1 ORDER BY CASE weekday WHEN 'sunday' THEN 0 WHEN 'monday' THEN 1 WHEN 'tuesday' THEN 2 WHEN 'wednesday' THEN 3 WHEN 'thursday' THEN 4 WHEN 'friday' THEN 5 WHEN 'saturday' THEN 6 END`)

	t.Run("Success", func(t *testing.T) {
		rows := sqlmock.NewRows([]string{"organization_id", "weekday", "opening_time", "closing_time"}).
			AddRow(orgID, "monday", "09:00:00", "17:00:00").
			AddRow(orgID, "tuesday", "09:00:00", "17:00:00")

		mock.ExpectQuery(query).WithArgs(orgID).WillReturnRows(rows)

		hours, err := store.GetOperatingHours(orgID)

		assert.NoError(t, err)
		// Store returns all 7 days (filling in closed=true for missing ones)
		assert.Len(t, hours, 7)
		// Monday and Tuesday should have times, others should be closed
		assert.Equal(t, "monday", hours[1].Weekday)
		assert.Equal(t, "09:00:00", hours[1].OpeningTime)
		assert.Equal(t, "tuesday", hours[2].Weekday)
		assert.Equal(t, "09:00:00", hours[2].OpeningTime)
		// Sunday (index 0) should be closed
		assert.Equal(t, "sunday", hours[0].Weekday)
		assert.NotNil(t, hours[0].Closed)
		assert.True(t, *hours[0].Closed)
		AssertExpectations(t, mock)
	})

	t.Run("DBError", func(t *testing.T) {
		mock.ExpectQuery(query).WithArgs(orgID).WillReturnError(fmt.Errorf("db error"))

		hours, err := store.GetOperatingHours(orgID)

		assert.Error(t, err)
		assert.Nil(t, hours)
		AssertExpectations(t, mock)
	})
}

func TestGetOperatingHoursByDay(t *testing.T) {
	db, mock := NewTestDB(t)
	logger := NewTestLogger()
	store := database.NewPostgresOperatingHoursStore(db, logger)

	orgID := uuid.New()
	weekday := "Wednesday"

	query := regexp.QuoteMeta(`SELECT organization_id, weekday, opening_time, closing_time FROM organizations_operating_hours WHERE organization_id = $1 AND weekday = $2`)

	t.Run("Success", func(t *testing.T) {
		rows := sqlmock.NewRows([]string{"organization_id", "weekday", "opening_time", "closing_time"}).
			AddRow(orgID, weekday, "10:00:00", "18:00:00")

		mock.ExpectQuery(query).WithArgs(orgID, weekday).WillReturnRows(rows)

		hours, err := store.GetOperatingHoursByDay(orgID, weekday)

		assert.NoError(t, err)
		assert.NotNil(t, hours)
		assert.Equal(t, weekday, hours.Weekday)
		AssertExpectations(t, mock)
	})

	t.Run("NotFound", func(t *testing.T) {
		mock.ExpectQuery(query).WithArgs(orgID, weekday).WillReturnError(sql.ErrNoRows)

		hours, err := store.GetOperatingHoursByDay(orgID, weekday)

		assert.NoError(t, err)
		// Store returns a non-nil OperatingHours with Closed=true when not found
		assert.NotNil(t, hours)
		assert.Equal(t, weekday, hours.Weekday)
		assert.NotNil(t, hours.Closed)
		assert.True(t, *hours.Closed)
		AssertExpectations(t, mock)
	})
}

func TestSetOperatingHours(t *testing.T) {
	db, mock := NewTestDB(t)
	logger := NewTestLogger()
	store := database.NewPostgresOperatingHoursStore(db, logger)

	orgID := uuid.New()
	hours := []database.OperatingHours{
		{OrganizationID: orgID, Weekday: "Monday", OpeningTime: "09:00", ClosingTime: "17:00"},
		{OrganizationID: orgID, Weekday: "Tuesday", OpeningTime: "09:00", ClosingTime: "17:00"},
	}

	deleteQuery := regexp.QuoteMeta(`DELETE FROM organizations_operating_hours WHERE organization_id = $1`)
	insertQuery := regexp.QuoteMeta(`INSERT INTO organizations_operating_hours (organization_id, weekday, opening_time, closing_time) VALUES ($1, $2, $3, $4)`)

	t.Run("Success", func(t *testing.T) {
		mock.ExpectBegin()

		// Expect deletion of old hours
		mock.ExpectExec(deleteQuery).WithArgs(orgID).WillReturnResult(sqlmock.NewResult(0, 5))

		// Expect insertion of new hours
		for _, h := range hours {
			mock.ExpectExec(insertQuery).
				WithArgs(orgID, h.Weekday, h.OpeningTime, h.ClosingTime).
				WillReturnResult(sqlmock.NewResult(1, 1))
		}

		mock.ExpectCommit()

		err := store.SetOperatingHours(orgID, hours)

		assert.NoError(t, err)
		AssertExpectations(t, mock)
	})

	t.Run("TransactionRollbackOnError", func(t *testing.T) {
		mock.ExpectBegin()
		mock.ExpectExec(deleteQuery).WithArgs(orgID).WillReturnError(fmt.Errorf("delete failed"))
		mock.ExpectRollback()

		err := store.SetOperatingHours(orgID, hours)

		assert.Error(t, err)
		AssertExpectations(t, mock)
	})
}

func TestUpsertOperatingHours(t *testing.T) {
	db, mock := NewTestDB(t)
	logger := NewTestLogger()
	store := database.NewPostgresOperatingHoursStore(db, logger)

	hours := &database.OperatingHours{
		OrganizationID: uuid.New(),
		Weekday:        "Friday",
		OpeningTime:    "08:00",
		ClosingTime:    "20:00",
	}

	query := regexp.QuoteMeta(`INSERT INTO organizations_operating_hours (organization_id, weekday, opening_time, closing_time) VALUES ($1, $2, $3, $4) ON CONFLICT (organization_id, weekday) DO UPDATE SET opening_time = EXCLUDED.opening_time, closing_time = EXCLUDED.closing_time`)

	t.Run("Success", func(t *testing.T) {
		mock.ExpectExec(query).
			WithArgs(hours.OrganizationID, hours.Weekday, hours.OpeningTime, hours.ClosingTime).
			WillReturnResult(sqlmock.NewResult(1, 1))

		err := store.UpsertOperatingHours(hours)

		assert.NoError(t, err)
		AssertExpectations(t, mock)
	})

	t.Run("DBError", func(t *testing.T) {
		mock.ExpectExec(query).
			WithArgs(hours.OrganizationID, hours.Weekday, hours.OpeningTime, hours.ClosingTime).
			WillReturnError(fmt.Errorf("upsert failed"))

		err := store.UpsertOperatingHours(hours)

		assert.Error(t, err)
		AssertExpectations(t, mock)
	})
}

func TestDeleteOperatingHoursByDay(t *testing.T) {
	db, mock := NewTestDB(t)
	logger := NewTestLogger()
	store := database.NewPostgresOperatingHoursStore(db, logger)

	orgID := uuid.New()
	weekday := "Sunday"

	query := regexp.QuoteMeta(`DELETE FROM organizations_operating_hours WHERE organization_id = $1 AND weekday = $2`)

	t.Run("Success", func(t *testing.T) {
		mock.ExpectExec(query).WithArgs(orgID, weekday).WillReturnResult(sqlmock.NewResult(0, 1))

		err := store.DeleteOperatingHoursByDay(orgID, weekday)

		assert.NoError(t, err)
		AssertExpectations(t, mock)
	})

	t.Run("NotFound", func(t *testing.T) {
		mock.ExpectExec(query).WithArgs(orgID, weekday).WillReturnResult(sqlmock.NewResult(0, 0))

		err := store.DeleteOperatingHoursByDay(orgID, weekday)

		assert.Error(t, err)
		assert.Equal(t, "no operating hours found to delete", err.Error())
		AssertExpectations(t, mock)
	})
}

func TestDeleteAllOperatingHours(t *testing.T) {
	db, mock := NewTestDB(t)
	logger := NewTestLogger()
	store := database.NewPostgresOperatingHoursStore(db, logger)

	orgID := uuid.New()

	query := regexp.QuoteMeta(`DELETE FROM organizations_operating_hours WHERE organization_id = $1`)

	t.Run("Success", func(t *testing.T) {
		mock.ExpectExec(query).WithArgs(orgID).WillReturnResult(sqlmock.NewResult(0, 7))

		err := store.DeleteAllOperatingHours(orgID)

		assert.NoError(t, err)
		AssertExpectations(t, mock)
	})

	t.Run("DBError", func(t *testing.T) {
		mock.ExpectExec(query).WithArgs(orgID).WillReturnError(fmt.Errorf("delete failed"))

		err := store.DeleteAllOperatingHours(orgID)

		assert.Error(t, err)
		AssertExpectations(t, mock)
	})
}
