package api

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"log/slog"
	"net/http"
	"strconv"
	"time"

	"github.com/clockwise/clockwise/backend/internal/database"
	"github.com/clockwise/clockwise/backend/internal/middleware"
	"github.com/clockwise/clockwise/backend/internal/service"
	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
)

type CampaignHandler struct {
	CampaignStore       database.CampaignStore
	UploadCSVService    service.UploadService
	OrderStore          database.OrderStore
	OrgStore            database.OrgStore
	OperatingHoursStore database.OperatingHoursStore
	RulesStore          database.RulesStore
	Logger              *slog.Logger
	MLServiceURL        string
}

func NewCampaignHandler(campaignStore database.CampaignStore, uploadservice service.UploadService, orderStore database.OrderStore, orgStore database.OrgStore, operatingHoursStore database.OperatingHoursStore, rulesStore database.RulesStore, Logger *slog.Logger) *CampaignHandler {
	return &CampaignHandler{
		CampaignStore:       campaignStore,
		UploadCSVService:    uploadservice,
		OrderStore:          orderStore,
		OrgStore:            orgStore,
		OperatingHoursStore: operatingHoursStore,
		RulesStore:          rulesStore,
		Logger:              Logger,
		MLServiceURL:        "http://cw-ml-service:8000",
	}
}

// Campaign Recommendation Request/Response Structures
type RecommendCampaignRequest struct {
	RecommendationStartDate string   `json:"recommendation_start_date" binding:"required"`
	NumRecommendations      int      `json:"num_recommendations"`
	OptimizeFor             string   `json:"optimize_for"`
	MaxDiscount             float64  `json:"max_discount"`
	MinCampaignDurationDays int      `json:"min_campaign_duration_days"`
	MaxCampaignDurationDays int      `json:"max_campaign_duration_days"`
	AvailableItems          []string `json:"available_items"`
}

type RecommendedCampaignItem struct {
	CampaignID            string         `json:"campaign_id"`
	Items                 []string       `json:"items"`
	DiscountPercentage    float64        `json:"discount_percentage"`
	StartDate             string         `json:"start_date"`
	EndDate               string         `json:"end_date"`
	DurationDays          int            `json:"duration_days"`
	ExpectedUplift        float64        `json:"expected_uplift"`
	ExpectedROI           float64        `json:"expected_roi"`
	ExpectedRevenue       float64        `json:"expected_revenue"`
	ConfidenceScore       float64        `json:"confidence_score"`
	Reasoning             string         `json:"reasoning"`
	PriorityScore         float64        `json:"priority_score"`
	RecommendedForContext map[string]any `json:"recommended_for_context"`
}

type CampaignRecommendationResponse struct {
	RestaurantName     string                    `json:"restaurant_name"`
	RecommendationDate string                    `json:"recommendation_date"`
	Recommendations    []RecommendedCampaignItem `json:"recommendations"`
	AnalysisSummary    map[string]any            `json:"analysis_summary"`
	Insights           map[string]any            `json:"insights"`
	ConfidenceLevel    string                    `json:"confidence_level"`
}

type CampaignFeedbackRequest struct {
	CampaignID    string   `json:"campaign_id" binding:"required"`
	ActualUplift  *float64 `json:"actual_uplift"`
	ActualROI     *float64 `json:"actual_roi"`
	ActualRevenue *float64 `json:"actual_revenue"`
	Success       bool     `json:"success"`
	Notes         *string  `json:"notes"`
}

type CampaignFeedbackResponse struct {
	Status            string         `json:"status"`
	Message           string         `json:"message"`
	UpdatedParameters map[string]any `json:"updated_parameters,omitempty"`
}

func (ch *CampaignHandler) UploadCampaignsCSVHandler(c *gin.Context) {
	user := middleware.ValidateOrgAccess(c)
	if user == nil {
		return
	}

	if user.UserRole != "admin" && user.UserRole != "manager" {
		c.JSON(http.StatusForbidden, gin.H{"error": "Only admins and managers can upload campaigns"})
		return
	}

	ch.Logger.Info("uploading campaigns CSV", "org_id", user.OrganizationID)

	// Get the file from the request
	file, _, err := c.Request.FormFile("file")
	if err != nil {
		ch.Logger.Error("failed to get file from request", "error", err)
		c.JSON(http.StatusBadRequest, gin.H{"error": "Failed to get file from request"})
		return
	}
	defer file.Close()

	// Parse the CSV file
	csvData, err := ch.UploadCSVService.ParseCSV(file)
	if err != nil {
		ch.Logger.Error("failed to parse CSV", "error", err)
		if err == service.ErrEmptyFile {
			c.JSON(http.StatusBadRequest, gin.H{"error": "CSV file is empty"})
			return
		}
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid CSV format"})
		return
	}

	// Expected columns: id, name, status, start_time, end_time, discount_percent
	requiredColumns := []string{"id", "name", "status", "start_time", "end_time"}
	for _, col := range requiredColumns {
		found := false
		for _, header := range csvData.Headers {
			if header == col {
				found = true
				break
			}
		}
		if !found {
			ch.Logger.Warn("missing required column", "column", col)
			c.JSON(http.StatusBadRequest, gin.H{"error": "Missing required column: " + col})
			return
		}
	}

	// Store each campaign from CSV
	var successCount, errorCount int
	for i, row := range csvData.Rows {
		// Parse campaign ID
		campaignID, err := uuid.Parse(row["id"])
		if err != nil {
			ch.Logger.Warn("invalid campaign id in row", "row", i, "error", err)
			errorCount++
			continue
		}

		// Parse start_time
		startTime, err := time.Parse(time.RFC3339, row["start_time"])
		if err != nil {
			// Try alternative format
			startTime, err = time.Parse("2006-01-02 15:04:05", row["start_time"])
			if err != nil {
				ch.Logger.Warn("invalid start_time in row", "row", i, "error", err)
				errorCount++
				continue
			}
		}

		// Parse end_time
		endTime, err := time.Parse(time.RFC3339, row["end_time"])
		if err != nil {
			// Try alternative format
			endTime, err = time.Parse("2006-01-02 15:04:05", row["end_time"])
			if err != nil {
				ch.Logger.Warn("invalid end_time in row", "row", i, "error", err)
				errorCount++
				continue
			}
		}

		// Parse discount_percent (optional)
		var discountPercent *float64
		if row["discount_percent"] != "" {
			d, err := strconv.ParseFloat(row["discount_percent"], 64)
			if err == nil {
				discountPercent = &d
			}
		}

		campaign := database.Campaign{
			ID:              campaignID,
			Name:            row["name"],
			Status:          row["status"],
			StartTime:       startTime.Format(time.RFC3339),
			EndTime:         endTime.Format(time.RFC3339),
			DiscountPercent: discountPercent,
		}

		err = ch.CampaignStore.StoreCampaign(user.OrganizationID, campaign)
		if err != nil {
			ch.Logger.Error("failed to store campaign", "row", i, "error", err)
			errorCount++
			continue
		}
		successCount++
	}

	c.JSON(http.StatusOK, gin.H{
		"message":       "Campaigns CSV uploaded successfully",
		"total_rows":    csvData.Total,
		"success_count": successCount,
		"error_count":   errorCount,
	})
}

func (ch *CampaignHandler) UploadCampaignsItemsCSVHandlers(c *gin.Context) {
	user := middleware.ValidateOrgAccess(c)
	if user == nil {
		return
	}

	if user.UserRole != "admin" && user.UserRole != "manager" {
		c.JSON(http.StatusForbidden, gin.H{"error": "Only admins and managers can upload campaign items"})
		return
	}

	ch.Logger.Info("uploading campaign items CSV", "org_id", user.OrganizationID)

	// Get the file from the request
	file, _, err := c.Request.FormFile("file")
	if err != nil {
		ch.Logger.Error("failed to get file from request", "error", err)
		c.JSON(http.StatusBadRequest, gin.H{"error": "Failed to get file from request"})
		return
	}
	defer file.Close()

	existingCampaigns, err := ch.CampaignStore.GetAllCampaigns(user.OrganizationID)
	if err != nil {
		ch.Logger.Error("failed to check existing campaigns", "error", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to verify existing campaigns"})
		return
	}
	if len(existingCampaigns) == 0 {
		c.JSON(http.StatusBadRequest, gin.H{"error": "You must import at least one campaign before uploading campaign items"})
		return
	}

	// Parse the CSV file
	csvData, err := ch.UploadCSVService.ParseCSV(file)
	if err != nil {
		ch.Logger.Error("failed to parse CSV", "error", err)
		if err == service.ErrEmptyFile {
			c.JSON(http.StatusBadRequest, gin.H{"error": "CSV file is empty"})
			return
		}
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid CSV format"})
		return
	}

	// Expected columns: campaign_id, item_id
	requiredColumns := []string{"campaign_id", "item_id"}
	for _, col := range requiredColumns {
		found := false
		for _, header := range csvData.Headers {
			if header == col {
				found = true
				break
			}
		}
		if !found {
			ch.Logger.Warn("missing required column", "column", col)
			c.JSON(http.StatusBadRequest, gin.H{"error": "Missing required column: " + col})
			return
		}
	}

	// Group items by campaign_id
	campaignItemsMap := make(map[uuid.UUID][]database.Item)
	for i, row := range csvData.Rows {
		// Parse campaign_id
		campaignID, err := uuid.Parse(row["campaign_id"])
		if err != nil {
			ch.Logger.Warn("invalid campaign_id in row", "row", i, "error", err)
			continue
		}

		// Parse item_id
		itemID, err := uuid.Parse(row["item_id"])
		if err != nil {
			ch.Logger.Warn("invalid item_id in row", "row", i, "error", err)
			continue
		}

		// Add item to the campaign's item list
		campaignItemsMap[campaignID] = append(campaignItemsMap[campaignID], database.Item{
			ItemID: itemID,
		})
	}

	// Store items for each campaign
	var successCount, errorCount int
	for campaignID, items := range campaignItemsMap {
		err := ch.CampaignStore.StoreCampaignItems(user.OrganizationID, campaignID, items)
		if err != nil {
			ch.Logger.Error("failed to store campaign items", "campaign_id", campaignID, "error", err)
			errorCount += len(items)
			continue
		}
		successCount += len(items)
	}

	c.JSON(http.StatusOK, gin.H{
		"message":       "Campaign items CSV uploaded successfully",
		"total_rows":    csvData.Total,
		"success_count": successCount,
		"error_count":   errorCount,
	})
}

func (ch *CampaignHandler) GetCampaignsInsightsHandler(c *gin.Context) {
	user := middleware.ValidateOrgAccess(c)
	if user == nil {
		return
	}

	if user.UserRole != "admin" && user.UserRole != "manager" {
		c.JSON(http.StatusForbidden, gin.H{"error": "Only admins and managers can access campaign insights"})
		return
	}

	ch.Logger.Info("getting campaign insights", "org_id", user.OrganizationID)

	insights, err := ch.CampaignStore.GetCampaignInsights(user.OrganizationID)
	if err != nil {
		ch.Logger.Error("failed to get campaign insights", "error", err, "org_id", user.OrganizationID)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to retrieve campaign insights"})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"message": "Campaign insights retrieved successfully",
		"data":    insights,
	})
}

func (ch *CampaignHandler) GetAllCampaignsHandler(c *gin.Context) {
	user := middleware.ValidateOrgAccess(c)
	if user == nil {
		return
	}

	if user.UserRole != "admin" && user.UserRole != "manager" {
		c.JSON(http.StatusForbidden, gin.H{"error": "Only admins and managers can access campaigns"})
		return
	}

	ch.Logger.Info("getting all campaigns", "org_id", user.OrganizationID)

	campaigns, err := ch.CampaignStore.GetAllCampaigns(user.OrganizationID)
	if err != nil {
		ch.Logger.Error("failed to get all campaigns", "error", err, "org_id", user.OrganizationID)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to retrieve campaigns"})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"message": "Campaigns retrieved successfully",
		"data":    campaigns,
	})
}

func (ch *CampaignHandler) GetAllCampaignsForLastWeekHandler(c *gin.Context) {
	user := middleware.ValidateOrgAccess(c)
	if user == nil {
		return
	}

	if user.UserRole != "admin" && user.UserRole != "manager" {
		c.JSON(http.StatusForbidden, gin.H{"error": "Only admins and managers can access campaigns"})
		return
	}

	ch.Logger.Info("getting campaigns for last week", "org_id", user.OrganizationID)

	campaigns, err := ch.CampaignStore.GetAllCampaignsFromLastWeek(user.OrganizationID)
	if err != nil {
		ch.Logger.Error("failed to get campaigns for last week", "error", err, "org_id", user.OrganizationID)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to retrieve campaigns"})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"message": "Campaigns retrieved successfully",
		"data":    campaigns,
	})
}

func (ch *CampaignHandler) RecommendCampaignsHandler(c *gin.Context) {
	user := middleware.ValidateOrgAccess(c)
	if user == nil {
		return
	}

	if user.UserRole != "admin" && user.UserRole != "manager" {
		c.JSON(http.StatusForbidden, gin.H{"error": "Only admins and managers can get campaign recommendations"})
		return
	}

	ch.Logger.Info("getting campaign recommendations", "org_id", user.OrganizationID)

	var request RecommendCampaignRequest
	if err := c.ShouldBindJSON(&request); err != nil {
		ch.Logger.Warn("invalid recommendation request", "error", err)
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// Set defaults
	if request.NumRecommendations == 0 {
		request.NumRecommendations = 5
	}
	if request.OptimizeFor == "" {
		request.OptimizeFor = "roi"
	}
	if request.MaxDiscount == 0 {
		request.MaxDiscount = 30.0
	}
	if request.MinCampaignDurationDays == 0 {
		request.MinCampaignDurationDays = 3
	}
	if request.MaxCampaignDurationDays == 0 {
		request.MaxCampaignDurationDays = 14
	}

	// Fetch organization data
	org, err := ch.OrgStore.GetOrganizationByID(user.OrganizationID)
	if err != nil {
		ch.Logger.Error("failed to get organization", "error", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to retrieve organization data"})
		return
	}

	// Fetch organization rules for delivery and phone settings
	rules, err := ch.RulesStore.GetRulesByOrganizationID(user.OrganizationID)
	if err != nil {
		ch.Logger.Error("failed to get organization rules", "error", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to retrieve organization rules"})
		return
	}

	// Fetch operating hours
	operatingHours, err := ch.OperatingHoursStore.GetOperatingHours(user.OrganizationID)
	if err != nil {
		ch.Logger.Warn("failed to get operating hours, using empty", "error", err)
		operatingHours = []database.OperatingHours{}  // Use empty if not found
	}

	// Fetch historical orders
	orders, err := ch.OrderStore.GetAllOrders(user.OrganizationID)
	if err != nil {
		ch.Logger.Error("failed to get orders", "error", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to retrieve historical orders"})
		return
	}

	// Fetch historical campaigns
	campaigns, err := ch.CampaignStore.GetAllCampaigns(user.OrganizationID)
	if err != nil {
		ch.Logger.Error("failed to get campaigns", "error", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to retrieve historical campaigns"})
		return
	}

	// Build ML service request
	// Handle nil latitude/longitude with defaults
	latitude := 0.0
	if org.Location.Latitude != nil {
		latitude = *org.Location.Latitude
	}
	longitude := 0.0
	if org.Location.Longitude != nil {
		longitude = *org.Location.Longitude
	}

	// Convert operating hours to map format for ML service
	operatingHoursMap := make(map[string]any)
	for _, hours := range operatingHours {
		operatingHoursMap[hours.Weekday] = map[string]any{
			"weekday":      hours.Weekday,
			"opening_time": hours.OpeningTime,
			"closing_time": hours.ClosingTime,
		}
	}

	// Handle nil number_of_shifts_per_day with default value
	numberOfShiftsPerDay := 3
	if rules.NumberOfShiftsPerDay != nil {
		numberOfShiftsPerDay = *rules.NumberOfShiftsPerDay
	}

	mlRequest := map[string]any{
		"place": map[string]any{
			"place_id":                 user.OrganizationID.String(),
			"place_name":               org.Name,
			"latitude":                 latitude,
			"longitude":                longitude,
			"type":                     org.Type,
			"delivery":                 rules.Delivery,
			"receiving_phone":          rules.ReceivingPhone,
			"opening_hours":            operatingHoursMap,
			"fixed_shifts":             rules.FixedShifts,
			"number_of_shifts_per_day": numberOfShiftsPerDay,
			"waiting_time":             rules.WaitingTime,
		},
		"orders":                     ch.convertOrdersForML(orders),
		"campaigns":                  ch.convertCampaignsForML(campaigns),
		"order_items":                ch.convertOrderItemsForML(orders),
		"recommendation_start_date":  request.RecommendationStartDate,
		"num_recommendations":        request.NumRecommendations,
		"optimize_for":               request.OptimizeFor,
		"max_discount":               request.MaxDiscount,
		"min_campaign_duration_days": request.MinCampaignDurationDays,
		"max_campaign_duration_days": request.MaxCampaignDurationDays,
		"available_items":            request.AvailableItems,
	}

	jsonData, err := json.Marshal(mlRequest)
	if err != nil {
		ch.Logger.Error("failed to marshal request", "error", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to prepare recommendation request"})
		return
	}

	// Call ML service
	client := &http.Client{Timeout: 60 * time.Second}
	resp, err := client.Post(
		fmt.Sprintf("%s/recommend/campaigns", ch.MLServiceURL),
		"application/json",
		bytes.NewBuffer(jsonData),
	)
	if err != nil {
		ch.Logger.Error("failed to call ML service", "error", err)
		c.JSON(http.StatusServiceUnavailable, gin.H{"error": "Campaign recommendation service unavailable"})
		return
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		ch.Logger.Error("failed to read ML response", "error", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to read recommendation response"})
		return
	}

	if resp.StatusCode != http.StatusOK {
		ch.Logger.Error("ML service error", "status", resp.StatusCode, "body", string(body))
		c.JSON(resp.StatusCode, gin.H{"error": "Recommendation service error", "details": string(body)})
		return
	}

	var mlResponse CampaignRecommendationResponse
	if err := json.Unmarshal(body, &mlResponse); err != nil {
		ch.Logger.Error("failed to parse ML response", "error", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to parse recommendations"})
		return
	}

	ch.Logger.Info("campaign recommendations retrieved", "count", len(mlResponse.Recommendations))
	c.JSON(http.StatusOK, mlResponse)
}

func (ch *CampaignHandler) SubmitCampaignFeedbackHandler(c *gin.Context) {
	user := middleware.ValidateOrgAccess(c)
	if user == nil {
		return
	}

	if user.UserRole != "admin" && user.UserRole != "manager" {
		c.JSON(http.StatusForbidden, gin.H{"error": "Only admins and managers can submit campaign feedback"})
		return
	}

	ch.Logger.Info("submitting campaign feedback", "org_id", user.OrganizationID)

	var feedback CampaignFeedbackRequest
	if err := c.ShouldBindJSON(&feedback); err != nil {
		ch.Logger.Warn("invalid feedback request", "error", err)
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	jsonData, err := json.Marshal(feedback)
	if err != nil {
		ch.Logger.Error("failed to marshal feedback", "error", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to prepare feedback"})
		return
	}

	// Call ML service
	client := &http.Client{Timeout: 30 * time.Second}
	resp, err := client.Post(
		fmt.Sprintf("%s/recommend/campaigns/feedback", ch.MLServiceURL),
		"application/json",
		bytes.NewBuffer(jsonData),
	)
	if err != nil {
		ch.Logger.Error("failed to call ML service", "error", err)
		c.JSON(http.StatusServiceUnavailable, gin.H{"error": "Campaign feedback service unavailable"})
		return
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		ch.Logger.Error("failed to read ML response", "error", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to read feedback response"})
		return
	}

	if resp.StatusCode != http.StatusOK {
		ch.Logger.Error("ML service error", "status", resp.StatusCode, "body", string(body))
		c.JSON(resp.StatusCode, gin.H{"error": "Feedback service error", "details": string(body)})
		return
	}

	var mlResponse CampaignFeedbackResponse
	if err := json.Unmarshal(body, &mlResponse); err != nil {
		ch.Logger.Error("failed to parse ML response", "error", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to parse feedback response"})
		return
	}

	ch.Logger.Info("campaign feedback submitted", "campaign_id", feedback.CampaignID, "success", feedback.Success)
	c.JSON(http.StatusOK, mlResponse)
}

// Helper functions to convert data formats for ML service
func (ch *CampaignHandler) convertOrdersForML(orders []database.Order) []map[string]any {
	mlOrders := make([]map[string]any, len(orders))
	for i, order := range orders {
		mlOrders[i] = map[string]any{
			"time":            order.CreateTime.Format(time.RFC3339),
			"total_amount":    order.TotalAmount,
			"items":           order.OrderCount,
			"status":          order.OrderStatus,
			"discount_amount": order.DiscountAmount,
		}
	}
	return mlOrders
}

func (ch *CampaignHandler) convertCampaignsForML(campaigns []database.Campaign) []map[string]any {
	mlCampaigns := make([]map[string]any, len(campaigns))
	for i, campaign := range campaigns {
		itemNames := make([]string, len(campaign.ItemsIncluded))
		for j, item := range campaign.ItemsIncluded {
			itemNames[j] = item.Name
		}

		discount := 0.0
		if campaign.DiscountPercent != nil {
			discount = *campaign.DiscountPercent
		}

		mlCampaigns[i] = map[string]any{
			"start_time":     campaign.StartTime,
			"end_time":       campaign.EndTime,
			"items_included": itemNames,
			"discount":       discount,
		}
	}
	return mlCampaigns
}

func (ch *CampaignHandler) convertOrderItemsForML(orders []database.Order) []map[string]any {
	var mlOrderItems []map[string]any
	for _, order := range orders {
		for _, item := range order.OrderItems {
			quantity := 1
			if item.Quantity != nil {
				quantity = *item.Quantity
			}
			mlOrderItems = append(mlOrderItems, map[string]any{
				"order_id": order.OrderID.String(),
				"item_id":  item.ItemID.String(),
				"quantity": quantity,
			})
		}
	}
	return mlOrderItems
}
