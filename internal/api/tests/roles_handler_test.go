package api

import (
	"bytes"
	"encoding/json"
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

func TestGetAllRoles(t *testing.T) {
	env := setupRolesEnv()
	orgID := uuid.New()
	admin := &database.User{ID: uuid.New(), OrganizationID: orgID, UserRole: "admin"}
	employee := &database.User{ID: uuid.New(), OrganizationID: orgID, UserRole: "employee"}

	// Register route once
	env.Router.GET("/:org/roles", authMiddleware(admin), env.Handler.GetAllRoles)
	// We need a separate router for the employee test to inject the employee user middleware
	// or we can just use the same router if we had a dynamic middleware, but sticking to the existing pattern:
	employeeRouter := gin.New()
	employeeRouter.GET("/:org/roles", authMiddleware(employee), env.Handler.GetAllRoles)

	t.Run("Success_Admin", func(t *testing.T) {
		env.ResetMocks()
		roles := []*database.OrganizationRole{{Role: "Server"}}
		env.RolesStore.On("GetRolesByOrganizationID", orgID).Return(roles, nil).Once()

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/"+orgID.String()+"/roles", nil)
		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusOK, w.Code)
		assert.Contains(t, w.Body.String(), "Server")
		env.RolesStore.AssertExpectations(t)
	})

	t.Run("Failure_Forbidden", func(t *testing.T) {
		env.ResetMocks()
		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/"+orgID.String()+"/roles", nil)
		employeeRouter.ServeHTTP(w, req)

		assert.Equal(t, http.StatusForbidden, w.Code)
	})
}

func TestCreateRole(t *testing.T) {
	env := setupRolesEnv()
	orgID := uuid.New()
	admin := &database.User{ID: uuid.New(), OrganizationID: orgID, UserRole: "admin"}

	env.Router.POST("/:org/roles", authMiddleware(admin), env.Handler.CreateRole)

	t.Run("Success", func(t *testing.T) {
		env.ResetMocks()
		reqBody := api.CreateRoleRequest{Role: "Chef", MinNeededPerShift: 2}

		// 1. Check if exists
		env.RolesStore.On("GetRoleByName", orgID, "Chef").Return(nil, nil).Once()
		// 2. Create
		env.RolesStore.On("CreateRole", mock.MatchedBy(func(r *database.OrganizationRole) bool {
			return r.Role == "Chef" && r.OrganizationID == orgID
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
		// NeedForDemand is true, but ItemsPerRolePerHour is nil/missing (default 0 not allowed if check strictly, but 0 is >= 0 so strictly nil check needs pointer or logic)
		// The handler logic: if req.ItemsPerRolePerHour == nil || *req.ItemsPerRolePerHour < 0
		reqBody := api.CreateRoleRequest{Role: "Chef", NeedForDemand: true} // ItemsPerRolePerHour is nil

		jsonBytes, _ := json.Marshal(reqBody)
		w := httptest.NewRecorder()
		req, _ := http.NewRequest("POST", "/"+orgID.String()+"/roles", bytes.NewBuffer(jsonBytes))
		req.Header.Set("Content-Type", "application/json")
		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusBadRequest, w.Code)
		// {"error":"items_per_role_per_hour must be >= 0 when need_for_demand is true"}
		assert.Contains(t, w.Body.String(), "items_per_role_per_hour must be \\u003e= 0 when need_for_demand is true")
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
		existingRole := &database.OrganizationRole{Role: roleName}

		env.RolesStore.On("GetRoleByName", orgID, roleName).Return(existingRole, nil).Once()
		env.RolesStore.On("UpdateRole", mock.MatchedBy(func(r *database.OrganizationRole) bool {
			return r.Role == roleName && r.MinNeededPerShift == 5
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
