# ClockWise: Intelligent Shift Planning System

![Go](https://img.shields.io/badge/Go-00ADD8?style=for-the-badge&logo=go&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![REST API](https://img.shields.io/badge/REST-API-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Make](https://img.shields.io/badge/Make-A42E2B?style=for-the-badge&logo=gnu&logoColor=white)

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
- **PTO & Leave Management**: Track employee time-off requests and maintain schedule integrity
- **Schedule Optimization**: Generate balanced schedules that respect employee preferences while meeting business needs
- **Labor Cost Analytics**: Monitor labor costs in real-time with predictive cost projections
- **Performance Metrics**: Dashboard with KPIs for coverage rates, labor cost efficiency, and service quality
- **Employee Management**: Comprehensive employee profiles with skills, availability, and preferences
- **Organization Management**: Multi-location support with centralized management capabilities

---

## Technologies Used

### Backend
- **Language**: Go 1.x
- **Framework**: RESTful API with Go standard library
- **Database**: PostgreSQL 12.4

### Infrastructure
- **Containerization**: Docker & Docker Compose
- **Database Migration**: Custom migration system (SQL-based)
- **Authentication**: Middleware-based request handling

### Tools & Utilities
- **Build System**: GNU Make
- **Database**: PostgreSQL with Alpine Linux container
- **Configuration**: Environment-based configuration via `.env`

---

## Installation

### Prerequisites
- Go 1.x or higher
- Docker and Docker Compose
- PostgreSQL CLI (optional, for local development)
- Make utility

### Step-by-Step Setup

#### 1. Clone the Repository
```bash
git clone <repository-url>
cd ClockWise
```

#### 2. Configure Environment Variables
Create a `.env` file in the project root:
```env
DB_HOST=db
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=your_password
DB_NAME=clockwise
API_PORT=8080
```

#### 3. Start PostgreSQL Container
```bash
make docker-run
```
This will spin up a PostgreSQL 12.4 container with persistent data storage.

#### 4. Run Database Migrations
Migrations are automatically applied on application startup. The migration files are located in the `migrations/` directory and include:
- Organizations schema
- Users and authentication
- Marketing campaigns
- Schedule management
- Orders and delivery
- Layoff and hiring records

#### 5. Build the Application
```bash
make build
```

#### 6. Run the Application
```bash
make run
```
The API will be available at `http://localhost:8080`

---

## Usage

### API Endpoints

#### Organizations
- `POST /api/organizations` - Create new organization
- `GET /api/organizations/:id` - Get organization details
- `PUT /api/organizations/:id` - Update organization

#### Users/Employees
- `POST /api/users` - Create new user/employee
- `GET /api/users/:id` - Get user details
- `PUT /api/users/:id` - Update user profile

#### Schedules & Shifts
- `GET /api/schedules/:org_id` - View schedules
- `POST /api/schedules` - Create/update schedules
- `GET /api/shifts/:id` - Get shift details

#### Demand Forecasting
- `GET /api/forecast/:org_id` - Get demand forecast
- `GET /api/insights/:org_id` - Get staffing insights

### Command Line Usage

```bash
# Run complete build with tests
make all

# Build the application only
make build

# Run the application
make run

# Start database container
make docker-run

# Stop database container
make docker-down

# Run integration tests
make itest

# Run test suite
make test

# Enable live reload during development
make watch

# Clean build artifacts
make clean
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
│                   API Layer (REST)                       │
│        ┌──────────────────────────────────────┐         │
│        │  Organization Handlers               │         │
│        │  User/Employee Handlers              │         │
│        │  Schedule & Shift Handlers           │         │
│        │  Demand Forecasting Handlers         │         │
└────────────┬───────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────┐
│              Middleware Layer                            │
│     ┌─────────────────────────────────────┐             │
│     │  Authentication & Authorization      │             │
│     │  Request/Response Logging            │             │
│     │  Error Handling                      │             │
└────────────┬────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────┐
│            Business Logic Layer (Services)               │
│     ┌─────────────────────────────────────┐             │
│     │  Email Service                       │             │
│     │  Forecasting Engine                  │             │
│     │  Scheduling Optimizer                │             │
└────────────┬────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────┐
│             Data Access Layer                            │
│     ┌─────────────────────────────────────┐             │
│     │  Organization Store                  │             │
│     │  User Store                          │             │
│     │  Schedule Store                      │             │
│     │  Database Connection Pool            │             │
└────────────┬────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────┐
│         PostgreSQL Database (Docker Container)           │
│     ┌─────────────────────────────────────┐             │
│     │  Organizations                      │             │
│     │  Users & Authentication              │             │
│     │  Schedules & Shifts                  │             │
│     │  Forecasts & Analytics               │             │
│     │  Orders & Delivery Data              │             │
└─────────────────────────────────────────────────────────┘
```

### Project Structure

```
ClockWise/
├── cmd/
│   └── api/
│       └── main.go                 # Application entry point
├── internal/
│   ├── api/
│   │   ├── org_handler.go         # Organization endpoints
│   │   └── user_handler.go        # User endpoints
│   ├── database/
│   │   ├── database.go            # DB connection management
│   │   ├── org_store.go           # Organization data access
│   │   └── user_store.go          # User data access
│   ├── middleware/
│   │   └── middleware.go          # HTTP middleware
│   ├── server/
│   │   ├── server.go              # Server setup
│   │   └── routes.go              # Route definitions
│   ├── service/
│   │   └── email_service.go       # Email notifications
│   └── utils/
│       └── utils.go               # Utility functions
├── migrations/
│   ├── 00001_organizations.sql
│   ├── 00002_users.sql
│   ├── 00003_marketing_campaigns.sql
│   ├── 00004_schedules.sql
│   ├── 00005_orders.sql
│   ├── 00006_delivery.sql
│   ├── 00007_tables.sql
│   ├── 00008_layoffs_hirings.sql
│   └── 00009_organizations_managers.sql
├── docker-compose.yml             # Docker configuration
├── go.mod                          # Go dependencies
├── Makefile                        # Build automation
└── README.md                       # This file
```

---

## Development

### Testing

```bash
# Run all tests with coverage
make test

# Run integration tests with database
make itest
```

### Live Reload Development

For faster development iteration:

```bash
make watch
```

This enables automatic recompilation when you modify source files.

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
- Real-time notifications and alerts
- Advanced analytics and reporting dashboard
- Multi-language support

---

## Support & Documentation

For issues, feature requests, or questions, please refer to the project's issue tracker or contact the development team.

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