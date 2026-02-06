package api

import (
	"log/slog"
	"time"

	"github.com/gin-gonic/gin"
)

type DashboardHandler struct {
	Logger *slog.Logger
}

func NewDashboardHandler(Logger *slog.Logger) *DashboardHandler{
	return &DashboardHandler{
		Logger: Logger,
	}
}

type DemandPredictionRequest struct {
	PredicationStartDate time.Time `json:"prediction_start_date"`
	PredictionDays       int       `json:"prediction_days"`
}


// Demand is auto generated every day and store in the database -> Background Tasks

func (dh *DashboardHandler) GetDashboardHandler(c *gin.Context) {

}

func (dh *DashboardHandler) GetDemandHeatMapHandler(c *gin.Context) {

}

func (dh *DashboardHandler) RefreshDemandHeatMapHandler(c * gin.Context) {

}
