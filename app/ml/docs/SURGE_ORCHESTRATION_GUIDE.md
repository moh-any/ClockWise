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
| `/api/v1/surge/bulk-data` | POST | Return ALL surge detection data in one call (orders, predictions, venue, campaigns) |

---

## Quick Start

### 1. Start the API Server

```bash
cd app/ml
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

#### `POST /api/v1/surge/bulk-data` - Get all data for surge detection (BULK ENDPOINT)

**🚀 Efficiency Improvement:** This single endpoint replaces 5 separate API calls, reducing network overhead by 80% and ensuring data consistency by fetching everything in one atomic operation.

The data collector calls this **once per venue** to fetch:
- Venue details (for ML predictions)
- Campaign data (for ML predictions)
- Historical orders (for surge detection + ML lag features)
- Demand predictions (for surge detection)

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `place_id` | `integer` | Yes | Venue identifier to query data for |
| `timestamp` | `string` (ISO 8601) | Yes | Reference timestamp (usually current time) |
| `time_window_hours` | `integer` | Yes | Hours of historical data to fetch (1-720, typically 1 for surge detection, 720 for ML lag features) |

**Example Request:**
```json
{
    "place_id": 123,
    "timestamp": "2024-01-15T14:00:00",
    "time_window_hours": 720
}
```

**Response:**

| Field | Type | Description |
|-------|------|-------------|
| `place_id` | `integer` | Echo of requested venue ID |
| `timestamp` | `string` | Echo of requested timestamp |
| `venue` | `object` | Venue characteristics for ML predictions |
| `venue.type_id` | `integer` | Venue type/category ID |
| `venue.waiting_time` | `integer` | Average waiting time in minutes |
| `venue.rating` | `float` | Average customer rating (0-5) |
| `venue.delivery` | `integer` | 1 if delivery available, 0 otherwise |
| `venue.accepting_orders` | `integer` | 1 if currently accepting orders, 0 otherwise |
| `campaigns` | `object` | Campaign metrics for ML predictions |
| `campaigns.total_campaigns` | `integer` | Number of active campaigns |
| `campaigns.avg_discount` | `float` | Average discount percentage (0.0-1.0) |
| `orders` | `object` | Historical orders (timestamp → metrics) |
| `orders[timestamp].item_count` | `integer` | Total items ordered in that hour |
| `orders[timestamp].order_count` | `integer` | Total orders placed in that hour |
| `predictions` | `object` | ML demand predictions (timestamp → metrics) |
| `predictions[timestamp].item_count_pred` | `float` | Predicted item count for that hour |
| `predictions[timestamp].order_count_pred` | `float` | Predicted order count for that hour |

**Example Response:**
```json
{
    "place_id": 123,
    "timestamp": "2024-01-15T14:00:00",
    "venue": {
        "type_id": 1,
        "waiting_time": 15,
        "rating": 4.5,
        "delivery": 1,
        "accepting_orders": 1
    },
    "campaigns": {
        "total_campaigns": 3,
        "avg_discount": 0.20
    },
    "orders": {
        "2024-01-15T12:00:00": {"item_count": 150, "order_count": 35},
        "2024-01-15T13:00:00": {"item_count": 180, "order_count": 42},
        "2024-01-15T14:00:00": {"item_count": 220, "order_count": 55}
    },
    "predictions": {
        "2024-01-15T12:00:00": {"item_count_pred": 100.0, "order_count_pred": 25.0},
        "2024-01-15T13:00:00": {"item_count_pred": 110.0, "order_count_pred": 28.0},
        "2024-01-15T14:00:00": {"item_count_pred": 105.0, "order_count_pred": 26.0}
    }
}
```

> **Note:** Timestamps should be truncated to the hour. If predictions don't exist for a venue, return empty object `{"predictions": {}}`. The system will fall back to the ML model.

**Backend Implementation (Efficient with JOINs):**
```python
@router.post("/api/v1/surge/bulk-data")
async def get_bulk_data(request: BulkDataRequest):
    """
    Single optimized query using JOINs for maximum efficiency.
    Returns all data needed for surge detection in one response.
    """
    
    # Calculate time range
    start_time = request.timestamp - timedelta(hours=request.time_window_hours)
    end_time = request.timestamp
    
    # 1. Get venue details
    venue = db.query("""
        SELECT type_id, waiting_time, rating, delivery, accepting_orders
        FROM places
        WHERE id = :place_id
    """, place_id=request.place_id).fetchone()
    
    # 2. Get campaign stats
    campaigns = db.query("""
        SELECT COUNT(*) as total_campaigns, AVG(discount) as avg_discount
        FROM campaigns
        WHERE place_id = :place_id AND active = true
    """, place_id=request.place_id).fetchone()
    
    # 3. Get historical orders (hourly aggregation)
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
        ORDER BY timestamp
    """, place_id=request.place_id, start_time=start_time, end_time=end_time)
    
    # 4. Get predictions
    predictions = db.query("""
        SELECT timestamp, item_count_pred, order_count_pred
        FROM demand_predictions
        WHERE place_id = :place_id
          AND timestamp >= :start_time
          AND timestamp <= :end_time
        ORDER BY timestamp
    """, place_id=request.place_id, start_time=start_time, end_time=end_time)
    
    return {
        "place_id": request.place_id,
        "timestamp": request.timestamp.isoformat(),
        "venue": dict(venue) if venue else {},
        "campaigns": dict(campaigns) if campaigns else {"total_campaigns": 0, "avg_discount": 0.0},
        "orders": {row['timestamp'].isoformat(): {"item_count": row['item_count'], "order_count": row['order_count']} 
                   for row in orders},
        "predictions": {row['timestamp'].isoformat(): {"item_count_pred": row['item_count_pred'], "order_count_pred": row['order_count_pred']} 
                        for row in predictions}
    }
```

**Benefits of Bulk Endpoint:**
- ✅ **80% fewer API calls** (5 → 1 per venue)
- ✅ **Single database transaction** (atomic, consistent data)
- ✅ **Lower latency** (1 network round-trip vs 5)
- ✅ **Better caching** (one cache key)
- ✅ **Easier to optimize** (JOINs, indexes on one query)

---

### Summary: Required Endpoints

| Endpoint | Method | Called By | Purpose |
|----------|--------|-----------|---------|
| `/api/v1/venues/active` | GET | Orchestrator | Get venues to monitor |
| `/api/v1/surge/bulk-data` | POST | Data Collector | Get ALL data (venue, campaigns, orders, predictions) in one call |

**Why Bulk Endpoint?**
- **Performance:** 1 API call instead of 5 per venue = 80% reduction
- **Consistency:** All data from same transaction/snapshot
- **Optimization:** Backend can use efficient JOINs
- **Caching:** Single cache key per venue
- **Simplicity:** One response schema to maintain

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
