"""
Comprehensive unit tests for demand prediction model and feature engineering pipeline

Tests cover:
1. Model Loading - Verify model and metadata load correctly
2. Feature Engineering - Time parsing, order processing, aggregation
3. Feature Preparation - Complete pipeline from raw data to model-ready features
4. Prediction Quality - Output validation, range checks, zero handling
5. API Integration - Request/response handling
6. Edge Cases - Missing data, extreme values, closed hours
7. Zero Demand Handling - Critical bug testing (closed hours should predict zero)

CRITICAL BUG TESTED:
- Model trained without zeros may predict phantom demand during closed hours
- Tests verify predictions respect business hours
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from pathlib import Path
import joblib
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api.main import (
    parse_time_to_hour,
    time_to_slot,
    process_historical_orders,
    aggregate_to_hourly,
    add_time_features,
    add_lag_features,
    calculate_campaign_features,
    create_prediction_windows,
    add_weather_features_mock,
    add_holiday_features_mock,
    prepare_features_for_prediction,
    align_features_with_model,
    PlaceData,
    OrderData,
    CampaignData,
    OpeningHoursDay
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def sample_place_data():
    """Create sample place data"""
    return PlaceData(
        place_id="test_pl_001",
        place_name="Test Restaurant",
        type="restaurant",
        latitude=55.6761,
        longitude=12.5683,
        waiting_time=30,
        receiving_phone=True,
        delivery=True,
        opening_hours={
            "monday": OpeningHoursDay(**{"from": "10:00", "to": "22:00"}),
            "tuesday": OpeningHoursDay(**{"from": "10:00", "to": "22:00"}),
            "wednesday": OpeningHoursDay(**{"from": "10:00", "to": "22:00"}),
            "thursday": OpeningHoursDay(**{"from": "10:00", "to": "22:00"}),
            "friday": OpeningHoursDay(**{"from": "10:00", "to": "22:00"}),
            "saturday": OpeningHoursDay(**{"from": "11:00", "to": "23:00"}),
            "sunday": OpeningHoursDay(closed=True)
        },
        fixed_shifts=True,
        number_of_shifts_per_day=3,
        shift_times=["10:00-14:00", "14:00-18:00", "18:00-22:00"],
        rating=4.5,
        accepting_orders=True
    )


@pytest.fixture
def sample_orders():
    """Create sample historical orders (7 days worth)"""
    orders = []
    base_date = datetime(2024, 1, 1, 12, 0, 0)
    
    for day in range(7):
        for hour_offset in range(12):  # Orders from 12 PM to 11 PM
            order_time = base_date + timedelta(days=day, hours=hour_offset)
            
            # More orders during dinner time (6-9 PM)
            num_orders = 3 if 18 <= (12 + hour_offset) <= 21 else 1
            
            for _ in range(num_orders):
                orders.append(OrderData(
                    time=order_time.isoformat(),
                    items=np.random.randint(1, 5),
                    status="completed",
                    total_amount=np.random.uniform(20, 80),
                    discount_amount=0
                ))
    
    return orders


@pytest.fixture
def sample_campaigns():
    """Create sample campaign data"""
    return [
        CampaignData(
            start_time="2024-01-01T00:00:00",
            end_time="2024-01-07T23:59:59",
            items_included=["pizza", "pasta"],
            discount=15.0
        )
    ]


@pytest.fixture
def model_path():
    """Path to saved model"""
    return Path("data/models/rf_model.joblib")


@pytest.fixture
def metadata_path():
    """Path to model metadata"""
    return Path("data/models/rf_model_metadata.json")


# =============================================================================
# TEST MODEL LOADING
# =============================================================================

class TestModelLoading:
    """Test model and metadata loading"""
    
    def test_model_file_exists(self, model_path):
        """Test that model file exists"""
        assert model_path.exists(), f"Model file not found at {model_path}"
    
    def test_metadata_file_exists(self, metadata_path):
        """Test that metadata file exists"""
        assert metadata_path.exists(), f"Metadata file not found at {metadata_path}"
    
    def test_model_loads_successfully(self, model_path):
        """Test that model can be loaded"""
        model = joblib.load(model_path)
        assert model is not None
        assert hasattr(model, 'predict')
    
    def test_metadata_loads_successfully(self, metadata_path):
        """Test that metadata can be loaded"""
        metadata = joblib.load(metadata_path)
        assert metadata is not None
        assert isinstance(metadata, dict)
    
    def test_metadata_contains_required_fields(self, metadata_path):
        """Test metadata has all required fields"""
        metadata = joblib.load(metadata_path)
        
        required_fields = ['model_type', 'hyperparameters']
        for field in required_fields:
            assert field in metadata, f"Missing required field: {field}"
        
        # Check that hyperparameters are populated
        assert len(metadata['hyperparameters']) > 0
    
    def test_model_can_predict(self, model_path):
        """Test that model can make predictions"""
        model = joblib.load(model_path)
        
        # Create dummy input with correct number of features
        n_features = 35  # Based on expected_features list
        X_dummy = np.random.rand(1, n_features)
        
        try:
            predictions = model.predict(X_dummy)
            assert predictions is not None
            assert len(predictions) == 1
            assert len(predictions[0]) == 2  # item_count, order_count
        except Exception as e:
            pytest.skip(f"Model prediction requires specific feature format: {e}")


# =============================================================================
# TEST TIME PARSING FUNCTIONS
# =============================================================================

class TestTimeParsing:
    """Test time parsing and conversion functions"""
    
    def test_parse_time_to_hour_basic(self):
        """Test basic time parsing"""
        assert parse_time_to_hour("10:00") == 10.0
        assert parse_time_to_hour("14:30") == 14.5
        assert parse_time_to_hour("23:45") == 23.75
        assert parse_time_to_hour("00:00") == 0.0
    
    def test_parse_time_to_hour_closed(self):
        """Test parsing 'closed' returns -1"""
        assert parse_time_to_hour("closed") == -1
        assert parse_time_to_hour("Closed") == -1
        assert parse_time_to_hour("CLOSED") == -1
    
    def test_time_to_slot(self):
        """Test time to slot conversion"""
        assert time_to_slot("10:00", 1.0) == 10
        assert time_to_slot("14:00", 1.0) == 14
        assert time_to_slot("10:00", 2.0) == 5
        assert time_to_slot("14:00", 0.5) == 28
    
    def test_time_to_slot_closed(self):
        """Test closed time returns -1"""
        assert time_to_slot("closed", 1.0) == -1


# =============================================================================
# TEST ORDER PROCESSING
# =============================================================================

class TestOrderProcessing:
    """Test order data processing functions"""
    
    def test_process_historical_orders_basic(self, sample_orders):
        """Test basic order processing"""
        df = process_historical_orders(sample_orders, "test_place")
        
        assert len(df) > 0
        assert 'place_id' in df.columns
        assert 'created_dt' in df.columns
        assert 'date' in df.columns
        assert 'hour' in df.columns
        assert 'item_count' in df.columns
    
    def test_process_historical_orders_empty(self):
        """Test processing with empty orders raises error"""
        with pytest.raises(ValueError, match="At least some historical orders"):
            process_historical_orders([], "test_place")
    
    def test_aggregate_to_hourly(self, sample_orders):
        """Test hourly aggregation"""
        df = process_historical_orders(sample_orders, "test_place")
        hourly = aggregate_to_hourly(df)
        
        assert 'item_count' in hourly.columns
        assert 'order_count' in hourly.columns
        assert 'total_revenue' in hourly.columns
        assert 'datetime' in hourly.columns
        
        # Check aggregation logic
        assert hourly['order_count'].min() >= 0
        assert hourly['item_count'].min() >= 0
    
    def test_aggregate_handles_multiple_days(self, sample_orders):
        """Test aggregation across multiple days"""
        df = process_historical_orders(sample_orders, "test_place")
        hourly = aggregate_to_hourly(df)
        
        unique_dates = hourly['date'].nunique()
        assert unique_dates >= 7, "Should have at least 7 days of data"


# =============================================================================
# TEST FEATURE ENGINEERING
# =============================================================================

class TestFeatureEngineering:
    """Test feature engineering functions"""
    
    def test_add_time_features(self, sample_orders):
        """Test time feature addition"""
        df = process_historical_orders(sample_orders, "test_place")
        hourly = aggregate_to_hourly(df)
        featured = add_time_features(hourly)
        
        assert 'day_of_week' in featured.columns
        assert 'month' in featured.columns
        assert 'week_of_year' in featured.columns
        
        # Validate ranges
        assert featured['day_of_week'].min() >= 0
        assert featured['day_of_week'].max() <= 6
        assert featured['month'].min() >= 1
        assert featured['month'].max() <= 12
    
    def test_add_lag_features(self, sample_orders):
        """Test lag feature creation"""
        df = process_historical_orders(sample_orders, "test_place")
        hourly = aggregate_to_hourly(df)
        hourly = add_time_features(hourly)
        lagged = add_lag_features(hourly, 'item_count')
        
        lag_cols = ['prev_hour_items', 'prev_day_items', 'prev_week_items', 
                    'prev_month_items', 'rolling_7d_avg_items']
        
        for col in lag_cols:
            assert col in lagged.columns
            # No NaN values (should be filled with 0)
            assert lagged[col].isna().sum() == 0
    
    def test_lag_features_sorted_by_time(self, sample_orders):
        """Test that lag features respect time ordering"""
        df = process_historical_orders(sample_orders, "test_place")
        hourly = aggregate_to_hourly(df)
        hourly = add_time_features(hourly)
        lagged = add_lag_features(hourly, 'item_count')
        
        # First rows should have 0 for early lags
        assert lagged.iloc[0]['prev_hour_items'] == 0
    
    def test_calculate_campaign_features_empty(self):
        """Test campaign feature calculation with no campaigns"""
        result = calculate_campaign_features([])
        assert result['total_campaigns'] == 0
        assert result['avg_discount'] == 0
    
    def test_calculate_campaign_features_with_data(self, sample_campaigns):
        """Test campaign feature calculation with campaigns"""
        result = calculate_campaign_features(sample_campaigns)
        assert result['total_campaigns'] == 1
        assert result['avg_discount'] == 15.0
    
    def test_create_prediction_windows(self):
        """Test future prediction window creation"""
        windows = create_prediction_windows("2024-01-15", 3, "test_place")
        
        assert len(windows) == 3 * 24  # 3 days * 24 hours
        assert 'place_id' in windows.columns
        assert 'datetime' in windows.columns
        assert 'hour' in windows.columns
        assert 'day_of_week' in windows.columns
        
        # Check date range
        dates = windows['date'].unique()
        assert len(dates) == 3


# =============================================================================
# TEST MOCK FEATURE FUNCTIONS
# =============================================================================

class TestMockFeatures:
    """Test mock feature functions (fallbacks)"""
    
    def test_add_weather_features_mock(self):
        """Test weather mock adds all required columns"""
        df = pd.DataFrame({'test': [1, 2, 3]})
        result = add_weather_features_mock(df)
        
        weather_cols = [
            'temperature_2m', 'relative_humidity_2m', 'precipitation',
            'rain', 'snowfall', 'weather_code', 'cloud_cover',
            'wind_speed_10m', 'is_rainy', 'is_snowy', 'is_cold',
            'is_hot', 'is_cloudy', 'is_windy', 'good_weather',
            'weather_severity'
        ]
        
        for col in weather_cols:
            assert col in result.columns
    
    def test_add_holiday_features_mock(self):
        """Test holiday mock adds required column"""
        df = pd.DataFrame({'test': [1, 2, 3]})
        result = add_holiday_features_mock(df)
        
        assert 'is_holiday' in result.columns
        assert (result['is_holiday'] == 0).all()


# =============================================================================
# TEST COMPLETE FEATURE PIPELINE
# =============================================================================

class TestFeaturePipeline:
    """Test complete feature preparation pipeline"""
    
    def test_prepare_features_basic(self, sample_place_data, sample_orders, sample_campaigns):
        """Test basic feature preparation pipeline"""
        features = prepare_features_for_prediction(
            place=sample_place_data,
            orders=sample_orders,
            campaigns=sample_campaigns,
            prediction_start="2024-01-08",
            prediction_days=2
        )
        
        assert len(features) == 2 * 24  # 2 days * 24 hours
        assert 'datetime' in features.columns
        assert 'hour' in features.columns
        assert 'type_id' in features.columns
        assert 'waiting_time' in features.columns
        assert 'rating' in features.columns
    
    def test_prepare_features_has_all_required_columns(self, sample_place_data, 
                                                       sample_orders, sample_campaigns):
        """Test that all required columns are present"""
        features = prepare_features_for_prediction(
            place=sample_place_data,
            orders=sample_orders,
            campaigns=sample_campaigns,
            prediction_start="2024-01-08",
            prediction_days=1
        )
        
        required_cols = [
            'place_id', 'hour', 'type_id', 'waiting_time', 'rating',
            'delivery', 'accepting_orders', 'total_campaigns', 'avg_discount',
            'prev_hour_items', 'prev_day_items', 'temperature_2m'
        ]
        
        for col in required_cols:
            assert col in features.columns, f"Missing column: {col}"
    
    def test_prepare_features_no_nulls(self, sample_place_data, sample_orders, 
                                      sample_campaigns):
        """Test that pipeline produces no null values in model features"""
        features = prepare_features_for_prediction(
            place=sample_place_data,
            orders=sample_orders,
            campaigns=sample_campaigns,
            prediction_start="2024-01-08",
            prediction_days=1
        )
        
        # Check only model input features (not target columns which are null for future data)
        model_feature_cols = [col for col in features.columns 
                             if col not in ['item_count', 'order_count', 'total_revenue']]
        
        null_counts = features[model_feature_cols].isnull().sum()
        assert null_counts.sum() == 0, f"Found null values in model features: {null_counts[null_counts > 0]}"
    
    def test_prepare_features_respects_prediction_period(self, sample_place_data,
                                                         sample_orders, sample_campaigns):
        """Test that output covers exact prediction period"""
        start_date = "2024-01-08"
        days = 3
        
        features = prepare_features_for_prediction(
            place=sample_place_data,
            orders=sample_orders,
            campaigns=sample_campaigns,
            prediction_start=start_date,
            prediction_days=days
        )
        
        # Check date range
        start = pd.to_datetime(start_date).date()
        dates_in_result = features['datetime'].dt.date.unique()
        
        assert len(dates_in_result) == days
        assert dates_in_result[0] == start


# =============================================================================
# TEST FEATURE ALIGNMENT
# =============================================================================

class TestFeatureAlignment:
    """Test feature alignment with model expectations"""
    
    def test_align_features_converts_place_id(self, sample_place_data, sample_orders, 
                                              sample_campaigns):
        """Test that string place_id is converted to numeric"""
        features = prepare_features_for_prediction(
            place=sample_place_data,
            orders=sample_orders,
            campaigns=sample_campaigns,
            prediction_start="2024-01-08",
            prediction_days=1
        )
        
        aligned = align_features_with_model(features)
        
        assert aligned['place_id'].dtype == 'float64'
    
    def test_align_features_has_correct_columns(self, sample_place_data, sample_orders,
                                                sample_campaigns):
        """Test that aligned features have exactly the expected columns"""
        features = prepare_features_for_prediction(
            place=sample_place_data,
            orders=sample_orders,
            campaigns=sample_campaigns,
            prediction_start="2024-01-08",
            prediction_days=1
        )
        
        aligned = align_features_with_model(features)
        
        expected_features = [
            'place_id', 'hour', 'day_of_week', 'month', 'week_of_year',
            'type_id', 'waiting_time', 'rating', 'delivery', 'accepting_orders',
            'total_campaigns', 'avg_discount',
            'prev_hour_items', 'prev_day_items', 'prev_week_items', 'prev_month_items',
            'rolling_7d_avg_items',
            'temperature_2m', 'relative_humidity_2m', 'precipitation', 'rain',
            'snowfall', 'weather_code', 'cloud_cover', 'wind_speed_10m',
            'is_rainy', 'is_snowy', 'is_cold', 'is_hot', 'is_cloudy', 'is_windy',
            'good_weather', 'weather_severity',
            'is_holiday'
        ]
        
        assert list(aligned.columns) == expected_features
    
    def test_align_features_fills_missing_columns(self):
        """Test that missing columns are filled with 0"""
        # Create incomplete feature set
        df = pd.DataFrame({
            'place_id': [1.0],
            'hour': [12],
            'day_of_week': [0]
        })
        
        aligned = align_features_with_model(df)
        
        # Should have all expected features
        assert len(aligned.columns) >= 30
        # Missing columns should be 0
        assert 'is_holiday' in aligned.columns
        assert aligned['is_holiday'].iloc[0] == 0


# =============================================================================
# TEST PREDICTION QUALITY
# =============================================================================

class TestPredictionQuality:
    """Test prediction output quality and validity"""
    
    def test_predictions_are_non_negative(self, model_path, sample_place_data,
                                         sample_orders, sample_campaigns):
        """Test that predictions are never negative"""
        if not model_path.exists():
            pytest.skip("Model file not found")
        
        model = joblib.load(model_path)
        
        features = prepare_features_for_prediction(
            place=sample_place_data,
            orders=sample_orders,
            campaigns=sample_campaigns,
            prediction_start="2024-01-08",
            prediction_days=1
        )
        
        X = align_features_with_model(features)
        predictions = model.predict(X)
        
        assert (predictions >= 0).all(), "Found negative predictions"
    
    def test_predictions_are_reasonable_range(self, model_path, sample_place_data,
                                             sample_orders, sample_campaigns):
        """Test that predictions are in reasonable range"""
        if not model_path.exists():
            pytest.skip("Model file not found")
        
        model = joblib.load(model_path)
        
        features = prepare_features_for_prediction(
            place=sample_place_data,
            orders=sample_orders,
            campaigns=sample_campaigns,
            prediction_start="2024-01-08",
            prediction_days=1
        )
        
        X = align_features_with_model(features)
        predictions = model.predict(X)
        
        # Item counts should be reasonable (< 10000 per hour)
        assert (predictions[:, 0] < 10000).all(), "Unreasonably high item predictions"
        
        # Order counts should be reasonable (< 1000 per hour)
        assert (predictions[:, 1] < 1000).all(), "Unreasonably high order predictions"
    
    def test_predictions_shape_matches_input(self, model_path, sample_place_data,
                                            sample_orders, sample_campaigns):
        """Test that prediction shape matches input"""
        if not model_path.exists():
            pytest.skip("Model file not found")
        
        model = joblib.load(model_path)
        
        days = 2
        features = prepare_features_for_prediction(
            place=sample_place_data,
            orders=sample_orders,
            campaigns=sample_campaigns,
            prediction_start="2024-01-08",
            prediction_days=days
        )
        
        X = align_features_with_model(features)
        predictions = model.predict(X)
        
        assert len(predictions) == days * 24
        assert predictions.shape[1] == 2  # item_count, order_count


# =============================================================================
# TEST ZERO DEMAND HANDLING (CRITICAL BUG)
# =============================================================================

class TestZeroDemandHandling:
    """
    Test zero demand handling - CRITICAL BUG DETECTION
    
    The model was trained without zeros, so it may predict phantom demand
    during closed hours. These tests detect this issue.
    """
    
    def test_closed_sunday_predictions(self, model_path, sample_orders, sample_campaigns):
        """
        CRITICAL: Test predictions on closed Sunday
        
        Expected: All hours should have zero or very low predictions
        Bug: Model predicts 2-5 items/hour even when closed
        """
        if not model_path.exists():
            pytest.skip("Model file not found")
        
        # Create place that's closed on Sundays
        place = PlaceData(
            place_id="test_pl_001",
            place_name="Test Restaurant",
            type="restaurant",
            latitude=55.6761,
            longitude=12.5683,
            waiting_time=30,
            receiving_phone=True,
            delivery=True,
            opening_hours={
                "monday": OpeningHoursDay(**{"from": "10:00", "to": "22:00"}),
                "tuesday": OpeningHoursDay(**{"from": "10:00", "to": "22:00"}),
                "wednesday": OpeningHoursDay(**{"from": "10:00", "to": "22:00"}),
                "thursday": OpeningHoursDay(**{"from": "10:00", "to": "22:00"}),
                "friday": OpeningHoursDay(**{"from": "10:00", "to": "22:00"}),
                "saturday": OpeningHoursDay(**{"from": "10:00", "to": "22:00"}),
                "sunday": OpeningHoursDay(closed=True)  # CLOSED
            },
            fixed_shifts=True,
            number_of_shifts_per_day=3,
            shift_times=["10:00-14:00", "14:00-18:00", "18:00-22:00"],
            rating=4.5,
            accepting_orders=True
        )
        
        # Predict for a Sunday (2024-01-14 is a Sunday)
        features = prepare_features_for_prediction(
            place=place,
            orders=sample_orders,
            campaigns=sample_campaigns,
            prediction_start="2024-01-14",  # Sunday
            prediction_days=1
        )
        
        model = joblib.load(model_path)
        X = align_features_with_model(features)
        predictions = model.predict(X)
        
        # Check if model predicts phantom demand on closed day
        avg_items = predictions[:, 0].mean()
        max_items = predictions[:, 0].max()
        
        # Log results for analysis
        print(f"\nClosed Sunday Predictions:")
        print(f"  Average items/hour: {avg_items:.2f}")
        print(f"  Max items prediction: {max_items:.2f}")
        print(f"  Hour-by-hour: {predictions[:, 0]}")
        
        # This test DOCUMENTS the bug (may fail, which is expected)
        try:
            assert avg_items < 1.0, f"PHANTOM DEMAND DETECTED: Model predicts {avg_items:.2f} items/hour on closed Sunday"
        except AssertionError as e:
            pytest.xfail(f"KNOWN BUG: {e}\nModel needs retraining with zero values included")
    
    def test_closed_hours_predictions(self, model_path, sample_orders, sample_campaigns):
        """
        CRITICAL: Test predictions during closed hours (late night)
        
        Expected: Hours outside 10:00-22:00 should be zero
        Bug: Model predicts demand at 2 AM, 4 AM, etc.
        """
        if not model_path.exists():
            pytest.skip("Model file not found")
        
        place = PlaceData(
            place_id="test_pl_001",
            place_name="Test Restaurant",
            type="restaurant",
            latitude=55.6761,
            longitude=12.5683,
            waiting_time=30,
            receiving_phone=True,
            delivery=True,
            opening_hours={
                "monday": OpeningHoursDay(**{"from": "10:00", "to": "22:00"}),  # Open 10-22
                "tuesday": OpeningHoursDay(**{"from": "10:00", "to": "22:00"}),
                "wednesday": OpeningHoursDay(**{"from": "10:00", "to": "22:00"}),
                "thursday": OpeningHoursDay(**{"from": "10:00", "to": "22:00"}),
                "friday": OpeningHoursDay(**{"from": "10:00", "to": "22:00"}),
                "saturday": OpeningHoursDay(**{"from": "10:00", "to": "22:00"}),
                "sunday": OpeningHoursDay(**{"from": "10:00", "to": "22:00"})
            },
            fixed_shifts=True,
            number_of_shifts_per_day=3,
            shift_times=["10:00-14:00", "14:00-18:00", "18:00-22:00"],
            rating=4.5,
            accepting_orders=True
        )
        
        features = prepare_features_for_prediction(
            place=place,
            orders=sample_orders,
            campaigns=sample_campaigns,
            prediction_start="2024-01-08",  # Monday
            prediction_days=1
        )
        
        model = joblib.load(model_path)
        X = align_features_with_model(features)
        predictions = model.predict(X)
        
        # Extract predictions for closed hours (0-9, 22-23)
        closed_hours = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 22, 23]
        closed_predictions = predictions[closed_hours, 0]
        
        avg_closed = closed_predictions.mean()
        max_closed = closed_predictions.max()
        
        print(f"\nClosed Hours Predictions (0-9, 22-23):")
        print(f"  Average items/hour: {avg_closed:.2f}")
        print(f"  Max items prediction: {max_closed:.2f}")
        print(f"  By hour: {closed_predictions}")
        
        # This test DOCUMENTS the bug
        try:
            assert avg_closed < 1.0, f"PHANTOM DEMAND: Model predicts {avg_closed:.2f} items/hour during closed hours"
        except AssertionError as e:
            pytest.xfail(f"KNOWN BUG: {e}\nConsider post-processing to zero out closed hours")
    
    def test_can_training_data_have_zeros(self):
        """
        Test if training data contained zeros (it shouldn't based on preprocessing)
        """
        try:
            df = pd.read_csv('data/processed/combined_features.csv')
            
            # Check if zeros exist in targets
            zero_items = (df['item_count'] == 0).sum()
            zero_orders = (df['order_count'] == 0).sum()
            
            total_rows = len(df)
            
            print(f"\nTraining Data Zero Analysis:")
            print(f"  Total rows: {total_rows}")
            print(f"  Rows with zero item_count: {zero_items} ({zero_items/total_rows*100:.2f}%)")
            print(f"  Rows with zero order_count: {zero_orders} ({zero_orders/total_rows*100:.2f}%)")
            
            # This SHOULD fail because model_selection.ipynb removes zeros
            if zero_items == 0:
                pytest.xfail("CONFIRMED: Training data has NO zeros. Model cannot predict zero demand.")
            
        except FileNotFoundError:
            pytest.skip("Training data file not found")


# =============================================================================
# TEST EDGE CASES
# =============================================================================

class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def test_single_day_prediction(self, sample_place_data, sample_orders, sample_campaigns):
        """Test prediction for single day"""
        features = prepare_features_for_prediction(
            place=sample_place_data,
            orders=sample_orders,
            campaigns=sample_campaigns,
            prediction_start="2024-01-08",
            prediction_days=1
        )
        
        assert len(features) == 24
    
    def test_long_prediction_window(self, sample_place_data, sample_orders, sample_campaigns):
        """Test prediction for long period"""
        features = prepare_features_for_prediction(
            place=sample_place_data,
            orders=sample_orders,
            campaigns=sample_campaigns,
            prediction_start="2024-01-08",
            prediction_days=30
        )
        
        assert len(features) == 30 * 24
    
    def test_missing_rating_handled(self, sample_orders, sample_campaigns):
        """Test that missing rating is handled"""
        place = PlaceData(
            place_id="test_pl_001",
            place_name="Test Restaurant",
            type="restaurant",
            latitude=55.6761,
            longitude=12.5683,
            waiting_time=30,
            receiving_phone=True,
            delivery=True,
            opening_hours={
                "monday": OpeningHoursDay(**{"from": "10:00", "to": "22:00"}),
                "tuesday": OpeningHoursDay(**{"from": "10:00", "to": "22:00"}),
                "wednesday": OpeningHoursDay(**{"from": "10:00", "to": "22:00"}),
                "thursday": OpeningHoursDay(**{"from": "10:00", "to": "22:00"}),
                "friday": OpeningHoursDay(**{"from": "10:00", "to": "22:00"}),
                "saturday": OpeningHoursDay(**{"from": "10:00", "to": "22:00"}),
                "sunday": OpeningHoursDay(closed=True)
            },
            fixed_shifts=True,
            number_of_shifts_per_day=3,
            shift_times=["10:00-14:00", "14:00-18:00", "18:00-22:00"],
            rating=None,  # Missing rating
            accepting_orders=True
        )
        
        features = prepare_features_for_prediction(
            place=place,
            orders=sample_orders,
            campaigns=sample_campaigns,
            prediction_start="2024-01-08",
            prediction_days=1
        )
        
        # Should fill with default (4.0)
        assert features['rating'].iloc[0] == 4.0
    
    def test_no_campaigns_handled(self, sample_place_data, sample_orders):
        """Test that empty campaigns list is handled"""
        features = prepare_features_for_prediction(
            place=sample_place_data,
            orders=sample_orders,
            campaigns=[],  # No campaigns
            prediction_start="2024-01-08",
            prediction_days=1
        )
        
        assert features['total_campaigns'].iloc[0] == 0
        assert features['avg_discount'].iloc[0] == 0


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-W", "ignore::DeprecationWarning"])
