"""
V6 Model Feature Verification Script
=====================================
Tests that the API can generate all 69 features required by the v6 model.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Import the feature engineering module
from src.api_feature_engineering import apply_all_api_features

def create_test_dataframe():
    """Create a minimal test DataFrame with required base features"""
    
    # Create 7 days of hourly data
    start_date = datetime(2026, 2, 1)
    hours = []
    
    for day in range(7):
        for hour in range(24):
            dt = start_date + timedelta(days=day, hours=hour)
            hours.append({
                'datetime': dt,
                'place_id': 1001.0,
                'hour': hour,
                'day_of_week': dt.weekday(),
                'month': dt.month,
                'week_of_year': dt.isocalendar()[1],
                'item_count': np.random.randint(10, 50),  # Mock historical demand
                
                # Basic lag features (normally computed from historical data)
                'prev_hour_items': 20,
                'prev_day_items': 25,
                'prev_week_items': 22,
                'prev_month_items': 24,
                'rolling_7d_avg_items': 23,
                
                # Weather features (from weather API)
                'temperature_2m': 15.0,
                'relative_humidity_2m': 70.0,
                'precipitation': 0.0,
                'rain': 0.0,
                'snowfall': 0.0,
                'weather_code': 1,
                'cloud_cover': 50.0,
                'wind_speed_10m': 15.0,
                'is_rainy': 0,
                'is_snowy': 0,
                'is_cold': 0,
                'is_hot': 0,
                'is_cloudy': 0,
                'is_windy': 0,
                'good_weather': 1,
                'weather_severity': 0
            })
    
    return pd.DataFrame(hours)


def verify_features():
    """Verify that all 69 features are generated"""
    
    print("="*80)
    print("V6 MODEL FEATURE VERIFICATION")
    print("="*80)
    
    # Create test data
    print("\n1. Creating test DataFrame...")
    df = create_test_dataframe()
    print(f"   Base features: {len(df.columns)} columns, {len(df)} rows")
    print(f"   Columns: {list(df.columns)}")
    
    # Apply feature engineering
    print("\n2. Applying feature engineering...")
    try:
        df_features = apply_all_api_features(df, historical_df=df)
        print(f"   ✓ Feature engineering successful")
        print(f"   Total features: {len(df_features.columns)} columns")
    except Exception as e:
        print(f"   ✗ Feature engineering failed: {e}")
        return False
    
    # Check for expected features
    print("\n3. Verifying feature counts by category...")
    
    feature_categories = {
        'Base features': ['place_id', 'hour', 'day_of_week', 'month', 'week_of_year'],
        'Basic lag features': ['prev_hour_items', 'prev_day_items', 'prev_week_items'],
        'Weather features': ['temperature_2m', 'precipitation', 'wind_speed_10m'],
        'Cyclical time': ['hour_sin', 'hour_cos', 'day_of_week_sin'],
        'Time context': ['is_breakfast_rush', 'is_lunch_rush', 'is_weekend'],
        'Additional lags': ['rolling_3d_avg_items', 'rolling_14d_avg_items', 'demand_trend_7d'],
        'Venue-specific': ['venue_hour_avg', 'venue_dow_avg', 'venue_volatility'],
        'Weekend-specific': ['venue_weekend_avg', 'venue_weekday_avg', 'venue_weekend_lift'],
        'Weather interactions': ['feels_like_temp', 'bad_weather_score', 'temp_change_1h']
    }
    
    all_present = True
    for category, sample_features in feature_categories.items():
        present = [f for f in sample_features if f in df_features.columns]
        if len(present) == len(sample_features):
            print(f"   ✓ {category}: {len(present)}/{len(sample_features)} present")
        else:
            print(f"   ✗ {category}: {len(present)}/{len(sample_features)} present")
            print(f"      Missing: {set(sample_features) - set(present)}")
            all_present = False
    
    # Check total feature count
    print(f"\n4. Total Feature Count:")
    expected_total = 69
    actual_total = len(df_features.columns)
    
    if actual_total >= expected_total:
        print(f"   ✓ Generated {actual_total} features (expected {expected_total})")
    else:
        print(f"   ✗ Generated {actual_total} features (expected {expected_total})")
        print(f"   Missing: {expected_total - actual_total} features")
        all_present = False
    
    # Check for NaN values
    print(f"\n5. Data Quality Check:")
    nan_count = df_features.isnull().sum().sum()
    if nan_count == 0:
        print(f"   ✓ No NaN values detected")
    else:
        print(f"   ⚠ Warning: {nan_count} NaN values detected")
        nan_cols = df_features.columns[df_features.isnull().any()].tolist()
        print(f"   Columns with NaN: {nan_cols[:10]}...")  # Show first 10
    
    # Summary
    print("\n" + "="*80)
    if all_present and actual_total >= expected_total:
        print("✓ VERIFICATION PASSED - All features generated successfully!")
    else:
        print("✗ VERIFICATION FAILED - Some features missing")
    print("="*80)
    
    return all_present and actual_total >= expected_total


if __name__ == "__main__":
    success = verify_features()
    sys.exit(0 if success else 1)
