package api

import (
	"log/slog"
	"net/http"

	"github.com/clockwise/clockwise/backend/internal/database"
	"github.com/clockwise/clockwise/backend/internal/service"
	"github.com/clockwise/clockwise/backend/internal/utils"

	"github.com/gin-gonic/gin"
)

type OrgHandler struct {
	orgStore       database.OrgStore
	userStore      database.UserStore
	userRolesStore database.UserRolesStore
	rolesStore     database.RolesStore
	emailService   service.EmailService
	Logger         *slog.Logger
}

func NewOrgHandler(orgStore database.OrgStore, userStore database.UserStore, userRolesStore database.UserRolesStore, rolesStore database.RolesStore, emailService service.EmailService, logger *slog.Logger) *OrgHandler {
	return &OrgHandler{
		orgStore:       orgStore,
		userStore:      userStore,
		userRolesStore: userRolesStore,
		rolesStore:     rolesStore,
		emailService:   emailService,
		Logger:         logger,
	}
}

type RegisterOrgRequest struct {
	OrgName       string   `json:"org_name" binding:"required"`
	OrgAddress    string   `json:"org_address"`
	Latitude      *float64 `json:"latitude"`
	Longitude     *float64 `json:"longitude"`
	AdminFullName string   `json:"admin_full_name" binding:"required"`
	AdminEmail    string   `json:"admin_email" binding:"required,email"`
	AdminPassword string   `json:"admin_password" binding:"required,min=8"`
	Hex1          string   `json:"hex1" binding:"required,len=6"`
	Hex2          string   `json:"hex2" binding:"required,len=6"`
	Hex3          string   `json:"hex3" binding:"required,len=6"`
}

type DelegateUserRequest struct {
	FullName              string   `json:"full_name" binding:"required"`
	Email                 string   `json:"email" binding:"required,email"`
	Role                  string   `json:"role" binding:"required"`
	SalaryPerHour         float64  `json:"salary_per_hour" binding:"required"`
	MaxHoursPerWeek       *int     `json:"max_hours_per_week"`
	PreferredHoursPerWeek *int     `json:"preferred_hours_per_week"`
	MaxConsecSlots        *int     `json:"max_consec_slots"`
	UserRoles             []string `json:"user_roles"`
}

// RegisterOrganization godoc
// @Summary      Register a new organization
// @Description  Creates a new organization along with an admin user account
// @Tags         Organizations
// @Accept       json
// @Produce      json
// @Param        request body RegisterOrgRequest true "Organization registration details"
// @Success      201 {object} map[string]interface{} "Organization registered successfully"
// @Failure      400 {object} map[string]string "Invalid request body"
// @Failure      500 {object} map[string]string "Registration failed"
// @Router       /register [post]
func (h *OrgHandler) RegisterOrganization(c *gin.Context) {
	h.Logger.Info("register organization request received")

	var req RegisterOrgRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		h.Logger.Warn("invalid registration request", "error", err)
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	org := &database.Organization{
		Name:    req.OrgName,
		Address: req.OrgAddress,
		Location: database.Location{
			Latitude:  req.Latitude,
			Longitude: req.Longitude,
		},
		HexCode1:        req.Hex1,
		HexCode2:        req.Hex2,
		HexCode3:        req.Hex3,
		AcceptingOrders: true, // Default to accepting orders
	}

	user := &database.User{
		FullName: req.AdminFullName,
		Email:    req.AdminEmail,
		UserRole: "admin",
	}

	if err := h.orgStore.CreateOrgWithAdmin(org, user, req.AdminPassword); err != nil {
		h.Logger.Error("failed to create organization with admin", "error", err, "org_name", req.OrgName, "admin_email", req.AdminEmail)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Registration failed: " + err.Error()})
		return
	}

	h.Logger.Info("organization registered successfully", "org_id", org.ID, "user_id", user.ID, "org_name", req.OrgName)
	c.JSON(http.StatusCreated, gin.H{
		"message": "Organization registered successfully",
		"org_id":  org.ID,
		"user_id": user.ID,
	})
}

// DelegateUser godoc
// @Summary      Create a new employee
// @Description  Delegates/creates a new user in the organization. Only admins and managers can perform this action.
// @Tags         Staffing
// @Accept       json
// @Produce      json
// @Security     BearerAuth
// @Param        org path string true "Organization ID"
// @Param        request body DelegateUserRequest true "New employee details"
// @Success      201 {object} map[string]interface{} "User delegated successfully"
// @Failure      400 {object} map[string]string "Invalid request body"
// @Failure      401 {object} map[string]string "Unauthorized"
// @Failure      403 {object} map[string]string "Staff cannot delegate users"
// @Failure      500 {object} map[string]string "Internal server error"
// @Router       /{org}/staffing [post]
func (h *OrgHandler) DelegateUser(c *gin.Context) {
	h.Logger.Info("delegate user request received")

	currentUserInterface, exists := c.Get("user")
	if !exists {
		h.Logger.Warn("unauthorized delegation attempt - no user in context")
		c.JSON(http.StatusUnauthorized, gin.H{"error": "Unauthorized"})
		return
	}
	currentUser := currentUserInterface.(*database.User)

	if currentUser.UserRole == "staff" {
		h.Logger.Warn("forbidden delegation attempt by staff", "user_id", currentUser.ID, "email", currentUser.Email)
		c.JSON(http.StatusForbidden, gin.H{"error": "Staff cannot delegate users"})
		return
	}

	var req DelegateUserRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		h.Logger.Warn("invalid delegate user request", "error", err)
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	h.Logger.Debug("delegating user", "email", req.Email, "role", req.Role, "delegated_by", currentUser.ID)

	// Validate user roles if provided
	if len(req.UserRoles) > 0 {
		orgRoles, err := h.rolesStore.GetRolesByOrganizationID(currentUser.OrganizationID)
		if err != nil {
			h.Logger.Error("failed to get organization roles", "error", err, "org_id", currentUser.OrganizationID)
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to validate roles"})
			return
		}

		validRoles := make(map[string]bool)
		for _, role := range orgRoles {
			validRoles[role.Role] = true
		}

		for _, role := range req.UserRoles {
			if !validRoles[role] {
				h.Logger.Warn("invalid role in request", "role", role, "organization_id", currentUser.OrganizationID)
				c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid role: " + role + ". Role does not exist in this organization."})
				return
			}
		}
	}

	org, err := h.orgStore.GetOrganizationByID(currentUser.OrganizationID)
	if err != nil {
		h.Logger.Error("failed to retrieve organization", "error", err, "org_id", currentUser.OrganizationID)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to retrieve organization"})
		return
	}

	tempPassword, err := utils.GenerateRandomPassword(8)
	if err != nil {
		h.Logger.Error("failed to generate temporary password", "error", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to generate password"})
		return
	}

	newUser := &database.User{
		FullName:              req.FullName,
		Email:                 req.Email,
		UserRole:              req.Role,
		OrganizationID:        currentUser.OrganizationID,
		SalaryPerHour:         &req.SalaryPerHour,
		MaxHoursPerWeek:       req.MaxHoursPerWeek,
		PreferredHoursPerWeek: req.PreferredHoursPerWeek,
		MaxConsecSlots:        req.MaxConsecSlots,
	}

	if err := newUser.PasswordHash.Set(tempPassword); err != nil {
		h.Logger.Error("failed to hash password", "error", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Calculation error"})
		return
	}

	if err := h.userStore.CreateUser(newUser); err != nil {
		h.Logger.Error("failed to create delegated user", "error", err, "email", req.Email)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Database error: " + err.Error()})
		return
	}

	// Set user roles if provided
	if len(req.UserRoles) > 0 {
		if err := h.userRolesStore.SetUserRoles(newUser.ID, currentUser.OrganizationID, req.UserRoles); err != nil {
			h.Logger.Error("failed to set user roles", "error", err, "user_id", newUser.ID)
			// Don't fail the whole request, just log the error
		}
	}

	go func() {
		if err := h.emailService.SendWelcomeEmail(newUser.Email, newUser.FullName, tempPassword, newUser.UserRole, org.Name); err != nil {
			h.Logger.Error("failed to send welcome email", "error", err, "email", newUser.Email)
		}
	}()

	h.Logger.Info("user delegated successfully", "user_id", newUser.ID, "email", newUser.Email, "role", newUser.UserRole, "org_id", currentUser.OrganizationID)
	c.JSON(http.StatusCreated, gin.H{
		"message": "User delegated successfully. Email sent.",
		"user_id": newUser.ID,
	})
}
