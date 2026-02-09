"""
Real-time Data Collector for Surge Detection - Layer 1
Collects actual orders, predictions, and social signals every 5 minutes.
"""

import sys
from pathlib import Path

# Add parent directory to path to enable src imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
import joblib
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

from src.social_media_apis import get_social_aggregator
import requests


class RealTimeDataCollector:
    """
    Collects and aggregates real-time data from multiple sources.
    Runs as background service (Celery task or separate process).
    
    Data Sources:
    1. Actual orders (from database or POS system)
    2. Demand predictions (from ML model)
    3. Social media signals (from APIs)
    
    Output: Returns collected data via API for backend team to store
    """
    
    def __init__(self, 
                 model_path: str = "data/models/rf_model.joblib",
                 update_interval_seconds: int = 300,
                 demo_mode: bool = False,
                 enable_monitoring: bool = True,
                 auto_maintain: bool = False,
                 maintenance_check_interval_hours: int = 6):
        """
        Initialize data collector.
        
        Args:
            model_path: Path to trained prediction model
            update_interval_seconds: Collection interval (default 5 minutes)
            demo_mode: If True, use simulated social media data
            enable_monitoring: If True, log predictions vs actuals for model maintenance
            auto_maintain: If True, automatically check and run model maintenance
            maintenance_check_interval_hours: How often to check for maintenance needs (default 6 hours)
        """
        self.update_interval = update_interval_seconds
        self.demo_mode = demo_mode
        self.enable_monitoring = enable_monitoring
        self.auto_maintain = auto_maintain
        self.maintenance_check_interval = timedelta(hours=maintenance_check_interval_hours)
        self._last_maintenance_check = None
        
        # Initialize social media aggregator
        self.social = get_social_aggregator(demo_mode=demo_mode)
        
        # Initialize model monitor for logging predictions vs actuals
        self.monitor = None
        if enable_monitoring:
            try:
                from src.model_monitor import ModelMonitor
                self.monitor = ModelMonitor()
                print(f"✅ Model monitor initialized for performance tracking")
            except Exception as e:
                print(f"⚠️  Could not initialize model monitor: {e}")
        
        if auto_maintain:
            print(f"🔧 Auto-maintenance enabled (check every {maintenance_check_interval_hours}h)")
        
        # Load ML model for predictions
        self.model = None
        self.model_path = Path(model_path)
        if self.model_path.exists():
            try:
                self.model = joblib.load(self.model_path)
                print(f"✅ ML model loaded from {model_path}")
            except Exception as e:
                print(f"⚠️  Could not load model: {e}")
                print("   Predictions will use fallback method")
        else:
            print(f"⚠️  Model not found at {model_path}")
        
        print(f"🔄 Data collector initialized (interval: {update_interval_seconds}s)")
    
    def _fetch_bulk_data(self, place_id: str, timestamp: datetime, 
                         time_window_hours: int = 1) -> Optional[Dict]:
        """
        Fetch ALL data needed for surge detection in a single API call.
        
        Calls: POST /api/v1/surge/bulk-data
        
        This bulk endpoint should return venue details, campaigns, orders, 
        and predictions in one response for efficiency.
        
        Args:
            place_id: Venue ID (UUID string)
            timestamp: Reference timestamp
            time_window_hours: Hours of historical data to fetch
        
        Returns:
            Bulk data dict or None if API unavailable
        """
        try:
            response = requests.post(
                "http://localhost:8000/api/v1/surge/bulk-data",
                json={
                    "place_id": place_id,
                    "timestamp": timestamp.isoformat(),
                    "time_window_hours": time_window_hours
                },
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"⚠️  Bulk data API returned {response.status_code}")
                return None
                
        except Exception as e:
            print(f"⚠️  Could not fetch bulk data via API: {e}")
            return None
    
    def collect_actual_orders(self, 
                              place_id: str, 
                              time_window: timedelta) -> Dict[datetime, Dict[str, int]]:
        """
        Query actual orders via bulk data endpoint.
        
        Args:
            place_id: Venue ID
            time_window: Look-back period (e.g., last 1 hour)
        
        Returns:
            Dict mapping timestamp -> {item_count: int, order_count: int}
        """
        # Try bulk data endpoint first
        bulk_data = self._fetch_bulk_data(
            place_id=place_id,
            timestamp=datetime.now(),
            time_window_hours=int(time_window.total_seconds() / 3600)
        )
        
        if bulk_data and 'orders' in bulk_data:
            # Convert string timestamps to datetime if needed
            orders = bulk_data['orders']
            if orders and isinstance(list(orders.keys())[0], str):
                return {
                    datetime.fromisoformat(ts): data
                    for ts, data in orders.items()
                }
            return orders
        
        # Fallback to simulated data
        print("   Falling back to simulated order data")
        return self._simulate_actual_orders(place_id, time_window)
    
    def _simulate_actual_orders(self, 
                                place_id: str, 
                                time_window: timedelta) -> Dict[datetime, Dict[str, int]]:
        """
        Simulate actual order data for testing.
        In production, replace with real database query.
        """
        results = {}
        now = datetime.now()
        
        # Generate hourly data for the time window
        hours = int(time_window.total_seconds() / 3600)
        
        for hour_offset in range(hours):
            timestamp = now - timedelta(hours=hour_offset)
            timestamp = timestamp.replace(minute=0, second=0, microsecond=0)
            
            # Simulate order volumes (baseline + random variation)
            base_items = 100
            base_orders = 25
            
            # Add time-of-day pattern
            hour_of_day = timestamp.hour
            if 11 <= hour_of_day <= 13:  # Lunch peak
                multiplier = 2.0
            elif 18 <= hour_of_day <= 20:  # Dinner peak
                multiplier = 2.5
            else:
                multiplier = 1.0
            
            # Add random variation
            variation = np.random.uniform(0.8, 1.2)
            
            results[timestamp] = {
                'item_count': int(base_items * multiplier * variation),
                'order_count': int(base_orders * multiplier * variation)
            }
        
        return results
    
    def collect_predictions(self, 
                           place_id: str, 
                           time_window: timedelta) -> Dict[datetime, Dict[str, float]]:
        """
        Get demand predictions via bulk data endpoint.
        
        Args:
            place_id: Venue ID
            time_window: Time period to predict for
        
        Returns:
            Dict mapping timestamp -> {item_count_pred: float, order_count_pred: float}
        """
        # Try bulk data endpoint first
        bulk_data = self._fetch_bulk_data(
            place_id=place_id,
            timestamp=datetime.now(),
            time_window_hours=int(time_window.total_seconds() / 3600)
        )
        
        if bulk_data and 'predictions' in bulk_data:
            # Convert string timestamps to datetime if needed
            predictions = bulk_data['predictions']
            if predictions and isinstance(list(predictions.keys())[0], str):
                return {
                    datetime.fromisoformat(ts): data
                    for ts, data in predictions.items()
                }
            return predictions
        
        # Fall back to model-based predictions
        print("   Falling back to model-based predictions")
        return self._predict_with_model(place_id, time_window)
    
    def _predict_with_model(self, 
                           place_id: str, 
                           time_window: timedelta) -> Dict[datetime, Dict[str, float]]:
        """
        Generate predictions using the loaded ML model.
        
        Builds feature vectors matching the training data format and uses
        the model to generate predictions.
        """
        if self.model is None:
            print("⚠️  Model not loaded, returning baseline predictions")
            return self._baseline_predictions(time_window)
        
        predictions = {}
        now = datetime.now()
        hours = int(time_window.total_seconds() / 3600)
        
        for hour_offset in range(hours):
            timestamp = now - timedelta(hours=hour_offset)
            timestamp = timestamp.replace(minute=0, second=0, microsecond=0)
            
            try:
                # Build feature vector matching training format
                features = self._build_feature_vector(place_id, timestamp)
                
                # Make prediction (features is now a DataFrame)
                pred = self.model.predict(features)
                
                predictions[timestamp] = {
                    'item_count_pred': float(pred[0][0]),
                    'order_count_pred': float(pred[0][1])
                }
            except Exception as e:
                print(f"⚠️  Prediction error for {timestamp}: {e}")
                predictions[timestamp] = {
                    'item_count_pred': 100.0,
                    'order_count_pred': 25.0
                }
        
        return predictions
    
    def _build_feature_vector(self, place_id: str, timestamp: datetime) -> np.ndarray:
        """
        Build feature vector matching training data format with real data.
        
        Collects features from:
        - Bulk data API (venue, campaigns, historical orders) - SINGLE CALL
        - Holiday API (is_holiday) - external service
        - Weather API (weather features) - external service
        
        Features match those in train_model.py's x.columns exactly.
        """
        # Time-based features
        day_of_week = timestamp.weekday()
        hour = timestamp.hour
        month = timestamp.month
        week_of_year = timestamp.isocalendar()[1]
        
        # Fetch all backend data in ONE API call
        bulk_data = self._fetch_bulk_data(
            place_id=place_id,
            timestamp=timestamp,
            time_window_hours=720  # 30 days for lag features
        )
        
        # 1. Extract venue features from bulk data
        venue_features = self._extract_venue_features(bulk_data)
        
        # 2. Extract campaign features from bulk data
        campaign_features = self._extract_campaign_features(bulk_data)
        
        # 3. Extract lag features from bulk data
        lag_features = self._extract_lag_features(bulk_data, timestamp)
        
        # 4. Get holiday status (external API)
        is_holiday = self._get_holiday_status(timestamp)
        
        # 5. Get weather features (external API)
        weather_features = self._get_weather_features(timestamp)
        
        # Construct feature vector - ORDER MUST MATCH MODEL TRAINING (34 features)
        feature_dict = {
            # 'place_id': float(place_id), # ID not used as feature usually, or needs hashing if uuid. Skipping for now or hashing.
            # For this specific model, if it was trained on ints, we might have an issue. 
            # Assuming we can skip or hash it.
            'place_id': 0.0, # Placeholder if UUID
            'hour': float(hour),
            'day_of_week': float(day_of_week),
            'month': float(month),
            'week_of_year': float(week_of_year),
            'type_id': venue_features['type_id'],
            'waiting_time': venue_features['waiting_time'],
            'rating': venue_features['rating'],
            'delivery': venue_features['delivery'],
            'accepting_orders': venue_features['accepting_orders'],
            'total_campaigns': campaign_features['total_campaigns'],
            'avg_discount': campaign_features['avg_discount'],
            'prev_hour_items': lag_features['prev_hour_items'],
            'prev_day_items': lag_features['prev_day_items'],
            'prev_week_items': lag_features['prev_week_items'],
            'prev_month_items': lag_features['prev_month_items'],
            'rolling_7d_avg_items': lag_features['rolling_7d_avg_items'],
            'temperature_2m': weather_features['temperature_2m'],
            'relative_humidity_2m': weather_features['relative_humidity_2m'],
            'precipitation': weather_features['precipitation'],
            'rain': weather_features['rain'],
            'snowfall': weather_features['snowfall'],
            'weather_code': weather_features['weather_code'],
            'cloud_cover': weather_features['cloud_cover'],
            'wind_speed_10m': weather_features['wind_speed_10m'],
            'is_rainy': weather_features['is_rainy'],
            'is_snowy': weather_features['is_snowy'],
            'is_cold': weather_features['is_cold'],
            'is_hot': weather_features['is_hot'],
            'is_cloudy': weather_features['is_cloudy'],
            'is_windy': weather_features['is_windy'],
            'good_weather': weather_features['good_weather'],
            'weather_severity': weather_features['weather_severity'],
            'is_holiday': float(is_holiday)
        }
        
        # Return as DataFrame with column names (required by ColumnTransformer)
        return pd.DataFrame([feature_dict])
    
    def _extract_venue_features(self, bulk_data: Optional[Dict]) -> Dict[str, float]:
        """
        Extract venue features from bulk data response.
        
        Args:
            bulk_data: Response from bulk data endpoint
        
        Returns:
            Venue features dict with defaults if unavailable
        """
        if bulk_data and 'venue' in bulk_data:
            venue = bulk_data['venue']
            return {
                'type_id': float(venue.get('type_id', 0.0)),
                'waiting_time': float(venue.get('waiting_time', 15.0)),
                'rating': float(venue.get('rating', 4.0)),
                'delivery': float(venue.get('delivery', 1.0)),
                'accepting_orders': float(venue.get('accepting_orders', 1.0))
            }
        
        # Fallback defaults
        return {
            'type_id': 0.0,
            'waiting_time': 15.0,
            'rating': 4.0,
            'delivery': 1.0,
            'accepting_orders': 1.0
        }
    
    def _extract_campaign_features(self, bulk_data: Optional[Dict]) -> Dict[str, float]:
        """
        Extract campaign features from bulk data response.
        
        Args:
            bulk_data: Response from bulk data endpoint
        
        Returns:
            Campaign features dict with defaults if unavailable
        """
        if bulk_data and 'campaigns' in bulk_data:
            campaigns = bulk_data['campaigns']
            return {
                'total_campaigns': float(campaigns.get('total_campaigns', 2.0)),
                'avg_discount': float(campaigns.get('avg_discount', 0.15))
            }
        
        # Fallback defaults
        return {
            'total_campaigns': 2.0,
            'avg_discount': 0.15
        }
    
    def _extract_lag_features(self, bulk_data: Optional[Dict], timestamp: datetime) -> Dict[str, float]:
        """
        Extract lag features from bulk data historical orders.
        
        Calculates:
        - 1 hour ago (prev_hour_items)
        - 1 day ago (prev_day_items)
        - 1 week ago (prev_week_items)
        - 1 month ago (prev_month_items)
        - Last 7 days average (rolling_7d_avg_items)
        
        Args:
            bulk_data: Response from bulk data endpoint (includes historical orders)
            timestamp: Reference timestamp
        
        Returns:
            Lag features dict with defaults if unavailable
        """
        if not bulk_data or 'orders' not in bulk_data:
            # Fallback defaults
            return {
                'prev_hour_items': 100.0,
                'prev_day_items': 100.0,
                'prev_week_items': 100.0,
                'prev_month_items': 100.0,
                'rolling_7d_avg_items': 100.0
            }
        
        try:
            orders = bulk_data['orders']
            
            # Convert to datetime keys if needed
            if orders and isinstance(list(orders.keys())[0], str):
                orders = {
                    datetime.fromisoformat(ts): data
                    for ts, data in orders.items()
                }
            
            # Define lookback periods
            lookback_periods = {
                'prev_hour': timedelta(hours=1),
                'prev_day': timedelta(days=1),
                'prev_week': timedelta(weeks=1),
                'prev_month': timedelta(days=30)
            }
            
            lag_values = {}
            
            # Calculate lag values
            for key, delta in lookback_periods.items():
                target_time = timestamp - delta
                # Find orders within 1 hour of target time
                total_items = sum(
                    order['item_count']
                    for order_time, order in orders.items()
                    if abs((order_time - target_time).total_seconds()) < 3600
                )
                lag_values[key] = float(total_items) if total_items > 0 else 100.0
            
            # Calculate 7-day rolling average
            seven_days_ago = timestamp - timedelta(days=7)
            recent_orders = [
                order['item_count']
                for order_time, order in orders.items()
                if order_time >= seven_days_ago and order_time <= timestamp
            ]
            
            rolling_avg = sum(recent_orders) / len(recent_orders) if recent_orders else 100.0
            
            return {
                'prev_hour_items': lag_values.get('prev_hour', 100.0),
                'prev_day_items': lag_values.get('prev_day', 100.0),
                'prev_week_items': lag_values.get('prev_week', 100.0),
                'prev_month_items': lag_values.get('prev_month', 100.0),
                'rolling_7d_avg_items': rolling_avg
            }
            
        except Exception as e:
            print(f"⚠️  Could not extract lag features: {e}")
            # Fallback defaults
            return {
                'prev_hour_items': 100.0,
                'prev_day_items': 100.0,
                'prev_week_items': 100.0,
                'prev_month_items': 100.0,
                'rolling_7d_avg_items': 100.0
            }
    
    def _get_holiday_status(self, timestamp: datetime) -> int:
        """
        Check if timestamp is a holiday using holiday API.
        
        Returns:
            1 if holiday, 0 if not
        """
        try:
            from src.holiday_api import HolidayChecker
            
            checker = HolidayChecker()
            # Use Copenhagen coordinates as default
            result = checker.is_holiday(
                check_date=timestamp.date(),
                latitude=55.6761,
                longitude=12.5683
            )
            
            return 1 if result.get('is_holiday', False) else 0
            
        except Exception as e:
            print(f"⚠️  Could not check holiday status: {e}")
            return 0
    
    def _get_weather_features(self, timestamp: datetime) -> Dict[str, float]:
        """
        Get weather features from weather API or use fallback defaults.
        
        Uses Open-Meteo API via weather_api module.
        Returns all 16 weather features to match model training.
        """
        try:
            from src.weather_api import WeatherAPI
            
            weather_api = WeatherAPI(latitude=55.6761, longitude=12.5683)
            
            # Determine if historical or forecast
            if timestamp.date() < datetime.now().date():
                # Historical weather
                date_str = timestamp.strftime('%Y-%m-%d')
                weather_df = weather_api.get_historical_weather(date_str, date_str)
            else:
                # Forecast weather
                weather_df = weather_api.get_forecast_weather(days=7)
            
            # Filter to exact hour
            weather_df = weather_df[
                (weather_df['date'] == timestamp.date()) &
                (weather_df['hour'] == timestamp.hour)
            ]
            
            if not weather_df.empty:
                # Add derived features (is_rainy, is_snowy, etc.)
                weather_df = weather_api.add_weather_features(weather_df)
                
                row = weather_df.iloc[0]
                return {
                    'temperature_2m': float(row.get('temperature_2m', 15.0)),
                    'relative_humidity_2m': float(row.get('relative_humidity_2m', 65.0)),
                    'precipitation': float(row.get('precipitation', 0.0)),
                    'rain': float(row.get('rain', 0.0)),
                    'snowfall': float(row.get('snowfall', 0.0)),
                    'weather_code': float(row.get('weather_code', 0.0)),
                    'cloud_cover': float(row.get('cloud_cover', 50.0)),
                    'wind_speed_10m': float(row.get('wind_speed_10m', 5.0)),
                    'is_rainy': float(row.get('is_rainy', 0.0)),
                    'is_snowy': float(row.get('is_snowy', 0.0)),
                    'is_cold': float(row.get('is_cold', 0.0)),
                    'is_hot': float(row.get('is_hot', 0.0)),
                    'is_cloudy': float(row.get('is_cloudy', 0.0)),
                    'is_windy': float(row.get('is_windy', 0.0)),
                    'good_weather': float(row.get('good_weather', 0.0)),
                    'weather_severity': float(row.get('weather_severity', 0.0))
                }
        
        except Exception as e:
            print(f"⚠️  Could not fetch weather: {e}")
        
        # Fallback defaults (typical Copenhagen weather)
        return {
            'temperature_2m': 15.0,
            'relative_humidity_2m': 65.0,
            'precipitation': 0.0,
            'rain': 0.0,
            'snowfall': 0.0,
            'weather_code': 0.0,
            'cloud_cover': 50.0,
            'wind_speed_10m': 5.0,
            'is_rainy': 0.0,
            'is_snowy': 0.0,
            'is_cold': 0.0,
            'is_hot': 0.0,
            'is_cloudy': 0.0,
            'is_windy': 0.0,
            'good_weather': 1.0,
            'weather_severity': 0.0
        }
    
    def _baseline_predictions(self, time_window: timedelta) -> Dict[datetime, Dict[str, float]]:
        """Fallback baseline predictions"""
        predictions = {}
        now = datetime.now()
        hours = int(time_window.total_seconds() / 3600)
        
        for hour_offset in range(hours):
            timestamp = now - timedelta(hours=hour_offset)
            timestamp = timestamp.replace(minute=0, second=0, microsecond=0)
            predictions[timestamp] = {
                'item_count_pred': 100.0,
                'order_count_pred': 25.0
            }
        
        return predictions
    
    
    def collect_social_signals(self, 
                               place_id: int,
                               venue_name: str,
                               latitude: float,
                               longitude: float) -> Dict[str, float]:
        """
        Fetch social media signals (cached, refreshed every 15 min).
        
        Args:
            place_id: Venue ID
            venue_name: Restaurant name for social media search
            latitude: Location latitude
            longitude: Location longitude
        
        Returns:
            Social signal dictionary with composite score
        """
        return self.social.get_composite_signal(
            place_id=place_id,
            venue_name=venue_name,
            latitude=latitude,
            longitude=longitude
        )
    
    def aggregate_and_collect(self, 
                           place_id: str,
                           venue_name: str,
                           latitude: float,
                           longitude: float) -> Optional[Dict[str, any]]:
        """
        Combine all data sources and return aggregated metrics.
        This is the main method called every 5 minutes per active venue.
        
        Args:
            place_id: Venue ID
            venue_name: Restaurant name
            latitude: Location latitude
            longitude: Location longitude
        
        Returns:
            Metrics dictionary if successful, None otherwise
        """
        try:
            current_time = datetime.now()
            
            # 1. Fetch actual orders (last hour)
            actuals = self.collect_actual_orders(place_id, timedelta(hours=1))
            
            # 2. Fetch predictions (last hour)
            predictions = self.collect_predictions(place_id, timedelta(hours=1))
            
            # 3. Fetch social signals
            social = self.collect_social_signals(place_id, venue_name, latitude, longitude)
            
            # 4. Aggregate hourly totals
            actual_items = sum(a['item_count'] for a in actuals.values())
            actual_orders = sum(a['order_count'] for a in actuals.values())
            
            predicted_items = sum(p['item_count_pred'] for p in predictions.values())
            predicted_orders = sum(p['order_count_pred'] for p in predictions.values())
            
            # 5. Calculate ratio
            ratio = actual_items / predicted_items if predicted_items > 0 else 0.0
            
            # 6. Calculate excess demand
            excess_demand = actual_items - predicted_items
            
            # 7. Build metrics dict
            metrics = {
                'place_id': place_id,
                'timestamp': current_time.isoformat(),
                'actual_items': actual_items,
                'actual_orders': actual_orders,
                'predicted_items': predicted_items,
                'predicted_orders': predicted_orders,
                'ratio': ratio,
                'social_signals': social,
                'excess_demand': excess_demand
            }
            
            # 8. Log to model monitor for performance tracking and retraining
            if self.monitor is not None and self.enable_monitoring:
                try:
                    # Build feature dict for retraining data
                    features = self._build_feature_vector(place_id, current_time)
                    feature_dict = features.to_dict('records')[0] if not features.empty else None
                    
                    self.monitor.log_prediction_vs_actual(
                        place_id=place_id,
                        timestamp=current_time,
                        predicted_items=predicted_items,
                        predicted_orders=predicted_orders,
                        actual_items=actual_items,
                        actual_orders=actual_orders,
                        features=feature_dict
                    )
                except Exception as e:
                    # Don't fail data collection if monitoring fails
                    print(f"⚠️  Could not log to monitor: {e}")
            
            print(f"✅ Collected metrics for place {place_id} at {current_time.strftime('%H:%M')}")
            print(f"   Actual: {actual_items:.0f} items | Predicted: {predicted_items:.0f} | Ratio: {ratio:.2f}x")
            
            return metrics
            
        except Exception as e:
            print(f"❌ Error aggregating data for place {place_id}: {e}")
            return None
    
    def collect_for_all_venues(self, venues: List[Dict[str, any]]) -> Dict[str, any]:
        """
        Collect data for all active venues in one batch.
        
        Args:
            venues: List of venue dicts with:
                - place_id: int
                - name: str
                - latitude: float
                - longitude: float
        
        Returns:
            Dictionary with:
                'metrics': List[Dict] - Collected metrics for each venue
                'summary': Dict - Summary statistics
        """
        start_time = datetime.now()
        successful = 0
        failed = 0
        metrics_list = []
        
        for venue in venues:
            try:
                metrics = self.aggregate_and_collect(
                    place_id=venue['place_id'],
                    venue_name=venue['name'],
                    latitude=venue['latitude'],
                    longitude=venue['longitude']
                )
                
                if metrics:
                    metrics_list.append(metrics)
                    successful += 1
                else:
                    failed += 1
                    
            except Exception as e:
                print(f"❌ Failed to collect for venue {venue.get('place_id')}: {e}")
                failed += 1
        
        duration = (datetime.now() - start_time).total_seconds()
        
        # Run automatic maintenance if enabled
        maintenance_result = None
        if self.auto_maintain:
            maintenance_result = self.run_automatic_maintenance()
        
        return {
            'metrics': metrics_list,
            'summary': {
                'total_venues': len(venues),
                'successful': successful,
                'failed': failed,
                'duration_seconds': duration,
                'avg_time_per_venue': duration / len(venues) if venues else 0
            },
            'maintenance': maintenance_result
        }
    
    def get_single_venue_metrics(self, place_id: str, venue_name: str, 
                                 latitude: float, longitude: float) -> Optional[Dict[str, any]]:
        """
        Get current metrics for a single venue.
        Convenience method for API endpoint.
        
        Args:
            place_id: Venue ID
            venue_name: Restaurant name
            latitude: Location latitude
            longitude: Location longitude
        
        Returns:
            Metrics dictionary or None if failed
        """
        return self.aggregate_and_collect(place_id, venue_name, latitude, longitude)
    
    def run_automatic_maintenance(self, force: bool = False) -> Optional[Dict]:
        """
        Check if model maintenance is needed and run it automatically.
        
        This is called after each collection cycle when auto_maintain=True.
        Only runs if enough time has passed since last check.
        
        Args:
            force: If True, skip interval check and run immediately
        
        Returns:
            Maintenance result dict or None if no action taken
        """
        if not self.auto_maintain and not force:
            return None
        
        now = datetime.now()
        
        # Check if we should run maintenance check
        if not force and self._last_maintenance_check is not None:
            time_since_last = now - self._last_maintenance_check
            if time_since_last < self.maintenance_check_interval:
                return None  # Too soon
        
        self._last_maintenance_check = now
        print(f"\n🔧 Running automatic model maintenance check...")
        
        try:
            from src.model_manager import HybridModelManager
            
            manager = HybridModelManager()
            
            # Check what action is needed
            should_retrain, retrain_reason = manager.should_full_retrain()
            should_finetune, finetune_reason = manager.should_fine_tune()
            
            if should_retrain:
                print(f"   📊 Full retrain needed: {retrain_reason}")
                result = manager.update_model()
                
                if result.get('status') == 'success':
                    # Reload the model after update
                    self._reload_model()
                    print(f"   ✅ Full retrain completed successfully")
                else:
                    print(f"   ⚠️  Full retrain failed: {result.get('error', 'Unknown error')}")
                
                return result
            
            elif should_finetune:
                print(f"   📊 Fine-tune needed: {finetune_reason}")
                result = manager.update_model()
                
                if result.get('status') == 'success':
                    # Reload the model after update
                    self._reload_model()
                    print(f"   ✅ Fine-tune completed successfully")
                else:
                    print(f"   ⚠️  Fine-tune failed: {result.get('error', 'Unknown error')}")
                
                return result
            
            else:
                print(f"   ✅ No maintenance needed")
                return {'status': 'no_action', 'message': 'Model is healthy'}
        
        except Exception as e:
            print(f"   ❌ Maintenance check failed: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def _reload_model(self) -> None:
        """Reload the ML model from disk after maintenance update."""
        try:
            if self.model_path.exists():
                self.model = joblib.load(self.model_path)
                print(f"   🔄 Model reloaded from {self.model_path}")
        except Exception as e:
            print(f"   ⚠️  Could not reload model: {e}")


def load_venues_from_database() -> List[Dict[str, any]]:
    """
    Load list of active venues via API endpoint.
    
    Calls: GET /api/v1/venues/active
    
    Returns:
        List of venue dictionaries
    """
    try:
        response = requests.get(
            "http://localhost:8000/api/v1/venues/active",
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get('venues', [])
        else:
            print(f"⚠️  Venues API returned {response.status_code}, using fallback")
            return _get_fallback_venues()
            
    except Exception as e:
        print(f"⚠️  Could not fetch venues via API: {e}")
        return _get_fallback_venues()


def _get_fallback_venues() -> List[Dict[str, any]]:
    """Fallback venues for demo/testing when API unavailable."""
    return [
        {
            'place_id': 1,
            'name': 'Sample Restaurant 1',
            'latitude': 55.6761,
            'longitude': 12.5683
        },
        {
            'place_id': 2,
            'name': 'Sample Restaurant 2',
            'latitude': 55.6867,
            'longitude': 12.5700
        }
    ]


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Real-Time Data Collector for Surge Detection')
    parser.add_argument('--auto-maintain', action='store_true', 
                        help='Enable automatic model maintenance')
    parser.add_argument('--maintenance-interval', type=int, default=6,
                        help='Hours between maintenance checks (default: 6)')
    parser.add_argument('--force-maintenance', action='store_true',
                        help='Force run maintenance check now')
    parser.add_argument('--demo', action='store_true', default=True,
                        help='Use demo mode for social media APIs')
    args = parser.parse_args()
    
    print("=== Real-Time Data Collector Demo ===\n")
    
    # Initialize collector with options
    print("Using DEMO MODE for social media APIs (simulated data)\n")
    collector = RealTimeDataCollector(
        demo_mode=args.demo,
        auto_maintain=args.auto_maintain,
        maintenance_check_interval_hours=args.maintenance_interval
    )
    
    # Force maintenance check if requested
    if args.force_maintenance:
        print("\n🔧 Forcing maintenance check...")
        result = collector.run_automatic_maintenance(force=True)
        if result:
            print(f"   Result: {result.get('status', 'unknown')}")
        print()
    
    # Load venues
    venues = load_venues_from_database()
    print(f"\n📍 Loaded {len(venues)} active venues\n")
    
    # Collect data for all venues
    print("🔄 Collecting data for all venues...\n")
    result = collector.collect_for_all_venues(venues)
    
    print("\n" + "="*60)
    print("📊 Collection Summary:")
    print(f"   Total venues: {result['summary']['total_venues']}")
    print(f"   Successful: {result['summary']['successful']}")
    print(f"   Failed: {result['summary']['failed']}")
    print(f"   Duration: {result['summary']['duration_seconds']:.2f}s")
    print(f"   Avg per venue: {result['summary']['avg_time_per_venue']:.2f}s")
    print(f"   Metrics collected: {len(result['metrics'])}")
    
    if result.get('maintenance'):
        print(f"\n🔧 Maintenance: {result['maintenance'].get('status', 'unknown')}")
    print("="*60)
    
    # Show sample metrics
    if result['metrics']:
        print("\n📈 Sample Metrics (First Venue):")
        sample = result['metrics'][0]
        print(f"   Place ID: {sample['place_id']}")
        print(f"   Timestamp: {sample['timestamp']}")
        print(f"   Actual/Predicted Items: {sample['actual_items']:.0f} / {sample['predicted_items']:.0f}")
        print(f"   Ratio: {sample['ratio']:.2f}x")
        print(f"   Excess Demand: {sample['excess_demand']:.0f}")
