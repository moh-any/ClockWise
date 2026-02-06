package api

import (
	"bytes"
	"encoding/json"
	"errors"
	"log/slog"
	"mime/multipart"
	"net/http"
	"net/http/httptest"
	"os"
	"testing"
	"time"

	"github.com/clockwise/clockwise/backend/internal/api"
	"github.com/clockwise/clockwise/backend/internal/database"
	"github.com/clockwise/clockwise/backend/internal/service"
	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/mock"
)

type StaffingTestEnv struct {
	Router        *gin.Engine
	UserStore     *MockUserStore
	OrgStore      *MockOrgStore
	UploadService *MockUploadService
	EmailService  *MockEmailService
	Handler       *api.StaffingHandler
}

func setupStaffingEnv() *StaffingTestEnv {
	gin.SetMode(gin.TestMode)

	userStore := new(MockUserStore)
	orgStore := new(MockOrgStore)
	uploadService := new(MockUploadService)
	emailService := new(MockEmailService)
	logger := slog.New(slog.NewTextHandler(os.Stdout, nil))

	handler := api.NewStaffingHandler(userStore, orgStore, uploadService, emailService, logger)

	return &StaffingTestEnv{
		Router:        gin.New(),
		UserStore:     userStore,
		OrgStore:      orgStore,
		UploadService: uploadService,
		EmailService:  emailService,
		Handler:       handler,
	}
}

func (env *StaffingTestEnv) ResetMocks() {
	env.UserStore.ExpectedCalls = nil
	env.UserStore.Calls = nil
	env.OrgStore.ExpectedCalls = nil
	env.OrgStore.Calls = nil
	env.UploadService.ExpectedCalls = nil
	env.UploadService.Calls = nil
	env.EmailService.ExpectedCalls = nil
	env.EmailService.Calls = nil
}

func TestGetStaffingSummary(t *testing.T) {
	env := setupStaffingEnv()
	orgID := uuid.New()
	admin := &database.User{ID: uuid.New(), OrganizationID: orgID, UserRole: "admin"}

	// Register route
	env.Router.GET("/:org/staffing", authMiddleware(admin), env.Handler.GetStaffingSummary)

	t.Run("Success", func(t *testing.T) {
		env.ResetMocks()
		employees := []*database.User{
			{UserRole: "manager"},
			{UserRole: "employee"},
			{UserRole: "employee"},
		}

		env.UserStore.On("GetUsersByOrganization", orgID).Return(employees, nil).Once()

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/"+orgID.String()+"/staffing", nil)
		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusOK, w.Code)
		assert.Contains(t, w.Body.String(), `"total_employees":3`)
		assert.Contains(t, w.Body.String(), `"manager":1`)
		assert.Contains(t, w.Body.String(), `"employee":2`)
		env.UserStore.AssertExpectations(t)
	})

	t.Run("Failure_DBError", func(t *testing.T) {
		env.ResetMocks()
		env.UserStore.On("GetUsersByOrganization", orgID).Return(nil, errors.New("db error")).Once()

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/"+orgID.String()+"/staffing", nil)
		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusInternalServerError, w.Code)
	})
}

func TestGetAllEmployees(t *testing.T) {
	env := setupStaffingEnv()
	orgID := uuid.New()
	admin := &database.User{ID: uuid.New(), OrganizationID: orgID, UserRole: "admin"}

	// Register route
	env.Router.GET("/:org/staffing/employees", authMiddleware(admin), env.Handler.GetAllEmployees)

	t.Run("Success", func(t *testing.T) {
		env.ResetMocks()
		employees := []*database.User{
			{ID: uuid.New(), FullName: "John Doe"},
		}

		env.UserStore.On("GetUsersByOrganization", orgID).Return(employees, nil).Once()

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/"+orgID.String()+"/staffing/employees", nil)
		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusOK, w.Code)
		assert.Contains(t, w.Body.String(), "John Doe")
		env.UserStore.AssertExpectations(t)
	})

	t.Run("Failure_DBError", func(t *testing.T) {
		env.ResetMocks()
		env.UserStore.On("GetUsersByOrganization", orgID).Return(nil, errors.New("db error")).Once()

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/"+orgID.String()+"/staffing/employees", nil)
		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusInternalServerError, w.Code)
	})
}

func TestUploadEmployeesCSV(t *testing.T) {
	env := setupStaffingEnv()
	orgID := uuid.New()
	admin := &database.User{ID: uuid.New(), OrganizationID: orgID, UserRole: "admin"}
	employee := &database.User{ID: uuid.New(), OrganizationID: orgID, UserRole: "employee"}

	// Register route
	env.Router.POST("/:org/staffing/upload", authMiddleware(admin), env.Handler.UploadEmployeesCSV)

	employeeRouter := gin.New()
	employeeRouter.POST("/:org/staffing/upload", authMiddleware(employee), env.Handler.UploadEmployeesCSV)

	t.Run("Success_Upload", func(t *testing.T) {
		env.ResetMocks()

		org := &database.Organization{ID: orgID, Name: "Clockwise"}

		csvData := &service.CSVData{
			Headers: []string{"full_name", "email", "role", "salary"},
			Rows: []map[string]string{
				{"full_name": "New User", "email": "new@test.com", "role": "employee", "salary": "20.5"},
			},
			Total: 1,
		}

		// Use mock.Anything for the multipart.File as it changes on every request
		env.UploadService.On("ParseCSV", mock.Anything).Return(csvData, nil).Once()
		env.OrgStore.On("GetOrganizationByID", orgID).Return(org, nil).Once()

		// CreateUser expectation
		env.UserStore.On("CreateUser", mock.MatchedBy(func(u *database.User) bool {
			// Debug mismatch if any
			if u.Email != "new@test.com" {
				return false
			}
			if u.UserRole != "employee" {
				return false
			}
			if u.SalaryPerHour == nil || *u.SalaryPerHour != 20.5 {
				return false
			}
			return true
		})).Return(nil).Once()

		// Email expectation (async)
		env.EmailService.On("SendWelcomeEmail", "new@test.com", "New User", mock.Anything, "employee", "Clockwise").Return(nil).Once()

		// Build Multipart Request
		body := new(bytes.Buffer)
		writer := multipart.NewWriter(body)
		part, _ := writer.CreateFormFile("file", "test.csv")
		part.Write([]byte("dummy content"))
		writer.Close()

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("POST", "/"+orgID.String()+"/staffing/upload", body)
		req.Header.Set("Content-Type", writer.FormDataContentType())

		env.Router.ServeHTTP(w, req)

		time.Sleep(20 * time.Millisecond) // Wait for async email

		// DEBUG LOGS - Run with `go test -v`
		t.Logf("Response Code: %d", w.Code)
		t.Logf("Response Body: %s", w.Body.String())

		assert.Equal(t, http.StatusOK, w.Code)
		assert.Contains(t, w.Body.String(), "Bulk upload completed")
		assert.Contains(t, w.Body.String(), `"created_count":1`)

		env.UploadService.AssertExpectations(t)
		env.UserStore.AssertExpectations(t)
		env.EmailService.AssertExpectations(t)
	})

	t.Run("Failure_Forbidden", func(t *testing.T) {
		env.ResetMocks()
		w := httptest.NewRecorder()
		req, _ := http.NewRequest("POST", "/"+orgID.String()+"/staffing/upload", nil)
		employeeRouter.ServeHTTP(w, req)

		assert.Equal(t, http.StatusForbidden, w.Code)
	})

	t.Run("Failure_NoFile", func(t *testing.T) {
		env.ResetMocks()
		w := httptest.NewRecorder()
		req, _ := http.NewRequest("POST", "/"+orgID.String()+"/staffing/upload", nil)
		// Missing multipart body
		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusBadRequest, w.Code)
		assert.Contains(t, w.Body.String(), "No file uploaded")
	})

	t.Run("Failure_InvalidCSVHeader", func(t *testing.T) {
		env.ResetMocks()

		csvData := &service.CSVData{
			Headers: []string{"wrong_header"},
			Rows:    []map[string]string{},
		}

		env.UploadService.On("ParseCSV", mock.Anything).Return(csvData, nil).Once()

		body := new(bytes.Buffer)
		writer := multipart.NewWriter(body)
		part, _ := writer.CreateFormFile("file", "bad.csv")
		part.Write([]byte("dummy"))
		writer.Close()

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("POST", "/"+orgID.String()+"/staffing/upload", body)
		req.Header.Set("Content-Type", writer.FormDataContentType())

		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusBadRequest, w.Code)
		assert.Contains(t, w.Body.String(), "Missing required header")
	})

	t.Run("Partial_Failure_RowValidation", func(t *testing.T) {
		env.ResetMocks()
		org := &database.Organization{ID: orgID, Name: "Clockwise"}

		csvData := &service.CSVData{
			Headers: []string{"full_name", "email", "role", "salary"},
			Rows: []map[string]string{
				// Invalid role
				{"full_name": "Bad Role", "email": "bad@test.com", "role": "wizard", "salary": "10"},
				// Valid
				{"full_name": "Good", "email": "good@test.com", "role": "staff", "salary": "10"},
			},
		}

		env.UploadService.On("ParseCSV", mock.Anything).Return(csvData, nil).Once()
		env.OrgStore.On("GetOrganizationByID", orgID).Return(org, nil).Once()

		// Only one CreateUser call expected
		env.UserStore.On("CreateUser", mock.MatchedBy(func(u *database.User) bool {
			return u.Email == "good@test.com"
		})).Return(nil).Once()

		env.EmailService.On("SendWelcomeEmail", "good@test.com", mock.Anything, mock.Anything, mock.Anything, mock.Anything).Return(nil).Once()

		body := new(bytes.Buffer)
		writer := multipart.NewWriter(body)
		part, _ := writer.CreateFormFile("file", "mixed.csv")
		part.Write([]byte("dummy"))
		writer.Close()

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("POST", "/"+orgID.String()+"/staffing/upload", body)
		req.Header.Set("Content-Type", writer.FormDataContentType())

		env.Router.ServeHTTP(w, req)
		time.Sleep(10 * time.Millisecond)

		assert.Equal(t, http.StatusOK, w.Code)

		// Check JSON response for failed count
		var resp map[string]interface{}
		json.Unmarshal(w.Body.Bytes(), &resp)

		assert.Equal(t, float64(1), resp["created_count"])
		assert.Equal(t, float64(1), resp["failed_count"]) // 1 failure
	})
}
