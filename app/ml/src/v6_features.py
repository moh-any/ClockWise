"""
Feature List Reference
======================
Complete list of all 69 features expected by v6 model.
Use this as a reference when debugging or extending the model.
"""

# V6 Model Features (69 total)
V6_MODEL_FEATURES = [
    # ===== BASIC FEATURES (13) =====
    'place_id',              # Venue identifier (hashed)
    'hour',                  # Hour of day (0-23)
    'day_of_week',           # Day of week (0=Mon, 6=Sun)
    'month',                 # Month (1-12)
    'week_of_year',          # Week number in year
    'type_id',               # Venue type (bar, cafe, restaurant, etc.)
    'waiting_time',          # Average wait time in minutes
    'rating',                # Venue rating (0-5)
    'delivery',              # Delivery available (0/1)
    'accepting_orders',      # Currently accepting orders (0/1)
    'total_campaigns',       # Number of active campaigns
    'avg_discount',          # Average discount percentage
    'is_holiday',            # Is it a holiday? (0/1)
    
    # ===== BASIC LAG FEATURES (5) =====
    'prev_hour_items',       # Items sold previous hour
    'prev_day_items',        # Items sold 24 hours ago
    'prev_week_items',       # Items sold 7 days ago
    'prev_month_items',      # Items sold 30 days ago (approximation)
    'rolling_7d_avg_items',  # 7-day rolling average
    
    # ===== BASIC WEATHER FEATURES (16) =====
    'temperature_2m',        # Temperature at 2m height (°C)
    'relative_humidity_2m',  # Relative humidity (%)
    'precipitation',         # Total precipitation (mm)
    'rain',                  # Rain amount (mm)
    'snowfall',              # Snowfall amount (cm)
    'weather_code',          # WMO weather code
    'cloud_cover',           # Cloud coverage (%)
    'wind_speed_10m',        # Wind speed at 10m (km/h)
    'is_rainy',              # Is it raining? (0/1)
    'is_snowy',              # Is it snowing? (0/1)
    'is_cold',               # Is it cold? (<10°C) (0/1)
    'is_hot',                # Is it hot? (>25°C) (0/1)
    'is_cloudy',             # Is it cloudy? (>70%) (0/1)
    'is_windy',              # Is it windy? (>20 km/h) (0/1)
    'good_weather',          # Overall good weather indicator (0/1)
    'weather_severity',      # Composite weather severity score
    
    # ===== CYCLICAL TIME FEATURES (6) =====
    'hour_sin',              # Hour sine encoding
    'hour_cos',              # Hour cosine encoding
    'day_of_week_sin',       # Day of week sine encoding
    'day_of_week_cos',       # Day of week cosine encoding
    'month_sin',             # Month sine encoding
    'month_cos',             # Month cosine encoding
    
    # ===== TIME CONTEXT INDICATORS (21) =====
    'is_breakfast_rush',     # 7-9 AM
    'is_lunch_rush',         # 11 AM - 1 PM
    'is_peak_lunch',         # 12-2 PM (narrower window)
    'is_dinner_rush',        # 6-8 PM
    'is_peak_dinner',        # 5-7 PM (includes problematic 4-5 PM)
    'is_late_night',         # 10 PM - 2 AM
    'is_midnight_zone',      # 11 PM - 1 AM (problematic hours 0, 23)
    'is_early_morning',      # 6-8 AM
    'is_afternoon',          # 2-5 PM
    'is_evening',            # 5-9 PM
    'is_weekend',            # Saturday or Sunday (0/1)
    'is_friday',             # Friday (0/1)
    'is_saturday',           # Saturday (0/1)
    'is_sunday',             # Sunday (0/1)
    'friday_evening',        # Friday after 5 PM (0/1)
    'saturday_evening',      # Saturday after 5 PM (0/1)
    'weekend_lunch',         # Weekend 11 AM - 2 PM (0/1)
    'weekend_dinner',        # Weekend 5-8 PM (0/1)
    'weekday_lunch',         # Weekday 11 AM - 2 PM (0/1)
    'weekday_dinner',        # Weekday 5-8 PM (0/1)
    'is_month_start',        # First 5 days of month (0/1)
    'is_month_end',          # Last week of month (0/1)
    
    # ===== ADDITIONAL LAG FEATURES (7) =====
    'rolling_3d_avg_items',  # 3-day rolling average
    'rolling_14d_avg_items', # 14-day rolling average
    'rolling_30d_avg_items', # 30-day rolling average
    'rolling_7d_std_items',  # 7-day rolling standard deviation (volatility)
    'demand_trend_7d',       # 7-day trend slope
    'lag_same_hour_last_week',    # Same hour last week
    'lag_same_hour_2_weeks',      # Same hour 2 weeks ago
    
    # ===== VENUE-SPECIFIC FEATURES (7) =====
    'venue_hour_avg',        # Venue's avg demand at this hour
    'venue_dow_avg',         # Venue's avg demand on this day of week
    'venue_volatility',      # Venue's demand standard deviation
    'venue_total_items',     # Venue's total historical items
    'venue_growth_recent_vs_historical',  # Recent growth ratio (7d/30d)
    'venue_peak_hour',       # Venue's peak hour (numeric 0-23)
    'is_venue_peak_hour',    # Is this the venue's peak hour? (0/1)
    
    # ===== WEEKEND-SPECIFIC FEATURES (6) =====
    'venue_weekend_avg',     # Venue's average weekend demand
    'venue_weekday_avg',     # Venue's average weekday demand
    'venue_weekend_lift',    # Weekend/weekday demand ratio
    'last_weekend_same_hour', # Last weekend's demand at this hour
    'venue_weekend_volatility', # Weekend demand standard deviation
    'weekend_day_position',  # Position in weekend (Fri=0, Sat=1, Sun=2, else=-1)
    
    # ===== WEATHER INTERACTION FEATURES (8) =====
    'feels_like_temp',       # Apparent temperature (temp - wind + humidity effects)
    'bad_weather_score',     # Composite bad weather indicator (0-1)
    'temp_change_1h',        # Temperature change from 1 hour ago
    'temp_change_3h',        # Temperature change from 3 hours ago
    'weather_getting_worse', # Is weather deteriorating? (0/1)
    'weekend_good_weather',  # Weekend × good weather interaction
    'rush_bad_weather',      # (Lunch/dinner rush) × bad weather interaction
    'cold_evening',          # Cold × evening interaction
]


def print_feature_summary():
    """Print feature breakdown by category"""
    categories = {
        'Basic Features': 13,
        'Basic Lag Features': 5,
        'Basic Weather Features': 16,
        'Cyclical Time Features': 6,
        'Time Context Indicators': 21,
        'Additional Lag Features': 7,
        'Venue-Specific Features': 7,
        'Weekend-Specific Features': 6,
        'Weather Interaction Features': 8,
    }
    
    print("="*60)
    print("V6 MODEL FEATURE BREAKDOWN")
    print("="*60)
    
    total = 0
    for category, count in categories.items():
        print(f"{category:.<40} {count:>3}")
        total += count
    
    print("-"*60)
    print(f"{'TOTAL':.<40} {total:>3}")
    print("="*60)


def validate_feature_list(df_columns):
    """
    Validate that a DataFrame has all required features.
    
    Args:
        df_columns: List or Index of column names
        
    Returns:
        tuple: (is_valid, missing_features, extra_features)
    """
    df_cols_set = set(df_columns)
    model_cols_set = set(V6_MODEL_FEATURES)
    
    missing = model_cols_set - df_cols_set
    extra = df_cols_set - model_cols_set
    is_valid = len(missing) == 0
    
    return is_valid, sorted(missing), sorted(extra)


if __name__ == "__main__":
    print_feature_summary()
    print(f"\nTotal features defined: {len(V6_MODEL_FEATURES)}")
    print(f"\nFeature names:")
    for i, feature in enumerate(V6_MODEL_FEATURES, 1):
        print(f"  {i:2}. {feature}")
