"""
Holiday API Module
==================
Determine if a date is a holiday based on geographic location (latitude/longitude).
"""

import requests
from datetime import datetime, date
from typing import Optional, Dict, List
import holidays
import pandas as pd

class HolidayChecker:
    """Check if a date is a holiday based on geographic coordinates."""
    
    def __init__(self):
        """Initialize the holiday checker."""
        self.country_cache = {}
        
    def get_country_from_coords(self, latitude: float, longitude: float) -> Optional[str]:
        """
        Get country code from latitude and longitude using reverse geocoding.
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            
        Returns:
            ISO 3166-1 alpha-2 country code (e.g., 'DK', 'US', 'GB') or None
        """
        # Check cache first
        cache_key = f"{latitude:.2f},{longitude:.2f}"
        if cache_key in self.country_cache:
            return self.country_cache[cache_key]
        
        try:
            # Using Nominatim (OpenStreetMap) reverse geocoding - free, no API key needed
            url = "https://nominatim.openstreetmap.org/reverse"
            params = {
                'lat': latitude,
                'lon': longitude,
                'format': 'json',
                'zoom': 3  # Country level
            }
            headers = {
                'User-Agent': 'HolidayChecker/1.0'
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            country_code = data.get('address', {}).get('country_code', '').upper()
            
            # Cache the result
            self.country_cache[cache_key] = country_code if country_code else None
            
            return country_code if country_code else None
            
        except Exception as e:
            print(f"Error getting country from coordinates: {e}")
            return None
    
    def is_holiday(self, check_date: date, latitude: float, longitude: float, 
                   country_code: Optional[str] = None) -> Dict[str, any]:
        """
        Check if a date is a holiday at a given location.
        
        Args:
            check_date: Date to check
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            country_code: Optional country code (if known, skips geocoding)
            
        Returns:
            Dictionary with:
                - is_holiday: bool
                - holiday_name: str or None
                - country: str (country code)
        """
        # Get country code if not provided
        if country_code is None:
            country_code = self.get_country_from_coords(latitude, longitude)
            
        if country_code is None:
            return {
                'is_holiday': False,
                'holiday_name': None,
                'country': None,
                'error': 'Could not determine country from coordinates'
            }
        
        try:
            # Get holidays for the country
            country_holidays = holidays.country_holidays(country_code)
            
            # Check if date is a holiday
            if check_date in country_holidays:
                return {
                    'is_holiday': True,
                    'holiday_name': country_holidays.get(check_date),
                    'country': country_code
                }
            else:
                return {
                    'is_holiday': False,
                    'holiday_name': None,
                    'country': country_code
                }
                
        except Exception as e:
            return {
                'is_holiday': False,
                'holiday_name': None,
                'country': country_code,
                'error': f'Error checking holidays: {e}'
            }

def add_holiday_feature(df: pd.DataFrame, 
                    date_column: str = 'datetime',
                    latitude_column: str = 'latitude',
                    longitude_column: str = 'longitude',
                    default_latitude: float = 55.6761,
                    default_longitude: float = 12.5683) -> pd.DataFrame:
    """
    Add is_holiday column to a DataFrame based on date and location.
    
    ===== FIX: Batch API calls by unique (date, lat, lon) combinations =====
    
    Args:
        df: DataFrame with date, latitude, and longitude columns
        date_column: Name of the date column
        latitude_column: Name of the latitude column
        longitude_column: Name of the longitude column
        default_latitude: Default latitude for NaN values (Copenhagen)
        default_longitude: Default longitude for NaN values (Copenhagen)
        
    Returns:
        DataFrame with added 'is_holiday' boolean column
    """
    # Create a copy to avoid modifying original
    result_df = df.copy()
    
    # Fill NaN lat/lon with defaults
    result_df[latitude_column] = result_df[latitude_column].fillna(default_latitude)
    result_df[longitude_column] = result_df[longitude_column].fillna(default_longitude)
    
    # Convert date column to date if needed
    if not pd.api.types.is_datetime64_any_dtype(result_df[date_column]):
        result_df['_date_for_holiday'] = pd.to_datetime(result_df[date_column]).dt.date
    else:
        result_df['_date_for_holiday'] = result_df[date_column].dt.date
    
    # Initialize checker
    checker = HolidayChecker()
    
    # ===== FIX: Get unique combinations and batch lookup =====
    unique_combos = result_df[['_date_for_holiday', latitude_column, longitude_column]].drop_duplicates()
    
    print(f"Checking holidays for {len(unique_combos)} unique (date, location) combinations...")
    
    holiday_lookup = {}
    for idx, row in unique_combos.iterrows():
        check_date = row['_date_for_holiday']
        lat = row[latitude_column]
        lon = row[longitude_column]
        
        result = checker.is_holiday(check_date, lat, lon)
        holiday_lookup[(check_date, lat, lon)] = result.get('is_holiday', False)
        
        if (idx + 1) % 100 == 0:
            print(f"  Processed {idx + 1}/{len(unique_combos)} combinations")
    
    # Map back to full dataframe
    result_df['is_holiday'] = result_df.apply(
        lambda row: holiday_lookup.get(
            (row['_date_for_holiday'], row[latitude_column], row[longitude_column]), 
            False
        ),
        axis=1
    )
    
    # Clean up temporary column
    result_df = result_df.drop(columns=['_date_for_holiday'])
    
    print(f"Found {result_df['is_holiday'].sum()} holiday records out of {len(result_df)} total")
    
    return result_df