package api

import (
	"log/slog"
	"net/http"

	"github.com/clockwise/clockwise/backend/internal/database"
	"github.com/clockwise/clockwise/backend/internal/middleware"
	"github.com/clockwise/clockwise/backend/internal/service"
	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
)

type OfferHandler struct {
	Logger       *slog.Logger
	EmailService service.EmailService
	UserStore    database.UserStore
	OfferStore   database.OfferStore
	OrgStore     database.OrgStore
}

func NewOfferHandler(userStore database.UserStore, orgStore database.OrgStore, offerStore database.OfferStore, emailSvc service.EmailService, logger *slog.Logger) *OfferHandler {
	return &OfferHandler{
		Logger:       logger,
		EmailService: emailSvc,
		UserStore:    userStore,
		OfferStore:   offerStore,
		OrgStore:     orgStore,
	}
}

type OfferHandleroffer struct {
}

type OfferHandlerResponse struct {
}

type OfferActionBody struct {
	OfferID string `json:"offer_id"`
	
}

func (oh *OfferHandler) GetAllOffersForEmployeeHandler(c *gin.Context) {

}

func (oh *OfferHandler) AcceptOfferHandler(c *gin.Context) {
	oh.Logger.Info("accept offer received")

	user := middleware.ValidateOrgAccess(c)
	if user == nil {
		return
	}

	// Only employee can access this resource
	if user.UserRole != "employee" {
		oh.Logger.Warn("forbidden accept attempt", "user_id", user.ID, "role", user.UserRole)
		c.JSON(http.StatusForbidden, gin.H{"error": "You don't have permission to accept offers"})
		return
	}

	var req OfferActionBody
	if err := c.ShouldBindJSON(&req); err != nil {
		oh.Logger.Warn("invalid offer body", "error", err)
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	offerID, err := uuid.Parse(req.OfferID)
	if err != nil {
		oh.Logger.Warn("invalid offer ID", "id", req.OfferID)
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid offer ID"})
		return
	}

	// Verify offer belongs to organization
	offer, err := oh.OfferStore.GetOfferByID(offerID)
	if err != nil {
		oh.Logger.Error("failed to get offer", "error", err, "offer_id", offerID)
		c.JSON(http.StatusNotFound, gin.H{"error": "Offer not found"})
		return
	}

	employee, err := oh.UserStore.GetUserByID(user.ID)
	if err != nil || employee.OrganizationID != user.OrganizationID {
		oh.Logger.Warn("attempted to accept offer from different organization")
		c.JSON(http.StatusForbidden, gin.H{"error": "Access denied"})
		return
	}

	if err := oh.OfferStore.UpdateOfferStatus(offerID, "accepted"); err != nil {
		oh.Logger.Error("failed to accept offer", "error", err, "offer_id", offerID)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to accept offer"})
		return
	}
	
	//TODO: Send update schedule and redirect to the schedule

	go func() {
		
		// Notify managers and admins
		managerEmails, err := oh.OrgStore.GetManagerEmailsByOrgID(user.OrganizationID)
		if err != nil {
			oh.Logger.Error("failed to get manager emails", "error", err)
		}
		
		adminEmails, err := oh.OrgStore.GetAdminEmailsByOrgID(user.OrganizationID)
		if err != nil {
			oh.Logger.Error("failed to get admin emails", "error", err)
		}
		
		notifyEmails := append(managerEmails, adminEmails...)
		if len(notifyEmails) > 0 {
			if err := oh.EmailService.SendOfferAcceptedEmailToManagerAndAdmin(notifyEmails, employee.FullName, offer.Status, offer.StartTime.String()); err != nil {
				oh.Logger.Error("failed to send offer accepted email")
			}
		}
	}()


	oh.Logger.Info("offer accepted", "offer_id", offerID, "by", user.ID)
	c.JSON(http.StatusOK, gin.H{
		"message":    "offer accepted successfully",
		"offer_id": offerID,
	})
}

func (oh *OfferHandler) DeclineOfferHandler(c *gin.Context) {
	oh.Logger.Info("decline offer received")

	user := middleware.ValidateOrgAccess(c)
	if user == nil {
		return
	}

	// Only employee can access this resource
	if user.UserRole != "employee" {
		oh.Logger.Warn("forbidden decline attempt", "user_id", user.ID, "role", user.UserRole)
		c.JSON(http.StatusForbidden, gin.H{"error": "You don't have permission to decline offers"})
		return
	}

	var req OfferActionBody
	if err := c.ShouldBindJSON(&req); err != nil {
		oh.Logger.Warn("invalid offer body", "error", err)
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	offerID, err := uuid.Parse(req.OfferID)
	if err != nil {
		oh.Logger.Warn("invalid offer ID", "id", req.OfferID)
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid offer ID"})
		return
	}

	// Verify offer belongs to organization
	offer, err := oh.OfferStore.GetOfferByID(offerID)
	if err != nil {
		oh.Logger.Error("failed to get offer", "error", err, "offer_id", offerID)
		c.JSON(http.StatusNotFound, gin.H{"error": "Offer not found"})
		return
	}

	employee, err := oh.UserStore.GetUserByID(user.ID)
	if err != nil || employee.OrganizationID != user.OrganizationID {
		oh.Logger.Warn("attempted to decline offer from different organization")
		c.JSON(http.StatusForbidden, gin.H{"error": "Access denied"})
		return
	}

	if err := oh.OfferStore.UpdateOfferStatus(offerID, "declined"); err != nil {
		oh.Logger.Error("failed to decline offer", "error", err, "offer_id", offerID)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to decline offer"})
		return
	}

	go func() {
		
		// Notify managers and admins
		managerEmails, err := oh.OrgStore.GetManagerEmailsByOrgID(user.OrganizationID)
		if err != nil {
			oh.Logger.Error("failed to get manager emails", "error", err)
		}
		
		adminEmails, err := oh.OrgStore.GetAdminEmailsByOrgID(user.OrganizationID)
		if err != nil {
			oh.Logger.Error("failed to get admin emails", "error", err)
		}
		
		notifyEmails := append(managerEmails, adminEmails...)
		if len(notifyEmails) > 0 {
			if err := oh.EmailService.SendOfferDeclinedEmailToManagerAndAdmin(notifyEmails, employee.FullName, offer.Status, offer.StartTime.String()); err != nil {
				oh.Logger.Error("failed to send offer decline email")
			}
		}
	}()


	oh.Logger.Info("offer declined", "offer_id", offerID, "by", user.ID)
	c.JSON(http.StatusOK, gin.H{
		"message":    "offer declined successfully",
		"offer_id": offerID,
	})
}
