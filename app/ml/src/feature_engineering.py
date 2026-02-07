import numpy as np
import pandas as pd
import os
from pathlib import Path
from src.weather_api import get_weather_for_demand_data
from src.holiday_api import add_holiday_feature

# This module contains functions for feature engineering on time series data.

def load_all_csvs_from_folder(folder_path: str, subfolder: str = 'raw') -> dict:
    """
    Loads all CSV files from a specified folder and subfolder into a dictionary of DataFrames.
    
    Parameters:
    folder_path: Paths to the the main folder.
    subfolder: Subfolder name where CSV files are located. Default is 'raw'.
    
    Returns:
    dict: Dictionary with filenames (without extension) as keys and DataFrames as values.
    """
    datasets = {}
    data_dir = Path(folder_path) / subfolder
    
    for csv_file in data_dir.glob("*.csv"):
        name = csv_file.stem
        datasets[name] = pd.read_csv(csv_file, low_memory=False, on_bad_lines='skip')
        print(f"Loaded {name} with shape {datasets[name].shape}")

    return datasets

def get_raw_features(datasets: dict, columns_file_path: str) -> dict:
    """
    Extracts raw features from datasets based on specified columns in a CSV file.
    
    Parameters:
    datasets: Dictionary of DataFrames.
    columns_file_path: Path to the CSV file containing dataset names and column names to extract.
    
    Returns:
    dict: Dictionary with dataset names as keys and DataFrames of raw features as values.
    """
    raw_features = {}
    columns_df = pd.read_csv(columns_file_path, skipinitialspace=True)
    # columns_df.columns = columns_df.columns.str.strip()  # Strip whitespace from column names
    
    datasets['fct_orders'] = datasets['fct_orders'][datasets['fct_orders']['status'] != 'closed']
    
    for name, df in datasets.items():
        dataset_columns = columns_df[columns_df['dataset_name'] == name]['column_name'].tolist()
        selected_columns = [col for col in dataset_columns if col in df.columns]
        raw_features[name] = df[selected_columns].copy()
        print(f"Extracted raw features for {name} with shape {raw_features[name].shape}")

    return raw_features

def join_orders_with_items(orders_df: pd.DataFrame, order_items_df: pd.DataFrame) -> pd.DataFrame:
    """
    Join order items with orders to get item counts per order.
    
    Parameters:
    orders_df: DataFrame with order data (must have 'id', 'created', 'place_id', 'total_amount')
    order_items_df: DataFrame with order items (must have 'order_id', 'item_id')
    
    Returns:
    DataFrame with orders enriched with item_count and time features
    """
    orders = orders_df.copy()
    
    # Add timestamp info
    orders['created_dt'] = pd.to_datetime(orders['created'], unit='s')
    orders['date'] = orders['created_dt'].dt.date
    orders['hour'] = orders['created_dt'].dt.hour
    
    # Aggregate items per order
    items_per_order = order_items_df.groupby('order_id').agg(
        item_count=('item_id', 'count')
    ).reset_index()
    
    # Join items count back to orders
    orders = orders.merge(items_per_order, left_on='id', right_on='order_id', how='left')
    orders['item_count'] = orders['item_count'].fillna(0)
    
    print(f"-> Joined {len(order_items_df):,} items to {len(orders):,} orders")
    return orders


def aggregate_to_hourly(orders_df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate orders to hourly demand per venue.
    
    Parameters:
    orders_df: DataFrame with orders (must have 'place_id', 'date', 'hour', 'item_count', 'total_amount')
    
    Returns:
    DataFrame with hourly aggregated demand per venue
    """
    hourly_demand = orders_df.groupby(['place_id', 'date', 'hour']).agg(
        item_count=('item_count', 'sum'),
        order_count=('created', 'count'),
        total_revenue=('total_amount', 'sum'),
        avg_order_value=('total_amount', 'mean'),
        avg_items_per_order=('item_count', 'mean')
    ).reset_index()
    
    # Convert date to datetime for downstream processing
    hourly_demand['datetime'] = pd.to_datetime(hourly_demand['date'].astype(str)) + \
                                 pd.to_timedelta(hourly_demand['hour'], unit='h')
    
    print(f"-> Aggregated to {len(hourly_demand):,} hourly records")
    return hourly_demand


def add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add time-based features from datetime column.
    
    Parameters:
    df: DataFrame with 'datetime' column
    
    Returns:
    DataFrame with added time features
    """
    df = df.copy()
    df['day_of_week'] = df['datetime'].dt.dayofweek  # 0=Mon, 6=Sun
    df['month'] = df['datetime'].dt.month
    df['week_of_year'] = df['datetime'].dt.isocalendar().week
    
    print(f"-> Added time features (day_of_week, month, week_of_year)")
    return df


def add_cyclical_time_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add cyclical encoding for time features to capture periodic nature.
    
    Parameters:
    df: DataFrame with 'hour', 'day_of_week', 'month' columns
    
    Returns:
    DataFrame with cyclical time features
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
    
    print(f"-> Added cyclical time features (hour_sin/cos, day_of_week_sin/cos, month_sin/cos)")
    return df


def add_time_context_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add time context indicators for rush hours, weekend, etc.
    
    Parameters:
    df: DataFrame with 'hour', 'day_of_week', 'datetime' columns
    
    Returns:
    DataFrame with time context indicators
    """
    df = df.copy()
    
    # Rush hour periods
    df['is_breakfast_rush'] = ((df['hour'] >= 7) & (df['hour'] <= 9)).astype(int)
    df['is_lunch_rush'] = ((df['hour'] >= 11) & (df['hour'] <= 13)).astype(int)
    df['is_dinner_rush'] = ((df['hour'] >= 18) & (df['hour'] <= 20)).astype(int)
    df['is_late_night'] = ((df['hour'] >= 22) | (df['hour'] <= 2)).astype(int)
    
    # Weekend indicator
    df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
    
    # Month start/end indicators
    df['is_month_start'] = (df['datetime'].dt.day <= 5).astype(int)
    df['is_month_end'] = (df['datetime'].dt.day >= 25).astype(int)
    
    print(f"-> Added time context indicators (breakfast/lunch/dinner rush, late night, weekend, month start/end)")
    return df


def add_venue_specific_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add venue-specific historical performance features (Phase 2).
    
    Parameters:
    df: DataFrame with 'place_id', 'hour', 'day_of_week', 'item_count' columns
    
    Returns:
    DataFrame with venue-specific features
    """
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
    
    print(f"-> Added venue-specific features (hour/dow averages, volatility, growth, peak hour)")
    return df


def add_weather_interaction_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add weather interaction features (Phase 2).
    
    Parameters:
    df: DataFrame with weather and time features
    
    Returns:
    DataFrame with weather interaction features
    """
    df = df.copy()
    
    # Feels-like temperature (comfort index)
    if all(col in df.columns for col in ['temperature_2m', 'wind_speed_10m', 'relative_humidity_2m']):
        df['feels_like_temp'] = (
            df['temperature_2m'] 
            - (df['wind_speed_10m'] * 0.5)
            + (df['relative_humidity_2m'] * 0.1)
        )
    
    # Bad weather composite score
    if all(col in df.columns for col in ['precipitation', 'wind_speed_10m', 'cloud_cover']):
        df['bad_weather_score'] = (
            (df['precipitation'] > 0).astype(int) * 0.4 +
            (df['wind_speed_10m'] > 20).astype(int) * 0.3 +
            (df['cloud_cover'] > 70).astype(int) * 0.3
        )
    
    # Temperature change features (if possible)
    if 'temperature_2m' in df.columns:
        df = df.sort_values(['place_id', 'datetime'])
        df['temp_change_1h'] = df.groupby('place_id')['temperature_2m'].diff(1).fillna(0)
        df['temp_change_3h'] = df.groupby('place_id')['temperature_2m'].diff(3).fillna(0)
    
    # Weather deterioration
    if 'weather_severity' in df.columns:
        df['weather_getting_worse'] = (
            (df.groupby('place_id')['weather_severity'].diff(1) > 0).astype(int)
        ).fillna(0)
    
    # Time-Weather Interactions
    if 'is_weekend' in df.columns and 'good_weather' in df.columns:
        df['weekend_good_weather'] = df['is_weekend'] * df['good_weather']
    
    if all(col in df.columns for col in ['is_lunch_rush', 'is_dinner_rush', 'bad_weather_score']):
        df['rush_bad_weather'] = (
            (df['is_lunch_rush'] | df['is_dinner_rush']) * df['bad_weather_score']
        )
    
    if 'is_cold' in df.columns and 'hour' in df.columns:
        df['cold_evening'] = (df['is_cold'] * (df['hour'] >= 18).astype(int))
    
    print(f"-> Added weather interaction features (feels-like, bad weather score, time×weather)")
    return df


def join_place_features(df: pd.DataFrame, places_df: pd.DataFrame) -> pd.DataFrame:
    """
    Join venue characteristics from dim_places.
    
    Parameters:
    df: DataFrame with 'place_id' column
    places_df: DataFrame with place info (must have 'id')
    
    Returns:
    DataFrame with place features joined
    """
    places = places_df.copy()
    places = places.rename(columns={'id': 'place_id'})
    
    # Select relevant columns that exist
    place_cols = ['place_id', 'type_id', 'waiting_time', 'rating', 'delivery', 'accepting_orders', 'longitude', 'latitude']
    place_cols = [c for c in place_cols if c in places.columns]
    
    result = df.merge(places[place_cols], on='place_id', how='left')
    
    print(f"-> Joined {len(place_cols)} place features")
    return result


def add_campaign_features(df: pd.DataFrame, campaigns_df: pd.DataFrame) -> pd.DataFrame:
    """
    Add campaign-related features.
    
    Parameters:
    df: DataFrame with 'place_id' column
    campaigns_df: DataFrame with campaign data
    
    Returns:
    DataFrame with campaign features added
    """
    campaigns = campaigns_df.copy()
    
    # Aggregate campaign stats by place
    campaign_counts = campaigns.groupby('place_id').agg(
        total_campaigns=('place_id', 'count'),
        avg_discount=('discount', 'mean')
    ).reset_index()
    
    result = df.merge(campaign_counts, on='place_id', how='left')
    result['total_campaigns'] = result['total_campaigns'].fillna(0)
    result['avg_discount'] = result['avg_discount'].fillna(0)
    
    print(f"-> Added campaign features (total_campaigns, avg_discount)")
    return result


def add_lag_features(df: pd.DataFrame, target_col: str = 'item_count') -> pd.DataFrame:
    """
    Add lag and rolling average features for time series prediction.
    
    ===== FIX: Shift rolling features to avoid data leakage =====
    
    Parameters:
    df: DataFrame with 'place_id', 'datetime', and target column
    target_col: Column to create lag features from (default: 'item_count')
    
    Returns:
    DataFrame with lag features added
    """
    df = df.copy()
    df = df.sort_values(['place_id', 'datetime'])
    
    # Lag features within each venue
    df['prev_hour_items'] = df.groupby('place_id')[target_col].shift(1)
    df['prev_day_items'] = df.groupby('place_id')[target_col].shift(24)
    df['prev_week_items'] = df.groupby('place_id')[target_col].shift(168)  # 7*24
    df['prev_month_items'] = df.groupby('place_id')[target_col].shift(720)  # 30*24
    
    # Same-time historical lags (more predictive)
    df['lag_same_hour_last_week'] = df.groupby('place_id')[target_col].shift(168)  # 7 * 24
    df['lag_same_hour_2_weeks'] = df.groupby('place_id')[target_col].shift(336)  # 14 * 24
    
    # Rolling averages with multiple windows
    for window_days in [3, 7, 14, 30]:
        window_hours = window_days * 24
        df[f'rolling_{window_days}d_avg_items'] = df.groupby('place_id')[target_col].transform(
            lambda x: x.rolling(window=window_hours, min_periods=1).mean()
        )
    
    # Volatility feature (rolling standard deviation)
    df['rolling_7d_std_items'] = df.groupby('place_id')[target_col].transform(
        lambda x: x.rolling(window=168, min_periods=1).std()
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
        lambda x: x.rolling(window=168, min_periods=2).apply(calculate_trend, raw=True)
    )
    
    # Fill NaN in lag features with 0
    lag_cols = [
        'prev_hour_items', 'prev_day_items', 'prev_week_items', 'prev_month_items',
        'lag_same_hour_last_week', 'lag_same_hour_2_weeks', 'rolling_7d_std_items', 'demand_trend_7d'
    ]
    df[lag_cols] = df[lag_cols].fillna(0)
    
    print(f"-> Added enhanced lag & rolling features (3d/7d/14d/30d avg, volatility, trend, same-hour lags)")
    return df


def combine_features(raw_features: dict) -> pd.DataFrame:
    """
    Combines raw features into a single DataFrame for demand prediction.
    
    Orchestrates the feature engineering pipeline:
    1. Join orders with items
    2. Aggregate to hourly level
    3. Add time features
    4. Join place features
    5. Add campaign features
    6. Add lag features
    7. Add weather features
    
    Parameters:
    raw_features (dict): Dictionary of DataFrames with raw features.
    
    Returns:
    pd.DataFrame: Combined DataFrame ready for demand prediction model.
    """
    print("\n" + "=" * 60)
    print("FEATURE ENGINEERING PIPELINE")
    print("=" * 60)
    
    # Step 1: Join orders with items
    print("\nStep 1: Joining orders with items...")
    orders = join_orders_with_items(
        raw_features['fct_orders'],
        raw_features['fct_order_items']
    )
    
    # Step 2: Aggregate to hourly
    print("\nStep 2: Aggregating to hourly demand...")
    hourly = aggregate_to_hourly(orders)
    
    # Step 3: Add time features
    print("\nStep 3: Adding time features...")
    hourly = add_time_features(hourly)
    
    # Step 3b: Add cyclical time features
    print("\nStep 3b: Adding cyclical time features...")
    hourly = add_cyclical_time_features(hourly)
    
    # Step 3c: Add time context indicators
    print("\nStep 3c: Adding time context indicators...")
    hourly = add_time_context_indicators(hourly)
    
    # Step 4: Join place features
    print("\nStep 4: Joining place features...")
    combined = join_place_features(hourly, raw_features['dim_places'])
    
    # Step 5: Add campaign features
    print("\nStep 5: Adding campaign features...")
    combined = add_campaign_features(combined, raw_features['fct_campaigns'])
    
    # Step 6: Add lag features
    print("\nStep 6: Adding lag features...")
    combined = add_lag_features(combined)
    
    # Step 6b: Add venue-specific historical features (Phase 2)
    print("\nStep 6b: Adding venue-specific historical features...")
    combined = add_venue_specific_features(combined)
    
    # Step 7: Add weather features
    print("\nStep 7: Adding weather features...")
    combined = get_weather_for_demand_data(combined)
    
    # Step 7b: Add weather interaction features (Phase 2)
    print("\nStep 7b: Adding weather interaction features...")
    combined = add_weather_interaction_features(combined)
    
    # Step 8: Add holiday features
    print("\nStep 8: Adding holiday features...")
    combined = add_holiday_feature(combined)
    
    # Final cleanup
    combined = combined.drop(columns=['date', 'time'], errors='ignore')
    
    print("\n" + "=" * 60)
    print(f"   Final dataset: {combined.shape[0]:,} rows × {combined.shape[1]} columns")
    print(f"   Target: 'item_count'")
    print(f"   Features: {list(combined.columns)}")
    print("=" * 60)
    
    return combined

if __name__ == "__main__":
    datasets = load_all_csvs_from_folder("data")
    print(f"\nLoaded {len(datasets)} datasets: {list(datasets.keys())}")

    raw_features = get_raw_features(datasets, "data/columns.csv")
    print(f"\nExtracted raw features for {len(raw_features)} datasets: {list(raw_features.keys())}")
    
    combined = combine_features(raw_features)
    print(f"\nCombined features shape: {combined.shape}")
    print(combined.info())

    combined.to_csv("data/processed/combined_features.csv", index=False)
    print(f"Saved combined features to data/processed/combined_features.csv")