package database

import (
	"fmt"
	"regexp"
	"testing"

	"github.com/DATA-DOG/go-sqlmock"
	"github.com/clockwise/clockwise/backend/internal/database"
	"github.com/google/uuid"
	"github.com/stretchr/testify/assert"
)

func TestGetUserRoles(t *testing.T) {
	db, mock := NewTestDB(t)
	logger := NewTestLogger()
	store := database.NewPostgresUserRolesStore(db, logger)

	userID := uuid.New()
	orgID := uuid.New()
	query := regexp.QuoteMeta(`SELECT user_role FROM user_roles WHERE user_id = $1 AND organization_id = $2 ORDER BY user_role`)

	t.Run("Success", func(t *testing.T) {
		rows := sqlmock.NewRows([]string{"user_role"}).AddRow("Chef").AddRow("Manager")
		mock.ExpectQuery(query).WithArgs(userID, orgID).WillReturnRows(rows)

		roles, err := store.GetUserRoles(userID, orgID)
		assert.NoError(t, err)
		assert.Len(t, roles, 2)
		assert.Equal(t, "Chef", roles[0])
		AssertExpectations(t, mock)
	})
}

func TestSetUserRoles(t *testing.T) {
	db, mock := NewTestDB(t)
	logger := NewTestLogger()
	store := database.NewPostgresUserRolesStore(db, logger)

	userID := uuid.New()
	orgID := uuid.New()
	roles := []string{"Server", "Cashier"}

	deleteQuery := regexp.QuoteMeta(`DELETE FROM user_roles WHERE user_id = $1 AND organization_id = $2`)
	insertQuery := regexp.QuoteMeta(`INSERT INTO user_roles (user_id, organization_id, user_role) VALUES ($1, $2, $3)`)

	t.Run("Success", func(t *testing.T) {
		mock.ExpectBegin()
		mock.ExpectExec(deleteQuery).WithArgs(userID, orgID).WillReturnResult(sqlmock.NewResult(0, 5)) // Deleted old
		for _, role := range roles {
			mock.ExpectExec(insertQuery).WithArgs(userID, orgID, role).WillReturnResult(sqlmock.NewResult(1, 1))
		}
		mock.ExpectCommit()

		err := store.SetUserRoles(userID, orgID, roles)
		assert.NoError(t, err)
		AssertExpectations(t, mock)
	})

	t.Run("RollbackOnError", func(t *testing.T) {
		mock.ExpectBegin()
		mock.ExpectExec(deleteQuery).WillReturnError(fmt.Errorf("delete error"))
		mock.ExpectRollback()

		err := store.SetUserRoles(userID, orgID, roles)
		assert.Error(t, err)
		AssertExpectations(t, mock)
	})
}

func TestAddUserRole(t *testing.T) {
	db, mock := NewTestDB(t)
	logger := NewTestLogger()
	store := database.NewPostgresUserRolesStore(db, logger)

	userID := uuid.New()
	orgID := uuid.New()
	role := "Driver"
	query := regexp.QuoteMeta(`INSERT INTO user_roles (user_id, organization_id, user_role) VALUES ($1, $2, $3) ON CONFLICT (user_id, organization_id, user_role) DO NOTHING`)

	t.Run("Success", func(t *testing.T) {
		mock.ExpectExec(query).WithArgs(userID, orgID, role).WillReturnResult(sqlmock.NewResult(1, 1))
		err := store.AddUserRole(userID, orgID, role)
		assert.NoError(t, err)
		AssertExpectations(t, mock)
	})
}

func TestRemoveUserRole(t *testing.T) {
	db, mock := NewTestDB(t)
	logger := NewTestLogger()
	store := database.NewPostgresUserRolesStore(db, logger)

	userID := uuid.New()
	orgID := uuid.New()
	role := "Driver"
	query := regexp.QuoteMeta(`DELETE FROM user_roles WHERE user_id = $1 AND organization_id = $2 AND user_role = $3`)

	t.Run("Success", func(t *testing.T) {
		mock.ExpectExec(query).WithArgs(userID, orgID, role).WillReturnResult(sqlmock.NewResult(0, 1))
		err := store.RemoveUserRole(userID, orgID, role)
		assert.NoError(t, err)
		AssertExpectations(t, mock)
	})
}

func TestDeleteAllUserRoles(t *testing.T) {
	db, mock := NewTestDB(t)
	logger := NewTestLogger()
	store := database.NewPostgresUserRolesStore(db, logger)

	userID := uuid.New()
	orgID := uuid.New()
	query := regexp.QuoteMeta(`DELETE FROM user_roles WHERE user_id = $1 AND organization_id = $2`)

	t.Run("Success", func(t *testing.T) {
		mock.ExpectExec(query).WithArgs(userID, orgID).WillReturnResult(sqlmock.NewResult(0, 3))
		err := store.DeleteAllUserRoles(userID, orgID)
		assert.NoError(t, err)
		AssertExpectations(t, mock)
	})
}
