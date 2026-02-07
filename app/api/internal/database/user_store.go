package database

import (
	"database/sql"
	"errors"
	"log/slog"
	"time"

	"github.com/google/uuid"
	"golang.org/x/crypto/bcrypt"
)

type Password struct {
	plainText *string
	hash      []byte
}

func Hash(plaintextPassword string) ([]byte, error) {
	hash, err := bcrypt.GenerateFromPassword([]byte(plaintextPassword), 12)
	if err != nil {
		return nil, err
	}
	return hash, nil
}
func (p *Password) Set(plaintextPassword string) error {
	hash, err := bcrypt.GenerateFromPassword([]byte(plaintextPassword), 12)
	if err != nil {
		return err
	}

	p.plainText = &plaintextPassword
	p.hash = hash
	return nil
}

func (p *Password) Matches(plaintextPassword string) (bool, error) {
	err := bcrypt.CompareHashAndPassword(p.hash, []byte(plaintextPassword))
	if err != nil {
		switch {
		case errors.Is(err, bcrypt.ErrMismatchedHashAndPassword):
			return false, nil
		default:
			return false, err
		}
	}

	return true, nil
}

type User struct {
	ID                    uuid.UUID `json:"id"`
	FullName              string    `json:"full_name"`
	Email                 string    `json:"email"`
	PasswordHash          Password  `json:"-"`
	UserRole              string    `json:"user_role"`
	SalaryPerHour         *float64  `json:"salary_per_hour,omitempty"`
	OrganizationID        uuid.UUID `json:"organization_id"`
	MaxHoursPerWeek       *int      `json:"max_hours_per_week,omitempty"`
	PreferredHoursPerWeek *int      `json:"preferred_hours_per_week,omitempty"`
	MaxConsecSlots        *int      `json:"max_consec_slots,omitempty"`
	OnCall                *bool     `json:"on_call"`
	CreatedAt             time.Time `json:"created_at"`
	UpdatedAt             time.Time `json:"updated_at"`
}

var AnonymousUser = &User{}

func (u *User) IsAnonymous() bool {
	return u == AnonymousUser
}

type UserProfile struct {
	FullName            string    `json:"full_name"`
	Email               string    `json:"email"`
	UserRole            string    `json:"user_role"`
	SalaryPerHour       *float64  `json:"salary_per_hour,omitempty"`
	Organization        string    `json:"organization"`
	CreatedAt           time.Time `json:"created_at"`
	HoursWorked         *float64  `json:"hours_worked,omitempty"`
	HoursWorkedThisWeek *float64  `json:"this_week_hours,omitempty"`
}

type PostgresUserStore struct {
	db *sql.DB
}

func NewPostgresUserStore(db *sql.DB, Logger *slog.Logger) *PostgresUserStore {
	return &PostgresUserStore{
		db: db,
	}
}

type UserStore interface {
	CreateUser(user *User) error
	GetUserByEmail(email string) (*User, error)
	GetUserByID(id uuid.UUID) (*User, error)
	GetUsersByOrganization(orgID uuid.UUID) ([]*User, error)
	UpdateUser(user *User) error
	DeleteUser(id uuid.UUID) error
	LayoffUser(id uuid.UUID, reason string) error
	GetProfile(id uuid.UUID) (*UserProfile, error)
	ChangePassword(id uuid.UUID, passwordHash []byte) error
}

func (pgus *PostgresUserStore) CreateUser(user *User) error {
	// Ensure ID is generated if not present
	if user.ID == uuid.Nil {
		user.ID = uuid.New()
	}
	if user.CreatedAt.IsZero() {
		user.CreatedAt = time.Now()
	}
	if user.UpdatedAt.IsZero() {
		user.UpdatedAt = time.Now()
	}

	query :=
		`insert into users
	(id, full_name, email, password_hash, user_role, organization_id, salary_per_hour, max_hours_per_week, preferred_hours_per_week, max_consec_slots, on_call, created_at, updated_at) 
	values ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13) returning id, created_at, updated_at`

	err := pgus.db.QueryRow(query,
		user.ID,
		user.FullName,
		user.Email,
		user.PasswordHash.hash,
		user.UserRole,
		user.OrganizationID,
		user.SalaryPerHour,
		user.MaxHoursPerWeek,
		user.PreferredHoursPerWeek,
		user.MaxConsecSlots,
		user.OnCall,
		user.CreatedAt,
		user.UpdatedAt,
	).Scan(&user.ID, &user.CreatedAt, &user.UpdatedAt)

	if err != nil {
		return err
	}
	return nil
}

func (pgus *PostgresUserStore) GetUserByEmail(email string) (*User, error) {
	var user User
	query :=
		`select 
	id, full_name, email, password_hash, user_role, organization_id, salary_per_hour, max_hours_per_week, preferred_hours_per_week, max_consec_slots, on_call, created_at, updated_at 
	from users where email=$1`

	var hash []byte

	err := pgus.db.QueryRow(query, email).Scan(
		&user.ID,
		&user.FullName,
		&user.Email,
		&hash,
		&user.UserRole,
		&user.OrganizationID,
		&user.SalaryPerHour,
		&user.MaxHoursPerWeek,
		&user.PreferredHoursPerWeek,
		&user.MaxConsecSlots,
		&user.OnCall,
		&user.CreatedAt,
		&user.UpdatedAt,
	)
	if err != nil {
		return nil, err
	}
	user.PasswordHash.hash = hash
	return &user, nil
}

func (pgus *PostgresUserStore) UpdateUser(user *User) error {
	query :=
		`update users 
	set full_name=$1, email=$2, user_role=$3, organization_id=$4, salary_per_hour=$5, max_hours_per_week=$6, preferred_hours_per_week=$7, max_consec_slots=$8, on_call=$9, updated_at=CURRENT_TIMESTAMP where id=$10 
	returning updated_at`
	res, err := pgus.db.Exec(query, user.FullName, user.Email, user.UserRole, user.OrganizationID, user.SalaryPerHour, user.MaxHoursPerWeek, user.PreferredHoursPerWeek, user.MaxConsecSlots, user.OnCall, user.ID)
	if err != nil {
		return err
	}
	rowsAffected, err := res.RowsAffected()
	if err != nil {
		return err
	}
	if rowsAffected == 0 {
		return sql.ErrNoRows
	}
	return nil
}

func (pgus *PostgresUserStore) GetUserByID(id uuid.UUID) (*User, error) {
	var user User
	query := `SELECT id, full_name, email, password_hash, user_role, organization_id, salary_per_hour, max_hours_per_week, preferred_hours_per_week, max_consec_slots, on_call, created_at, updated_at 
		FROM users WHERE id=$1`

	var hash []byte
	err := pgus.db.QueryRow(query, id).Scan(
		&user.ID,
		&user.FullName,
		&user.Email,
		&hash,
		&user.UserRole,
		&user.OrganizationID,
		&user.SalaryPerHour,
		&user.MaxHoursPerWeek,
		&user.PreferredHoursPerWeek,
		&user.MaxConsecSlots,
		&user.OnCall,
		&user.CreatedAt,
		&user.UpdatedAt,
	)
	if err != nil {
		return nil, err
	}
	user.PasswordHash.hash = hash
	return &user, nil
}

func (pgus *PostgresUserStore) GetUsersByOrganization(orgID uuid.UUID) ([]*User, error) {
	query := `SELECT id, full_name, email, user_role, organization_id, salary_per_hour, max_hours_per_week, preferred_hours_per_week, max_consec_slots, on_call, created_at, updated_at 
		FROM users WHERE organization_id=$1 ORDER BY created_at DESC`

	rows, err := pgus.db.Query(query, orgID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var users []*User
	for rows.Next() {
		var user User
		err := rows.Scan(
			&user.ID,
			&user.FullName,
			&user.Email,
			&user.UserRole,
			&user.OrganizationID,
			&user.SalaryPerHour,
			&user.MaxHoursPerWeek,
			&user.PreferredHoursPerWeek,
			&user.MaxConsecSlots,
			&user.OnCall,
			&user.CreatedAt,
			&user.UpdatedAt,
		)
		if err != nil {
			return nil, err
		}
		users = append(users, &user)
	}

	if err = rows.Err(); err != nil {
		return nil, err
	}

	return users, nil
}

func (pgus *PostgresUserStore) DeleteUser(id uuid.UUID) error {
	query := `DELETE FROM users WHERE id=$1`
	res, err := pgus.db.Exec(query, id)
	if err != nil {
		return err
	}
	rowsAffected, err := res.RowsAffected()
	if err != nil {
		return err
	}
	if rowsAffected == 0 {
		return sql.ErrNoRows
	}
	return nil
}

func (pgus *PostgresUserStore) LayoffUser(id uuid.UUID, reason string) error {
	tx, err := pgus.db.Begin()
	if err != nil {
		return err
	}
	defer tx.Rollback()

	// Get user info before deletion
	var userName, userEmail string
	var orgID uuid.UUID
	getUserQuery := `SELECT full_name, email, organization_id FROM users WHERE id=$1`
	err = tx.QueryRow(getUserQuery, id).Scan(&userName, &userEmail, &orgID)
	if err != nil {
		return err
	}

	// Insert layoff record with user info
	layoffQuery := `INSERT INTO layoffs_hirings (id, user_id, user_name, user_email, organization_id, action, reason, action_date) 
		VALUES ($1, $2, $3, $4, $5, 'layoff', $6, CURRENT_TIMESTAMP)`

	_, err = tx.Exec(layoffQuery, uuid.New(), id, userName, userEmail, orgID, reason)
	if err != nil {
		return err
	}

	// Delete the user
	deleteQuery := `DELETE FROM users WHERE id=$1`
	res, err := tx.Exec(deleteQuery, id)
	if err != nil {
		return err
	}
	rowsAffected, err := res.RowsAffected()
	if err != nil {
		return err
	}
	if rowsAffected == 0 {
		return sql.ErrNoRows
	}

	return tx.Commit()
}

// Get Profile of User From PostgreSQL Database (admins profile has salaries and hours empty)
func (pgus *PostgresUserStore) GetProfile(id uuid.UUID) (*UserProfile, error) {
	var profile UserProfile
	var totalHours, weekHours sql.NullFloat64

	// Get user info with organization name and calculated hours
	query := `
		SELECT 
			u.full_name,
			u.email,
			u.user_role,
			u.salary_per_hour,
			o.name as organization,
			u.created_at,
			COALESCE(SUM(EXTRACT(EPOCH FROM (s.end_hour - s.start_hour)) / 3600), 0) as total_hours,
			COALESCE(SUM(
				CASE 
					WHEN s.schedule_date >= date_trunc('week', CURRENT_DATE) 
					THEN EXTRACT(EPOCH FROM (s.end_hour - s.start_hour)) / 3600
					ELSE 0 
				END
			), 0) as week_hours
		FROM users u
		JOIN organizations o ON u.organization_id = o.id
		LEFT JOIN schedules s ON u.id = s.employee_id AND (s.schedule_date + s.end_hour) <= CURRENT_TIMESTAMP
		WHERE u.id = $1
		GROUP BY u.id, u.full_name, u.email, u.user_role, u.salary_per_hour, o.name, u.created_at
	`

	err := pgus.db.QueryRow(query, id).Scan(
		&profile.FullName,
		&profile.Email,
		&profile.UserRole,
		&profile.SalaryPerHour,
		&profile.Organization,
		&profile.CreatedAt,
		&totalHours,
		&weekHours,
	)
	if err != nil {
		return nil, err
	}

	// Set hours only for non-admin users
	if profile.UserRole != "admin" && totalHours.Valid && totalHours.Float64 > 0 {
		profile.HoursWorked = &totalHours.Float64
	}
	if profile.UserRole != "admin" && weekHours.Valid && weekHours.Float64 > 0 {
		profile.HoursWorkedThisWeek = &weekHours.Float64
	}

	return &profile, nil
}

// Change Password in the database for the user
func (pgus *PostgresUserStore) ChangePassword(id uuid.UUID, passwordHash []byte) error {
	query := `UPDATE users SET password_hash = $1, updated_at = CURRENT_TIMESTAMP WHERE id = $2`

	res, err := pgus.db.Exec(query, passwordHash, id)
	if err != nil {
		return err
	}

	rowsAffected, err := res.RowsAffected()
	if err != nil {
		return err
	}
	if rowsAffected == 0 {
		return sql.ErrNoRows
	}

	return nil
}
