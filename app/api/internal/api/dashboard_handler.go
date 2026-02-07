package api

// TODO Demand is auto generated every day and store in the database -> Background Tasks
import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"log/slog"
	"net/http"
	"os"
	"time"

	"github.com/clockwise/clockwise/backend/internal/database"
	"github.com/clockwise/clockwise/backend/internal/middleware"
	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
)

type DashboardHandler struct {
	OrgStore            database.OrgStore
	RulesStore          database.RulesStore
	OperatingHoursStore database.OperatingHoursStore
	OrderStore          database.OrderStore
	CampaignStore       database.CampaignStore
	DemandStore         database.DemandStore
	Logger              *slog.Logger
}

func NewDashboardHandler(
	orgStore database.OrgStore,
	rulesStore database.RulesStore,
	operatingHoursStore database.OperatingHoursStore,
	orderStore database.OrderStore,
	campaignStore database.CampaignStore,
	demandStore database.DemandStore,
	logger *slog.Logger,
) *DashboardHandler {
	return &DashboardHandler{
		OrgStore:            orgStore,
		RulesStore:          rulesStore,
		OperatingHoursStore: operatingHoursStore,
		OrderStore:          orderStore,
		CampaignStore:       campaignStore,
		DemandStore:         demandStore,
		Logger:              logger,
	}
}

type DemandPredictionRequest struct {
	Place                Place               `json:"place"`
	Orders               []database.Order    `json:"orders"`
	Campaigns            []database.Campaign `json:"campaigns"`
	PredicationStartDate time.Time           `json:"prediction_start_date"`
	PredictionDays       *int                `json:"prediction_days,omitempty"`
}

type Place struct {
	ID                 uuid.UUID                 `json:"place_id"`
	Name               string                    `json:"name"`
	Type               string                    `json:"type"`
	Latitude           *float64                  `json:"latitude,omitempty"`
	Longitude          *float64                  `json:"longitude,omitempty"`
	WaitingTime        int                       `json:"waiting_time"`
	ReceivingPhone     bool                      `json:"receiving_phone"`
	Delivery           bool                      `json:"delivery"`
	OpeningHours       []database.OperatingHours `json:"opening_hours"`
	FixedShifts        bool                      `json:"fixed_shifts"`
	NumberShiftsPerDay int                       `json:"number_of_shifts_per_day"`
	ShiftTimes         []database.ShiftTime      `json:"shift_time"`
	Rating             *float64                  `json:"rating,omitempty"`
	AcceptingOrders    bool                      `json:"accepting_orders"`
}

func (dh *DashboardHandler) GetDemandHeatMapHandler(c *gin.Context) {
	user := middleware.ValidateOrgAccess(c)
	if user == nil {
		return
	}

	if user.UserRole != "admin" && user.UserRole != "manager" {
		c.JSON(http.StatusForbidden, gin.H{"error": "Only admins and managers can access demand data"})
		return
	}

	dh.Logger.Info("retrieving demand heatmap from database", "org_id", user.OrganizationID)

	// Get latest demand predictions from database (last 7 days)
	demandResponse, err := dh.DemandStore.GetLatestDemandHeatMap(user.OrganizationID)
	if err != nil {
		dh.Logger.Error("failed to retrieve demand heatmap", "error", err, "org_id", user.OrganizationID)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to retrieve demand data"})
		return
	}

	// Check if demand data exists
	if demandResponse == nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "No demand data found for this organization"})
		return
	}

	// Return the demand heatmap
	c.JSON(http.StatusOK, demandResponse)
}

func (dh *DashboardHandler) PredictDemandHeatMapHandler(c *gin.Context) {
	user := middleware.ValidateOrgAccess(c)
	if user == nil {
		return
	}

	if user.UserRole != "admin" && user.UserRole != "manager" {
		c.JSON(http.StatusForbidden, gin.H{"error": "Only admins and managers can access orders"})
		return
	}

	dh.Logger.Info("requesting demand from external api", "org_id", user.OrganizationID)

	organization, err := dh.OrgStore.GetOrganizationByID(user.OrganizationID)

	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to get organization details"})
		return
	}

	if organization == nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "organization not found"})
		return
	}

	organization_rules, err := dh.RulesStore.GetRulesByOrganizationID(user.OrganizationID)

	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to get organization rules details"})
		return
	}

	if organization_rules == nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "organization rules not found"})
		return
	}

	operating_hours, err := dh.OperatingHoursStore.GetOperatingHours(user.OrganizationID)

	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to get organization operating hours details"})
		return
	}

	if operating_hours == nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "operating hours not found"})
		return
	}

	if organization_rules.NumberOfShiftsPerDay == nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "number of shifts per day not configured"})
		return
	}

	Place := Place{
		ID:                 organization.ID,
		Name:               organization.Name,
		Type:               organization.Type,
		Latitude:           organization.Location.Latitude,
		Longitude:          organization.Location.Longitude,
		WaitingTime:        organization_rules.WaitingTime,
		ReceivingPhone:     organization_rules.ReceivingPhone,
		Delivery:           organization_rules.Delivery,
		OpeningHours:       operating_hours,
		FixedShifts:        organization_rules.FixedShifts,
		NumberShiftsPerDay: *organization_rules.NumberOfShiftsPerDay,
		ShiftTimes:         organization_rules.ShiftTimes,
		Rating:             organization.Rating,
		AcceptingOrders:    organization_rules.AcceptingOrders,
	}

	orders, err := dh.OrderStore.GetAllOrders(user.OrganizationID)

	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to get organization orders details, please make sure to upload them"})
		return
	}

	if orders == nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "no orders found for this organization"})
		return
	}

	campaigns, err := dh.CampaignStore.GetAllCampaigns(user.OrganizationID)

	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to get organization campaigns details, please make sure to upload them"})
		return
	}

	if campaigns == nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "no campaigns found for this organization"})
		return
	}
	days := 7

	request := DemandPredictionRequest{
		Place:                Place,
		Orders:               orders,
		Campaigns:            campaigns,
		PredicationStartDate: time.Now(),
		PredictionDays:       &days,
	}

	// Call external ML API
	mlURL := os.Getenv("ML_URL")
	if mlURL == "" {
		mlURL = "http://cw-ml-service:8000"
	}

	// Make an api call to the demand model http://cw-ml-service:8000/predict/demand
	client := &http.Client{}

	// JSON
	jsonPayload, err := json.Marshal(request)
	if err != nil {
		dh.Logger.Error("failed to marshal request", "error", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to prepare request payload"})
		return
	}

	dh.Logger.Info(string(jsonPayload))
	req, err := http.NewRequest("POST", fmt.Sprintf("%v%v", os.Getenv("ML_URL"), "/predict/demand"), bytes.NewBuffer(jsonPayload))
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to create request"})
		return
	}

	req.Header.Add("Content-Type", "application/json")

	resp, err := client.Do(req)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	defer resp.Body.Close()

	// Validate response status code first
	if resp.StatusCode != http.StatusOK {
		dh.Logger.Error("ML API returned error", "status_code", resp.StatusCode)
		body, _ := io.ReadAll(resp.Body)
		c.JSON(resp.StatusCode, gin.H{"error": "ML service returned an error", "details": string(body)})
		return
	}

	// Process Response with custom UnmarshalJSON for date parsing
	var demandResponse database.DemandPredictResponse
	decoder := json.NewDecoder(resp.Body)

	if err := decoder.Decode(&demandResponse); err != nil {
		dh.Logger.Error("failed to decode ML response", "error", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to decode ML response"})
		return
	}

	// Store in Demand Store
	err = dh.DemandStore.StoreDemandHeatMap(user.OrganizationID, demandResponse)

	if err != nil {
		c.AbortWithStatusJSON(http.StatusInternalServerError, gin.H{"error": "internal server error"})
		return
	}

	// Return the successfully decoded response
	c.JSON(http.StatusOK, gin.H{"message": "demand prediction retrieved successfuly from API", "data": demandResponse})
}
