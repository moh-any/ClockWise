# Surge Detection System - Backend Integration Guide

## Overview

The surge detection system monitors restaurant venues in real-time and detects unexpected demand surges. It integrates three layers:

| Layer | Component | Purpose |
|-------|-----------|---------|
| Layer 1 | `data_collector.py` | Collect orders, predictions, social signals |
| Layer 2 | `surge_detector.py` | Detect surges by analyzing metrics |
| Layer 3 | `alert_system.py` | Format alerts (email only) with optional LLM analysis |

**Orchestrator:** `surge_orchestrator.py` - Background task that runs all layers every 5 minutes

**API:** `surge_api.py` - FastAPI endpoints for control and manual operations

### Architecture: API-Only Communication

The surge detection system communicates **exclusively via API endpoints** - there are no direct database queries in the codebase. This design allows the backend team to:

- Control data access and security
- Implement caching strategies
- Add rate limiting and authentication
- Use any database technology

**Required API Endpoints (Backend Team Must Implement):**

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/venues/active` | GET | Return list of active venues |
| `/api/v1/orders/query` | POST | Return historical orders for a venue |
| `/api/v1/predictions/query` | POST | Return demand predictions for a venue |

---

## Quick Start

### 1. Start the API Server

```bash
cd c:\Users\Lenovo\deloitte
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Start Surge Orchestrator

**Option A: Via API call**
```bash
curl -X POST http://localhost:8000/api/v1/surge/orchestrator/start
```

**Option B: Standalone background process**
```bash
python src/surge_orchestrator.py
```

### 3. Check Status
```bash
curl http://localhost:8000/api/v1/surge/orchestrator/status
```

---

## API Endpoints

Base URL: `http://localhost:8000/api/v1/surge`

### Orchestrator Control

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/orchestrator/start` | Start background monitoring |
| `POST` | `/orchestrator/stop` | Stop background monitoring |
| `POST` | `/orchestrator/pause` | Pause (keeps task, skips cycles) |
| `POST` | `/orchestrator/resume` | Resume after pause |
| `GET` | `/orchestrator/status` | Get current status |
| `GET` | `/orchestrator/history` | Get recent cycle history |

### Surge Detection

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/check` | Manual check with custom metrics |
| `POST` | `/check/single` | Check single venue (live data) |
| `POST` | `/check/batch` | Check multiple venues |

### Configuration & Monitoring

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/config` | Get current configuration |
| `PUT` | `/config` | Update configuration |
| `GET` | `/health` | Health check |
| `GET` | `/metrics` | Detection metrics |
| `GET` | `/alerts/recent` | Recent alert history |

---

## Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SURGE ORCHESTRATOR (Every 5 min)                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐          │
│  │   LAYER 1       │    │   LAYER 2       │    │   LAYER 3       │          │
│  │ Data Collector  │───>│ Surge Detector  │───>│ Alert Dispatcher│          │
│  │                 │    │                 │    │                 │          │
│  │ • Actual orders │    │ • Analyze ratio │    │ • Format email  │          │
│  │ • Predictions   │    │ • Check trend   │    │ • LLM analysis  │          │
│  │ • Social media  │    │ • Calculate risk│    │ • Recommendations│          │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘          │
│                                                        │                    │
│                                                        ▼                    │
│                                               ┌─────────────────┐           │
│                                               │ Alert Callback  │           │
│                                               │ (Backend Team)  │           │
│                                               └─────────────────┘           │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Backend Team Implementation Tasks

### 1. Implement Alert Callback

When a surge is detected, the orchestrator calls your callback function. Implement this to:

```python
def handle_alert(alert: dict, venue: dict):
    """
    Called when a surge alert is generated.
    
    Args:
        alert: {
            'severity': 'moderate'|'high'|'critical',
            'subject': '⚠️ HIGH SURGE ALERT - Pizza Paradise',
            'message': '...formatted alert message...',
            'channels': ['email'],  # Always email only
            'timestamp': '2024-01-15T14:30:00'
        }
        venue: {
            'place_id': 123,
            'name': 'Pizza Paradise',
            'latitude': 55.6761,
            'longitude': 12.5683
        }
    """
    # 1. Store alert in database
    AlertModel.create(
        place_id=venue['place_id'],
        severity=alert['severity'],
        message=alert['message'],
        created_at=alert['timestamp']
    )
    
    # 2. Send email notification
    send_email(
        to=get_venue_managers(venue['place_id']),
        subject=alert['subject'],
        body=alert['message']
    )
    
    # 3. Update admin dashboard
    push_to_dashboard(alert, venue)
```

Register your callback:
```python
from surge_orchestrator import get_orchestrator

orchestrator = get_orchestrator()
orchestrator.set_alert_callback(handle_alert)
```

### 2. Implement Required API Endpoints

The surge detection system communicates **only via API endpoints** - no direct database queries. 
Backend team must implement these endpoints:

---

#### `GET /api/v1/venues/active` - Get venues to monitor

The orchestrator calls this to get the list of venues to check for surges.

**Request:** No body required

**Response:**

| Field | Type | Description |
|-------|------|-------------|
| `venues` | `array` | List of active venue objects |
| `venues[].place_id` | `integer` | **Required.** Unique venue identifier |
| `venues[].name` | `string` | **Required.** Venue display name (used in alerts) |
| `venues[].latitude` | `float` | **Required.** Venue latitude for social media geo-search |
| `venues[].longitude` | `float` | **Required.** Venue longitude for social media geo-search |

**Example Response:**
```json
{
    "venues": [
        {
            "place_id": 123,
            "name": "Pizza Paradise",
            "latitude": 55.6761,
            "longitude": 12.5683
        },
        {
            "place_id": 456,
            "name": "Burger House",
            "latitude": 55.6800,
            "longitude": 12.5700
        }
    ]
}
```

**Backend Implementation:**
```python
@router.get("/api/v1/venues/active")
async def get_active_venues():
    venues = db.query("""
        SELECT id as place_id, name, latitude, longitude 
        FROM places 
        WHERE accepting_orders = true AND active = true
    """)
    return {"venues": [dict(v) for v in venues]}
```

---

#### `POST /api/v1/orders/query` - Get historical orders

The data collector calls this to fetch actual order data for surge detection.

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `place_id` | `integer` | Yes | Venue identifier to query orders for |
| `time_window_hours` | `integer` | Yes | Number of hours to look back (typically 1-3) |
| `end_time` | `string` (ISO 8601) | Yes | End timestamp for query window |

**Example Request:**
```json
{
    "place_id": 123,
    "time_window_hours": 3,
    "end_time": "2024-01-15T14:00:00"
}
```

**Response:**

| Field | Type | Description |
|-------|------|-------------|
| `orders` | `object` | Dictionary mapping ISO timestamp → order metrics |
| `orders[timestamp].item_count` | `integer` | **Required.** Total items ordered in that hour |
| `orders[timestamp].order_count` | `integer` | **Required.** Total orders placed in that hour |

**Example Response:**
```json
{
    "orders": {
        "2024-01-15T12:00:00": {"item_count": 150, "order_count": 35},
        "2024-01-15T13:00:00": {"item_count": 180, "order_count": 42},
        "2024-01-15T14:00:00": {"item_count": 220, "order_count": 55}
    }
}
```

> **Note:** Timestamps should be truncated to the hour. Each key represents an hourly bucket.

**Backend Implementation:**
```python
@router.post("/api/v1/orders/query")
async def query_orders(request: OrderQueryRequest):
    orders = db.query("""
        SELECT 
            date_trunc('hour', created_at) as timestamp,
            COUNT(*) as order_count,
            SUM(item_count) as item_count
        FROM orders
        WHERE place_id = :place_id
          AND created_at >= :start_time
          AND created_at <= :end_time
        GROUP BY date_trunc('hour', created_at)
    """, place_id=request.place_id, ...)
    return {"orders": format_orders(orders)}
```

---

#### `POST /api/v1/predictions/query` - Get demand predictions

The data collector calls this to fetch ML model predictions for comparison with actual orders.

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `place_id` | `integer` | Yes | Venue identifier to query predictions for |
| `time_window_hours` | `integer` | Yes | Number of hours to look back (typically 1-3) |
| `end_time` | `string` (ISO 8601) | Yes | End timestamp for query window |

**Example Request:**
```json
{
    "place_id": 123,
    "time_window_hours": 3,
    "end_time": "2024-01-15T14:00:00"
}
```

**Response:**

| Field | Type | Description |
|-------|------|-------------|
| `predictions` | `object` | Dictionary mapping ISO timestamp → prediction metrics |
| `predictions[timestamp].item_count_pred` | `float` | **Required.** Predicted item count for that hour |
| `predictions[timestamp].order_count_pred` | `float` | **Required.** Predicted order count for that hour |

**Example Response:**
```json
{
    "predictions": {
        "2024-01-15T12:00:00": {"item_count_pred": 100.0, "order_count_pred": 25.0},
        "2024-01-15T13:00:00": {"item_count_pred": 110.0, "order_count_pred": 28.0},
        "2024-01-15T14:00:00": {"item_count_pred": 105.0, "order_count_pred": 26.0}
    }
}
```

> **Note:** If no predictions exist for a venue, return an empty object `{"predictions": {}}`. The system will fall back to the ML model for real-time predictions.

**Backend Implementation:**
```python
@router.post("/api/v1/predictions/query")
async def query_predictions(request: PredictionQueryRequest):
    predictions = db.query("""
        SELECT timestamp, item_count_pred, order_count_pred
        FROM demand_predictions
        WHERE place_id = :place_id
          AND timestamp >= :start_time
          AND timestamp <= :end_time
    """, place_id=request.place_id, ...)
    return {"predictions": format_predictions(predictions)}
```

---

### Summary: Required Endpoints

| Endpoint | Method | Called By | Purpose |
|----------|--------|-----------|---------|
| `/api/v1/venues/active` | GET | Orchestrator | Get venues to monitor |
| `/api/v1/orders/query` | POST | Data Collector | Get historical orders |
| `/api/v1/predictions/query` | POST | Data Collector | Get ML predictions |

### Error Handling

All endpoints should return appropriate HTTP status codes:

| Status | Meaning | When to Use |
|--------|---------|-------------|
| `200` | Success | Data returned successfully |
| `400` | Bad Request | Invalid request body or parameters |
| `404` | Not Found | Venue not found |
| `500` | Server Error | Database or internal error |

**Error Response Format:**
```json
{
    "error": "Venue not found",
    "detail": "No venue with place_id 999 exists"
}
```

> **Note:** If an API endpoint is unavailable or returns an error, the system falls back to demo/simulated data for testing purposes.

### 3. Environment Configuration

Set these environment variables:

```bash
# Required for LLM analysis (FREE)
GEMINI_API_KEY=your-gemini-api-key

# Optional: Social media APIs
TWITTER_BEARER_TOKEN=your-twitter-token
EVENTBRITE_API_KEY=your-eventbrite-key
```

---

## Configuration Reference

| Parameter | Default | Description |
|-----------|---------|-------------|
| `check_interval_seconds` | 300 | How often to check (5 min) |
| `surge_threshold` | 1.5 | Minimum ratio to detect surge |
| `window_hours` | 3 | Hours of data to analyze |
| `min_excess_items` | 20 | Minimum excess items per hour |
| `cooldown_hours` | 2 | Hours between alerts for same venue |
| `llm_threshold` | 0.7 | Risk score for LLM analysis |
| `enable_llm` | true | Enable Gemini LLM analysis |

Update via API:
```bash
curl -X PUT http://localhost:8000/api/v1/surge/config \
  -H "Content-Type: application/json" \
  -d '{"surge_threshold": 2.0, "check_interval_seconds": 600}'
```

---

## Surge Detection Logic

### Detection Criteria

A surge is detected when ALL conditions are met over the analysis window:

1. **Ratio Threshold**: `actual / predicted >= 1.5` for all hours in window
2. **Minimum Excess**: `total_excess >= 20 * window_hours` items
3. **Not in Cooldown**: No alert for this venue in last 2 hours

### Severity Levels

| Severity | Ratio Range | Action Timeline |
|----------|------------|-----------------|
| Moderate | 1.5x - 2.0x | Within 30 minutes |
| High | 2.0x - 3.0x | Within 15 minutes |
| Critical | > 3.0x | Immediately (5 min) |

### Risk Score Components

```
risk_score = (ratio_severity × 0.40) + (social_signals × 0.35) + (trend × 0.25)
```

- **Ratio Severity** (40%): How far above threshold
- **Social Signals** (35%): Twitter virality, Google Trends
- **Trend** (25%): Accelerating (+0.1), Stable, Decelerating (-0.1)

---

## Alert Format

All alerts are sent via **email only**. Example format:

```
⚠️ SURGE ALERT - Pizza Paradise
============================================================

CURRENT STATUS:
• Demand Level: 2.6x normal (accelerating)
• Detected At: 2024-01-15 14:30
• Root Cause: Social Media Viral Post
• Risk Score: 0.75/1.0
• Severity: HIGH

DETAILED ANALYSIS:  (if LLM enabled)
• A TikTok video featuring your signature pizza went viral
• Viral Potential: 85%
• Estimated Duration: 4 hours
• Urgency Level: 80%

RECOMMENDED ACTIONS:
1. Call in 2 additional kitchen staff immediately
2. Prepare extra ingredients for popular items
3. Enable overflow mode in ordering system

EXPECTED TIMELINE:
• Estimated Duration: 3-6 hours
• Action Required: Within 15 minutes

------------------------------------------------------------
⏰ IMMEDIATE ACTION REQUIRED
Review and activate emergency schedule as soon as possible.
```

---

## Testing

### Manual Surge Check

```bash
curl -X POST http://localhost:8000/api/v1/surge/check \
  -H "Content-Type: application/json" \
  -d '{
    "venue": {
      "place_id": 123,
      "name": "Test Restaurant"
    },
    "metrics": [
      {"timestamp": "2024-01-15T12:00:00", "actual": 200, "predicted": 100, "social_signals": {}},
      {"timestamp": "2024-01-15T13:00:00", "actual": 220, "predicted": 100, "social_signals": {}},
      {"timestamp": "2024-01-15T14:00:00", "actual": 250, "predicted": 100, "social_signals": {"composite_signal": 0.7}}
    ]
  }'
```

Expected response when surge detected:
```json
{
  "surge_detected": true,
  "alert": {
    "severity": "high",
    "subject": "⚠️ HIGH SURGE ALERT - Test Restaurant",
    "message": "...",
    "channels": ["email"],
    "timestamp": "2024-01-15T14:30:00"
  },
  "surge_event": {
    "place_id": 123,
    "severity": "high",
    "risk_score": 0.75,
    "avg_ratio": 2.23,
    "trend": "accelerating",
    "root_cause": "social_media_trending",
    "recommendations": [...]
  }
}
```

### Run Tests

```bash
pytest tests/test_surge_detector.py -v
pytest tests/test_alert_system.py -v
```

---

## Production Deployment

### Option 1: Background Process with API

```python
# In your FastAPI startup event
from fastapi import FastAPI
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    from surge_orchestrator import get_orchestrator
    orchestrator = get_orchestrator()
    orchestrator.set_alert_callback(your_alert_handler)
    await orchestrator.start()
    
    yield
    
    # Shutdown
    await orchestrator.stop()

app = FastAPI(lifespan=lifespan)
```

### Option 2: Cron Job (Alternative)

If you prefer not to use background tasks, call the batch endpoint every 5 minutes:

```bash
# crontab -e
*/5 * * * * curl -X POST http://localhost:8000/api/v1/surge/check/batch \
  -H "Content-Type: application/json" \
  -d '{"venues": [{"place_id": 1, "name": "Venue 1"}, ...]}' \
  >> /var/log/surge_detection.log 2>&1
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| No surges detected | Lower `surge_threshold` or check metrics data |
| Too many alerts | Increase `cooldown_hours` |
| LLM analysis failing | Check `GEMINI_API_KEY` is set |
| Orchestrator in ERROR state | Check logs, restart with `/orchestrator/start` |
| Slow detection cycles | Reduce number of venues or increase interval |

---

## Files Reference

| File | Purpose |
|------|---------|
| `src/surge_orchestrator.py` | Background task orchestrator |
| `src/surge_api.py` | FastAPI endpoints |
| `src/data_collector.py` | Layer 1 - Data collection |
| `src/surge_detector.py` | Layer 2 - Surge detection |
| `src/alert_system.py` | Layer 3 - Alert formatting |
| `src/llm_analyzer_gemini.py` | FREE LLM analysis |
| `api/main.py` | Main API (surge routes integrated) |

---

## Support

For questions, check the example files:
- `src/example_alert_integration.py` - End-to-end demo
- `src/example_gemini_integration.py` - LLM integration demo
