package database

import (
	"database/sql"
	"log/slog"
	"os"
	"testing"

	"github.com/DATA-DOG/go-sqlmock"
	"github.com/stretchr/testify/assert"
)

// NewTestDB returns a mock database connection and the mock controller.
// It ensures expectations are met when the test finishes.
func NewTestDB(t *testing.T) (*sql.DB, sqlmock.Sqlmock) {
	db, mock, err := sqlmock.New()
	if err != nil {
		t.Fatalf("an error '%s' was not expected when opening a stub database connection", err)
	}

	t.Cleanup(func() {
		db.Close()
	})

	return db, mock
}

// NewTestLogger returns a logger for tests.
func NewTestLogger() *slog.Logger {
	return slog.New(slog.NewTextHandler(os.Stdout, nil))
}

// AssertExpectations ensures all database expectations were met.
func AssertExpectations(t *testing.T, mock sqlmock.Sqlmock) {
	if err := mock.ExpectationsWereMet(); err != nil {
		t.Errorf("there were unfulfilled expectations: %s", err)
	}
}

// NewRow is a helper to create a single row result for scalar values.
func NewRow(val interface{}) *sqlmock.Rows {
	return sqlmock.NewRows([]string{"value"}).AddRow(val)
}

// CheckError is a helper to assert no error occurred.
func CheckError(t *testing.T, err error) {
	assert.NoError(t, err)
}
