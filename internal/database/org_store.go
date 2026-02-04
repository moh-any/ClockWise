package database

import (
	"database/sql"
	"fmt"
	"log/slog"
	"time"
	"github.com/google/uuid"
)

type Organization struct {
	ID        uuid.UUID `json:"id"`
	Name      string    `json:"name"`
	Address   string    `json:"address"`
	Email     string    `json:"email"`
	CreatedAt time.Time `json:"created_at"`
	UpdatedAt time.Time `json:"updated_at"`
	HexCode1 string `json:"hex1"`
	HexCode2 string `json:"hex2"`
	HexCode3 string `json:"hex3"`
}

type OrgStore interface {
	CreateOrgWithAdmin(org *Organization, adminUser *User, password string) error
	GetOrganizationByID(id uuid.UUID) (*Organization, error)
}

type PostgresOrgStore struct {
	db *sql.DB
}

func NewPostgresOrgStore(db *sql.DB, Logger *slog.Logger) *PostgresOrgStore {
	return &PostgresOrgStore{db: db}
}

func (s *PostgresOrgStore) CreateOrgWithAdmin(org *Organization, user *User, plainPassword string) error {
	tx, err := s.db.Begin()
	if err != nil {
		return err
	}
	defer tx.Rollback()

	org.ID = uuid.New()
	org.CreatedAt = time.Now()
	org.UpdatedAt = time.Now()
	if org.Email == "" {
		org.Email = user.Email
	}

	queryOrg := `INSERT INTO organizations (id, name, address, email, created_at, updated_at,hex_code1,hex_code2,hex_code3) VALUES ($1, $2, $3, $4, $5, $6,$7,$8,$9)`
	if _, err := tx.Exec(queryOrg, org.ID, org.Name, org.Address, org.Email, org.CreatedAt, org.UpdatedAt,org.HexCode1,org.HexCode2,org.HexCode3); err != nil {
		return fmt.Errorf("failed to insert org: %w", err)
	}

	roles := []string{"admin", "manager", "employee"}
	queryRoles := `INSERT INTO organizations_roles (organization_id, role) VALUES ($1, $2)`
	for _, role := range roles {
		if _, err := tx.Exec(queryRoles, org.ID, role); err != nil {
			return fmt.Errorf("failed to insert role %s: %w", role, err)
		}
	}

	user.ID = uuid.New()
	user.OrganizationID = org.ID
	user.CreatedAt = time.Now()
	user.UpdatedAt = time.Now()

	if err := user.PasswordHash.Set(plainPassword); err != nil {
		return err
	}

	queryUser := `INSERT INTO users (id, full_name, email, password_hash, user_role, organization_id, created_at, updated_at) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)`
	_, err = tx.Exec(queryUser, user.ID, user.FullName, user.Email, user.PasswordHash.hash, user.UserRole, user.OrganizationID, user.CreatedAt, user.UpdatedAt)

	if err != nil {
		return fmt.Errorf("failed to insert admin user: %w", err)
	}

	return tx.Commit()
}

func (s *PostgresOrgStore) GetOrganizationByID(id uuid.UUID) (*Organization, error) {
	var org Organization
	query := `SELECT id, name, address, email, created_at, updated_at FROM organizations WHERE id = $1`
	err := s.db.QueryRow(query, id).Scan(&org.ID, &org.Name, &org.Address, &org.Email, &org.CreatedAt, &org.UpdatedAt)
	if err != nil {
		return nil, err
	}
	return &org, nil
}
