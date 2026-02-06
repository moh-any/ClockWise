package database

import (
	"database/sql"
	"fmt"
	"log/slog"
	"time"

	"github.com/google/uuid"
)

type Organization struct {
	ID              uuid.UUID `json:"id"`
	Name            string    `json:"name"`
	Address         string    `json:"address"`
	Email           string    `json:"email"`
	Location        Location  `json:"location"`
	CreatedAt       time.Time `json:"created_at"`
	UpdatedAt       time.Time `json:"updated_at"`
	HexCode1        string    `json:"hex1"`
	HexCode2        string    `json:"hex2"`
	HexCode3        string    `json:"hex3"`
	Rating          *float64  `json:"rating"`
	AcceptingOrders bool      `json:"accepting_orders"`
}

type OrganizationProfile struct {
	Name              string   `json:"name"`
	Address           string   `json:"address"`
	Email             string   `json:"email"`
	Location          Location `json:"location"`
	HexCode1          string   `json:"hex1"`
	HexCode2          string   `json:"hex2"`
	HexCode3          string   `json:"hex3"`
	Rating            *float64 `json:"rating"`
	AcceptingOrders   bool     `json:"accepting_orders"`
	NumberOfEmployees int      `json:"number_of_employees"`
}

type OrgStore interface {
	CreateOrgWithAdmin(org *Organization, adminUser *User, password string) error
	GetOrganizationByID(id uuid.UUID) (*Organization, error)
	GetOrganizationProfile(id uuid.UUID) (*OrganizationProfile, error)
	GetManagerEmailsByOrgID(orgID uuid.UUID) ([]string, error)
	GetAdminEmailsByOrgID(orgID uuid.UUID) ([]string, error)
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

	queryOrg := `INSERT INTO organizations (id, name, address, latitude, longitude, email, created_at, updated_at, hex_code1, hex_code2, hex_code3, rating, accepting_orders) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)`
	if _, err := tx.Exec(queryOrg, org.ID, org.Name, org.Address, org.Location.Latitude, org.Location.Longitude, org.Email, org.CreatedAt, org.UpdatedAt, org.HexCode1, org.HexCode2, org.HexCode3, org.Rating, org.AcceptingOrders); err != nil {
		return fmt.Errorf("failed to insert org: %w", err)
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
	query := `SELECT id, name, address, latitude, longitude, email, hex_code1, hex_code2, hex_code3, rating, accepting_orders, created_at, updated_at FROM organizations WHERE id = $1`
	err := s.db.QueryRow(query, id).Scan(&org.ID, &org.Name, &org.Address, &org.Location.Latitude, &org.Location.Longitude, &org.Email, &org.HexCode1, &org.HexCode2, &org.HexCode3, &org.Rating, &org.AcceptingOrders, &org.CreatedAt, &org.UpdatedAt)
	if err != nil {
		return nil, err
	}
	return &org, nil
}

func (s *PostgresOrgStore) GetOrganizationProfile(id uuid.UUID) (*OrganizationProfile, error) {
	var profile OrganizationProfile

	// Get organization details
	orgQuery := `
		SELECT name, address, latitude, longitude, email, hex_code1, hex_code2, hex_code3, rating, accepting_orders
		FROM organizations 
		WHERE id = $1
	`
	err := s.db.QueryRow(orgQuery, id).Scan(
		&profile.Name,
		&profile.Address,
		&profile.Location.Latitude,
		&profile.Location.Longitude,
		&profile.Email,
		&profile.HexCode1,
		&profile.HexCode2,
		&profile.HexCode3,
		&profile.Rating,
		&profile.AcceptingOrders,
	)
	if err != nil {
		if err == sql.ErrNoRows {
			return nil, fmt.Errorf("organization not found")
		}
		return nil, err
	}

	// Get number of employees (excluding admin)
	countQuery := `SELECT COUNT(*) FROM users WHERE organization_id = $1 AND user_role != 'admin'`
	err = s.db.QueryRow(countQuery, id).Scan(&profile.NumberOfEmployees)
	if err != nil {
		return nil, err
	}

	return &profile, nil
}

func (s *PostgresOrgStore) GetManagerEmailsByOrgID(orgID uuid.UUID) ([]string, error) {
	query := `SELECT email FROM users WHERE organization_id = $1 AND user_role = 'manager'`
	rows, err := s.db.Query(query, orgID)
	if err != nil {
		return nil, fmt.Errorf("failed to get manager emails: %w", err)
	}
	defer rows.Close()

	var emails []string
	for rows.Next() {
		var email string
		if err := rows.Scan(&email); err != nil {
			return nil, err
		}
		emails = append(emails, email)
	}
	return emails, nil
}

func (s *PostgresOrgStore) GetAdminEmailsByOrgID(orgID uuid.UUID) ([]string, error) {
	query := `SELECT email FROM users WHERE organization_id = $1 AND user_role = 'admin'`
	rows, err := s.db.Query(query, orgID)
	if err != nil {
		return nil, fmt.Errorf("failed to get admin emails: %w", err)
	}
	defer rows.Close()

	var emails []string
	for rows.Next() {
		var email string
		if err := rows.Scan(&email); err != nil {
			return nil, err
		}
		emails = append(emails, email)
	}
	return emails, nil
}
