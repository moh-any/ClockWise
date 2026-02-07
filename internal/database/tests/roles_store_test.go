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

func TestCreateRole(t *testing.T) {
	db, mock := NewTestDB(t)
	logger := NewTestLogger()
	store := database.NewPostgresRolesStore(db, logger)

	role := &database.OrganizationRole{
		OrganizationID:      uuid.New(),
		Role:                "Chef",
		MinNeededPerShift:   2,
		ItemsPerRolePerHour: func() *int { i := 5; return &i }(),
		NeedForDemand:       true,
		Independent:         func() *bool { b := false; return &b }(),
	}

	query := regexp.QuoteMeta(`INSERT INTO organizations_roles (organization_id, role, min_needed_per_shift, items_per_role_per_hour, need_for_demand, independent) VALUES ($1, $2, $3, $4, $5, $6)`)

	t.Run("Success", func(t *testing.T) {
		mock.ExpectExec(query).
			WithArgs(role.OrganizationID, role.Role, role.MinNeededPerShift, role.ItemsPerRolePerHour, role.NeedForDemand, role.Independent).
			WillReturnResult(sqlmock.NewResult(1, 1))

		err := store.CreateRole(role)
		assert.NoError(t, err)
		AssertExpectations(t, mock)
	})

	t.Run("DBError", func(t *testing.T) {
		mock.ExpectExec(query).WillReturnError(fmt.Errorf("db error"))
		err := store.CreateRole(role)
		assert.Error(t, err)
		AssertExpectations(t, mock)
	})
}

func TestGetRolesByOrganizationID(t *testing.T) {
	db, mock := NewTestDB(t)
	logger := NewTestLogger()
	store := database.NewPostgresRolesStore(db, logger)

	orgID := uuid.New()
	query := regexp.QuoteMeta(`SELECT organization_id, role, min_needed_per_shift, items_per_role_per_hour, need_for_demand, independent FROM organizations_roles WHERE organization_id = $1 ORDER BY role`)

	t.Run("Success", func(t *testing.T) {
		rows := sqlmock.NewRows([]string{"organization_id", "role", "min_needed_per_shift", "items_per_role_per_hour", "need_for_demand", "independent"}).
			AddRow(orgID, "Chef", 2, 5, true, false).
			AddRow(orgID, "Server", 3, 10, true, true)

		mock.ExpectQuery(query).WithArgs(orgID).WillReturnRows(rows)

		roles, err := store.GetRolesByOrganizationID(orgID)
		assert.NoError(t, err)
		assert.Len(t, roles, 2)
		AssertExpectations(t, mock)
	})
}

func TestGetRoleByName(t *testing.T) {
	db, mock := NewTestDB(t)
	logger := NewTestLogger()
	store := database.NewPostgresRolesStore(db, logger)

	orgID := uuid.New()
	roleName := "Chef"
	query := regexp.QuoteMeta(`SELECT organization_id, role, min_needed_per_shift, items_per_role_per_hour, need_for_demand, independent FROM organizations_roles WHERE organization_id = $1 AND role = $2`)

	t.Run("Success", func(t *testing.T) {
		rows := sqlmock.NewRows([]string{"organization_id", "role", "min_needed_per_shift", "items_per_role_per_hour", "need_for_demand", "independent"}).
			AddRow(orgID, roleName, 2, 5, true, false)

		mock.ExpectQuery(query).WithArgs(orgID, roleName).WillReturnRows(rows)

		role, err := store.GetRoleByName(orgID, roleName)
		assert.NoError(t, err)
		assert.Equal(t, roleName, role.Role)
		AssertExpectations(t, mock)
	})

	t.Run("NotFound", func(t *testing.T) {
		mock.ExpectQuery(query).WithArgs(orgID, roleName).WillReturnError(sql.ErrNoRows)
		role, err := store.GetRoleByName(orgID, roleName)
		assert.NoError(t, err)
		assert.Nil(t, role)
		AssertExpectations(t, mock)
	})
}

func TestUpdateRole(t *testing.T) {
	db, mock := NewTestDB(t)
	logger := NewTestLogger()
	store := database.NewPostgresRolesStore(db, logger)

	role := &database.OrganizationRole{
		OrganizationID:      uuid.New(),
		Role:                "Chef",
		MinNeededPerShift:   5,
		ItemsPerRolePerHour: func() *int { i := 10; return &i }(),
		NeedForDemand:       false,
		Independent:         func() *bool { b := true; return &b }(),
	}

	query := regexp.QuoteMeta(`UPDATE organizations_roles SET min_needed_per_shift = $3, items_per_role_per_hour = $4, need_for_demand = $5, independent = $6 WHERE organization_id = $1 AND role = $2`)

	t.Run("Success", func(t *testing.T) {
		mock.ExpectExec(query).
			WithArgs(role.OrganizationID, role.Role, role.MinNeededPerShift, role.ItemsPerRolePerHour, role.NeedForDemand, role.Independent).
			WillReturnResult(sqlmock.NewResult(0, 1))

		err := store.UpdateRole(role)
		assert.NoError(t, err)
		AssertExpectations(t, mock)
	})

	t.Run("NotFound", func(t *testing.T) {
		mock.ExpectExec(query).WillReturnResult(sqlmock.NewResult(0, 0))
		err := store.UpdateRole(role)
		assert.Error(t, err)
		assert.Equal(t, "no role found to update", err.Error())
		AssertExpectations(t, mock)
	})
}

func TestDeleteRole(t *testing.T) {
	db, mock := NewTestDB(t)
	logger := NewTestLogger()
	store := database.NewPostgresRolesStore(db, logger)

	orgID := uuid.New()
	roleName := "Chef"
	query := regexp.QuoteMeta(`DELETE FROM organizations_roles WHERE organization_id = $1 AND role = $2`)

	t.Run("Success", func(t *testing.T) {
		mock.ExpectExec(query).WithArgs(orgID, roleName).WillReturnResult(sqlmock.NewResult(0, 1))
		err := store.DeleteRole(orgID, roleName)
		assert.NoError(t, err)
		AssertExpectations(t, mock)
	})

	t.Run("ProtectedRole", func(t *testing.T) {
		err := store.DeleteRole(orgID, "admin")
		assert.Error(t, err)
		assert.Contains(t, err.Error(), "cannot delete protected role")
	})

	t.Run("NotFound", func(t *testing.T) {
		mock.ExpectExec(query).WithArgs(orgID, roleName).WillReturnResult(sqlmock.NewResult(0, 0))
		err := store.DeleteRole(orgID, roleName)
		assert.Error(t, err)
		assert.Equal(t, "no role found to delete", err.Error())
		AssertExpectations(t, mock)
	})
}
