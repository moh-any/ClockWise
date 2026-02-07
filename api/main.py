"""
Restaurant Demand Prediction & Scheduling API v3.1
====================================================
FastAPI-based REST API for:
1. Predicting hourly restaurant demand (item_count & order_count)
2. Generating optimal staff schedules based on demand and employee preferences
3. Recommending AI-powered marketing campaigns
4. Real-time data collection for surge detection

Version 3.1 Updates:
- Added management insights structure matching scheduler output
- Fixed input/output alignment across all endpoints
- Added comprehensive insights for hiring and workforce decisions
- Weather and holiday data auto-fetched from external APIs
- Integrated surge detection and real-time data collection
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Union, Any
from datetime import datetime, date, timedelta
from fastapi.openapi.docs import get_redoc_html  
import pandas as pd
import numpy as np
import joblib
from pathlib import Path
import logging
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# IMPORT EXTERNAL MODULES WITH FALLBACKS
# ============================================================================

# Weather API
try:
    from src.weather_api import get_weather_for_demand_data, WeatherAPI
    WEATHER_API_AVAILABLE = True
    logger.info("Weather API imported successfully")
except ImportError as e:
    WEATHER_API_AVAILABLE = False
    logger.warning(f"Weather API not available: {e}")

# Holiday API
try:
    from src.holiday_api import add_holiday_feature, HolidayChecker
    HOLIDAY_API_AVAILABLE = True
    logger.info("Holiday API imported successfully")
except ImportError as e:
    HOLIDAY_API_AVAILABLE = False
    logger.warning(f"Holiday API not available: {e}")

# Scheduler
try:
    from src.scheduler_cpsat import (
        SchedulerCPSAT, 
        SchedulerInput, 
        Employee, 
        Role, 
        ProductionChain, 
        Shift,
        generate_management_insights
    )
    SCHEDULER_AVAILABLE = True
    logger.info("Scheduler imported successfully")
except ImportError as e:
    SCHEDULER_AVAILABLE = False
    logger.warning(f"Scheduler not available: {e}")

# Campaign Recommender
try:
    from src.campaign_analyzer import CampaignAnalyzer
    from src.campaign_recommender import CampaignRecommender, RecommenderContext
    CAMPAIGN_AVAILABLE = True
    logger.info("Campaign modules imported successfully")
except ImportError as e:
    CAMPAIGN_AVAILABLE = False
    logger.warning(f"Campaign modules not available: {e}")

# Surge Detection API
try:
    from src.surge_api import register_surge_routes
    SURGE_API_AVAILABLE = True
    logger.info("Surge Detection API imported successfully")
except ImportError as e:
    SURGE_API_AVAILABLE = False
    logger.warning(f"Surge Detection API not available: {e}")

# Data Collector
try:
    from src.data_collector import RealTimeDataCollector, load_venues_from_database
    DATA_COLLECTOR_AVAILABLE = True
    logger.info("Data collector imported successfully")
    data_collector = RealTimeDataCollector()
except ImportError as e:
    DATA_COLLECTOR_AVAILABLE = False
    data_collector = None
    logger.warning(f"Data collector not available: {e}")


# ============================================================================
# INITIALIZE FASTAPI APP
# ============================================================================

app = FastAPI(
    title="Restaurant Demand Prediction & Scheduling API",
    description="Predict hourly demand, generate optimal staff schedules, recommend AI-powered campaigns, and detect demand surges",
    version="3.1.0",
    docs_url="/docs",
    redoc_url=None,
    openapi_url="/openapi.json"
)

# Add custom ReDoc endpoint
@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=app.title + " - ReDoc",
        redoc_js_url="https://unpkg.com/redoc@latest/bundles/redoc.standalone.js",
    )

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Surge Detection API routes
if SURGE_API_AVAILABLE:
    register_surge_routes(app)
    logger.info("Surge Detection API routes registered at /api/v1/surge/*")


# ============================================================================
# PYDANTIC MODELS - SHARED
# ============================================================================

class OpeningHoursDay(BaseModel):
    """Opening hours for a specific day"""
    from_time: Optional[str] = Field(None, alias="from", description="Opening time (HH:MM)")
    to: Optional[str] = Field(None, description="Closing time (HH:MM)")
    closed: Optional[bool] = Field(None, description="True if closed this day")

    model_config = ConfigDict(populate_by_name=True)


class PlaceData(BaseModel):
    """Restaurant/Place information"""
    place_id: str
    place_name: str
    type: str
    latitude: float
    longitude: float
    waiting_time: Optional[int] = None
    receiving_phone: bool
    delivery: bool
    opening_hours: Dict[str, OpeningHoursDay]
    fixed_shifts: bool = True
    number_of_shifts_per_day: int = 3
    shift_times: List[str]
    rating: Optional[float] = None
    accepting_orders: Optional[bool] = True


class OrderData(BaseModel):
    """Historical order information"""
    time: str
    items: int
    status: str
    total_amount: float
    discount_amount: float = 0


class CampaignData(BaseModel):
    """Marketing campaign information"""
    start_time: str
    end_time: str
    items_included: List[str]
    discount: float


# ============================================================================
# PYDANTIC MODELS - DEMAND PREDICTION
# ============================================================================

class HourPrediction(BaseModel):
    """Prediction for a single hour"""
    hour: int
    order_count: int
    item_count: int


class DayPrediction(BaseModel):
    """Predictions for a single day"""
    day_name: str
    date: str
    hours: List[HourPrediction]


class DemandOutput(BaseModel):
    """Demand prediction output"""
    restaurant_name: str
    prediction_period: str
    days: List[DayPrediction]


class DemandPredictionRequest(BaseModel):
    """Request for demand prediction only"""
    place: PlaceData
    orders: List[OrderData]
    campaigns: List[CampaignData] = []
    prediction_start_date: str
    prediction_days: int = 7


class DemandPredictionResponse(BaseModel):
    """Response for demand prediction"""
    demand_output: DemandOutput


# ============================================================================
# PYDANTIC MODELS - SCHEDULING
# ============================================================================

class RoleData(BaseModel):
    """Role definition"""
    role_id: str
    role_name: str
    producing: bool
    items_per_employee_per_hour: Optional[float] = None
    min_present: int = 0
    is_independent: bool = True


class EmployeeHours(BaseModel):
    """Available/preferred hours for a specific day"""
    from_time: str = Field(..., alias="from")
    to: str

    model_config = ConfigDict(populate_by_name=True)


class EmployeeData(BaseModel):
    """Employee information"""
    employee_id: str
    role_ids: List[str]
    available_days: List[str]
    preferred_days: List[str]
    available_hours: Dict[str, EmployeeHours]
    preferred_hours: Dict[str, EmployeeHours]
    hourly_wage: float
    max_hours_per_week: float = 40.0
    max_consec_slots: int = 8
    pref_hours: float = 32.0


class ProductionChainData(BaseModel):
    """Production chain definition"""
    chain_id: str
    role_ids: List[str]
    contrib_factor: float = 1.0


class SchedulerConfig(BaseModel):
    """Scheduler configuration parameters"""
    slot_len_hour: float = 1.0
    min_rest_slots: int = 2
    min_shift_length_slots: int = 2
    meet_all_demand: bool = False


class ScheduleInput(BaseModel):
    """Input for schedule generation"""
    roles: List[RoleData]
    employees: List[EmployeeData]
    production_chains: List[ProductionChainData] = []
    scheduler_config: Optional[SchedulerConfig] = None


class ScheduleOutput(BaseModel):
    """Schedule output - organized by day and shift"""
    monday: List[Dict[str, List[str]]] = []
    tuesday: List[Dict[str, List[str]]] = []
    wednesday: List[Dict[str, List[str]]] = []
    thursday: List[Dict[str, List[str]]] = []
    friday: List[Dict[str, List[str]]] = []
    saturday: List[Dict[str, List[str]]] = []
    sunday: List[Dict[str, List[str]]] = []


class ManagementInsights(BaseModel):
    """Management insights for hiring and workforce decisions"""
    has_solution: bool
    peak_periods: List[Dict[str, Any]]
    capacity_analysis: Dict[str, Any]
    employee_utilization: Optional[List[Dict[str, Any]]] = None
    role_demand: Optional[Dict[str, Any]] = None
    hiring_recommendations: Optional[List[Dict[str, Any]]] = None
    coverage_gaps: Optional[List[Dict[str, Any]]] = None
    cost_analysis: Optional[Dict[str, Any]] = None
    workload_distribution: Optional[Dict[str, Any]] = None
    feasibility_analysis: Optional[List[Dict[str, Any]]] = None


class SchedulingRequest(BaseModel):
    """Request for scheduling only"""
    place: PlaceData
    schedule_input: ScheduleInput
    demand_predictions: List[DayPrediction]
    prediction_start_date: str


class SchedulingResponse(BaseModel):
    """Response for scheduling"""
    schedule_output: ScheduleOutput
    schedule_status: str
    schedule_message: Optional[str] = None
    objective_value: Optional[float] = None
    management_insights: Optional[ManagementInsights] = None


# ============================================================================
# PYDANTIC MODELS - CAMPAIGN RECOMMENDATIONS
# ============================================================================

class OrderItemData(BaseModel):
    """Order item data for affinity analysis"""
    order_id: str
    item_id: str
    quantity: Optional[int] = 1


class RecommendedCampaignItem(BaseModel):
    """A single campaign recommendation"""
    campaign_id: str
    items: List[str]
    discount_percentage: float
    start_date: str
    end_date: str
    duration_days: int
    expected_uplift: float
    expected_roi: float
    expected_revenue: float
    confidence_score: float
    reasoning: str
    priority_score: float
    recommended_for_context: Dict


class CampaignRecommendationRequest(BaseModel):
    """Request for campaign recommendations"""
    place: Union[PlaceData, Dict]
    orders: List[Union[OrderData, Dict]]
    campaigns: List[Union[CampaignData, Dict]] = []
    order_items: Optional[List[Union[OrderItemData, Dict]]] = None
    recommendation_start_date: str
    num_recommendations: int = 5
    optimize_for: str = "roi"
    max_discount: float = 30.0
    min_campaign_duration_days: int = 3
    max_campaign_duration_days: int = 14
    available_items: List[str] = []
    weather_forecast: Optional[Dict[str, float]] = None
    upcoming_holidays: Optional[List[str]] = None


class CampaignRecommendationResponse(BaseModel):
    """Response containing campaign recommendations"""
    restaurant_name: str
    recommendation_date: str
    recommendations: List[RecommendedCampaignItem]
    analysis_summary: Dict
    insights: Dict
    confidence_level: str


class CampaignFeedback(BaseModel):
    """Feedback on executed campaign"""
    campaign_id: str
    actual_uplift: Optional[float] = None
    actual_roi: Optional[float] = None
    actual_revenue: Optional[float] = None
    success: bool
    notes: Optional[str] = None


class CampaignFeedbackResponse(BaseModel):
    """Response after submitting campaign feedback"""
    status: str
    message: str
    updated_parameters: Optional[Dict] = None


# ============================================================================
# PYDANTIC MODELS - DATA COLLECTION
# ============================================================================

class VenueRequest(BaseModel):
    """Request model for single venue metrics"""
    place_id: int
    name: str
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)


class VenueMetrics(BaseModel):
    """Response model for venue metrics"""
    place_id: int
    timestamp: str
    actual_items: int
    actual_orders: int
    predicted_items: float
    predicted_orders: float
    ratio: float
    excess_demand: float
    social_signals: Dict[str, float]


class BatchVenueRequest(BaseModel):
    """Request model for batch venue metrics collection"""
    venues: List[VenueRequest]


class BatchMetricsResponse(BaseModel):
    """Response model for batch metrics collection"""
    metrics: List[VenueMetrics]
    summary: Dict[str, Union[int, float]]


# ============================================================================
# COMBINED REQUEST/RESPONSE (DEPRECATED)
# ============================================================================

class CombinedRequest(BaseModel):
    """Combined request (backward compatibility)"""
    demand_input: DemandPredictionRequest
    schedule_input: ScheduleInput


class PredictionResponse(BaseModel):
    """Complete prediction and scheduling response"""
    demand_output: DemandOutput
    schedule_output: ScheduleOutput


# ============================================================================
# MODEL LOADING
# ============================================================================

MODEL_PATH = Path("data/models/rf_model.joblib")
METADATA_PATH = Path("data/models/rf_model_metadata.json")

model = None
metadata = None

try:
    model = joblib.load(MODEL_PATH)
    metadata = joblib.load(METADATA_PATH)
    logger.info("✓ Demand prediction model loaded successfully")
except Exception as e:
    logger.error(f"✗ Failed to load demand model: {e}")


# ============================================================================
# HELPER FUNCTIONS - TIME PARSING
# ============================================================================

def parse_time_to_hour(time_str: str) -> float:
    """Convert HH:MM to decimal hours"""
    if time_str.lower() == "closed":
        return -1
    parts = time_str.split(":")
    return int(parts[0]) + int(parts[1]) / 60.0


def time_to_slot(time_str: str, slot_duration_hours: float = 1.0) -> int:
    """Convert HH:MM to slot index"""
    if time_str.lower() == "closed":
        return -1
    hour = parse_time_to_hour(time_str)
    return int(hour / slot_duration_hours)


# ============================================================================
# HELPER FUNCTIONS - ORDER PROCESSING
# ============================================================================

def process_historical_orders(orders: List[OrderData], place_id: str = "pl_001") -> pd.DataFrame:
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


# ============================================================================
# HELPER FUNCTIONS - FEATURE ENGINEERING
# ============================================================================

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


def create_prediction_windows(start_date: str, num_days: int, place_id: str = "pl_001") -> pd.DataFrame:
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
    """Add mock weather features (fallback)"""
    weather_defaults = {
        'temperature_2m': 15.0,
        'relative_humidity_2m': 70.0,
        'precipitation': 0.0,
        'rain': 0.0,
        'snowfall': 0.0,
        'weather_code': 1,
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


def add_holiday_features_mock(df: pd.DataFrame) -> pd.DataFrame:
    """Add mock holiday feature (fallback)"""
    df['is_holiday'] = 0
    return df


# ============================================================================
# MAIN FEATURE PREPARATION PIPELINE
# ============================================================================

def prepare_features_for_prediction(
    place: PlaceData,
    orders: List[OrderData],
    campaigns: List[CampaignData],
    prediction_start: str,
    prediction_days: int
) -> pd.DataFrame:
    """Complete feature engineering pipeline for prediction"""
    
    logger.info("Starting feature preparation pipeline...")
    
    orders_df = process_historical_orders(orders, place.place_id)
    hourly_hist = aggregate_to_hourly(orders_df)
    hourly_hist = add_time_features(hourly_hist)
    hourly_hist = add_lag_features(hourly_hist)
    
    future_df = create_prediction_windows(prediction_start, prediction_days, place.place_id)
    
    combined = pd.concat([hourly_hist, future_df], ignore_index=True)
    combined = combined.sort_values(['place_id', 'datetime'])
    combined = add_lag_features(combined)
    
    prediction_df = combined[combined['datetime'] >= pd.to_datetime(prediction_start)].copy()
    
    type_mapping = {'bar': 1332, 'cafe': 1333, 'lounge': 1334, 'restaurant': 1335, 'pub': 1336}
    prediction_df['type_id'] = type_mapping.get(place.type, 1335)
    prediction_df['waiting_time'] = place.waiting_time if place.waiting_time else 30
    prediction_df['rating'] = place.rating if place.rating else 4.0
    prediction_df['delivery'] = int(place.delivery)
    prediction_df['accepting_orders'] = int(place.accepting_orders if place.accepting_orders else True)
    
    prediction_df['latitude'] = place.latitude
    prediction_df['longitude'] = place.longitude
    
    campaign_stats = calculate_campaign_features(campaigns)
    prediction_df['total_campaigns'] = campaign_stats['total_campaigns']
    prediction_df['avg_discount'] = campaign_stats['avg_discount']
    
    if WEATHER_API_AVAILABLE:
        try:
            prediction_df = get_weather_for_demand_data(
                prediction_df,
                date_col='date',
                hour_col='hour',
                place_col='place_id',
                lat_col='latitude',
                lon_col='longitude',
                default_latitude=place.latitude,
                default_longitude=place.longitude
            )
            logger.info("✓ Weather features added")
        except Exception as e:
            logger.warning(f"Weather API failed: {e}. Using defaults.")
            prediction_df = add_weather_features_mock(prediction_df)
    else:
        prediction_df = add_weather_features_mock(prediction_df)
    
    if HOLIDAY_API_AVAILABLE:
        try:
            prediction_df = add_holiday_feature(
                prediction_df,
                date_column='datetime',
                latitude_column='latitude',
                longitude_column='longitude',
                default_latitude=place.latitude,
                default_longitude=place.longitude
            )
            logger.info("✓ Holiday features added")
        except Exception as e:
            logger.warning(f"Holiday API failed: {e}. Using defaults.")
            prediction_df = add_holiday_features_mock(prediction_df)
    else:
        prediction_df = add_holiday_features_mock(prediction_df)
    
    prediction_df = prediction_df.drop(['latitude', 'longitude'], axis=1, errors='ignore')
    
    logger.info(f"✓ Feature preparation complete. Shape: {prediction_df.shape}")
    return prediction_df


def align_features_with_model(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure feature set matches model expectations"""
    df = df.copy()
    
    if df['place_id'].dtype == 'object' or df['place_id'].dtype == 'string':
        def encode_place_id(place_str):
            hash_obj = hashlib.md5(str(place_str).encode('utf-8'))
            return float(int(hash_obj.hexdigest()[:8], 16) % 100000)
        
        df['place_id'] = df['place_id'].apply(encode_place_id)
    
    df['place_id'] = df['place_id'].astype('float64')
    
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
    
    for col in expected_features:
        if col not in df.columns:
            df[col] = 0
    
    df = df[expected_features].copy()
    df['type_id'] = df['type_id'].astype('float64')
    df['is_holiday'] = df['is_holiday'].astype('int')
    df.columns = df.columns.astype(str)
    
    if df.isnull().any().any():
        df = df.fillna(0)
    
    return df


def zero_out_closed_hours(
    predictions: np.ndarray,
    datetime_info: pd.DataFrame,
    place: PlaceData
) -> np.ndarray:
    """
    Post-processing filter to zero out predictions during closed hours.
    
    Model was trained without zeros, so it predicts phantom demand during closed hours.
    This filter applies business logic to enforce zero demand when restaurant is closed.
    """
    predictions = predictions.copy()
    
    day_name_map = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    
    for idx, row in datetime_info.iterrows():
        day_of_week = row['datetime'].weekday()
        hour = int(row['hour'])
        day_name = day_name_map[day_of_week]
        
        if day_name not in place.opening_hours:
            continue
        
        opening_hours = place.opening_hours[day_name]
        
        if opening_hours.closed:
            predictions[idx, 0] = 0
            predictions[idx, 1] = 0
            continue
        
        if opening_hours.from_time and opening_hours.to:
            open_hour = parse_time_to_hour(opening_hours.from_time)
            close_hour = parse_time_to_hour(opening_hours.to)
            
            if close_hour < open_hour:
                is_open = (hour >= open_hour) or (hour < close_hour)
            else:
                is_open = (open_hour <= hour < close_hour)
            
            if not is_open:
                predictions[idx, 0] = 0
                predictions[idx, 1] = 0
    
    zeroed_count = np.sum((predictions[:, 0] == 0) & (predictions[:, 1] == 0))
    logger.info(f"Post-processing: Zeroed out {zeroed_count}/{len(predictions)} hours during closed periods")
    
    return predictions


# ============================================================================
# SCHEDULER HELPER FUNCTIONS
# ============================================================================

def convert_api_data_to_scheduler_input(
    place: PlaceData,
    schedule_input: ScheduleInput,
    demand_predictions: pd.DataFrame,
    prediction_start_date: str
) -> SchedulerInput:
    """Convert API request data to scheduler input format"""
    
    config = schedule_input.scheduler_config or SchedulerConfig()
    
    scheduler_roles = []
    for role_data in schedule_input.roles:
        scheduler_roles.append(Role(
            id=role_data.role_id,
            producing=role_data.producing,
            items_per_hour=role_data.items_per_employee_per_hour or 0,
            min_present=role_data.min_present,
            is_independent=role_data.is_independent
        ))
    
    scheduler_chains = []
    for chain_data in schedule_input.production_chains:
        scheduler_chains.append(ProductionChain(
            id=chain_data.chain_id,
            roles=chain_data.role_ids,
            contrib_factor=chain_data.contrib_factor
        ))
    
    unique_dates = sorted(demand_predictions['date'].unique())
    num_days = len(unique_dates)
    num_slots_per_day = int(24 / config.slot_len_hour)
    
    prediction_start = pd.to_datetime(prediction_start_date).date()
    calendar_day_to_pred_days = {}
    
    for i in range(num_days):
        current_date = prediction_start + timedelta(days=i)
        calendar_day_name = current_date.strftime('%A').lower()
        
        if calendar_day_name not in calendar_day_to_pred_days:
            calendar_day_to_pred_days[calendar_day_name] = []
        calendar_day_to_pred_days[calendar_day_name].append(i)
    
    scheduler_employees = []
    
    for emp_data in schedule_input.employees:
        availability = {}
        for day_idx in range(num_days):
            for slot in range(num_slots_per_day):
                availability[(day_idx, slot)] = False
        
        for calendar_day_name in emp_data.available_days:
            pred_day_indices = calendar_day_to_pred_days.get(calendar_day_name.lower(), [])
            
            if not pred_day_indices or calendar_day_name.lower() not in emp_data.available_hours:
                continue
            
            hours = emp_data.available_hours[calendar_day_name.lower()]
            start_hour = parse_time_to_hour(hours.from_time)
            end_hour = parse_time_to_hour(hours.to)
            
            if start_hour == -1 or end_hour == -1:
                continue
            
            start_slot = int(start_hour / config.slot_len_hour)
            end_slot = int(end_hour / config.slot_len_hour)
            if end_hour % config.slot_len_hour > 0:
                end_slot += 1
            
            for pred_day_idx in pred_day_indices:
                for slot in range(start_slot, min(end_slot, num_slots_per_day)):
                    availability[(pred_day_idx, slot)] = True
        
        preferences = {}
        for calendar_day_name in emp_data.preferred_days:
            pred_day_indices = calendar_day_to_pred_days.get(calendar_day_name.lower(), [])
            
            if not pred_day_indices or calendar_day_name.lower() not in emp_data.preferred_hours:
                continue
            
            hours = emp_data.preferred_hours[calendar_day_name.lower()]
            start_hour = parse_time_to_hour(hours.from_time)
            end_hour = parse_time_to_hour(hours.to)
            
            if start_hour == -1 or end_hour == -1:
                continue
            
            start_slot = int(start_hour / config.slot_len_hour)
            end_slot = int(end_hour / config.slot_len_hour)
            if end_hour % config.slot_len_hour > 0:
                end_slot += 1
            
            for pred_day_idx in pred_day_indices:
                for slot in range(start_slot, min(end_slot, num_slots_per_day)):
                    preferences[(pred_day_idx, slot)] = True
        
        scheduler_employees.append(Employee(
            id=emp_data.employee_id,
            wage=emp_data.hourly_wage,
            max_hours_per_week=emp_data.max_hours_per_week,
            max_consec_slots=emp_data.max_consec_slots,
            pref_hours=emp_data.pref_hours,
            role_eligibility=set(emp_data.role_ids),
            availability=availability,
            slot_preferences=preferences
        ))
    
    date_to_day_idx = {d: i for i, d in enumerate(unique_dates)}
    demand_dict = {}
    
    for _, row in demand_predictions.iterrows():
        row_date = row['datetime'].date() if hasattr(row['datetime'], 'date') else row['date']
        day_idx = date_to_day_idx.get(row_date)
        
        if day_idx is None:
            continue
        
        hour = row['hour']
        slot = int(hour / config.slot_len_hour)
        demand_dict[(day_idx, slot)] = float(row['item_count'])
    
    shifts = []
    if place.fixed_shifts:
        shifts = parse_shift_times_fixed(place.shift_times, place, calendar_day_to_pred_days)
    
    return SchedulerInput(
        employees=scheduler_employees,
        roles=scheduler_roles,
        num_days=num_days,
        num_slots_per_day=num_slots_per_day,
        demand=demand_dict,
        chains=scheduler_chains,
        shifts=shifts,
        fixed_shifts=place.fixed_shifts,
        slot_len_hour=config.slot_len_hour,
        min_rest_slots=config.min_rest_slots,
        min_shift_length_slots=config.min_shift_length_slots,
        w_unmet=100000,
        w_wage=100,
        w_hours=50,
        w_fair=10,
        w_slot=1,
        meet_all_demand=config.meet_all_demand
    )


def parse_shift_times_fixed(
    shift_times: List[str], 
    place: PlaceData, 
    calendar_day_to_pred_days: Dict[str, List[int]]
) -> List[Shift]:
    """Parse shift time strings into Shift objects"""
    shifts = []
    
    for shift_idx, shift_time in enumerate(shift_times):
        parts = shift_time.split('-')
        if len(parts) != 2:
            continue
        
        start_str, end_str = parts
        start_hour = parse_time_to_hour(start_str)
        end_hour = parse_time_to_hour(end_str)
        
        if start_hour == -1 or end_hour == -1:
            continue
        
        if end_hour <= start_hour:
            end_hour += 24
        
        for calendar_day_name, hours in place.opening_hours.items():
            if hours.closed:
                continue
            
            pred_day_indices = calendar_day_to_pred_days.get(calendar_day_name.lower(), [])
            
            for pred_day_idx in pred_day_indices:
                shifts.append(Shift(
                    id=f"shift_{pred_day_idx}_{shift_idx}",
                    day=pred_day_idx,
                    start_slot=int(start_hour),
                    end_slot=int(end_hour)
                ))
    
    return shifts


def format_schedule_output(
    solution: Dict, 
    place: PlaceData, 
    config: SchedulerConfig,
    prediction_start_date: str,
    num_days: int
) -> ScheduleOutput:
    """Format scheduler solution to API output format"""
    
    day_names = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    
    prediction_start = pd.to_datetime(prediction_start_date).date()
    pred_day_to_calendar = {}
    for i in range(num_days):
        current_date = prediction_start + timedelta(days=i)
        calendar_day_name = current_date.strftime('%A').lower()
        pred_day_to_calendar[i] = calendar_day_name
    
    schedule_by_day = {day: [] for day in day_names}
    
    if not solution or 'schedule' not in solution:
        return ScheduleOutput(**schedule_by_day)
    
    if place.fixed_shifts:
        for entry in solution['schedule']:
            shift_id = entry.get('shift')
            if not shift_id:
                continue
            
            pred_day_idx = entry['day']
            calendar_day = pred_day_to_calendar.get(pred_day_idx)
            if not calendar_day:
                continue
            
            start_slot = entry.get('start_slot', 0)
            end_slot = entry.get('end_slot', 0)
            start_hour = int(start_slot * config.slot_len_hour)
            end_hour = int(end_slot * config.slot_len_hour)
            
            if end_hour > 24:
                end_hour = end_hour % 24
            
            shift_key = f"{start_hour:02d}:00-{end_hour:02d}:00"
            
            existing = False
            for shift_dict in schedule_by_day[calendar_day]:
                if shift_key in shift_dict:
                    if entry['employee'] not in shift_dict[shift_key]:
                        shift_dict[shift_key].append(entry['employee'])
                    existing = True
                    break
            
            if not existing:
                schedule_by_day[calendar_day].append({
                    shift_key: [entry['employee']]
                })
    
    return ScheduleOutput(**schedule_by_day)


def format_management_insights(insights_dict: Dict) -> ManagementInsights:
    """Convert raw insights dict to ManagementInsights model"""
    return ManagementInsights(
        has_solution=insights_dict.get('has_solution', False),
        peak_periods=insights_dict.get('peak_periods', []),
        capacity_analysis=insights_dict.get('capacity_analysis', {}),
        employee_utilization=insights_dict.get('employee_utilization'),
        role_demand=insights_dict.get('role_demand'),
        hiring_recommendations=insights_dict.get('hiring_recommendations'),
        coverage_gaps=insights_dict.get('coverage_gaps'),
        cost_analysis=insights_dict.get('cost_analysis'),
        workload_distribution=insights_dict.get('workload_distribution'),
        feasibility_analysis=insights_dict.get('feasibility_analysis')
    )


def _get_season(dt: pd.Timestamp) -> str:
    """Determine season from date"""
    month = dt.month
    
    if month in [12, 1, 2]:
        return "winter"
    elif month in [3, 4, 5]:
        return "spring"
    elif month in [6, 7, 8]:
        return "summer"
    else:
        return "fall"


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "model_loaded": model is not None,
        "scheduler_available": SCHEDULER_AVAILABLE,
        "weather_api_available": WEATHER_API_AVAILABLE,
        "holiday_api_available": HOLIDAY_API_AVAILABLE,
        "campaign_available": CAMPAIGN_AVAILABLE,
        "surge_api_available": SURGE_API_AVAILABLE,
        "data_collector_available": DATA_COLLECTOR_AVAILABLE,
        "version": "3.1.0",
        "features": [
            "demand_prediction",
            "staff_scheduling",
            "campaign_recommendations",
            "management_insights",
            "surge_detection",
            "real_time_data_collection"
        ]
    }


@app.get("/model/info", tags=["Model"])
def model_info():
    """Get model metadata"""
    if metadata is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    return metadata


@app.post("/predict/demand", response_model=DemandPredictionResponse, tags=["Demand Prediction"])
def predict_demand_only(request: DemandPredictionRequest):
    """Predict demand only (no scheduling)"""
    
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        logger.info(f"Processing demand prediction for {request.place.place_name}")
        
        features_df = prepare_features_for_prediction(
            place=request.place,
            orders=request.orders,
            campaigns=request.campaigns,
            prediction_start=request.prediction_start_date,
            prediction_days=request.prediction_days
        )
        
        datetime_info = features_df[['datetime', 'date', 'hour']].copy()
        X = align_features_with_model(features_df)
        
        predictions = model.predict(X)
        predictions = np.maximum(predictions, 0).round().astype(int)
        predictions = zero_out_closed_hours(predictions, datetime_info, request.place)
        
        datetime_info['item_count'] = predictions[:, 0]
        datetime_info['order_count'] = predictions[:, 1]
        datetime_info['day_name'] = datetime_info['datetime'].dt.strftime('%A').str.lower()
        
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
        
        demand_output = DemandOutput(
            restaurant_name=request.place.place_name,
            prediction_period=f"{request.prediction_start_date} to {days[-1].date}",
            days=days
        )
        
        logger.info("✓ Demand prediction completed")
        return DemandPredictionResponse(demand_output=demand_output)
        
    except Exception as e:
        logger.error(f"Demand prediction failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Demand prediction failed: {str(e)}")


@app.post("/predict/schedule", response_model=SchedulingResponse, tags=["Staff Scheduling"])
def predict_schedule_only(request: SchedulingRequest):
    """Generate schedule based on provided demand predictions"""
    
    if not SCHEDULER_AVAILABLE:
        raise HTTPException(status_code=503, detail="Scheduler not available")
    
    try:
        logger.info(f"Processing scheduling for {request.place.place_name}")
        
        demand_data = []
        for day in request.demand_predictions:
            for hour_pred in day.hours:
                demand_data.append({
                    'datetime': pd.to_datetime(f"{day.date} {hour_pred.hour:02d}:00:00"),
                    'date': pd.to_datetime(day.date).date(),
                    'hour': hour_pred.hour,
                    'item_count': hour_pred.item_count,
                    'order_count': hour_pred.order_count,
                    'day_name': day.day_name
                })
        
        datetime_info = pd.DataFrame(demand_data)
        config = request.schedule_input.scheduler_config or SchedulerConfig()
        
        scheduler_input = convert_api_data_to_scheduler_input(
            place=request.place,
            schedule_input=request.schedule_input,
            demand_predictions=datetime_info,
            prediction_start_date=request.prediction_start_date
        )
        
        scheduler = SchedulerCPSAT(scheduler_input)
        solution = scheduler.solve(time_limit_seconds=60)
        
        insights_dict = generate_management_insights(solution, scheduler_input)
        insights = format_management_insights(insights_dict)
        
        if solution:
            schedule_output = format_schedule_output(
                solution=solution,
                place=request.place,
                config=config,
                prediction_start_date=request.prediction_start_date,
                num_days=len(request.demand_predictions)
            )
            
            logger.info("✓ Schedule generated successfully")
            return SchedulingResponse(
                schedule_output=schedule_output,
                schedule_status=solution['status'],
                schedule_message="Schedule generated successfully",
                objective_value=solution['objective_value'],
                management_insights=insights
            )
        else:
            logger.warning("No feasible schedule found")
            return SchedulingResponse(
                schedule_output=ScheduleOutput(),
                schedule_status="INFEASIBLE",
                schedule_message="No feasible schedule found. Check constraints and employee availability.",
                management_insights=insights
            )
            
    except Exception as e:
        logger.error(f"Scheduling failed: {e}", exc_info=True)
        return SchedulingResponse(
            schedule_output=ScheduleOutput(),
            schedule_status="ERROR",
            schedule_message=f"Scheduling error: {str(e)}"
        )


@app.post("/recommend/campaigns", response_model=CampaignRecommendationResponse, tags=["Campaign Recommendations"])
async def recommend_campaigns(request: CampaignRecommendationRequest):
    """Generate AI-powered campaign recommendations"""
    
    if not CAMPAIGN_AVAILABLE:
        raise HTTPException(status_code=503, detail="Campaign recommender not available")
    
    try:
        if not request.orders:
            raise HTTPException(status_code=400, detail="Historical orders required")
        
        logger.info(f"Processing campaign recommendations")
        
        orders_data = []
        for i, order in enumerate(request.orders):
            if isinstance(order, dict):
                orders_data.append({
                    'id': f"order_{i}",
                    'created': pd.to_datetime(order['time']).timestamp(),
                    'place_id': request.place['place_id'] if isinstance(request.place, dict) else request.place.place_id,
                    'total_amount': order['total_amount'],
                    'item_count': order['items'],
                    'status': order['status'],
                    'discount_amount': order.get('discount_amount', 0)
                })
            else:
                orders_data.append({
                    'id': f"order_{i}",
                    'created': pd.to_datetime(order.time).timestamp(),
                    'place_id': request.place['place_id'] if isinstance(request.place, dict) else request.place.place_id,
                    'total_amount': order.total_amount,
                    'item_count': order.items,
                    'status': order.status,
                    'discount_amount': order.discount_amount
                })
        
        orders_df = pd.DataFrame(orders_data)
        
        campaigns_data = []
        for i, campaign in enumerate(request.campaigns):
            if isinstance(campaign, dict):
                campaigns_data.append({
                    'id': f"campaign_{i}",
                    'start_time': campaign['start_time'],
                    'end_time': campaign['end_time'],
                    'items_included': campaign['items_included'],
                    'discount': campaign['discount']
                })
            else:
                campaigns_data.append({
                    'id': f"campaign_{i}",
                    'start_time': campaign.start_time,
                    'end_time': campaign.end_time,
                    'items_included': campaign.items_included,
                    'discount': campaign.discount
                })
        
        order_items_data = []
        if request.order_items:
            for item in request.order_items:
                if isinstance(item, dict):
                    order_items_data.append({
                        'order_id': item['order_id'],
                        'item_id': item['item_id']
                    })
                else:
                    order_items_data.append({
                        'order_id': item.order_id,
                        'item_id': item.item_id
                    })
            order_items_df = pd.DataFrame(order_items_data)
        else:
            order_items_df = pd.DataFrame({
                'order_id': [f"order_{i}" for i in range(len(orders_df))],
                'item_id': ['item_generic'] * len(orders_df)
            })
        
        start_date = pd.to_datetime(request.recommendation_start_date)
        
        if isinstance(request.place, dict):
            place_lat = request.place.get('latitude', 55.6761)
            place_lon = request.place.get('longitude', 12.5683)
        else:
            place_lat = request.place.latitude or 55.6761
            place_lon = request.place.longitude or 12.5683
        
        weather_forecast = {'avg_temperature': 15.0, 'avg_precipitation': 0.0, 'good_weather_ratio': 0.7}
        
        if WEATHER_API_AVAILABLE:
            try:
                weather_api = WeatherAPI(latitude=float(place_lat), longitude=float(place_lon))
                forecast_df = weather_api.get_forecast_weather(days=14)
                
                if not forecast_df.empty:
                    forecast_df = weather_api.add_weather_features(forecast_df)
                    weather_forecast = {
                        'avg_temperature': float(forecast_df['temperature_2m'].mean()),
                        'avg_precipitation': float(forecast_df['precipitation'].mean()),
                        'good_weather_ratio': float(forecast_df['good_weather'].mean())
                    }
            except Exception as e:
                logger.warning(f"Weather fetch failed: {e}")
        
        upcoming_holidays = []
        
        if HOLIDAY_API_AVAILABLE:
            try:
                holiday_checker = HolidayChecker()
                
                for days_ahead in range(30):
                    check_date = (start_date + timedelta(days=days_ahead)).date()
                    result = holiday_checker.is_holiday(check_date, float(place_lat), float(place_lon))
                    
                    if result.get('is_holiday'):
                        upcoming_holidays.append(datetime.combine(check_date, datetime.min.time()))
            except Exception as e:
                logger.warning(f"Holiday fetch failed: {e}")
        
        analyzer = CampaignAnalyzer()
        
        if campaigns_data:
            analyzer.analyze_campaign_effectiveness(orders_df, campaigns_data, order_items_df)
        
        analyzer.extract_temporal_patterns(orders_df)
        
        if len(order_items_df) > 10:
            analyzer.extract_item_affinity(order_items_df, min_support=0.01)
        
        recommender = CampaignRecommender(
            analyzer=analyzer,
            exploration_rate=0.15,
            min_samples_for_prediction=max(3, len(campaigns_data) // 2)
        )
        
        if len(campaigns_data) >= 3:
            recommender.fit(use_xgboost=True)
        
        recent_orders = orders_df[orders_df['created'] >= (start_date.timestamp() - 30*24*3600)]
        recent_avg_daily_revenue = recent_orders['total_amount'].sum() / 30 if len(recent_orders) > 0 else 1000
        recent_avg_daily_orders = len(recent_orders) / 30 if len(recent_orders) > 0 else 10
        
        trend = "stable"
        if len(recent_orders) >= 14:
            first_week = recent_orders.iloc[:len(recent_orders)//2]['total_amount'].sum()
            second_week = recent_orders.iloc[len(recent_orders)//2:]['total_amount'].sum()
            
            if second_week > first_week * 1.1:
                trend = "increasing"
            elif second_week < first_week * 0.9:
                trend = "decreasing"
        
        available_items = request.available_items if request.available_items else order_items_df['item_id'].unique().tolist()
        
        context = RecommenderContext(
            current_date=start_date.to_pydatetime(),
            day_of_week=start_date.dayofweek,
            hour=start_date.hour,
            season=_get_season(start_date),
            recent_avg_daily_revenue=recent_avg_daily_revenue,
            recent_avg_daily_orders=recent_avg_daily_orders,
            recent_trend=trend,
            weather_forecast=weather_forecast,
            upcoming_holidays=upcoming_holidays,
            max_discount=request.max_discount,
            min_campaign_duration_days=request.min_campaign_duration_days,
            max_campaign_duration_days=request.max_campaign_duration_days,
            available_items=available_items
        )
        
        recommendations = recommender.recommend_campaigns(
            context=context,
            num_recommendations=request.num_recommendations,
            optimize_for=request.optimize_for
        )
        
        recommended_items = []
        for rec in recommendations:
            recommended_items.append(RecommendedCampaignItem(
                campaign_id=rec.campaign_id,
                items=rec.items,
                discount_percentage=rec.discount_percentage,
                start_date=rec.start_date,
                end_date=rec.end_date,
                duration_days=rec.duration_days,
                expected_uplift=rec.expected_uplift,
                expected_roi=rec.expected_roi,
                expected_revenue=rec.expected_revenue,
                confidence_score=rec.confidence_score,
                reasoning=rec.reasoning,
                priority_score=rec.priority_score,
                recommended_for_context=rec.recommended_for_context
            ))
        
        analysis_summary = analyzer.get_summary_statistics() if campaigns_data else {
            'total_campaigns_analyzed': 0,
            'avg_roi': 0.0,
            'success_rate': 0.0
        }
        
        insights = {}
        
        if analyzer.temporal_patterns:
            best_day = max(analyzer.temporal_patterns['by_day_of_week'].items(), key=lambda x: x[1]['avg_revenue'])
            insights['best_day_of_week'] = {
                'day': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][best_day[0]],
                'avg_revenue': best_day[1]['avg_revenue']
            }
        
        if analyzer.item_affinity:
            top_pairs = sorted(analyzer.item_affinity.items(), key=lambda x: x[1], reverse=True)[:5]
            insights['top_item_pairs'] = [
                {'items': list(pair), 'affinity_score': score}
                for pair, score in top_pairs
            ]
        
        model_confidence = "high" if len(campaigns_data) >= 10 else "medium" if len(campaigns_data) >= 5 else "low"
        restaurant_name = request.place['place_name'] if isinstance(request.place, dict) else request.place.place_name
        
        response = CampaignRecommendationResponse(
            restaurant_name=restaurant_name,
            recommendation_date=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            recommendations=recommended_items,
            analysis_summary=analysis_summary,
            insights=insights,
            confidence_level=model_confidence
        )
        
        logger.info(f"✓ Generated {len(recommended_items)} campaign recommendations")
        return response
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Campaign recommendation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed: {str(e)}")


@app.post("/recommend/campaigns/feedback", response_model=CampaignFeedbackResponse, tags=["Campaign Recommendations"])
async def submit_campaign_feedback(feedback: CampaignFeedback):
    """Submit feedback on executed campaigns for model improvement"""
    
    try:
        logger.info(f"Received feedback for {feedback.campaign_id}")
        
        return CampaignFeedbackResponse(
            status="success",
            message=f"Feedback for {feedback.campaign_id} received",
            updated_parameters={'status': 'feedback_stored'}
        )
    
    except Exception as e:
        logger.error(f"Feedback processing failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed: {str(e)}")


@app.post("/api/v1/collect/venue", response_model=VenueMetrics, tags=["Data Collection"])
async def collect_venue_metrics(venue: VenueRequest):
    """Collect real-time metrics for a single venue"""
    if not DATA_COLLECTOR_AVAILABLE:
        raise HTTPException(status_code=503, detail="Data collector not available")
    
    try:
        metrics = data_collector.get_single_venue_metrics(
            place_id=venue.place_id,
            venue_name=venue.name,
            latitude=venue.latitude,
            longitude=venue.longitude
        )
        
        if metrics is None:
            raise HTTPException(status_code=500, detail=f"Failed to collect metrics for venue {venue.place_id}")
        
        return metrics
        
    except Exception as e:
        logger.error(f"Error collecting metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/collect/batch", response_model=BatchMetricsResponse, tags=["Data Collection"])
async def collect_batch_metrics(batch: BatchVenueRequest):
    """Collect metrics for multiple venues in one call"""
    if not DATA_COLLECTOR_AVAILABLE:
        raise HTTPException(status_code=503, detail="Data collector not available")
    
    try:
        venues_list = [
            {
                'place_id': v.place_id,
                'name': v.name,
                'latitude': v.latitude,
                'longitude': v.longitude
            }
            for v in batch.venues
        ]
        
        result = data_collector.collect_for_all_venues(venues_list)
        return result
        
    except Exception as e:
        logger.error(f"Error collecting batch metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/collect/health", tags=["Data Collection"])
async def collector_health():
    """Check data collector health"""
    if not DATA_COLLECTOR_AVAILABLE:
        return {
            "status": "unavailable",
            "data_collector": False,
            "message": "Data collector module not loaded"
        }
    
    return {
        "status": "healthy",
        "data_collector": True,
        "ml_model_loaded": data_collector.model is not None,
        "message": "Data collector ready"
    }


@app.post("/predict", response_model=PredictionResponse, tags=["Deprecated"])
def predict_demand_and_schedule(request: CombinedRequest):
    """Combined prediction and scheduling endpoint (DEPRECATED)"""
    
    logger.warning("Combined /predict endpoint is deprecated")
    
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        features_df = prepare_features_for_prediction(
            place=request.demand_input.place,
            orders=request.demand_input.orders,
            campaigns=request.demand_input.campaigns,
            prediction_start=request.demand_input.prediction_start_date,
            prediction_days=request.demand_input.prediction_days
        )
        
        datetime_info = features_df[['datetime', 'date', 'hour']].copy()
        X = align_features_with_model(features_df)
        
        predictions = model.predict(X)
        predictions = np.maximum(predictions, 0).round().astype(int)
        predictions = zero_out_closed_hours(predictions, datetime_info, request.demand_input.place)
        
        datetime_info['item_count'] = predictions[:, 0]
        datetime_info['order_count'] = predictions[:, 1]
        datetime_info['day_name'] = datetime_info['datetime'].dt.strftime('%A').str.lower()
        
        schedule_output = ScheduleOutput()
        
        if SCHEDULER_AVAILABLE and request.schedule_input.employees and request.schedule_input.roles:
            try:
                config = request.schedule_input.scheduler_config or SchedulerConfig()
                
                scheduler_input = convert_api_data_to_scheduler_input(
                    place=request.demand_input.place,
                    schedule_input=request.schedule_input,
                    demand_predictions=datetime_info,
                    prediction_start_date=request.demand_input.prediction_start_date
                )
                
                scheduler = SchedulerCPSAT(scheduler_input)
                solution = scheduler.solve(time_limit_seconds=60)
                
                if solution:
                    schedule_output = format_schedule_output(
                        solution=solution,
                        place=request.demand_input.place,
                        config=config,
                        prediction_start_date=request.demand_input.prediction_start_date,
                        num_days=request.demand_input.prediction_days
                    )
            except Exception as e:
                logger.error(f"Scheduling failed: {e}")
        
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
            
            days.append(DayPrediction(day_name=day_name, date=str(date_val), hours=hours))
        
        demand_output = DemandOutput(
            restaurant_name=request.demand_input.place.place_name,
            prediction_period=f"{request.demand_input.prediction_start_date} to {days[-1].date}",
            days=days
        )
        
        return PredictionResponse(demand_output=demand_output, schedule_output=schedule_output)
        
    except Exception as e:
        logger.error(f"Request failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)