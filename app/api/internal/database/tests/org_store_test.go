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

func TestCreateOrgWithAdmin(t *testing.T) {
	db, mock := NewTestDB(t)
	logger := NewTestLogger()
	store := database.NewPostgresOrgStore(db, logger)

	org := &database.Organization{
		Name:     "Test Org",
		Address:  "123 Test St",
		Type:     "restaurant",
		Phone:    "+1234567890",
		Location: database.Location{Latitude: func() *float64 { f := 10.0; return &f }(), Longitude: func() *float64 { f := 20.0; return &f }()},
		Email:    "org@test.com",
		HexCode1: "FFFFFF",
		HexCode2: "000000",
		HexCode3: "111111",
		Rating:   func() *float64 { f := 5.0; return &f }(),
	}

	admin := &database.User{
		FullName: "Admin User",
		Email:    "admin@test.com",
		UserRole: "admin",
	}

	password := "password123"

	// Query regexes
	qInsertOrg := regexp.QuoteMeta(`INSERT INTO organizations (id, name, address, latitude, longitude, email, type, phone, created_at, updated_at, hex_code1, hex_code2, hex_code3, rating) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)`)
	qInsertUser := regexp.QuoteMeta(`INSERT INTO users (id, full_name, email, password_hash, user_role, organization_id, created_at, updated_at) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)`)

	t.Run("Success", func(t *testing.T) {
		mock.ExpectBegin()

		mock.ExpectExec(qInsertOrg).
			WithArgs(
				sqlmock.AnyArg(), // ID (generated)
				org.Name,
				org.Address,
				org.Location.Latitude,
				org.Location.Longitude,
				org.Email,
				org.Type,
				org.Phone,
				sqlmock.AnyArg(), // CreatedAt
				sqlmock.AnyArg(), // UpdatedAt
				org.HexCode1,
				org.HexCode2,
				org.HexCode3,
				org.Rating,
			).
			WillReturnResult(sqlmock.NewResult(1, 1))

		mock.ExpectExec(qInsertUser).
			WithArgs(
				sqlmock.AnyArg(), // User ID
				admin.FullName,
				admin.Email,
				sqlmock.AnyArg(), // Password Hash
				admin.UserRole,
				sqlmock.AnyArg(), // Org ID (from previous step)
				sqlmock.AnyArg(), // CreatedAt
				sqlmock.AnyArg(), // UpdatedAt
			).
			WillReturnResult(sqlmock.NewResult(1, 1))

		mock.ExpectCommit()

		err := store.CreateOrgWithAdmin(org, admin, password)
		assert.NoError(t, err)
		AssertExpectations(t, mock)
	})

	t.Run("Failure_OrgInsert", func(t *testing.T) {
		mock.ExpectBegin()
		mock.ExpectExec(qInsertOrg).WillReturnError(fmt.Errorf("insert org error"))
		mock.ExpectRollback()

		err := store.CreateOrgWithAdmin(org, admin, password)
		assert.Error(t, err)
		AssertExpectations(t, mock)
	})

	t.Run("Failure_UserInsert", func(t *testing.T) {
		mock.ExpectBegin()
		mock.ExpectExec(qInsertOrg).WillReturnResult(sqlmock.NewResult(1, 1))
		mock.ExpectExec(qInsertUser).WillReturnError(fmt.Errorf("insert user error"))
		mock.ExpectRollback()

		err := store.CreateOrgWithAdmin(org, admin, password)
		assert.Error(t, err)
		AssertExpectations(t, mock)
	})
}

func TestGetOrganizationByID(t *testing.T) {
	db, mock := NewTestDB(t)
	logger := NewTestLogger()
	store := database.NewPostgresOrgStore(db, logger)

	orgID := uuid.New()
	query := regexp.QuoteMeta(`SELECT id, name, address, latitude, longitude, email, type, phone, hex_code1, hex_code2, hex_code3, rating, created_at, updated_at FROM organizations WHERE id = $1`)

	t.Run("Success", func(t *testing.T) {
		rows := sqlmock.NewRows([]string{
			"id", "name", "address", "latitude", "longitude", "email",
			"type", "phone", "hex_code1", "hex_code2", "hex_code3", "rating",
			"created_at", "updated_at",
		}).AddRow(
			orgID, "Test Org", "Address", 1.0, 2.0, "email@test.com",
			"restaurant", "+1234567890", "000", "111", "222", 5.0,
			time.Now(), time.Now(),
		)

		mock.ExpectQuery(query).WithArgs(orgID).WillReturnRows(rows)

		org, err := store.GetOrganizationByID(orgID)
		assert.NoError(t, err)
		assert.Equal(t, "Test Org", org.Name)
		assert.Equal(t, "restaurant", org.Type)
		assert.Equal(t, "+1234567890", org.Phone)
		AssertExpectations(t, mock)
	})

	t.Run("DBError", func(t *testing.T) {
		mock.ExpectQuery(query).WithArgs(orgID).WillReturnError(fmt.Errorf("db error"))
		org, err := store.GetOrganizationByID(orgID)
		assert.Error(t, err)
		assert.Nil(t, org)
		AssertExpectations(t, mock)
	})
}

func TestGetOrganizationProfile(t *testing.T) {
	db, mock := NewTestDB(t)
	logger := NewTestLogger()
	store := database.NewPostgresOrgStore(db, logger)

	orgID := uuid.New()

	qOrg := regexp.QuoteMeta(`SELECT name, address, latitude, longitude, email, type, phone, hex_code1, hex_code2, hex_code3, rating FROM organizations WHERE id = $1`)
	qCount := regexp.QuoteMeta(`SELECT COUNT(*) FROM users WHERE organization_id = $1 AND user_role != 'admin'`)

	t.Run("Success", func(t *testing.T) {
		// Mock Organization Query
		rowsOrg := sqlmock.NewRows([]string{
			"name", "address", "latitude", "longitude", "email",
			"type", "phone", "hex_code1", "hex_code2", "hex_code3", "rating",
		}).AddRow(
			"Test Org", "Address", 1.0, 2.0, "email@test.com",
			"restaurant", "+1234567890", "000", "111", "222", 4.5,
		)
		mock.ExpectQuery(qOrg).WithArgs(orgID).WillReturnRows(rowsOrg)

		// Mock Employee Count Query
		mock.ExpectQuery(qCount).WithArgs(orgID).WillReturnRows(NewRow(10))

		profile, err := store.GetOrganizationProfile(orgID)
		assert.NoError(t, err)
		assert.Equal(t, "Test Org", profile.Name)
		assert.Equal(t, "restaurant", profile.Type)
		assert.Equal(t, "+1234567890", profile.Phone)
		assert.Equal(t, 10, profile.NumberOfEmployees)
		AssertExpectations(t, mock)
	})

	t.Run("NotFound", func(t *testing.T) {
		mock.ExpectQuery(qOrg).WithArgs(orgID).WillReturnError(sql.ErrNoRows)

		profile, err := store.GetOrganizationProfile(orgID)
		assert.Error(t, err)
		assert.Equal(t, "organization not found", err.Error())
		assert.Nil(t, profile)
		AssertExpectations(t, mock)
	})
}

func TestGetManagerEmailsByOrgID(t *testing.T) {
	db, mock := NewTestDB(t)
	logger := NewTestLogger()
	store := database.NewPostgresOrgStore(db, logger)

	orgID := uuid.New()
	query := regexp.QuoteMeta(`SELECT email FROM users WHERE organization_id = $1 AND user_role = 'manager'`)

	t.Run("Success", func(t *testing.T) {
		rows := sqlmock.NewRows([]string{"email"}).
			AddRow("manager1@test.com").
			AddRow("manager2@test.com")

		mock.ExpectQuery(query).WithArgs(orgID).WillReturnRows(rows)

		emails, err := store.GetManagerEmailsByOrgID(orgID)
		assert.NoError(t, err)
		assert.Len(t, emails, 2)
		assert.Contains(t, emails, "manager1@test.com")
		AssertExpectations(t, mock)
	})

	t.Run("DBError", func(t *testing.T) {
		mock.ExpectQuery(query).WithArgs(orgID).WillReturnError(fmt.Errorf("db error"))
		emails, err := store.GetManagerEmailsByOrgID(orgID)
		assert.Error(t, err)
		assert.Nil(t, emails)
		AssertExpectations(t, mock)
	})
}

func TestGetAdminEmailsByOrgID(t *testing.T) {
	db, mock := NewTestDB(t)
	logger := NewTestLogger()
	store := database.NewPostgresOrgStore(db, logger)

	orgID := uuid.New()
	query := regexp.QuoteMeta(`SELECT email FROM users WHERE organization_id = $1 AND user_role = 'admin'`)

	t.Run("Success", func(t *testing.T) {
		rows := sqlmock.NewRows([]string{"email"}).
			AddRow("admin@test.com")

		mock.ExpectQuery(query).WithArgs(orgID).WillReturnRows(rows)

		emails, err := store.GetAdminEmailsByOrgID(orgID)
		assert.NoError(t, err)
		assert.Len(t, emails, 1)
		assert.Equal(t, "admin@test.com", emails[0])
		AssertExpectations(t, mock)
	})

	t.Run("DBError", func(t *testing.T) {
		mock.ExpectQuery(query).WithArgs(orgID).WillReturnError(fmt.Errorf("db error"))
		emails, err := store.GetAdminEmailsByOrgID(orgID)
		assert.Error(t, err)
		assert.Nil(t, emails)
		AssertExpectations(t, mock)
	})
}
