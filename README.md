# AntiClockWise: Intelligent Shift Planning System

![Go](https://img.shields.io/badge/Go-1.25.5-00ADD8?style=for-the-badge&logo=go&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)
![React](https://img.shields.io/badge/React-18.3-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-12.4-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-7-DC382D?style=for-the-badge&logo=redis&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Nginx](https://img.shields.io/badge/Nginx-009639?style=for-the-badge&logo=nginx&logoColor=white)

---

## Table of Contents

- [Project Overview](#project-overview)
- [Features](#features)
- [System Architecture](#system-architecture)
- [Technology Stack](#technology-stack)
- [Backend (Go API)](#backend-go-api)
- [ML Service (Python / FastAPI)](#ml-service-python--fastapi)
  - [Demand Prediction](#1-demand-prediction)
  - [Staff Scheduling (CP-SAT)](#2-staff-scheduling-cp-sat)
  - [Surge Detection](#3-surge-detection-system)
  - [Campaign Recommender](#4-campaign-recommendation-system)
  - [Model Maintenance](#5-model-maintenance)
- [Frontend (React)](#frontend-react)
- [Database Schema](#database-schema)
- [Installation & Setup](#installation--setup)
- [Environment Variables](#environment-variables)
- [API Documentation](#api-documentation)
- [Development](#development)
- [Project Structure](#project-structure)
- [Team Members](#team-members)
- [License](#license)

---

## Project Overview

**AntiClockWise** is an end-to-end intelligent shift planning and workforce optimization platform designed for quick-service restaurants (QSR) and hospitality businesses. It combines a robust Go REST API, a Python ML service with multiple AI/ML models, and a React frontend to solve the critical challenge of accurately predicting and meeting wildly fluctuating customer demand to ensure optimal staffing on every shift.

### The Problem

Quick-service restaurants face constant staffing challenges:
- **Unpredictable demand spikes** from social media trends, weather, or special events
- **Schedule disruptions** from unexpected call-offs and absences
- **Labor cost pressures** that require balancing service quality with budget constraints
- **Employee burnout** from understaffing during peak periods
- **Inefficient manual scheduling** that fails to adapt to dynamic conditions
- **Marketing inefficiency** from running campaigns without data-driven guidance

AntiClockWise is the **Shift Wizard** — an intelligent system that monitors schedules, coverage, PTO, surprise events, and continuously recommends optimal staffing and marketing decisions.

---

## Features

### Workforce Management
- **Multi-tenant Organizations**: Each organization gets isolated data, roles, and branding (custom hex colors)
- **Role-Based Access Control**: Three tiers — Admin, Manager, Employee — each with tailored dashboards
- **Employee Lifecycle**: Hiring, onboarding with auto-generated welcome emails, layoff tracking with archived records
- **Bulk CSV Upload**: Import employees, orders, deliveries, campaigns, and items via CSV
- **Request Management**: Employees submit call-off/holiday/resign requests; managers approve or decline

### AI-Powered Demand Forecasting
- **CatBoost v6 Model**: Predicts hourly item and order counts with 69 engineered features
- **Quantile Loss (α=0.60)**: Biases predictions upward for safe staffing (MAE: 3.32, R²: 0.69)
- **Weather & Holiday Integration**: Incorporates real-time weather and public holiday data
- **Cyclical Time Encoding**: Properly handles hour-of-day and day-of-week periodicity

### Intelligent Scheduling (CP-SAT Solver)
- **Google OR-Tools CP-SAT**: Constraint-programming-based optimal schedule generation
- **15+ Constraint Types**: Max hours/week, consecutive shift limits, role coverage, employee preferences
- **Management Insights**: Automatically generates utilization analysis, coverage gap reports, hiring recommendations, and cost projections

### Surge Detection & Alerts
- **3-Layer Architecture**: Data collection → Surge detection → Alert system
- **Real-Time Monitoring**: 5-minute resolution venue metrics with social media signal integration
- **Configurable Thresholds**: 1.5x ratio threshold with 20-item minimum excess demand
- **Multi-Channel Alerts**: SMS (Twilio), email, with optional LLM-powered analysis (Gemini)

### Campaign Recommendation Engine
- **Thompson Sampling**: Contextual bandit for exploration-exploitation balance
- **XGBoost ROI Prediction**: 15+ contextual features for campaign performance prediction
- **Item Affinity Analysis**: Co-purchase lift matrix for optimal item bundling
- **Online Learning**: Continuous improvement from campaign feedback

### Frontend Dashboards
- **Admin Dashboard**: Full organizational control — staffing, scheduling, analytics, data uploads, demand heatmaps
- **Manager Dashboard**: Team management, request approvals, schedule oversight
- **Employee Dashboard**: Personal schedule view, preference submission, request management

**Business Approach**
- **Problem Solved:** Reduces overstaffing and understaffing by forecasting demand and automating schedules.
- **Who Benefits:** Store managers, operations leads, and workforce planners at multi-location retail and hospitality businesses.
- **Value Delivered:** Lower labor costs, improved service levels, faster response to demand surges, and simplified operational planning.
- **How It's Used:** Integrates with payroll and POS systems; ingest employee lists (including roles), forecasts demand, and generates optimized shift schedules.

---

## System Architecture
![Alt text](./Blank%20diagram.png)

### Docker Compose Services

| Container | Service | Port | Description |
|-----------|---------|------|-------------|
| `AntiClockWiseBackend` | `cw-app` | 8080 | Go REST API server |
| `AntiClockWiseDB` | `db` | 5432 | PostgreSQL 12.4 with persistent volume |
| `MLService` | `cw-ml-service` | 8000 | Python FastAPI ML service |
| `AntiClockWiseFrontend` | `cw-web` | 3000 | React development server |
| `AntiClockWiseNginx` | `nginx` | 80 | Reverse proxy & static assets |
| `AntiClockWiseRedis` | `redis` | 6379 | Cache layer (256MB, LRU eviction) |

---

## Technology Stack

### Backend (Go)
| Technology | Version | Purpose |
|-----------|---------|---------|
| Go | 1.25.5 | Primary language |
| Gin | 1.11 | HTTP web framework |
| gin-jwt/v3 | 3.4.1 | JWT authentication middleware |
| pgx/v5 | 5.8.0 | PostgreSQL driver |
| Goose v3 | 3.26.0 | SQL-based database migrations |
| go-sqlmock | 1.5.2 | Database mock for testing |
| testcontainers-go | 0.40.0 | Integration testing with real containers |
| bcrypt | - | Password hashing via `golang.org/x/crypto` |
| UUID | 1.6.0 | UUID generation (`google/uuid`) |
| CORS | 1.7.6 | Cross-origin resource sharing |
| Gzip | 1.2.5 | Response compression |

### ML Service (Python)
| Technology | Version | Purpose |
|-----------|---------|---------|
| Python | 3.11 | Runtime |
| FastAPI | 0.104.1 | REST API framework |
| CatBoost | - | Demand prediction (via scikit-learn interface) |
| XGBoost | 2.0.2 | Campaign ROI prediction |
| OR-Tools | 9.8.3296 | CP-SAT constraint-programming scheduler |
| pandas / numpy | latest | Data processing |
| holidays | 0.37 | Public holiday detection |
| pytrends | 4.9.2 | Google Trends for surge detection |
| Twilio | 8.10.0 | SMS/voice alert delivery |

### Frontend (React)
| Technology | Version | Purpose |
|-----------|---------|---------|
| React | 18.3.1 | UI framework |
| React Router DOM | 7.13.0 | Client-side routing |
| Create React App | 5.0.1 | Build toolchain |

### Infrastructure
| Technology | Version | Purpose |
|-----------|---------|---------|
| Docker Compose | latest | Multi-container orchestration (6 services) |
| Nginx | latest | Reverse proxy, rate limiting, gzip, security headers |
| Redis | 7-alpine | Caching with LRU eviction (256MB limit) |
| PostgreSQL | 12.4-alpine | Relational database with persistent volume |

---

## Backend (Go API)

The backend is a layered Go application using the Gin web framework, located in `app/api/`.

### Architecture Layers

```
Handlers (API Layer)     → HTTP request/response, validation
    ↓
Middleware               → JWT auth, org validation, CORS, logging
    ↓
Services                 → Business logic (email, CSV upload)
    ↓
Cache Layer (Redis)      → Wraps all stores, LRU with TTL
    ↓
Database Stores          → Direct PostgreSQL access via pgx
```

### Handlers

| Handler | File | Responsibility |
|---------|------|----------------|
| Organization | `org_handler.go` | Org profile, registration, delegation |
| Staffing | `staffing_handler.go` | Summary, CSV upload, employee listing |
| Employee | `employee_handler.go` | CRUD, layoff, requests approve/decline |
| Schedule | `schedule_handler.go` | Schedule get/predict via ML solver |
| Dashboard | `dashboard_handler.go` | Demand heatmap, ML predictions |
| Insights | `insights_handler.go` | Staffing analytics |
| Campaign | `campaign_handler.go` | Campaign CRUD, ML recommendation proxy |
| Orders | `orders_handler.go` | Orders, deliveries, items CRUD & CSV upload |
| Roles | `roles_handler.go` | Organization role management |
| Rules | `rules_handler.go` | Scheduling rules & operating hours |
| Preferences | `preferences_handler.go` | Employee shift preferences |
| Profile | `profile_handler.go` | User profile, password change |
| Offers | `offers_handlers.go` | Shift offer management (accept/decline) |
| Surge | `surge_handler.go` | Surge data retrieval, active venues |

### Database Stores (Data Access Layer)

| Store | File | Tables |
|-------|------|--------|
| `OrgStore` | `org_store.go` | organizations |
| `UserStore` | `user_store.go` | users, layoffs_hirings |
| `OrderStore` | `order_store.go` | orders, order_items |
| `CampaignStore` | `campaign_store.go` | marketing_campaigns |
| `ScheduleStore` | `schedule_store.go` | schedules |
| `RolesStore` | `roles_store.go` | organizations_roles |
| `RulesStore` | `rules_store.go` | Organization rules |
| `PreferencesStore` | `preferences_store.go` | preferences |
| `RequestStore` | `request_store.go` | requests |
| `DemandStore` | `demand_store.go` | demand |
| `OperatingHoursStore` | `operating_hours_store.go` | Operating hours |
| `InsightStore` | `insight_store.go` | Insights |
| `UserRolesStore` | `user_roles_store.go` | User-role assignments |
| `OfferStore` | `offer_store.go` | offers |
| `SurgeStore` | `surge_store.go` | Surge detection data |

### Authentication

- **JWT** via `gin-jwt/v3` with `golang-jwt/v5`
- **Access Token**: 15-minute expiry
- **Refresh Token**: 7-day expiry
- **Token Lookup**: `Authorization: Bearer <token>` header, query parameter, or cookie
- Claims include: `id`, `full_name`, `email`, `user_role`, `organization_id`

### Redis Caching

All database stores are wrapped with a Redis cache layer providing:
- Automatic cache invalidation on writes
- LRU eviction policy (256MB max memory)
- Append-only file persistence for durability
- Health checks every 10 seconds

### API Documentation

Full backend REST API documentation with request/response examples is available at:

**[`app/api/docs/API_DOCUMENTATION.md`](app/api/docs/API_DOCUMENTATION.md)**

Covers all 16 endpoint categories: Health, Auth, Profile, Roles, Rules, Preferences, Staffing, Insights, Organization, Orders, Deliveries, Items, Campaigns, Schedule, Surge, and Offers.

---

## ML Service (Python / FastAPI)

The ML service is a standalone Python FastAPI application located in `app/ml/`, providing four major subsystems. It runs as its own Docker container at `http://cw-ml-service:8000`.

### ML API Documentation

Full ML service REST API documentation is available at:

**[`app/api/docs/data.md`](app/api/docs/data.md)** — Unified API docs covering Demand Prediction, Staff Scheduling, and Campaign Recommendations endpoints with complete request/response schemas.

### 1. Demand Prediction

**Model**: CatBoost v6 with Quantile Loss  
**Files**: `src/deploy_model.py`, `src/v6_features.py`, `src/feature_engineering.py`, `src/api_feature_engineering.py`

| Metric | Value |
|--------|-------|
| MAE | 3.32 items |
| R² | 0.69 |
| Bias | +0.26 (intentional upward) |
| Improvement vs baseline | 42% |

#### 69 Engineered Features

| Category | Count | Examples |
|----------|-------|---------|
| Cyclical Time | 6 | `hour_sin`, `hour_cos`, `dow_sin`, `dow_cos` |
| Time Context | 21 | Rush hour flags, time-of-day bins, weekend indicators |
| Lag Features | 7 | 3d, 7d, 14d, 30d rolling averages |
| Venue-Specific | 7 | `venue_hour_avg`, `venue_volatility`, `venue_dow_avg` |
| Weekend Patterns | 6 | Weekend-hour interactions |
| Weather Interactions | 8 | Temperature, rain, wind interactions |
| External | 14 | Weather, holidays, campaign overlap |

#### Quantile Loss (α=0.60)

The model uses **quantile regression** instead of MSE — it predicts the 60th percentile of demand rather than the mean. This provides a deliberate upward bias that is ideal for staffing: slightly over-predicting is cheaper than being short-staffed during rush hours.

**Detailed documentation**: [`app/ml/docs/DEMAND_PREDICTION_MODEL.md`](app/ml/docs/DEMAND_PREDICTION_MODEL.md)  
**Feature engineering details**: [`app/ml/docs/V6_MODEL_INTEGRATION.md`](app/ml/docs/V6_MODEL_INTEGRATION.md)  
**Development history**: [`app/ml/docs/DEVELOPMENT_HISTORY.md`](app/ml/docs/DEVELOPMENT_HISTORY.md)

---

### 2. Staff Scheduling (CP-SAT)

**Engine**: Google OR-Tools CP-SAT Solver  
**File**: `src/scheduler_cpsat.py`

The scheduling engine takes demand predictions and employee data to generate optimal shift assignments by solving a constraint satisfaction problem.

#### Constraints Handled

| Constraint | Description |
|-----------|-------------|
| Max hours/week | Per-employee weekly hour limits |
| Consecutive shifts | Maximum consecutive working slots |
| Role coverage | Minimum staff per role per shift |
| Employee preferences | Day/time preferences with priority weighting |
| Availability | Approved time-off and unavailability |
| Demand matching | Staff levels matched to predicted demand |
| Fairness | Balanced distribution across employees |

#### Management Insights

Each generated schedule comes with automated analysis:

| Insight | Description |
|---------|-------------|
| **Utilization Analysis** | Per-employee hour utilization vs capacity |
| **Coverage Gaps** | Shifts where staffing falls below demand |
| **Hiring Recommendations** | Roles needing additional headcount |
| **Cost Analysis** | Total labor cost projections by role |

**Detailed documentation**: [`app/ml/docs/scheduler_api_usage.md`](app/ml/docs/scheduler_api_usage.md)

---

### 3. Surge Detection System

**Files**: `src/data_collector.py`, `src/surge_detector.py`, `src/alert_system.py`, `src/surge_orchestrator.py`, `src/surge_api.py`

A 3-layer real-time monitoring system that detects unexpected demand spikes and alerts management.

```
Layer 1: Data Collection        Layer 2: Detection          Layer 3: Alerts
┌─────────────────────┐    ┌─────────────────────┐    ┌───────────────────┐
│  ML Predictions     │    │  Ratio Analysis     │    │  SMS (Twilio)     │
│  Social Media APIs  │───>│  1.5x threshold     │───>│  Email            │
│  Historical Orders  │    │  20-item min excess  │    │  LLM Analysis     │
│  5-min resolution   │    │  Trend detection     │    │  (Gemini optional)│
└─────────────────────┘    └─────────────────────┘    └───────────────────┘
```

#### Surge Detection Criteria

- **Ratio threshold**: actual/predicted > 1.5
- **Minimum excess**: at least 20 items above prediction
- **Social signal boost**: Twitter mentions and sentiment amplify surge scoring
- **Trend detection**: Sustained growth over consecutive intervals

**Detailed documentation**:
- [`app/ml/docs/surge_detection_architecture.md`](app/ml/docs/surge_detection_architecture.md)
- [`app/ml/docs/SURGE_ORCHESTRATION_GUIDE.md`](app/ml/docs/SURGE_ORCHESTRATION_GUIDE.md)
- [`app/ml/docs/DATA_COLLECTION_API.md`](app/ml/docs/DATA_COLLECTION_API.md)

---

### 4. Campaign Recommendation System

**Files**: `src/campaign_analyzer.py`, `src/campaign_recommender.py`, `src/train_campaign_model.py`

An ML-powered marketing recommendation engine that suggests optimal promotional campaigns.

#### Algorithm

**Thompson Sampling** (contextual bandit) balances exploration of new campaign types with exploitation of proven performers.

```
Priority Score = 0.50 × Expected ROI (XGBoost)
               + 0.30 × Thompson Sample × 100
               + 0.20 × Confidence × 100
```

#### Features for ROI Prediction

| Category | Features |
|----------|----------|
| Campaign | discount, duration_days, num_items |
| Temporal | day_of_week, hour_of_day, is_weekend |
| Seasonal | season_winter/spring/summer/fall |
| Context | was_holiday, avg_temperature, weather |
| Historical | avg_orders_before, past campaign performance |

#### Recommendation Types

| Type | Description |
|------|-------------|
| **Template-Based** | Proven campaign formats with tuned parameters |
| **Affinity-Based** | Novel item combinations from co-purchase analysis |
| **Seasonal** | Time-appropriate campaigns for holidays/seasons |

#### Feedback Loop

The system supports online learning — campaign results are fed back via the `/recommend/campaigns/feedback` endpoint to continuously improve recommendations through Thompson Sampling prior updates and XGBoost retraining.

**Detailed documentation**: [`app/ml/docs/CAMPAIGN_RECOMMENDER.md`](app/ml/docs/CAMPAIGN_RECOMMENDER.md)

---

### 5. Model Maintenance

**Files**: `src/model_monitor.py`, `src/fine_tune_model.py`, `src/model_manager.py`

A 3-tier hybrid maintenance strategy ensures the demand prediction model stays accurate over time.

| Tier | Trigger | Action |
|------|---------|--------|
| **Tier 1** | Weekly | Fine-tune on new data (CatBoost warm start, lower learning rate 0.03) |
| **Tier 2** | Quarterly | Full model retraining with accumulated data |
| **Tier 3** | Drift detected | Emergency retraining when degradation exceeds 15% |

#### Model Monitor

- Logs prediction vs actual outcomes in `logs/predictions_log.csv`
- Tracks rolling performance metrics
- **15% degradation** → suggests retraining
- **25% degradation** → critical alert

**Detailed documentation**: [`app/ml/docs/MODEL_MAINTENANCE.md`](app/ml/docs/MODEL_MAINTENANCE.md)

---

## Frontend (React)

The frontend is a React 18 single-page application located in `web/`, built with Create React App. It communicates with the backend exclusively through the Nginx reverse proxy.

### Routing

| Path | Component | Access |
|------|-----------|--------|
| `/` | `App.jsx` | Public — landing page with Login/Signup modals |
| `/admin` | `AdminDashboard.jsx` | Protected — admin users only |
| `/manager` | `ManagerDashboard.jsx` | Protected — manager users only |
| `/employee` | `EmployeeDashboard.jsx` | Protected — employee users only |

All dashboard routes are wrapped with `ProtectedRoute.jsx` which checks for a valid `access_token` in `localStorage` before rendering.

### API Service Layer

The frontend API client (`src/services/api.js`, 1092 lines) provides organized API modules:

| Module | Functions |
|--------|-----------|
| `authAPI` | `register`, `login`, `refreshToken`, `logout`, `getCurrentUser` |
| `profileAPI` | `getProfile`, `changePassword` |
| `staffingAPI` | `getStaffingSummary`, `createEmployee`, `getAllEmployees`, `getEmployee`, `layoffEmployee`, `bulkUploadEmployees` |
| `requestsAPI` | `getEmployeeRequests`, `approveRequest`, `declineRequest`, `submitRequest`, `getAllRequests` |
| `rolesAPI` | `getAll`, `getRole`, `createRole`, `updateRole`, `deleteRole` |
| `rulesAPI` | `getRules`, `saveRules` |
| `ordersAPI` | `getOrderInsights`, `getAllOrders`, `getOrdersWeek`, `getOrdersToday`, `uploadOrdersCSV`, `uploadOrderItemsCSV` |
| `preferencesAPI` | `getPreferences`, `savePreferences` |
| `insightsAPI` | `getInsights` |
| `deliveriesAPI` | `getDeliveryInsights`, `getAllDeliveries`, `getDeliveriesWeek`, `getDeliveriesToday`, `uploadDeliveriesCSV` |
| `itemsAPI` | `getItemInsights`, `getAllItems`, `uploadItemsCSV` |
| `campaignsAPI` | `getCampaignInsights`, `getAllCampaigns`, `getCampaignsWeek`, `uploadCampaignsCSV`, `uploadCampaignItemsCSV`, `recommendCampaigns`, `submitCampaignFeedback` |
| `dashboardAPI` | `getSurgeInsights`, `getAllSurge`, `getSurgeWeek`, `getDemandHeatmap`, `generateDemandPrediction`, `getMySchedule`, `getAllSchedule`, `generateSchedule` |
| `organizationAPI` | `getProfile` |
| `healthAPI` | `checkHealth` |

### Custom Hooks

The `services/hooks.js` file provides React hooks for API state management:

| Hook | Purpose |
|------|---------|
| `useAPI` | Generic hook with loading/error states, auto-fetch, and refetch |
| `useAuth` | Authentication state management (user, login, logout, register) |
| `useStaffing` | Staffing data management (summary, employees, create, layoff, bulk upload) |
| `useRequests` | Employee request management (fetch, approve, decline with auto-refetch) |
- Failed refresh clears all stored data and redirects to login
- Tokens stored in `localStorage`: `access_token`, `refresh_token`, `org_id`, `user_id`

---

## Database Schema

PostgreSQL 12.4 with **23 SQL migrations** managed by Goose v3. Migrations run automatically on API server startup.

### Core Tables

| Table | Description |
|-------|-------------|
| `organizations` | Multi-tenant orgs with branding (name, address, hex colors) |
| `users` | Employees with role (admin/manager/employee), org FK, salary |
| `organizations_roles` | Custom roles per org (role name, min_needed, items_per_hour) |
| `schedules` | Generated shift schedules |
| `orders` | Historical order records |
| `delivery` | Delivery tracking |
| `marketing_campaigns` | Campaign history with discount/date ranges |
| `tables` | Restaurant table management |
| `layoffs_hirings` | Archived employee lifecycle events |
| `requests` | Employee time-off requests (calloff/holiday/resign) |
| `preferences` | Employee shift preferences and constraints |
| `demand` | Stored demand predictions |
| `production_chains` | Production chain tracking |
| `offers` | Special offers |
| `offers` | Shift offers for employees |

### Migration Files

```
app/api/migrations/
├── 00001_organizations.sql
├── 00002_users.sql
├── 00003_schedules.sql
├── 00004_orders.sql
├── 00005_delivery.sql
├── 00006_marketing_campaigns.sql
├── 00007_tables.sql
├── 00008_layoffs_hirings.sql
├── 00009_organizations_managers.sql
├── 00010_requests.sql
├── 00011_preferences.sql
├── 00012_drop_organizations_managers.sql
├── 00013_create_demand_table.sql
├── 00014_production_chains.sql
├── 00015_offers_table.sql
├── 00016_update_users_table.sql
├── 00017_alerts.sql
├── 00018_add_shift_times.sql
├── 00019_update_organizations.sql
├── 00020_move_accepting_orders.sql
├── 00021_fix_demand_day_constraint.sql
├── 00022_drop_alerts_table.sql
├── 00023_drop_schedule_check.sql
└── fs.go                              # Embedded filesystem
```

---

## Installation & Setup

### Prerequisites

- **Docker** and **Docker Compose** installed
- Ports 80, 3000, 5432, 6379, 8000, 8080 available

### Quick Start

```bash
# 1. Clone the repository
git clone <repository-url>
cd AntiClockWise

# 2. Create .env file (see Environment Variables section below)
cp .env.example .env   # or create manually

# 3. Start all 6 services
docker-compose up -d --build

# 4. Verify everything is running
docker-compose ps

# 5. The application is available at:
#    Frontend:  http://localhost       (via Nginx)
#    API:       http://localhost/api/  (via Nginx → Go backend)
#    Health:    http://localhost/health
```

### What Happens on Startup

1. PostgreSQL starts with a persistent volume (`postgres-data`)
2. Redis starts with append-only persistence (`redis-data`)
3. Go backend starts, runs all 23 database migrations automatically, connects to Redis
4. ML service loads the CatBoost model and starts the FastAPI server
5. React dev server starts on port 3000
6. Nginx starts and proxies: `/api/*` → Go backend, `/*` → React frontend

### Running Without Docker (Development)

```bash
# Start supporting services only
docker-compose up -d db redis cw-ml-service

# Backend (Go)
cd app/api
DB_HOST=localhost REDIS_ADDR=localhost:6379 go run cmd/api/main.go

# Frontend (React)
cd web
npm install
REACT_APP_API_BASE_URL=http://localhost:8080 npm start

# ML Service (Python)
cd app/ml
pip install -r requirements.txt
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

---

## Environment Variables

Create a `.env` file in the project root:

```env
# ─── Nginx ───
NGINX_PORT=80

# ─── Backend API ───
PORT=8080
HOST=localhost

# ─── Database ───
DB_HOST=db
DB_PORT=5432
POSTGRES_DB=AntiClockWise
POSTGRES_USER=AntiClockWise
POSTGRES_PASSWORD=<your_password>
DB_SCHEMA=public

# ─── Redis ───
REDIS_ADDR=redis:6379
REDIS_PASSWORD=<your_password>

# ─── Authentication ───
JWT_SECRET=<your_secret_key>

# ─── Email (SMTP) ───
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=<your_email>
SMTP_PASSWORD=<your_app_password>

# ─── ML Service ───
ML_PORT=8000
ML_HOST=localhost
ML_URL=http://cw-ml-service:8000

# ─── External APIs (ML) ───
TWITTER_BEARER_TOKEN=<your_token>      # Surge detection social signals
EVENTBRITE_API_KEY=<your_key>          # Event-based surge detection
GEMINI_API_KEY=<your_key>              # Optional LLM surge analysis

# ─── Frontend ───
WEB_PORT=3000
WEB_HOST=cw-web
```

---

## API Documentation

### Backend REST API

Comprehensive documentation with full request/response examples for all endpoints:

**[`app/api/docs/API_DOCUMENTATION.md`](app/api/docs/API_DOCUMENTATION.md)** (3000+ lines)

Endpoint categories:
| Category | Key Endpoints |
|----------|--------------|
| **Health** | `GET /health`, `GET /ml/health` |
| **Auth** | `POST /api/login`, `POST /api/register`, `POST /api/auth/refresh`, `POST /api/auth/logout`, `GET /api/auth/me` |
| **Profile** | `GET /api/auth/profile`, `POST /api/auth/profile/changepassword` |
| **Staffing** | `GET/POST /:org/staffing`, `POST /:org/staffing/upload`, `GET /:org/staffing/employees` |
| **Employees** | `GET/DELETE /:org/staffing/employees/:id/*` |
| **Roles** | `GET/POST/PUT/DELETE /:org/roles` |
| **Rules** | `GET/POST /:org/rules` |
| **Preferences** | `GET/POST /:org/preferences` |
| **Orders** | `GET /:org/orders/*`, `POST /:org/orders/upload/*` |
| **Deliveries** | `GET /:org/deliveries/*`, `POST /:org/deliveries/upload` |
| **Items** | `GET /:org/items/*`, `POST /:org/items/upload` |
| **Campaigns** | `GET /:org/campaigns/*`, `POST /:org/campaigns/upload/*`, `POST /:org/campaigns/recommend`, `POST /:org/campaigns/feedback` |
| **Dashboard** | `GET/POST /:org/dashboard/demand/*` |
| **Schedule** | `GET /:org/dashboard/schedule/*`, `POST /:org/dashboard/schedule/predict` |
| **Insights** | `GET /:org/insights` |
| **Surge** | `POST /api/surge/bulk-data`, `GET /api/surge/users`, `GET /api/venues/active` |
| **Offers** | `GET /:org/offers`, `POST /:org/offers/accept`, `POST /:org/offers/decline` |

### ML Service API

Unified ML API documentation with schemas for all ML endpoints:

**[`app/api/docs/data.md`](app/api/docs/data.md)** (1350+ lines)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `GET /` | GET | Health check & feature availability |
| `GET /model/info` | GET | Model metadata & hyperparameters |
| `POST /predict/demand` | POST | Hourly demand prediction (items + orders) |
| `POST /predict/schedule` | POST | Optimal staff schedule generation |
| `POST /recommend/campaigns` | POST | AI campaign recommendations |
| `POST /recommend/campaigns/feedback` | POST | Campaign feedback for online learning |
| `POST /api/v1/collect/venue` | POST | Single venue surge metrics |
| `POST /api/v1/collect/batch` | POST | Batch venue surge metrics |

---

## Development

### Docker Commands

```bash
# Start all services
docker-compose up -d

# Rebuild and start
docker-compose up -d --build

# View logs (all services)
docker-compose logs -f

# View specific service logs
docker-compose logs -f cw-app
docker-compose logs -f cw-ml-service

# Restart a single service
docker-compose restart cw-app

# Stop all services
docker-compose down

# Stop and remove volumes (destructive)
docker-compose down -v

# Access database shell
docker exec -it AntiClockWiseDB psql -U AntiClockWise -d AntiClockWise

# Access Redis CLI
docker exec -it AntiClockWiseRedis redis-cli
```

### Running Backend Tests

```bash
cd app/api

# Run all tests
go test ./...

# Run with coverage
go test -cover ./...

# Run specific package tests
go test ./internal/api/tests/...
go test ./internal/database/tests/...

# Verbose output
go test -v ./...
```

The test suite uses `go-sqlmock` for unit tests and `testcontainers-go` for integration tests with real PostgreSQL containers.

### Test Data Generation

```bash
# Generate test data for the application
python scripts/generate_test_data.py
```

### CSV Upload Formats

**Employees** (`POST /:org/staffing/upload`):
```csv
full_name,email,role
John Doe,john@example.com,employee
Jane Smith,jane@example.com,manager
```

**Orders** (`POST /:org/orders/upload/orders`):
```csv
time,items,status,total_amount,discount_amount
2024-01-15T12:30:00,3,completed,45.50,5.00
```

**Campaigns** (`POST /:org/campaigns/upload`):
```csv
start_time,end_time,discount,items_included
2024-01-10T00:00:00,2024-01-17T23:59:59,15.0,"pizza,cola"
```

---

## Project Structure

```
AntiClockWise/
├── .env                                # Environment configuration
├── docker-compose.yml                  # 6-service orchestration
├── README.md                           # This file
│
├── app/
│   ├── api/                            # ─── GO BACKEND ───
│   │   ├── Dockerfile                  # Multi-stage Go build
│   │   ├── go.mod                      # Go 1.25.5 dependencies
│   │   ├── go.sum
│   │   ├── cmd/
│   │   │   └── api/
│   │   │       └── main.go            # Entry point, graceful shutdown
│   │   ├── internal/
│   │   │   ├── api/                   # HTTP handlers
│   │   │   │   ├── org_handler.go
│   │   │   │   ├── staffing_handler.go
│   │   │   │   ├── employee_handler.go
│   │   │   │   ├── schedule_handler.go
│   │   │   │   ├── dashboard_handler.go
│   │   │   │   ├── campaign_handler.go
│   │   │   │   ├── orders_handler.go
│   │   │   │   ├── roles_handler.go
│   │   │   │   ├── rules_handler.go
│   │   │   │   ├── preferences_handler.go
│   │   │   │   ├── profile_handler.go
│   │   │   │   ├── insights_handler.go
│   │   │   │   ├── offers_handlers.go
│   │   │   │   ├── surge_handler.go
│   │   │   │   └── tests/            # Handler unit tests
│   │   │   ├── database/             # Data access stores
│   │   │   │   ├── database.go       # Connection pool & health
│   │   │   │   ├── org_store.go
│   │   │   │   ├── user_store.go
│   │   │   │   ├── order_store.go
│   │   │   │   ├── campaign_store.go
│   │   │   │   ├── schedule_store.go
│   │   │   │   ├── roles_store.go
│   │   │   │   ├── rules_store.go
│   │   │   │   ├── preferences_store.go
│   │   │   │   ├── request_store.go
│   │   │   │   ├── demand_store.go
│   │   │   │   ├── operating_hours_store.go
│   │   │   │   ├── insight_store.go
│   │   │   │   ├── user_roles_store.go
│   │   │   │   ├── offer_store.go
│   │   │   │   ├── surge_store.go
│   │   │   │   └── tests/
│   │   │   ├── cache/                # Redis cache wrappers
│   │   │   ├── middleware/
│   │   │   │   └── middleware.go     # JWT auth, org validation
│   │   │   ├── server/
│   │   │   │   ├── server.go         # DI, initialization
│   │   │   │   └── routes.go         # Route registration
│   │   │   ├── service/
│   │   │   │   ├── email_service.go  # SMTP (with mock fallback)
│   │   │   │   └── uploadcsv_service.go
│   │   │   └── utils/
│   │   │       └── utils.go          # Password generation
│   │   ├── migrations/               # 23 SQL migrations
│   │   │   ├── 00001_organizations.sql
│   │   │   ├── ...
│   │   │   ├── 00023_drop_schedule_check.sql
│   │   │   └── fs.go                 # Embedded filesystem
│   │   └── docs/
│   │       ├── API_DOCUMENTATION.md  # Full REST API docs
│   │       └── data.md               # ML API docs
│   │
│   └── ml/                            # ─── PYTHON ML SERVICE ───
│       ├── Dockerfile
│       ├── requirements.txt           # Python dependencies
│       ├── README.md
│       ├── data.md
│       ├── api/                       # FastAPI application
│       │   ├── main.py
│       │   └── campaign_models.py
│       ├── src/
│       │   ├── deploy_model.py        # Model loading & prediction API
│       │   ├── train_model.py         # CatBoost training pipeline
│       │   ├── feature_engineering.py # Training feature engineering
│       │   ├── api_feature_engineering.py  # API-time feature engineering
│       │   ├── v6_features.py         # V6 69-feature pipeline
│       │   ├── prediction_utils.py    # Prediction helpers
│       │   ├── scheduler_cpsat.py     # CP-SAT schedule solver
│       │   ├── campaign_analyzer.py   # Campaign performance analysis
│       │   ├── campaign_recommender.py # Thompson Sampling recommender
│       │   ├── train_campaign_model.py # XGBoost campaign model training
│       │   ├── data_collector.py      # Surge data collection
│       │   ├── surge_detector.py      # Surge detection logic
│       │   ├── surge_orchestrator.py  # Surge system orchestration
│       │   ├── surge_api.py           # Surge API endpoints
│       │   ├── alert_system.py        # Multi-channel alert delivery
│       │   ├── social_media_apis.py   # Twitter/Google Trends APIs
│       │   ├── weather_api.py         # Weather data integration
│       │   ├── holiday_api.py         # Holiday detection
│       │   ├── model_monitor.py       # Performance tracking
│       │   ├── fine_tune_model.py     # Incremental model updates
│       │   ├── model_manager.py       # Hybrid training lifecycle
│       │   ├── llm_analyzer_gemini.py # Optional Gemini LLM analysis
│       │   ├── config.py             # Configuration management
│       │   └── email_sender.py       # Email sending utility
│       ├── data/                      # Training data & models
│       ├── notebooks/                 # Jupyter analysis notebooks
│       ├── tests/                     # ML test suite
│       ├── logs/                      # Prediction & performance logs
│       └── docs/                      # ML documentation
│           ├── Documentation.md       # System overview
│           ├── DEMAND_PREDICTION_MODEL.md
│           ├── V6_MODEL_INTEGRATION.md
│           ├── DEVELOPMENT_HISTORY.md
│           ├── scheduler_api_usage.md
│           ├── surge_detection_architecture.md
│           ├── SURGE_ORCHESTRATION_GUIDE.md
│           ├── DATA_COLLECTION_API.md
│           ├── CAMPAIGN_RECOMMENDER.md
│           ├── MODEL_MAINTENANCE.md
│           └── problem.md
│
├── web/                                # ─── REACT FRONTEND ───
│   ├── Dockerfile
│   ├── package.json                   # React 18.3 + React Router 7
│   ├── public/
│   │   └── index.html
│   └── src/
│       ├── index.js                   # Router setup (/, /admin, /manager, /employee)
│       ├── App.jsx                    # Landing page with Login/Signup modals
│       ├── Login.jsx                  # Login modal component
│       ├── Signup.jsx                 # Registration modal component
│       ├── ProtectedRoute.jsx         # JWT-based route guard
│       ├── AdminDashboard.jsx         # Admin dashboard (full control)
│       ├── ManagerDashboard.jsx       # Manager dashboard
│       ├── EmployeeDashboard.jsx      # Employee dashboard
│       ├── services/
│       │   ├── api.js                 # API client (1092 lines, 15 modules)
│       │   └── hooks.js              # Custom hooks (useAPI, useAuth, useStaffing, useRequests)
│       ├── *.css                      # Component stylesheets
│       ├── Fonts/                     # Custom Ranade font family
│       ├── Icons/                     # UI icons
│       └── PICs/                      # Static images
│
├── nginx/
│   └── nginx.conf                     # Reverse proxy configuration
│
├── scripts/
│   └── generate_test_data.py          # Test data generation
│
└── test-data/                         # Sample CSV data files
```

---

## Nginx Configuration

The Nginx reverse proxy provides:

- **Routing**: `/api/*` → Go backend (port 8080), `/*` → React frontend (port 3000)
- **Rate Limiting**: 10 req/s per IP with burst of 20 (on API routes)
- **Security Headers**: `X-Frame-Options`, `X-Content-Type-Options`, `X-XSS-Protection`, `Referrer-Policy`
- **Gzip Compression**: Enabled for JSON, JS, CSS, HTML, SVG, fonts
- **WebSocket Support**: Upgrade headers for React hot-reload
- **Client Upload Limit**: 20MB max body size
- **Health Endpoints**: `/health` and `/ml/health` (no rate limiting)

---

## Team Members

### Backend Development
- **Mohamed Hany**
- **Ziad Eliwa**

### Machine Learning
- **Fares Osama**
- **Hazem Nasr**

### Frontend Development
- **Mostafa Mohamed**

---

## License

MIT License

Copyright (c) 2026 AntiClockWise Team

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
