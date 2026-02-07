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

type DashboardTestEnv struct {
	Router              *gin.Engine
	OrgStore            *MockOrgStore
	RulesStore          *MockRulesStore
	OperatingHoursStore *MockOperatingHoursStore
	OrderStore          *MockOrderStore
	CampaignStore       *MockCampaignStore
	DemandStore         *MockDemandStore
	Handler             *api.DashboardHandler
}

func setupDashboardEnv() *DashboardTestEnv {
	gin.SetMode(gin.TestMode)

	orgStore := new(MockOrgStore)
	rulesStore := new(MockRulesStore)
	opHoursStore := new(MockOperatingHoursStore)
	orderStore := new(MockOrderStore)
	campaignStore := new(MockCampaignStore)
	demandStore := new(MockDemandStore)
	logger := slog.New(slog.NewTextHandler(os.Stdout, nil))

	handler := api.NewDashboardHandler(orgStore, rulesStore, opHoursStore, orderStore, campaignStore, demandStore, logger)

	return &DashboardTestEnv{
		Router:              gin.New(),
		OrgStore:            orgStore,
		RulesStore:          rulesStore,
		OperatingHoursStore: opHoursStore,
		OrderStore:          orderStore,
		CampaignStore:       campaignStore,
		DemandStore:         demandStore,
		Handler:             handler,
	}
}

func (env *DashboardTestEnv) ResetMocks() {
	env.OrgStore.ExpectedCalls = nil
	env.OrgStore.Calls = nil
	env.RulesStore.ExpectedCalls = nil
	env.RulesStore.Calls = nil
	env.OperatingHoursStore.ExpectedCalls = nil
	env.OperatingHoursStore.Calls = nil
	env.OrderStore.ExpectedCalls = nil
	env.OrderStore.Calls = nil
	env.CampaignStore.ExpectedCalls = nil
	env.CampaignStore.Calls = nil
	env.DemandStore.ExpectedCalls = nil
	env.DemandStore.Calls = nil
}

// --- GetDemandHeatMap ---

func TestGetDemandHeatMapHandler(t *testing.T) {
	env := setupDashboardEnv()
	orgID := uuid.New()
	admin := &database.User{ID: uuid.New(), OrganizationID: orgID, UserRole: "admin"}

	env.Router.GET("/:org/dashboard/demand", authMiddleware(admin), env.Handler.GetDemandHeatMapHandler)

	t.Run("Success", func(t *testing.T) {
		env.ResetMocks()
		demandResp := &database.DemandPredictResponse{
			RestaurantName:   "Test Restaurant",
			PredictionPerion: "7 days",
			Days: []database.PredictionDay{
				{Day: "monday", Date: time.Now(), Hours: []database.PredictionHour{{HourNo: 10, OrderCount: 5, ItemCount: 20}}},
			},
		}
		env.DemandStore.On("GetLatestDemandHeatMap", orgID).Return(demandResp, nil).Once()

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/"+orgID.String()+"/dashboard/demand", nil)
		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusOK, w.Code)
		assert.Contains(t, w.Body.String(), "Test Restaurant")
		env.DemandStore.AssertExpectations(t)
	})

	t.Run("Success_Manager", func(t *testing.T) {
		env.ResetMocks()
		manager := &database.User{ID: uuid.New(), OrganizationID: orgID, UserRole: "manager"}
		router := gin.New()
		router.GET("/:org/dashboard/demand", authMiddleware(manager), env.Handler.GetDemandHeatMapHandler)

		demandResp := &database.DemandPredictResponse{
			RestaurantName:   "Test Restaurant",
			PredictionPerion: "7 days",
			Days:             []database.PredictionDay{},
		}
		env.DemandStore.On("GetLatestDemandHeatMap", orgID).Return(demandResp, nil).Once()

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/"+orgID.String()+"/dashboard/demand", nil)
		router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusOK, w.Code)
		env.DemandStore.AssertExpectations(t)
	})

	t.Run("Failure_EmployeeForbidden", func(t *testing.T) {
		env.ResetMocks()
		employee := &database.User{ID: uuid.New(), OrganizationID: orgID, UserRole: "employee"}
		router := gin.New()
		router.GET("/:org/dashboard/demand", authMiddleware(employee), env.Handler.GetDemandHeatMapHandler)

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/"+orgID.String()+"/dashboard/demand", nil)
		router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusForbidden, w.Code)
	})

	t.Run("Failure_NotFound", func(t *testing.T) {
		env.ResetMocks()
		env.DemandStore.On("GetLatestDemandHeatMap", orgID).Return(nil, nil).Once()

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/"+orgID.String()+"/dashboard/demand", nil)
		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusNotFound, w.Code)
		assert.Contains(t, w.Body.String(), "No demand data found")
		env.DemandStore.AssertExpectations(t)
	})

	t.Run("Failure_DBError", func(t *testing.T) {
		env.ResetMocks()
		env.DemandStore.On("GetLatestDemandHeatMap", orgID).Return(nil, errors.New("db error")).Once()

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/"+orgID.String()+"/dashboard/demand", nil)
		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusInternalServerError, w.Code)
		assert.Contains(t, w.Body.String(), "Failed to retrieve demand data")
		env.DemandStore.AssertExpectations(t)
	})

	t.Run("Failure_Unauthorized", func(t *testing.T) {
		env.ResetMocks()
		router := gin.New()
		router.GET("/:org/dashboard/demand", authMiddleware(nil), env.Handler.GetDemandHeatMapHandler)

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/"+orgID.String()+"/dashboard/demand", nil)
		router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusUnauthorized, w.Code)
	})
}

// --- PredictDemandHeatMap (partial - validation & data-fetch tests, skipping ML call) ---

func TestPredictDemandHeatMapHandler(t *testing.T) {
	env := setupDashboardEnv()
	orgID := uuid.New()
	admin := &database.User{ID: uuid.New(), OrganizationID: orgID, UserRole: "admin"}

	env.Router.POST("/:org/dashboard/demand/predict", authMiddleware(admin), env.Handler.PredictDemandHeatMapHandler)

	t.Run("Failure_EmployeeForbidden", func(t *testing.T) {
		env.ResetMocks()
		employee := &database.User{ID: uuid.New(), OrganizationID: orgID, UserRole: "employee"}
		router := gin.New()
		router.POST("/:org/dashboard/demand/predict", authMiddleware(employee), env.Handler.PredictDemandHeatMapHandler)

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("POST", "/"+orgID.String()+"/dashboard/demand/predict", nil)
		router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusForbidden, w.Code)
	})

	t.Run("Failure_OrgNotFound", func(t *testing.T) {
		env.ResetMocks()
		env.OrgStore.On("GetOrganizationByID", orgID).Return(nil, nil).Once()

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("POST", "/"+orgID.String()+"/dashboard/demand/predict", nil)
		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusNotFound, w.Code)
		assert.Contains(t, w.Body.String(), "organization not found")
		env.OrgStore.AssertExpectations(t)
	})

	t.Run("Failure_OrgDBError", func(t *testing.T) {
		env.ResetMocks()
		env.OrgStore.On("GetOrganizationByID", orgID).Return(nil, errors.New("db error")).Once()

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("POST", "/"+orgID.String()+"/dashboard/demand/predict", nil)
		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusInternalServerError, w.Code)
		assert.Contains(t, w.Body.String(), "failed to get organization details")
		env.OrgStore.AssertExpectations(t)
	})

	t.Run("Failure_RulesNotFound", func(t *testing.T) {
		env.ResetMocks()
		org := &database.Organization{ID: orgID, Name: "Test Org", Type: "restaurant"}
		env.OrgStore.On("GetOrganizationByID", orgID).Return(org, nil).Once()
		env.RulesStore.On("GetRulesByOrganizationID", orgID).Return(nil, nil).Once()

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("POST", "/"+orgID.String()+"/dashboard/demand/predict", nil)
		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusNotFound, w.Code)
		assert.Contains(t, w.Body.String(), "organization rules not found")
	})

	t.Run("Failure_OperatingHoursNotFound", func(t *testing.T) {
		env.ResetMocks()
		org := &database.Organization{ID: orgID, Name: "Test Org", Type: "restaurant"}
		rules := &database.OrganizationRules{OrganizationID: orgID}
		env.OrgStore.On("GetOrganizationByID", orgID).Return(org, nil).Once()
		env.RulesStore.On("GetRulesByOrganizationID", orgID).Return(rules, nil).Once()
		env.OperatingHoursStore.On("GetOperatingHours", orgID).Return(nil, nil).Once()

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("POST", "/"+orgID.String()+"/dashboard/demand/predict", nil)
		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusNotFound, w.Code)
		assert.Contains(t, w.Body.String(), "operating hours not found")
	})

	t.Run("Failure_NoOrders", func(t *testing.T) {
		env.ResetMocks()
		org := &database.Organization{ID: orgID, Name: "Test Org", Type: "restaurant"}
		rules := &database.OrganizationRules{OrganizationID: orgID}
		opHours := []database.OperatingHours{{Weekday: "monday", OpeningTime: "09:00", ClosingTime: "17:00"}}
		env.OrgStore.On("GetOrganizationByID", orgID).Return(org, nil).Once()
		env.RulesStore.On("GetRulesByOrganizationID", orgID).Return(rules, nil).Once()
		env.OperatingHoursStore.On("GetOperatingHours", orgID).Return(opHours, nil).Once()
		env.OrderStore.On("GetAllOrders", orgID).Return(nil, nil).Once()

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("POST", "/"+orgID.String()+"/dashboard/demand/predict", nil)
		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusNotFound, w.Code)
		assert.Contains(t, w.Body.String(), "no orders found")
	})

	t.Run("Failure_NoCampaigns", func(t *testing.T) {
		env.ResetMocks()
		org := &database.Organization{ID: orgID, Name: "Test Org", Type: "restaurant"}
		rules := &database.OrganizationRules{OrganizationID: orgID}
		opHours := []database.OperatingHours{{Weekday: "monday", OpeningTime: "09:00", ClosingTime: "17:00"}}
		orders := []database.Order{{OrderID: uuid.New(), OrderType: "dine-in", OrderStatus: "completed"}}
		env.OrgStore.On("GetOrganizationByID", orgID).Return(org, nil).Once()
		env.RulesStore.On("GetRulesByOrganizationID", orgID).Return(rules, nil).Once()
		env.OperatingHoursStore.On("GetOperatingHours", orgID).Return(opHours, nil).Once()
		env.OrderStore.On("GetAllOrders", orgID).Return(orders, nil).Once()
		env.CampaignStore.On("GetAllCampaigns", orgID).Return(nil, nil).Once()

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("POST", "/"+orgID.String()+"/dashboard/demand/predict", nil)
		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusNotFound, w.Code)
		assert.Contains(t, w.Body.String(), "no campaigns found")
	})
}
