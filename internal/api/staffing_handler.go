package api

import (
	"log/slog"
	"net/http"
	"strconv"

	"github.com/clockwise/clockwise/backend/internal/database"
	"github.com/clockwise/clockwise/backend/internal/middleware"
	"github.com/clockwise/clockwise/backend/internal/service"
	"github.com/clockwise/clockwise/backend/internal/utils"

	"github.com/gin-gonic/gin"
)

type StaffingHandler struct {
	userStore     database.UserStore
	orgStore      database.OrgStore
	uploadService service.UploadService
	emailService  service.EmailService
	Logger        *slog.Logger
}

func NewStaffingHandler(
	userStore database.UserStore,
	orgStore database.OrgStore,
	uploadService service.UploadService,
	emailService service.EmailService,
	logger *slog.Logger,
) *StaffingHandler {
	return &StaffingHandler{
		userStore:     userStore,
		orgStore:      orgStore,
		uploadService: uploadService,
		emailService:  emailService,
		Logger:        logger,
	}
}

type StaffingSummary struct {
	TotalEmployees int              `json:"total_employees"`
	ByRole         map[string]int   `json:"by_role"`
	Employees      []*database.User `json:"employees"`
}

// GetStaffingSummary godoc
// @Summary      Get staffing summary
// @Description  Returns staffing overview including total employees and breakdown by role
// @Tags         Staffing
// @Accept       json
// @Produce      json
// @Security     BearerAuth
// @Param        org path string true "Organization ID"
// @Success      200 {object} StaffingSummary "Staffing summary"
// @Failure      401 {object} map[string]string "Unauthorized"
// @Failure      500 {object} map[string]string "Failed to retrieve employees"
// @Router       /{org}/staffing [get]
func (h *StaffingHandler) GetStaffingSummary(c *gin.Context) {
	h.Logger.Info("get staffing summary request received")

	user := middleware.ValidateOrgAccess(c)
	if user == nil {
		return
	}

	employees, err := h.userStore.GetUsersByOrganization(user.OrganizationID)
	if err != nil {
		h.Logger.Error("failed to get employees", "error", err, "org_id", user.OrganizationID)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to retrieve employees"})
		return
	}

	// Count by role
	byRole := make(map[string]int)
	for _, emp := range employees {
		byRole[emp.UserRole]++
	}

	summary := StaffingSummary{
		TotalEmployees: len(employees),
		ByRole:         byRole,
		Employees:      employees,
	}

	h.Logger.Info("staffing summary retrieved", "org_id", user.OrganizationID, "total", len(employees))
	c.JSON(http.StatusOK, summary)
}

// UploadEmployeesCSV godoc
// @Summary      Bulk upload employees via CSV
// @Description  Upload a CSV file to create multiple employees at once. Required headers: full_name, email, role
// @Tags         Staffing
// @Accept       multipart/form-data
// @Produce      json
// @Security     BearerAuth
// @Param        org path string true "Organization ID"
// @Param        file formData file true "CSV file with employee data"
// @Success      200 {object} map[string]interface{} "Bulk upload completed"
// @Failure      400 {object} map[string]string "No file uploaded or invalid CSV format"
// @Failure      401 {object} map[string]string "Unauthorized"
// @Failure      403 {object} map[string]string "Permission denied"
// @Failure      500 {object} map[string]string "Internal server error"
// @Router       /{org}/staffing/upload [post]
func (h *StaffingHandler) UploadEmployeesCSV(c *gin.Context) {
	h.Logger.Info("upload employees CSV request received")

	user := middleware.ValidateOrgAccess(c)
	if user == nil {
		return
	}

	// Check permission - only admin and manager can upload
	if user.UserRole != "admin" && user.UserRole != "manager" {
		h.Logger.Warn("forbidden upload attempt", "user_id", user.ID, "role", user.UserRole)
		c.JSON(http.StatusForbidden, gin.H{"error": "You don't have permission to upload employees"})
		return
	}

	file, _, err := c.Request.FormFile("file")
	if err != nil {
		h.Logger.Warn("no file uploaded", "error", err)
		c.JSON(http.StatusBadRequest, gin.H{"error": "No file uploaded"})
		return
	}
	defer file.Close()

	csvData, err := h.uploadService.ParseCSV(file)
	if err != nil {
		h.Logger.Error("failed to parse CSV", "error", err)
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// Validate required headers
	requiredHeaders := map[string]bool{"full_name": false, "email": false, "role": false, "salary": false}
	for _, header := range csvData.Headers {
		if _, ok := requiredHeaders[header]; ok {
			requiredHeaders[header] = true
		}
	}
	for header, found := range requiredHeaders {
		if !found {
			h.Logger.Warn("missing required header in CSV", "header", header)
			c.JSON(http.StatusBadRequest, gin.H{"error": "Missing required header: " + header})
			return
		}
	}

	org, err := h.orgStore.GetOrganizationByID(user.OrganizationID)
	if err != nil {
		h.Logger.Error("failed to get organization", "error", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to retrieve organization"})
		return
	}

	var created []string
	var failed []map[string]string

	for _, row := range csvData.Rows {
		fullName := row["full_name"]
		email := row["email"]
		role := row["role"]
		salary, ok := row["salary"]

		
		// Validate role
		if role != "manager" && role != "staff" && role != "employee" {
			failed = append(failed, map[string]string{
				"email": email,
				"error": "Invalid role: " + role,
			})
			continue
		}
		
		var empSalary float64
		if ok {
			empSalary, err := strconv.ParseFloat(salary, 32)
			if err != nil {
				failed = append(failed, map[string]string {
					"email": email,
					"error": "invalid salary format. Please use only numbers in this format (123.12)",
				})
				h.Logger.Error("error parsing float", "error", err.Error(), "for user", email)
				c.AbortWithStatusJSON(http.StatusBadRequest,gin.H{"error":"you have error in salaries column use the specified format int the specs"})
			}
			h.Logger.Info("empolyee salary retrieved",email,empSalary)
		}
		// Generate temporary password
		tempPassword, err := utils.GenerateRandomPassword(8)
		if err != nil {
			failed = append(failed, map[string]string{
				"email": email,
				"error": "Failed to generate password",
			})
			continue
		}

		newUser := &database.User{
			FullName:       fullName,
			Email:          email,
			UserRole:       role,
			OrganizationID: user.OrganizationID,
			SalaryPerHour:         &empSalary,
		}

		if err := newUser.PasswordHash.Set(tempPassword); err != nil {
			failed = append(failed, map[string]string{
				"email": email,
				"error": "Failed to generate password",
			})
			continue
		}

		if err := h.userStore.CreateUser(newUser); err != nil {
			failed = append(failed, map[string]string{
				"email": email,
				"error": err.Error(),
			})
			continue
		}

		// Send welcome email asynchronously
		go func(email, name, password, role, orgName string) {
			if err := h.emailService.SendWelcomeEmail(email, name, password, role, orgName); err != nil {
				h.Logger.Error("failed to send welcome email", "error", err, "email", email)
			}
		}(email, fullName, tempPassword, role, org.Name)

		created = append(created, email)
	}

	h.Logger.Info("bulk employee upload completed",
		"org_id", user.OrganizationID,
		"created", len(created),
		"failed", len(failed))

	c.JSON(http.StatusOK, gin.H{
		"message":       "Bulk upload completed",
		"created_count": len(created),
		"created":       created,
		"failed_count":  len(failed),
		"failed":        failed,
	})
}

// GetAllEmployees godoc
// @Summary      Get all employees
// @Description  Returns a list of all employees in the organization
// @Tags         Staffing
// @Accept       json
// @Produce      json
// @Security     BearerAuth
// @Param        org path string true "Organization ID"
// @Success      200 {object} map[string]interface{} "List of employees"
// @Failure      401 {object} map[string]string "Unauthorized"
// @Failure      500 {object} map[string]string "Failed to retrieve employees"
// @Router       /{org}/staffing/employees [get]
func (h *StaffingHandler) GetAllEmployees(c *gin.Context) {
	h.Logger.Info("get all employees request received")

	user := middleware.ValidateOrgAccess(c)
	if user == nil {
		return
	}

	employees, err := h.userStore.GetUsersByOrganization(user.OrganizationID)
	if err != nil {
		h.Logger.Error("failed to get employees", "error", err, "org_id", user.OrganizationID)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to retrieve employees"})
		return
	}

	h.Logger.Info("employees retrieved", "org_id", user.OrganizationID, "count", len(employees))
	c.JSON(http.StatusOK, gin.H{
		"employees": employees,
		"total":     len(employees),
	})
}
