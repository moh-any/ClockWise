# Database Layer Test Documentation

This documentation provides an overview of the unit tests for the PostgreSQL storage layer in the **Clockwise** backend. These tests utilize `go-sqlmock` to simulate database interactions, ensuring that queries are constructed correctly, transactions are handled properly, and data scanning logic works as expected without requiring a live database connection.

## Table of Contents
- [Alert Store Tests](#alert-store-tests)
- [Campaign Store Tests](#campaign-store-tests)
- [Demand Store Tests](#demand-store-tests)
- [Insight Store Tests](#insight-store-tests)
- [Operating Hours Store Tests](#operating-hours-store-tests)
- [Order Store Tests](#order-store-tests)
- [Organization Store Tests](#organization-store-tests)
- [Preferences Store Tests](#preferences-store-tests)
- [Request Store Tests](#request-store-tests)
- [Roles Store Tests](#roles-store-tests)
- [Rules Store Tests](#rules-store-tests)
- [Schedule Store Tests](#schedule-store-tests)
- [User Roles Store Tests](#user-roles-store-tests)
- [User Store Tests](#user-store-tests)

---

## Alert Store Tests
**File:** `alert_store_test.go`  
**Focus:** Alert storage and analytics for organization-level notifications.

| Test Function | Description | Key Verifications |
| :--- | :--- | :--- |
| **`TestStoreAlert`** | Placeholder for alert creation. | Currently a no-op; reserved for future implementation. |
| **`TestGetAllAlerts`** | Retrieves all alerts for an organization. | **Success:** Verifies correct mapping of severity, type, message, and timestamp.<br>**Empty:** Returns empty slice when no alerts exist.<br>**DBError:** Handles query failure gracefully. |
| **`TestGetAllAlertsForLastWeek`** | Retrieves alerts from the past 7 days. | **Success:** Verifies time-filtered query returns correct alerts.<br>**DBError:** Handles query failure gracefully. |
| **`TestGetAlertInsights`** | Aggregates alert statistics by severity. | **Success:** Verifies 4 insight values — Total Alerts, High Severity, Medium Severity, Low Severity counts.<br>**NoAlerts:** Returns all-zero insights when no alerts exist.<br>**DBError:** Handles query failure gracefully. |

---

## Campaign Store Tests
**File:** `campaign_store_test.go`  
**Focus:** Marketing campaign storage, item associations, and campaign analytics.

| Test Function | Description | Key Verifications |
| :--- | :--- | :--- |
| **`TestStoreCampaign`** | Creates a new marketing campaign. | **Success:** Verifies insertion with name, description, discount, start/end dates, and `RETURNING id` capture.<br>**DBError:** Handles insert failure gracefully. |
| **`TestStoreCampaignItems`** | Associates menu items with a campaign. | **Success:** Verifies campaign existence check followed by item insertions.<br>**CampaignNotFound:** Returns error when the campaign does not exist. |
| **`TestGetAllCampaigns`** | Retrieves all campaigns with their associated items. | **Success:** Verifies campaign retrieval followed by per-campaign item population via secondary queries.<br>**Empty:** Returns empty slice when no campaigns exist.<br>**DBError:** Handles query failure gracefully. |
| **`TestGetAllCampaignsFromLastWeek`** | Retrieves campaigns created in the past 7 days. | **Success:** Verifies time-filtered query returns recent campaigns. |
| **`TestGetCampaignInsights`** | Aggregates campaign statistics. | **Success:** Verifies 5 insight values — Total Campaigns, Active Campaigns, Average Discount, Highest Discount Campaign, Most Items Campaign.<br>**DBError:** Handles query failure gracefully. |

---

## Demand Store Tests
**File:** `demand_store_test.go`  
**Focus:** Demand heatmap storage and retrieval for scheduling optimization.

| Test Function | Description | Key Verifications |
| :--- | :--- | :--- |
| **`TestStoreDemandHeatMap`** | Saves a full demand heatmap for an organization. | **Success:** **Transactional:** Deletes existing demand data, then inserts new hourly demand entries within a single transaction.<br>**RollbackOnInsert:** Verifies rollback when an insert fails mid-transaction.<br>**RollbackOnDelete:** Verifies rollback when the initial delete fails. |
| **`TestGetLatestDemandHeatMap`** | Retrieves the most recent demand heatmap grouped by day. | **Success:** Verifies rows are grouped by `day_of_week` using `MAX(created_at)` and ordered Sunday–Saturday.<br>**NoData:** Returns empty slice when no demand data exists.<br>**DBError:** Handles query failure gracefully. |
| **`TestDeleteDemandByOrganization`** | Removes all demand data for an organization. | **Success:** Verifies deletion query executes correctly.<br>**NoData:** Succeeds silently when no rows match.<br>**DBError:** Handles query failure gracefully. |

---

## Insight Store Tests
**File:** `insight_store_test.go`  
**Focus:** Analytics and dashboard statistics for different user roles.

| Test Function | Description | Key Verifications |
| :--- | :--- | :--- |
| **`TestGetInsightsForAdmin`** | Verifies the aggregation of high-level organization data for the Admin dashboard. | Checks 16 specific data points including: Employee counts, counts per role, average salaries, table capacity, current occupancy, revenue, shift data, and top-selling items. |
| **`TestGetInsightsForManager`** | Verifies the retrieval of specific data relevant to managers. | Validates 9 data points including: Personal salary, staff/intern counts, table capacity, daily orders, shift data, and delivery stats. |
| **`TestGetInsightsForEmployee`** | Verifies the retrieval of data relevant to standard employees. | Validates 9 data points including: Personal salary/role, manager availability on shift, and current restaurant capacity. |
| **`TestGetInsightsForEmployee` (NoManagerOnShift)** | Edge case test where no manager is currently working. | Ensures the system returns "No manager on shift" gracefully instead of failing or returning null. |

---

## Operating Hours Store Tests
**File:** `operating_hours_store_test.go`  
**Focus:** Management of organization opening and closing times.

| Test Function | Description | Key Verifications |
| :--- | :--- | :--- |
| **`TestGetOperatingHours`** | Fetches the full weekly schedule for an organization. | Ensures rows are ordered correctly by day of the week (Sunday to Saturday). |
| **`TestGetOperatingHoursByDay`** | Fetches operating hours for a specific day. | Tests successful retrieval and `sql.ErrNoRows` handling. |
| **`TestSetOperatingHours`** | Replaces the entire schedule for an organization. | **Transactional:** Verifies that existing hours are deleted and new hours are inserted within a single transaction. |
| **`TestUpsertOperatingHours`** | Inserts or updates a single day's hours. | Verifies the `ON CONFLICT` SQL clause is triggered to update existing records. |
| **`TestDeleteOperatingHoursByDay`** | Removes hours for a specific day. | Verifies deletion logic and error handling if the day does not exist. |
| **`TestDeleteAllOperatingHours`** | Clears the entire schedule. | Verifies the deletion query execution. |

---

## Order Store Tests
**File:** `order_store_test.go`  
**Focus:** Order processing, menu items, and delivery tracking.

| Test Function | Description | Key Verifications |
| :--- | :--- | :--- |
| **`TestGetAllOrders`** | Retrieves all orders for an organization. | Verifies complex fetching: gets Order details, then populates `OrderItems` and `DeliveryStatus` via separate queries. |
| **`TestStoreOrder`** | Creates a new order. | **Transactional:** Verifies insertion into `orders` and `deliveries` tables, followed by an upsert into `order_items`. |
| **`TestGetOrdersInsights`** | Aggregates order statistics. | Checks calculations for Total Orders, Weekly Orders, Orders Today, Busiest Day, and Busiest Hour. |
| **`TestStoreItems`** | Adds a new menu item. | Checks existence pre-flight query and subsequent insertion; tests duplicate prevention. |
| **`TestGetAllItems`** | Retrieves the full menu. | Verifies correct mapping of item fields (Price, Needed Employees). |
| **`TestGetItemsInsights`** | Aggregates menu item statistics. | Checks Total Items, Average Price, Most Expensive Item, Most Ordered Item, and Average Preparation Staff needed. |
| **`TestGetAllDeliveries`** | Retrieves delivery-specific data. | Verifies the `JOIN` between deliveries and orders. |

---

## Organization Store Tests
**File:** `org_store_test.go`  
**Focus:** Organization creation and profile management.

| Test Function | Description | Key Verifications |
| :--- | :--- | :--- |
| **`TestCreateOrgWithAdmin`** | Registers a new organization and its first admin. | **Transactional:** Ensures the Organization is inserted first, its ID is captured, and then the Admin User is inserted with that Org ID. |
| **`TestGetOrganizationByID`** | Fetches basic organization details. | Verifies field mapping for Name, Address, Location, and Branding colors. |
| **`TestGetOrganizationProfile`** | Fetches profile view + employee count. | Verifies two queries: One for org details and a second `COUNT(*)` query for non-admin employees. |
| **`TestGetManagerEmailsByOrgID`** | Fetches emails of all managers. | Verifies filtering users by `user_role = 'manager'`. |
| **`TestGetAdminEmailsByOrgID`** | Fetches emails of all admins. | Verifies filtering users by `user_role = 'admin'`. |

---

## Preferences Store Tests
**File:** `preferences_store_test.go`  
**Focus:** Employee scheduling preferences (availability).

| Test Function | Description | Key Verifications |
| :--- | :--- | :--- |
| **`TestUpsertPreference`** | Saves a single preference. | Verifies `ON CONFLICT` update logic for a specific employee and day. |
| **`TestUpsertPreferences`** | Saves multiple preferences. | **Transactional:** loops through a list of preferences and executes upserts within a transaction block. |
| **`TestGetPreferencesByEmployeeID`** | Fetches all preferences for a user. | Ensures results are ordered by day of the week. |
| **`TestGetPreferenceByDay`** | Fetches a specific day's preference. | Tests specific selection logic. |
| **`TestDeletePreferences`** | Clears all preferences for a user. | Verifies deletion by Employee ID. |
| **`TestDeletePreferenceByDay`** | Clears a specific day's preference. | Verifies deletion by Employee ID + Day. |

---

## Request Store Tests
**File:** `request_store_test.go`  
**Focus:** Time-off and administrative requests.

| Test Function | Description | Key Verifications |
| :--- | :--- | :--- |
| **`TestCreateRequest`** | Submits a new request. | Verifies insertion of request type, message, and status. |
| **`TestGetRequestByID`** | Retrieves a specific request. | Verifies correct field mapping. |
| **`TestGetRequestsByEmployee`** | Lists requests for a specific user. | Verifies filtering by Employee ID and sorting by submission date. |
| **`TestGetRequestsByOrganization`** | Lists all requests within an org. | Verifies the `JOIN` with the `users` table to fetch the requester's name and email. |
| **`TestUpdateRequestStatus`** | Approves/Denies a request. | Verifies updating the `status` and `updated_at` timestamp. |

---

## Roles Store Tests
**File:** `roles_store_test.go`  
**Focus:** Definition of workforce roles (e.g., Chef, Server).

| Test Function | Description | Key Verifications |
| :--- | :--- | :--- |
| **`TestCreateRole`** | Defines a new role. | Verifies storage of requirements like `min_needed_per_shift` and `items_per_role_per_hour`. |
| **`TestGetRolesByOrganizationID`** | Lists all roles. | Verifies retrieval. |
| **`TestGetRoleByName`** | Fetches specific role details. | Verifies filtering by role name. |
| **`TestUpdateRole`** | Modifies role requirements. | Verifies update logic and error handling if role doesn't exist. |
| **`TestDeleteRole`** | Removes a role. | **Logic Check:** Verifies that the system prevents deletion of the protected "admin" role. |

---

## Rules Store Tests
**File:** `rules_store_test.go`  
**Focus:** Scheduling constraints and logic.

| Test Function | Description | Key Verifications |
| :--- | :--- | :--- |
| **`TestCreateRules`** | Sets initial organization rules. | Verifies storage of constraints like `max_weekly_hours` and `fixed_shifts`. |
| **`TestGetRulesByOrganizationID`** | Fetches rules. | **Conditional Logic:** If `FixedShifts` is true, verifies a secondary query is executed to fetch `organization_shift_times`. |
| **`TestUpdateRules`** | Updates existing rules. | Verifies standard SQL update. |
| **`TestUpsertRules`** | Creates or Updates rules. | **Transactional:** Verifies `ON CONFLICT` update for rules, and (if applicable) deletes old shift times to prepare for new ones. |

---

## Schedule Store Tests
**File:** `schedule_store_test.go`  
**Focus:** Employee schedule storage and retrieval.

| Test Function | Description | Key Verifications |
| :--- | :--- | :--- |
| **`TestStoreScheduleForUser`** | Saves a weekly schedule for a specific employee. | **Success:** Verifies user existence in the organization before inserting schedule entries (day, start time, end time).<br>**UserNotInOrg:** Returns error when the user does not belong to the organization.<br>**VerifyError:** Handles user verification query failure.<br>**InsertError:** Handles schedule insertion failure. |
| **`TestGetScheduleForEmployeeForSevenDays`** | Retrieves 7-day schedule for a single employee. | **Success:** Verifies user existence check followed by schedule retrieval ordered by day of week.<br>**UserNotInOrg:** Returns error when the user does not belong to the organization.<br>**EmptyResult:** Returns empty slice when the user has no scheduled shifts. |

> **Note:** `GetFullScheduleForSevenDays` uses PostgreSQL `ARRAY_AGG` which cannot be tested with `go-sqlmock`. This function requires integration tests with a live database.

---

## User Roles Store Tests
**File:** `user_roles_store_test.go`  
**Focus:** Mapping users to specific roles.

| Test Function | Description | Key Verifications |
| :--- | :--- | :--- |
| **`TestGetUserRoles`** | Gets roles for a user. | Verifies retrieval. |
| **`TestSetUserRoles`** | Overwrites all roles for a user. | **Transactional:** Deletes all existing roles for the user/org combo, then inserts the new list. |
| **`TestAddUserRole`** | Adds a single role. | Verifies `ON CONFLICT DO NOTHING` to prevent duplicates. |
| **`TestRemoveUserRole`** | Removes a single role. | Verifies specific deletion. |
| **`TestDeleteAllUserRoles`** | Clears user roles. | Verifies bulk deletion for a user. |

---

## User Store Tests
**File:** `user_store_test.go`  
**Focus:** User account management and profile statistics.

| Test Function | Description | Key Verifications |
| :--- | :--- | :--- |
| **`TestCreateUser`** | Registers a user. | Verifies insertion of fields including salary, max hours, and on-call status. |
| **`TestGetUserByEmail`** | Login/Lookup functionality. | Verifies retrieval by email address. |
| **`TestUpdateUser`** | Modifies user details. | Verifies update query and `returning updated_at`. |
| **`TestLayoffUser`** | Removes a user with an audit trail. | **Transactional:** 1. Fetches user info. 2. Inserts into `layoffs_hirings` (history). 3. Deletes from `users`. |
| **`TestGetProfile`** | Fetches detailed user profile. | **Complex Query:** Verifies a query that joins `users`, `organizations`, and `schedules` to calculate `total_hours` worked and `week_hours` (current week). |
| **`TestChangePassword`** | Updates credentials. | Verifies password hash update. |