package api

import (
	"log/slog"
	"net/http"
	"time"

	"github.com/clockwise/clockwise/backend/internal/database"
	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
)

type SurgeHandler struct {
	surgeStore database.SurgeStore
	Logger     *slog.Logger
}

func NewSurgeHandler(surgeStore database.SurgeStore, logger *slog.Logger) *SurgeHandler {
	return &SurgeHandler{
		surgeStore: surgeStore,
		Logger:     logger,
	}
}

type BulkDataRequest struct {
	PlaceID         int       `json:"place_id"` // Mapped to OrgID via lookup or assumes int ID (using UUID for ClockWise)
	OrgID           string    `json:"org_id"`   // Direct UUID support for ClockWise
	Timestamp       time.Time `json:"timestamp"`
	TimeWindowHours int       `json:"time_window_hours"`
}

func (h *SurgeHandler) GetBulkSurgeData(c *gin.Context) {
	var req BulkDataRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid request body"})
		return
	}

	// Use OrgID if provided, otherwise fail (ClockWise uses UUIDs)
	orgID, err := uuid.Parse(req.OrgID)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid organization UUID"})
		return
	}

	endTime := req.Timestamp
	if endTime.IsZero() {
		endTime = time.Now()
	}
	startTime := endTime.Add(-time.Duration(req.TimeWindowHours) * time.Hour)

	// Fetch Data Parallel-ish (sequential for simplicity first)
	venue, err := h.surgeStore.GetVenueDetails(orgID)
	if err != nil {
		h.Logger.Error("Failed to get venue details", "error", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Internal server error"})
		return
	}

	campaigns, err := h.surgeStore.GetActiveCampaigns(orgID)
	if err != nil {
		h.Logger.Error("Failed to get campaigns", "error", err)
		// Continue with empty stats
		campaigns = &database.CampaignStats{}
	}

	orders, err := h.surgeStore.GetHistoricalOrders(orgID, startTime, endTime)
	if err != nil {
		h.Logger.Error("Failed to get orders", "error", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Internal server error"})
		return
	}

	predictions, err := h.surgeStore.GetDemandPredictions(orgID, startTime, endTime)
	if err != nil {
		h.Logger.Error("Failed to get predictions", "error", err)
		// Continue with empty predictions
		predictions = []database.PredictionAggregate{}
	}

	// Format Response
	ordersMap := make(map[string]map[string]int)
	for _, o := range orders {
		ordersMap[o.Timestamp.Format(time.RFC3339)] = map[string]int{
			"order_count": o.OrderCount,
			"item_count":  o.ItemCount,
		}
	}

	predsMap := make(map[string]map[string]float64)
	for _, p := range predictions {
		predsMap[p.Timestamp.Format(time.RFC3339)] = map[string]float64{
			"item_count_pred":  p.ItemCountPred,
			"order_count_pred": p.OrderCountPred,
		}
	}

	response := gin.H{
		"place_id":    req.PlaceID, // Echo back
		"org_id":      req.OrgID,
		"timestamp":   endTime.Format(time.RFC3339),
		"venue":       venue,
		"campaigns":   campaigns,
		"orders":      ordersMap,
		"predictions": predsMap,
	}

	c.JSON(http.StatusOK, response)
}

func (h *SurgeHandler) GetSurgeUsers(c *gin.Context) {
	orgIDStr := c.Query("org_id")
	if orgIDStr == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "org_id query parameter required"})
		return
	}

	orgID, err := uuid.Parse(orgIDStr)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid organization UUID"})
		return
	}

	emails, err := h.surgeStore.GetManagerAndAdminEmails(orgID)
	if err != nil {
		h.Logger.Error("Failed to get user emails", "error", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Internal server error"})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"org_id": orgIDStr,
		"emails": emails,
	})
}

func (h *SurgeHandler) GetActiveVenues(c *gin.Context) {
	venues, err := h.surgeStore.GetActiveVenues()
	if err != nil {
		h.Logger.Error("Failed to get active venues", "error", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Internal server error"})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"venues": venues,
	})
}
