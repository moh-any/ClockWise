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

type PreferencesTestEnv struct {
	Router           *gin.Engine
	PreferencesStore *MockPreferencesStore
	UserRolesStore   *MockUserRolesStore
	UserStore        *MockUserStore
	RolesStore       *MockRolesStore
	Handler          *api.PreferencesHandler
}

func setupPreferencesEnv() *PreferencesTestEnv {
	gin.SetMode(gin.TestMode)

	prefStore := new(MockPreferencesStore)
	userRolesStore := new(MockUserRolesStore)
	userStore := new(MockUserStore)
	rolesStore := new(MockRolesStore)
	logger := slog.New(slog.NewTextHandler(os.Stdout, nil))

	handler := api.NewPreferencesHandler(prefStore, userRolesStore, userStore, rolesStore, logger)

	return &PreferencesTestEnv{
		Router:           gin.New(),
		PreferencesStore: prefStore,
		UserRolesStore:   userRolesStore,
		UserStore:        userStore,
		RolesStore:       rolesStore,
		Handler:          handler,
	}
}

// ResetMocks clears calls for shared environment tests
func (env *PreferencesTestEnv) ResetMocks() {
	env.PreferencesStore.ExpectedCalls = nil
	env.PreferencesStore.Calls = nil
	env.UserRolesStore.ExpectedCalls = nil
	env.UserRolesStore.Calls = nil
	env.UserStore.ExpectedCalls = nil
	env.UserStore.Calls = nil
	env.RolesStore.ExpectedCalls = nil
	env.RolesStore.Calls = nil
}

func TestGetCurrentEmployeePreferences(t *testing.T) {
	env := setupPreferencesEnv()
	orgID := uuid.New()
	userID := uuid.New()
	user := &database.User{ID: userID, OrganizationID: orgID, UserRole: "employee"}

	// Register Route
	env.Router.GET("/:org/preferences", authMiddleware(user), env.Handler.GetCurrentEmployeePreferences)

	t.Run("Success", func(t *testing.T) {
		env.ResetMocks()

		prefs := []*database.EmployeePreference{
			{EmployeeID: userID, Day: "Monday", PreferredStartTime: nil},
		}
		roles := []string{"Server"}

		fullUser := &database.User{
			ID:              userID,
			MaxHoursPerWeek: func(i int) *int { return &i }(40),
		}

		env.PreferencesStore.On("GetPreferencesByEmployeeID", userID).Return(prefs, nil).Once()
		env.UserRolesStore.On("GetUserRoles", userID, orgID).Return(roles, nil).Once()
		env.UserStore.On("GetUserByID", userID).Return(fullUser, nil).Once()

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/"+orgID.String()+"/preferences", nil)
		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusOK, w.Code)
		assert.Contains(t, w.Body.String(), "Monday")
		assert.Contains(t, w.Body.String(), "Server")
		assert.Contains(t, w.Body.String(), "40")

		env.PreferencesStore.AssertExpectations(t)
		env.UserRolesStore.AssertExpectations(t)
		env.UserStore.AssertExpectations(t)
	})

	t.Run("Failure_PreferencesStoreError", func(t *testing.T) {
		env.ResetMocks()

		env.PreferencesStore.On("GetPreferencesByEmployeeID", userID).Return(nil, errors.New("db error")).Once()

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/"+orgID.String()+"/preferences", nil)
		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusInternalServerError, w.Code)
	})
}

func TestUpdateCurrentEmployeePreferences(t *testing.T) {
	env := setupPreferencesEnv()
	orgID := uuid.New()
	userID := uuid.New()
	user := &database.User{ID: userID, OrganizationID: orgID, UserRole: "employee"}

	// Register Route
	env.Router.POST("/:org/preferences", authMiddleware(user), env.Handler.UpdateCurrentEmployeePreferences)

	t.Run("Success_UpdateAll", func(t *testing.T) {
		env.ResetMocks()

		// Helper vars for pointers
		maxHours := 30
		prefHours := 25
		maxConsec := 4
		onCall := true

		prefRequest := api.PreferencesRequest{
			Preferences: []api.DayPreferenceRequest{
				{Day: "monday"},
			},
			UserRoles:             []string{"Server"},
			MaxHoursPerWeek:       &maxHours,
			PreferredHoursPerWeek: &prefHours,
			MaxConsecSlots:        &maxConsec,
			OnCall:                &onCall,
		}

		orgRoles := []*database.OrganizationRole{{Role: "Server"}}
		fullUser := &database.User{ID: userID}

		// 1. Upsert Preferences
		env.PreferencesStore.On("UpsertPreferences", userID, mock.Anything).Return(nil).Once()

		// 2. Validate Roles (GetRoles)
		env.RolesStore.On("GetRolesByOrganizationID", orgID).Return(orgRoles, nil).Once()

		// 3. Set User Roles
		env.UserRolesStore.On("SetUserRoles", userID, orgID, prefRequest.UserRoles).Return(nil).Once()

		// 4. Update User Settings (Get User -> Update User)
		env.UserStore.On("GetUserByID", userID).Return(fullUser, nil).Once()
		env.UserStore.On("UpdateUser", mock.MatchedBy(func(u *database.User) bool {
			if u.MaxHoursPerWeek == nil || *u.MaxHoursPerWeek != 30 {
				return false
			}
			if u.PreferredHoursPerWeek == nil || *u.PreferredHoursPerWeek != 25 {
				return false
			}
			if u.MaxConsecSlots == nil || *u.MaxConsecSlots != 4 {
				return false
			}
			if u.OnCall == nil || *u.OnCall != true {
				return false
			}
			return true
		})).Return(nil).Once()

		jsonBytes, _ := json.Marshal(prefRequest)
		w := httptest.NewRecorder()
		req, _ := http.NewRequest("POST", "/"+orgID.String()+"/preferences", bytes.NewBuffer(jsonBytes))
		req.Header.Set("Content-Type", "application/json")

		env.Router.ServeHTTP(w, req)

		// Debugging: Print body if test fails
		if w.Code != http.StatusOK {
			t.Logf("Response Status: %d", w.Code)
			t.Logf("Response Body: %s", w.Body.String())
		}

		assert.Equal(t, http.StatusOK, w.Code)
		env.PreferencesStore.AssertExpectations(t)
		env.UserRolesStore.AssertExpectations(t)
		env.RolesStore.AssertExpectations(t)
		env.UserStore.AssertExpectations(t)
	})

	t.Run("Failure_InvalidDay", func(t *testing.T) {
		env.ResetMocks()

		reqBody := `{"preferences": [{"day": "Funday"}]}`

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("POST", "/"+orgID.String()+"/preferences", bytes.NewBufferString(reqBody))
		req.Header.Set("Content-Type", "application/json")

		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusBadRequest, w.Code)
		assert.Contains(t, w.Body.String(), "Invalid day")
	})

	t.Run("Failure_DuplicateDay", func(t *testing.T) {
		env.ResetMocks()

		reqBody := `{"preferences": [{"day": "monday"}, {"day": "monday"}]}`

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("POST", "/"+orgID.String()+"/preferences", bytes.NewBufferString(reqBody))
		req.Header.Set("Content-Type", "application/json")

		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusBadRequest, w.Code)
		assert.Contains(t, w.Body.String(), "Duplicate day")
	})

	t.Run("Failure_InvalidRole", func(t *testing.T) {
		env.ResetMocks()

		prefRequest := api.PreferencesRequest{
			Preferences: []api.DayPreferenceRequest{{Day: "friday"}},
			UserRoles:   []string{"Wizard"},
		}

		orgRoles := []*database.OrganizationRole{{Role: "Server"}}

		env.PreferencesStore.On("UpsertPreferences", userID, mock.Anything).Return(nil).Once()
		env.RolesStore.On("GetRolesByOrganizationID", orgID).Return(orgRoles, nil).Once()

		jsonBytes, _ := json.Marshal(prefRequest)
		w := httptest.NewRecorder()
		req, _ := http.NewRequest("POST", "/"+orgID.String()+"/preferences", bytes.NewBuffer(jsonBytes))
		req.Header.Set("Content-Type", "application/json")

		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusBadRequest, w.Code)
		assert.Contains(t, w.Body.String(), "Role does not exist")
	})
}
