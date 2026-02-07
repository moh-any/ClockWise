# API Handler Test Documentation

This documentation provides an overview of the unit tests for the API layer of the **Clockwise** backend. These tests utilize `gin-gonic`'s test mode and `testify/mock` to simulate HTTP requests and verify controller logic, middleware authentication, and service interactions without requiring a live server or database.

## Table of Contents
- [Employee Handler Tests](#employee-handler-tests)
- [Insights Handler Tests](#insights-handler-tests)
- [Organization Handler Tests](#organization-handler-tests)
- [Preferences Handler Tests](#preferences-handler-tests)
- [Profile Handler Tests](#profile-handler-tests)
- [Roles Handler Tests](#roles-handler-tests)
- [Rules Handler Tests](#rules-handler-tests)
- [Staffing Handler Tests](#staffing-handler-tests)

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

## Staffing Handler Tests
**File:** `staffing_handler_test.go`  
**Focus:** Bulk employee management and reporting.

| Test Function | Description | Scenarios Covered |
| :--- | :--- | :--- |
| **`TestGetStaffingSummary`** | Verifies aggregation of staff counts. | • **Success:** Returns counts of employees per role.<br>• **Failure:** Handles DB aggregation errors. |
| **`TestGetAllEmployees`** | Verifies listing of all staff members. | • **Success:** Returns list of all users in the org.<br>• **Failure:** Handles DB retrieval errors. |
| **`TestUploadEmployeesCSV`** | Verifies bulk user creation via file upload. | • **Success:** Parses CSV, creates users, and sends welcome emails.<br>• **Forbidden:** Employees cannot upload staff lists.<br>• **NoFile:** Fails if file is missing.<br>• **InvalidCSV:** Fails on missing required headers.<br>• **Partial Failure:** Continues processing valid rows even if some fail validation. |