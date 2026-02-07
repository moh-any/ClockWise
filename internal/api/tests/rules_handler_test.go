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

type RulesTestEnv struct {
	Router              *gin.Engine
	RulesStore          *MockRulesStore
	OperatingHoursStore *MockOperatingHoursStore
	Handler             *api.RulesHandler
}

func setupRulesEnv() *RulesTestEnv {
	gin.SetMode(gin.TestMode)

	rulesStore := new(MockRulesStore)
	operatingHoursStore := new(MockOperatingHoursStore)
	logger := slog.New(slog.NewTextHandler(os.Stdout, nil))

	handler := api.NewRulesHandler(rulesStore, operatingHoursStore, logger)

	return &RulesTestEnv{
		Router:              gin.New(),
		RulesStore:          rulesStore,
		OperatingHoursStore: operatingHoursStore,
		Handler:             handler,
	}
}

func (env *RulesTestEnv) ResetMocks() {
	env.RulesStore.ExpectedCalls = nil
	env.RulesStore.Calls = nil
	env.OperatingHoursStore.ExpectedCalls = nil
	env.OperatingHoursStore.Calls = nil
}

func TestGetOrganizationRules(t *testing.T) {
	env := setupRulesEnv()
	orgID := uuid.New()
	admin := &database.User{ID: uuid.New(), OrganizationID: orgID, UserRole: "admin"}
	employee := &database.User{ID: uuid.New(), OrganizationID: orgID, UserRole: "employee"}

	// Register route once
	env.Router.GET("/:org/rules", authMiddleware(admin), env.Handler.GetOrganizationRules)

	// Separate router for employee test
	employeeRouter := gin.New()
	employeeRouter.GET("/:org/rules", authMiddleware(employee), env.Handler.GetOrganizationRules)

	t.Run("Success", func(t *testing.T) {
		env.ResetMocks()
		rules := &database.OrganizationRules{OrganizationID: orgID, MaxWeeklyHours: 40}
		operatingHours := []*database.OperatingHours{{Weekday: "Monday", OpeningTime: "09:00", ClosingTime: "17:00"}}

		env.RulesStore.On("GetRulesByOrganizationID", orgID).Return(rules, nil).Once()
		env.OperatingHoursStore.On("GetOperatingHours", orgID).Return(operatingHours, nil).Once()

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/"+orgID.String()+"/rules", nil)
		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusOK, w.Code)
		assert.Contains(t, w.Body.String(), "Monday")
		assert.Contains(t, w.Body.String(), "40")
		env.RulesStore.AssertExpectations(t)
		env.OperatingHoursStore.AssertExpectations(t)
	})

	t.Run("Success_NoRules", func(t *testing.T) {
		env.ResetMocks()
		// Rules not found (nil), Operating hours found
		env.RulesStore.On("GetRulesByOrganizationID", orgID).Return(nil, nil).Once()
		env.OperatingHoursStore.On("GetOperatingHours", orgID).Return([]*database.OperatingHours{}, nil).Once()

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/"+orgID.String()+"/rules", nil)
		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusOK, w.Code)
		assert.Contains(t, w.Body.String(), "No rules set")
	})

	t.Run("Failure_Forbidden", func(t *testing.T) {
		env.ResetMocks()
		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/"+orgID.String()+"/rules", nil)
		employeeRouter.ServeHTTP(w, req)

		assert.Equal(t, http.StatusForbidden, w.Code)
	})

	t.Run("Failure_DBError", func(t *testing.T) {
		env.ResetMocks()
		env.RulesStore.On("GetRulesByOrganizationID", orgID).Return(nil, errors.New("db error")).Once()

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/"+orgID.String()+"/rules", nil)
		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusInternalServerError, w.Code)
	})
}

func TestUpdateOrganizationRules(t *testing.T) {
	env := setupRulesEnv()
	orgID := uuid.New()
	admin := &database.User{ID: uuid.New(), OrganizationID: orgID, UserRole: "admin"}
	manager := &database.User{ID: uuid.New(), OrganizationID: orgID, UserRole: "manager"}

	env.Router.POST("/:org/rules", authMiddleware(admin), env.Handler.UpdateOrganizationRules)

	managerRouter := gin.New()
	managerRouter.POST("/:org/rules", authMiddleware(manager), env.Handler.UpdateOrganizationRules)

	t.Run("Success", func(t *testing.T) {
		env.ResetMocks()
		reqBody := api.RulesRequest{
			ShiftMaxHours:       8,
			ShiftMinHours:       4,
			MaxWeeklyHours:      40,
			MinWeeklyHours:      20,
			MinRestSlots:        2,
			SlotLenHour:         1.0,
			MinShiftLengthSlots: 4,
			WaitingTime:         15,
			OperatingHours: []api.OperatingHoursRequest{
				{Weekday: "Monday", OpeningTime: "09:00", ClosingTime: "17:00"},
			},
		}

		env.RulesStore.On("UpsertRules", mock.MatchedBy(func(r *database.OrganizationRules) bool {
			return r.OrganizationID == orgID && r.MaxWeeklyHours == 40
		})).Return(nil).Once()

		env.OperatingHoursStore.On("SetOperatingHours", orgID, mock.Anything).Return(nil).Once()
		env.OperatingHoursStore.On("GetOperatingHours", orgID).Return([]*database.OperatingHours{}, nil).Once()

		jsonBytes, _ := json.Marshal(reqBody)
		w := httptest.NewRecorder()
		req, _ := http.NewRequest("POST", "/"+orgID.String()+"/rules", bytes.NewBuffer(jsonBytes))
		req.Header.Set("Content-Type", "application/json")
		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusOK, w.Code)
		env.RulesStore.AssertExpectations(t)
		env.OperatingHoursStore.AssertExpectations(t)
	})

	t.Run("Failure_Forbidden", func(t *testing.T) {
		env.ResetMocks()
		w := httptest.NewRecorder()
		req, _ := http.NewRequest("POST", "/"+orgID.String()+"/rules", nil)
		managerRouter.ServeHTTP(w, req)

		assert.Equal(t, http.StatusForbidden, w.Code)
	})

	t.Run("Failure_Validation_MinExceedsMax", func(t *testing.T) {
		env.ResetMocks()
		reqBody := api.RulesRequest{
			ShiftMaxHours:       4,
			ShiftMinHours:       8, // Error: Min > Max
			MaxWeeklyHours:      40,
			MinWeeklyHours:      20,
			MinRestSlots:        2,
			SlotLenHour:         1.0,
			MinShiftLengthSlots: 4,
			WaitingTime:         15,
		}

		jsonBytes, _ := json.Marshal(reqBody)
		w := httptest.NewRecorder()
		req, _ := http.NewRequest("POST", "/"+orgID.String()+"/rules", bytes.NewBuffer(jsonBytes))
		req.Header.Set("Content-Type", "application/json")
		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusBadRequest, w.Code)
		assert.Contains(t, w.Body.String(), "Shift minimum hours cannot exceed")
	})

	t.Run("Failure_Validation_FixedShifts", func(t *testing.T) {
		env.ResetMocks()
		reqBody := api.RulesRequest{
			ShiftMaxHours:       8,
			ShiftMinHours:       4,
			MaxWeeklyHours:      40,
			MinWeeklyHours:      20,
			MinRestSlots:        2,
			SlotLenHour:         1.0,
			MinShiftLengthSlots: 4,
			WaitingTime:         15,
			FixedShifts:         true, // Error: NumberOfShiftsPerDay missing
		}

		jsonBytes, _ := json.Marshal(reqBody)
		w := httptest.NewRecorder()
		req, _ := http.NewRequest("POST", "/"+orgID.String()+"/rules", bytes.NewBuffer(jsonBytes))
		req.Header.Set("Content-Type", "application/json")
		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusBadRequest, w.Code)
		assert.Contains(t, w.Body.String(), "number_of_shifts_per_day must be \\u003e 0 when fixed_shifts is true")
	})

	t.Run("Failure_Validation_InvalidDay", func(t *testing.T) {
		env.ResetMocks()
		reqBody := api.RulesRequest{
			ShiftMaxHours:       8,
			ShiftMinHours:       4,
			MaxWeeklyHours:      40,
			MinWeeklyHours:      20,
			MinRestSlots:        2,
			SlotLenHour:         1.0,
			MinShiftLengthSlots: 4,
			WaitingTime:         15,
			OperatingHours: []api.OperatingHoursRequest{
				{Weekday: "Funday", OpeningTime: "09:00", ClosingTime: "17:00"},
			},
		}

		// Mock UpsertRules as validation happens after saving rules but before saving operating hours
		// Actually, handler saves rules first, then checks operating hours.
		// So UpsertRules will be called.
		env.RulesStore.On("UpsertRules", mock.Anything).Return(nil).Once()

		jsonBytes, _ := json.Marshal(reqBody)
		w := httptest.NewRecorder()
		req, _ := http.NewRequest("POST", "/"+orgID.String()+"/rules", bytes.NewBuffer(jsonBytes))
		req.Header.Set("Content-Type", "application/json")
		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusBadRequest, w.Code)
		assert.Contains(t, w.Body.String(), "Invalid weekday")
		env.RulesStore.AssertExpectations(t)
	})
}
