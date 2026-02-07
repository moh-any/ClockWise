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

type CampaignTestEnv struct {
	Router              *gin.Engine
	CampaignStore       *MockCampaignStore
	UploadService       *MockUploadService
	OrderStore          *MockOrderStore
	OrgStore            *MockOrgStore
	OperatingHoursStore *MockOperatingHoursStore
	RulesStore          *MockRulesStore
	Handler             *api.CampaignHandler
}

func setupCampaignEnv() *CampaignTestEnv {
	gin.SetMode(gin.TestMode)

	campaignStore := new(MockCampaignStore)
	uploadService := new(MockUploadService)
	orderStore := new(MockOrderStore)
	orgStore := new(MockOrgStore)
	opHoursStore := new(MockOperatingHoursStore)
	rulesStore := new(MockRulesStore)
	logger := slog.New(slog.NewTextHandler(os.Stdout, nil))

	handler := api.NewCampaignHandler(campaignStore, uploadService, orderStore, orgStore, opHoursStore, rulesStore, logger)

	return &CampaignTestEnv{
		Router:              gin.New(),
		CampaignStore:       campaignStore,
		UploadService:       uploadService,
		OrderStore:          orderStore,
		OrgStore:            orgStore,
		OperatingHoursStore: opHoursStore,
		RulesStore:          rulesStore,
		Handler:             handler,
	}
}

func (env *CampaignTestEnv) ResetMocks() {
	env.CampaignStore.ExpectedCalls = nil
	env.CampaignStore.Calls = nil
	env.UploadService.ExpectedCalls = nil
	env.UploadService.Calls = nil
	env.OrderStore.ExpectedCalls = nil
	env.OrderStore.Calls = nil
	env.OrgStore.ExpectedCalls = nil
	env.OrgStore.Calls = nil
	env.OperatingHoursStore.ExpectedCalls = nil
	env.OperatingHoursStore.Calls = nil
	env.RulesStore.ExpectedCalls = nil
	env.RulesStore.Calls = nil
}

// --- GetAllCampaigns ---

func TestGetAllCampaignsHandler(t *testing.T) {
	env := setupCampaignEnv()
	orgID := uuid.New()
	admin := &database.User{ID: uuid.New(), OrganizationID: orgID, UserRole: "admin"}

	env.Router.GET("/:org/campaigns", authMiddleware(admin), env.Handler.GetAllCampaignsHandler)

	t.Run("Success", func(t *testing.T) {
		env.ResetMocks()
		discount := 10.0
		campaigns := []database.Campaign{
			{ID: uuid.New(), Name: "Summer Sale", Status: "active", StartTime: "2024-06-01", EndTime: "2024-06-30", DiscountPercent: &discount},
		}
		env.CampaignStore.On("GetAllCampaigns", orgID).Return(campaigns, nil).Once()

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/"+orgID.String()+"/campaigns", nil)
		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusOK, w.Code)
		assert.Contains(t, w.Body.String(), "Summer Sale")
		assert.Contains(t, w.Body.String(), "Campaigns retrieved successfully")
		env.CampaignStore.AssertExpectations(t)
	})

	t.Run("Failure_EmployeeForbidden", func(t *testing.T) {
		env.ResetMocks()
		employee := &database.User{ID: uuid.New(), OrganizationID: orgID, UserRole: "employee"}
		router := gin.New()
		router.GET("/:org/campaigns", authMiddleware(employee), env.Handler.GetAllCampaignsHandler)

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/"+orgID.String()+"/campaigns", nil)
		router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusForbidden, w.Code)
	})

	t.Run("Failure_DBError", func(t *testing.T) {
		env.ResetMocks()
		env.CampaignStore.On("GetAllCampaigns", orgID).Return(nil, errors.New("db error")).Once()

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/"+orgID.String()+"/campaigns", nil)
		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusInternalServerError, w.Code)
		assert.Contains(t, w.Body.String(), "Failed to retrieve campaigns")
		env.CampaignStore.AssertExpectations(t)
	})
}

// --- GetAllCampaignsForLastWeek ---

func TestGetAllCampaignsForLastWeekHandler(t *testing.T) {
	env := setupCampaignEnv()
	orgID := uuid.New()
	admin := &database.User{ID: uuid.New(), OrganizationID: orgID, UserRole: "admin"}

	env.Router.GET("/:org/campaigns/week", authMiddleware(admin), env.Handler.GetAllCampaignsForLastWeekHandler)

	t.Run("Success", func(t *testing.T) {
		env.ResetMocks()
		campaigns := []database.Campaign{
			{ID: uuid.New(), Name: "Flash Sale", Status: "completed"},
		}
		env.CampaignStore.On("GetAllCampaignsFromLastWeek", orgID).Return(campaigns, nil).Once()

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/"+orgID.String()+"/campaigns/week", nil)
		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusOK, w.Code)
		assert.Contains(t, w.Body.String(), "Flash Sale")
		env.CampaignStore.AssertExpectations(t)
	})

	t.Run("Failure_EmployeeForbidden", func(t *testing.T) {
		env.ResetMocks()
		employee := &database.User{ID: uuid.New(), OrganizationID: orgID, UserRole: "employee"}
		router := gin.New()
		router.GET("/:org/campaigns/week", authMiddleware(employee), env.Handler.GetAllCampaignsForLastWeekHandler)

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/"+orgID.String()+"/campaigns/week", nil)
		router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusForbidden, w.Code)
	})

	t.Run("Failure_DBError", func(t *testing.T) {
		env.ResetMocks()
		env.CampaignStore.On("GetAllCampaignsFromLastWeek", orgID).Return(nil, errors.New("db error")).Once()

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/"+orgID.String()+"/campaigns/week", nil)
		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusInternalServerError, w.Code)
		env.CampaignStore.AssertExpectations(t)
	})
}

// --- GetCampaignsInsights ---

func TestGetCampaignsInsightsHandler(t *testing.T) {
	env := setupCampaignEnv()
	orgID := uuid.New()
	admin := &database.User{ID: uuid.New(), OrganizationID: orgID, UserRole: "admin"}

	env.Router.GET("/:org/campaigns/insights", authMiddleware(admin), env.Handler.GetCampaignsInsightsHandler)

	t.Run("Success", func(t *testing.T) {
		env.ResetMocks()
		insights := []database.Insight{
			{Title: "Total Campaigns", Statistic: "12"},
		}
		env.CampaignStore.On("GetCampaignInsights", orgID).Return(insights, nil).Once()

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/"+orgID.String()+"/campaigns/insights", nil)
		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusOK, w.Code)
		assert.Contains(t, w.Body.String(), "Total Campaigns")
		assert.Contains(t, w.Body.String(), "Campaign insights retrieved successfully")
		env.CampaignStore.AssertExpectations(t)
	})

	t.Run("Failure_EmployeeForbidden", func(t *testing.T) {
		env.ResetMocks()
		employee := &database.User{ID: uuid.New(), OrganizationID: orgID, UserRole: "employee"}
		router := gin.New()
		router.GET("/:org/campaigns/insights", authMiddleware(employee), env.Handler.GetCampaignsInsightsHandler)

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/"+orgID.String()+"/campaigns/insights", nil)
		router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusForbidden, w.Code)
	})

	t.Run("Failure_DBError", func(t *testing.T) {
		env.ResetMocks()
		env.CampaignStore.On("GetCampaignInsights", orgID).Return(nil, errors.New("db error")).Once()

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/"+orgID.String()+"/campaigns/insights", nil)
		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusInternalServerError, w.Code)
		env.CampaignStore.AssertExpectations(t)
	})
}

// --- RecommendCampaignsHandler (validation tests only, no real ML calls) ---

func TestRecommendCampaignsHandler(t *testing.T) {
	env := setupCampaignEnv()
	orgID := uuid.New()
	admin := &database.User{ID: uuid.New(), OrganizationID: orgID, UserRole: "admin"}

	env.Router.POST("/:org/campaigns/recommend", authMiddleware(admin), env.Handler.RecommendCampaignsHandler)

	t.Run("Failure_EmployeeForbidden", func(t *testing.T) {
		env.ResetMocks()
		employee := &database.User{ID: uuid.New(), OrganizationID: orgID, UserRole: "employee"}
		router := gin.New()
		router.POST("/:org/campaigns/recommend", authMiddleware(employee), env.Handler.RecommendCampaignsHandler)

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("POST", "/"+orgID.String()+"/campaigns/recommend", nil)
		req.Header.Set("Content-Type", "application/json")
		router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusForbidden, w.Code)
		assert.Contains(t, w.Body.String(), "Only admins and managers")
	})

	t.Run("Failure_InvalidBody", func(t *testing.T) {
		env.ResetMocks()

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("POST", "/"+orgID.String()+"/campaigns/recommend", nil)
		req.Header.Set("Content-Type", "application/json")
		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusBadRequest, w.Code)
	})
}

// --- SubmitCampaignFeedbackHandler (validation tests only) ---

func TestSubmitCampaignFeedbackHandler(t *testing.T) {
	env := setupCampaignEnv()
	orgID := uuid.New()
	admin := &database.User{ID: uuid.New(), OrganizationID: orgID, UserRole: "admin"}

	env.Router.POST("/:org/campaigns/feedback", authMiddleware(admin), env.Handler.SubmitCampaignFeedbackHandler)

	t.Run("Failure_EmployeeForbidden", func(t *testing.T) {
		env.ResetMocks()
		employee := &database.User{ID: uuid.New(), OrganizationID: orgID, UserRole: "employee"}
		router := gin.New()
		router.POST("/:org/campaigns/feedback", authMiddleware(employee), env.Handler.SubmitCampaignFeedbackHandler)

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("POST", "/"+orgID.String()+"/campaigns/feedback", nil)
		req.Header.Set("Content-Type", "application/json")
		router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusForbidden, w.Code)
		assert.Contains(t, w.Body.String(), "Only admins and managers")
	})

	t.Run("Failure_InvalidBody", func(t *testing.T) {
		env.ResetMocks()

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("POST", "/"+orgID.String()+"/campaigns/feedback", nil)
		req.Header.Set("Content-Type", "application/json")
		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusBadRequest, w.Code)
	})
}
