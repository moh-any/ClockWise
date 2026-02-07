package api

import (
	"mime/multipart"

	"github.com/clockwise/clockwise/backend/internal/database"
	"github.com/clockwise/clockwise/backend/internal/service"
	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
	"github.com/stretchr/testify/mock"
)

// --- Shared Middleware ---

func authMiddleware(user *database.User) gin.HandlerFunc {
	return func(c *gin.Context) {
		if user != nil {
			c.Set("user", user)
		}
		c.Next()
	}
}

// --- Shared Mocks ---

// MockUserStore
type MockUserStore struct {
	mock.Mock
}

func (m *MockUserStore) GetUserByID(id uuid.UUID) (*database.User, error) {
	args := m.Called(id)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*database.User), args.Error(1)
}

func (m *MockUserStore) GetProfile(id uuid.UUID) (*database.UserProfile, error) {
	args := m.Called(id)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*database.UserProfile), args.Error(1)
}

func (m *MockUserStore) ChangePassword(id uuid.UUID, hash []byte) error {
	args := m.Called(id, hash)
	return args.Error(0)
}

func (m *MockUserStore) LayoffUser(id uuid.UUID, reason string) error {
	args := m.Called(id, reason)
	return args.Error(0)
}

func (m *MockUserStore) CreateUser(user *database.User) error {
	args := m.Called(user)
	if user.ID == uuid.Nil {
		user.ID = uuid.New()
	}
	return args.Error(0)
}

func (m *MockUserStore) UpdateUser(user *database.User) error {
	args := m.Called(user)
	return args.Error(0)
}

func (m *MockUserStore) GetUsersByOrganization(orgID uuid.UUID) ([]*database.User, error) {
	args := m.Called(orgID)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).([]*database.User), args.Error(1)
}

func (m *MockUserStore) GetUserByEmail(email string) (*database.User, error) { return nil, nil }
func (m *MockUserStore) DeleteUser(id uuid.UUID) error                       { return nil }

// MockRequestStore
type MockRequestStore struct {
	mock.Mock
}

func (m *MockRequestStore) CreateRequest(req *database.Request) error {
	args := m.Called(req)
	if req.ID == uuid.Nil {
		req.ID = uuid.New()
	}
	return args.Error(0)
}

func (m *MockRequestStore) GetRequestByID(id uuid.UUID) (*database.Request, error) {
	args := m.Called(id)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*database.Request), args.Error(1)
}

func (m *MockRequestStore) GetRequestsByEmployee(employeeID uuid.UUID) ([]*database.Request, error) {
	args := m.Called(employeeID)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).([]*database.Request), args.Error(1)
}

func (m *MockRequestStore) UpdateRequestStatus(id uuid.UUID, status string) error {
	args := m.Called(id, status)
	return args.Error(0)
}

func (m *MockRequestStore) GetRequestsByOrganization(orgID uuid.UUID) ([]*database.RequestWithEmployee, error) {
	return nil, nil
}

// MockOrgStore
type MockOrgStore struct {
	mock.Mock
}

func (m *MockOrgStore) GetManagerEmailsByOrgID(orgID uuid.UUID) ([]string, error) {
	args := m.Called(orgID)
	return args.Get(0).([]string), args.Error(1)
}

func (m *MockOrgStore) GetAdminEmailsByOrgID(orgID uuid.UUID) ([]string, error) {
	args := m.Called(orgID)
	return args.Get(0).([]string), args.Error(1)
}

func (m *MockOrgStore) CreateOrgWithAdmin(org *database.Organization, admin *database.User, pw string) error {
	args := m.Called(org, admin, pw)
	if org.ID == uuid.Nil {
		org.ID = uuid.New()
	}
	if admin.ID == uuid.Nil {
		admin.ID = uuid.New()
	}
	return args.Error(0)
}

func (m *MockOrgStore) GetOrganizationByID(id uuid.UUID) (*database.Organization, error) {
	args := m.Called(id)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*database.Organization), args.Error(1)
}

func (m *MockOrgStore) GetOrganizationProfile(id uuid.UUID) (*database.OrganizationProfile, error) {
	args := m.Called(id)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*database.OrganizationProfile), args.Error(1)
}

// MockEmailService
type MockEmailService struct {
	mock.Mock
}

func (m *MockEmailService) SendWelcomeEmail(toEmail, username, password, role string, organization string) error {
	args := m.Called(toEmail, username, password, role, organization)
	return args.Error(0)
}

func (m *MockEmailService) SendRequestApprovedEmail(toEmail, fullName, requestType string) error {
	args := m.Called(toEmail, fullName, requestType)
	return args.Error(0)
}

func (m *MockEmailService) SendRequestDeclinedEmail(toEmail, fullName, requestType string) error {
	args := m.Called(toEmail, fullName, requestType)
	return args.Error(0)
}

func (m *MockEmailService) SendLayoffEmail(toEmail, fullName, reason string) error {
	args := m.Called(toEmail, fullName, reason)
	return args.Error(0)
}

func (m *MockEmailService) SendRequestSubmittedEmail(toEmail, fullName, requestType, message string) error {
	args := m.Called(toEmail, fullName, requestType, message)
	return args.Error(0)
}

func (m *MockEmailService) SendRequestNotifyEmail(toEmails []string, employeeName, requestType, message string) error {
	args := m.Called(toEmails, employeeName, requestType, message)
	return args.Error(0)
}

// MockRolesStore
type MockRolesStore struct {
	mock.Mock
}

func (m *MockRolesStore) GetRolesByOrganizationID(orgID uuid.UUID) ([]database.OrganizationRole, error) {
	args := m.Called(orgID)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).([]database.OrganizationRole), args.Error(1)
}

func (m *MockRolesStore) CreateRole(role *database.OrganizationRole) error {
	args := m.Called(role)
	return args.Error(0)
}

func (m *MockRolesStore) GetRoleByName(orgID uuid.UUID, name string) (*database.OrganizationRole, error) {
	args := m.Called(orgID, name)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*database.OrganizationRole), args.Error(1)
}

func (m *MockRolesStore) UpdateRole(role *database.OrganizationRole) error {
	args := m.Called(role)
	return args.Error(0)
}

func (m *MockRolesStore) DeleteRole(orgID uuid.UUID, roleName string) error {
	args := m.Called(orgID, roleName)
	return args.Error(0)
}

// MockUserRolesStore
type MockUserRolesStore struct {
	mock.Mock
}

func (m *MockUserRolesStore) SetUserRoles(userID uuid.UUID, orgID uuid.UUID, roles []string) error {
	args := m.Called(userID, orgID, roles)
	return args.Error(0)
}

func (m *MockUserRolesStore) GetUserRoles(userID uuid.UUID, orgID uuid.UUID) ([]string, error) {
	args := m.Called(userID, orgID)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).([]string), args.Error(1)
}

func (m *MockUserRolesStore) AddUserRole(userID uuid.UUID, orgID uuid.UUID, role string) error {
	return nil
}
func (m *MockUserRolesStore) RemoveUserRole(userID uuid.UUID, orgID uuid.UUID, role string) error {
	return nil
}
func (m *MockUserRolesStore) DeleteAllUserRoles(userID uuid.UUID, orgID uuid.UUID) error {
	return nil
}

// MockInsightStore
type MockInsightStore struct {
	mock.Mock
}

func (m *MockInsightStore) GetInsightsForAdmin(orgID uuid.UUID) ([]database.Insight, error) {
	args := m.Called(orgID)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).([]database.Insight), args.Error(1)
}

func (m *MockInsightStore) GetInsightsForManager(orgID uuid.UUID, userID uuid.UUID) ([]database.Insight, error) {
	args := m.Called(orgID, userID)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).([]database.Insight), args.Error(1)
}

func (m *MockInsightStore) GetInsightsForEmployee(orgID uuid.UUID, userID uuid.UUID) ([]database.Insight, error) {
	args := m.Called(orgID, userID)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).([]database.Insight), args.Error(1)
}

// MockPreferencesStore
type MockPreferencesStore struct {
	mock.Mock
}

func (m *MockPreferencesStore) UpsertPreference(pref *database.EmployeePreference) error {
	args := m.Called(pref)
	return args.Error(0)
}

func (m *MockPreferencesStore) UpsertPreferences(employeeID uuid.UUID, prefs []*database.EmployeePreference) error {
	args := m.Called(employeeID, prefs)
	return args.Error(0)
}

func (m *MockPreferencesStore) GetPreferencesByEmployeeID(employeeID uuid.UUID) ([]*database.EmployeePreference, error) {
	args := m.Called(employeeID)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).([]*database.EmployeePreference), args.Error(1)
}

func (m *MockPreferencesStore) GetPreferenceByDay(employeeID uuid.UUID, day string) (*database.EmployeePreference, error) {
	args := m.Called(employeeID, day)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*database.EmployeePreference), args.Error(1)
}

func (m *MockPreferencesStore) DeletePreferences(employeeID uuid.UUID) error {
	args := m.Called(employeeID)
	return args.Error(0)
}

func (m *MockPreferencesStore) DeletePreferenceByDay(employeeID uuid.UUID, day string) error {
	args := m.Called(employeeID, day)
	return args.Error(0)
}

// MockRulesStore
type MockRulesStore struct {
	mock.Mock
}

func (m *MockRulesStore) CreateRules(rules *database.OrganizationRules) error {
	args := m.Called(rules)
	return args.Error(0)
}

func (m *MockRulesStore) GetRulesByOrganizationID(orgID uuid.UUID) (*database.OrganizationRules, error) {
	args := m.Called(orgID)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*database.OrganizationRules), args.Error(1)
}

func (m *MockRulesStore) UpdateRules(rules *database.OrganizationRules) error {
	args := m.Called(rules)
	return args.Error(0)
}

func (m *MockRulesStore) UpsertRules(rules *database.OrganizationRules) error {
	args := m.Called(rules)
	return args.Error(0)
}

// MockOperatingHoursStore
type MockOperatingHoursStore struct {
	mock.Mock
}

func (m *MockOperatingHoursStore) GetOperatingHours(orgID uuid.UUID) ([]database.OperatingHours, error) {
	args := m.Called(orgID)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).([]database.OperatingHours), args.Error(1)
}

func (m *MockOperatingHoursStore) GetOperatingHoursByDay(orgID uuid.UUID, weekday string) (*database.OperatingHours, error) {
	args := m.Called(orgID, weekday)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*database.OperatingHours), args.Error(1)
}

func (m *MockOperatingHoursStore) SetOperatingHours(orgID uuid.UUID, hours []database.OperatingHours) error {
	args := m.Called(orgID, hours)
	return args.Error(0)
}

func (m *MockOperatingHoursStore) UpsertOperatingHours(hours *database.OperatingHours) error {
	args := m.Called(hours)
	return args.Error(0)
}

func (m *MockOperatingHoursStore) DeleteOperatingHoursByDay(orgID uuid.UUID, weekday string) error {
	args := m.Called(orgID, weekday)
	return args.Error(0)
}

func (m *MockOperatingHoursStore) DeleteAllOperatingHours(orgID uuid.UUID) error {
	args := m.Called(orgID)
	return args.Error(0)
}

// MockUploadService
type MockUploadService struct {
	mock.Mock
}

func (m *MockUploadService) ParseCSV(file multipart.File) (*service.CSVData, error) {
	args := m.Called(file) // IMPORTANT: We use mock.MatchedBy or mock.Anything in tests
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*service.CSVData), args.Error(1)
}
