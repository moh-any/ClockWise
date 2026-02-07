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

type OrderTestEnv struct {
	Router        *gin.Engine
	OrderStore    *MockOrderStore
	UploadService *MockUploadService
	Handler       *api.OrderHandler
}

func setupOrderEnv() *OrderTestEnv {
	gin.SetMode(gin.TestMode)

	orderStore := new(MockOrderStore)
	uploadService := new(MockUploadService)
	logger := slog.New(slog.NewTextHandler(os.Stdout, nil))

	handler := api.NewOrderHandler(orderStore, uploadService, logger)

	return &OrderTestEnv{
		Router:        gin.New(),
		OrderStore:    orderStore,
		UploadService: uploadService,
		Handler:       handler,
	}
}

func (env *OrderTestEnv) ResetMocks() {
	env.OrderStore.ExpectedCalls = nil
	env.OrderStore.Calls = nil
	env.UploadService.ExpectedCalls = nil
	env.UploadService.Calls = nil
}

// --- GetAllOrders ---

func TestGetAllOrdersHandler(t *testing.T) {
	env := setupOrderEnv()
	orgID := uuid.New()
	admin := &database.User{ID: uuid.New(), OrganizationID: orgID, UserRole: "admin"}

	env.Router.GET("/:org/orders", authMiddleware(admin), env.Handler.GetAllOrders)

	t.Run("Success", func(t *testing.T) {
		env.ResetMocks()
		total := 25.50
		orders := []database.Order{
			{OrderID: uuid.New(), UserID: uuid.New(), OrganizationID: orgID, CreateTime: time.Now(), OrderType: "dine-in", OrderStatus: "completed", TotalAmount: &total},
		}
		env.OrderStore.On("GetAllOrders", orgID).Return(orders, nil).Once()

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/"+orgID.String()+"/orders", nil)
		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusOK, w.Code)
		assert.Contains(t, w.Body.String(), "Orders retrieved successfully")
		assert.Contains(t, w.Body.String(), "dine-in")
		env.OrderStore.AssertExpectations(t)
	})

	t.Run("Failure_EmployeeForbidden", func(t *testing.T) {
		env.ResetMocks()
		employee := &database.User{ID: uuid.New(), OrganizationID: orgID, UserRole: "employee"}
		router := gin.New()
		router.GET("/:org/orders", authMiddleware(employee), env.Handler.GetAllOrders)

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/"+orgID.String()+"/orders", nil)
		router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusForbidden, w.Code)
		assert.Contains(t, w.Body.String(), "Only admins and managers")
	})

	t.Run("Failure_DBError", func(t *testing.T) {
		env.ResetMocks()
		env.OrderStore.On("GetAllOrders", orgID).Return(nil, errors.New("db error")).Once()

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/"+orgID.String()+"/orders", nil)
		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusInternalServerError, w.Code)
		assert.Contains(t, w.Body.String(), "Failed to retrieve orders")
		env.OrderStore.AssertExpectations(t)
	})
}

// --- GetAllOrdersForLastWeek ---

func TestGetAllOrdersForLastWeekHandler(t *testing.T) {
	env := setupOrderEnv()
	orgID := uuid.New()
	admin := &database.User{ID: uuid.New(), OrganizationID: orgID, UserRole: "admin"}

	env.Router.GET("/:org/orders/week", authMiddleware(admin), env.Handler.GetAllOrdersForLastWeek)

	t.Run("Success", func(t *testing.T) {
		env.ResetMocks()
		orders := []database.Order{
			{OrderID: uuid.New(), OrderType: "delivery", OrderStatus: "completed"},
		}
		env.OrderStore.On("GetAllOrdersForLastWeek", orgID).Return(orders, nil).Once()

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/"+orgID.String()+"/orders/week", nil)
		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusOK, w.Code)
		assert.Contains(t, w.Body.String(), "Orders retrieved successfully")
		env.OrderStore.AssertExpectations(t)
	})

	t.Run("Failure_EmployeeForbidden", func(t *testing.T) {
		env.ResetMocks()
		employee := &database.User{ID: uuid.New(), OrganizationID: orgID, UserRole: "employee"}
		router := gin.New()
		router.GET("/:org/orders/week", authMiddleware(employee), env.Handler.GetAllOrdersForLastWeek)

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/"+orgID.String()+"/orders/week", nil)
		router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusForbidden, w.Code)
	})

	t.Run("Failure_DBError", func(t *testing.T) {
		env.ResetMocks()
		env.OrderStore.On("GetAllOrdersForLastWeek", orgID).Return(nil, errors.New("db error")).Once()

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/"+orgID.String()+"/orders/week", nil)
		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusInternalServerError, w.Code)
		env.OrderStore.AssertExpectations(t)
	})
}

// --- GetAllOrdersToday ---

func TestGetAllOrdersTodayHandler(t *testing.T) {
	env := setupOrderEnv()
	orgID := uuid.New()
	admin := &database.User{ID: uuid.New(), OrganizationID: orgID, UserRole: "admin"}

	env.Router.GET("/:org/orders/today", authMiddleware(admin), env.Handler.GetAllOrdersToday)

	t.Run("Success", func(t *testing.T) {
		env.ResetMocks()
		orders := []database.Order{
			{OrderID: uuid.New(), OrderType: "takeout", OrderStatus: "pending"},
		}
		env.OrderStore.On("GetTodaysOrder", orgID).Return(orders, nil).Once()

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/"+orgID.String()+"/orders/today", nil)
		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusOK, w.Code)
		assert.Contains(t, w.Body.String(), "Orders retrieved successfully")
		env.OrderStore.AssertExpectations(t)
	})

	t.Run("Failure_EmployeeForbidden", func(t *testing.T) {
		env.ResetMocks()
		employee := &database.User{ID: uuid.New(), OrganizationID: orgID, UserRole: "employee"}
		router := gin.New()
		router.GET("/:org/orders/today", authMiddleware(employee), env.Handler.GetAllOrdersToday)

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/"+orgID.String()+"/orders/today", nil)
		router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusForbidden, w.Code)
	})

	t.Run("Failure_DBError", func(t *testing.T) {
		env.ResetMocks()
		env.OrderStore.On("GetTodaysOrder", orgID).Return(nil, errors.New("db error")).Once()

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/"+orgID.String()+"/orders/today", nil)
		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusInternalServerError, w.Code)
		env.OrderStore.AssertExpectations(t)
	})
}

// --- GetOrdersInsights ---

func TestGetOrdersInsightsHandler(t *testing.T) {
	env := setupOrderEnv()
	orgID := uuid.New()
	admin := &database.User{ID: uuid.New(), OrganizationID: orgID, UserRole: "admin"}

	env.Router.GET("/:org/orders/insights", authMiddleware(admin), env.Handler.GetOrdersInsights)

	t.Run("Success", func(t *testing.T) {
		env.ResetMocks()
		insights := []database.Insight{
			{Title: "Total Orders", Statistic: "150"},
			{Title: "Average Order Value", Statistic: "$25.00"},
		}
		env.OrderStore.On("GetOrdersInsights", orgID).Return(insights, nil).Once()

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/"+orgID.String()+"/orders/insights", nil)
		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusOK, w.Code)
		assert.Contains(t, w.Body.String(), "Order insights retrieved successfully")
		assert.Contains(t, w.Body.String(), "Total Orders")
		env.OrderStore.AssertExpectations(t)
	})

	t.Run("Failure_DBError", func(t *testing.T) {
		env.ResetMocks()
		env.OrderStore.On("GetOrdersInsights", orgID).Return(nil, errors.New("db error")).Once()

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/"+orgID.String()+"/orders/insights", nil)
		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusInternalServerError, w.Code)
		assert.Contains(t, w.Body.String(), "Failed to retrieve order insights")
		env.OrderStore.AssertExpectations(t)
	})
}

// --- GetAllItems ---

func TestGetAllItemsHandler(t *testing.T) {
	env := setupOrderEnv()
	orgID := uuid.New()
	admin := &database.User{ID: uuid.New(), OrganizationID: orgID, UserRole: "admin"}

	env.Router.GET("/:org/items", authMiddleware(admin), env.Handler.GetAllItems)

	t.Run("Success", func(t *testing.T) {
		env.ResetMocks()
		price := 12.99
		neededEmp := 2
		items := []database.Item{
			{ItemID: uuid.New(), Name: "Burger", Price: &price, NeededNumEmployeesToPrepare: &neededEmp},
		}
		env.OrderStore.On("GetAllItems", orgID).Return(items, nil).Once()

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/"+orgID.String()+"/items", nil)
		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusOK, w.Code)
		assert.Contains(t, w.Body.String(), "Items retrieved successfully")
		assert.Contains(t, w.Body.String(), "Burger")
		env.OrderStore.AssertExpectations(t)
	})

	t.Run("Failure_EmployeeForbidden", func(t *testing.T) {
		env.ResetMocks()
		employee := &database.User{ID: uuid.New(), OrganizationID: orgID, UserRole: "employee"}
		router := gin.New()
		router.GET("/:org/items", authMiddleware(employee), env.Handler.GetAllItems)

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/"+orgID.String()+"/items", nil)
		router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusForbidden, w.Code)
	})

	t.Run("Failure_DBError", func(t *testing.T) {
		env.ResetMocks()
		env.OrderStore.On("GetAllItems", orgID).Return(nil, errors.New("db error")).Once()

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/"+orgID.String()+"/items", nil)
		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusInternalServerError, w.Code)
		env.OrderStore.AssertExpectations(t)
	})
}

// --- GetItemsInsights ---

func TestGetItemsInsightsHandler(t *testing.T) {
	env := setupOrderEnv()
	orgID := uuid.New()
	admin := &database.User{ID: uuid.New(), OrganizationID: orgID, UserRole: "admin"}

	env.Router.GET("/:org/items/insights", authMiddleware(admin), env.Handler.GetItemsInsights)

	t.Run("Success", func(t *testing.T) {
		env.ResetMocks()
		insights := []database.Insight{
			{Title: "Most Popular Item", Statistic: "Burger"},
		}
		env.OrderStore.On("GetItemsInsights", orgID).Return(insights, nil).Once()

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/"+orgID.String()+"/items/insights", nil)
		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusOK, w.Code)
		assert.Contains(t, w.Body.String(), "Item insights retrieved successfully")
		assert.Contains(t, w.Body.String(), "Most Popular Item")
		env.OrderStore.AssertExpectations(t)
	})

	t.Run("Failure_DBError", func(t *testing.T) {
		env.ResetMocks()
		env.OrderStore.On("GetItemsInsights", orgID).Return(nil, errors.New("db error")).Once()

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/"+orgID.String()+"/items/insights", nil)
		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusInternalServerError, w.Code)
		env.OrderStore.AssertExpectations(t)
	})
}

// --- GetAllDeliveries ---

func TestGetAllDeliveriesHandler(t *testing.T) {
	env := setupOrderEnv()
	orgID := uuid.New()
	admin := &database.User{ID: uuid.New(), OrganizationID: orgID, UserRole: "admin"}

	env.Router.GET("/:org/deliveries", authMiddleware(admin), env.Handler.GetAllDeliveries)

	t.Run("Success", func(t *testing.T) {
		env.ResetMocks()
		deliveries := []database.OrderDelivery{
			{OrderID: uuid.New(), DriverID: uuid.New(), DeliveryStatus: "delivered", OutForDeliveryTime: time.Now()},
		}
		env.OrderStore.On("GetAllDeliveries", orgID).Return(deliveries, nil).Once()

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/"+orgID.String()+"/deliveries", nil)
		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusOK, w.Code)
		assert.Contains(t, w.Body.String(), "Deliveries retrieved successfully")
		assert.Contains(t, w.Body.String(), "delivered")
		env.OrderStore.AssertExpectations(t)
	})

	t.Run("Failure_EmployeeForbidden", func(t *testing.T) {
		env.ResetMocks()
		employee := &database.User{ID: uuid.New(), OrganizationID: orgID, UserRole: "employee"}
		router := gin.New()
		router.GET("/:org/deliveries", authMiddleware(employee), env.Handler.GetAllDeliveries)

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/"+orgID.String()+"/deliveries", nil)
		router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusForbidden, w.Code)
	})

	t.Run("Failure_DBError", func(t *testing.T) {
		env.ResetMocks()
		env.OrderStore.On("GetAllDeliveries", orgID).Return(nil, errors.New("db error")).Once()

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/"+orgID.String()+"/deliveries", nil)
		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusInternalServerError, w.Code)
		env.OrderStore.AssertExpectations(t)
	})
}

// --- GetAllDeliveriesForLastWeek ---

func TestGetAllDeliveriesForLastWeekHandler(t *testing.T) {
	env := setupOrderEnv()
	orgID := uuid.New()
	admin := &database.User{ID: uuid.New(), OrganizationID: orgID, UserRole: "admin"}

	env.Router.GET("/:org/deliveries/week", authMiddleware(admin), env.Handler.GetAllDeliveriesForLastWeek)

	t.Run("Success", func(t *testing.T) {
		env.ResetMocks()
		deliveries := []database.OrderDelivery{
			{OrderID: uuid.New(), DriverID: uuid.New(), DeliveryStatus: "delivered"},
		}
		env.OrderStore.On("GetAllDeliveriesForLastWeek", orgID).Return(deliveries, nil).Once()

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/"+orgID.String()+"/deliveries/week", nil)
		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusOK, w.Code)
		assert.Contains(t, w.Body.String(), "Deliveries retrieved successfully")
		env.OrderStore.AssertExpectations(t)
	})

	t.Run("Failure_DBError", func(t *testing.T) {
		env.ResetMocks()
		env.OrderStore.On("GetAllDeliveriesForLastWeek", orgID).Return(nil, errors.New("db error")).Once()

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/"+orgID.String()+"/deliveries/week", nil)
		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusInternalServerError, w.Code)
		env.OrderStore.AssertExpectations(t)
	})
}

// --- GetAllDeliveriesToday ---

func TestGetAllDeliveriesTodayHandler(t *testing.T) {
	env := setupOrderEnv()
	orgID := uuid.New()
	admin := &database.User{ID: uuid.New(), OrganizationID: orgID, UserRole: "admin"}

	env.Router.GET("/:org/deliveries/today", authMiddleware(admin), env.Handler.GetAllDeliveriesToday)

	t.Run("Success", func(t *testing.T) {
		env.ResetMocks()
		deliveries := []database.OrderDelivery{
			{OrderID: uuid.New(), DriverID: uuid.New(), DeliveryStatus: "in_transit"},
		}
		env.OrderStore.On("GetTodaysDeliveries", orgID).Return(deliveries, nil).Once()

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/"+orgID.String()+"/deliveries/today", nil)
		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusOK, w.Code)
		assert.Contains(t, w.Body.String(), "Deliveries retrieved successfully")
		env.OrderStore.AssertExpectations(t)
	})

	t.Run("Failure_DBError", func(t *testing.T) {
		env.ResetMocks()
		env.OrderStore.On("GetTodaysDeliveries", orgID).Return(nil, errors.New("db error")).Once()

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/"+orgID.String()+"/deliveries/today", nil)
		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusInternalServerError, w.Code)
		env.OrderStore.AssertExpectations(t)
	})
}

// --- GetDeliveryInsights ---

func TestGetDeliveryInsightsHandler(t *testing.T) {
	env := setupOrderEnv()
	orgID := uuid.New()
	admin := &database.User{ID: uuid.New(), OrganizationID: orgID, UserRole: "admin"}

	env.Router.GET("/:org/deliveries/insights", authMiddleware(admin), env.Handler.GetDeliveryInsights)

	t.Run("Success", func(t *testing.T) {
		env.ResetMocks()
		insights := []database.Insight{
			{Title: "Total Deliveries", Statistic: "78"},
		}
		env.OrderStore.On("GetDeliveryInsights", orgID).Return(insights, nil).Once()

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/"+orgID.String()+"/deliveries/insights", nil)
		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusOK, w.Code)
		assert.Contains(t, w.Body.String(), "Delivery insights retrieved successfully")
		assert.Contains(t, w.Body.String(), "Total Deliveries")
		env.OrderStore.AssertExpectations(t)
	})

	t.Run("Failure_DBError", func(t *testing.T) {
		env.ResetMocks()
		env.OrderStore.On("GetDeliveryInsights", orgID).Return(nil, errors.New("db error")).Once()

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/"+orgID.String()+"/deliveries/insights", nil)
		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusInternalServerError, w.Code)
		env.OrderStore.AssertExpectations(t)
	})
}
