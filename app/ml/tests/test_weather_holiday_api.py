"""
Comprehensive tests for Weather and Holiday API modules

Tests cover:
1. WeatherAPI - Historical weather, forecasts, derived features
2. HolidayChecker - Holiday detection, country lookup
3. Integration - Data enrichment with weather and holidays

Note: External API calls are mocked to avoid network dependencies.

Usage:
    pytest tests/test_weather_holiday_api.py -v
    pytest tests/test_weather_holiday_api.py::TestWeatherAPI -v
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.weather_api import WeatherAPI
from src.holiday_api import HolidayChecker, add_holiday_feature


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def weather_api():
    """Create WeatherAPI instance with default Copenhagen coordinates."""
    return WeatherAPI()


@pytest.fixture
def holiday_checker():
    """Create HolidayChecker instance."""
    return HolidayChecker()


@pytest.fixture
def mock_weather_response():
    """Create mock weather API response."""
    return {
        "hourly": {
            "time": [f"2026-01-{d+1:02d}T{h:02d}:00" for d in range(2) for h in range(24)],
            "temperature_2m": [10.0 + np.random.uniform(-5, 5) for _ in range(48)],
            "relative_humidity_2m": [70.0 + np.random.uniform(-20, 20) for _ in range(48)],
            "precipitation": [np.random.uniform(0, 2) for _ in range(48)],
            "rain": [np.random.uniform(0, 2) for _ in range(48)],
            "snowfall": [np.random.uniform(0, 1) for _ in range(48)],
            "weather_code": [np.random.randint(0, 100) for _ in range(48)],
            "cloud_cover": [np.random.uniform(0, 100) for _ in range(48)],
            "wind_speed_10m": [np.random.uniform(0, 30) for _ in range(48)]
        }
    }


@pytest.fixture
def sample_df_for_holidays():
    """Create sample DataFrame for holiday testing."""
    return pd.DataFrame({
        'datetime': pd.date_range('2026-12-24', periods=10, freq='D'),
        'latitude': [55.6761] * 10,
        'longitude': [12.5683] * 10,
        'value': range(10)
    })


# =============================================================================
# TEST WEATHER API
# =============================================================================

class TestWeatherAPI:
    """Test WeatherAPI class."""
    
    def test_api_initialization(self, weather_api):
        """Test API initializes with correct defaults."""
        assert weather_api.latitude == 55.6761
        assert weather_api.longitude == 12.5683
    
    def test_api_custom_coordinates(self):
        """Test API with custom coordinates."""
        api = WeatherAPI(latitude=40.7128, longitude=-74.0060)
        
        assert api.latitude == 40.7128
        assert api.longitude == -74.0060
    
    def test_hourly_variables_defined(self, weather_api):
        """Test hourly variables are defined."""
        assert len(weather_api.HOURLY_VARIABLES) > 0
        assert 'temperature_2m' in weather_api.HOURLY_VARIABLES
        assert 'precipitation' in weather_api.HOURLY_VARIABLES
    
    @patch('src.weather_api.requests.get')
    def test_get_historical_weather_success(self, mock_get, weather_api, mock_weather_response):
        """Test successful historical weather fetch."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_weather_response
        mock_get.return_value = mock_response
        
        result = weather_api.get_historical_weather('2026-01-01', '2026-01-02')
        
        assert isinstance(result, pd.DataFrame)
        assert 'temperature_2m' in result.columns
        assert 'time' in result.columns
        assert len(result) == 48  # 2 days * 24 hours
    
    @patch('src.weather_api.requests.get')
    def test_get_historical_weather_has_date_hour(self, mock_get, weather_api, mock_weather_response):
        """Test historical weather includes date and hour columns."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_weather_response
        mock_get.return_value = mock_response
        
        result = weather_api.get_historical_weather('2026-01-01', '2026-01-02')
        
        assert 'date' in result.columns
        assert 'hour' in result.columns
    
    @patch('src.weather_api.requests.get')
    def test_get_forecast_weather_success(self, mock_get, weather_api, mock_weather_response):
        """Test successful forecast fetch."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_weather_response
        mock_get.return_value = mock_response
        
        result = weather_api.get_forecast_weather(days=2)
        
        assert isinstance(result, pd.DataFrame)
        assert 'temperature_2m' in result.columns
    
    @patch('src.weather_api.requests.get')
    def test_get_forecast_max_days(self, mock_get, weather_api, mock_weather_response):
        """Test forecast respects max 16 days limit."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_weather_response
        mock_get.return_value = mock_response
        
        # Request more than 16 days
        weather_api.get_forecast_weather(days=20)
        
        # Verify params use min(days, 16)
        call_args = mock_get.call_args
        assert call_args[1]['params']['forecast_days'] <= 16
    
    @patch('src.weather_api.requests.get')
    def test_api_error_handling(self, mock_get, weather_api):
        """Test API handles HTTP errors."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_get.return_value = mock_response
        
        with pytest.raises(Exception) as exc_info:
            weather_api.get_historical_weather('2026-01-01', '2026-01-02')
        
        assert "API Error" in str(exc_info.value)
    
    @patch('src.weather_api.requests.get')
    def test_retry_on_connection_error(self, mock_get, weather_api, mock_weather_response):
        """Test retry logic on connection errors."""
        import requests
        
        # First two calls fail, third succeeds
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_weather_response
        
        mock_get.side_effect = [
            requests.exceptions.ConnectionError("Connection failed"),
            requests.exceptions.ConnectionError("Connection failed"),
            mock_response
        ]
        
        result = weather_api.get_historical_weather('2026-01-01', '2026-01-02')
        
        assert isinstance(result, pd.DataFrame)
        assert mock_get.call_count == 3
    
    @patch('src.weather_api.requests.get')
    def test_custom_coordinates_in_request(self, mock_get, mock_weather_response):
        """Test custom coordinates are used in API request."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_weather_response
        mock_get.return_value = mock_response
        
        api = WeatherAPI(latitude=40.0, longitude=-70.0)
        api.get_historical_weather('2026-01-01', '2026-01-02')
        
        call_args = mock_get.call_args
        assert call_args[1]['params']['latitude'] == 40.0
        assert call_args[1]['params']['longitude'] == -70.0


# =============================================================================
# TEST HOLIDAY CHECKER
# =============================================================================

class TestHolidayChecker:
    """Test HolidayChecker class."""
    
    def test_checker_initialization(self, holiday_checker):
        """Test checker initializes with empty cache."""
        assert holiday_checker.country_cache == {}
    
    @patch('src.holiday_api.requests.get')
    def test_get_country_from_coords_success(self, mock_get, holiday_checker):
        """Test successful country lookup."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'address': {'country_code': 'dk'}
        }
        mock_get.return_value = mock_response
        
        result = holiday_checker.get_country_from_coords(55.6761, 12.5683)
        
        assert result == 'DK'
    
    @patch('src.holiday_api.requests.get')
    def test_country_cache(self, mock_get, holiday_checker):
        """Test country lookup uses cache."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'address': {'country_code': 'dk'}
        }
        mock_get.return_value = mock_response
        
        # First call
        result1 = holiday_checker.get_country_from_coords(55.6761, 12.5683)
        # Second call (should use cache)
        result2 = holiday_checker.get_country_from_coords(55.6761, 12.5683)
        
        assert result1 == result2
        assert mock_get.call_count == 1  # Only called once
    
    @patch('src.holiday_api.requests.get')
    def test_is_holiday_christmas_dk(self, mock_get, holiday_checker):
        """Test Christmas is detected as holiday in Denmark."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'address': {'country_code': 'dk'}
        }
        mock_get.return_value = mock_response
        
        christmas = date(2026, 12, 25)
        result = holiday_checker.is_holiday(christmas, 55.6761, 12.5683)
        
        assert result['is_holiday'] is True
        assert result['country'] == 'DK'
    
    @patch('src.holiday_api.requests.get')
    def test_is_holiday_regular_day(self, mock_get, holiday_checker):
        """Test regular day is not detected as holiday."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'address': {'country_code': 'dk'}
        }
        mock_get.return_value = mock_response
        
        regular_day = date(2026, 3, 15)  # A random day
        result = holiday_checker.is_holiday(regular_day, 55.6761, 12.5683)
        
        assert result['is_holiday'] is False
    
    def test_is_holiday_with_country_code(self, holiday_checker):
        """Test holiday check with provided country code (no geocoding)."""
        christmas = date(2026, 12, 25)
        
        # Provide country code directly
        result = holiday_checker.is_holiday(christmas, 55.6761, 12.5683, country_code='DK')
        
        assert result['is_holiday'] is True
        assert result['country'] == 'DK'
    
    def test_us_independence_day(self, holiday_checker):
        """Test US Independence Day detection."""
        july_4th = date(2026, 7, 4)
        
        result = holiday_checker.is_holiday(july_4th, 40.7128, -74.0060, country_code='US')
        
        assert result['is_holiday'] is True
        assert 'Independence' in result['holiday_name']
    
    def test_holiday_name_returned(self, holiday_checker):
        """Test holiday name is returned."""
        christmas = date(2026, 12, 25)
        
        result = holiday_checker.is_holiday(christmas, 55.6761, 12.5683, country_code='DK')
        
        assert result['holiday_name'] is not None
    
    @patch('src.holiday_api.requests.get')
    def test_handles_geocoding_error(self, mock_get, holiday_checker):
        """Test handling of geocoding errors."""
        mock_get.side_effect = Exception("Network error")
        
        result = holiday_checker.get_country_from_coords(55.6761, 12.5683)
        
        assert result is None


# =============================================================================
# TEST ADD HOLIDAY FEATURE
# =============================================================================

class TestAddHolidayFeature:
    """Test add_holiday_feature function."""
    
    @patch.object(HolidayChecker, 'is_holiday')
    def test_add_holiday_column(self, mock_is_holiday, sample_df_for_holidays):
        """Test adding is_holiday column to DataFrame."""
        # Mock holiday response
        mock_is_holiday.return_value = {'is_holiday': True, 'country': 'DK'}
        
        result = add_holiday_feature(sample_df_for_holidays)
        
        assert 'is_holiday' in result.columns
    
    @patch.object(HolidayChecker, 'is_holiday')
    def test_preserves_original_columns(self, mock_is_holiday, sample_df_for_holidays):
        """Test original columns are preserved."""
        mock_is_holiday.return_value = {'is_holiday': False, 'country': 'DK'}
        
        original_cols = list(sample_df_for_holidays.columns)
        result = add_holiday_feature(sample_df_for_holidays)
        
        for col in original_cols:
            assert col in result.columns
    
    @patch.object(HolidayChecker, 'is_holiday')
    def test_handles_nan_coordinates(self, mock_is_holiday):
        """Test handling of NaN coordinates (uses defaults)."""
        mock_is_holiday.return_value = {'is_holiday': False, 'country': 'DK'}
        
        df = pd.DataFrame({
            'datetime': pd.date_range('2026-01-01', periods=3, freq='D'),
            'latitude': [np.nan, 55.0, np.nan],
            'longitude': [np.nan, 12.0, np.nan],
            'value': [1, 2, 3]
        })
        
        result = add_holiday_feature(df)
        
        # Should not crash and fill with defaults
        assert len(result) == 3
        assert 'is_holiday' in result.columns
    
    @patch.object(HolidayChecker, 'is_holiday')
    def test_holiday_detection_batch(self, mock_is_holiday, sample_df_for_holidays):
        """Test holiday detection is batched for unique combinations."""
        mock_is_holiday.return_value = {'is_holiday': True, 'country': 'DK'}
        
        # All rows have same location, so should batch
        add_holiday_feature(sample_df_for_holidays)
        
        # Should only call is_holiday for unique (date, lat, lon) combinations
        # All rows have same lat/lon, but different dates
        assert mock_is_holiday.call_count == 10  # 10 unique dates


# =============================================================================
# TEST WEATHER DERIVED FEATURES
# =============================================================================

class TestWeatherDerivedFeatures:
    """Test derived weather features."""
    
    @patch('src.weather_api.requests.get')
    def test_weather_dataframe_types(self, mock_get, weather_api, mock_weather_response):
        """Test weather DataFrame has correct data types."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_weather_response
        mock_get.return_value = mock_response
        
        result = weather_api.get_historical_weather('2026-01-01', '2026-01-02')
        
        assert pd.api.types.is_datetime64_any_dtype(result['time'])
        assert pd.api.types.is_numeric_dtype(result['temperature_2m'])
    
    @patch('src.weather_api.requests.get')
    def test_hour_extraction(self, mock_get, weather_api, mock_weather_response):
        """Test hour is correctly extracted from time."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_weather_response
        mock_get.return_value = mock_response
        
        result = weather_api.get_historical_weather('2026-01-01', '2026-01-02')
        
        # Hour should be in 0-23 range
        assert result['hour'].min() >= 0
        assert result['hour'].max() <= 23


# =============================================================================
# EDGE CASES
# =============================================================================

class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_holiday_checker_unknown_country(self, holiday_checker):
        """Test holiday check with unknown country code."""
        # Use an invalid country code
        result = holiday_checker.is_holiday(
            date(2026, 1, 1), 0.0, 0.0, country_code='XX'
        )
        
        # Should handle gracefully
        assert 'error' in result or result['is_holiday'] is False
    
    @patch('src.weather_api.requests.get')
    def test_weather_empty_response(self, mock_get, weather_api):
        """Test handling of empty weather response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"hourly": {}}
        mock_get.return_value = mock_response
        
        # Should handle empty data gracefully
        try:
            result = weather_api.get_historical_weather('2026-01-01', '2026-01-02')
            assert len(result) == 0
        except (KeyError, ValueError):
            pass  # Expected if required columns missing
    
    def test_holiday_leap_year(self, holiday_checker):
        """Test holiday detection on leap year date."""
        leap_date = date(2028, 2, 29)  # 2028 is a leap year
        
        result = holiday_checker.is_holiday(
            leap_date, 55.6761, 12.5683, country_code='DK'
        )
        
        # Should not crash
        assert 'is_holiday' in result
    
    @patch.object(HolidayChecker, 'is_holiday')
    def test_add_holiday_single_row(self, mock_is_holiday):
        """Test add_holiday_feature with single row."""
        mock_is_holiday.return_value = {'is_holiday': True, 'country': 'DK'}
        
        df = pd.DataFrame({
            'datetime': [datetime(2026, 12, 25)],
            'latitude': [55.6761],
            'longitude': [12.5683]
        })
        
        result = add_holiday_feature(df)
        
        assert len(result) == 1
        assert result['is_holiday'].values[0] == True  # Use == for numpy bool


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestIntegration:
    """Integration tests for weather and holiday APIs."""
    
    @patch('src.weather_api.requests.get')
    def test_weather_and_holiday_enrichment(self, mock_get, mock_weather_response):
        """Test enriching data with both weather and holidays."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_weather_response
        mock_get.return_value = mock_response
        
        # Get weather
        api = WeatherAPI()
        weather_df = api.get_historical_weather('2026-01-01', '2026-01-02')
        
        # Add location for holidays
        weather_df['latitude'] = 55.6761
        weather_df['longitude'] = 12.5683
        weather_df['datetime'] = weather_df['time']
        
        # Check holidays (with known country to avoid geocoding)
        checker = HolidayChecker()
        
        # January 1st should be a holiday in many countries
        jan_1_result = checker.is_holiday(date(2026, 1, 1), 55.6761, 12.5683, country_code='DK')
        
        assert jan_1_result['is_holiday'] is True
    
    @patch('src.weather_api.requests.get')  
    def test_concurrent_weather_requests(self, mock_get, mock_weather_response):
        """Test multiple weather API requests."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_weather_response
        mock_get.return_value = mock_response
        
        api = WeatherAPI()
        
        # Multiple requests
        result1 = api.get_historical_weather('2026-01-01', '2026-01-02')
        result2 = api.get_historical_weather('2026-01-03', '2026-01-04')
        
        assert len(result1) > 0
        assert len(result2) > 0
