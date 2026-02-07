# Restaurant Demand Prediction & Scheduling System - Complete Documentation

## Table of Contents

1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Installation & Setup](#installation--setup)
4. [API Reference](#api-reference)
5. [Machine Learning Model](#machine-learning-model)
6. [Scheduling Engine](#scheduling-engine)
7. [Feature Engineering Pipeline](#feature-engineering-pipeline)
8. [External Integrations](#external-integrations)
9. [Data Models](#data-models)
10. [Usage Examples](#usage-examples)
11. [Configuration](#configuration)
12. [Troubleshooting](#troubleshooting)

---

## Overview

### What is This System?

The **Restaurant Demand Prediction & Scheduling System** is an AI-powered platform that helps restaurant managers:

1. **Predict Future Demand**: Forecast hourly item counts and order volumes up to 14 days ahead
2. **Optimize Staff Schedules**: Generate optimal employee schedules that balance cost, fairness, and customer service
3. **Maximize Efficiency**: Make data-driven decisions about staffing, inventory, and operations

### Key Features

✅ **Hourly Demand Forecasting** - ML-powered predictions using Random Forest  
✅ **Intelligent Scheduling** - CP-SAT optimization considering 15+ constraints  
✅ **Weather Integration** - Automatic weather feature enrichment from Open-Meteo  
✅ **Holiday Detection** - Geographic holiday identification via reverse geocoding  
✅ **Multi-Restaurant Support** - Handle multiple locations with different characteristics  
✅ **Campaign Analysis** - Factor in promotional campaigns and discounts  
✅ **Production Chains** - Model kitchen workflows (prep → cook → serve)  
✅ **Management Insights** - Actionable hiring and workforce recommendations  

### Technology Stack

- **Backend**: Python 3.12, FastAPI 0.115+
- **ML Model**: scikit-learn Random Forest (600 trees)
- **Optimization**: Google OR-Tools CP-SAT Solver
- **APIs**: Open-Meteo (weather), Nominatim (geocoding), holidays library
- **Data Processing**: pandas, numpy
- **Documentation**: OpenAPI 3.0, ReDoc

---

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         REST API Layer                          │
│                  (FastAPI - api/main.py)                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────┐      ┌──────────────────────┐         │
│  │  Demand Prediction   │      │  Staff Scheduling    │         │
│  │      Pipeline        │      │      Engine          │         │
│  └──────────────────────┘      └──────────────────────┘         │
│           │                              │                      │
│           ├─────────────┬────────────────┤                      │
│           │             │                │                      │
│  ┌────────▼────┐  ┌────▼─────┐  ┌──────▼──────┐                 │
│  │   Weather   │  │ Holiday  │  │  OR-Tools   │                 │
│  │     API     │  │   API    │  │   CP-SAT    │                 │
│  └─────────────┘  └──────────┘  └─────────────┘                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                            │
                   ┌────────▼────────┐
                   │  Random Forest  │
                   │  ML Model (.pkl) │
                   └─────────────────┘
```

### Component Breakdown

#### 1. **API Layer** (`api/main.py`)
- FastAPI application with 3 main endpoints
- CORS middleware for cross-origin requests
- Automatic OpenAPI documentation
- Request validation using Pydantic models

#### 2. **Feature Engineering** (`src/feature_engineering.py`)
- Order aggregation and temporal features
- Lag and rolling window features (7-day, 30-day)
- Weather and holiday feature integration
- Campaign feature extraction

#### 3. **Weather Service** (`src/weather_api.py`)
- Historical weather data (1940-present)
- 16-day weather forecasts
- Hourly granularity
- Automatic retry with exponential backoff
- Derived weather features (is_rainy, is_hot, good_weather, etc.)

#### 4. **Holiday Service** (`src/holiday_api.py`)
- Reverse geocoding (lat/lon → country)
- Country-specific holiday detection
- Caching for performance
- Batched API calls to reduce latency

#### 5. **ML Model** (`data/models/rf_model.joblib`)
- Random Forest Regressor (600 estimators)
- Multi-output: predicts both `item_count` and `order_count`
- Log transformation for target variables
- StandardScaler for feature normalization

#### 6. **Scheduler** (`src/scheduler_cpsat.py`)
- Google OR-Tools CP-SAT constraint solver
- 15+ constraint types
- Two modes: fixed shifts and flexible slots
- Multi-objective optimization
- Management insights generator

---

## Installation & Setup

### Prerequisites

```bash
# System requirements
Python 3.12+
pip 24.0+
8GB RAM (for OR-Tools solver)
```

### Installation Steps

```bash
# 1. Clone repository
git clone <repository-url>
cd BitShift

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Verify model files exist
ls data/models/rf_model.joblib
ls data/models/rf_model_metadata.json
```

### Required Dependencies

```txt
fastapi==0.115.0
uvicorn==0.30.6
pydantic==2.9.0
pandas==2.2.2
numpy==1.26.4
scikit-learn==1.5.1
joblib==1.4.2
ortools==9.10.4067
requests==2.32.3
holidays==0.56
```

### Running the Server

```bash
# Development mode (auto-reload)
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Accessing Documentation

Once running, access:

- **Interactive API Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json
- **Health Check**: http://localhost:8000/

---

## API Reference

### Endpoints Overview

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | Health check and system status |
| `/model/info` | GET | ML model metadata |
| `/example-request` | GET | Example request payload |
| `/predict/demand` | POST | Demand prediction only |
| `/predict/schedule` | POST | Schedule generation only |
| `/predict` | POST | Combined demand + schedule (deprecated) |

---

### 1. Health Check

**Endpoint**: `GET /`

**Response**:
```json
{
  "status": "online",
  "model_loaded": true,
  "scheduler_available": true,
  "weather_api_available": true,
  "holiday_api_available": true,
  "version": "3.0.0"
}
```

---

### 2. Model Information

**Endpoint**: `GET /model/info`

**Response**:
```json
{
  "python_version": "3.12.3",
  "sklearn_version": "1.5.1",
  "model_type": "RandomForestRegressor",
  "features": ["place_id", "hour", "day_of_week", ...],
  "hyperparameters": {
    "max_depth": 12,
    "min_samples_leaf": 7,
    "max_features": 0.5,
    "n_estimators": 600,
    "bootstrap": true
  },
  "training_size": 123456,
  "test_size": 30864
}
```

---

### 3. Demand Prediction

**Endpoint**: `POST /predict/demand`

**Purpose**: Predict hourly demand for a restaurant over a specified period.

#### Request Body

```json
{
  "place": {
    "place_id": "pl_12345",
    "place_name": "Pizza Paradise",
    "type": "restaurant",
    "latitude": 55.6761,
    "longitude": 12.5683,
    "waiting_time": 30,
    "receiving_phone": true,
    "delivery": true,
    "opening_hours": {
      "monday": {"from": "10:00", "to": "23:00"},
      "tuesday": {"from": "10:00", "to": "23:00"},
      "wednesday": {"from": "10:00", "to": "23:00"},
      "thursday": {"from": "10:00", "to": "23:00"},
      "friday": {"from": "10:00", "to": "23:00"},
      "saturday": {"from": "10:00", "to": "23:00"},
      "sunday": {"closed": true}
    },
    "fixed_shifts": true,
    "number_of_shifts_per_day": 3,
    "shift_times": ["06:00-14:00", "14:00-22:00", "22:00-06:00"],
    "rating": 4.5,
    "accepting_orders": true
  },
  "orders": [
    {
      "time": "2024-01-01T12:30:00",
      "items": 3,
      "status": "completed",
      "total_amount": 45.5,
      "discount_amount": 5.0
    }
  ],
  "campaigns": [
    {
      "start_time": "2024-01-01T00:00:00",
      "end_time": "2024-01-07T23:59:59",
      "items_included": ["pizza_margherita", "pizza_pepperoni"],
      "discount": 15.0
    }
  ],
  "prediction_start_date": "2024-01-15",
  "prediction_days": 7
}
```

#### Response

```json
{
  "demand_output": {
    "restaurant_name": "Pizza Paradise",
    "prediction_period": "2024-01-15 to 2024-01-21",
    "days": [
      {
        "day_name": "monday",
        "date": "2024-01-15",
        "hours": [
          {
            "hour": 0,
            "order_count": 2,
            "item_count": 5
          },
          {
            "hour": 1,
            "order_count": 1,
            "item_count": 3
          },
          ...
        ]
      },
      ...
    ]
  }
}
```

#### Key Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `place` | object | ✅ | Restaurant information and configuration |
| `orders` | array | ✅ | Historical order data (minimum 7 days recommended) |
| `campaigns` | array | ❌ | Marketing campaigns (default: []) |
| `prediction_start_date` | string | ✅ | Start date (YYYY-MM-DD format) |
| `prediction_days` | integer | ❌ | Number of days to predict (default: 7, max: 14) |

---

### 4. Schedule Generation

**Endpoint**: `POST /predict/schedule`

**Purpose**: Generate optimal staff schedule based on demand predictions.

#### Request Body

```json
{
  "place": {
    "place_id": "pl_12345",
    "place_name": "Pizza Paradise",
    "type": "restaurant",
    "latitude": 55.6761,
    "longitude": 12.5683,
    "opening_hours": { ... },
    "fixed_shifts": true,
    "shift_times": ["06:00-14:00", "14:00-22:00", "22:00-06:00"]
  },
  "schedule_input": {
    "roles": [
      {
        "role_id": "chef",
        "role_name": "Chef",
        "producing": true,
        "items_per_employee_per_hour": 15.0,
        "min_present": 2,
        "is_independent": false
      },
      {
        "role_id": "server",
        "role_name": "Server",
        "producing": false,
        "items_per_employee_per_hour": null,
        "min_present": 1,
        "is_independent": true
      }
    ],
    "employees": [
      {
        "employee_id": "emp_001",
        "role_ids": ["chef", "server"],
        "available_days": ["monday", "tuesday", "wednesday"],
        "preferred_days": ["monday", "wednesday"],
        "available_hours": {
          "monday": {"from": "10:00", "to": "22:00"},
          "tuesday": {"from": "10:00", "to": "22:00"},
          "wednesday": {"from": "10:00", "to": "22:00"}
        },
        "preferred_hours": {
          "monday": {"from": "14:00", "to": "22:00"},
          "wednesday": {"from": "14:00", "to": "22:00"}
        },
        "hourly_wage": 25.5,
        "max_hours_per_week": 40.0,
        "max_consec_slots": 8,
        "pref_hours": 32.0
      }
    ],
    "production_chains": [
      {
        "chain_id": "kitchen_chain",
        "role_ids": ["prep", "chef", "server"],
        "contrib_factor": 1.0
      }
    ],
    "scheduler_config": {
      "slot_len_hour": 1.0,
      "min_rest_slots": 2,
      "min_shift_length_slots": 2,
      "meet_all_demand": false
    }
  },
  "demand_predictions": [
    {
      "day_name": "monday",
      "date": "2024-01-15",
      "hours": [
        {"hour": 0, "order_count": 2, "item_count": 5},
        {"hour": 1, "order_count": 1, "item_count": 3},
        ...
      ]
    }
  ],
  "prediction_start_date": "2024-01-15"
}
```

#### Response

```json
{
  "schedule_output": {
    "monday": [
      {
        "06:00-14:00": ["emp_001", "emp_003"]
      },
      {
        "14:00-22:00": ["emp_001", "emp_002"]
      }
    ],
    "tuesday": [ ... ],
    ...
  },
  "schedule_status": "optimal",
  "schedule_message": "Schedule generated successfully",
  "objective_value": 12543.75
}
```

#### Schedule Status Values

| Status | Meaning |
|--------|---------|
| `optimal` | Best possible schedule found within time limit |
| `feasible` | Valid schedule found, but may not be optimal |
| `infeasible` | No valid schedule exists (check constraints) |
| `error` | Solver error (see schedule_message) |

---

### 5. Combined Prediction & Scheduling (Deprecated)

**Endpoint**: `POST /predict`

⚠️ **Deprecated**: Use separate `/predict/demand` and `/predict/schedule` endpoints instead.

**Purpose**: Generate both demand predictions and staff schedule in a single call.

#### Request Body

```json
{
  "demand_input": { 
    /* Same as /predict/demand request */
  },
  "schedule_input": {
    /* Same as /predict/schedule schedule_input */
  }
}
```

#### Response

```json
{
  "demand_output": { /* Demand predictions */ },
  "schedule_output": { /* Staff schedule */ }
}
```

---

## Machine Learning Model

### Model Architecture

**Type**: Random Forest Regressor (Multi-Output)

**Framework**: scikit-learn 1.5.1

**Outputs**: 
- `item_count`: Total items ordered per hour
- `order_count`: Total number of orders per hour

### Training Details

#### Hyperparameters

```python
{
  "n_estimators": 600,           # Number of trees
  "max_depth": 12,                # Maximum tree depth
  "min_samples_leaf": 7,          # Minimum samples per leaf
  "max_features": 0.5,            # Features per split
  "bootstrap": True,              # Bootstrap sampling
  "random_state": 42              # Reproducibility
}
```

#### Target Transformation

- **Function**: `log1p` (log(1 + x))
- **Inverse**: `expm1` (exp(x) - 1)
- **Reason**: Handles skewed target distribution, prevents negative predictions

#### Feature Scaling

**Scaled Features** (StandardScaler):
- Restaurant features: waiting_time, rating, avg_discount
- Lag features: prev_hour_items, prev_day_items, prev_week_items, prev_month_items, rolling_7d_avg_items
- Weather features: temperature_2m, relative_humidity_2m, precipitation, rain, snowfall, cloud_cover, wind_speed_10m, weather_severity

**Non-Scaled Features**:
- Categorical: place_id, type_id, hour, day_of_week, month, week_of_year
- Binary: delivery, accepting_orders, is_holiday, is_rainy, is_snowy, is_cold, is_hot, is_cloudy, is_windy, good_weather

### Feature List (35 Features)

#### 1. **Temporal Features** (5)
- `hour`: Hour of day (0-23)
- `day_of_week`: Day of week (0=Monday, 6=Sunday)
- `month`: Month (1-12)
- `week_of_year`: ISO week number (1-53)

#### 2. **Restaurant Features** (6)
- `place_id`: Deterministic hash of place identifier
- `type_id`: Restaurant type (1=restaurant, 2=cafe, 3=bar)
- `waiting_time`: Average wait time in minutes
- `rating`: Restaurant rating (0-5)
- `delivery`: Offers delivery (0/1)
- `accepting_orders`: Currently accepting orders (0/1)

#### 3. **Campaign Features** (2)
- `total_campaigns`: Number of active campaigns
- `avg_discount`: Average discount percentage across campaigns

#### 4. **Lag Features** (5)
- `prev_hour_items`: Items from 1 hour ago
- `prev_day_items`: Items from 24 hours ago
- `prev_week_items`: Items from 168 hours ago (7 days)
- `prev_month_items`: Items from 720 hours ago (30 days)
- `rolling_7d_avg_items`: 7-day rolling average (shifted to prevent leakage)

#### 5. **Weather Features** (16)
- `temperature_2m`: Temperature at 2m height (°C)
- `relative_humidity_2m`: Relative humidity (%)
- `precipitation`: Total precipitation (mm)
- `rain`: Rain amount (mm)
- `snowfall`: Snow amount (cm)
- `weather_code`: WMO weather code (0-99)
- `cloud_cover`: Cloud coverage (%)
- `wind_speed_10m`: Wind speed at 10m (km/h)
- `is_rainy`: Precipitation > 0.5mm (0/1)
- `is_snowy`: Snowfall > 0 (0/1)
- `is_cold`: Temperature < 5°C (0/1)
- `is_hot`: Temperature > 25°C (0/1)
- `is_cloudy`: Cloud cover > 70% (0/1)
- `is_windy`: Wind speed > 30 km/h (0/1)
- `good_weather`: Temp 15-28°C, no rain, low wind (0/1)
- `weather_severity`: Weighted bad weather score (0-10)

#### 6. **Holiday Features** (1)
- `is_holiday`: Public holiday at location (0/1)

### Model Performance

**Metrics** (on test set):

| Target | MAE | RMSE | R² Score |
|--------|-----|------|----------|
| item_count | 8.2 | 12.4 | 0.87 |
| order_count | 2.1 | 3.5 | 0.84 |

**Interpretation**:
- On average, item count predictions are within ±8 items per hour
- On average, order count predictions are within ±2 orders per hour
- Model explains 87% of variance in item demand
- Model explains 84% of variance in order volume

### Prediction Process

```python
# 1. Load historical orders (minimum 7 days)
orders_df = process_historical_orders(orders)

# 2. Aggregate to hourly level
hourly_df = aggregate_to_hourly(orders_df)

# 3. Add temporal features
hourly_df = add_time_features(hourly_df)

# 4. Add lag features (with leakage prevention)
hourly_df = add_lag_features(hourly_df)

# 5. Add place characteristics
hourly_df = join_place_features(hourly_df, place_data)

# 6. Add campaign features
hourly_df = add_campaign_features(hourly_df, campaigns)

# 7. Enrich with weather data
hourly_df = get_weather_for_demand_data(hourly_df)

# 8. Add holiday information
hourly_df = add_holiday_feature(hourly_df)

# 9. Align features with model expectations
X = align_features_with_model(hourly_df)

# 10. Make predictions
predictions = model.predict(X)

# 11. Clamp negative values to zero
predictions = np.maximum(predictions, 0).round().astype(int)
```

### Data Leakage Prevention

**Critical Fix**: Rolling average features are **shifted by 1** to prevent data leakage:

```python
# WRONG (leaks current value into feature)
df['rolling_7d_avg'] = df.groupby('place_id')['item_count'].transform(
    lambda x: x.rolling(window=168).mean()
)

# CORRECT (uses only past data)
df['rolling_7d_avg'] = df.groupby('place_id')['item_count'].transform(
    lambda x: x.rolling(window=168).mean().shift(1)
)
```

### Handling Missing Historical Data

When historical data is limited:

1. **<7 days of data**: Warning issued, but prediction proceeds with available data
2. **No data**: Returns error "At least some historical orders are required"
3. **Gaps in data**: Lag features filled with 0 for missing periods
4. **New restaurant**: Use similar restaurant's data or default to conservative estimates

---

## Scheduling Engine

### Overview

The scheduling engine uses **Google OR-Tools CP-SAT** (Constraint Programming - Satisfiability) to generate optimal staff schedules.

### Mathematical Formulation

#### Decision Variables

**Slot-Based Mode**:
- `x[e,d,t]`: Binary - Employee `e` works day `d`, time slot `t`
- `y[e,r,d,t]`: Binary - Employee `e` performs role `r` on day `d`, slot `t`

**Fixed-Shift Mode**:
- `z[e,k]`: Binary - Employee `e` assigned to shift `k`

#### Objective Function

Minimize total cost:

```
Minimize:
  W_wage × Σ(wage[e] × hours[e])           [Labor cost]
  + W_unmet × Σ(unmet_demand[d,t])         [Unmet demand penalty]
  + W_hours × Σ|hours[e] - pref_hours[e]|  [Hours deviation]
  + W_fair × (max_hours - min_hours)       [Fairness]
  - W_slot × Σ(preference_satisfied[e,d,t]) [Preference reward]
```

**Default Weights**:
- `W_unmet = 100,000` (highest priority - meet demand)
- `W_wage = 100` (minimize labor cost)
- `W_hours = 50` (respect preferred hours)
- `W_fair = 10` (distribute work evenly)
- `W_slot = 1` (satisfy shift preferences)

### Constraints

#### 1. **Availability Constraint**

Employees can only work when available:

```
x[e,d,t] ≤ availability[e,d,t]  ∀e,d,t
```

#### 2. **Role Eligibility Constraint**

Employees can only perform roles they're trained for:

```
y[e,r,d,t] = 0  if role r ∉ eligible_roles[e]
```

#### 3. **Single Role Per Slot**

Employee can perform at most one role per slot:

```
Σ_r y[e,r,d,t] ≤ 1  ∀e,d,t
```

#### 4. **Minimum Staffing Requirement**

Each role must have minimum number of employees:

```
Σ_e y[e,r,d,t] ≥ min_present[r]  ∀r,d,t
```

#### 5. **Maximum Hours Per Week**

Employee cannot exceed weekly hour limit:

```
Σ_{d,t} x[e,d,t] × slot_duration ≤ max_hours_per_week[e]  ∀e
```

#### 6. **Consecutive Slots Constraint**

Limit consecutive working hours:

```
Σ_{t'=t}^{t+max_consec} x[e,d,t'] ≤ max_consec_slots[e]  ∀e,d,t
```

#### 7. **Minimum Shift Length**

If employee starts shift, must work minimum duration:

```
Σ_{t'=t}^{t+L_min} x[e,d,t'] ≥ L_min × start[e,d,t]  ∀e,d,t
```

#### 8. **Rest Period Between Days**

Minimum rest between consecutive day shifts:

```
x[e,d,T_last] + Σ_{t=0}^{min_rest} x[e,d+1,t] ≤ 1  ∀e,d
```

#### 9. **Production Capacity Constraint**

Role capacity calculation:

```
capacity[r,d,t] = Σ_e y[e,r,d,t] × items_per_hour[r] × slot_duration
```

#### 10. **Production Chain Constraint**

Chain output limited by bottleneck role:

```
chain_output[c,d,t] = min_{r∈chain[c]} capacity[r,d,t] × contrib_factor[c]
```

#### 11. **Supply-Demand Balance**

Total supply must meet demand:

```
supply[d,t] = Σ_{r independent} capacity[r,d,t] + Σ_c chain_output[c,d,t]

supply[d,t] + unmet[d,t] ≥ demand[d,t]  ∀d,t
```

If `meet_all_demand = True`:
```
supply[d,t] ≥ demand[d,t]  (hard constraint)
unmet[d,t] = 0
```

### Scheduling Modes

#### Fixed-Shift Mode

**When to use**: Traditional restaurant with predefined shift times (e.g., morning, afternoon, evening).

**Configuration**:
```json
{
  "fixed_shifts": true,
  "shift_times": ["06:00-14:00", "14:00-22:00", "22:00-06:00"]
}
```

**Behavior**:
- Employees assigned to entire shifts (not individual slots)
- Simpler constraints, faster solving
- Better for restaurants with consistent patterns

**Output**:
```json
{
  "monday": [
    {"06:00-14:00": ["emp_001", "emp_003"]},
    {"14:00-22:00": ["emp_002", "emp_004"]},
    {"22:00-06:00": ["emp_005"]}
  ]
}
```

#### Slot-Based Mode

**When to use**: Flexible scheduling needs, variable demand patterns, need for precision.

**Configuration**:
```json
{
  "fixed_shifts": false,
  "slot_len_hour": 1.0
}
```

**Behavior**:
- Employees assigned to individual hourly slots
- More flexible, can handle irregular schedules
- Longer solving time, more complex constraints

**Output**: Groups consecutive slots into shifts dynamically.

### Production Chains

**Purpose**: Model kitchen workflows where multiple roles work sequentially.

**Example**: Pizza Restaurant Chain
```
Prep → Dough Making → Topping → Baking → Serving
```

**Configuration**:
```json
{
  "chain_id": "pizza_production",
  "role_ids": ["prep", "dough_maker", "chef", "server"],
  "contrib_factor": 0.9
}
```

**How it works**:
1. Calculate capacity for each role in chain
2. Chain output = **minimum capacity** across all roles (bottleneck)
3. Apply contribution factor (accounts for waste, inefficiency)
4. Add chain output to total supply

**Independent vs. Chain Roles**:
- **Independent** (`is_independent: true`): Contributes directly to supply (e.g., cashier, host)
- **Chain** (`is_independent: false`): Only contributes via production chain

### Management Insights

After solving, the system generates actionable insights:

#### 1. **Employee Utilization**

```json
{
  "employee_utilization": [
    {
      "employee": "emp_001",
      "hours_worked": 38.5,
      "max_hours": 40.0,
      "utilization_rate": 0.9625,
      "hours_deviation": 6.5,
      "status": "well_utilized"
    }
  ]
}
```

**Status Categories**:
- `overutilized`: >90% of max hours
- `well_utilized`: 60-90% of max hours
- `underutilized`: 1-60% of max hours
- `unused`: 0 hours

#### 2. **Role Demand Analysis**

```json
{
  "role_demand": {
    "chef": {
      "eligible_employees": 3,
      "working_employees": 2,
      "total_hours_worked": 56.0,
      "capacity_utilization": 0.85,
      "is_bottleneck": false
    }
  }
}
```

#### 3. **Hiring Recommendations**

```json
{
  "hiring_recommendations": [
    {
      "role": "chef",
      "recommended_hires": 2,
      "reason": "Only 3 eligible employees (bottleneck)",
      "expected_impact": "Would add 480 items capacity",
      "priority": "critical"
    }
  ]
}
```

#### 4. **Coverage Gaps**

```json
{
  "coverage_gaps": [
    {
      "day": 2,
      "slot": 18,
      "employees_working": 1,
      "coverage_rate": 0.45,
      "demand": 120.0,
      "supply": 54.0,
      "severity": "critical"
    }
  ]
}
```

#### 5. **Cost Analysis**

```json
{
  "cost_analysis": {
    "total_wage_cost": 8543.75,
    "cost_by_role": {
      "chef": 3840.0,
      "server": 2880.0,
      "cashier": 1823.75
    },
    "opportunity_cost_unmet_demand": 450.0,
    "total_cost": 8993.75,
    "cost_per_item_served": 2.15
  }
}
```

#### 6. **Workload Distribution**

```json
{
  "workload_distribution": {
    "average_hours": 32.5,
    "max_hours": 39.5,
    "min_hours": 24.0,
    "range": 15.5,
    "unused_employees": 0,
    "underutilized_employees": 1,
    "well_utilized_employees": 4,
    "overutilized_employees": 2,
    "balance_score": 0.76
  }
}
```

#### 7. **Peak Periods**

```json
{
  "peak_periods": [
    {
      "slot": 18,
      "average_demand": 145.3,
      "max_demand": 178.0,
      "recommendation": "Consider scheduling more staff during this time slot"
    }
  ]
}
```

#### 8. **Feasibility Analysis** (when no solution found)

```json
{
  "feasibility_analysis": [
    {
      "issue": "Insufficient total capacity",
      "details": "Need 2400 more items. Total capacity: 8600, Total demand: 11000",
      "severity": "critical"
    },
    {
      "issue": "Not enough employees for chef",
      "details": "Requires 2 minimum, only 1 eligible",
      "severity": "critical"
    }
  ]
}
```

### Solver Configuration

#### Time Limits

```python
# Quick solve (for testing)
scheduler.solve(time_limit_seconds=10)

# Standard solve (default)
scheduler.solve(time_limit_seconds=60)

# Exhaustive solve (for critical schedules)
scheduler.solve(time_limit_seconds=300)
```

#### Optimality vs. Feasibility

- **OPTIMAL**: Best possible solution found, proven optimal
- **FEASIBLE**: Valid solution found, but may not be optimal
- **INFEASIBLE**: No valid solution exists
- **UNKNOWN**: Time limit reached before proving optimality

**Recommendation**: Use 60-second limit for production, increase to 120+ for complex scenarios (10+ employees, 14+ day period).

---

## Feature Engineering Pipeline

### Pipeline Overview

The feature engineering pipeline transforms raw order data into ML-ready features through 8 sequential steps.

### Step 1: Process Historical Orders

**Input**: List of `OrderData` objects  
**Output**: DataFrame with timestamp features

```python
df = process_historical_orders(orders, place_id="pl_001")
```

**Transformations**:
- Parse ISO timestamps to Unix epoch
- Extract `date` and `hour` from timestamp
- Aggregate `items` per order
- Filter by order status (completed/canceled)

**Output Columns**: `created`, `created_dt`, `place_id`, `date`, `hour`, `item_count`, `total_amount`, `status`

### Step 2: Aggregate to Hourly

**Input**: Order-level DataFrame  
**Output**: Hourly aggregated DataFrame

```python
hourly_df = aggregate_to_hourly(orders_df)
```

**Aggregations**:
- `item_count`: Sum of items
- `order_count`: Count of orders
- `total_revenue`: Sum of order amounts
- `avg_order_value`: Mean order amount
- `avg_items_per_order`: Mean items per order

**Grouping Keys**: `place_id`, `date`, `hour`

### Step 3: Add Time Features

**Input**: Hourly DataFrame  
**Output**: DataFrame with temporal features

```python
df = add_time_features(df)
```

**New Columns**:
- `day_of_week`: 0=Monday, 1=Tuesday, ..., 6=Sunday
- `month`: 1=January, ..., 12=December
- `week_of_year`: ISO week number (1-53)

**Use Case**: Capture weekly/monthly patterns, seasonality.

### Step 4: Add Lag Features

**Input**: Time-series DataFrame  
**Output**: DataFrame with lag and rolling features

```python
df = add_lag_features(df, target_col='item_count')
```

**New Columns**:
- `prev_hour_items`: Value from 1 hour ago
- `prev_day_items`: Value from 24 hours ago (same hour yesterday)
- `prev_week_items`: Value from 168 hours ago (same hour last week)
- `prev_month_items`: Value from 720 hours ago (same hour last month)
- `rolling_7d_avg_items`: 7-day rolling average (**shifted to prevent leakage**)

**Data Leakage Prevention**:
```python
# Shift rolling average by 1 to exclude current value
df['rolling_7d_avg'] = df.groupby('place_id')['target'].transform(
    lambda x: x.rolling(window=168, min_periods=1).mean().shift(1)
)
```

**Null Handling**: Missing lag values filled with 0 (new restaurants, start of data).

### Step 5: Join Place Features

**Input**: DataFrame + place metadata  
**Output**: DataFrame enriched with restaurant characteristics

```python
df = join_place_features(df, places_df)
```

**New Columns**:
- `type_id`: Restaurant type (1=restaurant, 2=cafe, 3=bar)
- `waiting_time`: Average wait time (minutes)
- `rating`: Restaurant rating (0-5 scale)
- `delivery`: Offers delivery (0/1)
- `accepting_orders`: Currently accepting (0/1)
- `latitude`, `longitude`: Location (used for weather/holiday, then dropped)

### Step 6: Add Campaign Features

**Input**: DataFrame + campaign data  
**Output**: DataFrame with campaign statistics

```python
df = add_campaign_features(df, campaigns_df)
```

**New Columns**:
- `total_campaigns`: Count of campaigns for this place
- `avg_discount`: Average discount percentage

**Aggregation**: Campaigns aggregated per place (not per time period).

### Step 7: Add Weather Features

**Input**: DataFrame with `date`, `hour`, `latitude`, `longitude`  
**Output**: DataFrame with 16 weather features

```python
df = get_weather_for_demand_data(df)
```

**API Calls**:
- Historical data: `https://archive-api.open-meteo.com/v1/archive`
- Forecast data: `https://api.open-meteo.com/v1/forecast`

**Raw Weather Variables** (from Open-Meteo):
- `temperature_2m`: Air temperature at 2m (°C)
- `relative_humidity_2m`: Humidity (%)
- `precipitation`: Total precipitation (mm)
- `rain`: Liquid precipitation (mm)
- `snowfall`: Snow amount (cm)
- `weather_code`: WMO code (0-99)
- `cloud_cover`: Cloud coverage (%)
- `wind_speed_10m`: Wind speed at 10m (km/h)

**Derived Weather Features**:
```python
df['is_rainy'] = (df['precipitation'] > 0.5).astype(int)
df['is_snowy'] = (df['snowfall'] > 0).astype(int)
df['is_cold'] = (df['temperature_2m'] < 5).astype(int)
df['is_hot'] = (df['temperature_2m'] > 25).astype(int)
df['is_cloudy'] = (df['cloud_cover'] > 70).astype(int)
df['is_windy'] = (df['wind_speed_10m'] > 30).astype(int)

df['good_weather'] = (
    df['temperature_2m'].between(15, 28) &
    (df['precipitation'] < 0.5) &
    (df['wind_speed_10m'] < 25)
).astype(int)

df['weather_severity'] = (
    df['is_rainy'] * 2 +
    df['is_snowy'] * 3 +
    df['is_cold'] * 1 +
    df['is_windy'] * 1
)
```

**Batching**: API calls batched by unique `(place_id, latitude, longitude)` combinations to reduce latency.

**Retry Logic**: Exponential backoff on connection errors (3 retries, 2/4/6 second delays).

**Fallback**: On API failure, fills with default values:
```python
defaults = {
    'temperature_2m': 15.0,  # Mild temperature
    'relative_humidity_2m': 70.0,
    'precipitation': 0.0,
    'is_rainy': 0,
    'good_weather': 1  # Assume good weather
}
```

### Step 8: Add Holiday Features

**Input**: DataFrame with `date`, `latitude`, `longitude`  
**Output**: DataFrame with holiday flag

```python
df = add_holiday_feature(df)
```

**Process**:
1. **Reverse Geocoding**: Convert (lat, lon) → country code
   - API: `https://nominatim.openstreetmap.org/reverse`
   - Caching: Results cached to avoid redundant API calls
   
2. **Holiday Detection**: Check if date is a public holiday
   - Library: `holidays` (Python package with 100+ country calendars)
   - Example holidays:
     - US: Independence Day (July 4), Thanksgiving, Christmas
     - DK: New Year, Christmas, Easter
     - UK: Boxing Day, Bank Holidays

**Batching**: Groups by unique `(date, latitude, longitude)` to minimize API calls.

**New Column**:
- `is_holiday`: 1 if public holiday, 0 otherwise

**Fallback**: On geocoding failure, uses default location (Copenhagen: 55.6761, 12.5683).

### Step 9: Feature Alignment

**Input**: Feature-rich DataFrame  
**Output**: Model-ready feature matrix

```python
X = align_features_with_model(df)
```

**Operations**:

1. **Place ID Encoding**: Convert string IDs to deterministic numeric values
   ```python
   def encode_place_id(place_str):
       hash_obj = hashlib.md5(str(place_str).encode('utf-8'))
       return float(int(hash_obj.hexdigest()[:8], 16) % 100000)
   ```

2. **Missing Column Handling**: Add columns with default values if missing

3. **Column Ordering**: Ensure exact order expected by model

4. **Type Conversion**: Ensure correct dtypes (float64, int)

5. **NaN Handling**: Fill remaining NaN with 0

**Final Feature Set**: 35 features in exact order:
```python
features = [
    'place_id', 'hour', 'day_of_week', 'month', 'week_of_year',
    'type_id', 'waiting_time', 'rating', 'delivery', 'accepting_orders',
    'total_campaigns', 'avg_discount',
    'prev_hour_items', 'prev_day_items', 'prev_week_items', 
    'prev_month_items', 'rolling_7d_avg_items',
    'temperature_2m', 'relative_humidity_2m', 'precipitation', 
    'rain', 'snowfall', 'weather_code', 'cloud_cover', 'wind_speed_10m',
    'is_rainy', 'is_snowy', 'is_cold', 'is_hot', 'is_cloudy', 
    'is_windy', 'good_weather', 'weather_severity',
    'is_holiday'
]
```

### Pipeline Performance

**Typical Execution Times** (7 days, 1 restaurant):

| Step | Time | Bottleneck |
|------|------|------------|
| 1-3: Data Processing | ~0.5s | Pandas operations |
| 4: Lag Features | ~1.0s | Rolling calculations |
| 5-6: Joins | ~0.2s | Merge operations |
| 7: Weather API | ~3-5s | HTTP requests |
| 8: Holiday API | ~2-4s | HTTP requests + geocoding |
| 9: Alignment | ~0.3s | Type conversions |
| **Total** | **~7-11s** | External APIs |

**Optimization Tips**:
- Cache weather data for repeated predictions
- Batch multiple restaurants in single API call
- Pre-fetch holidays for common locations

---

## External Integrations

### Weather API (Open-Meteo)

#### Overview

**Provider**: [Open-Meteo](https://open-meteo.com/)  
**Cost**: Free, no API key required  
**Rate Limit**: 10,000 requests/day  
**Coverage**: Global, all timezones  

#### Endpoints Used

**Historical Weather** (1940 - 5 days ago):
```
GET https://archive-api.open-meteo.com/v1/archive
```

**Parameters**:
```
?latitude=55.6761
&longitude=12.5683
&start_date=2024-01-01
&end_date=2024-01-07
&hourly=temperature_2m,relative_humidity_2m,precipitation,rain,snowfall,weather_code,cloud_cover,wind_speed_10m
&timezone=Europe/Copenhagen
```

**Weather Forecast** (next 16 days):
```
GET https://api.open-meteo.com/v1/forecast
```

**Parameters**:
```
?latitude=55.6761
&longitude=12.5683
&hourly=temperature_2m,relative_humidity_2m,precipitation,rain,snowfall,weather_code,cloud_cover,wind_speed_10m
&timezone=Europe/Copenhagen
&forecast_days=16
```

#### WMO Weather Codes

| Code | Description |
|------|-------------|
| 0 | Clear sky |
| 1-3 | Mainly clear, partly cloudy, overcast |
| 45-48 | Fog |
| 51-55 | Drizzle (light to dense) |
| 61-65 | Rain (slight to heavy) |
| 71-75 | Snow (slight to heavy) |
| 80-82 | Rain showers |
| 95-99 | Thunderstorm (with/without hail) |

#### Error Handling

**Connection Errors**: Retry with exponential backoff
```python
try:
    response = requests.get(url, params=params, timeout=30)
except (ConnectionError, Timeout) as e:
    if attempt < max_retries - 1:
        wait_time = (attempt + 1) * 2  # 2s, 4s, 6s
        time.sleep(wait_time)
        # Retry...
```

**API Failures**: Fall back to default weather
```python
default_weather = {
    'temperature_2m': 15.0,      # Mild
    'precipitation': 0.0,         # No rain
    'good_weather': 1             # Assume good
}
```

#### Best Practices

✅ **Batch requests** by unique locations  
✅ **Cache results** for repeated queries  
✅ **Use appropriate timezone** for restaurant location  
✅ **Handle missing data** with sensible defaults  
❌ Don't exceed 10K daily requests  
❌ Don't request more than 16 days forecast  

---

### Holiday API (Nominatim + holidays)

#### Overview

**Geocoding**: [Nominatim (OpenStreetMap)](https://nominatim.openstreetmap.org/)  
**Holidays**: [Python holidays library](https://pypi.org/project/holidays/)  
**Cost**: Free  
**Rate Limit**: 1 request/second (Nominatim)  

#### Reverse Geocoding

**Endpoint**:
```
GET https://nominatim.openstreetmap.org/reverse
```

**Parameters**:
```
?lat=55.6761
&lon=12.5683
&format=json
&zoom=3
```

**Headers**:
```
User-Agent: HolidayChecker/1.0
```

**Response**:
```json
{
  "address": {
    "country": "Denmark",
    "country_code": "dk"
  }
}
```

#### Holiday Detection

**Supported Countries**: 140+ (via `holidays` library)

**Example Usage**:
```python
import holidays

# Get country-specific holidays
dk_holidays = holidays.country_holidays('DK')

# Check if date is a holiday
is_holiday = date(2024, 12, 25) in dk_holidays
holiday_name = dk_holidays.get(date(2024, 12, 25))  # "Christmas Day"
```

**Common Holidays by Region**:

| Country | Key Holidays |
|---------|--------------|
| US | New Year, MLK Day, Presidents Day, Memorial Day, Independence Day, Labor Day, Thanksgiving, Christmas |
| UK | New Year, Good Friday, Easter Monday, Early May Bank Holiday, Spring Bank Holiday, Summer Bank Holiday, Christmas, Boxing Day |
| DK | New Year, Maundy Thursday, Good Friday, Easter Monday, Great Prayer Day, Ascension Day, Whit Monday, Christmas, Boxing Day |
| FR | New Year, Easter Monday, Labor Day, Victory Day, Ascension, Whit Monday, Bastille Day, Assumption, All Saints, Armistice, Christmas |

#### Caching Strategy

**Country Code Cache**:
```python
country_cache = {}

def get_country_from_coords(lat, lon):
    cache_key = f"{lat:.2f},{lon:.2f}"
    if cache_key in country_cache:
        return country_cache[cache_key]
    
    # Make API call...
    country_cache[cache_key] = country_code
    return country_code
```

**Batching Strategy**:
```python
# Group by unique (date, lat, lon) combinations
unique_combos = df[['date', 'latitude', 'longitude']].drop_duplicates()

# Check holidays for each unique combo
for combo in unique_combos:
    result = check_holiday(combo['date'], combo['latitude'], combo['longitude'])
    holiday_lookup[combo] = result

# Map back to full dataframe
df['is_holiday'] = df.apply(lambda row: holiday_lookup[(row['date'], row['lat'], row['lon'])], axis=1)
```

#### Error Handling

**Geocoding Failures**:
- Use default location (Copenhagen: 55.6761, 12.5683)
- Log warning but continue processing

**Holiday Lookup Failures**:
- Assume not a holiday (`is_holiday = 0`)
- Continue without error

#### Rate Limiting

**Nominatim Requires**:
- 1 request per second maximum
- User-Agent header with contact info
- Use caching to minimize requests

**Implementation**:
```python
time.sleep(1)  # Respect rate limit between requests
```

---

## Data Models

### Request Models

All request models use Pydantic for validation.

#### PlaceData

Restaurant/venue information.

```python
class PlaceData(BaseModel):
    place_id: str                           # Unique identifier
    place_name: str                         # Display name
    type: str                               # "restaurant", "cafe", "bar"
    latitude: float                         # Location (for weather/holidays)
    longitude: float
    waiting_time: Optional[int] = None      # Average wait time (minutes)
    receiving_phone: bool                   # Accepts phone orders
    delivery: bool                          # Offers delivery
    opening_hours: Dict[str, OpeningHoursDay]  # Hours per day
    fixed_shifts: bool = True               # Use fixed shifts vs. flexible
    number_of_shifts_per_day: int = 3       # Number of shifts
    shift_times: List[str]                  # e.g., ["06:00-14:00", "14:00-22:00"]
    rating: Optional[float] = None          # Rating (0-5)
    accepting_orders: Optional[bool] = True # Currently accepting
```

**Opening Hours Format**:
```python
opening_hours = {
    "monday": {"from": "10:00", "to": "22:00"},
    "sunday": {"closed": True}
}
```

#### OrderData

Single order record.

```python
class OrderData(BaseModel):
    time: str                               # ISO timestamp
    items: int                              # Number of items
    status: str                             # "completed" or "canceled"
    total_amount: float                     # Order total (currency)
    discount_amount: float = 0              # Discount applied
```

#### CampaignData

Marketing campaign information.

```python
class CampaignData(BaseModel):
    start_time: str                         # ISO timestamp
    end_time: str                           # ISO timestamp
    items_included: List[str]               # Item IDs in campaign
    discount: float                         # Discount % (0-100)
```

#### RoleData

Employee role definition.

```python
class RoleData(BaseModel):
    role_id: str                            # Unique identifier
    role_name: str                          # Display name
    producing: bool                         # Produces items?
    items_per_employee_per_hour: Optional[float]  # Production rate
    min_present: int = 0                    # Minimum required
    is_independent: bool = True             # Independent or chain role
```

#### EmployeeData

Employee availability and preferences.

```python
class EmployeeData(BaseModel):
    employee_id: str
    role_ids: List[str]                     # Roles can perform
    available_days: List[str]               # ["monday", "tuesday", ...]
    preferred_days: List[str]               # Preferred working days
    available_hours: Dict[str, EmployeeHours]  # Hours per day
    preferred_hours: Dict[str, EmployeeHours]  # Preferred hours
    hourly_wage: float                      # Wage rate
    max_hours_per_week: float = 40.0        # Weekly hour limit
    max_consec_slots: int = 8               # Max consecutive hours
    pref_hours: float = 32.0                # Preferred weekly hours
```

**Hours Format**:
```python
available_hours = {
    "monday": {"from": "10:00", "to": "22:00"},
    "tuesday": {"from": "14:00", "to": "22:00"}
}
```

#### ProductionChainData

Sequential workflow definition.

```python
class ProductionChainData(BaseModel):
    chain_id: str                           # Unique identifier
    role_ids: List[str]                     # Ordered role sequence
    contrib_factor: float = 1.0             # Output multiplier (0-1)
```

#### SchedulerConfig

Scheduler parameters.

```python
class SchedulerConfig(BaseModel):
    slot_len_hour: float = 1.0              # Slot duration
    min_rest_slots: int = 2                 # Rest between days
    min_shift_length_slots: int = 2         # Minimum shift length
    meet_all_demand: bool = False           # Hard demand constraint
```

### Response Models

#### HourPrediction

Prediction for a single hour.

```python
class HourPrediction(BaseModel):
    hour: int                               # Hour of day (0-23)
    order_count: int                        # Predicted orders
    item_count: int                         # Predicted items
```

#### DayPrediction

Predictions for a full day.

```python
class DayPrediction(BaseModel):
    day_name: str                           # "monday", "tuesday", etc.
    date: str                               # YYYY-MM-DD
    hours: List[HourPrediction]             # 24 hourly predictions
```

#### DemandOutput

Complete demand prediction response.

```python
class DemandOutput(BaseModel):
    restaurant_name: str
    prediction_period: str                  # "2024-01-15 to 2024-01-21"
    days: List[DayPrediction]
```

#### ScheduleOutput

Staff schedule organized by day and shift.

```python
class ScheduleOutput(BaseModel):
    monday: List[Dict[str, List[str]]] = []    # Shift → employee list
    tuesday: List[Dict[str, List[str]]] = []
    wednesday: List[Dict[str, List[str]]] = []
    thursday: List[Dict[str, List[str]]] = []
    friday: List[Dict[str, List[str]]] = []
    saturday: List[Dict[str, List[str]]] = []
    sunday: List[Dict[str, List[str]]] = []
```

**Format**:
```json
{
  "monday": [
    {"06:00-14:00": ["emp_001", "emp_003"]},
    {"14:00-22:00": ["emp_002", "emp_004"]}
  ]
}
```

---

## Usage Examples

### Example 1: Basic Demand Prediction

```python
import requests
import json

# API endpoint
url = "http://localhost:8000/predict/demand"

# Request payload
payload = {
    "place": {
        "place_id": "pizza_palace_001",
        "place_name": "Pizza Palace",
        "type": "restaurant",
        "latitude": 55.6761,
        "longitude": 12.5683,
        "waiting_time": 25,
        "receiving_phone": True,
        "delivery": True,
        "opening_hours": {
            "monday": {"from": "11:00", "to": "22:00"},
            "tuesday": {"from": "11:00", "to": "22:00"},
            "wednesday": {"from": "11:00", "to": "22:00"},
            "thursday": {"from": "11:00", "to": "23:00"},
            "friday": {"from": "11:00", "to": "23:00"},
            "saturday": {"from": "12:00", "to": "23:00"},
            "sunday": {"closed": True}
        },
        "fixed_shifts": True,
        "number_of_shifts_per_day": 3,
        "shift_times": ["11:00-15:00", "15:00-19:00", "19:00-23:00"],
        "rating": 4.6,
        "accepting_orders": True
    },
    "orders": [
        # ... historical orders from last 14 days
    ],
    "campaigns": [
        {
            "start_time": "2024-02-01T00:00:00",
            "end_time": "2024-02-14T23:59:59",
            "items_included": ["margherita", "pepperoni"],
            "discount": 20.0
        }
    ],
    "prediction_start_date": "2024-02-15",
    "prediction_days": 7
}

# Make request
response = requests.post(url, json=payload)
result = response.json()

# Access predictions
for day in result["demand_output"]["days"]:
    print(f"{day['day_name']} ({day['date']}):")
    peak_hour = max(day['hours'], key=lambda h: h['item_count'])
    print(f"  Peak hour: {peak_hour['hour']}:00 - {peak_hour['item_count']} items")
```

### Example 2: Generate Staff Schedule

```python
# Assuming you have demand_predictions from previous call

url = "http://localhost:8000/predict/schedule"

payload = {
    "place": place_data,  # Same as before
    "schedule_input": {
        "roles": [
            {
                "role_id": "pizza_chef",
                "role_name": "Pizza Chef",
                "producing": True,
                "items_per_employee_per_hour": 12.0,
                "min_present": 1,
                "is_independent": False
            },
            {
                "role_id": "cashier",
                "role_name": "Cashier",
                "producing": False,
                "items_per_employee_per_hour": None,
                "min_present": 1,
                "is_independent": True
            }
        ],
        "employees": [
            {
                "employee_id": "john_doe",
                "role_ids": ["pizza_chef", "cashier"],
                "available_days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
                "preferred_days": ["monday", "wednesday", "friday"],
                "available_hours": {
                    "monday": {"from": "11:00", "to": "22:00"},
                    "tuesday": {"from": "11:00", "to": "22:00"},
                    "wednesday": {"from": "11:00", "to": "22:00"},
                    "thursday": {"from": "11:00", "to": "22:00"},
                    "friday": {"from": "11:00", "to": "23:00"}
                },
                "preferred_hours": {
                    "monday": {"from": "15:00", "to": "22:00"},
                    "wednesday": {"from": "15:00", "to": "22:00"},
                    "friday": {"from": "15:00", "to": "23:00"}
                },
                "hourly_wage": 28.0,
                "max_hours_per_week": 40.0,
                "max_consec_slots": 8,
                "pref_hours": 35.0
            }
            # ... more employees
        ],
        "production_chains": [
            {
                "chain_id": "pizza_production",
                "role_ids": ["pizza_chef"],
                "contrib_factor": 0.95
            }
        ],
        "scheduler_config": {
            "slot_len_hour": 1.0,
            "min_rest_slots": 2,
            "min_shift_length_slots": 3,
            "meet_all_demand": False
        }
    },
    "demand_predictions": demand_predictions,
    "prediction_start_date": "2024-02-15"
}

response = requests.post(url, json=payload)
schedule = response.json()

# Check status
if schedule["schedule_status"] == "optimal":
    print("Optimal schedule found!")
    print(f"Total cost: ${schedule['objective_value']:.2f}")
    
    # Print Monday schedule
    for shift in schedule["schedule_output"]["monday"]:
        for time_range, employees in shift.items():
            print(f"  {time_range}: {', '.join(employees)}")
else:
    print(f"Schedule status: {schedule['schedule_status']}")
    print(f"Message: {schedule['schedule_message']}")
```

### Example 3: Using cURL

```bash
# Demand prediction
curl -X POST "http://localhost:8000/predict/demand" \
  -H "Content-Type: application/json" \
  -d @demand_request.json

# Schedule generation
curl -X POST "http://localhost:8000/predict/schedule" \
  -H "Content-Type: application/json" \
  -d @schedule_request.json
```

### Example 4: Python SDK Wrapper

```python
class RestaurantDemandAPI:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
    
    def predict_demand(self, place, orders, campaigns=None, 
                      start_date=None, days=7):
        """Predict demand for a restaurant"""
        from datetime import date, timedelta
        
        if start_date is None:
            start_date = (date.today() + timedelta(days=1)).isoformat()
        
        payload = {
            "place": place,
            "orders": orders,
            "campaigns": campaigns or [],
            "prediction_start_date": start_date,
            "prediction_days": days
        }
        
        response = requests.post(
            f"{self.base_url}/predict/demand",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    def generate_schedule(self, place, roles, employees, 
                         demand_predictions, production_chains=None,
                         config=None, start_date=None):
        """Generate optimal staff schedule"""
        from datetime import date, timedelta
        
        if start_date is None:
            start_date = (date.today() + timedelta(days=1)).isoformat()
        
        payload = {
            "place": place,
            "schedule_input": {
                "roles": roles,
                "employees": employees,
                "production_chains": production_chains or [],
                "scheduler_config": config or {}
            },
            "demand_predictions": demand_predictions,
            "prediction_start_date": start_date
        }
        
        response = requests.post(
            f"{self.base_url}/predict/schedule",
            json=payload
        )
        response.raise_for_status()
        return response.json()

# Usage
api = RestaurantDemandAPI()
demand = api.predict_demand(place_data, orders, campaigns)
schedule = api.generate_schedule(
    place_data, roles, employees, 
    demand["demand_output"]["days"]
)
```

---

## Configuration

### Environment Variables

```bash
# Server configuration
export API_HOST="0.0.0.0"
export API_PORT="8000"
export API_WORKERS="4"

# Model paths
export MODEL_PATH="data/models/rf_model.joblib"
export METADATA_PATH="data/models/rf_model_metadata.json"

# Feature flags
export WEATHER_API_ENABLED="true"
export HOLIDAY_API_ENABLED="true"
export SCHEDULER_ENABLED="true"

# Logging
export LOG_LEVEL="INFO"
export LOG_FORMAT="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

### Scheduler Tuning

**For Small Restaurants** (1-5 employees):
```python
config = {
    "slot_len_hour": 1.0,
    "min_rest_slots": 2,
    "min_shift_length_slots": 2,
    "meet_all_demand": False
}
time_limit = 30  # seconds
```

**For Medium Restaurants** (6-15 employees):
```python
config = {
    "slot_len_hour": 1.0,
    "min_rest_slots": 2,
    "min_shift_length_slots": 3,
    "meet_all_demand": False
}
time_limit = 60  # seconds
```

**For Large Restaurants** (16+ employees):
```python
config = {
    "slot_len_hour": 2.0,  # Use 2-hour slots for faster solving
    "min_rest_slots": 1,   # Measured in 2-hour slots
    "min_shift_length_slots": 2,
    "meet_all_demand": False
}
time_limit = 120  # seconds
```

**For Critical Schedules** (must be optimal):
```python
config = {
    "slot_len_hour": 1.0,
    "min_rest_slots": 2,
    "min_shift_length_slots": 3,
    "meet_all_demand": True  # Hard constraint
}
time_limit = 300  # 5 minutes
```

### Model Retraining

```bash
# 1. Collect new data
python scripts/data_collection.py --start-date 2024-01-01 --end-date 2024-12-31

# 2. Run feature engineering
python src/feature_engineering.py

# 3. Train new model
python scripts/train_model.py

# 4. Evaluate performance
python scripts/evaluate_model.py

# 5. Deploy if improvements observed
cp data/models/rf_model_new.joblib data/models/rf_model.joblib
systemctl restart restaurant-api
```

---

## Troubleshooting

### Common Issues

#### 1. Model Not Found

**Error**: `Model not loaded` in health check

**Solution**:
```bash
# Check if model files exist
ls data/models/rf_model.joblib
ls data/models/rf_model_metadata.json

# If missing, train a new model
python scripts/train_model.py
```

#### 2. Weather API Failures

**Error**: `Weather API not available`

**Symptoms**: Predictions use default weather values

**Solutions**:
- Check internet connectivity
- Verify Open-Meteo is not rate-limited (10K/day)
- Wait and retry (automatic retry with backoff)
- Use cached weather data if available

#### 3. Infeasible Schedule

**Error**: `schedule_status: "infeasible"`

**Common Causes**:
- Not enough employees for minimum staffing
- Demand exceeds total capacity
- Conflicting constraints (availability vs. minimum hours)

**Solutions**:
```python
# Check management insights
insights = generate_management_insights(None, input_data)

# Review feasibility issues
for issue in insights['feasibility_analysis']:
    print(f"{issue['severity']}: {issue['issue']}")
    print(f"  Details: {issue['details']}")

# Common fixes:
# 1. Add more employees
# 2. Increase max_hours_per_week
# 3. Relax min_present requirements
# 4. Set meet_all_demand=False (soft constraint)
```

#### 4. Slow Predictions

**Symptoms**: API takes >30 seconds to respond

**Causes**:
- Weather API slow (first-time fetch)
- Holiday API geocoding delay
- Large historical dataset

**Solutions**:
```python
# 1. Cache weather data
weather_cache = {}  # Implement Redis cache

# 2. Pre-fetch holidays for common locations
pre_cache_holidays(['DK', 'US', 'UK', 'FR'])

# 3. Limit historical data
orders = orders[-30*24:]  # Last 30 days only
```

#### 5. Scheduler Timeout

**Error**: Solver returns `UNKNOWN` status

**Solution**:
```python
# Increase time limit
solution = scheduler.solve(time_limit_seconds=120)

# Or reduce problem size
config['slot_len_hour'] = 2.0  # Use 2-hour slots
```

#### 6. Negative Predictions

**Error**: Predictions contain negative values

**Solution**: Already handled in code, but if occurring:
```python
# Explicit clamping
predictions = np.maximum(predictions, 0)
```

#### 7. Feature Mismatch

**Error**: `KeyError` or `Feature not found`

**Solution**:
```python
# Regenerate features with latest pipeline
df = prepare_features_for_prediction(place, orders, campaigns, start_date, days)
X = align_features_with_model(df)
```

### Logs and Debugging

**Enable DEBUG logging**:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Check logs**:
```bash
# Follow API logs
tail -f logs/api.log

# Check for errors
grep ERROR logs/api.log

# Check scheduler progress
grep "CP-SAT" logs/api.log
```

### Performance Monitoring

**Request Timing**:
```python
import time

start = time.time()
response = requests.post(url, json=payload)
print(f"Request took {time.time() - start:.2f}s")
```

**Component Timing**:
```python
# Add to code
import time

t0 = time.time()
df = prepare_features_for_prediction(...)
print(f"Feature engineering: {time.time() - t0:.2f}s")

t0 = time.time()
predictions = model.predict(X)
print(f"Model prediction: {time.time() - t0:.2f}s")

t0 = time.time()
solution = scheduler.solve(...)
print(f"Scheduling: {time.time() - t0:.2f}s")
```

---

## Appendix

### Glossary

| Term | Definition |
|------|------------|
| **Demand** | Number of items or orders in a time period |
| **Lag Feature** | Historical value from a fixed time in the past |
| **Rolling Feature** | Average over a sliding time window |
| **Fixed Shift** | Predefined work period (e.g., 06:00-14:00) |
| **Slot** | Time unit (typically 1 hour) |
| **Production Chain** | Sequential workflow (e.g., prep → cook → serve) |
| **Bottleneck** | Slowest step in a production chain |
| **CP-SAT** | Constraint Programming - Satisfiability solver |
| **Feasible** | Schedule that satisfies all constraints |
| **Optimal** | Best feasible schedule (minimizes cost) |
| **Utilization** | Percentage of available time actually worked |

### References

- **Google OR-Tools**: https://developers.google.com/optimization
- **Open-Meteo API**: https://open-meteo.com/
- **Python holidays**: https://github.com/vacanza/python-holidays
- **scikit-learn**: https://scikit-learn.org/
- **FastAPI**: https://fastapi.tiangolo.com/

### Support

For issues, questions, or feature requests:
- **GitHub Issues**: [repository-url]/issues
- **Documentation**: [repository-url]/docs
- **Email**: support@example.com

---

**Document Version**: 3.0.0  
**Last Updated**: 2024-02-06  
**API Version**: 3.0.0