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
  "max_consec_slots": 8
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

### PUT /api/auth/profile/changepassword

Change the current user's password.

**Authentication:** Required

**Request:**
```http
PUT /api/auth/profile/changepassword
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

**Authentication:** Required (admin or manager only)

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
      "role": "admin",
      "min_needed_per_shift": 0,
      "items_per_role_per_hour": null,
      "need_for_demand": false,
      "independent": true
    },
    {
      "organization_id": "uuid",
      "role": "manager",
      "min_needed_per_shift": 1,
      "items_per_role_per_hour": null,
      "need_for_demand": false,
      "independent": true
    },
    {
      "organization_id": "uuid",
      "role": "waiter",
      "min_needed_per_shift": 2,
      "items_per_role_per_hour": 10,
      "need_for_demand": true,
      "independent": false
    }
  ]
}
```

**Notes:**
- Default roles `admin` and `manager` are created automatically with each organization

**Error Responses:**
- `401 Unauthorized` - Missing or invalid token
- `403 Forbidden` - Access denied (not admin/manager or wrong organization)

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
  "role": "string (required, 1-50 characters)",
  "min_needed_per_shift": "integer (required, >= 0)",
  "items_per_role_per_hour": "integer (required if need_for_demand is true)",
  "need_for_demand": "boolean (required)",
  "independent": "boolean (required for custom roles)"
}
```

**Example Request:**
```json
{
  "role": "host",
  "min_needed_per_shift": 1,
  "need_for_demand": true,
  "items_per_role_per_hour": 5,
  "independent": false
}
```

**Response (201 Created):**
```json
{
  "message": "Role created successfully",
  "data": {
    "organization_id": "uuid",
    "role": "host",
    "min_needed_per_shift": 1,
    "items_per_role_per_hour": 5,
    "need_for_demand": true,
    "independent": false
  }
}
```

**Database Constraints:**
- If `need_for_demand` is true, `items_per_role_per_hour` must be >= 0
- If `need_for_demand` is false, `items_per_role_per_hour` must be null
- Custom roles require `independent` to be explicitly set

**Error Responses:**
- `400 Bad Request` - Invalid request body or constraint violation
- `401 Unauthorized` - Missing or invalid token
- `403 Forbidden` - Access denied
- `500 Internal Server Error` - Failed to create role (e.g., role already exists)

---

### GET /api/:org/roles/:role

Get details for a specific role.

**Authentication:** Required (admin or manager only)

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
    "role": "waiter",
    "min_needed_per_shift": 2,
    "items_per_role_per_hour": 10,
    "need_for_demand": true,
    "independent": false
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Missing or invalid token
- `403 Forbidden` - Access denied
- `404 Not Found` - Role not found

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
  "min_needed_per_shift": "integer (>= 0)",
  "items_per_role_per_hour": "integer (optional)",
  "need_for_demand": "boolean",
  "independent": "boolean (optional)"
}
```

**Example Request:**
```json
{
  "min_needed_per_shift": 2,
  "items_per_role_per_hour": 10,
  "need_for_demand": true,
  "independent": false
}
```

**Response (200 OK):**
```json
{
  "message": "Role updated successfully",
  "data": {
    "organization_id": "uuid",
    "role": "waiter",
    "min_needed_per_shift": 2,
    "items_per_role_per_hour": 10,
    "need_for_demand": true,
    "independent": false
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
    "operating_hours": [
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
      }
    ]
  }
}
```

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
    "max_consec_slots": 8
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
  "max_consec_slots": "integer (optional)"
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
  "max_consec_slots": 8
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
  "role": "string (required - must be valid organization role)",
  "salary_per_hour": "number (required)",
  "max_hours_per_week": "integer (optional)",
  "preferred_hours_per_week": "integer (optional)",
  "max_consec_slots": "integer (optional)",
  "user_roles": ["string (optional - additional roles)"]
}
```

**Example Request:**
```json
{
  "full_name": "Employee One",
  "email": "employee1@testorg.com",
  "role": "waiter",
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

**Notes:**
- The `role` must exist in the organization's roles
- An email is sent to the delegated user with login instructions
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

## Rate Limiting

Currently, no rate limiting is implemented. This may be added in future versions.

## CORS

CORS is enabled for `http://localhost:3000` for frontend development.
