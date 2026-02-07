# V6 Model Integration Guide

## Overview

The API has been updated to support the new **v6 optimized CatBoost model** which expects **69 features** (up from 33 in the previous version). All new features are automatically generated from existing user-provided data - **no additional API input is required**.

## Model Changes

### Previous Model (v5)
- **33 features** Tested campaign recommendation 
- Random Forest algorithm
- Basic time, lag, weather, and holiday features

### New Model (v6)
- **69 features** 
- CatBoost with Quantile Loss (alpha=0.60)
- 1.63% MAE improvement
- Enhanced feature set with:
  - Cyclical time encoding (6 features)
  - Advanced time context indicators (21 features)
  - Additional lag & rolling windows (7 features)
  - Venue-specific historical patterns (7 features)
  - Weekend-specific patterns (6 features)
  - Weather interaction features (8 features)

## Architecture

### Modular Design

The feature engineering is now modular and reusable across the codebase:

```
app/ml/src/api_feature_engineering.py
├── add_cyclical_time_features()
├── add_time_context_indicators()
├── add_additional_lag_features()
├── add_venue_specific_features()
├── add_weekend_specific_features()
├── add_weather_interaction_features()
└── apply_all_api_features()  ← Main orchestrator
```

### Integration Points

The new feature engineering is integrated into `main.py` at two key locations:

1. **Feature Preparation** (`prepare_features_for_prediction`)
   - Processes historical orders
   - Adds weather and holiday features
   - **NEW:** Calls `apply_all_api_features()` to generate v6 features

2. **Feature Alignment** (`align_features_with_model`) 
   - Ensures exactly 69 features are present
   - Fills missing features with defaults (0)
   - Enforces correct data types

## New Features Breakdown

### 1. Cyclical Time Features (6)
Captures the periodic nature of time:
- `hour_sin`, `hour_cos` - Hour of day (0-23)
- `day_of_week_sin`, `day_of_week_cos` - Day of week (0-6)
- `month_sin`, `month_cos` - Month (1-12)

**Why?** Models can't naturally understand that hour 23 and hour 0 are adjacent. Cyclical encoding fixes this.

### 2. Time Context Indicators (21)
Binary flags for specific time periods:
- Rush hours: `is_breakfast_rush`, `is_lunch_rush`, `is_peak_lunch`, `is_dinner_rush`, `is_peak_dinner`
- Time of day: `is_early_morning`, `is_afternoon`, `is_evening`, `is_late_night`, `is_midnight_zone`
- Day types: `is_weekend`, `is_friday`, `is_saturday`, `is_sunday`
- Interactions: `friday_evening`, `saturday_evening`, `weekend_lunch`, `weekend_dinner`, `weekday_lunch`, `weekday_dinner`
- Month position: `is_month_start`, `is_month_end`

**Why?** Different time periods have distinct demand patterns that the model can learn.

### 3. Additional Lag Features (7)
Extended historical lookback:
- `rolling_3d_avg_items`, `rolling_14d_avg_items`, `rolling_30d_avg_items` - Multiple rolling windows
- `rolling_7d_std_items` - Demand volatility
- `demand_trend_7d` - 7-day trend slope
- `lag_same_hour_last_week`, `lag_same_hour_2_weeks` - Same-hour historical values

**Why?** Different time horizons capture different patterns (short-term vs long-term trends).

### 4. Venue-Specific Features (7)
Restaurant-specific historical patterns:
- `venue_hour_avg` - Average demand for this venue at this hour
- `venue_dow_avg` - Average demand for this venue on this day of week
- `venue_volatility` - How variable this venue's demand is
- `venue_total_items` - Total historical volume (size indicator)
- `venue_growth_recent_vs_historical` - Recent growth trend
- `venue_peak_hour` - This venue's busiest hour
- `is_venue_peak_hour` - Binary flag for peak hour

**Why?** Each restaurant has unique patterns based on location, menu, customer base, etc.

### 5. Weekend-Specific Features (6)
Weekend vs weekday behavioral differences:
- `venue_weekend_avg`, `venue_weekday_avg` - Separate averages
- `venue_weekend_lift` - Ratio of weekend to weekday demand
- `last_weekend_same_hour` - Last weekend's demand at this hour
- `venue_weekend_volatility` - Weekend demand variability
- `weekend_day_position` - Position in weekend (Fri=0, Sat=1, Sun=2)

**Why?** Weekends have fundamentally different demand patterns than weekdays.

### 6. Weather Interaction Features (8)
Complex weather effects:
- `feels_like_temp` - Comfort index (temp - wind + humidity effects)
- `bad_weather_score` - Composite bad weather indicator
- `temp_change_1h`, `temp_change_3h` - Temperature trends
- `weather_getting_worse` - Deteriorating conditions flag
- `weekend_good_weather` - Weekend × good weather interaction
- `rush_bad_weather` - Rush hour × bad weather interaction
- `cold_evening` - Cold × evening interaction

**Why?** Weather effects vary by time of day and day of week (e.g., rain impacts weekends more).

## API Usage

### No Changes Required!

The API endpoints remain **exactly the same**. All new features are computed automatically:

```python
# POST /predict/demand
{
  "place": { ... },           # Same as before
  "orders": [ ... ],          # Same as before
  "campaigns": [ ... ],       # Same as before
  "prediction_start_date": "2026-02-10",
  "prediction_days": 7
}
```

### Backward Compatibility

The system gracefully handles both old and new models:

- If `api_feature_engineering.py` is not available → falls back to basic features
- If a feature is missing → filled with default value (0)
- Old API requests continue to work without modification

## Testing

### Verify Feature Generation

Run the verification script to ensure all 69 features are generated:

```bash
cd app/ml
python tests/test_v6_features.py
```

Expected output:
```
V6 MODEL FEATURE VERIFICATION
=====================================
✓ Feature engineering successful
✓ Total features: 69 columns
✓ VERIFICATION PASSED
```

### Test API Endpoint

```bash
# Start API
cd app/ml
python -m uvicorn api.main:app --reload --port 8000

# Test prediction (use your actual test data)
curl -X POST http://localhost:8000/predict/demand \
  -H "Content-Type: application/json" \
  -d @tests/test_request.json
```

## Reusability

The feature engineering module is designed to be reused anywhere in the codebase:

### Example: Data Collection Pipeline

```python
from src.api_feature_engineering import apply_all_api_features

# Your data collection code
real_time_data = collect_venue_data()

# Apply same features used in training
features = apply_all_api_features(
    df=real_time_data,
    historical_df=historical_data
)

# Now features match the model's expectations
predictions = model.predict(features)
```

### Example: Batch Processor

```python
from src.api_feature_engineering import (
    add_cyclical_time_features,
    add_time_context_indicators,
    add_venue_specific_features
)

# Apply features step-by-step if needed
df = add_cyclical_time_features(df)
df = add_time_context_indicators(df)
df = add_venue_specific_features(df, historical_df)
```

## Performance Considerations

### Memory
- Feature generation adds ~55 columns to the DataFrame
- For 7 days × 24 hours = 168 rows: negligible impact
- For large batch predictions (1000+ venues): monitor memory usage

### Computation Time
- Cyclical features: O(n) - instant
- Time indicators: O(n) - instant
- Lag features: O(n) - fast (vectorized pandas operations)
- Venue statistics: O(n × m) where m = number of unique venues
  - For single-venue API calls: negligible
  - For multi-venue batch: may take 1-5 seconds

### Recommendations
- Single predictions: no optimization needed
- Batch predictions: consider caching venue statistics
- Real-time: pre-compute venue features, update periodically

## Troubleshooting

### Issue: "API feature engineering not available"

**Cause:** `api_feature_engineering.py` not found or import error

**Solution:**
1. Verify file exists: `app/ml/src/api_feature_engineering.py`
2. Check Python path in main.py
3. Install required packages: `pandas`, `numpy`

### Issue: Model expects different number of features

**Cause:** Model file doesn't match v6 metadata

**Solution:**
1. Check model metadata: `data/models/rf_model_metadata.json`
2. Verify `num_features: 69`
3. Retrain model if needed: `python src/train_model.py`

### Issue: NaN values in predictions

**Cause:** Some features couldn't be computed

**Solution:**
1. Check historical data has sufficient history (7+ days recommended)
2. Verify weather API is working
3. Enable fallback defaults in `align_features_with_model()`

### Issue: Poor predictions after upgrade

**Possible causes:**
1. Model file not updated (still using old v5 model)
2. Insufficient historical data for venue features
3. Weather API not providing data

**Solution:**
1. Retrain model with v6 pipeline
2. Require minimum 14 days of history for API calls
3. Verify weather API integration

## Migration Checklist

- [x] Create `api_feature_engineering.py` module
- [x] Update `main.py` imports
- [x] Update `prepare_features_for_prediction()`
- [x] Update `align_features_with_model()` to expect 69 features
- [x] Add graceful fallback if feature engineering unavailable
- [x] Create test script
- [x] Document changes
- [ ] Train new v6 model (if not done)
- [ ] Test API with sample requests
- [ ] Deploy to production
- [ ] Monitor predictions quality
- [ ] Update API documentation

## Future Enhancements

Possible extensions to the feature engineering:

1. **Dynamic venue features**: Update venue statistics regularly from live data
2. **External events**: Integrate sports events, concerts, public holidays
3. **Menu features**: Incorporate item-level popularity and pricing
4. **Competitive features**: Nearby restaurant data
5. **User features**: New vs returning customers, customer segments

## Support

For questions or issues:
- Check logs: Look for "Feature engineering" messages in API logs
- Run verification: `python tests/test_v6_features.py`
- Review errors: Check `get_errors` output in VS Code
- Consult docs: `app/ml/docs/DEVELOPMENT_HISTORY.md`
