"""
Model Performance Monitoring for Demand Prediction
===================================================
Monitors production model performance by comparing predictions vs actuals.
Integrates with the data collector to log metrics and detect drift.

Features:
- Logs predictions vs actuals to CSV for retraining
- Calculates rolling MAE and drift metrics
- Triggers alerts when performance degrades
- Provides data for fine-tuning decisions

Usage:
    # As part of data collection pipeline
    from src.model_monitor import ModelMonitor
    monitor = ModelMonitor()
    monitor.log_prediction_vs_actual(place_id, timestamp, predicted, actual)
    
    # Check model health
    health = monitor.get_model_health(days=7)
    if health['needs_retrain']:
        print("Model retraining recommended")
"""

import sys
import json
import pandas as pd
import numpy as np
import joblib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Tuple

# Add parent directory to path for running as script
_current_dir = Path(__file__).resolve().parent
_parent_dir = _current_dir.parent
if str(_parent_dir) not in sys.path:
    sys.path.insert(0, str(_parent_dir))
import json
import os


class ModelMonitor:
    """
    Monitors ML model performance and logs data for retraining.
    
    Stores:
    - logs/predictions_log.csv: Raw predictions vs actuals
    - logs/performance_metrics.json: Rolling performance metrics
    - logs/drift_alerts.json: Performance degradation alerts
    """
    
    def __init__(self, 
                 logs_dir: str = "logs",
                 model_dir: str = "data/models",
                 drift_threshold_pct: float = 15.0,
                 alert_threshold_pct: float = 25.0):
        """
        Initialize model monitor.
        
        Args:
            logs_dir: Directory for log files
            model_dir: Directory containing model metadata
            drift_threshold_pct: % degradation to suggest retraining
            alert_threshold_pct: % degradation to trigger alert
        """
        self.logs_dir = Path(logs_dir)
        self.model_dir = Path(model_dir)
        self.drift_threshold = drift_threshold_pct
        self.alert_threshold = alert_threshold_pct
        
        # Ensure directories exist
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        # File paths
        self.predictions_log_path = self.logs_dir / "predictions_log.csv"
        self.metrics_path = self.logs_dir / "performance_metrics.json"
        self.alerts_path = self.logs_dir / "drift_alerts.json"
        self.training_data_path = self.logs_dir / "training_data_new.csv"
        
        # Load baseline metrics from model metadata
        self.baseline_metrics = self._load_baseline_metrics()
        
        print(f"📊 ModelMonitor initialized (drift threshold: {drift_threshold_pct}%)")
    
    def _load_baseline_metrics(self) -> Dict[str, float]:
        """Load baseline MAE from model metadata."""
        metadata_path = self.model_dir / "rf_model_metadata.json"
        
        try:
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            # Extract baseline MAE
            if 'metrics' in metadata:
                metrics = metadata['metrics']
                if isinstance(metrics, dict) and 'item_count' in metrics:
                    return {
                        'item_count_mae': metrics['item_count'].get('mae_time_split', 3.5),
                        'order_count_mae': metrics.get('order_count', {}).get('mae_time_split', 1.8),
                        'training_date': metadata.get('training_date', 'unknown'),
                        'version': metadata.get('version', 'unknown')
                    }
            
            # Legacy format
            return {
                'item_count_mae': 3.5,
                'order_count_mae': 1.8,
                'training_date': metadata.get('training_date', 'unknown'),
                'version': metadata.get('version', 'unknown')
            }
            
        except Exception as e:
            print(f"⚠️  Could not load baseline metrics: {e}")
            return {
                'item_count_mae': 3.5,
                'order_count_mae': 1.8,
                'training_date': 'unknown',
                'version': 'unknown'
            }
    
    def log_prediction_vs_actual(self,
                                  place_id: int,
                                  timestamp: datetime,
                                  predicted_items: float,
                                  predicted_orders: float,
                                  actual_items: float,
                                  actual_orders: float,
                                  features: Optional[Dict] = None) -> None:
        """
        Log a single prediction vs actual observation.
        
        This data is used for:
        1. Performance monitoring (MAE calculation)
        2. Drift detection
        3. Fine-tuning / retraining
        
        Args:
            place_id: Venue ID
            timestamp: Observation timestamp
            predicted_items: Model's item_count prediction
            predicted_orders: Model's order_count prediction
            actual_items: Actual item_count observed
            actual_orders: Actual order_count observed
            features: Optional feature dict for retraining data
        """
        # Create log entry
        log_entry = {
            'timestamp': timestamp.isoformat(),
            'place_id': place_id,
            'predicted_items': predicted_items,
            'predicted_orders': predicted_orders,
            'actual_items': actual_items,
            'actual_orders': actual_orders,
            'item_error': actual_items - predicted_items,
            'order_error': actual_orders - predicted_orders,
            'item_abs_error': abs(actual_items - predicted_items),
            'order_abs_error': abs(actual_orders - predicted_orders),
            'logged_at': datetime.now().isoformat()
        }
        
        # Append to predictions log
        self._append_to_log(log_entry)
        
        # Also log features for retraining if provided
        if features:
            self._log_training_sample(features, actual_items, actual_orders, timestamp)
    
    def _append_to_log(self, entry: Dict) -> None:
        """Append entry to predictions log CSV."""
        df_entry = pd.DataFrame([entry])
        
        if self.predictions_log_path.exists():
            df_entry.to_csv(self.predictions_log_path, mode='a', 
                           header=False, index=False)
        else:
            df_entry.to_csv(self.predictions_log_path, index=False)
    
    def _log_training_sample(self, 
                             features: Dict,
                             actual_items: float,
                             actual_orders: float,
                             timestamp: datetime) -> None:
        """
        Log a training sample for future fine-tuning/retraining.
        
        This creates a dataset that can be used to update the model.
        """
        # Add targets to features
        sample = features.copy()
        sample['item_count'] = actual_items
        sample['order_count'] = actual_orders
        sample['datetime'] = timestamp.isoformat()
        
        df_sample = pd.DataFrame([sample])
        
        if self.training_data_path.exists():
            df_sample.to_csv(self.training_data_path, mode='a',
                            header=False, index=False)
        else:
            df_sample.to_csv(self.training_data_path, index=False)
    
    def log_batch_from_collector(self, 
                                 metrics_list: List[Dict],
                                 feature_vectors: Optional[Dict[int, Dict]] = None) -> int:
        """
        Log batch of metrics from data collector.
        
        This is the main integration point with the data collector.
        
        Args:
            metrics_list: List of metrics dicts from collector.collect_for_all_venues()
            feature_vectors: Optional dict mapping place_id -> feature dict
        
        Returns:
            Number of samples logged
        """
        logged = 0
        
        for metrics in metrics_list:
            try:
                place_id = metrics['place_id']
                timestamp = datetime.fromisoformat(metrics['timestamp'])
                
                # Get features for this venue if available
                features = feature_vectors.get(place_id) if feature_vectors else None
                
                self.log_prediction_vs_actual(
                    place_id=place_id,
                    timestamp=timestamp,
                    predicted_items=metrics['predicted_items'],
                    predicted_orders=metrics['predicted_orders'],
                    actual_items=metrics['actual_items'],
                    actual_orders=metrics['actual_orders'],
                    features=features
                )
                logged += 1
                
            except Exception as e:
                print(f"⚠️  Failed to log metrics for place {metrics.get('place_id')}: {e}")
        
        return logged
    
    def calculate_performance_metrics(self, 
                                       days: int = 7) -> Dict[str, float]:
        """
        Calculate performance metrics over the specified time window.
        
        Args:
            days: Number of days to look back
        
        Returns:
            Performance metrics dict
        """
        if not self.predictions_log_path.exists():
            print("⚠️  No predictions log found")
            return {'status': 'no_data'}
        
        # Load log
        df = pd.read_csv(self.predictions_log_path)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Filter to time window
        cutoff = datetime.now() - timedelta(days=days)
        df_window = df[df['timestamp'] >= cutoff]
        
        if df_window.empty:
            return {'status': 'insufficient_data', 'samples': 0}
        
        # Calculate metrics
        item_mae = df_window['item_abs_error'].mean()
        order_mae = df_window['order_abs_error'].mean()
        
        item_bias = df_window['item_error'].mean()  # Positive = under-predicting
        order_bias = df_window['order_error'].mean()
        
        # Calculate degradation vs baseline
        baseline_item_mae = self.baseline_metrics.get('item_count_mae', 3.5)
        baseline_order_mae = self.baseline_metrics.get('order_count_mae', 1.8)
        
        item_degradation_pct = ((item_mae - baseline_item_mae) / baseline_item_mae) * 100
        order_degradation_pct = ((order_mae - baseline_order_mae) / baseline_order_mae) * 100
        
        avg_degradation = (item_degradation_pct + order_degradation_pct) / 2
        
        metrics = {
            'status': 'ok',
            'time_window_days': days,
            'samples_count': len(df_window),
            'unique_venues': df_window['place_id'].nunique(),
            
            # Current performance
            'item_count_mae': round(item_mae, 4),
            'order_count_mae': round(order_mae, 4),
            'item_count_bias': round(item_bias, 4),
            'order_count_bias': round(order_bias, 4),
            
            # Baseline comparison
            'baseline_item_mae': baseline_item_mae,
            'baseline_order_mae': baseline_order_mae,
            'item_degradation_pct': round(item_degradation_pct, 2),
            'order_degradation_pct': round(order_degradation_pct, 2),
            'avg_degradation_pct': round(avg_degradation, 2),
            
            # Thresholds
            'drift_threshold_pct': self.drift_threshold,
            'alert_threshold_pct': self.alert_threshold,
            
            # Model info
            'model_version': self.baseline_metrics.get('version', 'unknown'),
            'model_training_date': self.baseline_metrics.get('training_date', 'unknown'),
            
            # Calculated at
            'calculated_at': datetime.now().isoformat()
        }
        
        return metrics
    
    def get_model_health(self, days: int = 7) -> Dict[str, any]:
        """
        Get overall model health status with recommendations.
        
        Args:
            days: Number of days to analyze
        
        Returns:
            Health status dict with recommendations
        """
        metrics = self.calculate_performance_metrics(days)
        
        if metrics.get('status') != 'ok':
            return {
                'healthy': True,  # Assume healthy if no data
                'status': metrics.get('status', 'unknown'),
                'message': 'Insufficient data for health check',
                'needs_retrain': False,
                'needs_alert': False,
                'recommendation': 'Continue monitoring'
            }
        
        avg_degradation = metrics['avg_degradation_pct']
        
        # Determine health status
        if avg_degradation < 0:
            status = 'improving'
            healthy = True
            needs_retrain = False
            needs_alert = False
            recommendation = 'Model is performing better than baseline'
        elif avg_degradation < self.drift_threshold:
            status = 'healthy'
            healthy = True
            needs_retrain = False
            needs_alert = False
            recommendation = 'Continue monitoring'
        elif avg_degradation < self.alert_threshold:
            status = 'degraded'
            healthy = False
            needs_retrain = True
            needs_alert = False
            recommendation = f'Performance degraded {avg_degradation:.1f}%. Consider fine-tuning.'
        else:
            status = 'critical'
            healthy = False
            needs_retrain = True
            needs_alert = True
            recommendation = f'Critical degradation {avg_degradation:.1f}%. Full retrain recommended.'
        
        health = {
            'healthy': healthy,
            'status': status,
            'metrics': metrics,
            'needs_retrain': needs_retrain,
            'needs_alert': needs_alert,
            'recommendation': recommendation,
            'suggested_action': 'fine_tune' if avg_degradation < self.alert_threshold else 'full_retrain'
        }
        
        # Log alert if needed
        if needs_alert:
            self._log_drift_alert(health)
        
        # Save metrics
        self._save_metrics(metrics)
        
        return health
    
    def _log_drift_alert(self, health: Dict) -> None:
        """Log a drift alert to alerts file."""
        alert = {
            'timestamp': datetime.now().isoformat(),
            'status': health['status'],
            'avg_degradation_pct': health['metrics']['avg_degradation_pct'],
            'recommendation': health['recommendation']
        }
        
        # Load existing alerts
        alerts = []
        if self.alerts_path.exists():
            with open(self.alerts_path, 'r') as f:
                alerts = json.load(f)
        
        alerts.append(alert)
        
        # Keep last 100 alerts
        alerts = alerts[-100:]
        
        with open(self.alerts_path, 'w') as f:
            json.dump(alerts, f, indent=2)
        
        print(f"⚠️  DRIFT ALERT logged: {health['status']} ({health['metrics']['avg_degradation_pct']:.1f}% degradation)")
    
    def _save_metrics(self, metrics: Dict) -> None:
        """Save performance metrics to file."""
        with open(self.metrics_path, 'w') as f:
            json.dump(metrics, f, indent=2)
    
    def get_training_data(self, 
                          days: Optional[int] = None,
                          min_samples: int = 1000) -> Optional[pd.DataFrame]:
        """
        Get accumulated training data for fine-tuning/retraining.
        
        Args:
            days: Optional number of days to include (None = all)
            min_samples: Minimum samples required
        
        Returns:
            DataFrame with training data or None if insufficient
        """
        if not self.training_data_path.exists():
            print("⚠️  No training data accumulated yet")
            return None
        
        df = pd.read_csv(self.training_data_path)
        
        if days:
            df['datetime'] = pd.to_datetime(df['datetime'])
            cutoff = datetime.now() - timedelta(days=days)
            df = df[df['datetime'] >= cutoff]
        
        if len(df) < min_samples:
            print(f"⚠️  Insufficient training data: {len(df)} samples (need {min_samples})")
            return None
        
        print(f"✅ Loaded {len(df)} training samples")
        return df
    
    def get_predictions_log(self, days: int = 30) -> Optional[pd.DataFrame]:
        """Get predictions log for analysis."""
        if not self.predictions_log_path.exists():
            return None
        
        df = pd.read_csv(self.predictions_log_path)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        cutoff = datetime.now() - timedelta(days=days)
        return df[df['timestamp'] >= cutoff]
    
    def get_error_analysis(self, days: int = 7) -> Dict[str, any]:
        """
        Analyze prediction errors by venue, hour, and day.
        
        Useful for identifying systematic issues.
        """
        df = self.get_predictions_log(days)
        if df is None or df.empty:
            return {'status': 'no_data'}
        
        df['hour'] = pd.to_datetime(df['timestamp']).dt.hour
        df['day_of_week'] = pd.to_datetime(df['timestamp']).dt.dayofweek
        
        # By hour
        hourly_mae = df.groupby('hour')['item_abs_error'].mean().to_dict()
        
        # By day of week
        daily_mae = df.groupby('day_of_week')['item_abs_error'].mean().to_dict()
        
        # By venue (top 10 worst)
        venue_mae = df.groupby('place_id')['item_abs_error'].mean().nlargest(10).to_dict()
        
        # Worst hours (highest MAE)
        worst_hours = sorted(hourly_mae.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            'status': 'ok',
            'samples': len(df),
            'hourly_mae': hourly_mae,
            'daily_mae': daily_mae,
            'worst_venues': venue_mae,
            'worst_hours': worst_hours,
            'overall_mae': df['item_abs_error'].mean(),
            'overall_bias': df['item_error'].mean()
        }
    
    def clear_old_logs(self, days_to_keep: int = 90) -> int:
        """
        Clear prediction logs older than specified days.
        
        Args:
            days_to_keep: Number of days of logs to retain
        
        Returns:
            Number of rows removed
        """
        if not self.predictions_log_path.exists():
            return 0
        
        df = pd.read_csv(self.predictions_log_path)
        original_len = len(df)
        
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        cutoff = datetime.now() - timedelta(days=days_to_keep)
        df = df[df['timestamp'] >= cutoff]
        
        df.to_csv(self.predictions_log_path, index=False)
        
        removed = original_len - len(df)
        print(f"🗑️  Removed {removed} old log entries (kept {len(df)})")
        
        return removed


def run_health_check():
    """Standalone health check script."""
    print("="*60)
    print("MODEL HEALTH CHECK")
    print("="*60 + "\n")
    
    monitor = ModelMonitor()
    
    # Get health for last 7 days
    health = monitor.get_model_health(days=7)
    
    print(f"Status: {health['status'].upper()}")
    print(f"Healthy: {'✅ Yes' if health['healthy'] else '❌ No'}")
    print(f"Needs Retrain: {'Yes' if health['needs_retrain'] else 'No'}")
    print(f"Recommendation: {health['recommendation']}")
    
    if 'metrics' in health and health['metrics'].get('status') == 'ok':
        m = health['metrics']
        print(f"\nMetrics (last {m['time_window_days']} days):")
        print(f"  Samples: {m['samples_count']}")
        print(f"  Venues: {m['unique_venues']}")
        print(f"  Item MAE: {m['item_count_mae']:.2f} (baseline: {m['baseline_item_mae']:.2f})")
        print(f"  Degradation: {m['avg_degradation_pct']:.1f}%")
    
    print("\n" + "="*60)
    
    return health


if __name__ == "__main__":
    run_health_check()
