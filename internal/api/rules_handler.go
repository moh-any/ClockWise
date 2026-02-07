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
	rulesStore          database.RulesStore
	operatingHoursStore database.OperatingHoursStore
	Logger              *slog.Logger
}

// NewRulesHandler creates a new RulesHandler
func NewRulesHandler(rulesStore database.RulesStore, operatingHoursStore database.OperatingHoursStore, logger *slog.Logger) *RulesHandler {
	return &RulesHandler{
		rulesStore:          rulesStore,
		operatingHoursStore: operatingHoursStore,
		Logger:              logger,
	}
}

// OperatingHoursRequest represents a single day's operating hours in a request
type OperatingHoursRequest struct {
	Weekday     string `json:"weekday" binding:"required"`
	OpeningTime string `json:"opening_time" binding:"required"`
	ClosingTime string `json:"closing_time" binding:"required"`
}

// RulesRequest represents the request body for creating/updating organization rules
type RulesRequest struct {
	ShiftMaxHours        int                     `json:"shift_max_hours" binding:"required,min=1"`
	ShiftMinHours        int                     `json:"shift_min_hours" binding:"required,min=1"`
	MaxWeeklyHours       int                     `json:"max_weekly_hours" binding:"required,min=1"`
	MinWeeklyHours       int                     `json:"min_weekly_hours" binding:"required,min=1"`
	FixedShifts          bool                    `json:"fixed_shifts"`
	NumberOfShiftsPerDay *int                    `json:"number_of_shifts_per_day"`
	MeetAllDemand        bool                    `json:"meet_all_demand"`
	MinRestSlots         int                     `json:"min_rest_slots" binding:"required,min=0"`
	SlotLenHour          float64                 `json:"slot_len_hour" binding:"required,gt=0"`
	MinShiftLengthSlots  int                     `json:"min_shift_length_slots" binding:"required,min=1"`
	OperatingHours       []OperatingHoursRequest `json:"operating_hours" binding:"max=7,dive"`
	ShiftTimes           []database.ShiftTime    `json:"shift_times,omitempty"` // Only if fixed
}

// RulesResponse represents the response for rules GET
type RulesResponse struct {
	Rules          *database.OrganizationRules `json:"rules"`
	OperatingHours []*database.OperatingHours  `json:"operating_hours"`
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

	// Get operating hours
	operatingHours, err := h.operatingHoursStore.GetOperatingHours(user.OrganizationID)
	if err != nil {
		h.Logger.Error("failed to get operating hours", "error", err, "organization_id", user.OrganizationID)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to retrieve operating hours"})
		return
	}
	if operatingHours == nil {
		operatingHours = []*database.OperatingHours{}
	}

	if rules == nil {
		h.Logger.Info("no rules found for organization", "organization_id", user.OrganizationID)
		c.JSON(http.StatusOK, gin.H{
			"message": "No rules set",
			"data": RulesResponse{
				Rules:          nil,
				OperatingHours: operatingHours,
			},
		})
		return
	}

	response := RulesResponse{
		Rules:          rules,
		OperatingHours: operatingHours,
	}

	h.Logger.Info("rules retrieved", "organization_id", user.OrganizationID)
	c.JSON(http.StatusOK, gin.H{
		"message": "Rules retrieved successfully",
		"data":    response,
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

	// Validate fixed_shifts constraint: if fixed_shifts is true, number_of_shifts_per_day is required
	if req.FixedShifts {
		if req.NumberOfShiftsPerDay == nil || *req.NumberOfShiftsPerDay <= 0 {
			h.Logger.Warn("number_of_shifts_per_day required when fixed_shifts is true")
			c.JSON(http.StatusBadRequest, gin.H{"error": "number_of_shifts_per_day must be > 0 when fixed_shifts is true"})
			return
		}
		// Validate shift_times if provided
		if len(req.ShiftTimes) > 0 && len(req.ShiftTimes) != *req.NumberOfShiftsPerDay {
			h.Logger.Warn("shift_times count mismatch", "provided", len(req.ShiftTimes), "expected", *req.NumberOfShiftsPerDay)
			c.JSON(http.StatusBadRequest, gin.H{"error": "shift_times count must match number_of_shifts_per_day"})
			return
		}
	} else {
		// If not fixed_shifts, number_of_shifts_per_day should be NULL and shift_times should be empty
		req.NumberOfShiftsPerDay = nil
		req.ShiftTimes = nil
	}

	rules := &database.OrganizationRules{
		OrganizationID:       user.OrganizationID,
		ShiftMaxHours:        req.ShiftMaxHours,
		ShiftMinHours:        req.ShiftMinHours,
		MaxWeeklyHours:       req.MaxWeeklyHours,
		MinWeeklyHours:       req.MinWeeklyHours,
		FixedShifts:          req.FixedShifts,
		NumberOfShiftsPerDay: req.NumberOfShiftsPerDay,
		MeetAllDemand:        req.MeetAllDemand,
		MinRestSlots:         req.MinRestSlots,
		SlotLenHour:          req.SlotLenHour,
		MinShiftLengthSlots:  req.MinShiftLengthSlots,
		ShiftTimes:           req.ShiftTimes,
	}

	// Use upsert to handle both create and update scenarios
	if err := h.rulesStore.UpsertRules(rules); err != nil {
		h.Logger.Error("failed to save rules", "error", err, "organization_id", user.OrganizationID)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to save rules"})
		return
	}

	// Save operating hours if provided
	if len(req.OperatingHours) > 0 {
		// Validate weekdays and check for duplicates
		seenDays := make(map[string]bool)
		for _, oh := range req.OperatingHours {
			if !database.IsValidDay(oh.Weekday) {
				h.Logger.Warn("invalid weekday in operating hours", "weekday", oh.Weekday)
				c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid weekday: " + oh.Weekday})
				return
			}
			if seenDays[oh.Weekday] {
				h.Logger.Warn("duplicate weekday in operating hours", "weekday", oh.Weekday)
				c.JSON(http.StatusBadRequest, gin.H{"error": "Duplicate weekday in operating hours: " + oh.Weekday})
				return
			}
			seenDays[oh.Weekday] = true
		}

		// Convert to database models
		operatingHours := make([]*database.OperatingHours, len(req.OperatingHours))
		for i, oh := range req.OperatingHours {
			operatingHours[i] = &database.OperatingHours{
				OrganizationID: user.OrganizationID,
				Weekday:        oh.Weekday,
				OpeningTime:    oh.OpeningTime,
				ClosingTime:    oh.ClosingTime,
			}
		}

		if err := h.operatingHoursStore.SetOperatingHours(user.OrganizationID, operatingHours); err != nil {
			h.Logger.Error("failed to save operating hours", "error", err, "organization_id", user.OrganizationID)
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to save operating hours"})
			return
		}
	}

	// Always fetch current operating hours for response
	currentOperatingHours, err := h.operatingHoursStore.GetOperatingHours(user.OrganizationID)
	if err != nil {
		h.Logger.Error("failed to get operating hours for response", "error", err, "organization_id", user.OrganizationID)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to retrieve operating hours"})
		return
	}
	if currentOperatingHours == nil {
		currentOperatingHours = []*database.OperatingHours{}
	}

	response := RulesResponse{
		Rules:          rules,
		OperatingHours: currentOperatingHours,
	}

	h.Logger.Info("rules saved", "organization_id", user.OrganizationID)
	c.JSON(http.StatusOK, gin.H{
		"message": "Rules saved successfully",
		"data":    response,
	})
}
