package api

import (
	"log/slog"
	"net/http"

	"github.com/clockwise/clockwise/backend/internal/database"
	"github.com/clockwise/clockwise/backend/internal/middleware"
	"github.com/gin-gonic/gin"
)

// PreferencesHandler handles preference-related HTTP requests
type PreferencesHandler struct {
	preferencesStore database.PreferencesStore
	userRolesStore   database.UserRolesStore
	userStore        database.UserStore
	rolesStore       database.RolesStore
	Logger           *slog.Logger
}

// NewPreferencesHandler creates a new PreferencesHandler
func NewPreferencesHandler(preferencesStore database.PreferencesStore, userRolesStore database.UserRolesStore, userStore database.UserStore, rolesStore database.RolesStore, logger *slog.Logger) *PreferencesHandler {
	return &PreferencesHandler{
		preferencesStore: preferencesStore,
		userRolesStore:   userRolesStore,
		userStore:        userStore,
		rolesStore:       rolesStore,
		Logger:           logger,
	}
}

// DayPreferenceRequest represents a single day's preference in a request
type DayPreferenceRequest struct {
	Day                string  `json:"day" binding:"required"`
	PreferredStartTime *string `json:"preferred_start_time"`
	PreferredEndTime   *string `json:"preferred_end_time"`
	AvailableStartTime *string `json:"available_start_time"`
	AvailableEndTime   *string `json:"available_end_time"`
}

// PreferencesRequest represents the request body for creating/updating preferences
type PreferencesRequest struct {
	Preferences           []DayPreferenceRequest `json:"preferences" binding:"required,min=1,max=7,dive"`
	UserRoles             []string               `json:"user_roles"`
	MaxHoursPerWeek       *int                   `json:"max_hours_per_week"`
	PreferredHoursPerWeek *int                   `json:"preferred_hours_per_week"`
	MaxConsecSlots        *int                   `json:"max_consec_slots"`
}

// PreferencesResponse represents the response for preferences GET
type PreferencesResponse struct {
	DayPreferences        []*database.EmployeePreference `json:"day_preferences"`
	UserRoles             []string                       `json:"user_roles"`
	MaxHoursPerWeek       *int                           `json:"max_hours_per_week"`
	PreferredHoursPerWeek *int                           `json:"preferred_hours_per_week"`
	MaxConsecSlots        *int                           `json:"max_consec_slots"`
}

// GetCurrentEmployeePreferences godoc
// @Summary      Get current employee preferences
// @Description  Returns the work preferences of the currently authenticated employee for all days
// @Tags         Preferences
// @Accept       json
// @Produce      json
// @Security     BearerAuth
// @Param        org path string true "Organization ID"
// @Success      200 {object} map[string]interface{} "Employee preferences"
// @Failure      401 {object} map[string]string "Unauthorized"
// @Failure      403 {object} map[string]string "Access denied"
// @Failure      500 {object} map[string]string "Internal server error"
// @Router       /{org}/preferences [get]
func (h *PreferencesHandler) GetCurrentEmployeePreferences(c *gin.Context) {
	h.Logger.Info("get current employee preferences request received")

	user := middleware.ValidateOrgAccess(c)
	if user == nil {
		return
	}

	// Get day preferences
	prefs, err := h.preferencesStore.GetPreferencesByEmployeeID(user.ID)
	if err != nil {
		h.Logger.Error("failed to get preferences", "error", err, "employee_id", user.ID)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to retrieve preferences"})
		return
	}
	if prefs == nil {
		prefs = []*database.EmployeePreference{}
	}

	// Get user roles
	roles, err := h.userRolesStore.GetUserRoles(user.ID, user.OrganizationID)
	if err != nil {
		h.Logger.Error("failed to get user roles", "error", err, "employee_id", user.ID)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to retrieve user roles"})
		return
	}
	if roles == nil {
		roles = []string{}
	}

	// Get user settings (max_hours, preferred_hours, max_consec_slots)
	fullUser, err := h.userStore.GetUserByID(user.ID)
	if err != nil {
		h.Logger.Error("failed to get user details", "error", err, "employee_id", user.ID)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to retrieve user details"})
		return
	}

	response := PreferencesResponse{
		DayPreferences:        prefs,
		UserRoles:             roles,
		MaxHoursPerWeek:       fullUser.MaxHoursPerWeek,
		PreferredHoursPerWeek: fullUser.PreferredHoursPerWeek,
		MaxConsecSlots:        fullUser.MaxConsecSlots,
	}

	h.Logger.Info("preferences retrieved", "employee_id", user.ID, "day_count", len(prefs), "roles_count", len(roles))
	c.JSON(http.StatusOK, gin.H{
		"message": "Preferences retrieved successfully",
		"data":    response,
	})
}

// UpdateCurrentEmployeePreferences godoc
// @Summary      Update current employee preferences
// @Description  Creates or updates the work preferences of the currently authenticated employee for multiple days
// @Tags         Preferences
// @Accept       json
// @Produce      json
// @Security     BearerAuth
// @Param        org path string true "Organization ID"
// @Param        preferences body PreferencesRequest true "Preferences data with array of day preferences"
// @Success      200 {object} map[string]interface{} "Preferences updated successfully"
// @Failure      400 {object} map[string]string "Invalid request body"
// @Failure      401 {object} map[string]string "Unauthorized"
// @Failure      403 {object} map[string]string "Access denied"
// @Failure      500 {object} map[string]string "Internal server error"
// @Router       /{org}/preferences [post]
func (h *PreferencesHandler) UpdateCurrentEmployeePreferences(c *gin.Context) {
	h.Logger.Info("update current employee preferences request received")

	user := middleware.ValidateOrgAccess(c)
	if user == nil {
		return
	}

	var req PreferencesRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		h.Logger.Warn("invalid request body", "error", err)
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid request body: " + err.Error()})
		return
	}

	// Validate all days and check for duplicates
	seenDays := make(map[string]bool)
	for _, dayPref := range req.Preferences {
		if !database.IsValidDay(dayPref.Day) {
			h.Logger.Warn("invalid day", "day", dayPref.Day)
			c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid day: " + dayPref.Day + ". Valid days are: Sunday, Monday, Tuesday, Wednesday, Thursday, Friday, Saturday"})
			return
		}
		if seenDays[dayPref.Day] {
			h.Logger.Warn("duplicate day in request", "day", dayPref.Day)
			c.JSON(http.StatusBadRequest, gin.H{"error": "Duplicate day in request: " + dayPref.Day})
			return
		}
		seenDays[dayPref.Day] = true
	}

	// Convert request to database models
	prefs := make([]*database.EmployeePreference, len(req.Preferences))
	for i, dayPref := range req.Preferences {
		prefs[i] = &database.EmployeePreference{
			EmployeeID:         user.ID,
			Day:                dayPref.Day,
			PreferredStartTime: dayPref.PreferredStartTime,
			PreferredEndTime:   dayPref.PreferredEndTime,
			AvailableStartTime: dayPref.AvailableStartTime,
			AvailableEndTime:   dayPref.AvailableEndTime,
		}
	}

	// Use upsert to handle both create and update scenarios
	if err := h.preferencesStore.UpsertPreferences(user.ID, prefs); err != nil {
		h.Logger.Error("failed to save preferences", "error", err, "employee_id", user.ID)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to save day preferences"})
		return
	}

	// Update user roles if provided
	if len(req.UserRoles) > 0 {
		// Validate that all roles exist in the organization
		orgRoles, err := h.rolesStore.GetRolesByOrganizationID(user.OrganizationID)
		if err != nil {
			h.Logger.Error("failed to get organization roles", "error", err, "organization_id", user.OrganizationID)
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to validate roles"})
			return
		}

		validRoles := make(map[string]bool)
		for _, role := range orgRoles {
			validRoles[role.Role] = true
		}

		for _, role := range req.UserRoles {
			if !validRoles[role] {
				h.Logger.Warn("invalid role in request", "role", role, "organization_id", user.OrganizationID)
				c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid role: " + role + ". Role does not exist in this organization."})
				return
			}
		}

		if err := h.userRolesStore.SetUserRoles(user.ID, user.OrganizationID, req.UserRoles); err != nil {
			h.Logger.Error("failed to save user roles", "error", err, "employee_id", user.ID)
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to save user roles"})
			return
		}
	}

	// Update user settings (max_hours, preferred_hours, max_consec_slots) if any provided
	if req.MaxHoursPerWeek != nil || req.PreferredHoursPerWeek != nil || req.MaxConsecSlots != nil {
		// Get current user to update
		fullUser, err := h.userStore.GetUserByID(user.ID)
		if err != nil {
			h.Logger.Error("failed to get user for update", "error", err, "employee_id", user.ID)
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to update user settings"})
			return
		}

		// Update only provided fields
		if req.MaxHoursPerWeek != nil {
			fullUser.MaxHoursPerWeek = req.MaxHoursPerWeek
		}
		if req.PreferredHoursPerWeek != nil {
			fullUser.PreferredHoursPerWeek = req.PreferredHoursPerWeek
		}
		if req.MaxConsecSlots != nil {
			fullUser.MaxConsecSlots = req.MaxConsecSlots
		}

		if err := h.userStore.UpdateUser(fullUser); err != nil {
			h.Logger.Error("failed to update user settings", "error", err, "employee_id", user.ID)
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to update user settings"})
			return
		}
	}

	h.Logger.Info("preferences saved", "employee_id", user.ID, "day_count", len(prefs))
	c.JSON(http.StatusOK, gin.H{
		"message": "Preferences saved successfully",
	})
}
