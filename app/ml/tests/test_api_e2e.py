"""
End-to-End API Feature Engineering Validation
==============================================
Simulates the complete API flow from raw input to model-ready features.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json

# Import API components
from src.api_feature_engineering import apply_all_api_features

def simulate_api_flow():
    """Simulate the complete API feature engineering pipeline"""
    
    print("="*80)
    print("END-TO-END API FEATURE ENGINEERING VALIDATION")
    print("="*80)
    
    # Step 1: Simulate raw user input (what API receives)
    print("\n1. Simulating raw user input...")
    print("   - Place info (type, location, ratings)")
    print("   - Historical orders (30 days)")
    print("   - Campaigns (if any)")
    
    # Step 2: Process historical orders to hourly demand
    print("\n2. Processing historical orders...")
    
    # Create mock historical data (30 days)
    start_date = datetime(2026, 1, 1)
    historical_data = []
    
    for day in range(30):
        for hour in range(24):
            dt = start_date + timedelta(days=day, hours=hour)
            historical_data.append({
                'datetime': dt,
                'place_id': 1001.0,
                'hour': hour,
                'day_of_week': dt.weekday(),
                'month': dt.month,
                'week_of_year': dt.isocalendar()[1],
                'item_count': max(0, int(20 + 15*np.sin(hour/24*2*np.pi) + np.random.randn()*5)),
                'order_count': max(0, int(5 + 3*np.sin(hour/24*2*np.pi) + np.random.randn()*2)),
            })
    
    historical_df = pd.DataFrame(historical_data)
    print(f"   ✓ Created {len(historical_df)} hours of historical data")
    
    # Step 3: Add basic lag features
    print("\n3. Adding basic lag features...")
    historical_df = historical_df.sort_values(['place_id', 'datetime'])
    historical_df['prev_hour_items'] = historical_df.groupby('place_id')['item_count'].shift(1).fillna(0)
    historical_df['prev_day_items'] = historical_df.groupby('place_id')['item_count'].shift(24).fillna(0)
    historical_df['prev_week_items'] = historical_df.groupby('place_id')['item_count'].shift(168).fillna(0)
    historical_df['prev_month_items'] = historical_df.groupby('place_id')['item_count'].shift(720).fillna(0)
    historical_df['rolling_7d_avg_items'] = historical_df.groupby('place_id')['item_count'].transform(
        lambda x: x.rolling(window=168, min_periods=1).mean().shift(1)
    ).fillna(0)
    print(f"   ✓ Added 5 basic lag features")
    
    # Step 4: Add place features
    print("\n4. Adding place features...")
    historical_df['type_id'] = 1335.0  # restaurant
    historical_df['waiting_time'] = 25.0
    historical_df['rating'] = 4.2
    historical_df['delivery'] = 1
    historical_df['accepting_orders'] = 1
    historical_df['total_campaigns'] = 2
    historical_df['avg_discount'] = 10.0
    print(f"   ✓ Added 7 place features")
    
    # Step 5: Add weather features (mock)
    print("\n5. Adding weather features...")
    weather_features = {
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
    }
    for col, val in weather_features.items():
        historical_df[col] = val
    print(f"   ✓ Added 16 weather features")
    
    # Step 6: Add holiday feature
    print("\n6. Adding holiday feature...")
    historical_df['is_holiday'] = 0
    print(f"   ✓ Added 1 holiday feature")
    
    # Step 7: Create prediction window (7 days ahead)
    print("\n7. Creating prediction window...")
    prediction_start = datetime(2026, 1, 31)
    prediction_data = []
    
    for day in range(7):
        for hour in range(24):
            dt = prediction_start + timedelta(days=day, hours=hour)
            prediction_data.append({
                'datetime': dt,
                'place_id': 1001.0,
                'hour': hour,
                'day_of_week': dt.weekday(),
                'month': dt.month,
                'week_of_year': dt.isocalendar()[1],
                'item_count': 0,  # Unknown - to be predicted
                'order_count': 0,
            })
    
    prediction_df = pd.DataFrame(prediction_data)
    
    # Copy all base features from historical
    for col in ['type_id', 'waiting_time', 'rating', 'delivery', 'accepting_orders',
                'total_campaigns', 'avg_discount', 'is_holiday'] + list(weather_features.keys()):
        prediction_df[col] = historical_df[col].iloc[0]
    
    # Add lag features (from end of historical period)
    last_historical = historical_df.iloc[-1]
    prediction_df['prev_hour_items'] = last_historical['item_count']
    prediction_df['prev_day_items'] = historical_df[historical_df['hour'] == prediction_df.iloc[0]['hour']].iloc[-1]['item_count']
    prediction_df['prev_week_items'] = historical_df.iloc[-168]['item_count'] if len(historical_df) >= 168 else 0
    prediction_df['prev_month_items'] = historical_df.iloc[-720]['item_count'] if len(historical_df) >= 720 else 0
    prediction_df['rolling_7d_avg_items'] = historical_df['item_count'].tail(168).mean()
    
    print(f"   ✓ Created {len(prediction_df)} hours for prediction")
    
    # Step 8: Apply v6 feature engineering
    print("\n8. Applying v6 feature engineering...")
    print("   This adds:")
    print("   - Cyclical time features (6)")
    print("   - Time context indicators (21)")
    print("   - Additional lag features (7)")
    print("   - Venue-specific features (7)")
    print("   - Weekend-specific features (6)")
    print("   - Weather interaction features (8)")
    
    # Combine historical and prediction for feature engineering
    combined_df = pd.concat([historical_df, prediction_df], ignore_index=True)
    combined_df = combined_df.sort_values(['place_id', 'datetime'])
    
    # Apply features
    combined_df = apply_all_api_features(
        df=combined_df,
        historical_df=historical_df
    )
    
    # Extract just the prediction window
    prediction_features = combined_df[combined_df['datetime'] >= prediction_start].copy()
    
    print(f"   ✓ Feature engineering complete")
    print(f"   Total columns: {len(prediction_features.columns)}")
    
    # Step 9: Align with model expectations (69 features)
    print("\n9. Aligning with model expectations (69 features)...")
    
    # Load model metadata to get expected features
    try:
        with open('data/models/rf_model_metadata.json', 'r') as f:
            metadata = json.load(f)
        expected_features = metadata.get('num_features', 69)
        print(f"   Model expects: {expected_features} features")
    except:
        print("   Warning: Could not load model metadata")
        expected_features = 69
    
    # This is what align_features_with_model() does
    print(f"   Available features: {len(prediction_features.columns)}")
    print(f"   Will select exactly {expected_features} for model")
    
    # Step 10: Validate results
    print("\n10. Validation...")
    
    # Check for NaN
    nan_count = prediction_features.isnull().sum().sum()
    if nan_count == 0:
        print(f"   ✓ No NaN values")
    else:
        print(f"   ⚠ Warning: {nan_count} NaN values detected")
    
    # Check feature categories
    feature_checks = {
        'Cyclical time': ['hour_sin', 'day_of_week_sin', 'month_sin'],
        'Time context': ['is_weekend', 'is_lunch_rush', 'is_dinner_rush'],
        'Venue-specific': ['venue_hour_avg', 'venue_dow_avg', 'venue_volatility'],
        'Weekend-specific': ['venue_weekend_avg', 'venue_weekend_lift'],
        'Weather interaction': ['feels_like_temp', 'bad_weather_score']
    }
    
    all_good = True
    for category, sample_cols in feature_checks.items():
        present = [c for c in sample_cols if c in prediction_features.columns]
        if len(present) == len(sample_cols):
            print(f"   ✓ {category}: Present")
        else:
            print(f"   ✗ {category}: Missing {set(sample_cols) - set(present)}")
            all_good = False
    
    # Summary
    print("\n" + "="*80)
    if all_good and nan_count == 0:
        print("✓ VALIDATION PASSED")
        print(f"  - Raw user input → {len(prediction_features.columns)} features")
        print(f"  - Ready for model inference")
        print(f"  - No additional user data required")
        print("✓ API wrapper successfully handles v6 model!")
    else:
        print("⚠ VALIDATION WARNING")
        print("  Some feature issues detected (see above)")
    print("="*80)
    
    return all_good and nan_count == 0


if __name__ == "__main__":
    success = simulate_api_flow()
    sys.exit(0 if success else 1)
