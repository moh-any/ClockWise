package api

import (
	"log/slog"

	"github.com/gin-gonic/gin"
)

type ScheduleHandler struct {
	Logger *slog.Logger
}

type SchedulePredictRequest struct {
	Place Place `json:"place"`
	ScheduleInput 
}

type ScheduleInput struct {
	
}

func NewScheduleHandler(logger *slog.Logger) *ScheduleHandler {
	return &ScheduleHandler{
		Logger: logger,
	}
}

func (sh *ScheduleHandler) GetScheduleHandler(c *gin.Context) {

}

func (sh *ScheduleHandler) PredictScheduleHandler(c *gin.Context) {

}

func (sh *ScheduleHandler) GetEmployeeScheduleHandler(c *gin.Context) {

}
