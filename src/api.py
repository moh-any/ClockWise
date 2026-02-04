"""
Restaurant Demand Prediction API
=================================
FastAPI-based REST API for predicting hourly restaurant demand.
Accepts restaurant, order, and campaign data, returns predictions for item_count and order_count.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, date, timedelta
import pandas as pd
import numpy as np
import joblib
from pathlib import Path
import logging

# Configure logging FIRST
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import weather API from src folder
try:
    from src.weather_api import WeatherAPI, get_weather_for_demand_data
    WEATHER_API_AVAILABLE = True
    logger.info("Weather API imported successfully")
except ImportError as e:
    WEATHER_API_AVAILABLE = False
    logger.warning(f"Weather API not available: {e}. Will use mock weather data.")

# Initialize FastAPI app
app = FastAPI(
    title="Restaurant Demand Prediction API",
    description="Predict hourly item_count and order_count for restaurants",
    version="1.0.0"
)

# ============================================================================
# REQUEST MODELS
# ============================================================================

class PlaceData(BaseModel):
    """Restaurant/Place information"""
    name: str = Field(..., description="Restaurant name")
    lat: float = Field(..., description="Latitude coordinate")
    long: float = Field(..., description="Longitude coordinate")
    waiting_time: Optional[int] = Field(None, description="Average waiting time in minutes")
    receiving_phone: bool = Field(..., description="Accepts phone orders")
    delivery: bool = Field(..., description="Offers delivery")
    opening_hours: str = Field(..., description="Opening hours (e.g., '10:00-22:00')")
    shift_duration: int = Field(..., description="Shift duration in hours")
    type_id: Optional[int] = Field(None, description="Restaurant type ID")
    rating: Optional[float] = Field(None, description="Restaurant rating (0-5)")
    accepting_orders: Optional[bool] = Field(True, description="Currently accepting orders")

class OrderData(BaseModel):
    """Historical order information"""
    time: str = Field(..., description="Order timestamp (ISO format)")
    items: int = Field(..., description="Number of items in order")
    status: str = Field(..., description="Order status: completed/canceled")
    total_amount: float = Field(..., description="Total order amount")
    discount_amount: float = Field(0, description="Discount applied")

class CampaignData(BaseModel):
    """Marketing campaign information"""
    start_time: str = Field(..., description="Campaign start time (ISO format)")
    end_time: str = Field(..., description="Campaign end time (ISO format)")
    items_included: List[str] = Field(..., description="Items included in campaign")
    discount: float = Field(..., description="Discount percentage (0-100)")

class PredictionRequest(BaseModel):
    """Complete prediction request"""
    place: PlaceData
    orders: List[OrderData] = Field(..., description="Historical orders (at least 7 days recommended)")
    campaigns: List[CampaignData] = Field(default=[], description="Active/past campaigns")
    prediction_start_date: str = Field(..., description="Start date for predictions (YYYY-MM-DD)")
    prediction_days: int = Field(7, description="Number of days to predict (default: 7)")

# ============================================================================
# RESPONSE MODELS
# ============================================================================

class HourPrediction(BaseModel):
    """Prediction for a single hour"""
    hour: int = Field(..., description="Hour of day (0-23)")
    order_count: int = Field(..., description="Predicted number of orders")
    item_count: int = Field(..., description="Predicted number of items")

class DayPrediction(BaseModel):
    """Predictions for a single day"""
    day_name: str = Field(..., description="Day name (mon, tue, wed, etc.)")
    date: str = Field(..., description="Date (YYYY-MM-DD)")
    hours: List[HourPrediction] = Field(..., description="Hourly predictions")

class PredictionResponse(BaseModel):
    """Complete prediction response"""
    restaurant_name: str
    prediction_period: str
    days: List[DayPrediction]

# ============================================================================
# MODEL LOADING
# ============================================================================

MODEL_PATH = Path("data/models/rf_model.joblib")
METADATA_PATH = Path("data/models/rf_model_metadata.json")

try:
    model = joblib.load(MODEL_PATH)
    metadata = joblib.load(METADATA_PATH)
    logger.info("Model loaded successfully")
except Exception as e:
    logger.error(f"Failed to load model: {e}")
    model = None
    metadata = None

# ============================================================================
# FEATURE ENGINEERING FUNCTIONS
# ============================================================================

def process_historical_orders(orders: List[OrderData], place_id: int = 1) -> pd.DataFrame:
    """Convert order data to DataFrame with temporal features"""
    if not orders:
        raise ValueError("At least some historical orders are required")
    
    order_dicts = []
    for order in orders:
        order_dicts.append({
            'created': pd.to_datetime(order.time).timestamp(),
            'place_id': place_id,
            'total_amount': order.total_amount,
            'item_count': order.items,
            'status': order.status
        })
    
    df = pd.DataFrame(order_dicts)
    
    # Add datetime features
    df['created_dt'] = pd.to_datetime(df['created'], unit='s')
    df['date'] = df['created_dt'].dt.date
    df['hour'] = df['created_dt'].dt.hour
    
    return df

def aggregate_to_hourly(orders_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate orders to hourly level"""
    hourly = orders_df.groupby(['place_id', 'date', 'hour']).agg(
        item_count=('item_count', 'sum'),
        order_count=('created', 'count'),
        total_revenue=('total_amount', 'sum')
    ).reset_index()
    
    hourly['datetime'] = pd.to_datetime(hourly['date'].astype(str)) + \
                         pd.to_timedelta(hourly['hour'], unit='h')
    
    return hourly

def add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add temporal features"""
    df = df.copy()
    df['day_of_week'] = df['datetime'].dt.dayofweek
    df['month'] = df['datetime'].dt.month
    df['week_of_year'] = df['datetime'].dt.isocalendar().week
    return df

def add_lag_features(df: pd.DataFrame, target_col: str = 'item_count') -> pd.DataFrame:
    """Add lag and rolling features"""
    df = df.copy()
    df = df.sort_values(['place_id', 'datetime'])
    
    df['prev_hour_items'] = df.groupby('place_id')[target_col].shift(1)
    df['prev_day_items'] = df.groupby('place_id')[target_col].shift(24)
    df['prev_week_items'] = df.groupby('place_id')[target_col].shift(168)
    df['prev_month_items'] = df.groupby('place_id')[target_col].shift(720)
    
    df['rolling_7d_avg_items'] = df.groupby('place_id')[target_col].transform(
        lambda x: x.rolling(window=168, min_periods=1).mean()
    )
    
    lag_cols = ['prev_hour_items', 'prev_day_items', 'prev_week_items', 'prev_month_items']
    df[lag_cols] = df[lag_cols].fillna(0)
    
    return df

def calculate_campaign_features(campaigns: List[CampaignData]) -> dict:
    """Calculate campaign statistics"""
    if not campaigns:
        return {'total_campaigns': 0, 'avg_discount': 0}
    
    total = len(campaigns)
    avg_discount = np.mean([c.discount for c in campaigns])
    
    return {'total_campaigns': total, 'avg_discount': avg_discount}

def create_prediction_windows(start_date: str, num_days: int, place_id: int = 1) -> pd.DataFrame:
    """Create future time windows for prediction"""
    start = pd.to_datetime(start_date)
    
    date_hours = []
    for day_offset in range(num_days):
        current_date = start + timedelta(days=day_offset)
        for hour in range(24):
            date_hours.append({
                'place_id': place_id,
                'datetime': current_date + timedelta(hours=hour),
                'date': current_date.date(),
                'hour': hour
            })
    
    df = pd.DataFrame(date_hours)
    return add_time_features(df)

def add_weather_features_mock(df: pd.DataFrame) -> pd.DataFrame:
    """Add mock weather features (fallback when weather API unavailable)"""
    logger.info("Using mock weather data")
    
    weather_defaults = {
        'temperature_2m': 15.0,
        'relative_humidity_2m': 70.0,
        'precipitation': 0.1,
        'rain': 0.1,
        'snowfall': 0.0,
        'weather_code': 1,  # 1 = mainly clear
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
    
    for col, val in weather_defaults.items():
        df[col] = val
    
    return df

def add_weather_features_real(df: pd.DataFrame, place: PlaceData) -> pd.DataFrame:
    """Add real weather features using weather API"""
    if not WEATHER_API_AVAILABLE:
        logger.warning("Weather API not available, using mock data")
        return add_weather_features_mock(df)
    
    try:
        logger.info("Fetching real weather data...")
        
        # Prepare dataframe for weather API
        df_weather = df.copy()
        df_weather['latitude'] = place.lat
        df_weather['longitude'] = place.long
        
        # Fetch weather data
        df_weather = get_weather_for_demand_data(
            demand_df=df_weather,
            date_col='date',
            hour_col='hour',
            place_col='place_id',
            lat_col='latitude',
            lon_col='longitude',
            default_latitude=place.lat,
            default_longitude=place.long
        )
        
        logger.info("Weather data fetched successfully")
        return df_weather
        
    except Exception as e:
        logger.error(f"Weather API failed: {e}", exc_info=True)
        logger.warning("Falling back to mock weather data")
        return add_weather_features_mock(df)

def prepare_features_for_prediction(
    place: PlaceData,
    orders: List[OrderData],
    campaigns: List[CampaignData],
    prediction_start: str,
    prediction_days: int
) -> pd.DataFrame:
    """
    Complete feature engineering pipeline for prediction
    """
    
    # 1. Process historical orders
    orders_df = process_historical_orders(orders)
    hourly_hist = aggregate_to_hourly(orders_df)
    hourly_hist = add_time_features(hourly_hist)
    hourly_hist = add_lag_features(hourly_hist)
    
    # 2. Create future prediction windows
    future_df = create_prediction_windows(prediction_start, prediction_days)
    
    # 3. Combine historical + future for lag feature calculation
    combined = pd.concat([hourly_hist, future_df], ignore_index=True)
    combined = combined.sort_values(['place_id', 'datetime'])
    
    # Recalculate lag features on combined data
    combined = add_lag_features(combined)
    
    # 4. Filter to only future predictions
    prediction_df = combined[combined['datetime'] >= pd.to_datetime(prediction_start)].copy()
    
    # 5. Add place features
    prediction_df['type_id'] = place.type_id if place.type_id else -1
    prediction_df['waiting_time'] = place.waiting_time if place.waiting_time else 30
    prediction_df['rating'] = place.rating if place.rating else 4.0
    prediction_df['delivery'] = int(place.delivery)
    prediction_df['accepting_orders'] = int(place.accepting_orders if place.accepting_orders else True)
    prediction_df['latitude'] = place.lat
    prediction_df['longitude'] = place.long
    
    # 6. Add campaign features
    campaign_stats = calculate_campaign_features(campaigns)
    prediction_df['total_campaigns'] = campaign_stats['total_campaigns']
    prediction_df['avg_discount'] = campaign_stats['avg_discount']
    
    # 7. Add weather features (mock for now)
    prediction_df = add_weather_features_real(prediction_df, place)    
    
    return prediction_df

def align_features_with_model(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure feature set matches what model expects
    """
    # Expected features based on training
    expected_features = [
        'place_id', 'hour', 'day_of_week', 'month', 'week_of_year',
        'type_id', 'waiting_time', 'rating', 'delivery', 'accepting_orders',
        'total_campaigns', 'avg_discount',
        'prev_hour_items', 'prev_day_items', 'prev_week_items', 'prev_month_items',
        'rolling_7d_avg_items',
        # Base weather features
        'temperature_2m', 'relative_humidity_2m', 'precipitation', 'rain',
        'snowfall', 'weather_code', 'cloud_cover', 'wind_speed_10m',
        # Derived weather features
        'is_rainy', 'is_snowy', 'is_cold', 'is_hot', 'is_cloudy', 'is_windy',
        'good_weather', 'weather_severity'
    ]
    
    # Add missing columns with defaults
    for col in expected_features:
        if col not in df.columns:
            logger.warning(f"Missing column '{col}', filling with 0")
            df[col] = 0
    
    # Keep only expected features in correct order
    df = df[expected_features]
    
    # Convert dtypes
    df['place_id'] = df['place_id'].astype('float64')
    df['type_id'] = df['type_id'].astype('float64')
    df.columns = df.columns.astype(str)
    
    return df

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/")
def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "model_loaded": model is not None,
        "version": "1.0.0"
    }

@app.get("/model/info")
def model_info():
    """Get model metadata"""
    if metadata is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    return metadata

@app.post("/predict", response_model=PredictionResponse)
def predict_demand(request: PredictionRequest):
    """
    Main prediction endpoint
    
    Accepts restaurant data and returns hourly demand predictions
    """
    
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        # 1. Feature engineering
        logger.info(f"Processing prediction request for {request.place.name}")
        
        features_df = prepare_features_for_prediction(
            place=request.place,
            orders=request.orders,
            campaigns=request.campaigns,
            prediction_start=request.prediction_start_date,
            prediction_days=request.prediction_days
        )
        
        # Keep datetime info for response formatting
        datetime_info = features_df[['datetime']].copy()
        
        # 2. Align features with model expectations
        X = align_features_with_model(features_df)
        
        # 3. Make predictions
        logger.info(f"Making predictions for {len(X)} hours")
        predictions = model.predict(X)
        
        # Ensure non-negative integers
        predictions = np.maximum(predictions, 0).round().astype(int)
        
        # 4. Format response
        datetime_info['order_count'] = predictions[:, 1]
        datetime_info['item_count'] = predictions[:, 0]
        datetime_info['date'] = datetime_info['datetime'].dt.date
        datetime_info['hour'] = datetime_info['datetime'].dt.hour
        datetime_info['day_name'] = datetime_info['datetime'].dt.strftime('%a').str.lower()
        
        # Group by day
        days = []
        for date_val, day_group in datetime_info.groupby('date'):
            day_name = day_group.iloc[0]['day_name']
            
            hours = []
            for _, row in day_group.iterrows():
                hours.append(HourPrediction(
                    hour=int(row['hour']),
                    order_count=int(row['order_count']),
                    item_count=int(row['item_count'])
                ))
            
            days.append(DayPrediction(
                day_name=day_name,
                date=str(date_val),
                hours=hours
            ))
        
        # 5. Create response
        response = PredictionResponse(
            restaurant_name=request.place.name,
            prediction_period=f"{request.prediction_start_date} to {days[-1].date}",
            days=days
        )
        
        logger.info(f"Prediction completed successfully")
        return response
        
    except Exception as e:
        logger.error(f"Prediction failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

# ============================================================================
# EXAMPLE REQUEST GENERATOR
# ============================================================================

@app.get("/example-request")
def get_example_request():
    """Get an example request JSON"""
    return {
        "place": {
            "name": "Pizza Paradise",
            "lat": 55.6761,
            "long": 12.5683,
            "waiting_time": 30,
            "receiving_phone": True,
            "delivery": True,
            "opening_hours": "10:00-23:00",
            "shift_duration": 8,
            "type_id": 1,
            "rating": 4.5,
            "accepting_orders": True
        },
        "orders": [
            {
                "time": "2024-01-01T12:30:00",
                "items": 3,
                "status": "completed",
                "total_amount": 45.50,
                "discount_amount": 5.00
            },
            {
                "time": "2024-01-01T13:15:00",
                "items": 2,
                "status": "completed",
                "total_amount": 32.00,
                "discount_amount": 0
            }
        ],
        "campaigns": [
            {
                "start_time": "2024-01-01T00:00:00",
                "end_time": "2024-01-07T23:59:59",
                "items_included": ["pizza_margherita", "pizza_pepperoni"],
                "discount": 15.0
            }
        ],
        "prediction_start_date": "2024-01-15",
        "prediction_days": 7
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)