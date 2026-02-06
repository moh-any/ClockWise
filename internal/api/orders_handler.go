package api

import (
	"log/slog"

	"github.com/gin-gonic/gin"
)

type OrderHandler struct {
	Logger *slog.Logger
}


func (oh *OrderHandler) GetAllOrders(c *gin.Context) {

}

func (oh * OrderHandler) GetAllOrdersForLastWeek(c *gin.Context) {
	
}

func (oh * OrderHandler) GetOrdersInsights(c *gin.Context) { 
	
}

func (oh * OrderHandler) UploadAllPastOrdersCSV(c *gin.Context) {

}

func (oh * OrderHandler) UploadOrderItemsCSV(c *gin.Context) {

}