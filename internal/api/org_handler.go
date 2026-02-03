package api

import (
	"ClockWise/backend/internal/database"
	"ClockWise/backend/internal/service"
	"ClockWise/backend/internal/utils"
	"fmt"
	"net/http"

	"github.com/gin-gonic/gin"
)

type OrgHandler struct {
	orgStore     database.OrgStore
	userStore    database.UserStore
	emailService service.EmailService
}

func NewOrgHandler(orgStore database.OrgStore, userStore database.UserStore, emailService service.EmailService) *OrgHandler {
	return &OrgHandler{
		orgStore:     orgStore,
		userStore:    userStore,
		emailService: emailService,
	}
}

type RegisterOrgRequest struct {
	OrgName       string `json:"org_name" binding:"required"`
	OrgAddress    string `json:"org_address"`
	AdminFullName string `json:"admin_full_name" binding:"required"`
	AdminEmail    string `json:"admin_email" binding:"required,email"`
	AdminPassword string `json:"admin_password" binding:"required,min=6"`
}

type DelegateUserRequest struct {
	FullName string `json:"full_name" binding:"required"`
	Email    string `json:"email" binding:"required,email"`
	Role     string `json:"role" binding:"required,oneof=manager staff"`
}

func (h *OrgHandler) RegisterOrganization(c *gin.Context) {
	var req RegisterOrgRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	org := &database.Organization{
		Name:    req.OrgName,
		Address: req.OrgAddress,
	}

	user := &database.User{
		FullName: req.AdminFullName,
		Email:    req.AdminEmail,
		UserRole: "admin",
	}

	if err := h.orgStore.CreateOrgWithAdmin(org, user, req.AdminPassword); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Registration failed: " + err.Error()})
		return
	}

	c.JSON(http.StatusCreated, gin.H{
		"message": "Organization registered successfully",
		"org_id":  org.ID,
		"user_id": user.ID,
	})
}

func (h *OrgHandler) DelegateUser(c *gin.Context) {
	currentUserInterface, exists := c.Get("user")
	if !exists {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "Unauthorized"})
		return
	}
	currentUser := currentUserInterface.(*database.User)

	if currentUser.UserRole == "staff" {
		c.JSON(http.StatusForbidden, gin.H{"error": "Staff cannot delegate users"})
		return
	}

	var req DelegateUserRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	org, err := h.orgStore.GetOrganizationByID(currentUser.OrganizationID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to retrieve organization"})
		return
	}

	tempPassword, err := utils.GenerateRandomPassword(8)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to generate password"})
		return
	}

	newUser := &database.User{
		FullName:       req.FullName,
		Email:          req.Email,
		UserRole:       req.Role,
		OrganizationID: currentUser.OrganizationID,
	}

	if err := newUser.PasswordHash.Set(tempPassword); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Calculation error"})
		return
	}

	if err := h.userStore.CreateUser(newUser); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Database error: " + err.Error()})
		return
	}

	go func() {
		if err := h.emailService.SendWelcomeEmail(newUser.Email, newUser.FullName, tempPassword, newUser.UserRole, org.Name); err != nil {
			fmt.Printf("Error sending email: %v\n", err)
		}
	}()

	c.JSON(http.StatusCreated, gin.H{
		"message": "User delegated successfully. Email sent.",
		"user_id": newUser.ID,
	})
}
