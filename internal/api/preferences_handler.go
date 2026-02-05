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
	Logger           *slog.Logger
}

// NewPreferencesHandler creates a new PreferencesHandler
func NewPreferencesHandler(preferencesStore database.PreferencesStore, logger *slog.Logger) *PreferencesHandler {
	return &PreferencesHandler{
		preferencesStore: preferencesStore,
		Logger:           logger,
	}
}

// PreferencesRequest represents the request body for creating/updating preferences
type PreferencesRequest struct {
	PreferredStartTime   string `json:"preferred_start_time" binding:"required"`
	PreferredEndTime     string `json:"preferred_end_time" binding:"required"`
	AvailableStartTime   string `json:"available_start_time" binding:"required"`
	AvailableEndTime     string `json:"available_end_time" binding:"required"`
	PreferredDaysPerWeek int    `json:"preferred_days_per_week" binding:"required,min=1,max=7"`
	AvailableDaysPerWeek int    `json:"available_days_per_week" binding:"required,min=1,max=7"`
}

// GetCurrentEmployeePreferences godoc
// @Summary      Get current employee preferences
// @Description  Returns the work preferences of the currently authenticated employee
// @Tags         Preferences
// @Accept       json
// @Produce      json
// @Security     BearerAuth
// @Param        org path string true "Organization ID"
// @Success      200 {object} database.Preferences "Employee preferences"
// @Success      204 "No preferences set"
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

	prefs, err := h.preferencesStore.GetPreferencesByEmployeeID(user.ID)
	if err != nil {
		h.Logger.Error("failed to get preferences", "error", err, "employee_id", user.ID)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to retrieve preferences"})
		return
	}

	if prefs == nil {
		h.Logger.Info("no preferences found for employee", "employee_id", user.ID)
		c.JSON(http.StatusOK, gin.H{
			"message": "No preferences set",
			"data":    nil,
		})
		return
	}

	h.Logger.Info("preferences retrieved", "employee_id", user.ID)
	c.JSON(http.StatusOK, gin.H{
		"message": "Preferences retrieved successfully",
		"data":    prefs,
	})
}

// UpdateCurrentEmployeePreferences godoc
// @Summary      Update current employee preferences
// @Description  Creates or updates the work preferences of the currently authenticated employee
// @Tags         Preferences
// @Accept       json
// @Produce      json
// @Security     BearerAuth
// @Param        org path string true "Organization ID"
// @Param        preferences body PreferencesRequest true "Preferences data"
// @Success      200 {object} map[string]interface{} "Preferences updated successfully"
// @Success      201 {object} map[string]interface{} "Preferences created successfully"
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

	// Validate that preferred days don't exceed available days
	if req.PreferredDaysPerWeek > req.AvailableDaysPerWeek {
		h.Logger.Warn("preferred days exceed available days",
			"preferred", req.PreferredDaysPerWeek,
			"available", req.AvailableDaysPerWeek)
		c.JSON(http.StatusBadRequest, gin.H{"error": "Preferred days per week cannot exceed available days per week"})
		return
	}

	prefs := &database.Preferences{
		EmployeeID:           user.ID,
		OrganizationID:       user.OrganizationID,
		PreferredStartTime:   req.PreferredStartTime,
		PreferredEndTime:     req.PreferredEndTime,
		AvailableStartTime:   req.AvailableStartTime,
		AvailableEndTime:     req.AvailableEndTime,
		PreferredDaysPerWeek: req.PreferredDaysPerWeek,
		AvailableDaysPerWeek: req.AvailableDaysPerWeek,
	}

	// Use upsert to handle both create and update scenarios
	if err := h.preferencesStore.UpsertPreferences(prefs); err != nil {
		h.Logger.Error("failed to save preferences", "error", err, "employee_id", user.ID)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to save preferences"})
		return
	}

	h.Logger.Info("preferences saved", "employee_id", user.ID)
	c.JSON(http.StatusOK, gin.H{
		"message": "Preferences saved successfully",
		"data":    prefs,
	})
}
