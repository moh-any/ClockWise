# QuickServe ML Platform

**Restaurant Demand Prediction, Scheduling, Surge Detection & Campaign AI**

Version 3.1.0 | February 2026

---

## Overview

The QuickServe ML Platform provides intelligent automation for restaurant operations through four interconnected systems:

| System | Purpose | Technology |
|--------|---------|------------|
| **Demand Prediction** | Forecast hourly item/order counts | CatBoost + Quantile Regression |
| **Staff Scheduling** | Optimal shift planning | Google OR-Tools CP-SAT |
| **Surge Detection** | Real-time viral event response | Social Media APIs |
| **Campaign AI** | Marketing campaign recommendations | XGBoost + Thompson Sampling |

---

## Quick Start

### Prerequisites

```bash
Python 3.12+
8GB RAM recommended
```

### Installation

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Run API Server

```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### Access Documentation

- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           REST API (FastAPI)                            │
│                         api/main.py - Port 8000                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐         │
│  │     Demand      │  │     Staff       │  │    Campaign     │         │
│  │   Prediction    │  │   Scheduling    │  │  Recommender    │         │
│  │                 │  │                 │  │                 │         │
│  │  POST /predict  │  │  POST /schedule │  │  POST /campaign │         │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘         │
│           │                    │                    │                  │
│           │                    │                    │                  │
│  ┌────────▼────────┐  ┌────────▼────────┐  ┌────────▼────────┐         │
│  │   CatBoost      │  │   OR-Tools      │  │    XGBoost +    │         │
│  │   Quantile      │  │   CP-SAT        │  │    Thompson     │         │
│  │   Regression    │  │   Solver        │  │    Sampling     │         │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘         │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────┐       │
│  │                   SURGE DETECTION SYSTEM                     │       │
│  │                     /api/v1/surge/*                          │       │
│  │                                                              │       │
│  │   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │       │
│  │   │   Social     │    │    Surge     │    │   Alert      │  │       │
│  │   │   Media      │───►│   Detector   │───►│   System     │  │       │
│  │   │   APIs       │    │              │    │              │  │       │
│  │   └──────────────┘    └──────────────┘    └──────────────┘  │       │
│  │                                                              │       │
│  └─────────────────────────────────────────────────────────────┘       │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                         EXTERNAL SERVICES                               │
│                                                                         │
│      ┌──────────┐   ┌──────────┐   ┌──────────┐                        │
│      │ Weather  │   │ Holiday  │   │ Twitter  │                        │
│      │ API      │   │ API      │   │ Trends   │                        │
│      └──────────┘   └──────────┘   └──────────┘                        │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Core Components

### 1. Demand Prediction Model

Forecasts hourly `item_count` and `order_count` for restaurant venues.

| Metric | Value |
|--------|-------|
| **Algorithm** | CatBoost with Quantile Loss (α=0.60) |
| **MAE** | 3.32 items |
| **R²** | 0.69 |
| **Bias** | +0.23 (slight over-prediction) |

**Key Features**:
- 54 engineered features (temporal, lag, rolling, venue-specific)
- Prediction intervals (20%, 50%, 80% quantiles)
- Sample weighting for high-demand periods
- Weather and holiday enrichment

**Files**:
- Model: `data/models/rf_model.joblib`
- Training: `src/train_model.py`
- Features: `src/feature_engineering.py`

📚 [Full Documentation](docs/DEMAND_PREDICTION_MODEL.md)

---

### 2. Staff Scheduling Engine

Generates optimal employee schedules using constraint programming.

| Feature | Description |
|---------|-------------|
| **Solver** | Google OR-Tools CP-SAT |
| **Constraints** | 15+ types (availability, hours, rest, skills) |
| **Modes** | Fixed shifts or flexible time slots |
| **Insights** | Hiring recommendations, coverage gaps |

**Optimization Objectives**:
1. Minimize unmet demand (highest priority)
2. Minimize labor costs
3. Balance workload fairly
4. Respect employee preferences

**Files**:
- Solver: `src/scheduler_cpsat.py`
- Mathematical Model: `src/scheduler_mathematical_model.md`

📚 [Full Documentation](docs/scheduler_api_usage.md)

---

### 3. Surge Detection System

Detects and responds to unexpected demand spikes from viral events.

| Layer | Purpose |
|-------|---------|
| **Data Collection** | Real-time orders + social signals |
| **Surge Detection** | Rolling ratio analysis |
| **Orchestration** | Emergency schedule generation |
| **Alerts** | Multi-channel notifications |

**Detection Criteria**:
- Actual/Predicted ratio > 1.5x for 3 consecutive hours
- Minimum 20 excess items per hour
- Cooldown period to prevent alert fatigue

**Files**:
- Detector: `src/surge_detector.py`
- Orchestrator: `src/surge_orchestrator.py`
- API: `src/surge_api.py`
- Social Media: `src/social_media_apis.py`

📚 [Full Documentation](docs/surge_detection_architecture.md)

---

### 4. Campaign Recommendation System

ML-powered marketing campaign suggestions using contextual bandits.

| Feature | Description |
|---------|-------------|
| **Algorithm** | Thomson Sampling + XGBoost |
| **Optimization** | ROI, Uplift, Revenue |
| **Learning** | Online updates from feedback |
| **Strategies** | Template-based, Affinity, Seasonal |

**Outputs**:
- Recommended campaigns with expected ROI
- Item combinations based on co-purchase affinity
- Seasonal recommendations
- Confidence scores and reasoning

**Files**:
- Recommender: `src/campaign_recommender.py`
- Analyzer: `src/campaign_analyzer.py`
- Training: `src/train_campaign_model.py`

📚 [Full Documentation](docs/CAMPAIGN_RECOMMENDER.md)

---

## API Endpoints

### Health & Status

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/model/info` | GET | Model metadata |

### Prediction & Scheduling

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/predict/demand` | POST | Demand forecast only |
| `/predict/schedule` | POST | Schedule generation only |
| `/predict/demand-and-schedule` | POST | Full pipeline |

### Campaign

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/recommend/campaigns` | POST | Get recommendations |
| `/recommend/campaigns/feedback` | POST | Submit feedback |

### Surge Detection

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/surge/venues` | GET | List monitored venues |
| `/api/v1/surge/venues/{id}/status` | GET | Venue surge status |
| `/api/v1/surge/events` | GET | Active surge events |
| `/api/v1/surge/venues/{id}/emergency-schedule` | POST | Generate emergency schedule |

---

## Directory Structure

```
app/ml/
├── api/
│   ├── main.py              # FastAPI application
│   └── campaign_models.py   # Pydantic models
├── data/
│   ├── models/              # Trained ML models
│   ├── training/            # Training data
│   └── processed/           # Feature datasets
├── docs/
│   ├── DEMAND_PREDICTION_MODEL.md
│   ├── scheduler_api_usage.md
│   ├── surge_detection_architecture.md
│   ├── CAMPAIGN_RECOMMENDER.md
│   └── ...
├── src/
│   ├── train_model.py       # Demand model training
│   ├── feature_engineering.py
│   ├── scheduler_cpsat.py   # CP-SAT scheduler
│   ├── surge_detector.py    # Surge detection engine
│   ├── surge_orchestrator.py
│   ├── surge_api.py         # Surge API routes
│   ├── campaign_recommender.py
│   ├── campaign_analyzer.py
│   ├── weather_api.py
│   ├── holiday_api.py
│   └── ...
├── tests/
│   └── ...
├── requirements.txt
└── README.md                # This file
```

---

## Configuration

### Environment Variables

Create a `.env` file:

```bash
# Optional: Twitter API for social signals
TWITTER_BEARER_TOKEN=your_token

# Optional: Weather API
WEATHER_API_KEY=optional_key
```

### Model Files

Required files in `data/models/`:
- `rf_model.joblib` - Demand prediction model
- `rf_model_metadata.json` - Model metadata
- `campaign_recommender.json` - Campaign model
- `campaign_recommender_model.xgb` - XGBoost model

---

## Training Models

### Demand Prediction Model

```bash
python src/train_model.py
```

Outputs:
- `data/models/rf_model.joblib`
- `data/models/rf_model_metadata.json`

### Campaign Recommender

```bash
python src/train_campaign_model.py --data-dir data/training
```

Outputs:
- `data/models/campaign_recommender.json`
- `data/models/campaign_recommender_model.xgb`

---

## Documentation Index

| Document | Description |
|----------|-------------|
| [DEMAND_PREDICTION_MODEL.md](docs/DEMAND_PREDICTION_MODEL.md) | Demand model architecture and usage |
| [scheduler_api_usage.md](docs/scheduler_api_usage.md) | Scheduler API guide |
| [surge_detection_architecture.md](docs/surge_detection_architecture.md) | Surge system design |
| [SURGE_ORCHESTRATION_GUIDE.md](docs/SURGE_ORCHESTRATION_GUIDE.md) | Surge response workflow |
| [CAMPAIGN_RECOMMENDER.md](docs/CAMPAIGN_RECOMMENDER.md) | Campaign AI documentation |
| [DATA_COLLECTION_API.md](docs/DATA_COLLECTION_API.md) | Data collection endpoints |
| [Documentation.md](docs/Documentation.md) | Complete API reference |
| [DEVELOPMENT_HISTORY.md](docs/DEVELOPMENT_HISTORY.md) | Model evolution history |
| [problem.md](docs/problem.md) | Problem statement |

---

## Testing

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

---

## Deployment

### Docker

```bash
docker build -t quickserve-ml .
docker run -p 8000:8000 quickserve-ml
```

### Production Considerations

1. **Scaling**: Use multiple uvicorn workers
2. **Monitoring**: Add Prometheus metrics endpoint
3. **Logging**: Configure structured logging for debugging
4. **Model Updates**: Hot-reload models without downtime

---

## License

MIT License - See LICENSE file for details.
