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
	"time"

	"github.com/clockwise/clockwise/backend/internal/api"
	"github.com/clockwise/clockwise/backend/internal/database"
	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/mock"
)

type EmployeeTestEnv struct {
	Router       *gin.Engine
	UserStore    *MockUserStore
	RequestStore *MockRequestStore
	OrgStore     *MockOrgStore
	EmailService *MockEmailService
	Handler      *api.EmployeeHandler
}

func setupEmployeeEnv() *EmployeeTestEnv {
	gin.SetMode(gin.TestMode)

	userStore := new(MockUserStore)
	requestStore := new(MockRequestStore)
	orgStore := new(MockOrgStore)
	emailService := new(MockEmailService)
	logger := slog.New(slog.NewTextHandler(os.Stdout, nil))

	handler := api.NewEmployeeHandler(userStore, emailService, requestStore, orgStore, logger)

	return &EmployeeTestEnv{
		Router:       gin.New(),
		UserStore:    userStore,
		RequestStore: requestStore,
		OrgStore:     orgStore,
		EmailService: emailService,
		Handler:      handler,
	}
}

func TestGetEmployeeDetails(t *testing.T) {
	env := setupEmployeeEnv()
	orgID := uuid.New()
	adminUser := &database.User{ID: uuid.New(), OrganizationID: orgID, UserRole: "admin"}
	targetEmployeeID := uuid.New()
	targetEmployee := &database.User{ID: targetEmployeeID, OrganizationID: orgID, FullName: "John Doe"}

	env.Router.GET("/:org/staffing/employees/:id", authMiddleware(adminUser), env.Handler.GetEmployeeDetails)

	t.Run("Success", func(t *testing.T) {
		env.UserStore.On("GetUserByID", targetEmployeeID).Return(targetEmployee, nil).Once()

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/"+orgID.String()+"/staffing/employees/"+targetEmployeeID.String(), nil)
		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusOK, w.Code)
		assert.Contains(t, w.Body.String(), "John Doe")
		env.UserStore.AssertExpectations(t)
	})

	t.Run("InvalidUUID", func(t *testing.T) {
		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/"+orgID.String()+"/staffing/employees/invalid-uuid", nil)
		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusBadRequest, w.Code)
	})

	t.Run("EmployeeNotFound", func(t *testing.T) {
		env.UserStore.On("GetUserByID", targetEmployeeID).Return(nil, errors.New("not found")).Once()

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/"+orgID.String()+"/staffing/employees/"+targetEmployeeID.String(), nil)
		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusNotFound, w.Code)
	})

	t.Run("DifferentOrganization", func(t *testing.T) {
		diffOrgID := uuid.New()
		diffOrgEmployee := &database.User{ID: targetEmployeeID, OrganizationID: diffOrgID}

		env.UserStore.On("GetUserByID", targetEmployeeID).Return(diffOrgEmployee, nil).Once()

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/"+orgID.String()+"/staffing/employees/"+targetEmployeeID.String(), nil)
		env.Router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusForbidden, w.Code)
	})
}

func TestLayoffEmployee(t *testing.T) {
	env := setupEmployeeEnv()
	orgID := uuid.New()

	t.Run("Success_AdminLayoff", func(t *testing.T) {
		admin := &database.User{ID: uuid.New(), OrganizationID: orgID, UserRole: "admin"}
		targetID := uuid.New()
		target := &database.User{ID: targetID, OrganizationID: orgID, FullName: "Target", Email: "target@test.com", UserRole: "employee"}

		r := gin.New()
		r.DELETE("/:org/staffing/employees/:id/layoff", authMiddleware(admin), env.Handler.LayoffEmployee)

		env.UserStore.On("GetUserByID", targetID).Return(target, nil).Once()
		env.UserStore.On("LayoffUser", targetID, "Budget cuts").Return(nil).Once()

		env.EmailService.On("SendLayoffEmail", target.Email, target.FullName, "Budget cuts").Return(nil).Once()

		body := map[string]string{"reason": "Budget cuts"}
		jsonBody, _ := json.Marshal(body)
		w := httptest.NewRecorder()
		req, _ := http.NewRequest("DELETE", "/"+orgID.String()+"/staffing/employees/"+targetID.String()+"/layoff", bytes.NewBuffer(jsonBody))
		r.ServeHTTP(w, req)

		time.Sleep(10 * time.Millisecond)

		assert.Equal(t, http.StatusOK, w.Code)
		env.UserStore.AssertExpectations(t)
		env.EmailService.AssertExpectations(t)
	})

	t.Run("Forbidden_EmployeeAttempt", func(t *testing.T) {
		employee := &database.User{ID: uuid.New(), OrganizationID: orgID, UserRole: "employee"}
		targetID := uuid.New()

		r := gin.New()
		r.DELETE("/:org/staffing/employees/:id/layoff", authMiddleware(employee), env.Handler.LayoffEmployee)

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("DELETE", "/"+orgID.String()+"/staffing/employees/"+targetID.String()+"/layoff", nil)
		r.ServeHTTP(w, req)

		assert.Equal(t, http.StatusForbidden, w.Code)
	})

	t.Run("Forbidden_SelfLayoff", func(t *testing.T) {
		admin := &database.User{ID: uuid.New(), OrganizationID: orgID, UserRole: "admin"}

		r := gin.New()
		r.DELETE("/:org/staffing/employees/:id/layoff", authMiddleware(admin), env.Handler.LayoffEmployee)

		env.UserStore.On("GetUserByID", admin.ID).Return(admin, nil).Once()

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("DELETE", "/"+orgID.String()+"/staffing/employees/"+admin.ID.String()+"/layoff", nil)
		r.ServeHTTP(w, req)

		assert.Equal(t, http.StatusBadRequest, w.Code)
		assert.Contains(t, w.Body.String(), "Cannot layoff yourself")
	})
}

func TestGetEmployeeRequests(t *testing.T) {
	env := setupEmployeeEnv()
	orgID := uuid.New()

	t.Run("Success_OwnRequests", func(t *testing.T) {
		employeeID := uuid.New()
		employee := &database.User{ID: employeeID, OrganizationID: orgID, UserRole: "employee"}

		r := gin.New()
		r.GET("/:org/staffing/employees/:id/requests", authMiddleware(employee), env.Handler.GetEmployeeRequests)

		requests := []*database.Request{
			{ID: uuid.New(), Type: "time-off", Status: "pending"},
		}

		env.UserStore.On("GetUserByID", employeeID).Return(employee, nil).Once()
		env.RequestStore.On("GetRequestsByEmployee", employeeID).Return(requests, nil).Once()

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/"+orgID.String()+"/staffing/employees/"+employeeID.String()+"/requests", nil)
		r.ServeHTTP(w, req)

		assert.Equal(t, http.StatusOK, w.Code)
		assert.Contains(t, w.Body.String(), "time-off")
	})
}

func TestApproveRequest(t *testing.T) {
	env := setupEmployeeEnv()
	orgID := uuid.New()
	manager := &database.User{ID: uuid.New(), OrganizationID: orgID, UserRole: "manager"}

	t.Run("Success", func(t *testing.T) {
		reqID := uuid.New()
		employeeID := uuid.New()
		employee := &database.User{ID: employeeID, OrganizationID: orgID, FullName: "John", Email: "john@test.com"}
		request := &database.Request{ID: reqID, EmployeeID: employeeID, Type: "holiday"}

		r := gin.New()
		r.POST("/:org/staffing/employees/:id/requests/approve", authMiddleware(manager), env.Handler.ApproveRequest)

		env.RequestStore.On("GetRequestByID", reqID).Return(request, nil).Once()
		env.UserStore.On("GetUserByID", employeeID).Return(employee, nil).Once()
		env.RequestStore.On("UpdateRequestStatus", reqID, "accepted").Return(nil).Once()

		env.EmailService.On("SendRequestApprovedEmail", employee.Email, employee.FullName, "holiday").Return(nil).Once()

		body := map[string]string{"request_id": reqID.String()}
		jsonBody, _ := json.Marshal(body)

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("POST", "/"+orgID.String()+"/staffing/employees/"+employeeID.String()+"/requests/approve", bytes.NewBuffer(jsonBody))
		r.ServeHTTP(w, req)

		time.Sleep(10 * time.Millisecond)

		assert.Equal(t, http.StatusOK, w.Code)
		env.RequestStore.AssertExpectations(t)
		env.EmailService.AssertExpectations(t)
	})

	t.Run("Forbidden_EmployeeApproves", func(t *testing.T) {
		emp := &database.User{ID: uuid.New(), OrganizationID: orgID, UserRole: "employee"}
		r := gin.New()
		r.POST("/:org/staffing/employees/:id/requests/approve", authMiddleware(emp), env.Handler.ApproveRequest)

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("POST", "/"+orgID.String()+"/staffing/employees/any/requests/approve", nil)
		r.ServeHTTP(w, req)

		assert.Equal(t, http.StatusForbidden, w.Code)
	})
}

func TestDeclineRequest(t *testing.T) {
	env := setupEmployeeEnv()
	orgID := uuid.New()
	admin := &database.User{ID: uuid.New(), OrganizationID: orgID, UserRole: "admin"}

	t.Run("Success", func(t *testing.T) {
		reqID := uuid.New()
		employeeID := uuid.New()
		employee := &database.User{ID: employeeID, OrganizationID: orgID, FullName: "John", Email: "john@test.com"}
		request := &database.Request{ID: reqID, EmployeeID: employeeID, Type: "calloff"}

		r := gin.New()
		r.POST("/:org/staffing/employees/:id/requests/decline", authMiddleware(admin), env.Handler.DeclineRequest)

		env.RequestStore.On("GetRequestByID", reqID).Return(request, nil).Once()
		env.UserStore.On("GetUserByID", employeeID).Return(employee, nil).Once()
		env.RequestStore.On("UpdateRequestStatus", reqID, "declined").Return(nil).Once()

		env.EmailService.On("SendRequestDeclinedEmail", employee.Email, employee.FullName, "calloff").Return(nil).Once()

		body := map[string]string{"request_id": reqID.String()}
		jsonBody, _ := json.Marshal(body)

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("POST", "/"+orgID.String()+"/staffing/employees/"+employeeID.String()+"/requests/decline", bytes.NewBuffer(jsonBody))
		r.ServeHTTP(w, req)

		time.Sleep(10 * time.Millisecond)

		assert.Equal(t, http.StatusOK, w.Code)
		env.RequestStore.AssertExpectations(t)
	})
}

func TestRequestHandlerForEmployee(t *testing.T) {
	env := setupEmployeeEnv()
	orgID := uuid.New()

	t.Run("Success_SubmitRequest", func(t *testing.T) {
		user := &database.User{ID: uuid.New(), OrganizationID: orgID, FullName: "Test User", Email: "test@test.com", UserRole: "employee"}

		r := gin.New()
		r.POST("/:org/request", authMiddleware(user), env.Handler.RequestHandlerForEmployee)

		env.RequestStore.On("CreateRequest", mock.MatchedBy(func(r *database.Request) bool {
			return r.EmployeeID == user.ID && r.Type == "calloff" && r.Message == "Sick"
		})).Return(nil).Once()

		env.EmailService.On("SendRequestSubmittedEmail", user.Email, user.FullName, "calloff", "Sick").Return(nil).Once()

		managers := []string{"mgr@test.com"}
		admins := []string{"admin@test.com"}
		env.OrgStore.On("GetManagerEmailsByOrgID", orgID).Return(managers, nil).Once()
		env.OrgStore.On("GetAdminEmailsByOrgID", orgID).Return(admins, nil).Once()

		allEmails := append(managers, admins...)
		env.EmailService.On("SendRequestNotifyEmail", allEmails, user.FullName, "calloff", "Sick").Return(nil).Once()

		body := api.CalloffRequest{Type: "calloff", Message: "Sick"}
		jsonBody, _ := json.Marshal(body)

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("POST", "/"+orgID.String()+"/request", bytes.NewBuffer(jsonBody))
		r.ServeHTTP(w, req)

		time.Sleep(20 * time.Millisecond)

		assert.Equal(t, http.StatusCreated, w.Code)
		env.RequestStore.AssertExpectations(t)
		env.EmailService.AssertExpectations(t)
	})

	t.Run("Forbidden_AdminCannotSubmit", func(t *testing.T) {
		admin := &database.User{ID: uuid.New(), OrganizationID: orgID, UserRole: "admin"}
		r := gin.New()
		r.POST("/:org/request", authMiddleware(admin), env.Handler.RequestHandlerForEmployee)

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("POST", "/"+orgID.String()+"/request", nil)
		r.ServeHTTP(w, req)

		assert.Equal(t, http.StatusForbidden, w.Code)
	})

	t.Run("BadRequest_InvalidType", func(t *testing.T) {
		user := &database.User{ID: uuid.New(), OrganizationID: orgID, UserRole: "employee"}
		r := gin.New()
		r.POST("/:org/request", authMiddleware(user), env.Handler.RequestHandlerForEmployee)

		body := map[string]string{"type": "invalid-type", "message": "hello"}
		jsonBody, _ := json.Marshal(body)

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("POST", "/"+orgID.String()+"/request", bytes.NewBuffer(jsonBody))
		r.ServeHTTP(w, req)

		assert.Equal(t, http.StatusBadRequest, w.Code)
	})
}
