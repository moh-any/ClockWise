"""
Restaurant Demand Prediction & Scheduling API v3.0
====================================================
FastAPI-based REST API for:
1. Predicting hourly restaurant demand (item_count & order_count)
2. Generating optimal staff schedules based on demand and employee preferences

Changes from v2.0:
- Restructured request/response format with demand_input and schedule_input
- Added missing scheduler parameters (max_hours_per_week, max_consec_slots, pref_hours, is_independent)
- Added production chains support
- Added scheduler configuration
- Updated output format for schedule_output
- Fixed all inconsistencies with weather/holiday API integration
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Union
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
    from src.weather_api import get_weather_for_demand_data
    WEATHER_API_AVAILABLE = True
    logger.info("Weather API imported successfully")
except ImportError as e:
    WEATHER_API_AVAILABLE = False
    logger.warning(f"Weather API not available: {e}")

# Holiday API
try:
    from src.holiday_api import add_holiday_feature
    HOLIDAY_API_AVAILABLE = True
    logger.info("Holiday API imported successfully")
except ImportError as e:
    HOLIDAY_API_AVAILABLE = False
    logger.warning(f"Holiday API not available: {e}")

# Scheduler
try:
    from src.scheduler_cpsat import SchedulerCPSAT, SchedulerInput, Employee, Role, ProductionChain, Shift
    SCHEDULER_AVAILABLE = True
    logger.info("Scheduler imported successfully")
except ImportError as e:
    SCHEDULER_AVAILABLE = False
    logger.warning(f"Scheduler not available: {e}")


# ============================================================================
# INITIALIZE FASTAPI APP
# ============================================================================

app = FastAPI(
    title="Restaurant Demand Prediction & Scheduling API",
    description="Predict hourly demand and generate optimal staff schedules",
    version="3.0.0",
    docs_url="/docs",
    redoc_url=None,  # Disable default redoc
    openapi_url="/openapi.json"
)

# Add custom ReDoc endpoint with reliable CDN
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


# ============================================================================
# REQUEST MODELS - DEMAND INPUT
# ============================================================================

class OpeningHoursDay(BaseModel):
    """Opening hours for a specific day - supports both open and closed states"""
    from_time: Optional[str] = Field(None, alias="from", description="Opening time (HH:MM)")
    to: Optional[str] = Field(None, description="Closing time (HH:MM)")
    closed: Optional[bool] = Field(None, description="True if closed this day")

    class Config:
        populate_by_name = True


class PlaceData(BaseModel):
    """Restaurant/Place information"""
    place_id: str = Field(..., description="Unique place identifier")
    place_name: str = Field(..., description="Restaurant name")
    type: str = Field(..., description="Place type (e.g., 'restaurant')")
    latitude: float = Field(..., description="Latitude coordinate")
    longitude: float = Field(..., description="Longitude coordinate")
    waiting_time: Optional[int] = Field(None, description="Average waiting time in minutes")
    receiving_phone: bool = Field(..., description="Accepts phone orders")
    delivery: bool = Field(..., description="Offers delivery")
    opening_hours: Dict[str, OpeningHoursDay] = Field(..., description="Opening hours per day")
    fixed_shifts: bool = Field(True, description="Whether to use fixed shifts for scheduling")
    number_of_shifts_per_day: int = Field(3, description="Number of shifts per day")
    shift_times: List[str] = Field(..., description="Shift time ranges (e.g., '06:00-14:00')")
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


class DemandInput(BaseModel):
    """Input for demand prediction"""
    place: PlaceData
    orders: List[OrderData] = Field(..., description="Historical orders (at least 7 days recommended)")
    campaigns: List[CampaignData] = Field(default=[], description="Active/past campaigns")
    prediction_start_date: str = Field(..., description="Start date for predictions (YYYY-MM-DD)")
    prediction_days: int = Field(7, description="Number of days to predict (default: 7)")


# ============================================================================
# REQUEST MODELS - SCHEDULE INPUT
# ============================================================================

class RoleData(BaseModel):
    """Role definition"""
    role_id: str = Field(..., description="Unique role identifier")
    role_name: str = Field(..., description="Role display name")
    producing: bool = Field(..., description="Whether role produces items")
    items_per_employee_per_hour: Optional[float] = Field(None, description="Production rate if producing")
    min_present: int = Field(0, description="Minimum employees required for this role")
    is_independent: bool = Field(True, description="Whether role is independent or part of a chain")


class EmployeeHours(BaseModel):
    """Available/preferred hours for a specific day"""
    from_time: str = Field(..., alias="from", description="Start time (HH:MM)")
    to: str = Field(..., description="End time (HH:MM)")

    class Config:
        populate_by_name = True


class EmployeeData(BaseModel):
    """Employee information"""
    employee_id: str = Field(..., description="Unique employee identifier")
    role_ids: List[str] = Field(..., description="List of role IDs this employee can perform")
    available_days: List[str] = Field(..., description="Days employee is available")
    preferred_days: List[str] = Field(..., description="Preferred working days")
    available_hours: Dict[str, EmployeeHours] = Field(..., description="Available hours per day")
    preferred_hours: Dict[str, EmployeeHours] = Field(..., description="Preferred hours per day")
    hourly_wage: float = Field(..., description="Hourly wage rate")
    max_hours_per_week: float = Field(40.0, description="Maximum hours per week")
    max_consec_slots: int = Field(8, description="Maximum consecutive slots")
    pref_hours: float = Field(32.0, description="Preferred weekly hours")


class ProductionChainData(BaseModel):
    """Production chain definition (e.g., prep -> cook -> serve)"""
    chain_id: str = Field(..., description="Unique chain identifier")
    role_ids: List[str] = Field(..., description="Ordered list of role IDs in the chain")
    contrib_factor: float = Field(1.0, description="Contribution factor to supply")


class SchedulerConfig(BaseModel):
    """Scheduler configuration parameters"""
    slot_len_hour: float = Field(1.0, description="Length of each time slot in hours")
    min_rest_slots: int = Field(2, description="Minimum rest slots between shifts")
    min_shift_length_slots: int = Field(2, description="Minimum shift length in slots")
    meet_all_demand: bool = Field(False, description="Whether to enforce demand as hard constraint")


class ScheduleInput(BaseModel):
    """Input for schedule generation"""
    roles: List[RoleData]
    employees: List[EmployeeData]
    production_chains: List[ProductionChainData] = Field(default=[], description="Production chains")
    scheduler_config: Optional[SchedulerConfig] = Field(None, description="Scheduler configuration")


# ============================================================================
# COMPLETE REQUEST MODEL
# ============================================================================

class PredictionRequest(BaseModel):
    """Complete prediction and scheduling request"""
    demand_input: DemandInput
    schedule_input: ScheduleInput


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
    day_name: str = Field(..., description="Day name (monday, tuesday, etc.)")
    date: str = Field(..., description="Date (YYYY-MM-DD)")
    hours: List[HourPrediction] = Field(..., description="Hourly predictions")


class DemandOutput(BaseModel):
    """Demand prediction output"""
    restaurant_name: str
    prediction_period: str
    days: List[DayPrediction]


class ScheduleOutput(BaseModel):
    """Schedule output - organized by day and shift"""
    monday: List[Dict[str, List[str]]] = Field(default=[], description="Monday shifts")
    tuesday: List[Dict[str, List[str]]] = Field(default=[], description="Tuesday shifts")
    wednesday: List[Dict[str, List[str]]] = Field(default=[], description="Wednesday shifts")
    thursday: List[Dict[str, List[str]]] = Field(default=[], description="Thursday shifts")
    friday: List[Dict[str, List[str]]] = Field(default=[], description="Friday shifts")
    saturday: List[Dict[str, List[str]]] = Field(default=[], description="Saturday shifts")
    sunday: List[Dict[str, List[str]]] = Field(default=[], description="Sunday shifts")


class PredictionResponse(BaseModel):
    """Complete prediction and scheduling response"""
    demand_output: DemandOutput
    schedule_output: ScheduleOutput


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


# ============================================================================
# FALLBACK FUNCTIONS FOR MISSING APIS
# ============================================================================

def add_weather_features_mock(df: pd.DataFrame) -> pd.DataFrame:
    """Add mock weather features (fallback when API unavailable)"""
    weather_defaults = {
        'temperature_2m': 15.0,
        'relative_humidity_2m': 70.0,
        'precipitation': 0.1,
        'rain': 0.1,
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
    """Add mock holiday feature (fallback when API unavailable)"""
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
    """
    Complete feature engineering pipeline for prediction
    
    Pipeline steps:
    1. Process historical orders
    2. Aggregate to hourly level
    3. Add time features
    4. Create future prediction windows
    5. Combine historical + future for lag calculation
    6. Add place features
    7. Add campaign features
    8. Add weather features (with fallback)
    9. Add holiday features (with fallback)
    10. Clean up intermediate columns
    
    Returns:
        DataFrame ready for model prediction
    """
    logger.info("Starting feature preparation pipeline...")
    
    # Step 1-3: Process historical data
    logger.info("Processing historical orders...")
    orders_df = process_historical_orders(orders, place.place_id)
    hourly_hist = aggregate_to_hourly(orders_df)
    hourly_hist = add_time_features(hourly_hist)
    hourly_hist = add_lag_features(hourly_hist)
    
    # Step 4: Create future prediction windows
    logger.info(f"Creating prediction windows for {prediction_days} days...")
    future_df = create_prediction_windows(prediction_start, prediction_days, place.place_id)
    
    # Step 5: Combine historical + future for proper lag calculation
    logger.info("Combining historical and future data for lag features...")
    combined = pd.concat([hourly_hist, future_df], ignore_index=True)
    combined = combined.sort_values(['place_id', 'datetime'])
    combined = add_lag_features(combined)
    
    # Filter to only future predictions
    prediction_df = combined[combined['datetime'] >= pd.to_datetime(prediction_start)].copy()
    
    # Step 6: Add place features
    logger.info("Adding place features...")
    type_mapping = {'restaurant': 1, 'cafe': 2, 'bar': 3}
    prediction_df['type_id'] = type_mapping.get(place.type, 1)
    prediction_df['waiting_time'] = place.waiting_time if place.waiting_time else 30
    prediction_df['rating'] = place.rating if place.rating else 4.0
    prediction_df['delivery'] = int(place.delivery)
    prediction_df['accepting_orders'] = int(place.accepting_orders if place.accepting_orders else True)
    
    # Add lat/lon for weather/holiday APIs (will be dropped later)
    prediction_df['latitude'] = place.latitude
    prediction_df['longitude'] = place.longitude
    
    # Step 7: Add campaign features
    logger.info("Adding campaign features...")
    campaign_stats = calculate_campaign_features(campaigns)
    prediction_df['total_campaigns'] = campaign_stats['total_campaigns']
    prediction_df['avg_discount'] = campaign_stats['avg_discount']
    
    # Step 8: Add weather features (with fallback)
    logger.info("Adding weather features...")
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
            logger.info("Weather features added successfully")
        except Exception as e:
            logger.warning(f"Weather API failed: {e}. Using mock data.")
            prediction_df = add_weather_features_mock(prediction_df)
    else:
        logger.warning("Weather API not available. Using mock data.")
        prediction_df = add_weather_features_mock(prediction_df)
    
    # Step 9: Add holiday features (with fallback)
    logger.info("Adding holiday features...")
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
            logger.info("Holiday features added successfully")
        except Exception as e:
            logger.warning(f"Holiday API failed: {e}. Using mock data.")
            prediction_df = add_holiday_features_mock(prediction_df)
    else:
        logger.warning("Holiday API not available. Using mock data.")
        prediction_df = add_holiday_features_mock(prediction_df)
    
    # Step 10: Clean up intermediate columns
    logger.info("Cleaning up intermediate columns...")
    prediction_df = prediction_df.drop(['latitude', 'longitude'], axis=1, errors='ignore')
    
    logger.info(f"Feature preparation complete. Shape: {prediction_df.shape}")
    return prediction_df


def align_features_with_model(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure feature set matches what model expects
    
    Handles:
    - String to numeric place_id conversion (DETERMINISTIC)
    - Missing column filling
    - Dtype conversions
    - Column ordering
    """
    df = df.copy()
    
    # ===== FIX: Use deterministic hash for place_id =====
    if df['place_id'].dtype == 'object' or df['place_id'].dtype == 'string':
        def encode_place_id(place_str):
            """Deterministic hash using MD5"""
            hash_obj = hashlib.md5(str(place_str).encode('utf-8'))
            return float(int(hash_obj.hexdigest()[:8], 16) % 100000)
        
        df['place_id'] = df['place_id'].apply(encode_place_id)
        logger.info(f"Encoded place_id to numeric values (deterministic)")
    
    # Ensure place_id is float
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
    
    # Add missing columns with 0
    for col in expected_features:
        if col not in df.columns:
            logger.warning(f"Missing column '{col}', filling with 0")
            df[col] = 0
    
    # Select only expected features in correct order
    df = df[expected_features].copy()
    
    # Convert dtypes
    df['type_id'] = df['type_id'].astype('float64')
    df['is_holiday'] = df['is_holiday'].astype('int')
    
    # Ensure all columns are string type (for column names)
    df.columns = df.columns.astype(str)
    
    # Verify no NaN values
    if df.isnull().any().any():
        null_cols = df.columns[df.isnull().any()].tolist()
        logger.warning(f"Columns with NaN values: {null_cols}")
        df = df.fillna(0)
    
    return df

# ============================================================================
# SCHEDULER HELPER FUNCTIONS
# ============================================================================

def parse_shift_times(shift_times: List[str], place: PlaceData) -> List[Shift]:
    """
    Parse shift time strings into Shift objects, respecting opening hours
    
    Only creates shifts for days when restaurant is open
    """
    shifts = []
    day_name_to_index = {
        'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
        'friday': 4, 'saturday': 5, 'sunday': 6
    }
    
    for idx, shift_time in enumerate(shift_times):
        parts = shift_time.split('-')
        if len(parts) != 2:
            logger.warning(f"Invalid shift time format: {shift_time}")
            continue
        
        start_str, end_str = parts
        start_hour = parse_time_to_hour(start_str)
        end_hour = parse_time_to_hour(end_str)
        
        if start_hour == -1 or end_hour == -1:
            continue
        
        # Handle overnight shifts (e.g., 22:00-06:00)
        if end_hour <= start_hour:
            end_hour += 24
        
        # Create shift ONLY for days restaurant is open
        for day_name, hours in place.opening_hours.items():
            if hours.closed:
                continue  # Skip closed days
            
            day_idx = day_name_to_index.get(day_name.lower())
            if day_idx is not None:
                shifts.append(Shift(
                    id=f"shift_{day_idx}_{idx}",
                    day=day_idx,
                    start_slot=int(start_hour),
                    end_slot=int(end_hour)
                ))
    
    logger.info(f"Parsed {len(shifts)} shifts from {len(shift_times)} shift times")
    return shifts


def convert_api_data_to_scheduler_input(
    place: PlaceData,
    schedule_input: ScheduleInput,
    demand_predictions: pd.DataFrame,
    prediction_start_date: str
) -> SchedulerInput:
    """
    Convert API request data to scheduler input format
    
    Handles:
    - Role conversion
    - Production chain conversion
    - Employee availability mapping (calendar days -> prediction period days)
    - Demand dictionary building
    - Shift parsing
    """
    
    # Get scheduler config or use defaults
    config = schedule_input.scheduler_config or SchedulerConfig()
    
    # Convert roles
    logger.info("Converting roles...")
    scheduler_roles = []
    for role_data in schedule_input.roles:
        scheduler_roles.append(Role(
            id=role_data.role_id,
            producing=role_data.producing,
            items_per_hour=role_data.items_per_employee_per_hour or 0,
            min_present=role_data.min_present,
            is_independent=role_data.is_independent
        ))
    
    # Convert production chains
    logger.info("Converting production chains...")
    scheduler_chains = []
    for chain_data in schedule_input.production_chains:
        scheduler_chains.append(ProductionChain(
            id=chain_data.chain_id,
            roles=chain_data.role_ids,
            contrib_factor=chain_data.contrib_factor
        ))
    
    # Determine prediction period details
    unique_dates = sorted(demand_predictions['date'].unique())
    num_days = len(unique_dates)
    num_slots_per_day = int(24 / config.slot_len_hour)
    
    # Map calendar days to prediction period days
    prediction_start = pd.to_datetime(prediction_start_date).date()
    calendar_day_to_pred_day = {}
    for i in range(num_days):
        current_date = prediction_start + timedelta(days=i)
        calendar_day_name = current_date.strftime('%A').lower()
        calendar_day_to_pred_day[calendar_day_name] = i
    
    logger.info(f"Prediction period: {num_days} days, {num_slots_per_day} slots/day")
    logger.info(f"Calendar day mapping: {calendar_day_to_pred_day}")
    
    # Convert employees
    logger.info("Converting employees...")
    scheduler_employees = []
    
    for emp_data in schedule_input.employees:
        # Initialize availability dict (default: unavailable for safety)
        availability = {}
        for day_idx in range(num_days):
            for slot in range(num_slots_per_day):
                availability[(day_idx, slot)] = False
        
        # Set available slots to True based on employee's available_days and available_hours
        for calendar_day_name in emp_data.available_days:
            # Map calendar day to prediction period day
            pred_day_idx = calendar_day_to_pred_day.get(calendar_day_name.lower())
            if pred_day_idx is None:
                continue  # Day not in prediction period
            
            # Get hours for this day
            if calendar_day_name.lower() not in emp_data.available_hours:
                continue
            
            hours = emp_data.available_hours[calendar_day_name.lower()]
            start_hour = parse_time_to_hour(hours.from_time)
            end_hour = parse_time_to_hour(hours.to)
            
            if start_hour == -1 or end_hour == -1:
                continue
            
            # Convert hours to slots
            start_slot = int(start_hour / config.slot_len_hour)
            end_slot = int(end_hour / config.slot_len_hour)
            if end_hour % config.slot_len_hour > 0:
                end_slot += 1
            
            # Mark slots as available
            for slot in range(start_slot, min(end_slot, num_slots_per_day)):
                availability[(pred_day_idx, slot)] = True
        
        # Build preferences (similar logic)
        preferences = {}
        for calendar_day_name in emp_data.preferred_days:
            pred_day_idx = calendar_day_to_pred_day.get(calendar_day_name.lower())
            if pred_day_idx is None:
                continue
            
            if calendar_day_name.lower() not in emp_data.preferred_hours:
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
    
    # Build demand dict from predictions
    logger.info("Building demand dictionary...")
    date_to_day_idx = {d: i for i, d in enumerate(unique_dates)}
    demand_dict = {}
    
    for _, row in demand_predictions.iterrows():
        # Get date (handle both date and datetime types)
        row_date = row['datetime'].date() if hasattr(row['datetime'], 'date') else row['date']
        day_idx = date_to_day_idx.get(row_date)
        
        if day_idx is None:
            continue
        
        hour = row['hour']
        slot = int(hour / config.slot_len_hour)
        demand_dict[(day_idx, slot)] = float(row['item_count'])
    
    logger.info(f"Built demand dict with {len(demand_dict)} entries")
    
    # Parse shifts if fixed_shifts is True
    shifts = []
    if place.fixed_shifts:
        logger.info("Parsing fixed shifts...")
        shifts = parse_shift_times(place.shift_times, place)
    
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


def format_schedule_output(
    solution: Dict, 
    place: PlaceData, 
    config: SchedulerConfig,
    prediction_start_date: str,
    num_days: int
) -> ScheduleOutput:
    """
    Format scheduler solution to match API output format
    
    Converts scheduler solution into day-based schedule with shift time ranges
    """
    day_names = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    
    # Map prediction day indices to calendar day names
    prediction_start = pd.to_datetime(prediction_start_date).date()
    pred_day_to_calendar = {}
    for i in range(num_days):
        current_date = prediction_start + timedelta(days=i)
        calendar_day_name = current_date.strftime('%A').lower()
        pred_day_to_calendar[i] = calendar_day_name
    
    # Initialize schedule output
    schedule_by_day = {day: [] for day in day_names}
    
    if not solution or 'schedule' not in solution:
        return ScheduleOutput(**schedule_by_day)
    
    if place.fixed_shifts:
        # Group by day and shift
        shift_assignments = {}
        for entry in solution['schedule']:
            shift_id = entry.get('shift')
            if not shift_id:
                continue
            
            if shift_id not in shift_assignments:
                shift_assignments[shift_id] = []
            shift_assignments[shift_id].append(entry['employee'])
        
        # Organize by day
        for entry in solution['schedule']:
            shift_id = entry.get('shift')
            if not shift_id:
                continue
            
            # Parse shift to get time range
            pred_day_idx = entry['day']
            calendar_day = pred_day_to_calendar.get(pred_day_idx)
            if not calendar_day:
                continue
            
            # Find matching shift time from place.shift_times
            start_slot = entry.get('start_slot', 0)
            end_slot = entry.get('end_slot', 0)
            start_hour = int(start_slot * config.slot_len_hour)
            end_hour = int(end_slot * config.slot_len_hour)
            
            # Handle overnight shifts
            if end_hour > 24:
                end_hour = end_hour % 24
            
            shift_key = f"{start_hour:02d}:00-{end_hour:02d}:00"
            
            # Check if this shift already exists for this day
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
    
    else:
        # Slot-based scheduling - group consecutive slots into shifts
        schedule_dict = {}
        for entry in solution['schedule']:
            pred_day_idx = entry['day']
            slot = entry['slot']
            employee = entry['employee']
            
            key = (pred_day_idx, employee)
            if key not in schedule_dict:
                schedule_dict[key] = []
            schedule_dict[key].append(slot)
        
        # Convert to shift format
        shift_groups = {}
        for (pred_day_idx, employee), slots in schedule_dict.items():
            slots = sorted(slots)
            
            # Group consecutive slots
            current_shift_start = slots[0]
            current_shift_end = slots[0] + 1
            
            for i in range(1, len(slots)):
                if slots[i] == current_shift_end:
                    current_shift_end = slots[i] + 1
                else:
                    # End current shift
                    start_hour = int(current_shift_start * config.slot_len_hour)
                    end_hour = int(current_shift_end * config.slot_len_hour)
                    shift_key = f"{start_hour:02d}:00-{end_hour:02d}:00"
                    
                    if (pred_day_idx, shift_key) not in shift_groups:
                        shift_groups[(pred_day_idx, shift_key)] = []
                    shift_groups[(pred_day_idx, shift_key)].append(employee)
                    
                    # Start new shift
                    current_shift_start = slots[i]
                    current_shift_end = slots[i] + 1
            
            # Add last shift
            start_hour = int(current_shift_start * config.slot_len_hour)
            end_hour = int(current_shift_end * config.slot_len_hour)
            shift_key = f"{start_hour:02d}:00-{end_hour:02d}:00"
            
            if (pred_day_idx, shift_key) not in shift_groups:
                shift_groups[(pred_day_idx, shift_key)] = []
            shift_groups[(pred_day_idx, shift_key)].append(employee)
        
        # Organize by calendar day
        for (pred_day_idx, shift_key), employees in shift_groups.items():
            calendar_day = pred_day_to_calendar.get(pred_day_idx)
            if calendar_day:
                schedule_by_day[calendar_day].append({shift_key: employees})
    
    return ScheduleOutput(**schedule_by_day)


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/")
def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "model_loaded": model is not None,
        "scheduler_available": SCHEDULER_AVAILABLE,
        "weather_api_available": WEATHER_API_AVAILABLE,
        "holiday_api_available": HOLIDAY_API_AVAILABLE,
        "version": "3.0.0"
    }


@app.get("/model/info")
def model_info():
    """Get model metadata"""
    if metadata is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    return metadata


@app.post("/predict", response_model=PredictionResponse)
def predict_demand_and_schedule(request: PredictionRequest):
    """
    Main prediction and scheduling endpoint
    
    Process:
    1. Validate input
    2. Prepare features for demand prediction
    3. Make demand predictions using ML model
    4. Generate optimal staff schedule based on predictions
    5. Format and return response
    """
    
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        # ===== STEP 1: DEMAND PREDICTION =====
        logger.info(f"Processing prediction request for {request.demand_input.place.place_name}")
        
        # Prepare features
        features_df = prepare_features_for_prediction(
            place=request.demand_input.place,
            orders=request.demand_input.orders,
            campaigns=request.demand_input.campaigns,
            prediction_start=request.demand_input.prediction_start_date,
            prediction_days=request.demand_input.prediction_days
        )
        
        # Store datetime info before feature alignment
        datetime_info = features_df[['datetime', 'date', 'hour']].copy()
        
        # Align features with model expectations
        X = align_features_with_model(features_df)
        
        # Make predictions
        logger.info(f"Making predictions for {len(X)} hours...")
        predictions = model.predict(X)
        predictions = np.maximum(predictions, 0).round().astype(int)
        
        # Add predictions to datetime info
        datetime_info['item_count'] = predictions[:, 0]
        datetime_info['order_count'] = predictions[:, 1]
        datetime_info['day_name'] = datetime_info['datetime'].dt.strftime('%A').str.lower()
        
        logger.info("Demand predictions completed successfully")
        
        # ===== STEP 2: STAFF SCHEDULING =====
        schedule_output = ScheduleOutput()
        
        if SCHEDULER_AVAILABLE and request.schedule_input.employees and request.schedule_input.roles:
            logger.info("Generating staff schedule...")
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
                    logger.info("Schedule generated successfully")
                else:
                    logger.warning("Scheduler found no solution")
                    
            except Exception as e:
                logger.error(f"Scheduling failed: {e}", exc_info=True)
        else:
            logger.warning("Scheduler not available or no employee/role data provided")
        
        # ===== STEP 3: FORMAT RESPONSE =====
        logger.info("Formatting response...")
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
            restaurant_name=request.demand_input.place.place_name,
            prediction_period=f"{request.demand_input.prediction_start_date} to {days[-1].date}",
            days=days
        )
        
        response = PredictionResponse(
            demand_output=demand_output,
            schedule_output=schedule_output
        )
        
        logger.info("Request completed successfully")
        return response
        
    except Exception as e:
        logger.error(f"Request failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Request failed: {str(e)}")


@app.get("/example-request")
def get_example_request():
    """Get an example request JSON matching the v3.0 structure"""
    return {
        "demand_input": {
            "place": {
                "place_id": "pl_12345",
                "place_name": "Pizza Paradise",
                "type": "restaurant",
                "latitude": 55.6761,
                "longitude": 12.5683,
                "waiting_time": 30,
                "receiving_phone": True,
                "delivery": True,
                "opening_hours": {
                    "monday": {"from": "10:00", "to": "23:00"},
                    "tuesday": {"from": "10:00", "to": "23:00"},
                    "wednesday": {"from": "10:00", "to": "23:00"},
                    "thursday": {"from": "10:00", "to": "23:00"},
                    "friday": {"from": "10:00", "to": "23:00"},
                    "saturday": {"from": "10:00", "to": "23:00"},
                    "sunday": {"closed": True}
                },
                "fixed_shifts": True,
                "number_of_shifts_per_day": 3,
                "shift_times": ["06:00-14:00", "14:00-22:00", "22:00-06:00"],
                "rating": 4.5,
                "accepting_orders": True
            },
            "orders": [
                {
                    "time": "2024-01-01T12:30:00",
                    "items": 3,
                    "status": "completed",
                    "total_amount": 45.5,
                    "discount_amount": 5.0
                },
                {
                    "time": "2024-01-01T13:15:00",
                    "items": 2,
                    "status": "completed",
                    "total_amount": 32.0,
                    "discount_amount": 0.0
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
        },
        "schedule_input": {
            "roles": [
                {
                    "role_id": "role_001",
                    "role_name": "Chef",
                    "producing": True,
                    "items_per_employee_per_hour": 15.0,
                    "min_present": 2,
                    "is_independent": False
                },
                {
                    "role_id": "role_002",
                    "role_name": "Pizza Maker",
                    "producing": True,
                    "items_per_employee_per_hour": 12.0,
                    "min_present": 1,
                    "is_independent": False
                },
                {
                    "role_id": "role_003",
                    "role_name": "Cashier",
                    "producing": False,
                    "items_per_employee_per_hour": None,
                    "min_present": 1,
                    "is_independent": True
                }
            ],
            "employees": [
                {
                    "employee_id": "emp_001",
                    "role_ids": ["role_001", "role_002"],
                    "available_days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
                    "preferred_days": ["monday", "wednesday", "friday"],
                    "available_hours": {
                        "monday": {"from": "10:00", "to": "22:00"},
                        "tuesday": {"from": "10:00", "to": "22:00"},
                        "wednesday": {"from": "10:00", "to": "22:00"},
                        "thursday": {"from": "10:00", "to": "22:00"},
                        "friday": {"from": "10:00", "to": "22:00"}
                    },
                    "preferred_hours": {
                        "monday": {"from": "14:00", "to": "22:00"},
                        "wednesday": {"from": "14:00", "to": "22:00"},
                        "friday": {"from": "14:00", "to": "22:00"}
                    },
                    "hourly_wage": 25.5,
                    "max_hours_per_week": 40.0,
                    "max_consec_slots": 8,
                    "pref_hours": 32.0
                }
            ],
            "production_chains": [
                {
                    "chain_id": "kitchen_chain",
                    "role_ids": ["role_001", "role_002"],
                    "contrib_factor": 1.0
                }
            ],
            "scheduler_config": {
                "slot_len_hour": 1.0,
                "min_rest_slots": 2,
                "min_shift_length_slots": 2,
                "meet_all_demand": False
            }
        }
    }


# ============================================================================
# RUN SERVER
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)