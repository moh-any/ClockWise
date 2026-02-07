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

type RolesTestEnv struct {
	Router     *gin.Engine
	RolesStore *MockRolesStore
	Handler    *api.RolesHandler
}

func setupRolesEnv() *RolesTestEnv {
	gin.SetMode(gin.TestMode)

	rolesStore := new(MockRolesStore)
	logger := slog.New(slog.NewTextHandler(os.Stdout, nil))

	handler := api.NewRolesHandler(rolesStore, logger)

	return &RolesTestEnv{
		Router:     gin.New(),
		RolesStore: rolesStore,
		Handler:    handler,
	}
}

func (env *RolesTestEnv) ResetMocks() {
	env.RolesStore.ExpectedCalls = nil
	env.RolesStore.Calls = nil
}

// Helpers for pointers
func intPtr(i int) *int    { return &i }
func boolPtr(b bool) *bool { return &b }

func TestGetAllRoles(t *testing.T) {
	env := setupRolesEnv()
	orgID := uuid.New()
	admin := &database.User{ID: uuid.New(), OrganizationID: orgID, UserRole: "admin"}

	env.Router.GET("/:org/roles", authMiddleware(admin), env.Handler.GetAllRoles)

	t.Run("Success", func(t *testing.T) {
		env.ResetMocks()
		roles := []database.OrganizationRole{{Role: "Server"}}
		env.RolesStore.On("GetRolesByOrganizationID", orgID).Return(roles, nil).Once()

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/"+orgID.String()+"/roles", nil)
		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusOK, w.Code)
		assert.Contains(t, w.Body.String(), "Server")
		env.RolesStore.AssertExpectations(t)
	})

	t.Run("Failure_DBError", func(t *testing.T) {
		env.ResetMocks()
		env.RolesStore.On("GetRolesByOrganizationID", orgID).Return(nil, errors.New("db error")).Once()

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/"+orgID.String()+"/roles", nil)
		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusInternalServerError, w.Code)
	})
}

func TestCreateRole(t *testing.T) {
	env := setupRolesEnv()
	orgID := uuid.New()
	admin := &database.User{ID: uuid.New(), OrganizationID: orgID, UserRole: "admin"}

	env.Router.POST("/:org/roles", authMiddleware(admin), env.Handler.CreateRole)

	t.Run("Success", func(t *testing.T) {
		env.ResetMocks()
		// Case: NeedForDemand=true, ItemsPerRolePerHour provided
		reqBody := api.CreateRoleRequest{
			Role:                "Chef",
			MinNeededPerShift:   2,
			NeedForDemand:       true,
			ItemsPerRolePerHour: intPtr(5),
			Independent:         boolPtr(false),
		}

		// 1. Check if exists
		env.RolesStore.On("GetRoleByName", orgID, "Chef").Return(nil, nil).Once()
		// 2. Create
		env.RolesStore.On("CreateRole", mock.MatchedBy(func(r *database.OrganizationRole) bool {
			return r.Role == "Chef" && r.OrganizationID == orgID && *r.ItemsPerRolePerHour == 5
		})).Return(nil).Once()

		jsonBytes, _ := json.Marshal(reqBody)
		w := httptest.NewRecorder()
		req, _ := http.NewRequest("POST", "/"+orgID.String()+"/roles", bytes.NewBuffer(jsonBytes))
		req.Header.Set("Content-Type", "application/json")
		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusCreated, w.Code)
		env.RolesStore.AssertExpectations(t)
	})

	t.Run("Failure_ProtectedRole", func(t *testing.T) {
		env.ResetMocks()
		reqBody := api.CreateRoleRequest{Role: "admin"}

		jsonBytes, _ := json.Marshal(reqBody)
		w := httptest.NewRecorder()
		req, _ := http.NewRequest("POST", "/"+orgID.String()+"/roles", bytes.NewBuffer(jsonBytes))
		req.Header.Set("Content-Type", "application/json")
		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusBadRequest, w.Code)
		assert.Contains(t, w.Body.String(), "Cannot create protected role")
	})

	t.Run("Failure_RoleExists", func(t *testing.T) {
		env.ResetMocks()
		reqBody := api.CreateRoleRequest{Role: "Chef"}
		existingRole := &database.OrganizationRole{Role: "Chef"}

		env.RolesStore.On("GetRoleByName", orgID, "Chef").Return(existingRole, nil).Once()

		jsonBytes, _ := json.Marshal(reqBody)
		w := httptest.NewRecorder()
		req, _ := http.NewRequest("POST", "/"+orgID.String()+"/roles", bytes.NewBuffer(jsonBytes))
		req.Header.Set("Content-Type", "application/json")
		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusConflict, w.Code)
		env.RolesStore.AssertExpectations(t)
	})

	t.Run("Failure_Validation_NeedDemand", func(t *testing.T) {
		env.ResetMocks()
		// NeedForDemand is true, but ItemsPerRolePerHour is nil
		reqBody := api.CreateRoleRequest{Role: "Chef", NeedForDemand: true}

		// FIX: Do NOT expect GetRoleByName.
		// The handler performs validation logic and returns 400 BEFORE calling the DB.

		jsonBytes, _ := json.Marshal(reqBody)
		w := httptest.NewRecorder()
		req, _ := http.NewRequest("POST", "/"+orgID.String()+"/roles", bytes.NewBuffer(jsonBytes))
		req.Header.Set("Content-Type", "application/json")
		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusBadRequest, w.Code)
		// FIX: Match the actual error message from your previous log
		assert.Contains(t, w.Body.String(), "items_per_role_per_hour must be \\u003e= 0")
		env.RolesStore.AssertExpectations(t)
	})
}

func TestGetRole(t *testing.T) {
	env := setupRolesEnv()
	orgID := uuid.New()
	admin := &database.User{ID: uuid.New(), OrganizationID: orgID, UserRole: "admin"}

	env.Router.GET("/:org/roles/:role", authMiddleware(admin), env.Handler.GetRole)

	t.Run("Success", func(t *testing.T) {
		env.ResetMocks()
		roleName := "Chef"
		role := &database.OrganizationRole{Role: roleName}

		env.RolesStore.On("GetRoleByName", orgID, roleName).Return(role, nil).Once()

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/"+orgID.String()+"/roles/"+roleName, nil)
		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusOK, w.Code)
		assert.Contains(t, w.Body.String(), "Chef")
		env.RolesStore.AssertExpectations(t)
	})

	t.Run("Failure_NotFound", func(t *testing.T) {
		env.ResetMocks()
		roleName := "Missing"

		env.RolesStore.On("GetRoleByName", orgID, roleName).Return(nil, nil).Once()

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/"+orgID.String()+"/roles/"+roleName, nil)
		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusNotFound, w.Code)
		env.RolesStore.AssertExpectations(t)
	})
}

func TestUpdateRole(t *testing.T) {
	env := setupRolesEnv()
	orgID := uuid.New()
	admin := &database.User{ID: uuid.New(), OrganizationID: orgID, UserRole: "admin"}

	env.Router.PUT("/:org/roles/:role", authMiddleware(admin), env.Handler.UpdateRole)

	t.Run("Success", func(t *testing.T) {
		env.ResetMocks()
		roleName := "Chef"
		reqBody := api.UpdateRoleRequest{MinNeededPerShift: 5}

		// Setup existing role
		existingRole := &database.OrganizationRole{Role: roleName, OrganizationID: orgID, MinNeededPerShift: 2}

		env.RolesStore.On("GetRoleByName", orgID, roleName).Return(existingRole, nil).Once()

		// Expect UpdateRole with modified fields
		// Note: handler updates existingRole struct directly.
		// reqBody has nil pointers for Items/Independent and false for NeedForDemand.
		// This overwrites existing role values.
		env.RolesStore.On("UpdateRole", mock.MatchedBy(func(r *database.OrganizationRole) bool {
			if r.Role != roleName {
				return false
			}
			if r.MinNeededPerShift != 5 {
				return false
			}
			// Defaults from request body zero values
			if r.ItemsPerRolePerHour != nil {
				return false
			}
			if r.NeedForDemand != false {
				return false
			}
			if r.Independent != nil {
				return false
			}
			return true
		})).Return(nil).Once()

		jsonBytes, _ := json.Marshal(reqBody)
		w := httptest.NewRecorder()
		req, _ := http.NewRequest("PUT", "/"+orgID.String()+"/roles/"+roleName, bytes.NewBuffer(jsonBytes))
		req.Header.Set("Content-Type", "application/json")
		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusOK, w.Code)
		env.RolesStore.AssertExpectations(t)
	})

	t.Run("Failure_Protected", func(t *testing.T) {
		env.ResetMocks()
		roleName := "admin"
		reqBody := api.UpdateRoleRequest{MinNeededPerShift: 5}

		jsonBytes, _ := json.Marshal(reqBody)
		w := httptest.NewRecorder()
		req, _ := http.NewRequest("PUT", "/"+orgID.String()+"/roles/"+roleName, bytes.NewBuffer(jsonBytes))
		req.Header.Set("Content-Type", "application/json")
		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusForbidden, w.Code)
	})

	t.Run("Failure_NotFound", func(t *testing.T) {
		env.ResetMocks()
		roleName := "Missing"
		reqBody := api.UpdateRoleRequest{MinNeededPerShift: 5}

		env.RolesStore.On("GetRoleByName", orgID, roleName).Return(nil, nil).Once()

		jsonBytes, _ := json.Marshal(reqBody)
		w := httptest.NewRecorder()
		req, _ := http.NewRequest("PUT", "/"+orgID.String()+"/roles/"+roleName, bytes.NewBuffer(jsonBytes))
		req.Header.Set("Content-Type", "application/json")
		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusNotFound, w.Code)
	})
}

func TestDeleteRole(t *testing.T) {
	env := setupRolesEnv()
	orgID := uuid.New()
	admin := &database.User{ID: uuid.New(), OrganizationID: orgID, UserRole: "admin"}

	env.Router.DELETE("/:org/roles/:role", authMiddleware(admin), env.Handler.DeleteRole)

	t.Run("Success", func(t *testing.T) {
		env.ResetMocks()
		roleName := "Chef"
		existingRole := &database.OrganizationRole{Role: roleName}

		env.RolesStore.On("GetRoleByName", orgID, roleName).Return(existingRole, nil).Once()
		env.RolesStore.On("DeleteRole", orgID, roleName).Return(nil).Once()

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("DELETE", "/"+orgID.String()+"/roles/"+roleName, nil)
		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusOK, w.Code)
		env.RolesStore.AssertExpectations(t)
	})

	t.Run("Failure_Protected", func(t *testing.T) {
		env.ResetMocks()
		roleName := "manager"

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("DELETE", "/"+orgID.String()+"/roles/"+roleName, nil)
		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusForbidden, w.Code)
	})

	t.Run("Failure_NotFound", func(t *testing.T) {
		env.ResetMocks()
		roleName := "Missing"

		env.RolesStore.On("GetRoleByName", orgID, roleName).Return(nil, nil).Once()

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("DELETE", "/"+orgID.String()+"/roles/"+roleName, nil)
		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusNotFound, w.Code)
	})
}
