"""
Comprehensive tests for Feature Engineering Pipeline

Tests cover:
1. Data Loading - CSV loading, raw feature extraction
2. Order Processing - Join orders with items, aggregation
3. Time Features - Time-based, cyclical, context indicators
4. Venue Features - Venue-specific historical patterns
5. Lag Features - Rolling windows, lag indicators
6. Weather Features - Weather interaction features
7. Pipeline Integration - End-to-end feature preparation

Usage:
    pytest tests/test_feature_engineering.py -v
    pytest tests/test_feature_engineering.py::TestTimeFeatures -v
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import sys
import os

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.feature_engineering import (
    join_orders_with_items,
    aggregate_to_hourly,
    add_time_features,
    add_cyclical_time_features,
    add_time_context_indicators,
    add_venue_specific_features,
    add_weekend_specific_features,
    add_weather_interaction_features
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def sample_orders():
    """Create sample orders DataFrame."""
    base_time = datetime(2026, 1, 1, 10, 0, 0)
    
    orders = []
    for i in range(100):
        order_time = base_time + timedelta(hours=i % 24, days=i // 24)
        orders.append({
            'id': f'order_{i}',
            'created': int(order_time.timestamp()),
            'place_id': f'place_{i % 3}',  # 3 venues
            'total_amount': np.random.uniform(15, 50)
        })
    
    return pd.DataFrame(orders)


@pytest.fixture
def sample_order_items():
    """Create sample order items DataFrame."""
    items = ['burger', 'pizza', 'salad', 'fries', 'drink']
    
    order_items = []
    for i in range(100):
        num_items = np.random.randint(1, 4)
        for j in range(num_items):
            order_items.append({
                'order_id': f'order_{i}',
                'item_id': np.random.choice(items)
            })
    
    return pd.DataFrame(order_items)


@pytest.fixture
def sample_hourly_data():
    """Create sample hourly aggregated data."""
    base_time = datetime(2026, 1, 1, 0, 0, 0)
    
    data = []
    for day in range(30):  # 30 days
        for hour in range(24):
            for place_id in ['place_0', 'place_1', 'place_2']:
                dt = base_time + timedelta(days=day, hours=hour)
                data.append({
                    'place_id': place_id,
                    'date': dt.date(),
                    'hour': hour,
                    'datetime': dt,
                    'item_count': np.random.randint(5, 30),
                    'order_count': np.random.randint(2, 15),
                    'total_revenue': np.random.uniform(100, 500)
                })
    
    return pd.DataFrame(data)


@pytest.fixture
def sample_data_with_weather(sample_hourly_data):
    """Create sample data with weather features."""
    df = sample_hourly_data.copy()
    df['temperature_2m'] = np.random.uniform(5, 25, len(df))
    df['precipitation'] = np.random.uniform(0, 5, len(df))
    df['wind_speed_10m'] = np.random.uniform(0, 30, len(df))
    df['relative_humidity_2m'] = np.random.uniform(40, 90, len(df))
    df['cloud_cover'] = np.random.uniform(0, 100, len(df))
    return df


# =============================================================================
# TEST ORDER PROCESSING
# =============================================================================

class TestOrderProcessing:
    """Test order processing functions."""
    
    def test_join_orders_with_items(self, sample_orders, sample_order_items):
        """Test joining orders with items."""
        result = join_orders_with_items(sample_orders, sample_order_items)
        
        assert 'item_count' in result.columns
        assert 'created_dt' in result.columns
        assert 'date' in result.columns
        assert 'hour' in result.columns
    
    def test_join_preserves_order_count(self, sample_orders, sample_order_items):
        """Test that join preserves original order count."""
        result = join_orders_with_items(sample_orders, sample_order_items)
        
        assert len(result) == len(sample_orders)
    
    def test_join_item_count_is_numeric(self, sample_orders, sample_order_items):
        """Test that item_count is numeric."""
        result = join_orders_with_items(sample_orders, sample_order_items)
        
        assert pd.api.types.is_numeric_dtype(result['item_count'])
    
    def test_join_handles_orders_without_items(self):
        """Test handling orders with no matching items."""
        orders = pd.DataFrame({
            'id': ['order_1', 'order_2'],
            'created': [1704067200, 1704070800],  # Unix timestamps
            'place_id': ['place_1', 'place_1'],
            'total_amount': [25.0, 30.0]
        })
        
        items = pd.DataFrame({
            'order_id': ['order_1'],  # Only order_1 has items
            'item_id': ['burger']
        })
        
        result = join_orders_with_items(orders, items)
        
        # order_2 should have item_count = 0
        assert result.loc[result['id'] == 'order_2', 'item_count'].values[0] == 0


class TestAggregation:
    """Test hourly aggregation."""
    
    def test_aggregate_to_hourly(self, sample_orders, sample_order_items):
        """Test hourly aggregation."""
        orders = join_orders_with_items(sample_orders, sample_order_items)
        result = aggregate_to_hourly(orders)
        
        assert 'item_count' in result.columns
        assert 'order_count' in result.columns
        assert 'total_revenue' in result.columns
    
    def test_aggregate_has_datetime(self, sample_orders, sample_order_items):
        """Test datetime column is created."""
        orders = join_orders_with_items(sample_orders, sample_order_items)
        result = aggregate_to_hourly(orders)
        
        assert 'datetime' in result.columns
        assert pd.api.types.is_datetime64_any_dtype(result['datetime'])
    
    def test_aggregate_groups_by_venue(self, sample_orders, sample_order_items):
        """Test aggregation groups by venue."""
        orders = join_orders_with_items(sample_orders, sample_order_items)
        result = aggregate_to_hourly(orders)
        
        # Should have data grouped by place_id
        assert 'place_id' in result.columns
        assert result['place_id'].nunique() <= sample_orders['place_id'].nunique()


# =============================================================================
# TEST TIME FEATURES
# =============================================================================

class TestTimeFeatures:
    """Test time-based feature engineering."""
    
    def test_add_time_features(self, sample_hourly_data):
        """Test adding basic time features."""
        result = add_time_features(sample_hourly_data)
        
        assert 'day_of_week' in result.columns
        assert 'month' in result.columns
        assert 'week_of_year' in result.columns
    
    def test_day_of_week_range(self, sample_hourly_data):
        """Test day_of_week is in valid range."""
        result = add_time_features(sample_hourly_data)
        
        assert result['day_of_week'].min() >= 0
        assert result['day_of_week'].max() <= 6
    
    def test_month_range(self, sample_hourly_data):
        """Test month is in valid range."""
        result = add_time_features(sample_hourly_data)
        
        assert result['month'].min() >= 1
        assert result['month'].max() <= 12


class TestCyclicalFeatures:
    """Test cyclical time encoding."""
    
    def test_add_cyclical_features(self, sample_hourly_data):
        """Test adding cyclical time features."""
        df = add_time_features(sample_hourly_data)
        result = add_cyclical_time_features(df)
        
        assert 'hour_sin' in result.columns
        assert 'hour_cos' in result.columns
        assert 'day_of_week_sin' in result.columns
        assert 'day_of_week_cos' in result.columns
        assert 'month_sin' in result.columns
        assert 'month_cos' in result.columns
    
    def test_cyclical_values_range(self, sample_hourly_data):
        """Test cyclical values are in [-1, 1] range."""
        df = add_time_features(sample_hourly_data)
        result = add_cyclical_time_features(df)
        
        assert result['hour_sin'].min() >= -1
        assert result['hour_sin'].max() <= 1
        assert result['hour_cos'].min() >= -1
        assert result['hour_cos'].max() <= 1
    
    def test_cyclical_continuity(self, sample_hourly_data):
        """Test cyclical encoding provides continuity (hour 23 ≈ hour 0)."""
        df = add_time_features(sample_hourly_data)
        result = add_cyclical_time_features(df)
        
        # Hour 23 and hour 0 should have similar cyclical values
        hour_23 = result[result['hour'] == 23]['hour_sin'].mean()
        hour_0 = result[result['hour'] == 0]['hour_sin'].mean()
        
        # They should be close (both near sin(0) = 0)
        assert abs(hour_23 - hour_0) < 0.5


class TestTimeContextIndicators:
    """Test time context indicators."""
    
    def test_add_context_indicators(self, sample_hourly_data):
        """Test adding time context indicators."""
        df = add_time_features(sample_hourly_data)
        result = add_time_context_indicators(df)
        
        assert 'is_lunch_rush' in result.columns
        assert 'is_dinner_rush' in result.columns
        assert 'is_weekend' in result.columns
    
    def test_lunch_rush_hours(self, sample_hourly_data):
        """Test lunch rush is correctly identified."""
        df = add_time_features(sample_hourly_data)
        result = add_time_context_indicators(df)
        
        # Hour 12 should be lunch rush
        hour_12 = result[result['hour'] == 12]['is_lunch_rush'].unique()
        assert 1 in hour_12
        
        # Hour 3 should not be lunch rush
        hour_3 = result[result['hour'] == 3]['is_lunch_rush'].unique()
        assert all(h == 0 for h in hour_3)
    
    def test_weekend_detection(self, sample_hourly_data):
        """Test weekend is correctly identified."""
        df = add_time_features(sample_hourly_data)
        result = add_time_context_indicators(df)
        
        # Saturday (day_of_week=5) should be weekend
        saturday = result[result['day_of_week'] == 5]['is_weekend'].unique()
        assert 1 in saturday
        
        # Monday (day_of_week=0) should not be weekend
        monday = result[result['day_of_week'] == 0]['is_weekend'].unique()
        assert all(m == 0 for m in monday)
    
    def test_friday_evening_indicator(self, sample_hourly_data):
        """Test Friday evening indicator."""
        df = add_time_features(sample_hourly_data)
        result = add_time_context_indicators(df)
        
        assert 'friday_evening' in result.columns
        
        # Friday evening (day=4, hour>=17)
        friday_19 = result[(result['day_of_week'] == 4) & (result['hour'] == 19)]
        if len(friday_19) > 0:
            assert friday_19['friday_evening'].values[0] == 1
    
    def test_month_boundaries(self, sample_hourly_data):
        """Test month start/end indicators."""
        df = add_time_features(sample_hourly_data)
        result = add_time_context_indicators(df)
        
        assert 'is_month_start' in result.columns
        assert 'is_month_end' in result.columns


# =============================================================================
# TEST VENUE FEATURES
# =============================================================================

class TestVenueFeatures:
    """Test venue-specific features."""
    
    @pytest.fixture
    def data_with_rolling(self, sample_hourly_data):
        """Add required rolling features."""
        df = sample_hourly_data.copy()
        df = df.sort_values(['place_id', 'datetime'])
        df['rolling_7d_avg_items'] = df.groupby('place_id')['item_count'].transform(
            lambda x: x.rolling(window=7*24, min_periods=1).mean()
        )
        df['rolling_30d_avg_items'] = df.groupby('place_id')['item_count'].transform(
            lambda x: x.rolling(window=30*24, min_periods=1).mean()
        )
        return df
    
    def test_add_venue_features(self, data_with_rolling):
        """Test adding venue-specific features."""
        df = add_time_features(data_with_rolling)
        result = add_venue_specific_features(df)
        
        assert 'venue_hour_avg' in result.columns
        assert 'venue_dow_avg' in result.columns
        assert 'venue_volatility' in result.columns
    
    def test_venue_hour_avg_calculation(self, data_with_rolling):
        """Test venue hour average is calculated correctly."""
        df = add_time_features(data_with_rolling)
        result = add_venue_specific_features(df)
        
        # Should have different averages for different venues
        venue_0_avg = result[result['place_id'] == 'place_0']['venue_hour_avg'].mean()
        assert not pd.isna(venue_0_avg)
    
    def test_venue_volatility_non_negative(self, data_with_rolling):
        """Test venue volatility is non-negative."""
        df = add_time_features(data_with_rolling)
        result = add_venue_specific_features(df)
        
        assert (result['venue_volatility'] >= 0).all()
    
    def test_venue_growth_ratio(self, data_with_rolling):
        """Test venue growth ratio is calculated."""
        df = add_time_features(data_with_rolling)
        result = add_venue_specific_features(df)
        
        assert 'venue_growth_recent_vs_historical' in result.columns
        # Ratio should be positive (or 1 if no historical data)
        assert (result['venue_growth_recent_vs_historical'] > 0).all()


class TestWeekendFeatures:
    """Test weekend-specific features."""
    
    @pytest.fixture
    def data_for_weekend(self, sample_hourly_data):
        """Prepare data for weekend features."""
        df = add_time_features(sample_hourly_data)
        return df
    
    def test_add_weekend_features(self, data_for_weekend):
        """Test adding weekend-specific features."""
        result = add_weekend_specific_features(data_for_weekend)
        
        assert 'venue_weekend_avg' in result.columns
        assert 'venue_weekday_avg' in result.columns
        assert 'venue_weekend_lift' in result.columns
    
    def test_weekend_lift_positive(self, data_for_weekend):
        """Test weekend lift is positive."""
        result = add_weekend_specific_features(data_for_weekend)
        
        assert (result['venue_weekend_lift'] > 0).all()
    
    def test_weekend_day_position(self, data_for_weekend):
        """Test weekend day position calculation."""
        result = add_weekend_specific_features(data_for_weekend)
        
        assert 'weekend_day_position' in result.columns
        
        # Friday should have position 0
        friday_pos = result[result['day_of_week'] == 4]['weekend_day_position'].unique()
        assert 0 in friday_pos
        
        # Saturday should have position 1
        saturday_pos = result[result['day_of_week'] == 5]['weekend_day_position'].unique()
        assert 1 in saturday_pos


# =============================================================================
# TEST WEATHER FEATURES
# =============================================================================

class TestWeatherFeatures:
    """Test weather interaction features."""
    
    def test_add_weather_features(self, sample_data_with_weather):
        """Test adding weather interaction features."""
        df = add_time_features(sample_data_with_weather)
        result = add_weather_interaction_features(df)
        
        assert 'feels_like_temp' in result.columns
        assert 'bad_weather_score' in result.columns
    
    def test_feels_like_temperature(self, sample_data_with_weather):
        """Test feels-like temperature calculation."""
        df = add_time_features(sample_data_with_weather)
        result = add_weather_interaction_features(df)
        
        assert result['feels_like_temp'].notna().any()
    
    def test_bad_weather_score_range(self, sample_data_with_weather):
        """Test bad weather score is in valid range."""
        df = add_time_features(sample_data_with_weather)
        result = add_weather_interaction_features(df)
        
        # Score should be between 0 and 1
        assert result['bad_weather_score'].min() >= 0
        assert result['bad_weather_score'].max() <= 1
    
    def test_temperature_change(self, sample_data_with_weather):
        """Test temperature change features."""
        df = add_time_features(sample_data_with_weather)
        df = df.sort_values(['place_id', 'datetime'])
        result = add_weather_interaction_features(df)
        
        assert 'temp_change_1h' in result.columns
        assert 'temp_change_3h' in result.columns
    
    def test_handles_missing_weather(self, sample_hourly_data):
        """Test handling data without weather columns."""
        df = add_time_features(sample_hourly_data)
        
        # Should not crash without weather columns
        result = add_weather_interaction_features(df)
        assert len(result) == len(df)


# =============================================================================
# EDGE CASES
# =============================================================================

class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_dataframe(self):
        """Test handling empty DataFrame."""
        empty_df = pd.DataFrame(columns=['place_id', 'date', 'hour', 'datetime', 'item_count'])
        empty_df['datetime'] = pd.to_datetime(empty_df['datetime'])
        
        result = add_time_features(empty_df)
        assert len(result) == 0
    
    def test_single_row(self):
        """Test handling single row DataFrame."""
        single_row = pd.DataFrame({
            'place_id': ['place_1'],
            'date': [datetime(2026, 1, 1).date()],
            'hour': [12],
            'datetime': [datetime(2026, 1, 1, 12, 0, 0)],
            'item_count': [10]
        })
        
        result = add_time_features(single_row)
        assert len(result) == 1
        assert result['day_of_week'].values[0] >= 0
    
    def test_all_same_hour(self):
        """Test data with all same hour."""
        same_hour = pd.DataFrame({
            'place_id': ['place_1'] * 10,
            'date': [datetime(2026, 1, d+1).date() for d in range(10)],
            'hour': [12] * 10,
            'datetime': [datetime(2026, 1, d+1, 12, 0, 0) for d in range(10)],
            'item_count': list(range(10))
        })
        
        result = add_time_features(same_hour)
        result = add_cyclical_time_features(result)
        
        # All hour_sin values should be the same
        assert result['hour_sin'].nunique() == 1
    
    def test_midnight_handling(self):
        """Test handling of midnight (hour 0)."""
        midnight_data = pd.DataFrame({
            'place_id': ['place_1'],
            'date': [datetime(2026, 1, 1).date()],
            'hour': [0],
            'datetime': [datetime(2026, 1, 1, 0, 0, 0)],
            'item_count': [5]
        })
        
        result = add_time_features(midnight_data)
        result = add_cyclical_time_features(result)
        result = add_time_context_indicators(result)
        
        # Midnight should be late night
        assert result['is_late_night'].values[0] == 1


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestIntegration:
    """Integration tests for feature pipeline."""
    
    def test_full_pipeline(self, sample_orders, sample_order_items):
        """Test complete feature engineering pipeline."""
        # Step 1: Join orders with items
        orders = join_orders_with_items(sample_orders, sample_order_items)
        
        # Step 2: Aggregate to hourly
        hourly = aggregate_to_hourly(orders)
        
        # Step 3: Add time features
        with_time = add_time_features(hourly)
        
        # Step 4: Add cyclical features
        with_cyclical = add_cyclical_time_features(with_time)
        
        # Step 5: Add context indicators
        result = add_time_context_indicators(with_cyclical)
        
        # Verify final output
        assert 'item_count' in result.columns
        assert 'hour_sin' in result.columns
        assert 'is_weekend' in result.columns
    
    def test_feature_count(self, sample_orders, sample_order_items):
        """Test feature count increases through pipeline."""
        orders = join_orders_with_items(sample_orders, sample_order_items)
        initial_cols = len(orders.columns)
        
        hourly = aggregate_to_hourly(orders)
        hourly_cols = len(hourly.columns)
        
        with_time = add_time_features(hourly)
        time_cols = len(with_time.columns)
        
        with_cyclical = add_cyclical_time_features(with_time)
        cyclical_cols = len(with_cyclical.columns)
        
        # Each step should maintain or add features
        # aggregate_to_hourly restructures data with datetime column
        assert hourly_cols >= 5  # At least datetime, place_id, order_count, revenue, item_count
        # add_time_features adds time components
        assert time_cols >= hourly_cols  # Should have at least same columns
        # add_cyclical_time_features adds sin/cos features
        assert cyclical_cols > time_cols  # Must add new cyclical features
    
    def test_no_nan_in_core_features(self, sample_orders, sample_order_items):
        """Test core features have no NaN values."""
        orders = join_orders_with_items(sample_orders, sample_order_items)
        hourly = aggregate_to_hourly(orders)
        result = add_time_features(hourly)
        result = add_cyclical_time_features(result)
        
        # Core time features should not have NaN
        assert result['day_of_week'].notna().all()
        assert result['hour_sin'].notna().all()
        assert result['hour_cos'].notna().all()
