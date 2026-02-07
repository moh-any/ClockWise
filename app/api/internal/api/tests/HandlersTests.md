# API Handler Test Documentation

This documentation provides an overview of the unit tests for the API layer of the **Clockwise** backend. These tests utilize `gin-gonic`'s test mode and `testify/mock` to simulate HTTP requests and verify controller logic, middleware authentication, and service interactions without requiring a live server or database.

## Table of Contents
- [Alert Handler Tests](#alert-handler-tests)
- [Campaign Handler Tests](#campaign-handler-tests)
- [Dashboard Handler Tests](#dashboard-handler-tests)
- [Employee Handler Tests](#employee-handler-tests)
- [Insights Handler Tests](#insights-handler-tests)
- [Orders Handler Tests](#orders-handler-tests)
- [Organization Handler Tests](#organization-handler-tests)
- [Preferences Handler Tests](#preferences-handler-tests)
- [Profile Handler Tests](#profile-handler-tests)
- [Roles Handler Tests](#roles-handler-tests)
- [Rules Handler Tests](#rules-handler-tests)
- [Schedule Handler Tests](#schedule-handler-tests)
- [Staffing Handler Tests](#staffing-handler-tests)

---

## Alert Handler Tests
**File:** `alert_handler_test.go`  
**Focus:** Alert retrieval, weekly filtering, and alert analytics for admin and manager users.

| Test Function | Description | Scenarios Covered |
| :--- | :--- | :--- |
| **`TestGetAllAlertsHandler`** | Verifies retrieval of all alerts for an organization. | • **Success (Admin):** Returns all alerts.<br>• **Success (Manager):** Manager can also access alerts.<br>• **Forbidden:** Employee role is denied access (403).<br>• **DBError:** Handles database failure gracefully (500).<br>• **Unauthorized:** Rejects requests without user context (401). |
| **`TestGetAllAlertsForLastWeekHandler`** | Verifies filtered retrieval of alerts from the past 7 days. | • **Success:** Returns weekly alerts.<br>• **Forbidden:** Employee role is denied access.<br>• **DBError:** Handles database failure gracefully. |
| **`TestGetAlertInsightsHandler`** | Verifies aggregation of alert statistics. | • **Success:** Returns alert analytics (total, severity breakdown).<br>• **Forbidden:** Employee role is denied access.<br>• **DBError:** Handles database failure gracefully. |

---

## Campaign Handler Tests
**File:** `campaign_handler_test.go`  
**Focus:** Campaign CRUD, marketing insights, ML-powered recommendations, and feedback submission.

| Test Function | Description | Scenarios Covered |
| :--- | :--- | :--- |
| **`TestGetAllCampaignsHandler`** | Verifies retrieval of all marketing campaigns. | • **Success:** Returns campaigns with discount info.<br>• **Forbidden:** Employee role is denied access.<br>• **DBError:** Handles database failure gracefully. |
| **`TestGetAllCampaignsForLastWeekHandler`** | Verifies filtered campaign retrieval for the past 7 days. | • **Success:** Returns recent campaigns.<br>• **Forbidden:** Employee role is denied access.<br>• **DBError:** Handles database failure gracefully. |
| **`TestGetCampaignsInsightsHandler`** | Verifies aggregation of campaign statistics. | • **Success:** Returns campaign analytics.<br>• **Forbidden:** Employee role is denied access.<br>• **DBError:** Handles database failure gracefully. |
| **`TestRecommendCampaignsHandler`** | Verifies ML recommendation request validation. | • **Forbidden:** Employee role is denied access.<br>• **InvalidBody:** Rejects missing required fields (400). |
| **`TestSubmitCampaignFeedbackHandler`** | Verifies ML feedback submission validation. | • **Forbidden:** Employee role is denied access.<br>• **InvalidBody:** Rejects missing required fields (400). |

---

## Dashboard Handler Tests
**File:** `dashboard_handler_test.go`  
**Focus:** Demand heatmap retrieval and ML-powered demand prediction workflows.

| Test Function | Description | Scenarios Covered |
| :--- | :--- | :--- |
| **`TestGetDemandHeatMapHandler`** | Verifies retrieval of stored demand prediction data. | • **Success (Admin):** Returns demand heatmap data.<br>• **Success (Manager):** Manager can also access demand data.<br>• **Forbidden:** Employee role is denied access.<br>• **NotFound:** Returns 404 when no demand data exists.<br>• **DBError:** Handles database failure gracefully.<br>• **Unauthorized:** Rejects unauthenticated requests. |
| **`TestPredictDemandHeatMapHandler`** | Verifies the multi-step data gathering before calling the ML service. | • **Forbidden:** Employee role is denied access.<br>• **OrgNotFound:** Returns 404 when organization doesn't exist.<br>• **OrgDBError:** Returns 500 on organization fetch failure.<br>• **RulesNotFound:** Returns 404 when rules are missing.<br>• **OperatingHoursNotFound:** Returns 404 when operating hours are missing.<br>• **NoOrders:** Returns 404 when no orders exist.<br>• **NoCampaigns:** Returns 404 when no campaigns exist. |

---

## Employee Handler Tests
**File:** `employee_handler_test.go`  
**Focus:** Management of individual employee records, termination logic, and request handling.

| Test Function | Description | Scenarios Covered |
| :--- | :--- | :--- |
| **`TestGetEmployeeDetails`** | Verifies retrieval of specific employee profile data. | • **Success:** Admin fetches employee details.<br>• **InvalidUUID:** Malformed ID format returns 400.<br>• **EmployeeNotFound:** Non-existent ID returns 404.<br>• **DifferentOrganization:** Accessing user from another org returns 403. |
| **`TestLayoffEmployee`** | Verifies the logic for terminating an employee. | • **Success:** Admin successfully lays off a user (updates DB & sends email).<br>• **Forbidden:** Regular employee cannot trigger layoffs.<br>• **Forbidden (Self):** Admin cannot lay off themselves. |
| **`TestGetEmployeeRequests`** | Verifies retrieval of time-off/schedule requests. | • **Success:** Employee fetches their own request history. |
| **`TestApproveRequest`** | Verifies manager approval workflow. | • **Success:** Manager approves a request; status updates and email is sent.<br>• **Forbidden:** Regular employee cannot approve requests. |
| **`TestDeclineRequest`** | Verifies request denial workflow. | • **Success:** Admin declines a request; status updates and email is sent. |
| **`TestRequestHandlerForEmployee`** | Verifies submission of new requests. | • **Success:** Employee submits a "calloff" request; notifications sent to managers/admins.<br>• **Forbidden:** Admin cannot submit employee requests.<br>• **BadRequest:** Submission with invalid request type. |

---

## Insights Handler Tests
**File:** `insights_handler_test.go`  
**Focus:** Dashboard analytics and role-based data retrieval.

| Test Function | Description | Scenarios Covered |
| :--- | :--- | :--- |
| **`TestGetInsightsHandler`** | Verifies the main analytics endpoint logic. | • **Success (Admin):** Calls `GetInsightsForAdmin`.<br>• **Success (Manager):** Calls `GetInsightsForManager`.<br>• **Success (Employee):** Calls `GetInsightsForEmployee`.<br>• **Failure:** Handles database errors gracefully (500).<br>• **Unauthorized:** Rejects requests without user context. |

---

## Orders Handler Tests
**File:** `orders_handler_test.go`  
**Focus:** Order management, menu items, delivery tracking, and associated analytics.

| Test Function | Description | Scenarios Covered |
| :--- | :--- | :--- |
| **`TestGetAllOrdersHandler`** | Verifies retrieval of all orders for an organization. | • **Success:** Returns orders with type and status.<br>• **Forbidden:** Employee role is denied access.<br>• **DBError:** Handles database failure gracefully. |
| **`TestGetAllOrdersForLastWeekHandler`** | Verifies filtered order retrieval for the past 7 days. | • **Success:** Returns weekly orders.<br>• **Forbidden:** Employee role is denied access.<br>• **DBError:** Handles database failure gracefully. |
| **`TestGetAllOrdersTodayHandler`** | Verifies retrieval of today's orders. | • **Success:** Returns today's orders.<br>• **Forbidden:** Employee role is denied access.<br>• **DBError:** Handles database failure gracefully. |
| **`TestGetOrdersInsightsHandler`** | Verifies aggregation of order statistics. | • **Success:** Returns order analytics (total, average value).<br>• **DBError:** Handles database failure gracefully. |
| **`TestGetAllItemsHandler`** | Verifies retrieval of all menu items. | • **Success:** Returns items with price and prep staff info.<br>• **Forbidden:** Employee role is denied access.<br>• **DBError:** Handles database failure gracefully. |
| **`TestGetItemsInsightsHandler`** | Verifies aggregation of menu item statistics. | • **Success:** Returns item analytics (most popular, avg price).<br>• **DBError:** Handles database failure gracefully. |
| **`TestGetAllDeliveriesHandler`** | Verifies retrieval of all deliveries. | • **Success:** Returns deliveries with status and driver info.<br>• **Forbidden:** Employee role is denied access.<br>• **DBError:** Handles database failure gracefully. |
| **`TestGetAllDeliveriesForLastWeekHandler`** | Verifies filtered delivery retrieval for the past 7 days. | • **Success:** Returns weekly deliveries.<br>• **DBError:** Handles database failure gracefully. |
| **`TestGetAllDeliveriesTodayHandler`** | Verifies retrieval of today's deliveries. | • **Success:** Returns today's deliveries.<br>• **DBError:** Handles database failure gracefully. |
| **`TestGetDeliveryInsightsHandler`** | Verifies aggregation of delivery statistics. | • **Success:** Returns delivery analytics.<br>• **DBError:** Handles database failure gracefully. |

---

## Organization Handler Tests
**File:** `org_handler_test.go`  
**Focus:** Organization registration, user delegation, and profile management.

| Test Function | Description | Scenarios Covered |
| :--- | :--- | :--- |
| **`TestRegisterOrganization`** | Verifies the sign-up flow for new organizations. | • **Success:** Creates Organization and Admin user transactionally.<br>• **BadRequest:** Handles invalid JSON payload. |
| **`TestDelegateUser`** | Verifies creation of new staff members by Admins. | • **Success:** Admin creates an "employee".<br>• **Success:** Admin creates a "manager".<br>• **Forbidden:** Staff cannot delegate new users.<br>• **Failure:** Validates role types (rejects invalid roles). |
| **`TestGetOrganizationProfile`** | Verifies fetching organization summary data. | • **Success:** Returns org name and employee count.<br>• **Unauthorized:** Fails if user is not authenticated.<br>• **StoreError:** Handles DB failures gracefully. |

---

## Preferences Handler Tests
**File:** `preferences_handler_test.go`  
**Focus:** Employee scheduling availability and preferences.

| Test Function | Description | Scenarios Covered |
| :--- | :--- | :--- |
| **`TestGetCurrentEmployeePreferences`** | Verifies fetching a user's own preferences. | • **Success:** Returns preferences, current roles, and max hours.<br>• **Failure:** Handles database retrieval errors. |
| **`TestUpdateCurrentEmployeePreferences`** | Verifies updating availability and roles. | • **Success:** Updates preferences, user roles, and max hours transactionally.<br>• **InvalidDay:** Rejects unknown days (e.g., "Funday").<br>• **DuplicateDay:** Rejects duplicate entries for the same day.<br>• **InvalidRole:** Rejects roles that do not exist in the organization. |

---

## Profile Handler Tests
**File:** `profile_handler_test.go`  
**Focus:** User profile management and security settings.

| Test Function | Description | Scenarios Covered |
| :--- | :--- | :--- |
| **`TestGetProfileHandler`** | Verifies retrieval of the logged-in user's profile. | • **Success:** Returns full user profile.<br>• **NotFound:** User ID not found in DB.<br>• **Unauthorized:** Request missing authentication context. |
| **`TestChangePasswordHandler`** | Verifies password update logic. | • **Success:** Updates password when old password matches.<br>• **IncorrectOldPassword:** Fails update if old password is wrong.<br>• **InvalidBody:** Rejects empty fields.<br>• **DBError:** Handles storage failure during update. |

---

## Roles Handler Tests
**File:** `roles_handler_test.go`  
**Focus:** CRUD operations for organization roles (e.g., Server, Chef).

| Test Function | Description | Scenarios Covered |
| :--- | :--- | :--- |
| **`TestGetAllRoles`** | Verifies listing of all defined roles. | • **Success:** Admin fetches role list.<br>• **Forbidden:** Regular employees cannot access the role list. |
| **`TestCreateRole`** | Verifies definition of new roles. | • **Success:** Creates a new role.<br>• **ProtectedRole:** Prevents creation of roles named "admin".<br>• **Conflict:** Fails if role name already exists.<br>• **Validation:** Fails if `need_for_demand` is true but `items_per_role` is missing. |
| **`TestGetRole`** | Verifies fetching a single role by name. | • **Success:** Returns role details.<br>• **NotFound:** Returns 404 for non-existent role. |
| **`TestUpdateRole`** | Verifies modifying existing roles. | • **Success:** Updates role properties.<br>• **Protected:** Prevents updating "admin" role.<br>• **NotFound:** Returns 404 for non-existent role. |
| **`TestDeleteRole`** | Verifies removal of roles. | • **Success:** Deletes role.<br>• **Protected:** Prevents deletion of "manager" or "admin".<br>• **NotFound:** Returns 404 for non-existent role. |

---

## Rules Handler Tests
**File:** `rules_handler_test.go`  
**Focus:** Organization scheduling rules and operating hours.

| Test Function | Description | Scenarios Covered |
| :--- | :--- | :--- |
| **`TestGetOrganizationRules`** | Verifies retrieval of rules and hours. | • **Success:** Returns rules and operating hours.<br>• **Success (No Rules):** Returns empty set gracefully.<br>• **Forbidden:** Employee cannot view admin rules.<br>• **DBError:** Handles storage failures. |
| **`TestUpdateOrganizationRules`** | Verifies updating scheduling constraints. | • **Success:** Updates rules and operating hours.<br>• **Forbidden:** Managers cannot update organization rules.<br>• **Validation (Min/Max):** Fails if Min hours > Max hours.<br>• **Validation (Fixed):** Fails if `fixed_shifts` is true but `shifts_per_day` is missing.<br>• **Validation (Day):** Fails on invalid weekday names. |

---

## Schedule Handler Tests
**File:** `schedule_handler_test.go`  
**Focus:** Schedule retrieval, per-employee schedules, and demand-based schedule prediction.

| Test Function | Description | Scenarios Covered |
| :--- | :--- | :--- |
| **`TestGetScheduleHandler`** | Verifies full schedule retrieval for the organization. | • **Admin Success:** Admin retrieves full schedule.<br>• **Manager Success:** Manager retrieves full schedule.<br>• **Forbidden:** Employee role is denied access.<br>• **DBError:** Handles database failure gracefully.<br>• **Unauthorized:** Missing auth token is rejected. |
| **`TestGetCurrentUserScheduleHandler`** | Verifies schedule retrieval for the currently authenticated user. | • **Employee Success:** Employee retrieves own schedule.<br>• **Manager Success:** Manager retrieves own schedule.<br>• **Forbidden:** Admin role is denied access.<br>• **DBError:** Handles database failure gracefully. |
| **`TestGetEmployeeScheduleHandler`** | Verifies schedule retrieval for a specific employee by ID. | • **Success:** Returns schedule for the specified employee.<br>• **Invalid ID:** Rejects non-UUID employee ID.<br>• **Not Found:** Returns error for non-existent employee.<br>• **Different Org:** Denies access to employees in other organizations.<br>• **DBError:** Handles database failure gracefully. |
| **`TestPredictScheduleHandler`** | Verifies ML-based schedule prediction requiring multiple data sources. | • **Forbidden:** Employee role is denied access.<br>• **OrgError:** Handles org retrieval failure.<br>• **RulesError:** Handles rules retrieval failure.<br>• **HoursError:** Handles operating hours retrieval failure.<br>• **DemandError:** Handles demand data retrieval failure.<br>• **RolesError:** Handles roles retrieval failure.<br>• **EmployeesError:** Handles employee list retrieval failure. |

---

## Staffing Handler Tests
**File:** `staffing_handler_test.go`  
**Focus:** Bulk employee management and reporting.

| Test Function | Description | Scenarios Covered |
| :--- | :--- | :--- |
| **`TestGetStaffingSummary`** | Verifies aggregation of staff counts. | • **Success:** Returns counts of employees per role.<br>• **Failure:** Handles DB aggregation errors. |
| **`TestGetAllEmployees`** | Verifies listing of all staff members. | • **Success:** Returns list of all users in the org.<br>• **Failure:** Handles DB retrieval errors. |
| **`TestUploadEmployeesCSV`** | Verifies bulk user creation via file upload. | • **Success:** Parses CSV, creates users, and sends welcome emails.<br>• **Forbidden:** Employees cannot upload staff lists.<br>• **NoFile:** Fails if file is missing.<br>• **InvalidCSV:** Fails on missing required headers.<br>• **Partial Failure:** Continues processing valid rows even if some fail validation. |