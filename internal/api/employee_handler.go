package api

import (
	"log/slog"
	"net/http"

	"github.com/clockwise/clockwise/backend/internal/database"
	"github.com/clockwise/clockwise/backend/internal/middleware"
	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
)

type EmployeeHandler struct {
	userStore    database.UserStore
	requestStore database.RequestStore
	Logger       *slog.Logger
}

func NewEmployeeHandler(userStore database.UserStore, requestStore database.RequestStore, logger *slog.Logger) *EmployeeHandler {
	return &EmployeeHandler{
		userStore:    userStore,
		requestStore: requestStore,
		Logger:       logger,
	}
}

type LayoffRequest struct {
	Reason string `json:"reason"`
}

type RequestActionBody struct {
	RequestID string `json:"request_id" binding:"required"`
}

// GetEmployeeDetails returns details of a specific employee
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
	c.JSON(http.StatusOK, employee)
}

// LayoffEmployee handles employee layoff
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

	h.Logger.Info("employee laid off successfully", "employee_id", employeeID, "by", user.ID)
	c.JSON(http.StatusOK, gin.H{
		"message":     "Employee laid off successfully",
		"employee_id": employeeID,
	})
}

// GetEmployeeRequests returns all requests for a specific employee
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
		"requests": requests,
		"total":    len(requests),
	})
}

// ApproveRequest approves an employee request
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

	h.Logger.Info("request approved", "request_id", requestID, "by", user.ID)
	c.JSON(http.StatusOK, gin.H{
		"message":    "Request approved successfully",
		"request_id": requestID,
	})
}

// DeclineRequest declines an employee request
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

	h.Logger.Info("request declined", "request_id", requestID, "by", user.ID)
	c.JSON(http.StatusOK, gin.H{
		"message":    "Request declined successfully",
		"request_id": requestID,
	})
}
