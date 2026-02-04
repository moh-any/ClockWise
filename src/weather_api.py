"""
Weather API module for fetching historical and forecast weather data.
Uses Open-Meteo API (free, no API key required).

Features:
- Historical weather data (from 1940 to present)
- Weather forecasts (up to 16 days ahead)
- Hourly granularity (matches our demand prediction data)
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, List, Tuple
import time


class WeatherAPI:
    """
    Fetches weather data from Open-Meteo API for demand prediction.
    
    Default location: Copenhagen, Denmark (55.6761, 12.5683)
    """
    
    HISTORICAL_URL = "https://archive-api.open-meteo.com/v1/archive"
    FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
    
    # Weather variables relevant for restaurant demand
    HOURLY_VARIABLES = [
        "temperature_2m",
        "relative_humidity_2m", 
        "precipitation",
        "rain",
        "snowfall",
        "weather_code",
        "cloud_cover",
        "wind_speed_10m"
    ]
    
    def __init__(self, latitude: float = 55.6761, longitude: float = 12.5683):
        """
        Initialize with location coordinates.
        
        Args:
            latitude: Default is Copenhagen (55.6761)
            longitude: Default is Copenhagen (12.5683)
        """
        self.latitude = latitude
        self.longitude = longitude
    
    def get_historical_weather(
        self, 
        start_date: str, 
        end_date: str,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        max_retries: int = 3
    ) -> pd.DataFrame:
        """
        Fetch historical weather data for a date range with retry logic.
        
        Args:
            start_date: Start date in 'YYYY-MM-DD' format
            end_date: End date in 'YYYY-MM-DD' format
            latitude: Optional override latitude
            longitude: Optional override longitude
            max_retries: Maximum number of retry attempts
            
        Returns:
            DataFrame with hourly weather data
        """
        params = {
            "latitude": latitude or self.latitude,
            "longitude": longitude or self.longitude,
            "start_date": start_date,
            "end_date": end_date,
            "hourly": ",".join(self.HOURLY_VARIABLES),
            "timezone": "Europe/Copenhagen"
        }
        
        for attempt in range(max_retries):
            try:
                response = requests.get(self.HISTORICAL_URL, params=params, timeout=30)
                
                if response.status_code != 200:
                    raise Exception(f"API Error: {response.status_code} - {response.text}")
                
                data = response.json()
                
                # Convert to DataFrame
                df = pd.DataFrame(data["hourly"])
                df["time"] = pd.to_datetime(df["time"])
                df["date"] = df["time"].dt.date
                df["hour"] = df["time"].dt.hour
                
                return df
            
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2  # Exponential backoff
                    print(f"Connection error, retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                else:
                    print(f"Failed after {max_retries} attempts: {e}")
                    raise
    
    def get_forecast_weather(
        self,
        days: int = 7,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        max_retries: int = 3
    ) -> pd.DataFrame:
        """
        Fetch weather forecast for upcoming days with retry logic.
        
        Args:
            days: Number of days to forecast (max 16)
            latitude: Optional override latitude
            longitude: Optional override longitude
            max_retries: Maximum number of retry attempts
            
        Returns:
            DataFrame with hourly forecast data
        """
        params = {
            "latitude": latitude or self.latitude,
            "longitude": longitude or self.longitude,
            "hourly": ",".join(self.HOURLY_VARIABLES),
            "timezone": "Europe/Copenhagen",
            "forecast_days": min(days, 16)
        }
        
        for attempt in range(max_retries):
            try:
                response = requests.get(self.FORECAST_URL, params=params, timeout=30)
                
                if response.status_code != 200:
                    raise Exception(f"API Error: {response.status_code} - {response.text}")
                
                data = response.json()
                
                # Convert to DataFrame
                df = pd.DataFrame(data["hourly"])
                df["time"] = pd.to_datetime(df["time"])
                df["date"] = df["time"].dt.date
                df["hour"] = df["time"].dt.hour
                
                return df
            
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2
                    print(f"Connection error, retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                else:
                    print(f"Failed after {max_retries} attempts: {e}")
                    raise
    
    def get_weather_for_dates(
        self,
        dates: List[str],
        latitude: Optional[float] = None,
        longitude: Optional[float] = None
    ) -> pd.DataFrame:
        """
        Fetch weather for specific dates (auto-detects historical vs forecast).
        
        Args:
            dates: List of dates in 'YYYY-MM-DD' format
            latitude: Optional override latitude
            longitude: Optional override longitude
            
        Returns:
            DataFrame with hourly weather for all requested dates
        """
        today = datetime.now().date()
        
        # Separate historical and future dates
        historical_dates = [d for d in dates if datetime.strptime(d, "%Y-%m-%d").date() < today]
        future_dates = [d for d in dates if datetime.strptime(d, "%Y-%m-%d").date() >= today]
        
        dfs = []
        
        # Fetch historical data
        if historical_dates:
            start = min(historical_dates)
            end = max(historical_dates)
            hist_df = self.get_historical_weather(start, end, latitude, longitude)
            hist_df = hist_df[hist_df["date"].astype(str).isin(historical_dates)]
            dfs.append(hist_df)
        
        # Fetch forecast data
        if future_dates:
            forecast_df = self.get_forecast_weather(16, latitude, longitude)
            forecast_df = forecast_df[forecast_df["date"].astype(str).isin(future_dates)]
            dfs.append(forecast_df)
        
        if dfs:
            return pd.concat(dfs, ignore_index=True)
        return pd.DataFrame()
    
    def add_weather_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add derived weather features useful for demand prediction.
        
        Args:
            df: DataFrame with weather data
            
        Returns:
            DataFrame with additional weather features
        """
        df = df.copy()
        
        # Weather condition flags
        df["is_rainy"] = (df["precipitation"] > 0.5).astype(int)
        df["is_snowy"] = (df["snowfall"] > 0).astype(int)
        df["is_cold"] = (df["temperature_2m"] < 5).astype(int)
        df["is_hot"] = (df["temperature_2m"] > 25).astype(int)
        df["is_cloudy"] = (df["cloud_cover"] > 70).astype(int)
        df["is_windy"] = (df["wind_speed_10m"] > 30).astype(int)
        
        # Good weather for outdoor dining
        df["good_weather"] = (
            (df["temperature_2m"].between(15, 28)) &
            (df["precipitation"] < 0.5) &
            (df["wind_speed_10m"] < 25)
        ).astype(int)
        
        # Weather severity score (higher = worse conditions)
        df["weather_severity"] = (
            df["is_rainy"] * 2 +
            df["is_snowy"] * 3 +
            df["is_cold"] * 1 +
            df["is_windy"] * 1
        )
        
        return df
    
    @staticmethod
    def decode_weather_code(code: int) -> str:
        """
        Decode WMO weather code to human-readable description.
        
        Args:
            code: WMO weather code
            
        Returns:
            Weather description string
        """
        weather_codes = {
            0: "Clear sky",
            1: "Mainly clear",
            2: "Partly cloudy",
            3: "Overcast",
            45: "Fog",
            48: "Depositing rime fog",
            51: "Light drizzle",
            53: "Moderate drizzle",
            55: "Dense drizzle",
            61: "Slight rain",
            63: "Moderate rain",
            65: "Heavy rain",
            71: "Slight snow",
            73: "Moderate snow",
            75: "Heavy snow",
            80: "Slight rain showers",
            81: "Moderate rain showers",
            82: "Violent rain showers",
            95: "Thunderstorm",
            96: "Thunderstorm with hail",
        }
        return weather_codes.get(code, f"Unknown ({code})")


def get_weather_for_demand_data(
    demand_df: pd.DataFrame,
    date_col: str = "date",
    hour_col: str = "hour",
    place_col: str = "place_id",
    lat_col: str = "latitude", 
    lon_col: str = "longitude",
    default_latitude: float = 55.6761,  # Copenhagen default
    default_longitude: float = 12.5683
) -> pd.DataFrame:
    """
    Fetch and merge weather data with demand prediction dataset.
    
    Args:
        demand_df: DataFrame with demand data
        date_col: Name of date column
        hour_col: Name of hour column
        place_col: Name of place ID column
        lat_col: Name of latitude column
        lon_col: Name of longitude column
        default_latitude: Default latitude for missing coordinates (default: Copenhagen)
        default_longitude: Default longitude for missing coordinates (default: Copenhagen)
        
    Returns:
        DataFrame with weather features merged
    """
    
    # Fill NaN coordinates with defaults BEFORE grouping
    demand_df = demand_df.copy()
    demand_df[lat_col] = demand_df[lat_col].fillna(default_latitude)
    demand_df[lon_col] = demand_df[lon_col].fillna(default_longitude)
    
    # Now group by filled coordinates
    location_groups = demand_df.groupby([place_col, lat_col, lon_col])[date_col].apply(
        lambda x: x.astype(str).unique().tolist()
    ).reset_index()
    
    all_weather = []
    default_api = WeatherAPI(latitude=default_latitude, longitude=default_longitude)
    
    print(f"Fetching weather data for {len(location_groups)} location groups...")
    
    for idx, row in location_groups.iterrows():
        place_id = row[place_col]
        lat = row[lat_col]
        lon = row[lon_col]
        dates = row[date_col]
        
        try:
            # Use specific location or fallback to default
            if pd.notna(lat) and pd.notna(lon):
                api = WeatherAPI(latitude=lat, longitude=lon)
            else:
                api = default_api  # Use Copenhagen for missing coordinates
            
            weather = api.get_weather_for_dates(dates)
            weather[place_col] = place_id
            all_weather.append(weather)
            
            # Small delay to avoid rate limiting
            if idx < len(location_groups) - 1:
                time.sleep(0.5)
                
            if (idx + 1) % 10 == 0:
                print(f"  Processed {idx + 1}/{len(location_groups)} locations")
        
        except Exception as e:
            print(f"  Warning: Failed to fetch weather for place {place_id}: {e}")
            # Continue with other locations instead of failing completely
            continue
    
    if all_weather:
        weather_df = pd.concat(all_weather, ignore_index=True)
        
        # Add weather features
        api = WeatherAPI()
        weather_df = api.add_weather_features(weather_df)
        
        # Merge with demand data
        demand_df[date_col] = pd.to_datetime(demand_df[date_col]).dt.date
        weather_df["date"] = pd.to_datetime(weather_df["date"]).dt.date
        
        merged_df = demand_df.merge(
            weather_df,
            left_on=[place_col, date_col, hour_col],
            right_on=[place_col, "date", "hour"],
            how="left"
        )
        
        # Drop duplicate date/hour columns if they exist
        if "date_y" in merged_df.columns:
            merged_df = merged_df.drop(columns=["date_y"])
        if "date_x" in merged_df.columns:
            merged_df = merged_df.rename(columns={"date_x": date_col})
        
        return merged_df
    
    return demand_df
