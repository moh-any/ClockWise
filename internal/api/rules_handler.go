package api

import (
	"log/slog"
	"net/http"

	"github.com/clockwise/clockwise/backend/internal/database"
	"github.com/clockwise/clockwise/backend/internal/middleware"
	"github.com/gin-gonic/gin"
)

// RulesHandler handles organization rules-related HTTP requests
type RulesHandler struct {
	rulesStore database.RulesStore
	Logger     *slog.Logger
}

// NewRulesHandler creates a new RulesHandler
func NewRulesHandler(rulesStore database.RulesStore, logger *slog.Logger) *RulesHandler {
	return &RulesHandler{
		rulesStore: rulesStore,
		Logger:     logger,
	}
}

// RulesRequest represents the request body for creating/updating organization rules
type RulesRequest struct {
	ShiftMaxHours  int `json:"shift_max_hours" binding:"required,min=1"`
	ShiftMinHours  int `json:"shift_min_hours" binding:"required,min=1"`
	MaxWeeklyHours int `json:"max_weekly_hours" binding:"required,min=1"`
	MinWeeklyHours int `json:"min_weekly_hours" binding:"required,min=1"`
}

// GetOrganizationRules godoc
// @Summary      Get organization rules
// @Description  Returns the scheduling rules for the organization. Only admins and managers can access this.
// @Tags         Rules
// @Accept       json
// @Produce      json
// @Security     BearerAuth
// @Param        org path string true "Organization ID"
// @Success      200 {object} database.OrganizationRules "Organization rules"
// @Success      204 "No rules set"
// @Failure      401 {object} map[string]string "Unauthorized"
// @Failure      403 {object} map[string]string "Access denied"
// @Failure      500 {object} map[string]string "Internal server error"
// @Router       /{org}/rules [get]
func (h *RulesHandler) GetOrganizationRules(c *gin.Context) {
	h.Logger.Info("get organization rules request received")

	user := middleware.ValidateOrgAccess(c)
	if user == nil {
		return
	}

	// Only admins and managers can view rules
	if user.UserRole != "admin" && user.UserRole != "manager" {
		h.Logger.Warn("forbidden access to rules", "user_id", user.ID, "role", user.UserRole)
		c.JSON(http.StatusForbidden, gin.H{"error": "Only admins and managers can view organization rules"})
		return
	}

	rules, err := h.rulesStore.GetRulesByOrganizationID(user.OrganizationID)
	if err != nil {
		h.Logger.Error("failed to get rules", "error", err, "organization_id", user.OrganizationID)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to retrieve rules"})
		return
	}

	if rules == nil {
		h.Logger.Info("no rules found for organization", "organization_id", user.OrganizationID)
		c.JSON(http.StatusOK, gin.H{
			"message": "No rules set",
			"data":    nil,
		})
		return
	}

	h.Logger.Info("rules retrieved", "organization_id", user.OrganizationID)
	c.JSON(http.StatusOK, gin.H{
		"message": "Rules retrieved successfully",
		"data":    rules,
	})
}

// UpdateOrganizationRules godoc
// @Summary      Update organization rules
// @Description  Creates or updates the scheduling rules for the organization. Only admins can modify rules.
// @Tags         Rules
// @Accept       json
// @Produce      json
// @Security     BearerAuth
// @Param        org path string true "Organization ID"
// @Param        rules body RulesRequest true "Rules data"
// @Success      200 {object} map[string]interface{} "Rules updated successfully"
// @Failure      400 {object} map[string]string "Invalid request body"
// @Failure      401 {object} map[string]string "Unauthorized"
// @Failure      403 {object} map[string]string "Access denied - admins only"
// @Failure      500 {object} map[string]string "Internal server error"
// @Router       /{org}/rules [post]
func (h *RulesHandler) UpdateOrganizationRules(c *gin.Context) {
	h.Logger.Info("update organization rules request received")

	user := middleware.ValidateOrgAccess(c)
	if user == nil {
		return
	}

	// Only admins can update rules
	if user.UserRole != "admin" {
		h.Logger.Warn("forbidden attempt to update rules", "user_id", user.ID, "role", user.UserRole)
		c.JSON(http.StatusForbidden, gin.H{"error": "Only admins can update organization rules"})
		return
	}

	var req RulesRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		h.Logger.Warn("invalid request body", "error", err)
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid request body: " + err.Error()})
		return
	}

	// Validate that min values don't exceed max values
	if req.ShiftMinHours > req.ShiftMaxHours {
		h.Logger.Warn("shift min hours exceed max hours",
			"min", req.ShiftMinHours,
			"max", req.ShiftMaxHours)
		c.JSON(http.StatusBadRequest, gin.H{"error": "Shift minimum hours cannot exceed shift maximum hours"})
		return
	}

	if req.MinWeeklyHours > req.MaxWeeklyHours {
		h.Logger.Warn("weekly min hours exceed max hours",
			"min", req.MinWeeklyHours,
			"max", req.MaxWeeklyHours)
		c.JSON(http.StatusBadRequest, gin.H{"error": "Minimum weekly hours cannot exceed maximum weekly hours"})
		return
	}

	// Validate that shift max doesn't exceed weekly max
	if req.ShiftMaxHours > req.MaxWeeklyHours {
		h.Logger.Warn("shift max hours exceed weekly max hours",
			"shift_max", req.ShiftMaxHours,
			"weekly_max", req.MaxWeeklyHours)
		c.JSON(http.StatusBadRequest, gin.H{"error": "Shift maximum hours cannot exceed maximum weekly hours"})
		return
	}

	rules := &database.OrganizationRules{
		OrganizationID: user.OrganizationID,
		ShiftMaxHours:  req.ShiftMaxHours,
		ShiftMinHours:  req.ShiftMinHours,
		MaxWeeklyHours: req.MaxWeeklyHours,
		MinWeeklyHours: req.MinWeeklyHours,
	}

	// Use upsert to handle both create and update scenarios
	if err := h.rulesStore.UpsertRules(rules); err != nil {
		h.Logger.Error("failed to save rules", "error", err, "organization_id", user.OrganizationID)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to save rules"})
		return
	}

	h.Logger.Info("rules saved", "organization_id", user.OrganizationID)
	c.JSON(http.StatusOK, gin.H{
		"message": "Rules saved successfully",
		"data":    rules,
	})
}
