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
                 demo_mode: bool = False):
        """
        Initialize data collector.
        
        Args:
            model_path: Path to trained prediction model
            update_interval_seconds: Collection interval (default 5 minutes)
            demo_mode: If True, use simulated social media data
        """
        self.update_interval = update_interval_seconds
        self.demo_mode = demo_mode
        
        # Initialize social media aggregator
        self.social = get_social_aggregator(demo_mode=demo_mode)
        
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
    
    def collect_actual_orders(self, 
                              place_id: int, 
                              time_window: timedelta) -> Dict[datetime, Dict[str, int]]:
        """
        Query actual orders via API endpoint.
        
        Args:
            place_id: Venue ID
            time_window: Look-back period (e.g., last 1 hour)
        
        Returns:
            Dict mapping timestamp -> {item_count: int, order_count: int}
        """
        try:
            
            # Call the orders API endpoint
            # This should match the pattern in main.py where the backend handles the query
            response = requests.post(
                "http://localhost:8000/api/v1/orders/query",
                json={
                    "place_id": place_id,
                    "time_window_hours": int(time_window.total_seconds() / 3600),
                    "end_time": datetime.now().isoformat()
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('orders', {})
            else:
                print(f"⚠️  Orders API returned {response.status_code}")
                return self._simulate_actual_orders(place_id, time_window)
                
        except Exception as e:
            print(f"⚠️  Could not fetch orders via API: {e}")
            print("   Falling back to simulated data")
            return self._simulate_actual_orders(place_id, time_window)
    
    def _simulate_actual_orders(self, 
                                place_id: int, 
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
                           place_id: int, 
                           time_window: timedelta) -> Dict[datetime, Dict[str, float]]:
        """
        Get demand predictions from the database for the time window.
        
        Args:
            place_id: Venue ID
            time_window: Time period to predict for
        
        Returns:
            Dict mapping timestamp -> {item_count_pred: float, order_count_pred: float}
        """
        # Try to fetch from database first
        db_predictions = self._fetch_predictions_from_database(place_id, time_window)
        if db_predictions:
            return db_predictions
        else:
            # Fall back to model-based predictions if no database records
            return self._predict_with_model(place_id, time_window) 
        
    
    def _fetch_predictions_from_database(self,
                                        place_id: int,
                                        time_window: timedelta) -> Optional[Dict[datetime, Dict[str, float]]]:
        """
        Fetch pre-computed predictions from database via API endpoint.
        
        Calls backend endpoint that queries:
        SELECT timestamp, item_count_pred, order_count_pred
        FROM demand_predictions
        WHERE place_id = %s
          AND timestamp >= NOW() - INTERVAL '...'
        ORDER BY timestamp DESC
        
        Args:
            place_id: Venue ID
            time_window: Time period to fetch
        
        Returns:
            Predictions dict or None if empty/unavailable
        """
        try:
            response = requests.post(
                "http://localhost:8000/api/v1/predictions/query",
                json={
                    "place_id": place_id,
                    "time_window_hours": int(time_window.total_seconds() / 3600),
                    "end_time": datetime.now().isoformat()
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                predictions = data.get('predictions', {})
                
                # Convert string timestamps back to datetime if needed
                if predictions:
                    return {
                        datetime.fromisoformat(ts): pred 
                        for ts, pred in predictions.items()
                    }
                return None
            else:
                print(f"⚠️  Predictions API returned {response.status_code}")
                return None
                
        except Exception as e:
            print(f"⚠️  Could not fetch predictions via API: {e}")
            return None
    
    def _predict_with_model(self, 
                           place_id: int, 
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
                
                # Make prediction
                pred = self.model.predict(features.reshape(1, -1))
                
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
    
    def _build_feature_vector(self, place_id: int, timestamp: datetime) -> np.ndarray:
        """
        Build feature vector matching training data format.
        
        Features should match those in train_model.py's x.columns
        """
        day_of_week = timestamp.weekday()
        hour = timestamp.hour
        month = timestamp.month
        week_of_year = timestamp.isocalendar()[1]
        
        # Construct feature vector with expected features
        # Order must match model training features
        feature_dict = {
            'place_id': float(place_id),
            'type_id': 0.0,
            'waiting_time': 15.0,
            'rating': 4.0,
            'delivery': 1.0,
            'accepting_orders': 1.0,
            'total_campaigns': 2.0,
            'avg_discount': 0.15,
            'day_of_week': float(day_of_week),
            'month': float(month),
            'week_of_year': float(week_of_year),
            'hour': float(hour),
            'prev_hour_items': 100.0,
            'prev_day_items': 100.0,
            'prev_week_items': 100.0,
            'prev_month_items': 100.0,
            'rolling_7d_avg_items': 100.0,
            'is_holiday': 0.0,
            'temperature_2m': 15.0,
            'relative_humidity_2m': 65.0,
            'precipitation': 0.0,
            'rain': 0.0,
            'snowfall': 0.0,
            'cloud_cover': 50.0,
            'wind_speed_10m': 5.0,
            'weather_severity': 0.0
        }
        
        return np.array([list(feature_dict.values())])
    
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
                           place_id: int,
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
        
        return {
            'metrics': metrics_list,
            'summary': {
                'total_venues': len(venues),
                'successful': successful,
                'failed': failed,
                'duration_seconds': duration,
                'avg_time_per_venue': duration / len(venues) if venues else 0
            }
        }
    
    def get_single_venue_metrics(self, place_id: int, venue_name: str, 
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


def load_venues_from_database() -> List[Dict[str, any]]:
    """
    Load list of active venues from database.
    
    In production, query your venue/places table:
    
    SELECT 
        id as place_id,
        name,
        latitude,
        longitude
    FROM dim_places
    WHERE accepting_orders = true
      AND active = true
    
    Returns:
        List of venue dictionaries
    """
    # TODO: Replace with actual database query
    # For demo, return sample venues
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
    # Demo usage
    print("=== Real-Time Data Collector Demo ===\n")
    
    # Initialize collector with demo mode for social media
    print("Using DEMO MODE for social media APIs (simulated data)\n")
    collector = RealTimeDataCollector(demo_mode=True)
    
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
