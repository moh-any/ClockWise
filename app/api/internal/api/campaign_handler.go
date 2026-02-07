package api

import (
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
	CampaignStore    database.CampaignStore
	UploadCSVService service.UploadService
	Logger           *slog.Logger
}

func NewCampaignHandler(campaignStore database.CampaignStore, uploadservice service.UploadService, Logger *slog.Logger) *CampaignHandler {
	return &CampaignHandler{
		CampaignStore:    campaignStore,
		UploadCSVService: uploadservice,
		Logger:           Logger,
	}
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
