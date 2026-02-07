"""
API Feature Engineering Module
================================
Modular feature engineering functions for API inference.
Generates all 69 features required by the v6 optimized model.

This module can be imported and reused in any API context where 
the model needs to make predictions from user-provided data.
"""

import numpy as np
import pandas as pd
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def add_cyclical_time_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add cyclical encoding for time features to capture periodic nature.
    
    Required columns: 'hour', 'day_of_week', 'month'
    Adds: hour_sin/cos, day_of_week_sin/cos, month_sin/cos (6 features)
    """
    df = df.copy()
    
    # Hour cyclical encoding (0-23)
    df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
    df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
    
    # Day of week cyclical encoding (0-6)
    df['day_of_week_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
    df['day_of_week_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)
    
    # Month cyclical encoding (1-12)
    df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
    df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)
    
    logger.debug("Added 6 cyclical time features")
    return df


def add_time_context_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add time context indicators for rush hours, weekend, etc.
    
    Required columns: 'hour', 'day_of_week', 'datetime'
    Adds: 21 time context indicator features
    """
    df = df.copy()
    
    # Rush hour periods
    df['is_breakfast_rush'] = ((df['hour'] >= 7) & (df['hour'] <= 9)).astype(int)
    df['is_lunch_rush'] = ((df['hour'] >= 11) & (df['hour'] <= 13)).astype(int)
    df['is_peak_lunch'] = ((df['hour'] >= 12) & (df['hour'] <= 14)).astype(int)
    df['is_dinner_rush'] = ((df['hour'] >= 18) & (df['hour'] <= 20)).astype(int)
    df['is_peak_dinner'] = ((df['hour'] >= 17) & (df['hour'] <= 19)).astype(int)
    df['is_late_night'] = ((df['hour'] >= 22) | (df['hour'] <= 2)).astype(int)
    df['is_midnight_zone'] = ((df['hour'] >= 23) | (df['hour'] <= 1)).astype(int)
    
    # Fine-grained hour categories
    df['is_early_morning'] = ((df['hour'] >= 6) & (df['hour'] <= 8)).astype(int)
    df['is_afternoon'] = ((df['hour'] >= 14) & (df['hour'] <= 17)).astype(int)
    df['is_evening'] = ((df['hour'] >= 17) & (df['hour'] <= 21)).astype(int)
    
    # Weekend indicator
    df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
    df['is_friday'] = (df['day_of_week'] == 4).astype(int)
    df['is_saturday'] = (df['day_of_week'] == 5).astype(int)
    df['is_sunday'] = (df['day_of_week'] == 6).astype(int)
    
    # Hour-Day interaction features
    df['friday_evening'] = ((df['day_of_week'] == 4) & (df['hour'] >= 17)).astype(int)
    df['saturday_evening'] = ((df['day_of_week'] == 5) & (df['hour'] >= 17)).astype(int)
    df['weekend_lunch'] = ((df['day_of_week'] >= 5) & (df['hour'] >= 11) & (df['hour'] <= 14)).astype(int)
    df['weekend_dinner'] = ((df['day_of_week'] >= 5) & (df['hour'] >= 17) & (df['hour'] <= 20)).astype(int)
    df['weekday_lunch'] = ((df['day_of_week'] < 5) & (df['hour'] >= 11) & (df['hour'] <= 14)).astype(int)
    df['weekday_dinner'] = ((df['day_of_week'] < 5) & (df['hour'] >= 17) & (df['hour'] <= 20)).astype(int)
    
    # Month start/end indicators
    df['is_month_start'] = (df['datetime'].dt.day <= 5).astype(int)
    df['is_month_end'] = (df['datetime'].dt.day >= 25).astype(int)
    
    logger.debug("Added 21 time context indicators")
    return df


def add_additional_lag_features(df: pd.DataFrame, target_col: str = 'item_count') -> pd.DataFrame:
    """
    Add additional rolling window and trend features beyond the basic lags.
    
    Required columns: 'place_id', 'datetime', target_col
    Adds: rolling_3d/14d/30d_avg_items, rolling_7d_std_items, demand_trend_7d, 
          lag_same_hour_last_week, lag_same_hour_2_weeks (7 features)
    """
    df = df.copy()
    df = df.sort_values(['place_id', 'datetime'])
    
    # Additional rolling averages
    for window_days in [3, 14, 30]:
        window_hours = window_days * 24
        df[f'rolling_{window_days}d_avg_items'] = df.groupby('place_id')[target_col].transform(
            lambda x: x.rolling(window=window_hours, min_periods=1).mean().shift(1)
        )
    
    # Volatility feature (rolling standard deviation)
    df['rolling_7d_std_items'] = df.groupby('place_id')[target_col].transform(
        lambda x: x.rolling(window=168, min_periods=1).std().shift(1)
    )
    
    # Trend feature (7-day slope)
    def calculate_trend(series):
        if len(series) < 2:
            return 0
        try:
            return np.polyfit(range(len(series)), series, 1)[0]
        except:
            return 0
    
    df['demand_trend_7d'] = df.groupby('place_id')[target_col].transform(
        lambda x: x.rolling(window=168, min_periods=2).apply(calculate_trend, raw=True).shift(1)
    )
    
    # Same-hour historical lags
    df['lag_same_hour_last_week'] = df.groupby('place_id')[target_col].shift(168)  # 7 * 24
    df['lag_same_hour_2_weeks'] = df.groupby('place_id')[target_col].shift(336)  # 14 * 24
    
    # Fill NaN in lag features
    lag_cols = [
        'rolling_3d_avg_items', 'rolling_14d_avg_items', 'rolling_30d_avg_items',
        'rolling_7d_std_items', 'demand_trend_7d',
        'lag_same_hour_last_week', 'lag_same_hour_2_weeks'
    ]
    df[lag_cols] = df[lag_cols].fillna(0)
    
    logger.debug("Added 7 additional lag & rolling features")
    return df


def add_venue_specific_features(df: pd.DataFrame, historical_df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """
    Add venue-specific historical performance features.
    
    Required columns: 'place_id', 'hour', 'day_of_week', 'item_count'
    Adds: venue_hour_avg, venue_dow_avg, venue_volatility, venue_total_items, 
          venue_growth_recent_vs_historical, venue_peak_hour, is_venue_peak_hour (7 features)
    
    Args:
        df: DataFrame to add features to (can be prediction window)
        historical_df: DataFrame with historical data to compute venue stats from.
                       If None, will use df itself (for training)
    """
    df = df.copy()
    
    # Use historical data if provided, otherwise use df itself
    source_df = historical_df if historical_df is not None else df
    
    # Compute venue statistics from source data
    venue_hour_stats = source_df.groupby(['place_id', 'hour'])['item_count'].mean().to_dict()
    venue_dow_stats = source_df.groupby(['place_id', 'day_of_week'])['item_count'].mean().to_dict()
    venue_volatility_stats = source_df.groupby('place_id')['item_count'].std().to_dict()
    venue_total_stats = source_df.groupby('place_id')['item_count'].sum().to_dict()
    
    # Map statistics to prediction dataframe
    df['venue_hour_avg'] = df.apply(lambda row: venue_hour_stats.get((row['place_id'], row['hour']), 0), axis=1)
    df['venue_dow_avg'] = df.apply(lambda row: venue_dow_stats.get((row['place_id'], row['day_of_week']), 0), axis=1)
    df['venue_volatility'] = df['place_id'].map(venue_volatility_stats).fillna(0)
    df['venue_total_items'] = df['place_id'].map(venue_total_stats).fillna(0)
    
    # Venue growth (ratio of rolling 7d to 30d)
    if 'rolling_7d_avg_items' in df.columns and 'rolling_30d_avg_items' in df.columns:
        df['venue_growth_recent_vs_historical'] = (
            df['rolling_7d_avg_items'] / df['rolling_30d_avg_items'].replace(0, 1)
        ).fillna(1)
    else:
        df['venue_growth_recent_vs_historical'] = 1.0
    
    # Venue peak hour (hour with highest average demand)
    venue_peak_hours = source_df.groupby('place_id').apply(
        lambda x: x.groupby('hour')['item_count'].mean().idxmax() if len(x) > 0 else 12
    ).to_dict()
    df['venue_peak_hour'] = df['place_id'].map(venue_peak_hours).fillna(12)
    df['is_venue_peak_hour'] = (df['hour'] == df['venue_peak_hour']).astype(int)
    
    logger.debug("Added 7 venue-specific features")
    return df


def add_weekend_specific_features(df: pd.DataFrame, historical_df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """
    Add weekend-specific features to address weekend vs weekday performance gap.
    
    Required columns: 'place_id', 'day_of_week', 'hour', 'item_count', 'datetime'
    Adds: venue_weekend_avg, venue_weekday_avg, venue_weekend_lift, 
          last_weekend_same_hour, venue_weekend_volatility, weekend_day_position (6 features)
    
    Args:
        df: DataFrame to add features to (can be prediction window)
        historical_df: DataFrame with historical data. If None, will use df itself
    """
    df = df.copy()
    
    # Use historical data if provided
    source_df = historical_df if historical_df is not None else df
    
    # Compute weekend/weekday averages per venue
    weekend_mask = source_df['day_of_week'] >= 5
    weekday_mask = source_df['day_of_week'] < 5
    
    venue_weekend_avg = source_df[weekend_mask].groupby('place_id')['item_count'].mean().to_dict()
    venue_weekday_avg = source_df[weekday_mask].groupby('place_id')['item_count'].mean().to_dict()
    venue_weekend_std = source_df[weekend_mask].groupby('place_id')['item_count'].std().to_dict()
    
    # Map to prediction dataframe
    df['venue_weekend_avg'] = df['place_id'].map(venue_weekend_avg).fillna(df.groupby('place_id')['item_count'].transform('mean'))
    df['venue_weekday_avg'] = df['place_id'].map(venue_weekday_avg).fillna(df.groupby('place_id')['item_count'].transform('mean'))
    df['venue_weekend_volatility'] = df['place_id'].map(venue_weekend_std).fillna(0)
    
    # Weekend lift ratio
    df['venue_weekend_lift'] = (df['venue_weekend_avg'] / df['venue_weekday_avg'].replace(0, 1)).fillna(1)
    
    # Last weekend's demand for same hour (shifted by 7 days)
    if 'item_count' in df.columns:
        df = df.sort_values(['place_id', 'datetime'])
        df['last_weekend_same_hour'] = df.groupby(['place_id', 'hour'])['item_count'].shift(168)
        df['last_weekend_same_hour'] = df['last_weekend_same_hour'].fillna(0)
    else:
        df['last_weekend_same_hour'] = 0
    
    # Weekend day position (Fri=0, Sat=1, Sun=2)
    df['weekend_day_position'] = df['day_of_week'].apply(lambda x: x - 4 if x >= 4 else -1)
    df['weekend_day_position'] = df['weekend_day_position'].clip(lower=-1)
    
    logger.debug("Added 6 weekend-specific features")
    return df


def add_weather_interaction_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add weather interaction features.
    
    Required columns: Various weather and time features
    Adds: feels_like_temp, bad_weather_score, temp_change_1h, temp_change_3h,
          weather_getting_worse, weekend_good_weather, rush_bad_weather, cold_evening (8 features)
    """
    df = df.copy()
    
    # Feels-like temperature (comfort index)
    if all(col in df.columns for col in ['temperature_2m', 'wind_speed_10m', 'relative_humidity_2m']):
        df['feels_like_temp'] = (
            df['temperature_2m'] 
            - (df['wind_speed_10m'] * 0.5)
            + (df['relative_humidity_2m'] * 0.1)
        )
    else:
        df['feels_like_temp'] = 15.0
    
    # Bad weather composite score
    if all(col in df.columns for col in ['precipitation', 'wind_speed_10m', 'cloud_cover']):
        df['bad_weather_score'] = (
            (df['precipitation'] > 0).astype(int) * 0.4 +
            (df['wind_speed_10m'] > 20).astype(int) * 0.3 +
            (df['cloud_cover'] > 70).astype(int) * 0.3
        )
    else:
        df['bad_weather_score'] = 0.0
    
    # Temperature change features
    if 'temperature_2m' in df.columns:
        df = df.sort_values(['place_id', 'datetime'])
        df['temp_change_1h'] = df.groupby('place_id')['temperature_2m'].diff(1).fillna(0)
        df['temp_change_3h'] = df.groupby('place_id')['temperature_2m'].diff(3).fillna(0)
    else:
        df['temp_change_1h'] = 0.0
        df['temp_change_3h'] = 0.0
    
    # Weather deterioration
    if 'weather_severity' in df.columns:
        df['weather_getting_worse'] = (
            df.groupby('place_id')['weather_severity'].diff(1) > 0
        ).astype(int).fillna(0)
    else:
        df['weather_getting_worse'] = 0
    
    # Time-Weather Interactions
    if 'is_weekend' in df.columns and 'good_weather' in df.columns:
        df['weekend_good_weather'] = df['is_weekend'] * df['good_weather']
    else:
        df['weekend_good_weather'] = 0
    
    if all(col in df.columns for col in ['is_lunch_rush', 'is_dinner_rush', 'bad_weather_score']):
        df['rush_bad_weather'] = (
            (df['is_lunch_rush'] | df['is_dinner_rush']) * df['bad_weather_score']
        )
    else:
        df['rush_bad_weather'] = 0
    
    if 'is_cold' in df.columns and 'hour' in df.columns:
        df['cold_evening'] = df['is_cold'] * (df['hour'] >= 18).astype(int)
    else:
        df['cold_evening'] = 0
    
    logger.debug("Added 8 weather interaction features")
    return df


def apply_all_api_features(
    df: pd.DataFrame,
    historical_df: Optional[pd.DataFrame] = None
) -> pd.DataFrame:
    """
    Apply all feature engineering transformations for API inference.
    
    This is the main function to call for API predictions. It applies all
    feature engineering steps in the correct order.
    
    Args:
        df: DataFrame to add features to (typically prediction window)
        historical_df: Optional historical data for computing venue statistics
        
    Returns:
        DataFrame with all 69 features required by v6 model
        
    Required input columns:
        - datetime, hour, day_of_week, month, place_id, item_count (or proxies)
        - Weather features (from weather API)
        - Basic lag features (computed earlier in pipeline)
    """
    logger.info(f"Starting API feature engineering pipeline on {len(df)} rows")
    
    # Step 1: Cyclical time features (6 features)
    df = add_cyclical_time_features(df)
    
    # Step 2: Time context indicators (21 features)
    df = add_time_context_indicators(df)
    
    # Step 3: Additional lag features (7 features)
    df = add_additional_lag_features(df)
    
    # Step 4: Venue-specific features (7 features)
    df = add_venue_specific_features(df, historical_df)
    
    # Step 5: Weekend-specific features (6 features)
    df = add_weekend_specific_features(df, historical_df)
    
    # Step 6: Weather interaction features (8 features)
    df = add_weather_interaction_features(df)
    
    logger.info(f"API feature engineering complete. Shape: {df.shape}")
    return df
