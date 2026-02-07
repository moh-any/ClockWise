package api

import (
	"errors"
	"log/slog"
	"net/http"
	"net/http/httptest"
	"os"
	"testing"
	"time"

	"github.com/clockwise/clockwise/backend/internal/api"
	"github.com/clockwise/clockwise/backend/internal/database"
	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
	"github.com/stretchr/testify/assert"
)

type ScheduleTestEnv struct {
	Router              *gin.Engine
	UserStore           *MockUserStore
	ScheduleStore       *MockScheduleStore
	OrgStore            *MockOrgStore
	RulesStore          *MockRulesStore
	UserRolesStore      *MockUserRolesStore
	OperatingHoursStore *MockOperatingHoursStore
	OrderStore          *MockOrderStore
	CampaignStore       *MockCampaignStore
	DemandStore         *MockDemandStore
	RoleStore           *MockRolesStore
	PreferenceStore     *MockPreferencesStore
	Handler             *api.ScheduleHandler
}

func setupScheduleEnv() *ScheduleTestEnv {
	gin.SetMode(gin.TestMode)

	userStore := new(MockUserStore)
	scheduleStore := new(MockScheduleStore)
	orgStore := new(MockOrgStore)
	rulesStore := new(MockRulesStore)
	userRolesStore := new(MockUserRolesStore)
	opHoursStore := new(MockOperatingHoursStore)
	orderStore := new(MockOrderStore)
	campaignStore := new(MockCampaignStore)
	demandStore := new(MockDemandStore)
	roleStore := new(MockRolesStore)
	preferenceStore := new(MockPreferencesStore)
	logger := slog.New(slog.NewTextHandler(os.Stdout, nil))

	handler := api.NewScheduleHandler(
		userStore, scheduleStore, logger,
		orgStore, rulesStore, userRolesStore,
		opHoursStore, orderStore, campaignStore,
		demandStore, roleStore, preferenceStore,
	)

	return &ScheduleTestEnv{
		Router:              gin.New(),
		UserStore:           userStore,
		ScheduleStore:       scheduleStore,
		OrgStore:            orgStore,
		RulesStore:          rulesStore,
		UserRolesStore:      userRolesStore,
		OperatingHoursStore: opHoursStore,
		OrderStore:          orderStore,
		CampaignStore:       campaignStore,
		DemandStore:         demandStore,
		RoleStore:           roleStore,
		PreferenceStore:     preferenceStore,
		Handler:             handler,
	}
}

func (env *ScheduleTestEnv) ResetMocks() {
	env.UserStore.ExpectedCalls = nil
	env.UserStore.Calls = nil
	env.ScheduleStore.ExpectedCalls = nil
	env.ScheduleStore.Calls = nil
	env.OrgStore.ExpectedCalls = nil
	env.OrgStore.Calls = nil
	env.RulesStore.ExpectedCalls = nil
	env.RulesStore.Calls = nil
	env.UserRolesStore.ExpectedCalls = nil
	env.UserRolesStore.Calls = nil
	env.OperatingHoursStore.ExpectedCalls = nil
	env.OperatingHoursStore.Calls = nil
	env.OrderStore.ExpectedCalls = nil
	env.OrderStore.Calls = nil
	env.CampaignStore.ExpectedCalls = nil
	env.CampaignStore.Calls = nil
	env.DemandStore.ExpectedCalls = nil
	env.DemandStore.Calls = nil
	env.RoleStore.ExpectedCalls = nil
	env.RoleStore.Calls = nil
	env.PreferenceStore.ExpectedCalls = nil
	env.PreferenceStore.Calls = nil
}

// --- GetScheduleHandler (full organization schedule) ---

func TestGetScheduleHandler(t *testing.T) {
	env := setupScheduleEnv()
	orgID := uuid.New()
	admin := &database.User{ID: uuid.New(), OrganizationID: orgID, UserRole: "admin"}

	env.Router.GET("/:org/schedule", authMiddleware(admin), env.Handler.GetScheduleHandler)

	t.Run("Success_Admin", func(t *testing.T) {
		env.ResetMocks()
		schedules := []database.Schedule{
			{
				Date:      time.Now(),
				Day:       "monday",
				StartTime: time.Date(2024, 1, 1, 9, 0, 0, 0, time.UTC),
				EndTime:   time.Date(2024, 1, 1, 17, 0, 0, 0, time.UTC),
				Employees: []string{uuid.New().String()},
			},
		}
		env.ScheduleStore.On("GetFullScheduleForSevenDays", orgID).Return(schedules, nil).Once()

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/"+orgID.String()+"/schedule", nil)
		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusOK, w.Code)
		assert.Contains(t, w.Body.String(), "Schedule retrieved successfully")
		assert.Contains(t, w.Body.String(), "monday")
		env.ScheduleStore.AssertExpectations(t)
	})

	t.Run("Success_Manager", func(t *testing.T) {
		env.ResetMocks()
		manager := &database.User{ID: uuid.New(), OrganizationID: orgID, UserRole: "manager"}
		router := gin.New()
		router.GET("/:org/schedule", authMiddleware(manager), env.Handler.GetScheduleHandler)

		schedules := []database.Schedule{}
		env.ScheduleStore.On("GetFullScheduleForSevenDays", orgID).Return(schedules, nil).Once()

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/"+orgID.String()+"/schedule", nil)
		router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusOK, w.Code)
		env.ScheduleStore.AssertExpectations(t)
	})

	t.Run("Failure_EmployeeForbidden", func(t *testing.T) {
		env.ResetMocks()
		employee := &database.User{ID: uuid.New(), OrganizationID: orgID, UserRole: "employee"}
		router := gin.New()
		router.GET("/:org/schedule", authMiddleware(employee), env.Handler.GetScheduleHandler)

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/"+orgID.String()+"/schedule", nil)
		router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusForbidden, w.Code)
		assert.Contains(t, w.Body.String(), "Only admins and managers")
	})

	t.Run("Failure_DBError", func(t *testing.T) {
		env.ResetMocks()
		env.ScheduleStore.On("GetFullScheduleForSevenDays", orgID).Return(nil, errors.New("db error")).Once()

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/"+orgID.String()+"/schedule", nil)
		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusInternalServerError, w.Code)
		assert.Contains(t, w.Body.String(), "Failed to retrieve schedule")
		env.ScheduleStore.AssertExpectations(t)
	})

	t.Run("Failure_Unauthorized", func(t *testing.T) {
		env.ResetMocks()
		router := gin.New()
		router.GET("/:org/schedule", authMiddleware(nil), env.Handler.GetScheduleHandler)

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/"+orgID.String()+"/schedule", nil)
		router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusUnauthorized, w.Code)
	})
}

// --- GetCurrentUserScheduleHandler ---

func TestGetCurrentUserScheduleHandler(t *testing.T) {
	env := setupScheduleEnv()
	orgID := uuid.New()
	employeeID := uuid.New()
	employee := &database.User{ID: employeeID, OrganizationID: orgID, UserRole: "employee"}

	env.Router.GET("/:org/schedule/me", authMiddleware(employee), env.Handler.GetCurrentUserScheduleHandler)

	t.Run("Success_Employee", func(t *testing.T) {
		env.ResetMocks()
		schedules := []database.Schedule{
			{
				Date:      time.Now(),
				Day:       "tuesday",
				StartTime: time.Date(2024, 1, 1, 8, 0, 0, 0, time.UTC),
				EndTime:   time.Date(2024, 1, 1, 16, 0, 0, 0, time.UTC),
				Employees: []string{employeeID.String()},
			},
		}
		env.ScheduleStore.On("GetScheduleForEmployeeForSevenDays", orgID, employeeID).Return(schedules, nil).Once()

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/"+orgID.String()+"/schedule/me", nil)
		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusOK, w.Code)
		assert.Contains(t, w.Body.String(), "Schedule retrieved successfully")
		assert.Contains(t, w.Body.String(), "tuesday")
		env.ScheduleStore.AssertExpectations(t)
	})

	t.Run("Success_Manager", func(t *testing.T) {
		env.ResetMocks()
		managerID := uuid.New()
		manager := &database.User{ID: managerID, OrganizationID: orgID, UserRole: "manager"}
		router := gin.New()
		router.GET("/:org/schedule/me", authMiddleware(manager), env.Handler.GetCurrentUserScheduleHandler)

		schedules := []database.Schedule{}
		env.ScheduleStore.On("GetScheduleForEmployeeForSevenDays", orgID, managerID).Return(schedules, nil).Once()

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/"+orgID.String()+"/schedule/me", nil)
		router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusOK, w.Code)
		env.ScheduleStore.AssertExpectations(t)
	})

	t.Run("Failure_AdminForbidden", func(t *testing.T) {
		env.ResetMocks()
		admin := &database.User{ID: uuid.New(), OrganizationID: orgID, UserRole: "admin"}
		router := gin.New()
		router.GET("/:org/schedule/me", authMiddleware(admin), env.Handler.GetCurrentUserScheduleHandler)

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/"+orgID.String()+"/schedule/me", nil)
		router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusForbidden, w.Code)
		assert.Contains(t, w.Body.String(), "Admin don't have schedules")
	})

	t.Run("Failure_DBError", func(t *testing.T) {
		env.ResetMocks()
		env.ScheduleStore.On("GetScheduleForEmployeeForSevenDays", orgID, employeeID).Return(nil, errors.New("db error")).Once()

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/"+orgID.String()+"/schedule/me", nil)
		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusInternalServerError, w.Code)
		assert.Contains(t, w.Body.String(), "Failed to retrieve schedule")
		env.ScheduleStore.AssertExpectations(t)
	})
}

// --- GetEmployeeScheduleHandler ---

func TestGetEmployeeScheduleHandler(t *testing.T) {
	env := setupScheduleEnv()
	orgID := uuid.New()
	admin := &database.User{ID: uuid.New(), OrganizationID: orgID, UserRole: "admin"}
	targetEmployeeID := uuid.New()

	env.Router.GET("/:org/schedule/employee/:id", authMiddleware(admin), env.Handler.GetEmployeeScheduleHandler)

	t.Run("Success", func(t *testing.T) {
		env.ResetMocks()
		targetEmployee := &database.User{ID: targetEmployeeID, OrganizationID: orgID, UserRole: "employee"}
		env.UserStore.On("GetUserByID", targetEmployeeID).Return(targetEmployee, nil).Once()

		schedules := []database.Schedule{
			{
				Date:      time.Now(),
				Day:       "wednesday",
				StartTime: time.Date(2024, 1, 1, 10, 0, 0, 0, time.UTC),
				EndTime:   time.Date(2024, 1, 1, 18, 0, 0, 0, time.UTC),
				Employees: []string{targetEmployeeID.String()},
			},
		}
		env.ScheduleStore.On("GetScheduleForEmployeeForSevenDays", orgID, targetEmployeeID).Return(schedules, nil).Once()

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/"+orgID.String()+"/schedule/employee/"+targetEmployeeID.String(), nil)
		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusOK, w.Code)
		assert.Contains(t, w.Body.String(), "Employee schedule retrieved successfully")
		assert.Contains(t, w.Body.String(), "wednesday")
		env.UserStore.AssertExpectations(t)
		env.ScheduleStore.AssertExpectations(t)
	})

	t.Run("Failure_InvalidEmployeeID", func(t *testing.T) {
		env.ResetMocks()

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/"+orgID.String()+"/schedule/employee/not-a-uuid", nil)
		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusBadRequest, w.Code)
		assert.Contains(t, w.Body.String(), "Invalid employee ID")
	})

	t.Run("Failure_EmployeeNotFound", func(t *testing.T) {
		env.ResetMocks()
		env.UserStore.On("GetUserByID", targetEmployeeID).Return(nil, errors.New("not found")).Once()

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/"+orgID.String()+"/schedule/employee/"+targetEmployeeID.String(), nil)
		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusNotFound, w.Code)
		assert.Contains(t, w.Body.String(), "Employee not found")
		env.UserStore.AssertExpectations(t)
	})

	t.Run("Failure_DifferentOrganization", func(t *testing.T) {
		env.ResetMocks()
		differentOrgID := uuid.New()
		targetEmployee := &database.User{ID: targetEmployeeID, OrganizationID: differentOrgID, UserRole: "employee"}
		env.UserStore.On("GetUserByID", targetEmployeeID).Return(targetEmployee, nil).Once()

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/"+orgID.String()+"/schedule/employee/"+targetEmployeeID.String(), nil)
		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusForbidden, w.Code)
		assert.Contains(t, w.Body.String(), "Access denied")
		env.UserStore.AssertExpectations(t)
	})

	t.Run("Failure_ScheduleDBError", func(t *testing.T) {
		env.ResetMocks()
		targetEmployee := &database.User{ID: targetEmployeeID, OrganizationID: orgID, UserRole: "employee"}
		env.UserStore.On("GetUserByID", targetEmployeeID).Return(targetEmployee, nil).Once()
		env.ScheduleStore.On("GetScheduleForEmployeeForSevenDays", orgID, targetEmployeeID).Return(nil, errors.New("db error")).Once()

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/"+orgID.String()+"/schedule/employee/"+targetEmployeeID.String(), nil)
		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusInternalServerError, w.Code)
		assert.Contains(t, w.Body.String(), "Failed to retrieve employee schedule")
		env.UserStore.AssertExpectations(t)
		env.ScheduleStore.AssertExpectations(t)
	})
}

// --- PredictScheduleHandler (validation & data-fetch tests, skipping ML call) ---

func TestPredictScheduleHandler(t *testing.T) {
	env := setupScheduleEnv()
	orgID := uuid.New()
	admin := &database.User{ID: uuid.New(), OrganizationID: orgID, UserRole: "admin"}

	env.Router.POST("/:org/schedule/predict", authMiddleware(admin), env.Handler.PredictScheduleHandler)

	t.Run("Failure_EmployeeForbidden", func(t *testing.T) {
		env.ResetMocks()
		employee := &database.User{ID: uuid.New(), OrganizationID: orgID, UserRole: "employee"}
		router := gin.New()
		router.POST("/:org/schedule/predict", authMiddleware(employee), env.Handler.PredictScheduleHandler)

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("POST", "/"+orgID.String()+"/schedule/predict", nil)
		router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusForbidden, w.Code)
	})

	t.Run("Failure_OrgError", func(t *testing.T) {
		env.ResetMocks()
		env.OrgStore.On("GetOrganizationByID", orgID).Return(nil, errors.New("db error")).Once()

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("POST", "/"+orgID.String()+"/schedule/predict", nil)
		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusInternalServerError, w.Code)
		assert.Contains(t, w.Body.String(), "failed to get organization details")
		env.OrgStore.AssertExpectations(t)
	})

	t.Run("Failure_RulesError", func(t *testing.T) {
		env.ResetMocks()
		org := &database.Organization{ID: orgID, Name: "Test Org", Type: "restaurant"}
		env.OrgStore.On("GetOrganizationByID", orgID).Return(org, nil).Once()
		env.RulesStore.On("GetRulesByOrganizationID", orgID).Return(nil, errors.New("db error")).Once()

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("POST", "/"+orgID.String()+"/schedule/predict", nil)
		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusInternalServerError, w.Code)
		assert.Contains(t, w.Body.String(), "failed to get organization rules details")
	})

	t.Run("Failure_OperatingHoursError", func(t *testing.T) {
		env.ResetMocks()
		org := &database.Organization{ID: orgID, Name: "Test Org", Type: "restaurant"}
		rules := &database.OrganizationRules{OrganizationID: orgID}
		env.OrgStore.On("GetOrganizationByID", orgID).Return(org, nil).Once()
		env.RulesStore.On("GetRulesByOrganizationID", orgID).Return(rules, nil).Once()
		env.OperatingHoursStore.On("GetOperatingHours", orgID).Return(nil, errors.New("db error")).Once()

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("POST", "/"+orgID.String()+"/schedule/predict", nil)
		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusInternalServerError, w.Code)
		assert.Contains(t, w.Body.String(), "failed to get organization operating hours details")
	})

	t.Run("Failure_DemandError", func(t *testing.T) {
		env.ResetMocks()
		org := &database.Organization{ID: orgID, Name: "Test Org", Type: "restaurant"}
		rules := &database.OrganizationRules{OrganizationID: orgID}
		opHours := []database.OperatingHours{{Weekday: "monday", OpeningTime: "09:00", ClosingTime: "17:00"}}
		env.OrgStore.On("GetOrganizationByID", orgID).Return(org, nil).Once()
		env.RulesStore.On("GetRulesByOrganizationID", orgID).Return(rules, nil).Once()
		env.OperatingHoursStore.On("GetOperatingHours", orgID).Return(opHours, nil).Once()
		env.DemandStore.On("GetLatestDemandHeatMap", orgID).Return(nil, errors.New("db error")).Once()

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("POST", "/"+orgID.String()+"/schedule/predict", nil)
		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusInternalServerError, w.Code)
		assert.Contains(t, w.Body.String(), "failed to get organization latest demands")
	})

	t.Run("Failure_RolesError", func(t *testing.T) {
		env.ResetMocks()
		org := &database.Organization{ID: orgID, Name: "Test Org", Type: "restaurant"}
		rules := &database.OrganizationRules{OrganizationID: orgID}
		opHours := []database.OperatingHours{{Weekday: "monday", OpeningTime: "09:00", ClosingTime: "17:00"}}
		demand := &database.DemandPredictResponse{Days: []database.PredictionDay{}}
		env.OrgStore.On("GetOrganizationByID", orgID).Return(org, nil).Once()
		env.RulesStore.On("GetRulesByOrganizationID", orgID).Return(rules, nil).Once()
		env.OperatingHoursStore.On("GetOperatingHours", orgID).Return(opHours, nil).Once()
		env.DemandStore.On("GetLatestDemandHeatMap", orgID).Return(demand, nil).Once()
		env.RoleStore.On("GetRolesByOrganizationID", orgID).Return(nil, errors.New("db error")).Once()

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("POST", "/"+orgID.String()+"/schedule/predict", nil)
		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusInternalServerError, w.Code)
	})

	t.Run("Failure_EmployeesError", func(t *testing.T) {
		env.ResetMocks()
		org := &database.Organization{ID: orgID, Name: "Test Org", Type: "restaurant"}
		rules := &database.OrganizationRules{OrganizationID: orgID}
		opHours := []database.OperatingHours{{Weekday: "monday", OpeningTime: "09:00", ClosingTime: "17:00"}}
		demand := &database.DemandPredictResponse{Days: []database.PredictionDay{}}
		roles := []database.OrganizationRole{{Role: "Server"}}
		env.OrgStore.On("GetOrganizationByID", orgID).Return(org, nil).Once()
		env.RulesStore.On("GetRulesByOrganizationID", orgID).Return(rules, nil).Once()
		env.OperatingHoursStore.On("GetOperatingHours", orgID).Return(opHours, nil).Once()
		env.DemandStore.On("GetLatestDemandHeatMap", orgID).Return(demand, nil).Once()
		env.RoleStore.On("GetRolesByOrganizationID", orgID).Return(roles, nil).Once()
		env.UserStore.On("GetUsersByOrganization", orgID).Return(nil, errors.New("db error")).Once()

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("POST", "/"+orgID.String()+"/schedule/predict", nil)
		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusInternalServerError, w.Code)
		assert.Contains(t, w.Body.String(), "failed to get employees from organization")
	})
}
