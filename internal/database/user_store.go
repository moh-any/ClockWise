package database

import (
	"database/sql"
	"errors"
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
	ID             uuid.UUID `json:"id"`
	UserName       string    `json:"username"`
	Email          string    `json:"email"`
	PasswordHash   Password  `json:"-"`
	UserRole       string    `json:"user_role"`
	OrganizationID uuid.UUID `json:"organization_id"`
	CreatedAt      time.Time `json:"created_at"`
	UpdatedAt      time.Time `json:"updated_at"`
}

var AnonymousUser = &User{}

func (u *User) IsAnonymous() bool {
	return u == AnonymousUser
}

type PostgresUserStore struct {
	db *sql.DB
}

func NewPostgresUserStore(db *sql.DB) *PostgresUserStore {
	return &PostgresUserStore{
		db: db,
	}
}

type UserStore interface {
	CreateUser(user *User) error
	GetUserByUserName(username string) (*User, error)
	UpdateUser(user *User) error
}

func (pgus *PostgresUserStore) CreateUser(user *User) error {
	query :=
		`insert into users
	(username,email,password_hash,user_role) 
	values ($1,$2,$3,$4) returning id,created_at,updated_at`
	err := pgus.db.QueryRow(query, user.UserName, user.Email, user.PasswordHash.hash, user.UserRole).Scan(&user.ID, &user.CreatedAt, &user.UpdatedAt)
	if err != nil {
		return err
	}
	return nil
}

func (pgus *PostgresUserStore) GetUserByUserName(username string) (*User, error) {
	var user User
	query :=
		`select 
	id,username,email,password_hash,user_role,organization_id,created_at,updated_at 
	from users where username=$1`
	err := pgus.db.QueryRow(query, username).Scan(
		&user.ID,
		&user.UserName,
		&user.Email,
		&user.PasswordHash.hash,
		&user.UserRole,
		&user.OrganizationID,
		&user.CreatedAt,
		&user.UpdatedAt,
	)
	if err != nil {
		return nil, err
	}
	return &user, nil
}

func (pgus *PostgresUserStore) UpdateUser(user *User) error {
	query :=
		`update users 
	set username=$1,email=$2,user_role=$3,organization_id=$4,updated_at=CURRENT_TIMESTAMP where id=$5 
	returning updated_at`
	res, err := pgus.db.Exec(query, user.UserName, user.Email, user.UserRole, user.OrganizationID, user.ID)
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
