package database

import (
	"database/sql"
	"errors"
	"log/slog"

	"github.com/google/uuid"
)

// OrganizationRole represents a role within an organization
type OrganizationRole struct {
	OrganizationID      uuid.UUID `json:"organization_id"`
	Role                string    `json:"role_id"`
	MinNeededPerShift   int       `json:"min_present"`
	ItemsPerRolePerHour *int      `json:"items_per_employee_per_hour"`
	NeedForDemand       bool      `json:"producing"`
	Independent         *bool     `json:"is_independent"`
}

// RolesStore defines the interface for organization roles data operations
type RolesStore interface {
	CreateRole(role *OrganizationRole) error
	GetRolesByOrganizationID(orgID uuid.UUID) ([]OrganizationRole, error)
	GetRoleByName(orgID uuid.UUID, roleName string) (*OrganizationRole, error)
	UpdateRole(role *OrganizationRole) error
	DeleteRole(orgID uuid.UUID, roleName string) error
}

// PostgresRolesStore implements RolesStore using PostgreSQL
type PostgresRolesStore struct {
	db     *sql.DB
	Logger *slog.Logger
}

// NewPostgresRolesStore creates a new PostgresRolesStore
func NewPostgresRolesStore(db *sql.DB, logger *slog.Logger) *PostgresRolesStore {
	return &PostgresRolesStore{
		db:     db,
		Logger: logger,
	}
}

// CreateRole creates a new role for an organization
func (s *PostgresRolesStore) CreateRole(role *OrganizationRole) error {
	query := `INSERT INTO organizations_roles 
		(organization_id, role, min_needed_per_shift, items_per_role_per_hour, need_for_demand, independent) 
		VALUES ($1, $2, $3, $4, $5, $6)`

	_, err := s.db.Exec(query,
		role.OrganizationID,
		role.Role,
		role.MinNeededPerShift,
		role.ItemsPerRolePerHour,
		role.NeedForDemand,
		role.Independent,
	)
	if err != nil {
		s.Logger.Error("failed to create role", "error", err, "organization_id", role.OrganizationID, "role", role.Role)
		return err
	}

	s.Logger.Info("role created", "organization_id", role.OrganizationID, "role", role.Role)
	return nil
}

// GetRolesByOrganizationID retrieves all roles for a specific organization
func (s *PostgresRolesStore) GetRolesByOrganizationID(orgID uuid.UUID) ([]OrganizationRole, error) {
	query := `SELECT organization_id, role, min_needed_per_shift, items_per_role_per_hour, need_for_demand, independent 
		FROM organizations_roles WHERE organization_id = $1 ORDER BY role`

	rows, err := s.db.Query(query, orgID)
	if err != nil {
		s.Logger.Error("failed to get roles", "error", err, "organization_id", orgID)
		return nil, err
	}
	defer rows.Close()

	var roles []OrganizationRole
	for rows.Next() {
		var r OrganizationRole
		if err := rows.Scan(
			&r.OrganizationID,
			&r.Role,
			&r.MinNeededPerShift,
			&r.ItemsPerRolePerHour,
			&r.NeedForDemand,
			&r.Independent,
		); err != nil {
			s.Logger.Error("failed to scan role", "error", err)
			return nil, err
		}
		roles = append(roles, r)
	}

	if err := rows.Err(); err != nil {
		return nil, err
	}

	return roles, nil
}

// GetRoleByName retrieves a specific role by name for an organization
func (s *PostgresRolesStore) GetRoleByName(orgID uuid.UUID, roleName string) (*OrganizationRole, error) {
	var role OrganizationRole

	query := `SELECT organization_id, role, min_needed_per_shift, items_per_role_per_hour, need_for_demand, independent 
		FROM organizations_roles WHERE organization_id = $1 AND role = $2`

	err := s.db.QueryRow(query, orgID, roleName).Scan(
		&role.OrganizationID,
		&role.Role,
		&role.MinNeededPerShift,
		&role.ItemsPerRolePerHour,
		&role.NeedForDemand,
		&role.Independent,
	)
	if err != nil {
		if errors.Is(err, sql.ErrNoRows) {
			return nil, nil // No role found
		}
		s.Logger.Error("failed to get role", "error", err, "organization_id", orgID, "role", roleName)
		return nil, err
	}

	return &role, nil
}

// UpdateRole updates an existing role
func (s *PostgresRolesStore) UpdateRole(role *OrganizationRole) error {
	query := `UPDATE organizations_roles SET 
		min_needed_per_shift = $3, 
		items_per_role_per_hour = $4, 
		need_for_demand = $5,
		independent = $6 
		WHERE organization_id = $1 AND role = $2`

	result, err := s.db.Exec(query,
		role.OrganizationID,
		role.Role,
		role.MinNeededPerShift,
		role.ItemsPerRolePerHour,
		role.NeedForDemand,
		role.Independent,
	)
	if err != nil {
		s.Logger.Error("failed to update role", "error", err, "organization_id", role.OrganizationID, "role", role.Role)
		return err
	}

	rowsAffected, _ := result.RowsAffected()
	if rowsAffected == 0 {
		return errors.New("no role found to update")
	}

	s.Logger.Info("role updated", "organization_id", role.OrganizationID, "role", role.Role)
	return nil
}

// DeleteRole deletes a role from an organization
func (s *PostgresRolesStore) DeleteRole(orgID uuid.UUID, roleName string) error {
	// Prevent deletion of protected roles
	if roleName == "admin" || roleName == "manager" {
		return errors.New("cannot delete protected role: " + roleName)
	}

	query := `DELETE FROM organizations_roles WHERE organization_id = $1 AND role = $2`

	result, err := s.db.Exec(query, orgID, roleName)
	if err != nil {
		s.Logger.Error("failed to delete role", "error", err, "organization_id", orgID, "role", roleName)
		return err
	}

	rowsAffected, _ := result.RowsAffected()
	if rowsAffected == 0 {
		return errors.New("no role found to delete")
	}

	s.Logger.Info("role deleted", "organization_id", orgID, "role", roleName)
	return nil
}