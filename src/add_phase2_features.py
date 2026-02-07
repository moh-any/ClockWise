"""
Add Phase 2 features to existing combined dataset without re-fetching weather data.
Phase 2 features: venue-specific historical + weather interactions
"""
import pandas as pd
import numpy as np
from pathlib import Path

def add_venue_specific_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add venue-specific historical performance features."""
    df = df.copy()
    
    # Average demand by hour for each venue
    venue_hour_avg = df.groupby(['place_id', 'hour'])['item_count'].transform('mean')
    df['venue_hour_avg'] = venue_hour_avg
    
    # Average demand by day of week for each venue
    venue_dow_avg = df.groupby(['place_id', 'day_of_week'])['item_count'].transform('mean')
    df['venue_dow_avg'] = venue_dow_avg
    
    # Venue volatility (consistency indicator)
    venue_std = df.groupby('place_id')['item_count'].transform('std')
    df['venue_volatility'] = venue_std.fillna(0)
    
    # Venue size/scale indicator (total historical items)
    venue_total = df.groupby('place_id')['item_count'].transform('sum')
    df['venue_total_items'] = venue_total
    
    # Recent growth trend (rolling 7d vs 30d)
    df['venue_growth_recent_vs_historical'] = (
        df['rolling_7d_avg_items'] / df['rolling_30d_avg_items']
    ).fillna(1)
    
    # Venue peak hour (hour with highest average demand)
    venue_peak_hour = df.groupby('place_id').apply(
        lambda x: x.groupby('hour')['item_count'].mean().idxmax()
    )
    df['venue_peak_hour'] = df['place_id'].map(venue_peak_hour)
    df['is_venue_peak_hour'] = (df['hour'] == df['venue_peak_hour']).astype(int)
    
    print(f"✓ Added 7 venue-specific features")
    return df


def add_weather_interaction_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add weather interaction features."""
    df = df.copy()
    
    # Feels-like temperature (comfort index)
    if all(col in df.columns for col in ['temperature_2m', 'wind_speed_10m', 'relative_humidity_2m']):
        df['feels_like_temp'] = (
            df['temperature_2m'] 
            - (df['wind_speed_10m'] * 0.5)
            + (df['relative_humidity_2m'] * 0.1)
        )
        print("  - feels_like_temp")
    
    # Bad weather composite score
    if all(col in df.columns for col in ['precipitation', 'wind_speed_10m', 'cloud_cover']):
        df['bad_weather_score'] = (
            (df['precipitation'] > 0).astype(int) * 0.4 +
            (df['wind_speed_10m'] > 20).astype(int) * 0.3 +
            (df['cloud_cover'] > 70).astype(int) * 0.3
        )
        print("  - bad_weather_score")
    
    # Temperature change features
    if 'temperature_2m' in df.columns:
        df = df.sort_values(['place_id', 'datetime'])
        df['temp_change_1h'] = df.groupby('place_id')['temperature_2m'].diff(1).fillna(0)
        df['temp_change_3h'] = df.groupby('place_id')['temperature_2m'].diff(3).fillna(0)
        print("  - temp_change_1h, temp_change_3h")
    
    # Weather deterioration
    if 'weather_severity' in df.columns:
        df['weather_getting_worse'] = (
            (df.groupby('place_id')['weather_severity'].diff(1) > 0).astype(int)
        ).fillna(0)
        print("  - weather_getting_worse")
    
    # Time-Weather Interactions
    if 'is_weekend' in df.columns and 'good_weather' in df.columns:
        df['weekend_good_weather'] = df['is_weekend'] * df['good_weather']
        print("  - weekend_good_weather")
    
    if all(col in df.columns for col in ['is_lunch_rush', 'is_dinner_rush', 'bad_weather_score']):
        df['rush_bad_weather'] = (
            (df['is_lunch_rush'] | df['is_dinner_rush']) * df['bad_weather_score']
        )
        print("  - rush_bad_weather")
    
    if 'is_cold' in df.columns and 'hour' in df.columns:
        df['cold_evening'] = (df['is_cold'] * (df['hour'] >= 18).astype(int))
        print("  - cold_evening")
    
    print(f"✓ Added weather interaction features")
    return df


def main():
    print("\n" + "="*60)
    print("PHASE 2 FEATURE ENGINEERING")
    print("="*60)
    
    # Load existing combined features (with Phase 1)
    input_path = Path("data/processed/combined_features.csv")
    print(f"\nLoading: {input_path}")
    df = pd.read_csv(input_path)
    print(f"  Shape: {df.shape}")
    print(f"  Columns: {df.shape[1]}")
    
    # Convert datetime
    df['datetime'] = pd.to_datetime(df['datetime'])
    
    # Add Phase 2 features
    print("\n1. Adding venue-specific historical features...")
    df = add_venue_specific_features(df)
    
    print("\n2. Adding weather interaction features...")
    df = add_weather_interaction_features(df)
    
    # Save
    output_path = Path("data/processed/combined_features.csv")
    print(f"\nSaving to: {output_path}")
    df.to_csv(output_path, index=False)
    
    print("\n" + "="*60)
    print(f"PHASE 2 COMPLETE")
    print(f"  Final shape: {df.shape}")
    print(f"  New total columns: {df.shape[1]}")
    print("="*60)
    
    # Show sample of new features
    new_feature_cols = [
        'venue_hour_avg', 'venue_dow_avg', 'venue_volatility', 
        'venue_total_items', 'venue_growth_recent_vs_historical',
        'venue_peak_hour', 'is_venue_peak_hour',
        'feels_like_temp', 'bad_weather_score', 'temp_change_1h', 
        'temp_change_3h', 'weather_getting_worse',
        'weekend_good_weather', 'rush_bad_weather', 'cold_evening'
    ]
    available_new_cols = [c for c in new_feature_cols if c in df.columns]
    
    print(f"\nNew Phase 2 features ({len(available_new_cols)}):")
    print(df[available_new_cols].head())
    print("\nSample statistics:")
    print(df[available_new_cols].describe())


if __name__ == "__main__":
    main()
