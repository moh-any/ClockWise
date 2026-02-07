package database

import (
	"database/sql"
	"regexp"
	"testing"
	"time"

	"github.com/DATA-DOG/go-sqlmock"
	"github.com/clockwise/clockwise/backend/internal/database"
	"github.com/google/uuid"
	"github.com/stretchr/testify/assert"
)

func TestCreateUser(t *testing.T) {
	db, mock := NewTestDB(t)
	logger := NewTestLogger()
	store := database.NewPostgresUserStore(db, logger)

	user := &database.User{
		ID:             uuid.New(),
		FullName:       "John Doe",
		Email:          "john@example.com",
		UserRole:       "employee",
		OrganizationID: uuid.New(),
		SalaryPerHour:  func() *float64 { f := 20.0; return &f }(),
	}
	// Note: PasswordHash is private in struct but handled in store logic if set. Here we assume empty hash for simple insert test.

	query := regexp.QuoteMeta(`insert into users (id, full_name, email, password_hash, user_role, organization_id, salary_per_hour, max_hours_per_week, preferred_hours_per_week, max_consec_slots, on_call, created_at, updated_at) values ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13) returning id, created_at, updated_at`)

	t.Run("Success", func(t *testing.T) {
		rows := sqlmock.NewRows([]string{"id", "created_at", "updated_at"}).AddRow(user.ID, time.Now(), time.Now())

		mock.ExpectQuery(query).
			WithArgs(user.ID, user.FullName, user.Email, sqlmock.AnyArg(), user.UserRole, user.OrganizationID, user.SalaryPerHour, user.MaxHoursPerWeek, user.PreferredHoursPerWeek, user.MaxConsecSlots, user.OnCall, sqlmock.AnyArg(), sqlmock.AnyArg()).
			WillReturnRows(rows)

		err := store.CreateUser(user)
		assert.NoError(t, err)
		AssertExpectations(t, mock)
	})
}

func TestGetUserByEmail(t *testing.T) {
	db, mock := NewTestDB(t)
	logger := NewTestLogger()
	store := database.NewPostgresUserStore(db, logger)

	email := "john@example.com"
	query := regexp.QuoteMeta(`select id, full_name, email, password_hash, user_role, organization_id, salary_per_hour, max_hours_per_week, preferred_hours_per_week, max_consec_slots, on_call, created_at, updated_at from users where email=$1`)

	t.Run("Success", func(t *testing.T) {
		rows := sqlmock.NewRows([]string{"id", "full_name", "email", "password_hash", "user_role", "organization_id", "salary_per_hour", "max_hours_per_week", "preferred_hours_per_week", "max_consec_slots", "on_call", "created_at", "updated_at"}).
			AddRow(uuid.New(), "John Doe", email, []byte("hash"), "employee", uuid.New(), 20.0, 40, 30, 4, false, time.Now(), time.Now())

		mock.ExpectQuery(query).WithArgs(email).WillReturnRows(rows)

		user, err := store.GetUserByEmail(email)
		assert.NoError(t, err)
		assert.Equal(t, email, user.Email)
		AssertExpectations(t, mock)
	})
}

func TestUpdateUser(t *testing.T) {
	db, mock := NewTestDB(t)
	logger := NewTestLogger()
	store := database.NewPostgresUserStore(db, logger)

	user := &database.User{
		ID:             uuid.New(),
		FullName:       "John Doe Updated",
		Email:          "john@example.com",
		UserRole:       "manager",
		OrganizationID: uuid.New(),
	}

	query := regexp.QuoteMeta(`update users set full_name=$1, email=$2, user_role=$3, organization_id=$4, salary_per_hour=$5, max_hours_per_week=$6, preferred_hours_per_week=$7, max_consec_slots=$8, on_call=$9, updated_at=CURRENT_TIMESTAMP where id=$10 returning updated_at`)

	t.Run("Success", func(t *testing.T) {
		mock.ExpectExec(query).
			WithArgs(user.FullName, user.Email, user.UserRole, user.OrganizationID, user.SalaryPerHour, user.MaxHoursPerWeek, user.PreferredHoursPerWeek, user.MaxConsecSlots, user.OnCall, user.ID).
			WillReturnResult(sqlmock.NewResult(0, 1))

		err := store.UpdateUser(user)
		assert.NoError(t, err)
		AssertExpectations(t, mock)
	})
}

func TestLayoffUser(t *testing.T) {
	db, mock := NewTestDB(t)
	logger := NewTestLogger()
	store := database.NewPostgresUserStore(db, logger)

	userID := uuid.New()
	reason := "Redundancy"
	orgID := uuid.New()

	getUserQuery := regexp.QuoteMeta(`SELECT full_name, email, organization_id FROM users WHERE id=$1`)
	insertLayoffQuery := regexp.QuoteMeta(`INSERT INTO layoffs_hirings (id, user_id, user_name, user_email, organization_id, action, reason, action_date) VALUES ($1, $2, $3, $4, $5, 'layoff', $6, CURRENT_TIMESTAMP)`)
	deleteUserQuery := regexp.QuoteMeta(`DELETE FROM users WHERE id=$1`)

	t.Run("Success", func(t *testing.T) {
		mock.ExpectBegin()

		// 1. Get User Info
		mock.ExpectQuery(getUserQuery).WithArgs(userID).
			WillReturnRows(sqlmock.NewRows([]string{"full_name", "email", "organization_id"}).AddRow("John Doe", "john@example.com", orgID))

		// 2. Insert Layoff Record
		mock.ExpectExec(insertLayoffQuery).
			WithArgs(sqlmock.AnyArg(), userID, "John Doe", "john@example.com", orgID, reason).
			WillReturnResult(sqlmock.NewResult(1, 1))

		// 3. Delete User
		mock.ExpectExec(deleteUserQuery).WithArgs(userID).
			WillReturnResult(sqlmock.NewResult(0, 1))

		mock.ExpectCommit()

		err := store.LayoffUser(userID, reason)
		assert.NoError(t, err)
		AssertExpectations(t, mock)
	})

	t.Run("RollbackOnUserNotFound", func(t *testing.T) {
		mock.ExpectBegin()
		mock.ExpectQuery(getUserQuery).WithArgs(userID).WillReturnError(sql.ErrNoRows)
		mock.ExpectRollback()

		err := store.LayoffUser(userID, reason)
		assert.Error(t, err)
		AssertExpectations(t, mock)
	})
}

func TestGetProfile(t *testing.T) {
	db, mock := NewTestDB(t)
	logger := NewTestLogger()
	store := database.NewPostgresUserStore(db, logger)

	userID := uuid.New()
	// Complex query - matching structure
	query := regexp.QuoteMeta(`SELECT u.full_name, u.email, u.user_role, u.salary_per_hour, o.name as organization, u.created_at, COALESCE(SUM(EXTRACT(EPOCH FROM (s.end_hour - s.start_hour)) / 3600), 0) as total_hours, COALESCE(SUM( CASE WHEN s.schedule_date >= date_trunc('week', CURRENT_DATE) THEN EXTRACT(EPOCH FROM (s.end_hour - s.start_hour)) / 3600 ELSE 0 END ), 0) as week_hours FROM users u JOIN organizations o ON u.organization_id = o.id LEFT JOIN schedules s ON u.id = s.employee_id AND (s.schedule_date + s.end_hour) <= CURRENT_TIMESTAMP WHERE u.id = $1 GROUP BY u.id, u.full_name, u.email, u.user_role, u.salary_per_hour, o.name, u.created_at`)

	t.Run("Success", func(t *testing.T) {
		rows := sqlmock.NewRows([]string{"full_name", "email", "user_role", "salary_per_hour", "organization", "created_at", "total_hours", "week_hours"}).
			AddRow("John Doe", "john@example.com", "employee", 25.0, "Acme Corp", time.Now(), 100.0, 40.0)

		mock.ExpectQuery(query).WithArgs(userID).WillReturnRows(rows)

		profile, err := store.GetProfile(userID)
		assert.NoError(t, err)
		assert.Equal(t, "John Doe", profile.FullName)
		assert.Equal(t, 25.0, *profile.SalaryPerHour)
		assert.Equal(t, 100.0, *profile.HoursWorked)
		AssertExpectations(t, mock)
	})
}

func TestChangePassword(t *testing.T) {
	db, mock := NewTestDB(t)
	logger := NewTestLogger()
	store := database.NewPostgresUserStore(db, logger)

	userID := uuid.New()
	newHash := []byte("newhash")
	query := regexp.QuoteMeta(`UPDATE users SET password_hash = $1, updated_at = CURRENT_TIMESTAMP WHERE id = $2`)

	t.Run("Success", func(t *testing.T) {
		mock.ExpectExec(query).WithArgs(newHash, userID).WillReturnResult(sqlmock.NewResult(0, 1))
		err := store.ChangePassword(userID, newHash)
		assert.NoError(t, err)
		AssertExpectations(t, mock)
	})
}
