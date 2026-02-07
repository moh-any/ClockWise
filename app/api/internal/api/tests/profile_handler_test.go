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

type ProfileTestEnv struct {
	Router    *gin.Engine
	UserStore *MockUserStore
	Handler   *api.ProfileHandler
}

func setupProfileEnv() *ProfileTestEnv {
	gin.SetMode(gin.TestMode)

	userStore := new(MockUserStore)
	logger := slog.New(slog.NewTextHandler(os.Stdout, nil))

	handler := api.NewProfileHandler(userStore, logger)

	return &ProfileTestEnv{
		Router:    gin.New(),
		UserStore: userStore,
		Handler:   handler,
	}
}

// ResetMocks clears mock expectations between tests sharing the same env
func (env *ProfileTestEnv) ResetMocks() {
	env.UserStore.ExpectedCalls = nil
	env.UserStore.Calls = nil
}

func TestGetProfileHandler(t *testing.T) {
	env := setupProfileEnv()
	orgID := uuid.New()
	userID := uuid.New()
	user := &database.User{ID: userID, OrganizationID: orgID, UserRole: "employee"}

	// FIX: Register Route ONCE here (outside t.Run)
	env.Router.GET("/profile", authMiddleware(user), env.Handler.GetProfileHandler)

	t.Run("Success", func(t *testing.T) {
		env.ResetMocks()

		profile := &database.UserProfile{
			FullName:     "John Doe",
			Email:        "john@test.com",
			Organization: "Clockwise",
			UserRole:     "employee",
		}

		env.UserStore.On("GetProfile", userID).Return(profile, nil).Once()

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/profile", nil)
		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusOK, w.Code)
		assert.Contains(t, w.Body.String(), "John Doe")
		env.UserStore.AssertExpectations(t)
	})

	t.Run("Failure_ProfileNotFound", func(t *testing.T) {
		env.ResetMocks()

		env.UserStore.On("GetProfile", userID).Return(nil, errors.New("not found")).Once()

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/profile", nil)
		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusNotFound, w.Code)
		env.UserStore.AssertExpectations(t)
	})

	t.Run("Failure_Unauthorized", func(t *testing.T) {
		env.ResetMocks()

		// For this specific test case, we need a router WITHOUT the auth middleware
		// injecting the user. Since the main env.Router has it baked in via the
		// registration above, we create a fresh one just for this negative test.
		r := gin.New()
		r.GET("/profile", env.Handler.GetProfileHandler)

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/profile", nil)
		r.ServeHTTP(w, req)

		// should return {"error": "Unauthorized"}
		assert.Equal(t, http.StatusUnauthorized, w.Code)
		assert.Contains(t, w.Body.String(), "Unauthorized")
	})
}

func TestChangePasswordHandler(t *testing.T) {
	env := setupProfileEnv()
	orgID := uuid.New()
	userID := uuid.New()
	user := &database.User{ID: userID, OrganizationID: orgID, UserRole: "employee"}

	// We need a user with a set password to test validation
	fullUser := &database.User{ID: userID, OrganizationID: orgID}
	_ = fullUser.PasswordHash.Set("oldPassword123") // Helper from database package

	// FIX: Register Route ONCE here (outside t.Run)
	env.Router.PUT("/profile/password", authMiddleware(user), env.Handler.ChangePasswordHandler)

	t.Run("Success", func(t *testing.T) {
		env.ResetMocks()

		reqBody := api.ChangePasswordRequest{
			OldPassword: "oldPassword123",
			NewPassword: "newPassword123",
		}

		// 1. Handler fetches full user
		env.UserStore.On("GetUserByID", userID).Return(fullUser, nil).Once()
		// 2. Handler updates password (hash will be random, so we match Anything)
		env.UserStore.On("ChangePassword", userID, mock.Anything).Return(nil).Once()

		jsonBytes, _ := json.Marshal(reqBody)
		w := httptest.NewRecorder()
		req, _ := http.NewRequest("PUT", "/profile/password", bytes.NewBuffer(jsonBytes))
		// FIX: Add Content-Type for binding
		req.Header.Set("Content-Type", "application/json")

		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusOK, w.Code)
		assert.Contains(t, w.Body.String(), "Password changed successfully")
		env.UserStore.AssertExpectations(t)
	})

	t.Run("Failure_IncorrectOldPassword", func(t *testing.T) {
		env.ResetMocks()

		reqBody := api.ChangePasswordRequest{
			OldPassword: "wrongPassword",
			NewPassword: "newPassword123",
		}

		env.UserStore.On("GetUserByID", userID).Return(fullUser, nil).Once()

		jsonBytes, _ := json.Marshal(reqBody)
		w := httptest.NewRecorder()
		req, _ := http.NewRequest("PUT", "/profile/password", bytes.NewBuffer(jsonBytes))
		req.Header.Set("Content-Type", "application/json")

		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusUnauthorized, w.Code)
		assert.Contains(t, w.Body.String(), "Incorrect old password")
		env.UserStore.AssertExpectations(t)
	})

	t.Run("Failure_InvalidBody", func(t *testing.T) {
		env.ResetMocks()

		reqBody := `{"old_password": ""}` // Missing required fields

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("PUT", "/profile/password", bytes.NewBufferString(reqBody))
		req.Header.Set("Content-Type", "application/json")

		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusBadRequest, w.Code)
	})

	t.Run("Failure_DBError", func(t *testing.T) {
		env.ResetMocks()

		reqBody := api.ChangePasswordRequest{
			OldPassword: "oldPassword123",
			NewPassword: "newPassword123",
		}

		env.UserStore.On("GetUserByID", userID).Return(fullUser, nil).Once()
		env.UserStore.On("ChangePassword", userID, mock.Anything).Return(errors.New("db fail")).Once()

		jsonBytes, _ := json.Marshal(reqBody)
		w := httptest.NewRecorder()
		req, _ := http.NewRequest("PUT", "/profile/password", bytes.NewBuffer(jsonBytes))
		req.Header.Set("Content-Type", "application/json")

		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusInternalServerError, w.Code)
		env.UserStore.AssertExpectations(t)
	})
}
