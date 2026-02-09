package database

import (
	"database/sql"
	"log/slog"

	"github.com/google/uuid"
)

// UserRole represents a role assignment for a user in an organization
type UserRole struct {
	UserID         uuid.UUID `json:"user_id"`
	OrganizationID uuid.UUID `json:"organization_id"`
	UserRole       string    `json:"user_role"`
}

// UserRolesStore defines the interface for user roles data operations
type UserRolesStore interface {
	// Get all roles for a user in an organization
	GetUserRoles(userID uuid.UUID, orgID uuid.UUID) ([]string, error)
	// Set roles for a user (replaces existing roles)
	SetUserRoles(userID uuid.UUID, orgID uuid.UUID, roles []string) error
	// Add a single role to a user
	AddUserRole(userID uuid.UUID, orgID uuid.UUID, role string) error
	// Remove a single role from a user
	RemoveUserRole(userID uuid.UUID, orgID uuid.UUID, role string) error
	// Delete all roles for a user
	DeleteAllUserRoles(userID uuid.UUID, orgID uuid.UUID) error
}

// PostgresUserRolesStore implements UserRolesStore using PostgreSQL
type PostgresUserRolesStore struct {
	db     *sql.DB
	Logger *slog.Logger
}

// NewPostgresUserRolesStore creates a new PostgresUserRolesStore
func NewPostgresUserRolesStore(db *sql.DB, logger *slog.Logger) *PostgresUserRolesStore {
	return &PostgresUserRolesStore{
		db:     db,
		Logger: logger,
	}
}

// GetUserRoles retrieves all roles for a user in an organization
func (s *PostgresUserRolesStore) GetUserRoles(userID uuid.UUID, orgID uuid.UUID) ([]string, error) {
	query := `SELECT user_role FROM user_roles WHERE user_id = $1 AND organization_id = $2 ORDER BY user_role`

	rows, err := s.db.Query(query, userID, orgID)

	if err != nil {
		s.Logger.Error("failed to get user roles", "error", err, "user_id", userID, "organization_id", orgID)
		return nil, err
	}

	defer rows.Close()

	roles := []string{}
	for rows.Next() {
		var role string
		if err := rows.Scan(&role); err != nil {
			s.Logger.Error("failed to scan role", "error", err)
			return nil, err
		}
		roles = append(roles, role)
	}

	return roles, nil
}

// SetUserRoles replaces all roles for a user with the provided list
func (s *PostgresUserRolesStore) SetUserRoles(userID uuid.UUID, orgID uuid.UUID, roles []string) error {
	tx, err := s.db.Begin()
	if err != nil {
		s.Logger.Error("failed to begin transaction", "error", err)
		return err
	}
	defer tx.Rollback()

	// Delete existing roles
	deleteQuery := `DELETE FROM user_roles WHERE user_id = $1 AND organization_id = $2`
	_, err = tx.Exec(deleteQuery, userID, orgID)
	if err != nil {
		s.Logger.Error("failed to delete existing roles", "error", err, "user_id", userID)
		return err
	}

	// Insert new roles
	insertQuery := `INSERT INTO user_roles (user_id, organization_id, user_role) VALUES ($1, $2, $3)`
	for _, role := range roles {
		_, err = tx.Exec(insertQuery, userID, orgID, role)
		if err != nil {
			s.Logger.Error("failed to insert role", "error", err, "user_id", userID, "role", role)
			return err
		}
	}

	if err := tx.Commit(); err != nil {
		s.Logger.Error("failed to commit transaction", "error", err)
		return err
	}

	s.Logger.Info("user roles set", "user_id", userID, "organization_id", orgID, "roles", roles)
	return nil
}

// AddUserRole adds a single role to a user
func (s *PostgresUserRolesStore) AddUserRole(userID uuid.UUID, orgID uuid.UUID, role string) error {
	query := `INSERT INTO user_roles (user_id, organization_id, user_role) VALUES ($1, $2, $3)
		ON CONFLICT (user_id, organization_id, user_role) DO NOTHING`

	_, err := s.db.Exec(query, userID, orgID, role)
	if err != nil {
		s.Logger.Error("failed to add user role", "error", err, "user_id", userID, "role", role)
		return err
	}

	s.Logger.Info("user role added", "user_id", userID, "organization_id", orgID, "role", role)
	return nil
}

// RemoveUserRole removes a single role from a user
func (s *PostgresUserRolesStore) RemoveUserRole(userID uuid.UUID, orgID uuid.UUID, role string) error {
	query := `DELETE FROM user_roles WHERE user_id = $1 AND organization_id = $2 AND user_role = $3`

	result, err := s.db.Exec(query, userID, orgID, role)
	if err != nil {
		s.Logger.Error("failed to remove user role", "error", err, "user_id", userID, "role", role)
		return err
	}

	rowsAffected, _ := result.RowsAffected()
	s.Logger.Info("user role removed", "user_id", userID, "organization_id", orgID, "role", role, "removed", rowsAffected > 0)
	return nil
}

// DeleteAllUserRoles removes all roles for a user in an organization
func (s *PostgresUserRolesStore) DeleteAllUserRoles(userID uuid.UUID, orgID uuid.UUID) error {
	query := `DELETE FROM user_roles WHERE user_id = $1 AND organization_id = $2`

	result, err := s.db.Exec(query, userID, orgID)
	if err != nil {
		s.Logger.Error("failed to delete all user roles", "error", err, "user_id", userID)
		return err
	}

	rowsAffected, _ := result.RowsAffected()
	s.Logger.Info("all user roles deleted", "user_id", userID, "organization_id", orgID, "count", rowsAffected)
	return nil
}
