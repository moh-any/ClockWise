package api

import (
	"log/slog"

	"github.com/clockwise/clockwise/backend/internal/database"
	"github.com/gin-gonic/gin"
)

type InsightHandler struct {
	InsightsStore database.InsightStore
	Logger *slog.Logger
}

func (ih *InsightHandler) GetInsightsHandler(c *gin.Context) {
	
}