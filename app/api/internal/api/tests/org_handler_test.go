package api

import (
	"bytes"
	"encoding/json"
	"errors"
	"log/slog"
	"net/http"
	"net/http/httptest"
	"os"
	"testing"

	"github.com/clockwise/clockwise/backend/internal/api"
	"github.com/clockwise/clockwise/backend/internal/database"
	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/mock"
)

type OrgTestEnv struct {
	Router         *gin.Engine
	OrgStore       *MockOrgStore
	UserStore      *MockUserStore
	RolesStore     *MockRolesStore
	UserRolesStore *MockUserRolesStore
	EmailService   *MockEmailService
	Handler        *api.OrgHandler
}

func setupOrgEnv() *OrgTestEnv {
	gin.SetMode(gin.TestMode)

	orgStore := new(MockOrgStore)
	userStore := new(MockUserStore)
	rolesStore := new(MockRolesStore)
	userRolesStore := new(MockUserRolesStore)
	emailService := new(MockEmailService)
	logger := slog.New(slog.NewTextHandler(os.Stdout, nil))

	handler := api.NewOrgHandler(orgStore, userStore, userRolesStore, rolesStore, emailService, logger)

	return &OrgTestEnv{
		Router:         gin.New(),
		OrgStore:       orgStore,
		UserStore:      userStore,
		RolesStore:     rolesStore,
		UserRolesStore: userRolesStore,
		EmailService:   emailService,
		Handler:        handler,
	}
}

func TestRegisterOrganization(t *testing.T) {
	env := setupOrgEnv()

	env.Router.POST("/register", env.Handler.RegisterOrganization)

	t.Run("Success", func(t *testing.T) {
		reqBody := api.RegisterOrgRequest{
			OrgName:       "Test Org",
			OrgAddress:    "123 St",
			OrgType:       "restaurant",
			OrgPhone:      "+1234567890",
			AdminFullName: "Admin User",
			AdminEmail:    "admin@test.com",
			AdminPassword: "password123",
			Hex1:          "000000",
			Hex2:          "111111",
			Hex3:          "222222",
		}

		env.OrgStore.On("CreateOrgWithAdmin", mock.Anything, mock.Anything, reqBody.AdminPassword).Return(nil).Once()

		jsonBytes, _ := json.Marshal(reqBody)
		req, _ := http.NewRequest("POST", "/register", bytes.NewBuffer(jsonBytes))
		req.Header.Set("Content-Type", "application/json")
		w := httptest.NewRecorder()

		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusCreated, w.Code)
		env.OrgStore.AssertExpectations(t)
	})

	t.Run("BadRequest_InvalidJSON", func(t *testing.T) {
		req, _ := http.NewRequest("POST", "/register", bytes.NewBufferString("{invalid"))
		req.Header.Set("Content-Type", "application/json")

		w := httptest.NewRecorder()

		env.Router.ServeHTTP(w, req)

		if w.Code != http.StatusBadRequest {
			t.Logf("Expected 400, got %d. Body: %s", w.Code, w.Body.String())
		}

		assert.Equal(t, http.StatusBadRequest, w.Code)
	})
}

func TestDelegateUser(t *testing.T) {
	env := setupOrgEnv()
	orgID := uuid.New()
	adminUser := &database.User{ID: uuid.New(), OrganizationID: orgID, UserRole: "admin", Email: "admin@test.com"}
	salary := 20.0

	t.Run("Success_SimpleDelegation", func(t *testing.T) {
		reqBody := api.DelegateUserRequest{
			FullName:      "New Employee",
			Email:         "new@test.com",
			Role:          "employee",
			SalaryPerHour: &salary,
		}

		org := &database.Organization{ID: orgID, Name: "Clockwise"}

		env.OrgStore.On("GetOrganizationByID", orgID).Return(org, nil).Once()
		env.UserStore.On("CreateUser", mock.MatchedBy(func(u *database.User) bool {
			return u.Email == reqBody.Email && u.UserRole == reqBody.Role
		})).Return(nil).Once()

		env.EmailService.On("SendWelcomeEmail", reqBody.Email, reqBody.FullName, mock.AnythingOfType("string"), reqBody.Role, org.Name).Return(nil).Once()

		jsonBytes, _ := json.Marshal(reqBody)
		r := gin.New()

		r.POST("/:org/staffing", authMiddleware(adminUser), env.Handler.DelegateUser)

		req, _ := http.NewRequest("POST", "/"+orgID.String()+"/staffing", bytes.NewBuffer(jsonBytes))
		w := httptest.NewRecorder()
		r.ServeHTTP(w, req)

		assert.Equal(t, http.StatusCreated, w.Code)
	})

	salary = 30.0
	t.Run("Success_WithRoles", func(t *testing.T) {
		reqBody := api.DelegateUserRequest{
			FullName:      "Manager User",
			Email:         "mgr@test.com",
			Role:          "manager",
			SalaryPerHour: &salary,
		}

		org := &database.Organization{ID: orgID, Name: "Clockwise"}

		env.OrgStore.On("GetOrganizationByID", orgID).Return(org, nil).Once()
		env.UserStore.On("CreateUser", mock.Anything).Return(nil).Once()
		env.EmailService.On("SendWelcomeEmail", mock.Anything, mock.Anything, mock.Anything, mock.Anything, mock.Anything).Return(nil).Once()

		jsonBytes, _ := json.Marshal(reqBody)
		r := gin.New()
		r.POST("/:org/staffing", authMiddleware(adminUser), env.Handler.DelegateUser)

		req, _ := http.NewRequest("POST", "/"+orgID.String()+"/staffing", bytes.NewBuffer(jsonBytes))
		w := httptest.NewRecorder()
		r.ServeHTTP(w, req)

		assert.Equal(t, http.StatusCreated, w.Code)
	})

	t.Run("Failure_ForbiddenForStaff", func(t *testing.T) {
		staffUser := &database.User{ID: uuid.New(), OrganizationID: orgID, UserRole: "staff"}

		r := gin.New()
		r.POST("/:org/staffing", authMiddleware(staffUser), env.Handler.DelegateUser)

		req, _ := http.NewRequest("POST", "/"+orgID.String()+"/staffing", nil)
		w := httptest.NewRecorder()
		r.ServeHTTP(w, req)

		assert.Equal(t, http.StatusBadRequest, w.Code)
	})
	salary = 10.0
	t.Run("Failure_InvalidRole", func(t *testing.T) {
		reqBody := api.DelegateUserRequest{
			FullName:      "Bad Role User",
			Email:         "bad@test.com",
			Role:          "invalid_role",
			SalaryPerHour: &salary,
		}
		jsonBytes, _ := json.Marshal(reqBody)
		r := gin.New()
		r.POST("/:org/staffing", authMiddleware(adminUser), env.Handler.DelegateUser)

		req, _ := http.NewRequest("POST", "/"+orgID.String()+"/staffing", bytes.NewBuffer(jsonBytes))
		w := httptest.NewRecorder()
		r.ServeHTTP(w, req)
		t.Logf("Response Body: %s", w.Body.String())
		t.Logf("Response Code: %d", w.Code)
		assert.Equal(t, http.StatusBadRequest, w.Code)
		assert.Contains(t, w.Body.String(), "Key: 'DelegateUserRequest.Role' Error:Field validation for 'Role' failed on the 'oneof' tag")
	})
}

func TestGetOrganizationProfile(t *testing.T) {
	env := setupOrgEnv()
	orgID := uuid.New()
	user := &database.User{ID: uuid.New(), OrganizationID: orgID, UserRole: "admin"}

	t.Run("Success", func(t *testing.T) {
		profile := &database.OrganizationProfile{
			Name:              "Clockwise",
			NumberOfEmployees: 10,
		}

		env.OrgStore.On("GetOrganizationProfile", orgID).Return(profile, nil).Once()

		r := gin.New()
		r.GET("/:org/profile", authMiddleware(user), env.Handler.GetOrganizationProfile)

		req, _ := http.NewRequest("GET", "/"+orgID.String()+"/profile", nil)
		w := httptest.NewRecorder()
		r.ServeHTTP(w, req)

		assert.Equal(t, http.StatusOK, w.Code)
		assert.Contains(t, w.Body.String(), "Clockwise")
	})

	t.Run("Unauthorized", func(t *testing.T) {
		r := gin.New()
		r.GET("/:org/profile", env.Handler.GetOrganizationProfile)

		req, _ := http.NewRequest("GET", "/"+orgID.String()+"/profile", nil)
		w := httptest.NewRecorder()
		r.ServeHTTP(w, req)

		assert.Equal(t, http.StatusUnauthorized, w.Code)
	})

	t.Run("StoreError", func(t *testing.T) {
		env.OrgStore.On("GetOrganizationProfile", orgID).Return(nil, errors.New("db error")).Once()

		r := gin.New()
		r.GET("/:org/profile", authMiddleware(user), env.Handler.GetOrganizationProfile)

		req, _ := http.NewRequest("GET", "/"+orgID.String()+"/profile", nil)
		w := httptest.NewRecorder()
		r.ServeHTTP(w, req)

		assert.Equal(t, http.StatusInternalServerError, w.Code)
	})
}
