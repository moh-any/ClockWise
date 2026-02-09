# Data Collection API - Backend Integration Guide

## Overview

The Data Collection API provides real-time metrics for surge detection. Instead of storing data in Redis, the API exposes endpoints that your backend team can call to retrieve collected metrics and store them in your database.

## Architecture

```
┌─────────────────┐      ┌──────────────────┐      ┌─────────────┐
│  Your Backend   │ ───> │  Collection API  │ ───> │  Your DB    │
│  (Every 5 min)  │      │  (FastAPI)       │      │             │
└─────────────────┘      └──────────────────┘      └─────────────┘
                               │
                               ├─> ML Model (predictions)
                               ├─> Social Media APIs
                               └─> Historical orders
```

## Base URL

```
http://localhost:8000/api/v1/collect
```

*(Update with your production URL)*

## Endpoints

### 1. Collect Single Venue Metrics

**POST** `/api/v1/collect/venue`

Collects real-time metrics for a single venue.

**Request Body:**
```json
{
  "place_id": 123,
  "name": "Sample Restaurant",
  "latitude": 55.6761,
  "longitude": 12.5683
}
```

**Response:**
```json
{
  "place_id": 123,
  "timestamp": "2026-02-06T14:30:00",
  "actual_items": 150,
  "actual_orders": 35,
  "predicted_items": 100.0,
  "predicted_orders": 25.0,
  "ratio": 1.5,
  "excess_demand": 50.0,
  "social_signals": {
    "composite_score": 0.75,
    "twitter_mentions": 10,
    "twitter_sentiment": 0.8
  }
}
```

### 2. Collect Batch Metrics (Recommended)

**POST** `/api/v1/collect/batch`

Collects metrics for multiple venues in one call. **Use this for better performance.**

**Request Body:**
```json
{
  "venues": [
    {
      "place_id": 123,
      "name": "Restaurant A",
      "latitude": 55.6761,
      "longitude": 12.5683
    },
    {
      "place_id": 124,
      "name": "Restaurant B",
      "latitude": 55.6867,
      "longitude": 12.5700
    }
  ]
}
```

**Response:**
```json
{
  "metrics": [
    {
      "place_id": 123,
      "timestamp": "2026-02-06T14:30:00",
      "actual_items": 150,
      "actual_orders": 35,
      "predicted_items": 100.0,
      "predicted_orders": 25.0,
      "ratio": 1.5,
      "excess_demand": 50.0,
      "social_signals": {
        "composite_score": 0.75
      }
    },
    {
      "place_id": 124,
      "timestamp": "2026-02-06T14:30:00",
      "actual_items": 200,
      "actual_orders": 50,
      "predicted_items": 120.0,
      "predicted_orders": 30.0,
      "ratio": 1.67,
      "excess_demand": 80.0,
      "social_signals": {
        "composite_score": 0.85
      }
    }
  ],
  "summary": {
    "total_venues": 2,
    "successful": 2,
    "failed": 0,
    "duration_seconds": 1.23,
    "avg_time_per_venue": 0.615
  }
}
```

### 3. Health Check

**GET** `/api/v1/collect/health`

Check if the data collector is running and healthy.

**Response:**
```json
{
  "status": "healthy",
  "data_collector": true,
  "ml_model_loaded": true,
  "social_apis": true,
  "update_interval_seconds": 300,
  "message": "Data collector ready"
}
```

## Integration Steps

### Step 1: Set Up Scheduled Job

Create a scheduled job (cron/celery) that runs **every 5 minutes**:

```python
# Example using Python (pseudo-code)
import requests
from datetime import datetime

def collect_metrics_job():
    """Run every 5 minutes"""
    
    # 1. Query your database for active venues
    venues = db.query("""
        SELECT id as place_id, name, latitude, longitude
        FROM dim_places
        WHERE accepting_orders = true AND active = true
    """)
    
    # 2. Call batch collection API
    response = requests.post(
        "http://localhost:8000/api/v1/collect/batch",
        json={"venues": venues},
        timeout=60
    )
    
    if response.status_code == 200:
        data = response.json()
        
        # 3. Store each venue's metrics in your database
        for metrics in data['metrics']:
            store_metrics_in_db(metrics)
        
        print(f"✅ Collected {len(data['metrics'])} venue metrics")
    else:
        print(f"❌ API call failed: {response.status_code}")
```

### Step 2: Create Database Table

Create a table to store the collected metrics:

```sql
CREATE TABLE surge_metrics (
    id SERIAL PRIMARY KEY,
    place_id INTEGER NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    actual_items INTEGER NOT NULL,
    actual_orders INTEGER NOT NULL,
    predicted_items FLOAT NOT NULL,
    predicted_orders FLOAT NOT NULL,
    ratio FLOAT NOT NULL,
    excess_demand FLOAT NOT NULL,
    social_composite_score FLOAT,
    social_twitter_mentions INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_place_timestamp (place_id, timestamp),
    INDEX idx_timestamp (timestamp)
);
```

### Step 3: Store Metrics Function

```python
def store_metrics_in_db(metrics: dict):
    """Store single venue metrics"""
    
    query = """
    INSERT INTO surge_metrics (
        place_id, timestamp, actual_items, actual_orders,
        predicted_items, predicted_orders, ratio, excess_demand,
        social_composite_score, social_twitter_mentions
    ) VALUES (
        %(place_id)s, %(timestamp)s, %(actual_items)s, %(actual_orders)s,
        %(predicted_items)s, %(predicted_orders)s, %(ratio)s, 
        %(excess_demand)s, %(social_composite_score)s,
        %(social_twitter_mentions)s
    )
    """
    
    params = {
        'place_id': metrics['place_id'],
        'timestamp': metrics['timestamp'],
        'actual_items': metrics['actual_items'],
        'actual_orders': metrics['actual_orders'],
        'predicted_items': metrics['predicted_items'],
        'predicted_orders': metrics['predicted_orders'],
        'ratio': metrics['ratio'],
        'excess_demand': metrics['excess_demand'],
        'social_composite_score': metrics['social_signals'].get('composite_score'),
        'social_twitter_mentions': metrics['social_signals'].get('twitter_mentions')
    }
    
    db.execute(query, params)
```

## Metrics Explanation

| Field | Type | Description |
|-------|------|-------------|
| `place_id` | int | Venue/restaurant ID |
| `timestamp` | string | ISO 8601 timestamp when metrics were collected |
| `actual_items` | int | Actual items ordered in last hour |
| `actual_orders` | int | Actual number of orders in last hour |
| `predicted_items` | float | ML model prediction for items |
| `predicted_orders` | float | ML model prediction for orders |
| `ratio` | float | actual_items / predicted_items (surge indicator) |
| `excess_demand` | float | actual_items - predicted_items |
| `social_signals` | dict | Social media activity signals |

**Surge Detection Logic:**
- `ratio > 1.3`: Possible surge (30% above prediction)
- `ratio > 1.5`: Strong surge (50% above prediction)
- `ratio > 2.0`: Critical surge (100% above prediction)

## Error Handling

The API returns standard HTTP status codes:

- `200 OK`: Success
- `500 Internal Server Error`: Collection failed for a venue
- `503 Service Unavailable`: Data collector not available

**Handle errors gracefully:**
```python
try:
    response = requests.post(api_url, json=payload, timeout=60)
    response.raise_for_status()
except requests.exceptions.Timeout:
    logger.error("API timeout - collector may be overloaded")
except requests.exceptions.RequestException as e:
    logger.error(f"API error: {e}")
```

## Performance Considerations

- **Batch endpoint is faster**: Use `/batch` instead of multiple `/venue` calls
- **Expected response time**: 0.5-1s per venue
- **Timeout recommendation**: Set 60s timeout for batch requests
- **Rate limiting**: Consider if calling for 100+ venues

## Testing

### Start the API server:
```bash
cd app/ml
python -m uvicorn api.main:app --reload --port 8000
```

### Test with curl:
```bash
# Single venue
curl -X POST "http://localhost:8000/api/v1/collect/venue" \
  -H "Content-Type: application/json" \
  -d '{
    "place_id": 123,
    "name": "Test Restaurant",
    "latitude": 55.6761,
    "longitude": 12.5683
  }'

# Health check
curl "http://localhost:8000/api/v1/collect/health"
```

### Test with Python:
```python
import requests

# Test single venue
response = requests.post(
    "http://localhost:8000/api/v1/collect/venue",
    json={
        "place_id": 123,
        "name": "Test Restaurant",
        "latitude": 55.6761,
        "longitude": 12.5683
    }
)
print(response.json())
```

## API Documentation

Interactive API documentation is available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Support

For questions or issues:
1. Check API health endpoint first
2. Review logs for error details
3. Verify venue data (lat/lon, place_id)
4. Contact ML team for model-related issues

## Next Steps

After integrating the collection API:
1. Implement the surge detection rules (ratio thresholds)
2. Set up alerts when surges are detected
3. Integrate with Layer 2 (scheduler) for staff adjustments
4. Monitor collection performance and adjust intervals if needed
