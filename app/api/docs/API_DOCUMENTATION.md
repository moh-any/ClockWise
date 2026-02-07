# ClockWise API Documentation

## Overview

ClockWise is a workforce management API built with Go and Gin framework. This document provides comprehensive documentation for all API endpoints.

**Base URL:** `http://localhost:8080`

## Authentication

The API uses JWT (JSON Web Tokens) for authentication. After logging in, include the access token in the Authorization header:

```
Authorization: Bearer <access_token>
```

**Token Details:**
- Access Token Timeout: 15 minutes
- Refresh Token Timeout: 7 days

---

## Table of Contents

1. [Health Check](#health-check)
2. [Authentication](#authentication-endpoints)
3. [Profile](#profile-endpoints)
4. [Roles](#roles-endpoints)
5. [Rules](#rules-endpoints)
6. [Preferences](#preferences-endpoints)
7. [Staffing](#staffing-endpoints)
8. [Insights](#insights-endpoints)
9. [Organization](#organization-endpoints)
10. [Orders](#orders-endpoints)
11. [Deliveries](#deliveries-endpoints)
12. [Items](#items-endpoints)
13. [Campaigns](#campaigns-endpoints)
14. [Schedule](#schedule-endpoints)
15. [Alerts](#alerts-endpoints)

---

## Health Check

### GET /health

Check if the server is running and healthy.

**Authentication:** Not required

**Request:**
```http
GET /health
```

**Response (200 OK):**
```json
{
  "status": "healthy"
}
```

---

## Authentication Endpoints

### POST /api/register

Register a new organization along with an admin user account.

**Authentication:** Not required

**Request:**
```http
POST /api/register
Content-Type: application/json
```

**Request Body:**
```json
{
  "org_name": "string (required)",
  "org_address": "string (optional)",
  "org_type": "string (required - restaurant|cafe|bar|lounge|pub)",
  "org_phone": "string (required)",
  "latitude": "number (optional)",
  "longitude": "number (optional)",
  "admin_full_name": "string (required)",
  "admin_email": "string (required, valid email)",
  "admin_password": "string (required, min 8 characters)",
  "hex1": "string (required, 6 characters - primary color)",
  "hex2": "string (required, 6 characters - secondary color)",
  "hex3": "string (required, 6 characters - tertiary color)"
}
```

**Example Request:**
```json
{
  "org_name": "TestOrg",
  "org_address": "123 Main St",
  "org_type": "restaurant",
  "org_phone": "+1234567890",
  "admin_full_name": "Admin User",
  "admin_email": "admin@testorg.com",
  "admin_password": "password123",
  "hex1": "FF5733",
  "hex2": "33FF57",
  "hex3": "3357FF"
}
```

**Response (201 Created):**
```json
{
  "message": "Organization registered successfully",
  "organization_id": "uuid",
  "user_id": "uuid"
}
```

**Error Responses:**
- `400 Bad Request` - Invalid request body
- `500 Internal Server Error` - Registration failed (e.g., organization name already exists)

---

### POST /api/login

Authenticate a user and receive access/refresh tokens.

**Authentication:** Not required

**Request:**
```http
POST /api/login
Content-Type: application/json
```

**Request Body:**
```json
{
  "email": "string (required)",
  "password": "string (required)"
}
```

**Example Request:**
```json
{
  "email": "admin@testorg.com",
  "password": "password123"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "sXSIUoHenGzizScOZH_qS_BFt25ESEWJsL3mbAOTeWk=",
  "expires_in": 900,
  "token_type": "Bearer"
}
```

**Error Responses:**
- `401 Unauthorized` - Invalid credentials

---

### GET /api/auth/me

Get the current authenticated user's claims from the JWT token.

**Authentication:** Required

**Request:**
```http
GET /api/auth/me
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "id": "uuid",
  "full_name": "Admin User",
  "email": "admin@testorg.com",
  "user_role": "admin",
  "organization_id": "uuid",
  "salary_per_hour": null,
  "max_hours_per_week": 40,
  "preferred_hours_per_week": 35,
  "max_consec_slots": 8,
  "on_call" : ok
}
```

**Error Responses:**
- `401 Unauthorized` - Missing or invalid token

---

### POST /api/auth/refresh

Refresh an existing JWT token to get a new access token.

**Authentication:** Required (current valid access token)

**Request:**
```http
POST /api/auth/refresh
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "refresh_token": "string (required - from login response)"
}
```

**Example Request:**
```json
{
  "refresh_token": "sXSIUoHenGzizScOZH_qS_BFt25ESEWJsL3mbAOTeWk="
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "C_vkmdBJaMbb5PTPKUums4mdH-GJg0A_N7yXQzMyA_Y=",
  "expires_at": 1770373220
}
```

**Error Responses:**
- `401 Unauthorized` - Missing refresh_token parameter or invalid token

---

### POST /api/auth/logout

Logout the current user.

**Authentication:** Required

**Request:**
```http
POST /api/auth/logout
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "code": 200
}
```

---

## Profile Endpoints

### GET /api/auth/profile

Get the current user's profile information including calculated work hours.

**Authentication:** Required

**Request:**
```http
GET /api/auth/profile
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "message": "Profile retrieved successfully",
  "data": {
    "full_name": "Admin User",
    "email": "admin@testorg.com",
    "user_role": "admin",
    "salary_per_hour": null,
    "organization": "TestOrg",
    "created_at": "2026-02-06T09:47:57.291686Z",
    "hours_worked": null,
    "hours_worked_this_week": null
  }
}
```

**Notes:**
- `hours_worked` and `hours_worked_this_week` are calculated from schedules and only shown for non-admin users
- Admin users will have these fields as null

**Error Responses:**
- `401 Unauthorized` - Missing or invalid token
- `404 Not Found` - Profile not found

---

### POST /api/auth/profile/changepassword

Change the current user's password.

**Authentication:** Required

**Request:**
```http
POST /api/auth/profile/changepassword
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "old_password": "string (required)",
  "new_password": "string (required, min 8 characters)"
}
```

**Response (200 OK):**
```json
{
  "message": "Password changed successfully"
}
```

**Error Responses:**
- `400 Bad Request` - Invalid request body
- `401 Unauthorized` - Incorrect old password
- `500 Internal Server Error` - Failed to change password

---

## Roles Endpoints

### GET /api/:org/roles

Get all roles for the organization.

**Authentication:** Required

**Request:**
```http
GET /api/{org_id}/roles
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `org` - Organization UUID

**Response (200 OK):**
```json
{
  "message": "Roles retrieved successfully",
  "data": [
    {
      "organization_id": "uuid",
      "role_id": "admin",
      "min_present": 0,
      "items_per_employee_per_hour": null,
      "producing": false,
      "is_independent": true
    },
    {
      "organization_id": "uuid",
      "role_id": "manager",
      "min_present": 1,
      "items_per_employee_per_hour": null,
      "producing": false,
      "is_independent": true
    },
    {
      "organization_id": "uuid",
      "role_id": "waiter",
      "min_present": 2,
      "items_per_employee_per_hour": 10,
      "producing": true,
      "is_independent": false
    }
  ]
}
```

**Notes:**
- Default roles `admin` and `manager` are created automatically with each organization

**Error Responses:**
- `401 Unauthorized` - Missing or invalid token
- `500 Internal Server Error` - Failed to retrieve roles

---

### POST /api/:org/roles

Create a new role for the organization.

**Authentication:** Required (admin or manager only)

**Request:**
```http
POST /api/{org_id}/roles
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Path Parameters:**
- `org` - Organization UUID

**Request Body:**
```json
{
  "role_id": "string (required, 1-50 characters)",
  "min_present": "integer (required, >= 0)",
  "items_per_employee_per_hour": "integer (required if producing is true)",
  "producing": "boolean (required)",
  "is_independent": "boolean (required for custom roles)"
}
```

**Example Request:**
```json
{
  "role_id": "host",
  "min_present": 1,
  "producing": true,
  "items_per_employee_per_hour": 5,
  "is_independent": false
}
```

**Response (201 Created):**
```json
{
  "message": "Role created successfully",
  "data": {
    "organization_id": "uuid",
    "role_id": "host",
    "min_present": 1,
    "items_per_employee_per_hour": 5,
    "producing": true,
    "is_independent": false
  }
}
```

**Database Constraints:**
- If `producing` is true, `items_per_employee_per_hour` must be >= 0
- If `producing` is false, `items_per_employee_per_hour` must be null
- Custom roles require `is_independent` to be explicitly set

**Error Responses:**
- `400 Bad Request` - Invalid request body or constraint violation
- `401 Unauthorized` - Missing or invalid token
- `403 Forbidden` - Access denied
- `500 Internal Server Error` - Failed to create role (e.g., role already exists)

---

### GET /api/:org/roles/:role

Get details for a specific role.

**Authentication:** Required

**Request:**
```http
GET /api/{org_id}/roles/{role_name}
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `org` - Organization UUID
- `role` - Role name (e.g., "waiter", "manager")

**Response (200 OK):**
```json
{
  "message": "Role retrieved successfully",
  "data": {
    "organization_id": "uuid",
    "role_id": "waiter",
    "min_present": 2,
    "items_per_employee_per_hour": 10,
    "producing": true,
    "is_independent": false
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Missing or invalid token
- `404 Not Found` - Role not found
- `500 Internal Server Error` - Failed to retrieve role

---

### PUT /api/:org/roles/:role

Update an existing role's configuration.

**Authentication:** Required (admin or manager only)

**Request:**
```http
PUT /api/{org_id}/roles/{role_name}
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Path Parameters:**
- `org` - Organization UUID
- `role` - Role name

**Request Body:**
```json
{
  "min_present": "integer (>= 0)",
  "items_per_employee_per_hour": "integer (optional)",
  "producing": "boolean",
  "is_independent": "boolean (optional)"
}
```

**Example Request:**
```json
{
  "min_present": 2,
  "items_per_employee_per_hour": 10,
  "producing": true,
  "is_independent": false
}
```

**Response (200 OK):**
```json
{
  "message": "Role updated successfully",
  "data": {
    "organization_id": "uuid",
    "role_id": "waiter",
    "min_present": 2,
    "items_per_employee_per_hour": 10,
    "producing": true,
    "is_independent": false
  }
}
```

**Error Responses:**
- `400 Bad Request` - Invalid request body
- `401 Unauthorized` - Missing or invalid token
- `403 Forbidden` - Access denied
- `404 Not Found` - Role not found
- `500 Internal Server Error` - Failed to update role

---

### DELETE /api/:org/roles/:role

Delete a role from the organization.

**Authentication:** Required (admin only)

**Request:**
```http
DELETE /api/{org_id}/roles/{role_name}
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `org` - Organization UUID
- `role` - Role name

**Response (200 OK):**
```json
{
  "message": "Role deleted successfully"
}
```

**Important Notes:**
- Cannot delete roles that have users assigned to them (foreign key constraint)
- Cannot delete `admin` or `manager` roles

**Error Responses:**
- `401 Unauthorized` - Missing or invalid token
- `403 Forbidden` - Access denied (not admin)
- `404 Not Found` - Role not found
- `500 Internal Server Error` - Failed to delete role (e.g., users still assigned)

---

## Rules Endpoints

### GET /api/:org/rules

Get the organization's scheduling rules and operating hours.

**Authentication:** Required (admin or manager only)

**Request:**
```http
GET /api/{org_id}/rules
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `org` - Organization UUID

**Response (200 OK):**
```json
{
  "message": "Rules retrieved successfully",
  "data": {
    "organization_id": "uuid",
    "shift_max_hours": 8,
    "shift_min_hours": 4,
    "max_weekly_hours": 40,
    "min_weekly_hours": 20,
    "fixed_shifts": false,
    "number_of_shifts_per_day": null,
    "meet_all_demand": true,
    "min_rest_slots": 2,
    "slot_len_hour": 0.5,
    "min_shift_length_slots": 4,
    "receiving_phone": true,
    "delivery": true,
    "waiting_time": 15,
    "accepting_orders": true,
    "operating_hours": [
      {
        "organization_id": "uuid",
        "weekday": "Sunday",
        "closed": true
      },
      {
        "organization_id": "uuid",
        "weekday": "Monday",
        "opening_time": "09:00:00",
        "closing_time": "22:00:00"
      },
      {
        "organization_id": "uuid",
        "weekday": "Tuesday",
        "opening_time": "09:00:00",
        "closing_time": "22:00:00"
      },
      {
        "organization_id": "uuid",
        "weekday": "Wednesday",
        "opening_time": "09:00:00",
        "closing_time": "22:00:00"
      },
      {
        "organization_id": "uuid",
        "weekday": "Thursday",
        "opening_time": "09:00:00",
        "closing_time": "22:00:00"
      },
      {
        "organization_id": "uuid",
        "weekday": "Friday",
        "opening_time": "09:00:00",
        "closing_time": "22:00:00"
      },
      {
        "organization_id": "uuid",
        "weekday": "Saturday",
        "opening_time": "09:00:00",
        "closing_time": "22:00:00"
      }
    ]
  }
}
```

**Operating Hours Notes:**
- All 7 days of the week are always returned (Sunday through Saturday)
- Days with operating hours will have `opening_time` and `closing_time` fields
- Days that are closed will have `closed: true` and omit the time fields
- The `closed` field is omitted when the business is open on that day

**Error Responses:**
- `401 Unauthorized` - Missing or invalid token
- `403 Forbidden` - Access denied
- `500 Internal Server Error` - Failed to retrieve rules

---

### POST /api/:org/rules

Create or update the organization's scheduling rules and operating hours.

**Authentication:** Required (admin only)

**Request:**
```http
POST /api/{org_id}/rules
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Path Parameters:**
- `org` - Organization UUID

**Request Body:**
```json
{
  "shift_max_hours": "integer (required)",
  "shift_min_hours": "integer (required)",
  "max_weekly_hours": "integer (required)",
  "min_weekly_hours": "integer (required)",
  "fixed_shifts": "boolean (required)",
  "number_of_shifts_per_day": "integer (required if fixed_shifts is true)",
  "meet_all_demand": "boolean (required)",
  "min_rest_slots": "integer (required)",
  "slot_len_hour": "decimal (required)",
  "min_shift_length_slots": "integer (required)",
  "receiving_phone": "boolean (optional, defaults to true)",
  "delivery": "boolean (optional, defaults to true)",
  "waiting_time": "integer (required - minutes)",
  "accepting_orders": "boolean (optional, defaults to true)",
  "operating_hours": [
    {
      "weekday": "string (required - Sunday|Monday|Tuesday|Wednesday|Thursday|Friday|Saturday)",
      "opening_time": "string (required - HH:MM format)",
      "closing_time": "string (required - HH:MM format)"
    }
  ]
}
```

**Example Request:**
```json
{
  "shift_max_hours": 8,
  "shift_min_hours": 4,
  "max_weekly_hours": 40,
  "min_weekly_hours": 20,
  "fixed_shifts": false,
  "meet_all_demand": true,
  "min_rest_slots": 2,
  "slot_len_hour": 0.5,
  "min_shift_length_slots": 4,
  "receiving_phone": true,
  "delivery": true,
  "waiting_time": 15,
  "accepting_orders": true,
  "operating_hours": [
    {
      "weekday": "Monday",
      "opening_time": "09:00",
      "closing_time": "22:00"
    },
    {
      "weekday": "Tuesday",
      "opening_time": "09:00",
      "closing_time": "22:00"
    }
  ]
}
```

**Response (200 OK):**
```json
{
  "message": "Rules saved successfully",
  "data": {
    "organization_id": "uuid",
    "shift_max_hours": 8,
    "shift_min_hours": 4,
    "max_weekly_hours": 40,
    "min_weekly_hours": 20,
    "fixed_shifts": false,
    "number_of_shifts_per_day": null,
    "meet_all_demand": true,
    "min_rest_slots": 2,
    "slot_len_hour": 0.5,
    "min_shift_length_slots": 4,
    "receiving_phone": true,
    "delivery": true,
    "waiting_time": 15,
    "accepting_orders": true,
    "operating_hours": [...]
  }
}
```

**Error Responses:**
- `400 Bad Request` - Invalid request body
- `401 Unauthorized` - Missing or invalid token
- `403 Forbidden` - Access denied (not admin)
- `500 Internal Server Error` - Failed to save rules

---

## Preferences Endpoints

### GET /api/:org/preferences

Get the current user's preferences including day preferences, user roles, and scheduling constraints.

**Authentication:** Required

**Request:**
```http
GET /api/{org_id}/preferences
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `org` - Organization UUID

**Response (200 OK):**
```json
{
  "message": "Preferences retrieved successfully",
  "data": {
    "day_preferences": [
      {
        "employee_id": "uuid",
        "day": "Monday",
        "preferred_start_time": "09:00:00",
        "preferred_end_time": "17:00:00",
        "available_start_time": "08:00:00",
        "available_end_time": "18:00:00"
      },
      {
        "employee_id": "uuid",
        "day": "Tuesday",
        "preferred_start_time": "10:00:00",
        "preferred_end_time": "16:00:00",
        "available_start_time": null,
        "available_end_time": null
      }
    ],
    "user_roles": ["waiter"],
    "max_hours_per_week": 40,
    "preferred_hours_per_week": 35,
    "max_consec_slots": 8,
    "on_call": true
  }
}
```

**Notes:**
- `day_preferences` contains availability for each day of the week
- `user_roles` are the roles the employee can perform
- Times are returned in HH:MM:SS format

**Error Responses:**
- `401 Unauthorized` - Missing or invalid token
- `403 Forbidden` - Access denied (wrong organization)
- `500 Internal Server Error` - Failed to retrieve preferences

---

### POST /api/:org/preferences

Update the current user's preferences.

**Authentication:** Required

**Request:**
```http
POST /api/{org_id}/preferences
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Path Parameters:**
- `org` - Organization UUID

**Request Body:**
```json
{
  "preferences": [
    {
      "day": "string (required - Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)",
      "preferred_start_time": "string (required - HH:MM format)",
      "preferred_end_time": "string (required - HH:MM format)",
      "available_start_time": "string (optional - HH:MM format)",
      "available_end_time": "string (optional - HH:MM format)"
    }
  ],
  "user_roles": ["string (role names)"],
  "max_hours_per_week": "integer (optional)",
  "preferred_hours_per_week": "integer (optional)",
  "max_consec_slots": "integer (optional)",
  "on_call": "boolean (optional)"
}
```

**Example Request:**
```json
{
  "preferences": [
    {
      "day": "Monday",
      "preferred_start_time": "09:00",
      "preferred_end_time": "17:00",
      "available_start_time": "08:00",
      "available_end_time": "18:00"
    },
    {
      "day": "Tuesday",
      "preferred_start_time": "10:00",
      "preferred_end_time": "16:00"
    }
  ],
  "user_roles": ["waiter"],
  "max_hours_per_week": 40,
  "preferred_hours_per_week": 35,
  "max_consec_slots": 8,
  "on_call" : true,
}
```

**Response (200 OK):**
```json
{
  "message": "Preferences saved successfully"
}
```

**Validation:**
- `user_roles` must be valid roles that exist in the organization
- Invalid roles will be rejected with an error

**Error Responses:**
- `400 Bad Request` - Invalid request body or invalid roles
- `401 Unauthorized` - Missing or invalid token
- `403 Forbidden` - Access denied
- `500 Internal Server Error` - Failed to save preferences

---

## Staffing Endpoints

### GET /api/:org/staffing

Get a staffing summary for the organization.

**Authentication:** Required (admin or manager only)

**Request:**
```http
GET /api/{org_id}/staffing
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `org` - Organization UUID

**Response (200 OK):**
```json
{
  "message": "Staffing summary retrieved successfully",
  "data": {
    "total_employees": 2,
    "by_role": {
      "admin": 1,
      "waiter": 1
    },
    "employees": [
      {
        "id": "uuid",
        "full_name": "Admin User",
        "email": "admin@testorg.com",
        "user_role": "admin",
        "organization_id": "uuid",
        "max_hours_per_week": 40,
        "preferred_hours_per_week": 35,
        "max_consec_slots": 8,
        "on_call": false,
        "created_at": "2026-02-06T09:47:57.291686Z",
        "updated_at": "2026-02-06T09:49:40.762669Z"
      }
    ]
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Missing or invalid token
- `403 Forbidden` - Access denied
- `500 Internal Server Error` - Failed to retrieve staffing data

---

### POST /api/:org/staffing

Delegate (invite) a new user to the organization.

**Authentication:** Required (admin or manager only)

**Request:**
```http
POST /api/{org_id}/staffing
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Path Parameters:**
- `org` - Organization UUID

**Request Body:**
```json
{
  "full_name": "string (required)",
  "email": "string (required, valid email)",
  "role": "string (required - employee|manager)",
  "salary_per_hour": "number (required)",
  "max_hours_per_week": "integer (optional)",
  "preferred_hours_per_week": "integer (optional)",
  "max_consec_slots": "integer (optional)",
  "on_call" : "boolean (optional,default=false)"
}
```

**Example Request:**
```json
{
  "full_name": "Employee One",
  "email": "employee1@testorg.com",
  "role": "employee",
  "salary_per_hour": 15.50
}
```

**Response (201 Created):**
```json
{
  "message": "User delegated successfully. Email sent.",
  "user_id": "uuid"
}
```

**Allowed Roles:**
| Role | Description |
|------|-------------|
| `employee` | Regular employee with staff permissions |
| `manager` | Manager with elevated permissions |

**Notes:**
- The `role` must be either `employee` or `manager`
- An email is sent to the delegated user with login credentials
- A random password is generated for the new user

**Error Responses:**
- `400 Bad Request` - Invalid request body or invalid role
- `401 Unauthorized` - Missing or invalid token
- `403 Forbidden` - Access denied
- `500 Internal Server Error` - Failed to delegate user

---

### GET /api/:org/staffing/employees

Get all employees in the organization.

**Authentication:** Required (admin or manager only)

**Request:**
```http
GET /api/{org_id}/staffing/employees
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `org` - Organization UUID

**Response (200 OK):**
```json
{
  "total": 2,
  "employees": [
    {
      "id": "uuid",
      "full_name": "Employee One",
      "email": "employee1@testorg.com",
      "user_role": "waiter",
      "salary_per_hour": 15.5,
      "organization_id": "uuid",
      "created_at": "2026-02-06T09:50:57.461744Z",
      "updated_at": "2026-02-06T09:50:57.461744Z"
    },
    {
      "id": "uuid",
      "full_name": "Admin User",
      "email": "admin@testorg.com",
      "user_role": "admin",
      "organization_id": "uuid",
      "max_hours_per_week": 40,
      "preferred_hours_per_week": 35,
      "max_consec_slots": 8,
      "on_call" : false,
      "created_at": "2026-02-06T09:47:57.291686Z",
      "updated_at": "2026-02-06T09:49:40.762669Z"
    }
  ]
}
```

**Error Responses:**
- `401 Unauthorized` - Missing or invalid token
- `403 Forbidden` - Access denied
- `500 Internal Server Error` - Failed to retrieve employees

---

### GET /api/:org/staffing/employees/:id

Get details for a specific employee.

**Authentication:** Required (admin or manager only)

**Request:**
```http
GET /api/{org_id}/staffing/employees/{employee_id}
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `org` - Organization UUID
- `id` - Employee UUID

**Response (200 OK):**
```json
{
  "message": "Employee details retrieved successfully",
  "data": {
    "id": "uuid",
    "full_name": "Employee One",
    "email": "employee1@testorg.com",
    "user_role": "waiter",
    "salary_per_hour": 15.5,
    "organization_id": "uuid",
    "created_at": "2026-02-06T09:50:57.461744Z",
    "updated_at": "2026-02-06T09:50:57.461744Z"
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Missing or invalid token
- `403 Forbidden` - Access denied
- `404 Not Found` - Employee not found
- `500 Internal Server Error` - Failed to retrieve employee

---

### GET /api/:org/staffing/employees/:id/requests

Get all requests (time-off, shift changes, etc.) for a specific employee.

**Authentication:** Required (admin or manager only)

**Request:**
```http
GET /api/{org_id}/staffing/employees/{employee_id}/requests
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `org` - Organization UUID
- `id` - Employee UUID

**Response (200 OK):**
```json
{
  "message": "Employee requests retrieved successfully",
  "total": 0,
  "requests": []
}
```

**Response with Requests:**
```json
{
  "message": "Employee requests retrieved successfully",
  "total": 1,
  "requests": [
    {
      "id": "uuid",
      "employee_id": "uuid",
      "request_type": "time_off",
      "status": "pending",
      "start_date": "2026-02-10",
      "end_date": "2026-02-12",
      "reason": "Vacation",
      "created_at": "2026-02-06T10:00:00Z"
    }
  ]
}
```

**Error Responses:**
- `401 Unauthorized` - Missing or invalid token
- `403 Forbidden` - Access denied
- `500 Internal Server Error` - Failed to retrieve requests

---

### POST /api/:org/staffing/employees/:id/requests/approve

Approve a pending request from an employee.

**Authentication:** Required (admin or manager only)

**Request:**
```http
POST /api/{org_id}/staffing/employees/{employee_id}/requests/approve
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Path Parameters:**
- `org` - Organization UUID
- `id` - Employee UUID

**Request Body:**
```json
{
  "request_id": "uuid (required)"
}
```

**Response (200 OK):**
```json
{
  "message": "Request approved successfully"
}
```

**Error Responses:**
- `400 Bad Request` - Invalid request body
- `401 Unauthorized` - Missing or invalid token
- `403 Forbidden` - Access denied
- `404 Not Found` - Request not found
- `500 Internal Server Error` - Failed to approve request

---

### POST /api/:org/staffing/employees/:id/requests/decline

Decline a pending request from an employee.

**Authentication:** Required (admin or manager only)

**Request:**
```http
POST /api/{org_id}/staffing/employees/{employee_id}/requests/decline
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Path Parameters:**
- `org` - Organization UUID
- `id` - Employee UUID

**Request Body:**
```json
{
  "request_id": "uuid (required)",
  "reason": "string (optional - reason for declining)"
}
```

**Response (200 OK):**
```json
{
  "message": "Request declined successfully"
}
```

**Error Responses:**
- `400 Bad Request` - Invalid request body
- `401 Unauthorized` - Missing or invalid token
- `403 Forbidden` - Access denied
- `404 Not Found` - Request not found
- `500 Internal Server Error` - Failed to decline request

---

### DELETE /api/:org/staffing/employees/:id/layoff

Lay off (deactivate) an employee from the organization.

**Authentication:** Required (admin only)

**Request:**
```http
DELETE /api/{org_id}/staffing/employees/{employee_id}/layoff
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `org` - Organization UUID
- `id` - Employee UUID

**Response (200 OK):**
```json
{
  "message": "Employee laid off successfully",
  "employee_id": "uuid"
}
```

**Error Responses:**
- `401 Unauthorized` - Missing or invalid token
- `403 Forbidden` - Access denied (not admin)
- `404 Not Found` - Employee not found
- `500 Internal Server Error` - Failed to lay off employee

---

## Insights Endpoints

### GET /api/:org/insights

Get dashboard insights and statistics for the organization. Returns different insights based on the user's role.

**Authentication:** Required

**Request:**
```http
GET /api/{org_id}/insights
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `org` - Organization UUID

**Response (200 OK) - Admin View:**
```json
{
  "message": "Insights retrieved successfully",
  "data": [
    {
      "title": "Number of Employees",
      "statistic": "5"
    },
    {
      "title": "Number of waiters",
      "statistic": "3"
    },
    {
      "title": "Average Employee Salary (per hour)",
      "statistic": "$15.50"
    },
    {
      "title": "Average waiter Salary (per hour)",
      "statistic": "$14.00"
    },
    {
      "title": "Number of Tables",
      "statistic": "10"
    },
    {
      "title": "Max Table Capacity",
      "statistic": "40 people"
    },
    {
      "title": "Current People at Tables",
      "statistic": "15 people"
    },
    {
      "title": "Average Orders per Day",
      "statistic": "25.5"
    },
    {
      "title": "Orders Served Today",
      "statistic": "18"
    },
    {
      "title": "Total Revenue",
      "statistic": "$15000.00"
    }
  ]
}
```

**Admin Insights Include:**
- Number of Employees (excluding admins)
- Number of employees per role
- Average Employee Salary
- Average Salary per role
- Number of Tables
- Max Table Capacity
- Current People at Tables
- Average Orders per Day
- Orders Served Today
- Number of orders per type (dine in, delivery, takeaway)
- Total Revenue
- Number of employees per role in current shift
- Most Selling items (top 5)

**Manager Insights Include:**
- All admin insights plus:
- Manager's own salary
- Number of deliveries today

**Employee Insights Include:**
- Employee's salary
- Employee's role
- Number of tables
- Manager currently in shift
- Table capacity info
- Orders served today
- Employees per role in current shift
- Orders per type today

**Error Responses:**
- `401 Unauthorized` - Missing or invalid token
- `403 Forbidden` - Access denied (wrong organization)
- `500 Internal Server Error` - Failed to retrieve insights

---

## Organization Endpoints

### GET /api/:org

Get the organization's profile and details.

**Authentication:** Required

**Request:**
```http
GET /api/{org_id}
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `org` - Organization UUID

**Response (200 OK):**
```json
{
  "message": "Organization profile retrieved successfully",
  "data": {
    "name": "Tech Solutions Inc.",
    "address": "123 Business Street, Cairo",
    "email": "contact@techsolutions.com",
    "location": {
      "latitude": 30.0444,
      "longitude": 31.2357
    },
    "hex1": "#3B82F6",
    "hex2": "#1E40AF",
    "hex3": "#DBEAFE",
    "rating": 4.5,
    "accepting_orders": true,
    "number_of_employees": 25
  }
}
```

**Notes:**
- `number_of_employees` excludes admin users
- `rating` may be null if no ratings exist

**Error Responses:**
- `401 Unauthorized` - Missing or invalid token
- `500 Internal Server Error` - Failed to retrieve organization profile

---

### POST /api/:org/request

Submit a calloff, holiday, or resignation request. Employees and managers can submit requests to their organization.

**Authentication:** Required (employees and managers only, admins cannot submit requests)

**Request:**
```http
POST /api/{org_id}/request
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Path Parameters:**
- `org` - Organization UUID

**Request Body:**
```json
{
  "type": "string (required - calloff|holiday|resign)",
  "message": "string (required)"
}
```

**Example Request:**
```json
{
  "type": "calloff",
  "message": "I am feeling unwell and need to take the day off."
}
```

**Response (201 Created):**
```json
{
  "message": "Request submitted successfully",
  "request_id": "uuid"
}
```

**Request Types:**
| Type | Description |
|------|-------------|
| `calloff` | Request time off for illness or emergency |
| `holiday` | Request scheduled time off / vacation |
| `resign` | Submit resignation notice |

**Notes:**
- Upon submission, the employee receives a confirmation email
- All managers and admins in the organization are notified via email
- Admins cannot submit requests (returns 403 Forbidden)

**Error Responses:**
- `400 Bad Request` - Invalid request body or invalid type value
- `401 Unauthorized` - Missing or invalid token
- `403 Forbidden` - Admins cannot submit requests
- `500 Internal Server Error` - Failed to submit request

---

## Orders Endpoints

### GET /api/:org/orders

Get order insights and analytics for the organization.

**Authentication:** Required (admin or manager only)

**Request:**
```http
GET /api/{org_id}/orders
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `org` - Organization UUID

**Response (200 OK):**
```json
{
  "message": "Order insights retrieved successfully",
  "data": [
    {
      "title": "Total Orders",
      "statistic": "150"
    },
    {
      "title": "Average Order Value",
      "statistic": "$45.00"
    }
  ]
}
```

**Error Responses:**
- `401 Unauthorized` - Missing or invalid token
- `403 Forbidden` - Access denied (not admin/manager)
- `500 Internal Server Error` - Failed to retrieve order insights

---

### GET /api/:org/orders/all

Get all orders for the organization, including their order items and delivery status.

**Authentication:** Required (admin or manager only)

**Request:**
```http
GET /api/{org_id}/orders/all
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `org` - Organization UUID

**Response (200 OK):**
```json
{
  "message": "Orders retrieved successfully",
  "data": [
    {
      "order_id": "uuid",
      "user_id": "uuid",
      "organization_id": "uuid",
      "create_time": "2026-02-06T10:30:00Z",
      "order_type": "dine_in",
      "order_status": "completed",
      "total_amount": 45.99,
      "discount_amount": 5.00,
      "rating": 4.5,
      "order_items": [
        {
          "item_id": "uuid",
          "quantity": 2,
          "total_price": 30
        }
      ],
      "delivery_status": null
    },
    {
      "order_id": "uuid",
      "user_id": "uuid",
      "organization_id": "uuid",
      "create_time": "2026-02-06T12:00:00Z",
      "order_type": "delivery",
      "order_status": "completed",
      "total_amount": 60.00,
      "discount_amount": 0.00,
      "rating": 5.0,
      "order_items": [
        {
          "item_id": "uuid",
          "quantity": 1,
          "total_price": 60
        }
      ],
      "delivery_status": {
        "driver_id": "uuid",
        "location": {
          "latitude": 30.0444,
          "longitude": 31.2357
        },
        "out_for_delivery_time": "2026-02-06T12:15:00Z",
        "delivered_time": "2026-02-06T12:45:00Z",
        "status": "delivered"
      }
    }
  ]
}
```

**Notes:**
- Each order includes its associated `order_items` (from the order_items junction table)
- Orders of type `delivery` include a `delivery_status` object; otherwise it is `null`

**Error Responses:**
- `401 Unauthorized` - Missing or invalid token
- `403 Forbidden` - Access denied (not admin/manager)
- `500 Internal Server Error` - Failed to retrieve orders

---

### GET /api/:org/orders/week

Get all orders from the last 7 days for the organization.

**Authentication:** Required (admin or manager only)

**Request:**
```http
GET /api/{org_id}/orders/week
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `org` - Organization UUID

**Response (200 OK):**
```json
{
  "message": "Orders retrieved successfully",
  "data": [
    {
      "order_id": "uuid",
      "user_id": "uuid",
      "organization_id": "uuid",
      "create_time": "2026-02-03T14:00:00Z",
      "order_type": "takeaway",
      "order_status": "completed",
      "total_amount": 25.00,
      "discount_amount": 0.00,
      "rating": null,
      "order_items": [],
      "delivery_status": null
    }
  ]
}
```

**Error Responses:**
- `401 Unauthorized` - Missing or invalid token
- `403 Forbidden` - Access denied (not admin/manager)
- `500 Internal Server Error` - Failed to retrieve orders

---

### GET /api/:org/orders/today

Get all orders from today for the organization.

**Authentication:** Required (admin or manager only)

**Request:**
```http
GET /api/{org_id}/orders/today
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `org` - Organization UUID

**Response (200 OK):**
```json
{
  "message": "Orders retrieved successfully",
  "data": [
    {
      "order_id": "uuid",
      "user_id": "uuid",
      "organization_id": "uuid",
      "create_time": "2026-02-06T09:00:00Z",
      "order_type": "dine_in",
      "order_status": "in_progress",
      "total_amount": 35.50,
      "discount_amount": 0.00,
      "rating": null,
      "order_items": [
        {
          "item_id": "uuid",
          "quantity": 3,
          "total_price": 35
        }
      ],
      "delivery_status": null
    }
  ]
}
```

**Error Responses:**
- `401 Unauthorized` - Missing or invalid token
- `403 Forbidden` - Access denied (not admin/manager)
- `500 Internal Server Error` - Failed to retrieve orders

---

### POST /api/:org/orders/upload/orders

Upload a CSV file containing past orders data.

**Authentication:** Required (admin or manager only)

**Request:**
```http
POST /api/{org_id}/orders/upload/orders
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
Content-Encoding: gzip
```

**Path Parameters:**
- `org` - Organization UUID

**Form Data:**
- `file` - CSV file with orders data

**Required CSV Columns:**
| Column | Type | Description |
|--------|------|-------------|
| `order_id` | UUID | Unique identifier for the order |
| `user_id` | UUID | The employee who handled the order |
| `create_time` | Timestamp | Order creation time (RFC3339 or `YYYY-MM-DD HH:MM:SS`) |
| `order_type` | String | Type of order (e.g., `dine_in`, `delivery`, `takeaway`) |
| `order_status` | String | Status of the order (e.g., `completed`, `cancelled`) |
| `total_amount` | Float | Total amount of the order |
| `discount_amount` | Float | Discount applied to the order |

**Optional CSV Columns:**
| Column | Type | Description |
|--------|------|-------------|
| `rating` | Float | Customer rating for the order |

**Response (200 OK):**
```json
{
  "message": "Orders CSV uploaded successfully",
  "total_rows": 100,
  "success_count": 98,
  "error_count": 2
}
```

**Error Responses:**
- `400 Bad Request` - Missing file, empty CSV, invalid format, or missing required column
- `401 Unauthorized` - Missing or invalid token
- `403 Forbidden` - Access denied (not admin/manager)

---

### POST /api/:org/orders/upload/items

Upload a CSV file containing order items data (links items to orders).

**Authentication:** Required (admin or manager only)

**Request:**
```http
POST /api/{org_id}/orders/upload/items
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
Content-Encoding: gzip
```

**Path Parameters:**
- `org` - Organization UUID

**Form Data:**
- `file` - CSV file with order items data

**Required CSV Columns:**
| Column | Type | Description |
|--------|------|-------------|
| `order_id` | UUID | The order to link the item to |
| `item_id` | UUID | The item from the items catalog |
| `quantity` | Integer | Quantity of the item in the order |
| `total_price` | Integer | Total price for this line item |

**Response (200 OK):**
```json
{
  "message": "Order items CSV uploaded successfully",
  "total_rows": 250,
  "success_count": 248,
  "error_count": 2
}
```

**Prerequisites:**
- At least one order must exist (upload orders CSV first)
- At least one item must exist (upload items CSV first)

**Notes:**
- If an order-item pair already exists, the quantities and prices are added together (upsert behavior)

**Error Responses:**
- `400 Bad Request` - Missing file, empty CSV, invalid format, missing required column, or prerequisites not met
- `401 Unauthorized` - Missing or invalid token
- `403 Forbidden` - Access denied (not admin/manager)
- `500 Internal Server Error` - Failed to verify existing orders or items

---

## Deliveries Endpoints

### GET /api/:org/deliveries

Get delivery insights and analytics for the organization.

**Authentication:** Required (admin or manager only)

**Request:**
```http
GET /api/{org_id}/deliveries
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `org` - Organization UUID

**Response (200 OK):**
```json
{
  "message": "Delivery insights retrieved successfully",
  "data": [
    {
      "title": "Total Deliveries",
      "statistic": "75"
    },
    {
      "title": "Average Delivery Time",
      "statistic": "30 min"
    }
  ]
}
```

**Error Responses:**
- `401 Unauthorized` - Missing or invalid token
- `403 Forbidden` - Access denied (not admin/manager)
- `500 Internal Server Error` - Failed to retrieve delivery insights

---

### GET /api/:org/deliveries/all

Get all deliveries for the organization.

**Authentication:** Required (admin or manager only)

**Request:**
```http
GET /api/{org_id}/deliveries/all
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `org` - Organization UUID

**Response (200 OK):**
```json
{
  "message": "Deliveries retrieved successfully",
  "data": [
    {
      "order_id": "uuid",
      "driver_id": "uuid",
      "location": {
        "latitude": 30.0444,
        "longitude": 31.2357
      },
      "out_for_delivery_time": "2026-02-06T12:15:00Z",
      "delivered_time": "2026-02-06T12:45:00Z",
      "status": "delivered"
    }
  ]
}
```

**Error Responses:**
- `401 Unauthorized` - Missing or invalid token
- `403 Forbidden` - Access denied (not admin/manager)
- `500 Internal Server Error` - Failed to retrieve deliveries

---

### GET /api/:org/deliveries/week

Get all deliveries from the last 7 days for the organization.

**Authentication:** Required (admin or manager only)

**Request:**
```http
GET /api/{org_id}/deliveries/week
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `org` - Organization UUID

**Response (200 OK):**
```json
{
  "message": "Deliveries retrieved successfully",
  "data": [
    {
      "order_id": "uuid",
      "driver_id": "uuid",
      "location": {
        "latitude": 30.0444,
        "longitude": 31.2357
      },
      "out_for_delivery_time": "2026-02-03T18:00:00Z",
      "delivered_time": "2026-02-03T18:30:00Z",
      "status": "delivered"
    }
  ]
}
```

**Error Responses:**
- `401 Unauthorized` - Missing or invalid token
- `403 Forbidden` - Access denied (not admin/manager)

---

### GET /api/:org/deliveries/today

Get all deliveries from today for the organization.

**Authentication:** Required (admin or manager only)

**Request:**
```http
GET /api/{org_id}/deliveries/today
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `org` - Organization UUID

**Response (200 OK):**
```json
{
  "message": "Deliveries retrieved successfully",
  "data": [
    {
      "order_id": "uuid",
      "driver_id": "uuid",
      "location": {
        "latitude": 30.0444,
        "longitude": 31.2357
      },
      "out_for_delivery_time": "2026-02-07T12:15:00Z",
      "delivered_time": "2026-02-07T12:45:00Z",
      "status": "delivered"
    }
  ]
}
```

**Error Responses:**
- `401 Unauthorized` - Missing or invalid token
- `403 Forbidden` - Access denied (not admin/manager)
- `500 Internal Server Error` - Failed to retrieve deliveries

---

### POST /api/:org/deliveries/upload

Upload a CSV file containing past deliveries data.

**Authentication:** Required (admin or manager only)

**Request:**
```http
POST /api/{org_id}/deliveries/upload
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
Content-Encoding: gzip
```

**Path Parameters:**
- `org` - Organization UUID

**Form Data:**
- `file` - CSV file with deliveries data

**Required CSV Columns:**
| Column | Type | Description |
|--------|------|-------------|
| `order_id` | UUID | The order this delivery belongs to |
| `driver_id` | UUID | The driver assigned to the delivery |
| `out_for_delivery_time` | Timestamp | Time the order went out for delivery (RFC3339 or `YYYY-MM-DD HH:MM:SS`) |
| `status` | String | Delivery status (e.g., `delivered`, `in_transit`, `failed`) |

**Optional CSV Columns:**
| Column | Type | Description |
|--------|------|-------------|
| `delivered_time` | Timestamp | Time the order was delivered |
| `delivery_latitude` | Float | Delivery destination latitude |
| `delivery_longitude` | Float | Delivery destination longitude |

**Response (200 OK):**
```json
{
  "message": "Deliveries CSV uploaded successfully",
  "total_rows": 50,
  "success_count": 49,
  "error_count": 1
}
```

**Prerequisites:**
- At least one order must exist (upload orders CSV first)

**Error Responses:**
- `400 Bad Request` - Missing file, empty CSV, invalid format, missing required column, or prerequisites not met
- `401 Unauthorized` - Missing or invalid token
- `403 Forbidden` - Access denied (not admin/manager)
- `500 Internal Server Error` - Failed to verify existing orders

---

## Items Endpoints

### GET /api/:org/items

Get item insights and analytics for the organization.

**Authentication:** Required (admin or manager only)

**Request:**
```http
GET /api/{org_id}/items
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `org` - Organization UUID

**Response (200 OK):**
```json
{
  "message": "Item insights retrieved successfully",
  "data": [
    {
      "title": "Total Items",
      "statistic": "25"
    },
    {
      "title": "Most Popular Item",
      "statistic": "Margherita Pizza"
    }
  ]
}
```

**Error Responses:**
- `401 Unauthorized` - Missing or invalid token
- `403 Forbidden` - Access denied (not admin/manager)
- `500 Internal Server Error` - Failed to retrieve item insights

---

### GET /api/:org/items/all

Get all items in the organization's catalog.

**Authentication:** Required (admin or manager only)

**Request:**
```http
GET /api/{org_id}/items/all
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `org` - Organization UUID

**Response (200 OK):**
```json
{
  "message": "Items retrieved successfully",
  "data": [
    {
      "item_id": "uuid",
      "name": "Margherita Pizza",
      "needed_employees": 2,
      "price": 12.99
    },
    {
      "item_id": "uuid",
      "name": "Caesar Salad",
      "needed_employees": 1,
      "price": 8.50
    }
  ]
}
```

**Error Responses:**
- `401 Unauthorized` - Missing or invalid token
- `403 Forbidden` - Access denied (not admin/manager)
- `500 Internal Server Error` - Failed to retrieve items

---

### POST /api/:org/items/upload

Upload a CSV file containing items catalog data.

**Authentication:** Required (admin or manager only)

**Request:**
```http
POST /api/{org_id}/items/upload
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
Content-Encoding: gzip
```

**Path Parameters:**
- `org` - Organization UUID

**Form Data:**
- `file` - CSV file with items data

**Required CSV Columns:**
| Column | Type | Description |
|--------|------|-------------|
| `item_id` | UUID | Unique identifier for the item |
| `name` | String | Name of the item |
| `needed_employees` | Integer | Number of employees needed to prepare the item |
| `price` | Float | Price of the item in decimal format |

**Response (200 OK):**
```json
{
  "message": "Items CSV uploaded successfully",
  "total_rows": 25,
  "success_count": 25,
  "error_count": 0
}
```

**Notes:**
- Duplicate item names within the same organization are not allowed

**Error Responses:**
- `400 Bad Request` - Missing file, empty CSV, invalid format, or missing required column
- `401 Unauthorized` - Missing or invalid token
- `403 Forbidden` - Access denied (not admin/manager)
- `500 Internal Server Error` - Failed to store item (e.g., duplicate name)

---

## Error Response Format

All error responses follow this format:

```json
{
  "error": "Error message describing what went wrong"
}
```

Or for authentication errors:

```json
{
  "message": "Error message"
}
```

## Common HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | OK - Request successful |
| 201 | Created - Resource created successfully |
| 400 | Bad Request - Invalid request body or parameters |
| 401 | Unauthorized - Missing or invalid authentication |
| 403 | Forbidden - Access denied (insufficient permissions) |
| 404 | Not Found - Resource not found |
| 500 | Internal Server Error - Server-side error |

---

## Campaigns Endpoints

Marketing campaigns endpoints allow admins and managers to manage promotional campaigns and analyze campaign performance. All campaign endpoints require authentication and admin or manager roles.

### GET /api/:org/campaigns

Get campaign insights and analytics for the organization.

**Authentication:** Required (Admin/Manager only)

**Path Parameters:**
- `org` (string, required): Organization ID (UUID)

**Request:**
```http
GET /api/:org/campaigns
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "message": "Campaign insights retrieved successfully",
  "data": [
    {
      "title": "Total Campaigns",
      "statistic": "15"
    },
    {
      "title": "Longest Campaign (days)",
      "statistic": "45.2"
    },
    {
      "title": "Biggest Discount (%)",
      "statistic": "30.00%"
    },
    {
      "title": "Most Featured Item",
      "statistic": "Burger Deluxe"
    }
  ]
}
```

**Campaign Insights:**
- **Total Campaigns**: Count of all campaigns created
- **Longest Campaign**: Duration in days of the longest-running campaign
- **Biggest Discount**: Highest discount percentage ever offered
- **Most Featured Item**: Item that appears most frequently across campaigns

**Error Responses:**
- **401 Unauthorized**: Missing or invalid authentication token
- **403 Forbidden**: User is not an admin or manager
- **500 Internal Server Error**: Server error retrieving insights

---

### POST /api/:org/campaigns/upload

Upload marketing campaigns data from a CSV file.

**Authentication:** Required (Admin/Manager only)

**Path Parameters:**
- `org` (string, required): Organization ID (UUID)

**Request:**
```http
POST /api/:org/campaigns/upload
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
Content-Encoding: gzip

file: <campaigns.csv>
```

**CSV Format:**

Required columns (order-independent):

| Column | Type | Description | Required | Example |
|--------|------|-------------|----------|---------|
| id | UUID | Campaign unique identifier | Yes | `550e8400-e29b-41d4-a716-446655440000` |
| name | String | Campaign name | Yes | `Summer Sale 2024` |
| status | String | Campaign status (active/inactive) | Yes | `active` |
| start_time | Timestamp | Campaign start date/time | Yes | `2024-06-01T00:00:00Z` |
| end_time | Timestamp | Campaign end date/time | Yes | `2024-08-31T23:59:59Z` |
| discount_percent | Float | Discount percentage (optional) | No | `15.50` |

**Timestamp Formats Supported:**
- RFC3339: `2024-06-01T00:00:00Z`
- DateTime: `2024-06-01 00:00:00`

**Status Values:**
- `active`: Campaign is currently active
- `inactive`: Campaign is inactive/ended

**Example CSV:**
```csv
id,name,status,start_time,end_time,discount_percent
550e8400-e29b-41d4-a716-446655440000,Summer Sale,active,2024-06-01T00:00:00Z,2024-08-31T23:59:59Z,15.00
660e8400-e29b-41d4-a716-446655440001,Holiday Promo,inactive,2023-12-01T00:00:00Z,2023-12-31T23:59:59Z,25.00
```

**Response (200 OK):**
```json
{
  "message": "Campaigns CSV uploaded successfully",
  "total_rows": 100,
  "success_count": 98,
  "error_count": 2
}
```

**Notes:**
- Campaigns must be uploaded before uploading campaign items
- Invalid rows are skipped and counted in `error_count`
- The handler validates UUID formats and timestamp formats
- Discount percentage is optional

**Error Responses:**
- **400 Bad Request**: Missing required columns, invalid CSV format, or empty file
- **401 Unauthorized**: Missing or invalid authentication token
- **403 Forbidden**: User is not an admin or manager
- **500 Internal Server Error**: Server error during upload

---

### POST /api/:org/campaigns/upload/items

Upload campaign-item associations from a CSV file. This endpoint associates items with existing campaigns.

**Authentication:** Required (Admin/Manager only)

**Prerequisites:** 
- Campaigns must already exist (uploaded via `/campaigns/upload`)
- Items must already exist (uploaded via `/items/upload`)

**Path Parameters:**
- `org` (string, required): Organization ID (UUID)

**Request:**
```http
POST /api/:org/campaigns/upload/items
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
Content-Encoding: gzip

file: <campaign_items.csv>
```

**CSV Format:**

Required columns (order-independent):

| Column | Type | Description | Required | Example |
|--------|------|-------------|----------|---------|
| campaign_id | UUID | Campaign identifier | Yes | `550e8400-e29b-41d4-a716-446655440000` |
| item_id | UUID | Item identifier | Yes | `770e8400-e29b-41d4-a716-446655440001` |

**Example CSV:**
```csv
campaign_id,item_id
550e8400-e29b-41d4-a716-446655440000,770e8400-e29b-41d4-a716-446655440001
550e8400-e29b-41d4-a716-446655440000,880e8400-e29b-41d4-a716-446655440002
660e8400-e29b-41d4-a716-446655440001,770e8400-e29b-41d4-a716-446655440001
```

**Response (200 OK):**
```json
{
  "message": "Campaign items CSV uploaded successfully",
  "total_rows": 50,
  "success_count": 48,
  "error_count": 2
}
```

**Notes:**
- Multiple items can be associated with the same campaign
- Items are grouped by campaign_id for efficient batch insertion
- Duplicate campaign-item pairs are ignored (ON CONFLICT DO NOTHING)
- Invalid UUIDs are skipped and counted in `error_count`
- If a campaign doesn't exist or doesn't belong to the organization, all its items will fail

**Error Responses:**
- **400 Bad Request**: Missing required columns, invalid CSV format, or empty file
- **401 Unauthorized**: Missing or invalid authentication token
- **403 Forbidden**: User is not an admin or manager
- **500 Internal Server Error**: Server error during upload

---

### GET /api/:org/campaigns/all

Retrieve all marketing campaigns for the organization, including associated items.

**Authentication:** Required (Admin/Manager only)

**Path Parameters:**
- `org` (string, required): Organization ID (UUID)

**Request:**
```http
GET /api/:org/campaigns/all
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "message": "Campaigns retrieved successfully",
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Summer Sale 2024",
      "status": "active",
      "start_time": "2024-06-01T00:00:00Z",
      "end_time": "2024-08-31T23:59:59Z",
      "discount": 15.00,
      "items_included": [
        {
          "item_id": "770e8400-e29b-41d4-a716-446655440001",
          "name": "Burger Deluxe",
          "needed_employees": 2,
          "price": 12.99
        },
        {
          "item_id": "880e8400-e29b-41d4-a716-446655440002",
          "name": "French Fries",
          "needed_employees": 1,
          "price": 3.99
        }
      ]
    },
    {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "name": "Holiday Promo",
      "status": "inactive",
      "start_time": "2023-12-01T00:00:00Z",
      "end_time": "2023-12-31T23:59:59Z",
      "discount": 25.00,
      "items_included": []
    }
  ]
}
```

**Response Fields:**
- `id`: Campaign unique identifier
- `name`: Campaign name
- `status`: Campaign status (active/inactive)
- `start_time`: Campaign start timestamp (RFC3339)
- `end_time`: Campaign end timestamp (RFC3339)
- `discount`: Discount percentage (nullable)
- `items_included`: Array of items in the campaign (may be empty)

**Items Fields:**
- `item_id`: Item unique identifier
- `name`: Item name
- `needed_employees`: Number of employees needed to prepare
- `price`: Item price (nullable)

**Notes:**
- Campaigns are ordered by start date (newest first)
- Returns all campaigns regardless of status or date
- Empty `items_included` array indicates no items associated

**Error Responses:**
- **401 Unauthorized**: Missing or invalid authentication token
- **403 Forbidden**: User is not an admin or manager
- **500 Internal Server Error**: Server error retrieving campaigns

---

### GET /api/:org/campaigns/week

Retrieve marketing campaigns started within the last 7 days, including associated items.

**Authentication:** Required (Admin/Manager only)

**Path Parameters:**
- `org` (string, required): Organization ID (UUID)

**Request:**
```http
GET /api/:org/campaigns/week
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "message": "Campaigns retrieved successfully",
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Weekend Flash Sale",
      "status": "active",
      "start_time": "2024-02-05T00:00:00Z",
      "end_time": "2024-02-07T23:59:59Z",
      "discount": 20.00,
      "items_included": [
        {
          "item_id": "770e8400-e29b-41d4-a716-446655440001",
          "name": "Pizza Margherita",
          "needed_employees": 3,
          "price": 15.99
        }
      ]
    }
  ]
}
```

**Response Structure:** Same as `/campaigns/all`

**Filter Criteria:**
- Only campaigns where `start_time >= NOW() - INTERVAL '7 days'`
- Ordered by start date (newest first)
- Includes all items associated with each campaign

**Notes:**
- Uses PostgreSQL `INTERVAL` for date filtering
- "Last week" means the last 7 days from the current timestamp
- Returns empty array if no campaigns started in the last 7 days

**Error Responses:**
- **401 Unauthorized**: Missing or invalid authentication token
- **403 Forbidden**: User is not an admin or manager
- **500 Internal Server Error**: Server error retrieving campaigns

---

## Dashboard Endpoints

### GET /api/:org/dashboard/demand

Retrieve stored demand heatmap predictions for the organization.

**Authentication:** Required (admin or manager only)

**Request:**
```http
GET /api/{org_id}/dashboard/demand
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `org` - Organization UUID

**Response (200 OK):**
```json
{
  "message": "Demand heatmap retrieved successfully",
  "data": {
    "restaurant_name": "Test Restaurant",
    "prediction_period": "2026-02-07 to 2026-02-13",
    "days": [
      {
        "day_name": "saturday",
        "date": "2026-02-07",
        "hours": [
          {
            "hour": 10,
            "order_count": 1,
            "item_count": 1
          },
          {
            "hour": 11,
            "order_count": 1,
            "item_count": 1
          }
        ]
      },
      {
        "day_name": "sunday",
        "date": "2026-02-08",
        "hours": [...]
      }
    ]
  }
}
```

**Response Fields:**
- `restaurant_name`: Name of the organization/restaurant
- `prediction_period`: Date range of predictions (e.g., "2026-02-07 to 2026-02-13")
- `days`: Array of daily predictions, each containing:
  - `day_name`: Day name in lowercase (e.g., "monday", "saturday")
  - `date`: Date in YYYY-MM-DD format
  - `hours`: Array of 24 hourly predictions, each containing:
    - `hour`: Hour of day (0-23)
    - `order_count`: Predicted number of orders for that hour
    - `item_count`: Predicted total number of items for that hour

**Notes:**
- Returns the most recently stored demand predictions for the organization
- Data is organized by day and hour for easy visualization
- All hours are included (0-23), with closed hours typically having 0 predictions
- Predictions are automatically generated by the ML service

**Error Responses:**
- **401 Unauthorized**: Missing or invalid authentication token
- **403 Forbidden**: User is not an admin or manager
- **404 Not Found**: No demand predictions found for the organization
- **500 Internal Server Error**: Server error retrieving demand data

---

### POST /api/:org/dashboard/demand/predict

Generate demand predictions using the ML service and store them in the database.

**Authentication:** Required (admin or manager only)

**Request:**
```http
POST /api/{org_id}/dashboard/demand/predict
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Path Parameters:**
- `org` - Organization UUID

**Request Body:**
```json
{
  "place": {
    "place_id": "4289bc18-b06c-4509-a710-89944e1cab16",
    "name": "Test Restaurant",
    "type": "restaurant",
    "latitude": 55.6761,
    "longitude": 12.5683,
    "waiting_time": 30,
    "receiving_phone": true,
    "delivery": true,
    "opening_hours": [
      {
        "weekday": "Sunday",
        "opening_time": "10:00:00",
        "closing_time": "22:00:00"
      },
      {
        "weekday": "Monday",
        "opening_time": "09:00:00",
        "closing_time": "22:00:00"
      }
    ],
    "fixed_shifts": true,
    "number_of_shifts_per_day": 3,
    "shift_time": [
      {
        "from": "09:00:00",
        "to": "14:00:00"
      },
      {
        "from": "14:00:00",
        "to": "19:00:00"
      },
      {
        "from": "19:00:00",
        "to": "23:00:00"
      }
    ],
    "accepting_orders": true
  },
  "orders": [
    {
      "order_id": "770e8400-e29b-41d4-a716-446655440001",
      "user_id": "550e8400-e29b-41d4-a716-446655440001",
      "create_time": "2024-02-01T12:30:00Z",
      "order_type": "dine in",
      "order_status": "completed",
      "total_amount": 45.50,
      "discount_amount": 0,
      "rating": 4.5,
      "items": null,
      "item_count": 2
    }
  ],
  "campaigns": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "name": "Campaign A",
      "status": "active",
      "start_time": "2024-02-01T10:00:00Z",
      "end_time": "2024-02-07T22:00:00Z",
      "items_included": [
        {
          "item_id": "660e8400-e29b-41d4-a716-446655440001",
          "name": "Margherita Pizza",
          "needed_employees": 1,
          "price": 15.50
        }
      ],
      "discount": 15
    }
  ],
  "prediction_start_date": "2026-02-07T12:50:16.391006154Z",
  "prediction_days": 7
}
```

**Request Fields:**
- `place`: Restaurant/organization details (location, hours, shifts)
- `orders`: Historical order data for training (array of past orders)
- `campaigns`: Active marketing campaigns affecting demand
- `prediction_start_date`: ISO 8601 timestamp to start predictions from
- `prediction_days`: Number of days to predict (typically 7)

**Response (200 OK):**
```json
{
  "message": "Demand prediction completed and stored successfully",
  "data": {
    "restaurant_name": "Test Restaurant",
    "prediction_period": "2026-02-07T12:50:16.391006154Z to 2026-02-13",
    "days": [
      {
        "day_name": "saturday",
        "date": "2026-02-07",
        "hours": [
          {
            "hour": 10,
            "order_count": 1,
            "item_count": 1
          }
        ]
      }
    ]
  }
}
```

**Process:**
1. ML service processes historical orders and campaigns
2. Extracts features: time, weather, holidays, demand patterns
3. Applies Random Forest model for hourly predictions
4. Zeros out predictions during closed business hours
5. Stores results in the `demand` table
6. Returns predictions for display

**ML Features Used:**
- **Temporal**: Day of week, month, week number, time of day
- **Historical**: Previous hour/day/week/month item counts, rolling 7-day average
- **External**: Weather data, holiday indicators
- **Business**: Campaign count, average discount, delivery availability, rating, waiting time
- **Location**: Place type, accepting orders status

**Notes:**
- Predictions automatically replace previous data for the organization
- Closed hours are automatically zeroed out based on business hours
- The ML service must be running and healthy for predictions to succeed
- All historical orders should be provided for accurate model training
- Predictions are deterministic based on the provided data

**Error Responses:**
- **400 Bad Request**: Invalid request body or missing required fields
- **401 Unauthorized**: Missing or invalid authentication token
- **403 Forbidden**: User is not an admin or manager
- **500 Internal Server Error**: ML service error or database error storing predictions
- **503 Service Unavailable**: ML service is not running or unavailable

**Database Storage:**
- Predictions are stored in the `demand` table
- Primary key: (organization_id, demand_date, hour)
- Previous predictions are deleted before storing new ones
- Constraints validate:
  - Hour is between 0-23
  - Order count and item count are non-negative
  - Day name matches the actual day of the week

---

## Schedule Endpoints

### GET /api/:org/dashboard/schedule/

Get the current authenticated user's schedule for the next 7 days.

**Authentication:** Required (manager or employee only)

**Request:**
```http
GET /api/:org/dashboard/schedule/
Authorization: Bearer <access_token>
```

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| org | UUID | Organization ID |

**Response (200 OK):**
```json
{
  "message": "Schedule retrieved successfully",
  "data": [
    {
      "date": "2026-02-07T00:00:00Z",
      "day": "saturday",
      "start_time": "2026-02-07T10:00:00Z",
      "end_time": "2026-02-07T14:00:00Z"
    }
  ]
}
```

**Error Responses:**
- `403 Forbidden` - Admins cannot access this endpoint
- `500 Internal Server Error` - Failed to retrieve schedule

---

### GET /api/:org/dashboard/schedule/all

Get the full organization schedule for the next 7 days. Only accessible by admin and manager roles.

**Authentication:** Required (admin or manager only)

**Request:**
```http
GET /api/:org/dashboard/schedule/all
Authorization: Bearer <access_token>
```

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| org | UUID | Organization ID |

**Response (200 OK):**
```json
{
  "message": "Schedule retrieved successfully",
  "data": [
    {
      "date": "2026-02-07T00:00:00Z",
      "day": "saturday",
      "start_time": "2026-02-07T10:00:00Z",
      "end_time": "2026-02-07T14:00:00Z"
    }
  ]
}
```

**Error Responses:**
- `403 Forbidden` - Employees cannot access this endpoint
- `500 Internal Server Error` - Failed to retrieve schedule

---

### POST /api/:org/dashboard/schedule/predict

Generate a new weekly schedule using the ML scheduling service. The endpoint gathers all necessary data (organization details, roles, employees, preferences, demand predictions) and sends it to the ML service for optimal schedule generation. The resulting schedule is stored in the database.

**Authentication:** Required (admin or manager only)

**Request:**
```http
POST /api/:org/dashboard/schedule/predict
Authorization: Bearer <access_token>
```

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| org | UUID | Organization ID |

**Request Body:** None required. All data is fetched internally from the database.

**Response (200 OK):**
```json
{
  "message": "schedule prediction retrieved successfully from API",
  "schedule_status": "OPTIMAL",
  "schedule_message": "Schedule generated successfully",
  "objective_value": 12345.67,
  "schedule_output": {
    "monday": [
      { "10:00-14:00": ["employee-uuid-1", "employee-uuid-2"] },
      { "14:00-22:00": ["employee-uuid-3"] }
    ],
    "tuesday": [],
    "wednesday": [],
    "thursday": [],
    "friday": [],
    "saturday": [],
    "sunday": []
  },
  "management_insights": {
    "has_solution": true,
    "peak_periods": [],
    "capacity_analysis": {},
    "employee_utilization": [],
    "role_demand": {},
    "hiring_recommendations": [],
    "coverage_gaps": [],
    "cost_analysis": {},
    "workload_distribution": {},
    "feasibility_analysis": []
  }
}
```

**Schedule Output Format:**
The `schedule_output` is a map where each key is a lowercase day name (`monday`–`sunday`) and the value is an array of shift objects. Each shift object maps a time range (`"HH:MM-HH:MM"`) to an array of employee UUIDs assigned to that shift.

**Management Insights:**
| Field | Type | Description |
|-------|------|-------------|
| has_solution | boolean | Whether the scheduler found a feasible solution |
| peak_periods | array | Identified peak demand periods |
| capacity_analysis | object | Workforce capacity vs demand analysis |
| employee_utilization | array | Per-employee utilization metrics |
| role_demand | object | Demand breakdown by role |
| hiring_recommendations | array | Suggested hiring actions |
| coverage_gaps | array | Shifts/slots with insufficient coverage |
| cost_analysis | object | Labor cost breakdown |
| workload_distribution | object | Fairness metrics for hour distribution |
| feasibility_analysis | array | Constraints that could not be satisfied |

**Prerequisites:**
- Organization must have demand predictions generated (via `/dashboard/demand/predict`)
- Organization must have employees with roles assigned
- Organization must have operating hours and rules configured

**Error Responses:**
- `403 Forbidden` - Only admins and managers can access this endpoint
- `500 Internal Server Error` - Failed to fetch required data or ML service error

**Notes:**
- The schedule is automatically stored in the database upon successful generation
- The ML service uses the OR-Tools CP-SAT solver with a 60-second time limit
- Employee availability and preferences are pulled from the preferences table
- Demand predictions must exist before generating a schedule

---

### GET /api/:org/staffing/employees/:id/schedule

Get a specific employee's schedule for the next 7 days. Accessible by admin and manager roles.

**Authentication:** Required (admin or manager)

**Request:**
```http
GET /api/:org/staffing/employees/:id/schedule
Authorization: Bearer <access_token>
```

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| org | UUID | Organization ID |
| id | UUID | Employee ID |

**Response (200 OK):**
```json
{
  "message": "Employee schedule retrieved successfully",
  "data": [
    {
      "date": "2026-02-07T00:00:00Z",
      "day": "saturday",
      "start_time": "2026-02-07T10:00:00Z",
      "end_time": "2026-02-07T14:00:00Z"
    }
  ]
}
```

**Error Responses:**
- `400 Bad Request` - Invalid employee ID format
- `403 Forbidden` - Employee belongs to a different organization
- `404 Not Found` - Employee not found
- `500 Internal Server Error` - Failed to retrieve schedule

---

## Alerts Endpoints

### GET /api/:org/dashboard/surge

Get alert insights for the organization (analytics).

**Authentication:** Required (admin or manager only)

**Request:**
```http
GET /api/{org_id}/dashboard/surge
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `org` - Organization UUID

**Response (200 OK):**
```json
{
  "message": "Alert insights retrieved successfully",
  "data": [
    {
      "title": "Total Alerts",
      "statistic": "45"
    },
    {
      "title": "Critical Alerts",
      "statistic": "5"
    },
    {
      "title": "High Severity Alerts",
      "statistic": "12"
    },
    {
      "title": "Most Common Severity",
      "statistic": "high"
    }
  ]
}
```

**Error Responses:**
- `401 Unauthorized` - Missing or invalid token
- `403 Forbidden` - Access denied (not admin or manager)
- `500 Internal Server Error` - Failed to retrieve insights

---

### GET /api/:org/dashboard/surge/all

Get all alerts for the organization.

**Authentication:** Required (admin or manager only)

**Request:**
```http
GET /api/{org_id}/dashboard/surge/all
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `org` - Organization UUID

**Response (200 OK):**
```json
{
  "message": "Alerts retrieved successfully",
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "organization_id": "660e8400-e29b-41d4-a716-446655440001",
      "severity": "critical",
      "subject": "High Order Volume Alert",
      "message": "Order volume has exceeded normal threshold by 40%"
    },
    {
      "id": "550e8400-e29b-41d4-a716-446655440002",
      "organization_id": "660e8400-e29b-41d4-a716-446655440001",
      "severity": "high",
      "subject": "Staff Shortage Warning",
      "message": "Current staffing level is 30% below recommended minimum"
    }
  ]
}
```

**Severity Levels:**
- `critical` - Urgent action required
- `high` - Immediate attention needed
- `moderate` - Monitor the situation

**Response Order:** Alerts are ordered by ID (newest first)

**Error Responses:**
- `401 Unauthorized` - Missing or invalid token
- `403 Forbidden` - Access denied (not admin or manager)
- `500 Internal Server Error` - Failed to retrieve alerts

---

### GET /api/:org/dashboard/surge/week

Get all alerts from the last 7 days for the organization.

**Authentication:** Required (admin or manager only)

**Request:**
```http
GET /api/{org_id}/dashboard/surge/week
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `org` - Organization UUID

**Response (200 OK):**
```json
{
  "message": "Alerts for last week retrieved successfully",
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "organization_id": "660e8400-e29b-41d4-a716-446655440001",
      "severity": "high",
      "subject": "Peak Hour Alert",
      "message": "System detected peak traffic during 7-9 PM window"
    }
  ]
}
```

**Filter Criteria:**
- Returns alerts generated within the last 7 days
- Ordered by ID (newest first)
- Only alerts belonging to the specified organization

**Notes:**
- "Last week" means the last 7 days from the current timestamp
- Returns empty array if no alerts were generated in the last 7 days

**Error Responses:**
- `401 Unauthorized` - Missing or invalid token
- `403 Forbidden` - Access denied (not admin or manager)
- `500 Internal Server Error` - Failed to retrieve alerts

---

## Rate Limiting

Currently, no rate limiting is implemented. This may be added in future versions.

## CORS

CORS is enabled for `http://localhost:3000` for frontend development.

---

## Database Schema

### Demand Table

The `demand` table stores hourly demand predictions for organizations.

**Table: `demand`**

```sql
CREATE TABLE demand (
    organization_id UUID REFERENCES organizations(id),
    demand_date DATE,
    day VARCHAR(10),
    hour INTEGER,
    order_count INTEGER,
    item_count INTEGER,
    PRIMARY KEY (organization_id, demand_date, hour),
    CHECK (hour >= 0 AND hour <= 23),
    CHECK (order_count >= 0),
    CHECK (item_count >= 0),
    CHECK (LOWER(TRIM(day)) = LOWER(TRIM(TO_CHAR(demand_date, 'Day'))))
);
```

**Column Descriptions:**

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `organization_id` | UUID | PRIMARY KEY, FOREIGN KEY | References the organization |
| `demand_date` | DATE | PRIMARY KEY | Date of the prediction |
| `day` | VARCHAR(10) | CHECK | Day name (e.g., 'saturday', 'sunday') |
| `hour` | INTEGER | PRIMARY KEY, CHECK | Hour of the day (0-23) |
| `order_count` | INTEGER | CHECK | Predicted number of orders (>= 0) |
| `item_count` | INTEGER | CHECK | Predicted total items (>= 0) |

**Key Changes:**

- **Migration 00021:** Updated day name constraint to support case-insensitive, whitespace-trimmed comparison. This allows the ML service to send lowercase day names (e.g., 'saturday') while validating them against PostgreSQL's day extraction from the date value.
- The constraint now uses: `LOWER(TRIM(day)) = LOWER(TRIM(TO_CHAR(demand_date, 'Day')))`
- Data is automatically deleted when new predictions are stored for an organization

**Associated Endpoints:**

- `POST /api/:org/dashboard/demand/predict` - Generate and store demand predictions
- `GET /api/:org/dashboard/demand` - Retrieve stored demand data

