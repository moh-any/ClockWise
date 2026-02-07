package api

import (
	"log/slog"
	"net/http"

	"github.com/clockwise/clockwise/backend/internal/database"
	"github.com/clockwise/clockwise/backend/internal/middleware"
	"github.com/gin-gonic/gin"
)

// RolesHandler handles organization roles-related HTTP requests
type RolesHandler struct {
	rolesStore database.RolesStore
	Logger     *slog.Logger
}

// NewRolesHandler creates a new RolesHandler
func NewRolesHandler(rolesStore database.RolesStore, logger *slog.Logger) *RolesHandler {
	return &RolesHandler{
		rolesStore: rolesStore,
		Logger:     logger,
	}
}

// CreateRoleRequest represents the request body for creating a role
type CreateRoleRequest struct {
	Role                string `json:"role" binding:"required,min=1,max=50"`
	MinNeededPerShift   int    `json:"min_needed_per_shift" binding:"min=0"`
	ItemsPerRolePerHour *int   `json:"items_per_role_per_hour"`
	NeedForDemand       bool   `json:"need_for_demand"`
	Independent         *bool  `json:"independent"`
}

// UpdateRoleRequest represents the request body for updating a role
type UpdateRoleRequest struct {
	MinNeededPerShift   int   `json:"min_needed_per_shift" binding:"min=0"`
	ItemsPerRolePerHour *int  `json:"items_per_role_per_hour"`
	NeedForDemand       bool  `json:"need_for_demand"`
	Independent         *bool `json:"independent"`
}

// GetAllRoles godoc
func (h *RolesHandler) GetAllRoles(c *gin.Context) {
	h.Logger.Info("get all roles request received")

	user := middleware.ValidateOrgAccess(c)
	if user == nil {
		return
	}

	roles, err := h.rolesStore.GetRolesByOrganizationID(user.OrganizationID)
	if err != nil {
		h.Logger.Error("failed to get roles", "error", err, "organization_id", user.OrganizationID)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to retrieve roles"})
		return
	}

	if roles == nil {
		roles = []*database.OrganizationRole{}
	}

	h.Logger.Info("roles retrieved", "organization_id", user.OrganizationID, "count", len(roles))
	c.JSON(http.StatusOK, gin.H{
		"message": "Roles retrieved successfully",
		"data":    roles,
	})
}

// CreateRole godoc
func (h *RolesHandler) CreateRole(c *gin.Context) {
	h.Logger.Info("create role request received")

	user := middleware.ValidateOrgAccess(c)
	if user == nil {
		return
	}

	// Only admins can create roles
	if user.UserRole != "admin" {
		h.Logger.Warn("forbidden attempt to create role", "user_id", user.ID, "role", user.UserRole)
		c.JSON(http.StatusForbidden, gin.H{"error": "Only admins can create roles"})
		return
	}

	var req CreateRoleRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		h.Logger.Warn("invalid request body", "error", err)
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid request body: " + err.Error()})
		return
	}

	// Prevent creating protected role names
	if req.Role == "admin" || req.Role == "manager" {
		h.Logger.Warn("attempted to create protected role", "role", req.Role)
		c.JSON(http.StatusBadRequest, gin.H{"error": "Cannot create protected role: " + req.Role})
		return
	}

	// Validate need_for_demand constraints
	if req.NeedForDemand {
		if req.ItemsPerRolePerHour == nil || *req.ItemsPerRolePerHour < 0 {
			h.Logger.Warn("items_per_role_per_hour required when need_for_demand is true")
			c.JSON(http.StatusBadRequest, gin.H{"error": "items_per_role_per_hour must be >= 0 when need_for_demand is true"})
			return
		}
		if req.MinNeededPerShift < 0 {
			h.Logger.Warn("min_needed_per_shift must be >= 0 when need_for_demand is true")
			c.JSON(http.StatusBadRequest, gin.H{"error": "min_needed_per_shift must be >= 0 when need_for_demand is true"})
			return
		}
	} else {
		// If not need_for_demand, items_per_role_per_hour should be NULL
		req.ItemsPerRolePerHour = nil
	}

	// Check if role already exists
	existingRole, err := h.rolesStore.GetRoleByName(user.OrganizationID, req.Role)
	if err != nil {
		h.Logger.Error("failed to check existing role", "error", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to create role"})
		return
	}
	if existingRole != nil {
		h.Logger.Warn("role already exists", "role", req.Role)
		c.JSON(http.StatusConflict, gin.H{"error": "Role already exists: " + req.Role})
		return
	}

	role := &database.OrganizationRole{
		OrganizationID:      user.OrganizationID,
		Role:                req.Role,
		MinNeededPerShift:   req.MinNeededPerShift,
		ItemsPerRolePerHour: req.ItemsPerRolePerHour,
		NeedForDemand:       req.NeedForDemand,
		Independent:         req.Independent,
	}

	if err := h.rolesStore.CreateRole(role); err != nil {
		h.Logger.Error("failed to create role", "error", err, "organization_id", user.OrganizationID)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to create role"})
		return
	}

	h.Logger.Info("role created", "organization_id", user.OrganizationID, "role", req.Role)
	c.JSON(http.StatusCreated, gin.H{
		"message": "Role created successfully",
		"data":    role,
	})
}

// GetRole godoc
func (h *RolesHandler) GetRole(c *gin.Context) {
	h.Logger.Info("get role request received")

	user := middleware.ValidateOrgAccess(c)
	if user == nil {
		return
	}

	roleName := c.Param("role")
	if roleName == "" {
		h.Logger.Warn("role name not provided")
		c.JSON(http.StatusBadRequest, gin.H{"error": "Role name is required"})
		return
	}

	role, err := h.rolesStore.GetRoleByName(user.OrganizationID, roleName)
	if err != nil {
		h.Logger.Error("failed to get role", "error", err, "organization_id", user.OrganizationID, "role", roleName)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to retrieve role"})
		return
	}

	if role == nil {
		h.Logger.Warn("role not found", "role", roleName)
		c.JSON(http.StatusNotFound, gin.H{"error": "Role not found: " + roleName})
		return
	}

	h.Logger.Info("role retrieved", "organization_id", user.OrganizationID, "role", roleName)
	c.JSON(http.StatusOK, gin.H{
		"message": "Role retrieved successfully",
		"data":    role,
	})
}

// UpdateRole godoc
func (h *RolesHandler) UpdateRole(c *gin.Context) {
	h.Logger.Info("update role request received")

	user := middleware.ValidateOrgAccess(c)
	if user == nil {
		return
	}

	// Only admins can update roles
	if user.UserRole != "admin" {
		h.Logger.Warn("forbidden attempt to update role", "user_id", user.ID, "role", user.UserRole)
		c.JSON(http.StatusForbidden, gin.H{"error": "Only admins can update roles"})
		return
	}

	roleName := c.Param("role")
	if roleName == "" {
		h.Logger.Warn("role name not provided")
		c.JSON(http.StatusBadRequest, gin.H{"error": "Role name is required"})
		return
	}

	// Prevent modifying protected roles
	if roleName == "admin" || roleName == "manager" {
		h.Logger.Warn("attempted to modify protected role", "role", roleName)
		c.JSON(http.StatusForbidden, gin.H{"error": "Cannot modify protected role: " + roleName})
		return
	}

	var req UpdateRoleRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		h.Logger.Warn("invalid request body", "error", err)
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid request body: " + err.Error()})
		return
	}

	// Check if role exists
	existingRole, err := h.rolesStore.GetRoleByName(user.OrganizationID, roleName)
	if err != nil {
		h.Logger.Error("failed to check existing role", "error", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to update role"})
		return
	}
	if existingRole == nil {
		h.Logger.Warn("role not found", "role", roleName)
		c.JSON(http.StatusNotFound, gin.H{"error": "Role not found: " + roleName})
		return
	}

	// Validate need_for_demand constraints
	if req.NeedForDemand {
		if req.ItemsPerRolePerHour == nil || *req.ItemsPerRolePerHour < 0 {
			h.Logger.Warn("items_per_role_per_hour required when need_for_demand is true")
			c.JSON(http.StatusBadRequest, gin.H{"error": "items_per_role_per_hour must be >= 0 when need_for_demand is true"})
			return
		}
		if req.MinNeededPerShift < 0 {
			h.Logger.Warn("min_needed_per_shift must be >= 0 when need_for_demand is true")
			c.JSON(http.StatusBadRequest, gin.H{"error": "min_needed_per_shift must be >= 0 when need_for_demand is true"})
			return
		}
	} else {
		// If not need_for_demand, items_per_role_per_hour should be NULL
		req.ItemsPerRolePerHour = nil
	}

	role := &database.OrganizationRole{
		OrganizationID:      user.OrganizationID,
		Role:                roleName,
		MinNeededPerShift:   req.MinNeededPerShift,
		ItemsPerRolePerHour: req.ItemsPerRolePerHour,
		NeedForDemand:       req.NeedForDemand,
		Independent:         req.Independent,
	}

	if err := h.rolesStore.UpdateRole(role); err != nil {
		h.Logger.Error("failed to update role", "error", err, "organization_id", user.OrganizationID, "role", roleName)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to update role"})
		return
	}

	h.Logger.Info("role updated", "organization_id", user.OrganizationID, "role", roleName)
	c.JSON(http.StatusOK, gin.H{
		"message": "Role updated successfully",
		"data":    role,
	})
}

// DeleteRole godoc
func (h *RolesHandler) DeleteRole(c *gin.Context) {
	h.Logger.Info("delete role request received")

	user := middleware.ValidateOrgAccess(c)
	if user == nil {
		return
	}

	// Only admins can delete roles
	if user.UserRole != "admin" {
		h.Logger.Warn("forbidden attempt to delete role", "user_id", user.ID, "role", user.UserRole)
		c.JSON(http.StatusForbidden, gin.H{"error": "Only admins can delete roles"})
		return
	}

	roleName := c.Param("role")
	if roleName == "" {
		h.Logger.Warn("role name not provided")
		c.JSON(http.StatusBadRequest, gin.H{"error": "Role name is required"})
		return
	}

	// Prevent deleting protected roles
	if roleName == "admin" || roleName == "manager" {
		h.Logger.Warn("attempted to delete protected role", "role", roleName)
		c.JSON(http.StatusForbidden, gin.H{"error": "Cannot delete protected role: " + roleName})
		return
	}

	// Check if role exists
	existingRole, err := h.rolesStore.GetRoleByName(user.OrganizationID, roleName)
	if err != nil {
		h.Logger.Error("failed to check existing role", "error", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to delete role"})
		return
	}
	if existingRole == nil {
		h.Logger.Warn("role not found", "role", roleName)
		c.JSON(http.StatusNotFound, gin.H{"error": "Role not found: " + roleName})
		return
	}

	if err := h.rolesStore.DeleteRole(user.OrganizationID, roleName); err != nil {
		h.Logger.Error("failed to delete role", "error", err, "organization_id", user.OrganizationID, "role", roleName)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to delete role"})
		return
	}

	h.Logger.Info("role deleted", "organization_id", user.OrganizationID, "role", roleName)
	c.JSON(http.StatusOK, gin.H{
		"message": "Role deleted successfully",
	})
}
