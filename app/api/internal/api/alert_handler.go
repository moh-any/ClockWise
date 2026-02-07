package api

import (
	"log/slog"
	"net/http"

	"github.com/clockwise/clockwise/backend/internal/database"
	"github.com/clockwise/clockwise/backend/internal/middleware"
	"github.com/gin-gonic/gin"
)

type AlertHandler struct {
	database.AlertStore
	Logger *slog.Logger
}

func NewAlertHandler(alertStore database.AlertStore, Logger *slog.Logger) *AlertHandler {
	return &AlertHandler{
		AlertStore: alertStore,
		Logger:     Logger,
	}
}

func (ah *AlertHandler) GetAllAlertsHandler(c *gin.Context) {
	user := middleware.ValidateOrgAccess(c)
	if user == nil {
		return
	}

	if user.UserRole != "admin" && user.UserRole != "manager" {
		c.JSON(http.StatusForbidden, gin.H{"error": "Access denied"})
		return
	}

	alerts, err := ah.AlertStore.GetAllAlerts(user.OrganizationID)
	if err != nil {
		ah.Logger.Error("Failed to get all alerts", "error", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to retrieve alerts"})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"message": "Alerts retrieved successfully",
		"data":    alerts,
	})
}

func (ah *AlertHandler) GetAllAlertsForLastWeekHandler(c *gin.Context) {
	user := middleware.ValidateOrgAccess(c)
	if user == nil {
		return
	}

	if user.UserRole != "admin" && user.UserRole != "manager" {
		c.JSON(http.StatusForbidden, gin.H{"error": "Access denied"})
		return
	}

	alerts, err := ah.AlertStore.GetAllAlertsForLastWeek(user.OrganizationID)
	if err != nil {
		ah.Logger.Error("Failed to get alerts for last week", "error", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to retrieve alerts"})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"message": "Alerts for last week retrieved successfully",
		"data":    alerts,
	})
}

func (ah *AlertHandler) GetAlertInsightsHandler(c *gin.Context) {
	user := middleware.ValidateOrgAccess(c)
	if user == nil {
		return
	}

	if user.UserRole != "admin" && user.UserRole != "manager" {
		c.JSON(http.StatusForbidden, gin.H{"error": "Access denied"})
		return
	}

	insights, err := ah.AlertStore.GetAlertInsights(user.OrganizationID)
	if err != nil {
		ah.Logger.Error("Failed to get alert insights", "error", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to retrieve alert insights"})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"message": "Alert insights retrieved successfully",
		"data":    insights,
	})
}
