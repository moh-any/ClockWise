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
        longitude: Optional[float] = None
    ) -> pd.DataFrame:
        """
        Fetch historical weather data for a date range.
        
        Args:
            start_date: Start date in 'YYYY-MM-DD' format
            end_date: End date in 'YYYY-MM-DD' format
            latitude: Optional override latitude
            longitude: Optional override longitude
            
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
        
        response = requests.get(self.HISTORICAL_URL, params=params)
        
        if response.status_code != 200:
            raise Exception(f"API Error: {response.status_code} - {response.text}")
        
        data = response.json()
        
        # Convert to DataFrame
        df = pd.DataFrame(data["hourly"])
        df["time"] = pd.to_datetime(df["time"])
        df["date"] = df["time"].dt.date
        df["hour"] = df["time"].dt.hour
        
        return df
    
    def get_forecast_weather(
        self,
        days: int = 7,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None
    ) -> pd.DataFrame:
        """
        Fetch weather forecast for upcoming days.
        
        Args:
            days: Number of days to forecast (max 16)
            latitude: Optional override latitude
            longitude: Optional override longitude
            
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
        
        response = requests.get(self.FORECAST_URL, params=params)
        
        if response.status_code != 200:
            raise Exception(f"API Error: {response.status_code} - {response.text}")
        
        data = response.json()
        
        # Convert to DataFrame
        df = pd.DataFrame(data["hourly"])
        df["time"] = pd.to_datetime(df["time"])
        df["date"] = df["time"].dt.date
        df["hour"] = df["time"].dt.hour
        
        return df
    
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
    hour_col: str = "hour"
) -> pd.DataFrame:
    """
    Fetch and merge weather data with demand prediction dataset.
    
    Args:
        demand_df: DataFrame with demand data (must have date and hour columns)
        date_col: Name of date column
        hour_col: Name of hour column
        
    Returns:
        DataFrame with weather features merged
    """
    api = WeatherAPI()
    
    # Get unique dates from demand data
    dates = demand_df[date_col].astype(str).unique().tolist()
    
    # Fetch weather for all dates
    print(f"Fetching weather for {len(dates)} unique dates...")
    weather_df = api.get_weather_for_dates(dates)
    
    # Add derived features
    weather_df = api.add_weather_features(weather_df)
    
    # Prepare for merge
    weather_df["date"] = weather_df["date"].astype(str)
    demand_df[date_col] = demand_df[date_col].astype(str)
    
    # Merge on date and hour
    merged = demand_df.merge(
        weather_df.drop(columns=["time"]),
        left_on=[date_col, hour_col],
        right_on=["date", "hour"],
        how="left"
    )
    
    print(f"Merged weather data: {len(weather_df)} weather records → {len(merged)} demand records")
    
    return merged
