package api

import (
	"log/slog"
	"net/http"

	"github.com/clockwise/clockwise/backend/internal/database"
	"github.com/clockwise/clockwise/backend/internal/middleware"
	"github.com/gin-gonic/gin"
)

type InsightHandler struct {
	InsightsStore database.InsightStore
	Logger        *slog.Logger
}


func NewInsightHandler(insightStore database.InsightStore, logger *slog.Logger) *InsightHandler {
	return &InsightHandler{
		InsightsStore:    insightStore,
		Logger:       logger,
	}
}
// GetInsightsHandler godoc
func (ih *InsightHandler) GetInsightsHandler(c *gin.Context) {
	// Get The insights depending on the current user role admin, manager or anyone else (employee)
	user := middleware.ValidateOrgAccess(c)
	if user == nil {
		c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error":"invalid user in context"})
		return
	}

	ih.Logger.Info("getting insights for user", "user_id", user.ID, "role", user.UserRole)

	var insights []database.Insight
	var err error

	switch user.UserRole {
	case "admin":
		insights, err = ih.InsightsStore.GetInsightsForAdmin(user.OrganizationID)
	case "manager":
		insights, err = ih.InsightsStore.GetInsightsForManager(user.OrganizationID, user.ID)
	case "employee":
		// Any other role is treated as employee
		insights, err = ih.InsightsStore.GetInsightsForEmployee(user.OrganizationID, user.ID)
	}

	// TODO: Add Current Demand State from API

	if err != nil {
		ih.Logger.Error("failed to get insights", "error", err, "user_id", user.ID, "role", user.UserRole)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to retrieve insights"})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"message": "Insights retrieved successfully",
		"data":    insights,
	})
}
