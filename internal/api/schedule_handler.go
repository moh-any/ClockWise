package api

import (
	"log/slog"

	"github.com/gin-gonic/gin"
)

type ScheduleHandler struct {
	Logger *slog.Logger
}

type ScheduleRefreshRequest struct {
}

func NewScheduleHandler(logger *slog.Logger) *ScheduleHandler {
	return &ScheduleHandler{
		Logger: logger,
	}
}

func (sh *ScheduleHandler) GetScheduleHandler(c *gin.Context) {

}

func (sh *ScheduleHandler) RefreshScheduleHandler(c *gin.Context) {

}

func (sh *ScheduleHandler) GetEmployeeScheduleHandler(c *gin.Context) {

}
