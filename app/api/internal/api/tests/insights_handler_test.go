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

type InsightTestEnv struct {
	Router       *gin.Engine
	InsightStore *MockInsightStore
	Handler      *api.InsightHandler
}

func setupInsightEnv() *InsightTestEnv {
	gin.SetMode(gin.TestMode)

	insightStore := new(MockInsightStore)
	logger := slog.New(slog.NewTextHandler(os.Stdout, nil))

	handler := api.NewInsightHandler(insightStore, logger)

	return &InsightTestEnv{
		Router:       gin.New(),
		InsightStore: insightStore,
		Handler:      handler,
	}
}

func TestGetInsightsHandler(t *testing.T) {
	env := setupInsightEnv()
	orgID := uuid.New()

	// Dummy insight data for verification
	dummyInsights := []database.Insight{
		{Title: "Test Insight", Statistic: "100"},
	}

	t.Run("Success_Admin", func(t *testing.T) {
		adminUser := &database.User{ID: uuid.New(), OrganizationID: orgID, UserRole: "admin"}

		// Setup expectations
		env.InsightStore.On("GetInsightsForAdmin", orgID).Return(dummyInsights, nil).Once()

		// Setup Request using the shared authMiddleware
		env.Router.GET("/:org/insights", authMiddleware(adminUser), env.Handler.GetInsightsHandler)
		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/"+orgID.String()+"/insights", nil)
		env.Router.ServeHTTP(w, req)

		// Assertions
		assert.Equal(t, http.StatusOK, w.Code)
		assert.Contains(t, w.Body.String(), "Test Insight")
		env.InsightStore.AssertExpectations(t)
	})

	t.Run("Success_Manager", func(t *testing.T) {
		managerUser := &database.User{ID: uuid.New(), OrganizationID: orgID, UserRole: "manager"}

		// Setup expectations
		env.InsightStore.On("GetInsightsForManager", orgID, managerUser.ID).Return(dummyInsights, nil).Once()

		r := gin.New()
		r.GET("/:org/insights", authMiddleware(managerUser), env.Handler.GetInsightsHandler)

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/"+orgID.String()+"/insights", nil)
		r.ServeHTTP(w, req)

		// Assertions
		assert.Equal(t, http.StatusOK, w.Code)
		env.InsightStore.AssertExpectations(t)
	})

	t.Run("Success_Employee", func(t *testing.T) {
		employeeUser := &database.User{ID: uuid.New(), OrganizationID: orgID, UserRole: "employee"}

		// Setup expectations
		env.InsightStore.On("GetInsightsForEmployee", orgID, employeeUser.ID).Return(dummyInsights, nil).Once()

		r := gin.New()
		r.GET("/:org/insights", authMiddleware(employeeUser), env.Handler.GetInsightsHandler)

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/"+orgID.String()+"/insights", nil)
		r.ServeHTTP(w, req)

		// Assertions
		assert.Equal(t, http.StatusOK, w.Code)
		env.InsightStore.AssertExpectations(t)
	})

	t.Run("Failure_StoreError", func(t *testing.T) {
		adminUser := &database.User{ID: uuid.New(), OrganizationID: orgID, UserRole: "admin"}

		// Setup expectations to fail
		env.InsightStore.On("GetInsightsForAdmin", orgID).Return(nil, errors.New("db error")).Once()

		r := gin.New()
		r.GET("/:org/insights", authMiddleware(adminUser), env.Handler.GetInsightsHandler)

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/"+orgID.String()+"/insights", nil)
		r.ServeHTTP(w, req)

		// Assertions
		assert.Equal(t, http.StatusInternalServerError, w.Code)
		assert.Contains(t, w.Body.String(), "Failed to retrieve insights")
		env.InsightStore.AssertExpectations(t)
	})

	t.Run("Failure_Unauthorized_NoUser", func(t *testing.T) {
		// No auth middleware injecting user
		r := gin.New()
		r.GET("/:org/insights", env.Handler.GetInsightsHandler)

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/"+orgID.String()+"/insights", nil)
		r.ServeHTTP(w, req)

		// Assertions
		assert.Equal(t, http.StatusUnauthorized, w.Code)
		assert.Contains(t, w.Body.String(), "invalid user in context")
	})
}
