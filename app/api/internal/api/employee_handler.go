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

type EmployeeHandler struct {
	userStore    database.UserStore
	requestStore database.RequestStore
	orgStore     database.OrgStore
	EmailService service.EmailService
	Logger       *slog.Logger
}

func NewEmployeeHandler(userStore database.UserStore, emailService service.EmailService, requestStore database.RequestStore, orgStore database.OrgStore, logger *slog.Logger) *EmployeeHandler {
	return &EmployeeHandler{
		userStore:    userStore,
		requestStore: requestStore,
		orgStore:     orgStore,
		EmailService: emailService,
		Logger:       logger,
	}
}

type LayoffRequest struct {
	Reason string `json:"reason"`
}

type RequestActionBody struct {
	RequestID string `json:"request_id" binding:"required"`
}

// GetEmployeeDetails godoc
func (h *EmployeeHandler) GetEmployeeDetails(c *gin.Context) {
	h.Logger.Info("get employee details request received")

	user := middleware.ValidateOrgAccess(c)
	if user == nil {
		return
	}

	employeeIDStr := c.Param("id")
	employeeID, err := uuid.Parse(employeeIDStr)
	if err != nil {
		h.Logger.Warn("invalid employee ID", "id", employeeIDStr)
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid employee ID"})
		return
	}

	employee, err := h.userStore.GetUserByID(employeeID)
	if err != nil {
		h.Logger.Error("failed to get employee", "error", err, "employee_id", employeeID)
		c.JSON(http.StatusNotFound, gin.H{"error": "Employee not found"})
		return
	}

	// Verify employee belongs to same organization
	if employee.OrganizationID != user.OrganizationID {
		h.Logger.Warn("attempted to access employee from different organization",
			"user_org", user.OrganizationID,
			"employee_org", employee.OrganizationID)
		c.JSON(http.StatusForbidden, gin.H{"error": "Access denied"})
		return
	}

	h.Logger.Info("employee details retrieved", "employee_id", employeeID)
	c.JSON(http.StatusOK, gin.H{
		"message": "Employee details retrieved successfully",
		"data":    employee,
	})
}

// LayoffEmployee godoc
func (h *EmployeeHandler) LayoffEmployee(c *gin.Context) {
	h.Logger.Info("layoff employee request received")

	user := middleware.ValidateOrgAccess(c)
	if user == nil {
		return
	}

	// Only admin and manager can layoff
	if user.UserRole != "admin" && user.UserRole != "manager" {
		h.Logger.Warn("forbidden layoff attempt", "user_id", user.ID, "role", user.UserRole)
		c.JSON(http.StatusForbidden, gin.H{"error": "You don't have permission to layoff employees"})
		return
	}

	employeeIDStr := c.Param("id")
	employeeID, err := uuid.Parse(employeeIDStr)
	if err != nil {
		h.Logger.Warn("invalid employee ID", "id", employeeIDStr)
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid employee ID"})
		return
	}

	// Verify employee exists and belongs to same organization
	employee, err := h.userStore.GetUserByID(employeeID)
	if err != nil {
		h.Logger.Error("failed to get employee", "error", err, "employee_id", employeeID)
		c.JSON(http.StatusNotFound, gin.H{"error": "Employee not found"})
		return
	}

	if employee.OrganizationID != user.OrganizationID {
		h.Logger.Warn("attempted to layoff employee from different organization")
		c.JSON(http.StatusForbidden, gin.H{"error": "Access denied"})
		return
	}

	// Prevent self-layoff
	if employee.ID == user.ID {
		h.Logger.Warn("attempted self-layoff", "user_id", user.ID)
		c.JSON(http.StatusBadRequest, gin.H{"error": "Cannot layoff yourself"})
		return
	}

	// Manager cannot layoff admin
	if user.UserRole == "manager" && employee.UserRole == "admin" {
		h.Logger.Warn("manager attempted to layoff admin", "manager_id", user.ID, "admin_id", employee.ID)
		c.JSON(http.StatusForbidden, gin.H{"error": "Managers cannot layoff admins"})
		return
	}

	var req LayoffRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		req.Reason = "No reason provided"
	}

	if err := h.userStore.LayoffUser(employeeID, req.Reason); err != nil {
		h.Logger.Error("failed to layoff employee", "error", err, "employee_id", employeeID)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to layoff employee"})
		return
	}

	go func() {
		if err := h.EmailService.SendLayoffEmail(employee.Email, employee.FullName, req.Reason); err != nil {
			h.Logger.Error("failed to send layoff email", "error", err, "email", employee.Email)
		}
	}()

	h.Logger.Info("employee laid off successfully", "employee_id", employeeID, "by", user.ID)
	c.JSON(http.StatusOK, gin.H{
		"message":     "Employee laid off successfully",
		"employee_id": employeeID,
	})
}

// GetEmployeeRequests godoc
func (h *EmployeeHandler) GetEmployeeRequests(c *gin.Context) {
	h.Logger.Info("get employee requests received")

	user := middleware.ValidateOrgAccess(c)
	if user == nil {
		return
	}

	employeeIDStr := c.Param("id")
	employeeID, err := uuid.Parse(employeeIDStr)
	if err != nil {
		h.Logger.Warn("invalid employee ID", "id", employeeIDStr)
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid employee ID"})
		return
	}

	// Verify access - can only view own requests or if admin/manager
	if employeeID != user.ID && user.UserRole != "admin" && user.UserRole != "manager" {
		h.Logger.Warn("forbidden request access attempt", "user_id", user.ID, "employee_id", employeeID)
		c.JSON(http.StatusForbidden, gin.H{"error": "Access denied"})
		return
	}

	// Verify employee belongs to same organization
	employee, err := h.userStore.GetUserByID(employeeID)
	if err != nil {
		h.Logger.Error("failed to get employee", "error", err, "employee_id", employeeID)
		c.JSON(http.StatusNotFound, gin.H{"error": "Employee not found"})
		return
	}

	if employee.OrganizationID != user.OrganizationID {
		h.Logger.Warn("attempted to access requests from different organization")
		c.JSON(http.StatusForbidden, gin.H{"error": "Access denied"})
		return
	}

	requests, err := h.requestStore.GetRequestsByEmployee(employeeID)
	if err != nil {
		h.Logger.Error("failed to get requests", "error", err, "employee_id", employeeID)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to retrieve requests"})
		return
	}

	h.Logger.Info("employee requests retrieved", "employee_id", employeeID, "count", len(requests))
	c.JSON(http.StatusOK, gin.H{
		"message":  "Employee requests retrieved successfully",
		"requests": requests,
		"total":    len(requests),
	})
}

// ApproveRequest godoc
func (h *EmployeeHandler) ApproveRequest(c *gin.Context) {
	h.Logger.Info("approve request received")

	user := middleware.ValidateOrgAccess(c)
	if user == nil {
		return
	}

	// Only admin and manager can approve
	if user.UserRole != "admin" && user.UserRole != "manager" {
		h.Logger.Warn("forbidden approve attempt", "user_id", user.ID, "role", user.UserRole)
		c.JSON(http.StatusForbidden, gin.H{"error": "You don't have permission to approve requests"})
		return
	}

	var req RequestActionBody
	if err := c.ShouldBindJSON(&req); err != nil {
		h.Logger.Warn("invalid request body", "error", err)
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	requestID, err := uuid.Parse(req.RequestID)
	if err != nil {
		h.Logger.Warn("invalid request ID", "id", req.RequestID)
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid request ID"})
		return
	}

	// Verify request belongs to organization
	request, err := h.requestStore.GetRequestByID(requestID)
	if err != nil {
		h.Logger.Error("failed to get request", "error", err, "request_id", requestID)
		c.JSON(http.StatusNotFound, gin.H{"error": "Request not found"})
		return
	}

	employee, err := h.userStore.GetUserByID(request.EmployeeID)
	if err != nil || employee.OrganizationID != user.OrganizationID {
		h.Logger.Warn("attempted to approve request from different organization")
		c.JSON(http.StatusForbidden, gin.H{"error": "Access denied"})
		return
	}

	if err := h.requestStore.UpdateRequestStatus(requestID, "accepted"); err != nil {
		h.Logger.Error("failed to approve request", "error", err, "request_id", requestID)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to approve request"})
		return
	}

	go func() {
		if err := h.EmailService.SendRequestApprovedEmail(employee.Email, employee.FullName, request.Type); err != nil {
			h.Logger.Error("failed to send request approved email", "error", err, "email", employee.Email)
		}
	}()

	//TODO: Handle If type = resign mark the employee as not working, else if holiday cancel for the whole day if call off cancel for the next shift
	if request.Type == "resign" {

	} else if request.Type == "holiday" {

	} else if request.Type == "calloff" { 

	}
	//TODO: Send to the model to update schedule and redirect to the schedule



	h.Logger.Info("request approved", "request_id", requestID, "by", user.ID)
	c.JSON(http.StatusOK, gin.H{
		"message":    "Request approved successfully",
		"request_id": requestID,
	})
}

// DeclineRequest godoc
func (h *EmployeeHandler) DeclineRequest(c *gin.Context) {
	h.Logger.Info("decline request received")

	user := middleware.ValidateOrgAccess(c)
	if user == nil {
		return
	}

	// Only admin and manager can decline
	if user.UserRole != "admin" && user.UserRole != "manager" {
		h.Logger.Warn("forbidden decline attempt", "user_id", user.ID, "role", user.UserRole)
		c.JSON(http.StatusForbidden, gin.H{"error": "You don't have permission to decline requests"})
		return
	}

	var req RequestActionBody
	if err := c.ShouldBindJSON(&req); err != nil {
		h.Logger.Warn("invalid request body", "error", err)
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	requestID, err := uuid.Parse(req.RequestID)
	if err != nil {
		h.Logger.Warn("invalid request ID", "id", req.RequestID)
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid request ID"})
		return
	}

	// Verify request belongs to organization
	request, err := h.requestStore.GetRequestByID(requestID)
	if err != nil {
		h.Logger.Error("failed to get request", "error", err, "request_id", requestID)
		c.JSON(http.StatusNotFound, gin.H{"error": "Request not found"})
		return
	}

	employee, err := h.userStore.GetUserByID(request.EmployeeID)
	if err != nil || employee.OrganizationID != user.OrganizationID {
		h.Logger.Warn("attempted to decline request from different organization")
		c.JSON(http.StatusForbidden, gin.H{"error": "Access denied"})
		return
	}

	if err := h.requestStore.UpdateRequestStatus(requestID, "declined"); err != nil {
		h.Logger.Error("failed to decline request", "error", err, "request_id", requestID)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to decline request"})
		return
	}

	go func() {
		if err := h.EmailService.SendRequestDeclinedEmail(employee.Email, employee.FullName, request.Type); err != nil {
			h.Logger.Error("failed to send request declined email", "error", err, "email", employee.Email)
		}
	}()

	h.Logger.Info("request declined", "request_id", requestID, "by", user.ID)
	c.JSON(http.StatusOK, gin.H{
		"message":    "Request declined successfully",
		"request_id": requestID,
	})
}

type CalloffRequest struct {
	Type    string `json:"type" binding:"required,oneof=calloff holiday resign"`
	Message string `json:"message" binding:"required"`
}

// RequestCalloffHandlerForEmployee godoc
func (h *EmployeeHandler) RequestHandlerForEmployee(c *gin.Context) {
	h.Logger.Info("employee request received")

	user := middleware.ValidateOrgAccess(c)
	if user == nil {
		return
	}

	if user.UserRole == "admin" {
		h.Logger.Warn("forbidden decline attempt", "user_id", user.ID, "role", user.UserRole)
		c.JSON(http.StatusForbidden, gin.H{"error": "You don't have permission send requests"})
		return
	}

	var req CalloffRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		h.Logger.Warn("invalid request body", "error", err)
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	request := &database.Request{
		EmployeeID: user.ID,
		Type:       req.Type,
		Message:    req.Message,
	}

	if err := h.requestStore.CreateRequest(request); err != nil {
		h.Logger.Error("failed to create request", "error", err, "user_id", user.ID)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to submit request"})
		return
	}

	go func() {
		if err := h.EmailService.SendRequestSubmittedEmail(user.Email, user.FullName, req.Type, req.Message); err != nil {
			h.Logger.Error("failed to send request submitted email", "error", err, "email", user.Email)
		}

		// Notify managers and admins
		managerEmails, err := h.orgStore.GetManagerEmailsByOrgID(user.OrganizationID)
		if err != nil {
			h.Logger.Error("failed to get manager emails", "error", err)
		}
		adminEmails, err := h.orgStore.GetAdminEmailsByOrgID(user.OrganizationID)
		if err != nil {
			h.Logger.Error("failed to get admin emails", "error", err)
		}
		notifyEmails := append(managerEmails, adminEmails...)
		if len(notifyEmails) > 0 {
			if err := h.EmailService.SendRequestNotifyEmail(notifyEmails, user.FullName, req.Type, req.Message); err != nil {
				h.Logger.Error("failed to send request notification to managers/admins", "error", err)
			}
		}
	}()

	h.Logger.Info("request submitted successfully", "request_id", request.ID, "user_id", user.ID, "type", req.Type)
	c.JSON(http.StatusCreated, gin.H{
		"message":    "Request submitted successfully",
		"request_id": request.ID,
	})
}
