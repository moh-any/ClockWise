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

	query := regexp.QuoteMeta(`SELECT organization_id, weekday, opening_time, closing_time FROM organizations_operating_hours WHERE organization_id = $1 ORDER BY CASE weekday WHEN 'Sunday' THEN 0 WHEN 'Monday' THEN 1 WHEN 'Tuesday' THEN 2 WHEN 'Wednesday' THEN 3 WHEN 'Thursday' THEN 4 WHEN 'Friday' THEN 5 WHEN 'Saturday' THEN 6 END`)

	t.Run("Success", func(t *testing.T) {
		rows := sqlmock.NewRows([]string{"organization_id", "weekday", "opening_time", "closing_time"}).
			AddRow(orgID, "Monday", "09:00:00", "17:00:00").
			AddRow(orgID, "Tuesday", "09:00:00", "17:00:00")

		mock.ExpectQuery(query).WithArgs(orgID).WillReturnRows(rows)

		hours, err := store.GetOperatingHours(orgID)

		assert.NoError(t, err)
		assert.Len(t, hours, 2)
		assert.Equal(t, "Monday", hours[0].Weekday)
		assert.Equal(t, "Tuesday", hours[1].Weekday)
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

		assert.NoError(t, err) // Expect nil, nil on ErrNoRows
		assert.Nil(t, hours)
		AssertExpectations(t, mock)
	})
}

func TestSetOperatingHours(t *testing.T) {
	db, mock := NewTestDB(t)
	logger := NewTestLogger()
	store := database.NewPostgresOperatingHoursStore(db, logger)

	orgID := uuid.New()
	hours := []*database.OperatingHours{
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
