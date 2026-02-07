# ClockWise: Intelligent Shift Planning System

![Go](https://img.shields.io/badge/Go-1.25.5-00ADD8?style=for-the-badge&logo=go&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-12.4-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Gin](https://img.shields.io/badge/Gin-1.11-00ADD8?style=for-the-badge&logo=go&logoColor=white)
![JWT](https://img.shields.io/badge/JWT-Auth-000000?style=for-the-badge&logo=jsonwebtokens&logoColor=white)

---

## Project Overview

**ClockWise** is an intelligent shift planning and workforce optimization system designed for quick-service restaurants and hospitality businesses. It solves the critical challenge of accurately predicting and meeting wildly fluctuating customer demand to ensure optimal staffing on every shift.

### The Problem

Quick-service restaurants face constant staffing challenges:
- **Unpredictable demand spikes** from social media trends, weather, or special events
- **Schedule disruptions** from unexpected call-offs and absences
- **Labor cost pressures** that require balancing service quality with budget constraints
- **Employee burnout** from understaffing during peak periods
- **Inefficient manual scheduling** that fails to adapt to dynamic conditions

ClockWise is the **Shift Wizard**—an intelligent system that monitors schedules, coverage, PTO, surprise events, and continuously recommends optimal staffing decisions.

---

## Features

### Core Capabilities

- **Demand Forecasting**: Predict customer traffic patterns based on historical data, day-of-week trends, and external events
- **Intelligent Shift Recommendations**: Real-time suggestions for optimal staffing levels with coverage analysis
- **Call-Off Management**: Quickly identify coverage gaps and auto-suggest solutions when employees call out
- **PTO & Leave Management**: Track employee time-off requests (calloff, holiday, resign) with approval workflow
- **Schedule Optimization**: Generate balanced schedules that respect employee preferences while meeting business needs
- **Labor Cost Analytics**: Monitor labor costs in real-time with predictive cost projections
- **Employee Management**: Comprehensive employee profiles with layoff/hiring history tracking
- **Organization Management**: Multi-tenant support with role-based access control (admin, manager, employee)
- **Bulk Employee Upload**: CSV-based bulk employee import with automatic welcome emails

---

## Technologies Used

### Backend
- **Language**: Go 1.25.5
- **Framework**: Gin Web Framework v1.11
- **Database**: PostgreSQL 12.4 (Alpine)
- **Authentication**: JWT with gin-jwt/v3
- **Password Hashing**: bcrypt via golang.org/x/crypto

### Infrastructure
- **Containerization**: Docker & Docker Compose (2 containers: API + Database)
- **Database Migration**: Goose v3 (SQL-based migrations)
- **Email Service**: SMTP-based notifications
- **Database Driver**: pgx/v5

### Key Dependencies
- `github.com/gin-gonic/gin` - HTTP web framework
- `github.com/appleboy/gin-jwt/v3` - JWT middleware
- `github.com/jackc/pgx/v5` - PostgreSQL driver
- `github.com/pressly/goose/v3` - Database migrations
- `github.com/google/uuid` - UUID generation
- `github.com/gin-contrib/cors` - CORS middleware

---

## Database Schema

### Tables

#### `organizations`
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| name | VARCHAR(100) | Organization name (unique) |
| address | TEXT | Physical address |
| email | VARCHAR(100) | Contact email (unique) |
| hex_code1, hex_code2, hex_code3 | VARCHAR(6) | Brand colors |
| created_at | TIMESTAMP | Creation timestamp |
| updated_at | TIMESTAMP | Last update timestamp |

#### `users`
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| full_name | VARCHAR(255) | Employee full name |
| email | VARCHAR(255) | Email address (unique) |
| password_hash | VARCHAR(255) | bcrypt hashed password |
| user_role | VARCHAR(50) | Role: admin, manager, employee |
| organization_id | UUID | Foreign key to organizations |
| created_at | TIMESTAMP | Creation timestamp |
| updated_at | TIMESTAMP | Last update timestamp |

#### `organizations_roles`
| Column | Type | Description |
|--------|------|-------------|
| organization_id | UUID | Foreign key to organizations |
| role | VARCHAR(50) | Role name (composite PK) |

#### `organizations_managers`
| Column | Type | Description |
|--------|------|-------------|
| organization_id | UUID | Foreign key to organizations |
| manager_id | UUID | Foreign key to users |

#### `requests`
| Column | Type | Description |
|--------|------|-------------|
| request_id | UUID | Primary key |
| employee_id | UUID | Foreign key to users |
| type | VARCHAR(20) | Type: calloff, holiday, resign |
| message | TEXT | Request message |
| submitted_at | TIMESTAMP | Submission timestamp |
| updated_at | TIMESTAMP | Last update timestamp |
| status | VARCHAR(10) | Status: accepted, declined, in queue |

#### `layoffs_hirings`
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| user_id | UUID | Employee ID |
| user_name | VARCHAR(255) | Employee name (archived) |
| user_email | VARCHAR(255) | Employee email (archived) |
| organization_id | UUID | Foreign key to organizations |
| action | VARCHAR(20) | Action: layoff, hiring |
| reason | TEXT | Reason for action |
| action_date | TIMESTAMP | Action timestamp |

#### `schedules`
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |

---

## Installation

### Prerequisites
- Docker and Docker Compose

### Docker Containers

The application runs in two containers:

| Container | Name | Description |
|-----------|------|-------------|
| **cw_app** | ClockwiseBackend | Go API server |
| **db** | ClockwiseDB | PostgreSQL 12.4 database |

### Step-by-Step Setup

#### 1. Clone the Repository
```bash
git clone <repository-url>
cd ClockWise
```

#### 2. Configure Environment Variables
Create a `.env` file in the project root:
```env
# Database Configuration
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_DB=clockwise
DB_PORT=5432
DB_HOST=db
DB_SCHEMA=public

# API Configuration
PORT=8080

# JWT Configuration
JWT_SECRET=your_super_secret_jwt_key

# SMTP Configuration (optional - falls back to mock emails if not set)
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USERNAME=your_email
SMTP_PASSWORD=your_email_password
```

#### 3. Start All Services
```bash
docker-compose up -d
```
This will:
- Build the Go application from Dockerfile
- Start PostgreSQL 12.4 container with persistent volume
- Run database migrations automatically on startup
- Start the API server

#### 4. Verify Services
```bash
# Check container status
docker-compose ps

# Check API health
curl http://localhost:8080/health

# View logs
docker-compose logs -f cw_app
```

The API will be available at `http://localhost:8080`

### Running Without Docker (Development)

```bash
# Start only the database
docker-compose up -d db

# Set DB_HOST to localhost in .env
DB_HOST=localhost

# Run the application
go run cmd/api/main.go
```

---

## API Endpoints

### Public Routes

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/login` | User authentication (returns JWT) |
| POST | `/register` | Register new organization with admin |
| GET | `/health` | Health check with DB stats |

### Auth Routes (Protected)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/refresh_token` | Refresh JWT token |
| POST | `/auth/logout` | Logout user |
| GET | `/auth/me` | Get current user info & claims |

### Organization Routes (Protected)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/:org/` | Get organization details |
| POST | `/:org/request` | Submit call-off/leave request |

### Dashboard Routes

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/:org/dashboard/` | Get dashboard data |
| GET | `/:org/dashboard/schedule/` | Get schedule |
| PUT | `/:org/dashboard/schedule/` | Edit schedule |
| POST | `/:org/dashboard/schedule/refresh` | Refresh/regenerate schedule |

### Insights Routes

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/:org/insights/` | Get staffing insights |

### Staffing Routes

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/:org/staffing/` | Get staffing summary (total, by role) |
| POST | `/:org/staffing/` | Delegate/create new user |
| POST | `/:org/staffing/upload` | Bulk upload employees via CSV |
| GET | `/:org/staffing/employees/` | Get all employees |

### Employee Routes

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/:org/staffing/employees/:id/` | Get employee details |
| DELETE | `/:org/staffing/employees/:id/layoff` | Layoff employee |
| GET | `/:org/staffing/employees/:id/schedule` | Get employee schedule |
| PUT | `/:org/staffing/employees/:id/schedule` | Edit employee schedule |
| GET | `/:org/staffing/employees/:id/requests` | Get employee requests |
| POST | `/:org/staffing/employees/:id/requests/approve` | Approve request |
| POST | `/:org/staffing/employees/:id/requests/decline` | Decline request |

### Preferences Routes (Employees Only)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/:org/preferences/` | Get employee preferences |
| PUT | `/:org/preferences/` | Update preferences |

### Rules Routes

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/:org/rules/` | Get organization rules |
| PUT | `/:org/rules/` | Update organization rules |

---

## Authentication

### JWT Token Structure

Access tokens contain the following claims:
```json
{
  "id": "user-uuid",
  "full_name": "John Doe",
  "email": "john@example.com",
  "user_role": "admin",
  "organization_id": "org-uuid"
}
```

### Token Configuration
- **Access Token Timeout**: 15 minutes
- **Refresh Token Timeout**: 7 days
- **Token Lookup**: Header (`Authorization: Bearer <token>`), Query (`?token=`), Cookie (`access_token`)

### Example Login Request
```bash
curl -X POST http://localhost:8080/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "password123"}'
```

---

## Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Client Applications                   │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│           Docker Container: ClockwiseBackend             │
│  ┌───────────────────────────────────────────────────┐  │
│  │               API Layer (Gin REST)                 │  │
│  │    Organization | Staffing | Employee | Dashboard  │  │
│  └────────────────────┬──────────────────────────────┘  │
│                       │                                  │
│  ┌────────────────────▼──────────────────────────────┐  │
│  │              Middleware Layer                      │  │
│  │   JWT Auth | Org Validation | CORS | Logging      │  │
│  └────────────────────┬──────────────────────────────┘  │
│                       │                                  │
│  ┌────────────────────▼──────────────────────────────┐  │
│  │          Business Logic Layer (Services)          │  │
│  │     Email Service | CSV Upload | Scheduling       │  │
│  └────────────────────┬──────────────────────────────┘  │
│                       │                                  │
│  ┌────────────────────▼──────────────────────────────┐  │
│  │           Data Access Layer (Stores)              │  │
│  │    OrgStore | UserStore | RequestStore | DB Pool  │  │
│  └────────────────────┬──────────────────────────────┘  │
└───────────────────────┼─────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│            Docker Container: ClockwiseDB                 │
│  ┌───────────────────────────────────────────────────┐  │
│  │           PostgreSQL 12.4 (Alpine)                │  │
│  │  organizations | users | requests | schedules     │  │
│  │  layoffs_hirings | organizations_roles            │  │
│  └───────────────────────────────────────────────────┘  │
│              Volume: postgres-data                       │
└─────────────────────────────────────────────────────────┘
```

### Project Structure

```
ClockWise/
├── cmd/
│   └── api/
│       └── main.go                 # Application entry point with graceful shutdown
├── internal/
│   ├── api/
│   │   ├── org_handler.go          # Organization & delegation endpoints
│   │   ├── staffing_handler.go     # Staffing summary & CSV upload
│   │   ├── employee_handler.go     # Employee CRUD & request management
│   │   ├── dashboard_handler.go    # Dashboard endpoints
│   │   ├── insights_handler.go     # Analytics & insights
│   │   ├── schedule_handler.go     # Schedule management
│   │   └── rules_handler.go        # Organization rules
│   ├── database/
│   │   ├── database.go             # DB connection & health checks
│   │   ├── org_store.go            # Organization data access
│   │   ├── user_store.go           # User CRUD & layoff operations
│   │   └── request_store.go        # Request data access
│   ├── middleware/
│   │   └── middleware.go           # JWT auth & ValidateOrgAccess
│   ├── server/
│   │   ├── server.go               # Server setup & dependency injection
│   │   └── routes.go               # Route definitions
│   ├── service/
│   │   ├── email_service.go        # SMTP email (with mock fallback)
│   │   └── uploadcsv_service.go    # CSV parsing service
│   └── utils/
│       └── utils.go                # Password generation utilities
├── migrations/
│   ├── 00001_organizations.sql
│   ├── 00002_users.sql
│   ├── 00004_schedules.sql
│   ├── 00008_layoffs_hirings.sql
│   ├── 00009_organizations_managers.sql
│   ├── 00010_requests.sql
│   └── fs.go                       # Embedded migrations filesystem
├── Dockerfile                      # Multi-stage Go build
├── docker-compose.yml              # 2-container orchestration
├── go.mod                          # Go 1.25.5 dependencies
└── README.md
```

---

## CSV Upload Format

For bulk employee upload via `POST /:org/staffing/upload`:

```csv
full_name,email,role
John Doe,john@example.com,employee
Jane Smith,jane@example.com,manager
Bob Wilson,bob@example.com,staff
```

**Required columns:**
- `full_name` - Employee's full name
- `email` - Employee's email address
- `role` - One of: `manager`, `staff`, `employee`

**Response:**
```json
{
  "message": "Bulk upload completed",
  "created_count": 2,
  "created": ["john@example.com", "jane@example.com"],
  "failed_count": 1,
  "failed": [{"email": "bob@example.com", "error": "duplicate key"}]
}
```

Welcome emails are sent automatically to created users with temporary passwords.

---

## Development

### Docker Commands

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Restart services
docker-compose restart

# Stop all services
docker-compose down

# Rebuild after code changes
docker-compose up -d --build

# Access database shell
docker exec -it ClockwiseDB psql -U postgres -d clockwise
```

### Running Tests

```bash
# Run all tests
go test ./...

# Run with coverage
go test -cover ./...

# Run specific package tests
go test ./internal/database/...
```

### Building Locally

```bash
# Build binary
go build -o clockwise cmd/api/main.go

# Run binary
./clockwise
```

---

## Team Members

### 💻 Backend Development
- **Mohamed Hany**
- **Ziad Eliwa**

### 🤖 Machine Learning
- **Fares Osama**
- **Hazem Nasr**

### 🎨 Frontend Development
- **Mostafa Mohamed**

---

## Future Roadmap

- Machine learning models for advanced demand forecasting
- Mobile app for employee scheduling
- Automated scheduling optimization using AI
- Integration with social media APIs for trend analysis
- Real-time notifications and alerts (WebSocket)
- Advanced analytics and reporting dashboard
- Multi-language support

---

## License

MIT License

Copyright (c) 2026 ClockWise Team

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.