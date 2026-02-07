package api

import (
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
)

type AlertTestEnv struct {
	Router     *gin.Engine
	AlertStore *MockAlertStore
	Handler    *api.AlertHandler
}

func setupAlertEnv() *AlertTestEnv {
	gin.SetMode(gin.TestMode)

	alertStore := new(MockAlertStore)
	logger := slog.New(slog.NewTextHandler(os.Stdout, nil))

	handler := api.NewAlertHandler(alertStore, logger)

	return &AlertTestEnv{
		Router:     gin.New(),
		AlertStore: alertStore,
		Handler:    handler,
	}
}

func (env *AlertTestEnv) ResetMocks() {
	env.AlertStore.ExpectedCalls = nil
	env.AlertStore.Calls = nil
}

// --- GetAllAlerts ---

func TestGetAllAlertsHandler(t *testing.T) {
	env := setupAlertEnv()
	orgID := uuid.New()
	admin := &database.User{ID: uuid.New(), OrganizationID: orgID, UserRole: "admin"}

	env.Router.GET("/:org/alerts", authMiddleware(admin), env.Handler.GetAllAlertsHandler)

	t.Run("Success_Admin", func(t *testing.T) {
		env.ResetMocks()
		alerts := []database.Alert{
			{Id: uuid.New(), Organization: orgID, Severity: "high", Subject: "Test Alert", Message: "Something happened"},
		}
		env.AlertStore.On("GetAllAlerts", orgID).Return(alerts, nil).Once()

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/"+orgID.String()+"/alerts", nil)
		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusOK, w.Code)
		assert.Contains(t, w.Body.String(), "Test Alert")
		assert.Contains(t, w.Body.String(), "Alerts retrieved successfully")
		env.AlertStore.AssertExpectations(t)
	})

	t.Run("Success_Manager", func(t *testing.T) {
		env.ResetMocks()
		manager := &database.User{ID: uuid.New(), OrganizationID: orgID, UserRole: "manager"}
		router := gin.New()
		router.GET("/:org/alerts", authMiddleware(manager), env.Handler.GetAllAlertsHandler)

		alerts := []database.Alert{}
		env.AlertStore.On("GetAllAlerts", orgID).Return(alerts, nil).Once()

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/"+orgID.String()+"/alerts", nil)
		router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusOK, w.Code)
		env.AlertStore.AssertExpectations(t)
	})

	t.Run("Failure_EmployeeForbidden", func(t *testing.T) {
		env.ResetMocks()
		employee := &database.User{ID: uuid.New(), OrganizationID: orgID, UserRole: "employee"}
		router := gin.New()
		router.GET("/:org/alerts", authMiddleware(employee), env.Handler.GetAllAlertsHandler)

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/"+orgID.String()+"/alerts", nil)
		router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusForbidden, w.Code)
		assert.Contains(t, w.Body.String(), "Access denied")
	})

	t.Run("Failure_DBError", func(t *testing.T) {
		env.ResetMocks()
		env.AlertStore.On("GetAllAlerts", orgID).Return(nil, errors.New("db error")).Once()

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/"+orgID.String()+"/alerts", nil)
		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusInternalServerError, w.Code)
		assert.Contains(t, w.Body.String(), "Failed to retrieve alerts")
		env.AlertStore.AssertExpectations(t)
	})

	t.Run("Failure_Unauthorized", func(t *testing.T) {
		env.ResetMocks()
		router := gin.New()
		router.GET("/:org/alerts", authMiddleware(nil), env.Handler.GetAllAlertsHandler)

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/"+orgID.String()+"/alerts", nil)
		router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusUnauthorized, w.Code)
	})
}

// --- GetAllAlertsForLastWeek ---

func TestGetAllAlertsForLastWeekHandler(t *testing.T) {
	env := setupAlertEnv()
	orgID := uuid.New()
	admin := &database.User{ID: uuid.New(), OrganizationID: orgID, UserRole: "admin"}

	env.Router.GET("/:org/alerts/week", authMiddleware(admin), env.Handler.GetAllAlertsForLastWeekHandler)

	t.Run("Success", func(t *testing.T) {
		env.ResetMocks()
		alerts := []database.Alert{
			{Id: uuid.New(), Organization: orgID, Severity: "critical", Subject: "Weekly", Message: "msg"},
		}
		env.AlertStore.On("GetAllAlertsForLastWeek", orgID).Return(alerts, nil).Once()

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/"+orgID.String()+"/alerts/week", nil)
		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusOK, w.Code)
		assert.Contains(t, w.Body.String(), "Weekly")
		assert.Contains(t, w.Body.String(), "Alerts for last week retrieved successfully")
		env.AlertStore.AssertExpectations(t)
	})

	t.Run("Failure_EmployeeForbidden", func(t *testing.T) {
		env.ResetMocks()
		employee := &database.User{ID: uuid.New(), OrganizationID: orgID, UserRole: "employee"}
		router := gin.New()
		router.GET("/:org/alerts/week", authMiddleware(employee), env.Handler.GetAllAlertsForLastWeekHandler)

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/"+orgID.String()+"/alerts/week", nil)
		router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusForbidden, w.Code)
	})

	t.Run("Failure_DBError", func(t *testing.T) {
		env.ResetMocks()
		env.AlertStore.On("GetAllAlertsForLastWeek", orgID).Return(nil, errors.New("db error")).Once()

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/"+orgID.String()+"/alerts/week", nil)
		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusInternalServerError, w.Code)
		env.AlertStore.AssertExpectations(t)
	})
}

// --- GetAlertInsights ---

func TestGetAlertInsightsHandler(t *testing.T) {
	env := setupAlertEnv()
	orgID := uuid.New()
	admin := &database.User{ID: uuid.New(), OrganizationID: orgID, UserRole: "admin"}

	env.Router.GET("/:org/alerts/insights", authMiddleware(admin), env.Handler.GetAlertInsightsHandler)

	t.Run("Success", func(t *testing.T) {
		env.ResetMocks()
		insights := []database.Insight{
			{Title: "Total Alerts", Statistic: "42"},
		}
		env.AlertStore.On("GetAlertInsights", orgID).Return(insights, nil).Once()

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/"+orgID.String()+"/alerts/insights", nil)
		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusOK, w.Code)
		assert.Contains(t, w.Body.String(), "Total Alerts")
		assert.Contains(t, w.Body.String(), "Alert insights retrieved successfully")
		env.AlertStore.AssertExpectations(t)
	})

	t.Run("Failure_EmployeeForbidden", func(t *testing.T) {
		env.ResetMocks()
		employee := &database.User{ID: uuid.New(), OrganizationID: orgID, UserRole: "employee"}
		router := gin.New()
		router.GET("/:org/alerts/insights", authMiddleware(employee), env.Handler.GetAlertInsightsHandler)

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/"+orgID.String()+"/alerts/insights", nil)
		router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusForbidden, w.Code)
	})

	t.Run("Failure_DBError", func(t *testing.T) {
		env.ResetMocks()
		env.AlertStore.On("GetAlertInsights", orgID).Return(nil, errors.New("db error")).Once()

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/"+orgID.String()+"/alerts/insights", nil)
		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusInternalServerError, w.Code)
		assert.Contains(t, w.Body.String(), "Failed to retrieve alert insights")
		env.AlertStore.AssertExpectations(t)
	})
}
