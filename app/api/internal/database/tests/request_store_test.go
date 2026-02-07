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

func TestCreateRequest(t *testing.T) {
	db, mock := NewTestDB(t)
	logger := NewTestLogger()
	store := database.NewPostgresRequestStore(db, logger)

	req := &database.Request{
		ID:         uuid.New(),
		EmployeeID: uuid.New(),
		Type:       "TimeOff",
		Message:    "Vacation",
		Status:     "Pending",
	}

	query := regexp.QuoteMeta(`INSERT INTO requests (request_id, employee_id, type, message, submitted_at, updated_at, status) VALUES ($1, $2, $3, $4, $5, $6, $7)`)

	t.Run("Success", func(t *testing.T) {
		mock.ExpectExec(query).
			WithArgs(req.ID, req.EmployeeID, req.Type, req.Message, sqlmock.AnyArg(), sqlmock.AnyArg(), req.Status).
			WillReturnResult(sqlmock.NewResult(1, 1))

		err := store.CreateRequest(req)
		assert.NoError(t, err)
		AssertExpectations(t, mock)
	})

	t.Run("DBError", func(t *testing.T) {
		mock.ExpectExec(query).WillReturnError(fmt.Errorf("db error"))
		err := store.CreateRequest(req)
		assert.Error(t, err)
		AssertExpectations(t, mock)
	})
}

func TestGetRequestByID(t *testing.T) {
	db, mock := NewTestDB(t)
	logger := NewTestLogger()
	store := database.NewPostgresRequestStore(db, logger)

	reqID := uuid.New()
	query := regexp.QuoteMeta(`SELECT request_id, employee_id, type, message, submitted_at, updated_at, status FROM requests WHERE request_id=$1`)

	t.Run("Success", func(t *testing.T) {
		rows := sqlmock.NewRows([]string{"request_id", "employee_id", "type", "message", "submitted_at", "updated_at", "status"}).
			AddRow(reqID, uuid.New(), "TimeOff", "Sick", time.Now(), time.Now(), "Pending")

		mock.ExpectQuery(query).WithArgs(reqID).WillReturnRows(rows)

		req, err := store.GetRequestByID(reqID)
		assert.NoError(t, err)
		assert.Equal(t, reqID, req.ID)
		AssertExpectations(t, mock)
	})

	t.Run("DBError", func(t *testing.T) {
		mock.ExpectQuery(query).WithArgs(reqID).WillReturnError(fmt.Errorf("db error"))
		req, err := store.GetRequestByID(reqID)
		assert.Error(t, err)
		assert.Nil(t, req)
		AssertExpectations(t, mock)
	})
}

func TestGetRequestsByEmployee(t *testing.T) {
	db, mock := NewTestDB(t)
	logger := NewTestLogger()
	store := database.NewPostgresRequestStore(db, logger)

	empID := uuid.New()
	query := regexp.QuoteMeta(`SELECT request_id, employee_id, type, message, submitted_at, updated_at, status FROM requests WHERE employee_id=$1 ORDER BY submitted_at DESC`)

	t.Run("Success", func(t *testing.T) {
		rows := sqlmock.NewRows([]string{"request_id", "employee_id", "type", "message", "submitted_at", "updated_at", "status"}).
			AddRow(uuid.New(), empID, "TimeOff", "Sick", time.Now(), time.Now(), "Pending")

		mock.ExpectQuery(query).WithArgs(empID).WillReturnRows(rows)

		reqs, err := store.GetRequestsByEmployee(empID)
		assert.NoError(t, err)
		assert.Len(t, reqs, 1)
		AssertExpectations(t, mock)
	})
}

func TestGetRequestsByOrganization(t *testing.T) {
	db, mock := NewTestDB(t)
	logger := NewTestLogger()
	store := database.NewPostgresRequestStore(db, logger)

	orgID := uuid.New()
	query := regexp.QuoteMeta(`SELECT r.request_id, r.employee_id, r.type, r.message, r.submitted_at, r.updated_at, r.status, u.full_name, u.email FROM requests r JOIN users u ON r.employee_id = u.id WHERE u.organization_id=$1 ORDER BY r.submitted_at DESC`)

	t.Run("Success", func(t *testing.T) {
		rows := sqlmock.NewRows([]string{"request_id", "employee_id", "type", "message", "submitted_at", "updated_at", "status", "full_name", "email"}).
			AddRow(uuid.New(), uuid.New(), "TimeOff", "Sick", time.Now(), time.Now(), "Pending", "John Doe", "john@test.com")

		mock.ExpectQuery(query).WithArgs(orgID).WillReturnRows(rows)

		reqs, err := store.GetRequestsByOrganization(orgID)
		assert.NoError(t, err)
		assert.Len(t, reqs, 1)
		assert.Equal(t, "John Doe", reqs[0].EmployeeName)
		AssertExpectations(t, mock)
	})
}

func TestUpdateRequestStatus(t *testing.T) {
	db, mock := NewTestDB(t)
	logger := NewTestLogger()
	store := database.NewPostgresRequestStore(db, logger)

	reqID := uuid.New()
	status := "Approved"
	query := regexp.QuoteMeta(`UPDATE requests SET status=$1, updated_at=CURRENT_TIMESTAMP WHERE request_id=$2`)

	t.Run("Success", func(t *testing.T) {
		mock.ExpectExec(query).WithArgs(status, reqID).WillReturnResult(sqlmock.NewResult(0, 1))
		err := store.UpdateRequestStatus(reqID, status)
		assert.NoError(t, err)
		AssertExpectations(t, mock)
	})

	t.Run("NotFound", func(t *testing.T) {
		mock.ExpectExec(query).WithArgs(status, reqID).WillReturnResult(sqlmock.NewResult(0, 0))
		err := store.UpdateRequestStatus(reqID, status)
		assert.Error(t, err)
		assert.Equal(t, sql.ErrNoRows, err)
		AssertExpectations(t, mock)
	})
}
