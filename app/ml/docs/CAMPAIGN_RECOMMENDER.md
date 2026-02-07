# Campaign Recommendation System

**Project**: QuickServe Kitchens Marketing AI  
**Version**: 1.0  
**Last Updated**: February 7, 2026

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Components](#components)
4. [Algorithm](#algorithm)
5. [API Reference](#api-reference)
6. [Training Pipeline](#training-pipeline)
7. [Files Reference](#files-reference)
8. [Usage Examples](#usage-examples)

---

## Overview

The Campaign Recommendation System is an ML-powered marketing platform that suggests optimal promotional campaigns based on historical performance, contextual factors, and business constraints.

### Key Features

| Feature | Description |
|---------|-------------|
| **Contextual Bandits** | Thompson Sampling for exploration-exploitation |
| **XGBoost Predictions** | Predict campaign ROI using 15+ contextual features |
| **Item Affinity Analysis** | Discover high-performing item combinations |
| **Seasonal Awareness** | Auto-adjust recommendations for seasons/holidays |
| **Online Learning** | Continuous improvement from campaign feedback |

### Performance Metrics

The system optimizes for:
- **ROI**: Primary metric (revenue lift vs discount cost)
- **Uplift**: Order volume increase during campaign
- **Revenue**: Total revenue during campaign period

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    CAMPAIGN RECOMMENDATION SYSTEM                │
└─────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────┐
│  LAYER 1: DATA ANALYSIS (CampaignAnalyzer)                        │
├───────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Historical Data:                                                 │
│  ┌────────────┐  ┌───────────────┐  ┌────────────────┐           │
│  │   Orders   │  │   Campaigns   │  │  Order Items   │           │
│  │   (CSV)    │  │    (JSON)     │  │    (CSV)       │           │
│  └─────┬──────┘  └───────┬───────┘  └───────┬────────┘           │
│        │                 │                   │                    │
│        └─────────────────┼───────────────────┘                    │
│                          ▼                                        │
│              ┌───────────────────────┐                            │
│              │  Campaign Metrics     │                            │
│              │  • Uplift %           │                            │
│              │  • ROI                │                            │
│              │  • Item performance   │                            │
│              │  • Context features   │                            │
│              └───────────────────────┘                            │
│                          │                                        │
│                          ▼                                        │
│              ┌───────────────────────┐                            │
│              │  Item Affinity Matrix │                            │
│              │  (co-purchase lift)   │                            │
│              └───────────────────────┘                            │
└───────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌───────────────────────────────────────────────────────────────────┐
│  LAYER 2: RECOMMENDATION ENGINE (CampaignRecommender)             │
├───────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────┐    ┌─────────────────┐                     │
│  │ Thompson Sampling │    │  XGBoost Model  │                     │
│  │ (Exploration)     │    │  (ROI Predict)  │                     │
│  └────────┬─────────┘    └────────┬────────┘                     │
│           │                       │                               │
│           └───────────┬───────────┘                               │
│                       ▼                                           │
│           ┌───────────────────────┐                               │
│           │  Priority Scoring     │                               │
│           │  • 50% Expected ROI   │                               │
│           │  • 30% Exploration    │                               │
│           │  • 20% Confidence     │                               │
│           └───────────────────────┘                               │
│                       │                                           │
│           ┌───────────┴───────────┐                               │
│           ▼                       ▼                               │
│  ┌────────────────┐   ┌─────────────────────┐                    │
│  │ Template-Based │   │  Novel Campaigns    │                    │
│  │ Recommendations│   │  (Affinity/Season)  │                    │
│  └────────────────┘   └─────────────────────┘                    │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌───────────────────────────────────────────────────────────────────┐
│  LAYER 3: API ENDPOINTS                                           │
├───────────────────────────────────────────────────────────────────┤
│                                                                   │
│  POST /recommend/campaigns     → Get recommendations              │
│  POST /recommend/campaigns/feedback → Submit performance feedback │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

---

## Components

### 1. CampaignAnalyzer (`src/campaign_analyzer.py`)

Analyzes historical campaign performance to extract patterns and metrics.

```python
@dataclass
class CampaignMetrics:
    campaign_id: str
    start_date: datetime
    end_date: datetime
    items_included: List[str]
    discount: float
    
    # Performance
    avg_daily_orders_during: float
    avg_daily_orders_before: float
    uplift_percentage: float
    
    # Profitability
    roi: float
    gross_margin: float
    
    # Context
    day_of_week_start: int
    season: str
    was_holiday: bool
```

**Key Methods**:
- `analyze_campaign_effectiveness()` - Calculate metrics for all campaigns
- `extract_item_affinity()` - Build co-purchase lift matrix
- `find_temporal_patterns()` - Discover time-based trends

### 2. CampaignRecommender (`src/campaign_recommender.py`)

Generates campaign recommendations using contextual bandits.

```python
@dataclass
class CampaignRecommendation:
    campaign_id: str
    items: List[str]
    discount_percentage: float
    start_date: str
    end_date: str
    duration_days: int
    
    # Predictions
    expected_uplift: float
    expected_roi: float
    expected_revenue: float
    confidence_score: float
    
    # Reasoning
    reasoning: str
    priority_score: float
```

**Key Methods**:
- `fit()` - Train recommendation model
- `recommend_campaigns()` - Generate recommendations
- `update_from_feedback()` - Online learning from results

---

## Algorithm

### Thompson Sampling

The system uses **Thompson Sampling** for balancing exploration (trying new campaigns) and exploitation (using proven campaigns).

```
For each campaign template:
    1. Initialize Beta(α=1, β=1) prior
    2. On success: α += 1
    3. On failure: β += 1
    4. Sample probability p ~ Beta(α, β)
    5. Use p in priority scoring
```

### Priority Score Calculation

```
priority_score = (
    0.50 × expected_roi +
    0.30 × thompson_sample × 100 +
    0.20 × confidence × 100
)
```

Where:
- **expected_roi**: XGBoost prediction for campaign ROI
- **thompson_sample**: Random draw from Beta distribution
- **confidence**: min(observations / 10, 1.0)

### Features for ROI Prediction

| Category | Features |
|----------|----------|
| **Campaign** | discount, duration_days, num_items |
| **Temporal** | day_of_week, hour_of_day, is_weekend |
| **Seasonal** | season_winter, season_spring, season_summer, season_fall |
| **Context** | was_holiday, avg_temperature, good_weather_ratio |
| **Historical** | avg_orders_before |

---

## API Reference

### Get Campaign Recommendations

**Endpoint**: `POST /recommend/campaigns`

**Request Body**:
```json
{
  "lat": 40.7128,
  "lon": -74.0060,
  "start_date": "2026-02-01",
  "num_days": 30,
  "orders": [...],
  "campaigns": [...],
  "order_items": [...],
  "num_recommendations": 5,
  "max_discount": 30.0,
  "min_campaign_duration_days": 3,
  "max_campaign_duration_days": 14,
  "available_items": ["burger", "salad", "pizza"]
}
```

**Response**:
```json
{
  "recommendations": [
    {
      "campaign_id": "rec_template_0_1705758645",
      "items": ["burger_classic", "fries_regular"],
      "discount_percentage": 15.0,
      "start_date": "2026-02-08",
      "end_date": "2026-02-15",
      "duration_days": 7,
      "expected_uplift": 22.5,
      "expected_roi": 85.3,
      "expected_revenue": 12500.0,
      "confidence_score": 0.8,
      "reasoning": "Recommended because: historically high ROI (95.2%), optimal day of week, predicted ROI: 85.3%",
      "priority_score": 72.4
    }
  ],
  "analysis_summary": {
    "total_campaigns_analyzed": 15,
    "avg_historical_roi": 45.2,
    "best_performing_items": ["burger_classic", "salad_caesar"],
    "successful_campaigns": 12
  }
}
```

### Submit Campaign Feedback

**Endpoint**: `POST /recommend/campaigns/feedback`

**Request Body**:
```json
{
  "campaign_id": "rec_template_0_1705758645",
  "actual_roi": 92.5,
  "actual_uplift": 28.3,
  "success": true
}
```

**Response**:
```json
{
  "status": "success",
  "message": "Feedback for rec_template_0_1705758645 received",
  "thompson_params_updated": true
}
```

---

## Training Pipeline

### 1. Prepare Training Data

Required files in `data/training/`:
- `orders.csv` - Historical orders
- `campaigns.csv` - Past campaign definitions
- `order_items.csv` - Order-item relationships

### 2. Train Model

```bash
python src/train_campaign_model.py --data-dir data/training --output-dir data/models
```

### 3. Output Files

```
data/models/
├── campaign_recommender.json         # Template parameters
├── campaign_recommender_metadata.json # Training metadata
└── campaign_recommender_model.xgb    # XGBoost model
```

### 4. Programmatic Training

```python
from src.campaign_analyzer import CampaignAnalyzer
from src.campaign_recommender import CampaignRecommender

# Initialize analyzer
analyzer = CampaignAnalyzer()

# Analyze historical campaigns
analyzer.analyze_campaign_effectiveness(orders_df, campaigns, order_items_df)
analyzer.extract_item_affinity(order_items_df)

# Train recommender
recommender = CampaignRecommender(analyzer)
recommender.fit(use_xgboost=True)

# Save model
recommender.save_model("data/models/campaign_recommender.json")
```

---

## Files Reference

| File | Description |
|------|-------------|
| `src/campaign_analyzer.py` | Historical campaign analysis |
| `src/campaign_recommender.py` | Recommendation engine |
| `src/train_campaign_model.py` | Training script |
| `api/campaign_models.py` | Pydantic API models |
| `data/models/campaign_recommender.json` | Trained model |


---

## Usage Examples

### Generate Recommendations

```python
from datetime import datetime
from src.campaign_recommender import CampaignRecommender, RecommenderContext

# Create context
context = RecommenderContext(
    current_date=datetime.now(),
    day_of_week=datetime.now().weekday(),
    hour=14,
    season='winter',
    recent_avg_daily_revenue=5000.0,
    recent_avg_daily_orders=150.0,
    recent_trend='stable',
    max_discount=25.0,
    available_items=['burger', 'salad', 'pizza', 'soup']
)

# Get recommendations
recommendations = recommender.recommend_campaigns(
    context=context,
    num_recommendations=5,
    optimize_for='roi'
)

for rec in recommendations:
    print(f"{rec.campaign_id}: {rec.items} @ {rec.discount_percentage}%")
    print(f"  Expected ROI: {rec.expected_roi:.1f}%")
    print(f"  Reasoning: {rec.reasoning}")
```

### Update from Feedback

```python
# After campaign completes
recommender.update_from_feedback(
    campaign_id="rec_template_0_1705758645",
    actual_roi=92.5,
    success=True
)
```

---

## Exploration Strategies

### 1. Template-Based (Exploitation)

Uses historically successful campaign templates with Thompson Sampling for selection.

### 2. Item Affinity (Exploration)

Generates novel campaigns by combining items with high co-purchase lift scores.

### 3. Seasonal (Exploration)

Creates seasonal campaigns based on keyword matching:
- **Winter**: soup, hot, warm, comfort, stew
- **Summer**: salad, cold, ice, fresh, light
- **Spring**: fresh, salad, light, vegetable
- **Fall**: pumpkin, soup, warm, hearty

---

## Configuration

Key parameters in `RecommenderContext`:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `max_discount` | 30.0 | Maximum discount percentage |
| `min_campaign_duration_days` | 3 | Minimum campaign length |
| `max_campaign_duration_days` | 14 | Maximum campaign length |
| `exploration_rate` | 0.1 | Probability of exploring novel campaigns |

---

## Future Improvements

1. **Deep Learning**: Replace XGBoost with neural network for complex pattern recognition
2. **Multi-Objective Optimization**: Pareto optimization for ROI vs. customer acquisition
3. **A/B Testing Integration**: Automated experiment design and analysis
4. **Customer Segmentation**: Personalized recommendations per customer segment
5. **Real-Time Adjustment**: Dynamic discount adjustment during campaign
