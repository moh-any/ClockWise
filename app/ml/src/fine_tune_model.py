"""
Model Fine-Tuning Module for Demand Prediction
===============================================
Provides incremental model updates using CatBoost's warm start capability.
Much faster than full retraining (~5-10 min vs 30-60 min).

Fine-tuning Strategy:
- Uses init_model parameter for warm starting
- Trains additional iterations on new data
- Preserves knowledge from historical training
- Supports both item_count and order_count models

Usage:
    from src.fine_tune_model import fine_tune_catboost, fine_tune_from_monitor_data
    
    # Fine-tune on new data file
    fine_tune_catboost('data/processed/new_data.csv')
    
    # Fine-tune on accumulated monitor data
    fine_tune_from_monitor_data(days=30)
"""

import sys
import numpy as np
import pandas as pd
import joblib
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple, Dict, List
import warnings
import shutil
import json

# Add parent directory to path for running as script
_current_dir = Path(__file__).resolve().parent
_parent_dir = _current_dir.parent
if str(_parent_dir) not in sys.path:
    sys.path.insert(0, str(_parent_dir))

warnings.filterwarnings('ignore')

try:
    from catboost import CatBoostRegressor
    CATBOOST_AVAILABLE = True
except ImportError:
    CATBOOST_AVAILABLE = False
    print("⚠️  CatBoost not available. Install with: pip install catboost")

from sklearn.preprocessing import StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.metrics import mean_absolute_error, r2_score


# Feature definitions (must match train_model.py)
SCALE_FEATURES = [
    'waiting_time', 'rating', 'avg_discount',
    'prev_hour_items', 'prev_day_items', 'prev_week_items', 
    'prev_month_items', 'rolling_7d_avg_items',
    # Phase 1 features - rolling windows
    'rolling_3d_avg_items', 'rolling_14d_avg_items', 'rolling_30d_avg_items',
    'rolling_7d_std_items', 'demand_trend_7d',
    'lag_same_hour_last_week', 'lag_same_hour_2_weeks',
    # Weather features
    'temperature_2m', 'relative_humidity_2m', 'precipitation', 
    'rain', 'snowfall', 'cloud_cover', 'wind_speed_10m', 'weather_severity',
    # Phase 2 features - venue-specific
    'venue_hour_avg', 'venue_dow_avg', 'venue_volatility', 
    'venue_total_items', 'venue_growth_recent_vs_historical',
    # Phase 2 features - weather interactions
    'feels_like_temp', 'bad_weather_score', 'temp_change_1h', 
    'temp_change_3h',
    # Phase 4 features - weekend specific
    'venue_weekend_avg', 'venue_weekday_avg', 'venue_weekend_lift',
    'last_weekend_same_hour', 'venue_weekend_volatility',
    'weekend_day_position'
]

TARGET_FEATURES = ['item_count', 'order_count']
USELESS_FEATURES = ['total_revenue', 'avg_order_value', 'avg_items_per_order', 'datetime']


class FineTuner:
    """
    Fine-tunes demand prediction models using CatBoost warm start.
    
    Attributes:
        model_path: Path to existing production model
        metadata_path: Path to model metadata
        output_dir: Directory for fine-tuned models
    """
    
    def __init__(self,
                 model_path: str = "data/models/rf_model.joblib",
                 metadata_path: str = "data/models/rf_model_metadata.json",
                 output_dir: str = "data/models"):
        """
        Initialize fine-tuner.
        
        Args:
            model_path: Path to existing production model
            metadata_path: Path to model metadata
            output_dir: Output directory for fine-tuned model
        """
        self.model_path = Path(model_path)
        self.metadata_path = Path(metadata_path)
        self.output_dir = Path(output_dir)
        
        if not CATBOOST_AVAILABLE:
            raise RuntimeError("CatBoost is required for fine-tuning. Install: pip install catboost")
        
        # Load existing model and metadata
        self.existing_models = None
        self.metadata = None
        self._load_existing_model()
    
    def _load_existing_model(self) -> None:
        """Load existing production model."""
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model not found: {self.model_path}")
        
        self.existing_models = joblib.load(self.model_path)
        
        if self.metadata_path.exists():
            try:
                with open(self.metadata_path, 'r') as f:
                    self.metadata = json.load(f)
            except Exception:
                # Fallback to joblib for legacy format
                try:
                    self.metadata = joblib.load(self.metadata_path)
                except Exception:
                    self.metadata = {}
        else:
            self.metadata = {}
        
        # Validate model type
        model_type = self.metadata.get('model_algorithm', '').lower()
        if 'catboost' not in model_type:
            print(f"⚠️  Existing model type: {model_type}")
            print("   Fine-tuning works best with CatBoost models.")
            print("   Will attempt to fine-tune anyway using new CatBoost models.")
    
    def _prepare_data(self, 
                      df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Prepare data for fine-tuning.
        
        Args:
            df: Raw data DataFrame
        
        Returns:
            Tuple of (X, y) DataFrames
        """
        # Remove targets and useless features
        drop_cols = TARGET_FEATURES + [c for c in USELESS_FEATURES if c in df.columns]
        
        # Keep only numeric columns that exist in data
        X = df.drop([c for c in drop_cols if c in df.columns], axis=1)
        y = df[TARGET_FEATURES].copy()
        
        # Handle missing values
        if 'longitude' in X.columns:
            X = X.drop(['longitude', 'latitude'], axis=1, errors='ignore')
        
        X['type_id'] = X['type_id'].fillna(-1) if 'type_id' in X.columns else -1
        X['waiting_time'] = X['waiting_time'].fillna(X['waiting_time'].median()) if 'waiting_time' in X.columns else 15
        X['rating'] = X['rating'].fillna(X['rating'].median()) if 'rating' in X.columns else 4.0
        X['delivery'] = X['delivery'].fillna(0) if 'delivery' in X.columns else 0
        X['accepting_orders'] = X['accepting_orders'].fillna(0) if 'accepting_orders' in X.columns else 0
        
        # Convert dtypes
        if 'place_id' in X.columns:
            X['place_id'] = X['place_id'].astype('float64')
        if 'type_id' in X.columns:
            X['type_id'] = X['type_id'].astype('float64')
        
        X.columns = X.columns.astype(str)
        y.columns = y.columns.astype(str)
        
        return X, y
    
    def _create_preprocessor(self, X: pd.DataFrame) -> ColumnTransformer:
        """Create preprocessor matching training pipeline."""
        # Filter to only include features that exist
        scale_features = [f for f in SCALE_FEATURES if f in X.columns]
        
        preprocessor = ColumnTransformer(
            transformers=[('scaler', StandardScaler(), scale_features)],
            remainder='passthrough'
        )
        
        return preprocessor
    
    def fine_tune(self,
                  new_data: pd.DataFrame,
                  additional_iterations: int = 500,
                  learning_rate: float = 0.03,
                  validate: bool = True,
                  validation_split: float = 0.2) -> Dict[str, any]:
        """
        Fine-tune the existing model on new data.
        
        Uses CatBoost's init_model parameter for warm starting.
        
        Args:
            new_data: DataFrame with new training data
            additional_iterations: Number of additional boosting iterations
            learning_rate: Learning rate for fine-tuning (lower = more conservative)
            validate: Whether to validate on holdout set
            validation_split: Fraction for validation
        
        Returns:
            Results dict with metrics and paths
        """
        print("="*60)
        print("FINE-TUNING MODEL")
        print("="*60)
        
        start_time = datetime.now()
        
        # Prepare data
        print(f"\n📊 Preparing {len(new_data)} samples...")
        X, y = self._prepare_data(new_data)
        
        print(f"   Features: {len(X.columns)}")
        print(f"   Targets: {list(y.columns)}")
        
        # Split for validation if requested
        if validate and len(X) > 100:
            split_idx = int(len(X) * (1 - validation_split))
            X_train, X_val = X.iloc[:split_idx], X.iloc[split_idx:]
            y_train, y_val = y.iloc[:split_idx], y.iloc[split_idx:]
            print(f"   Train/Val split: {len(X_train)}/{len(X_val)}")
        else:
            X_train, X_val = X, None
            y_train, y_val = y, None
        
        # Create preprocessor and transform
        print("\n🔧 Preprocessing features...")
        preprocessor = self._create_preprocessor(X_train)
        X_train_prep = preprocessor.fit_transform(X_train)
        
        if X_val is not None:
            X_val_prep = preprocessor.transform(X_val)
        
        # Fine-tune each target model
        print("\n🚀 Fine-tuning models...")
        fine_tuned_models = []
        metrics = {}
        
        for i, target in enumerate(TARGET_FEATURES):
            print(f"\n   {target}:")
            
            # Get existing model if available and compatible
            init_model = None
            if (self.existing_models is not None and 
                isinstance(self.existing_models, list) and 
                len(self.existing_models) > i):
                existing = self.existing_models[i]
                if hasattr(existing, 'save_model'):  # CatBoost model
                    # Save to temp file for init_model
                    temp_path = self.output_dir / f'temp_init_model_{target}.cbm'
                    existing.save_model(str(temp_path))
                    init_model = str(temp_path)
                    print(f"      Using existing model for warm start")
            
            # Create new model
            new_model = CatBoostRegressor(
                iterations=additional_iterations,
                depth=8,
                learning_rate=learning_rate,
                l2_leaf_reg=2.5,
                loss_function='Quantile:alpha=0.60',
                random_seed=42,
                verbose=False,
                thread_count=-1
            )
            
            # Log-transform target
            y_train_target = np.log1p(y_train[target])
            
            # Fine-tune
            if init_model:
                new_model.fit(X_train_prep, y_train_target, init_model=init_model)
                # Clean up temp file
                Path(init_model).unlink(missing_ok=True)
            else:
                new_model.fit(X_train_prep, y_train_target)
            
            fine_tuned_models.append(new_model)
            
            # Validate if requested
            if X_val is not None:
                y_pred = np.expm1(new_model.predict(X_val_prep))
                mae = mean_absolute_error(y_val[target], y_pred)
                r2 = r2_score(y_val[target], y_pred)
                
                metrics[target] = {
                    'mae': round(mae, 4),
                    'r2': round(r2, 4)
                }
                print(f"      Validation MAE: {mae:.4f}, R²: {r2:.4f}")
        
        # Save fine-tuned models
        print("\n💾 Saving fine-tuned model...")
        output_path = self.output_dir / 'rf_model_finetuned.joblib'
        joblib.dump(fine_tuned_models, output_path)
        
        # Update metadata
        fine_tune_count = self.metadata.get('fine_tune_count', 0) + 1
        new_metadata = self.metadata.copy()
        new_metadata.update({
            'version': f"{self.metadata.get('version', 'v6')}_ft{fine_tune_count}",
            'last_fine_tune': datetime.now().isoformat(),
            'fine_tune_count': fine_tune_count,
            'fine_tune_samples': len(new_data),
            'fine_tune_iterations': additional_iterations,
            'fine_tune_learning_rate': learning_rate,
            'fine_tune_metrics': metrics
        })
        
        metadata_output = self.output_dir / 'rf_model_finetuned_metadata.json'
        joblib.dump(new_metadata, metadata_output)
        
        duration = (datetime.now() - start_time).total_seconds()
        
        print(f"\n✅ Fine-tuning complete in {duration:.1f}s")
        print(f"   Model saved to: {output_path}")
        print(f"   Ready for deployment with: python src/deploy_model.py --fine-tuned")
        
        return {
            'status': 'success',
            'model_path': str(output_path),
            'metadata_path': str(metadata_output),
            'samples_used': len(new_data),
            'duration_seconds': duration,
            'metrics': metrics,
            'fine_tune_count': fine_tune_count
        }


def fine_tune_catboost(data_path: str,
                       additional_iterations: int = 500,
                       learning_rate: float = 0.03) -> Dict:
    """
    Convenience function to fine-tune model on new data file.
    
    Args:
        data_path: Path to CSV with new training data
        additional_iterations: Number of additional boosting iterations
        learning_rate: Learning rate for fine-tuning
    
    Returns:
        Results dict
    """
    print(f"📂 Loading data from {data_path}...")
    df = pd.read_csv(data_path)
    
    tuner = FineTuner()
    return tuner.fine_tune(
        new_data=df,
        additional_iterations=additional_iterations,
        learning_rate=learning_rate
    )


def fine_tune_from_monitor_data(days: int = 30,
                                 min_samples: int = 500,
                                 additional_iterations: int = 500) -> Optional[Dict]:
    """
    Fine-tune model using data accumulated by the model monitor.
    
    This is the recommended approach for scheduled fine-tuning.
    
    Args:
        days: Number of days of data to use
        min_samples: Minimum samples required
        additional_iterations: Number of additional iterations
    
    Returns:
        Results dict or None if insufficient data
    """
    from src.model_monitor import ModelMonitor
    
    print("📊 Loading accumulated training data from monitor...")
    monitor = ModelMonitor()
    
    df = monitor.get_training_data(days=days, min_samples=min_samples)
    
    if df is None:
        print("❌ Insufficient training data for fine-tuning")
        print(f"   Need at least {min_samples} samples from last {days} days")
        return None
    
    print(f"✅ Loaded {len(df)} samples from last {days} days")
    
    tuner = FineTuner()
    return tuner.fine_tune(
        new_data=df,
        additional_iterations=additional_iterations,
        learning_rate=0.03
    )


def fine_tune_from_processed_data(additional_iterations: int = 500) -> Dict:
    """
    Fine-tune on the latest combined_features.csv.
    
    Uses a rolling window of recent data.
    
    Args:
        additional_iterations: Number of additional iterations
    
    Returns:
        Results dict
    """
    from datetime import timedelta
    
    print("📂 Loading combined_features.csv...")
    df = pd.read_csv('data/processed/combined_features.csv')
    
    # Use only recent data (last 30 days relative to max date in data)
    if 'datetime' in df.columns:
        df['datetime'] = pd.to_datetime(df['datetime'])
        max_date = df['datetime'].max()
        cutoff = max_date - timedelta(days=30)
        df_recent = df[df['datetime'] >= cutoff]
        print(f"   Using {len(df_recent)} samples from last 30 days (of {len(df)} total)")
        df = df_recent
    
    tuner = FineTuner()
    return tuner.fine_tune(
        new_data=df,
        additional_iterations=additional_iterations,
        learning_rate=0.03
    )


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Fine-tune demand prediction model')
    parser.add_argument('--data', type=str, help='Path to new training data CSV')
    parser.add_argument('--days', type=int, default=30, help='Days of monitor data to use')
    parser.add_argument('--iterations', type=int, default=500, help='Additional iterations')
    parser.add_argument('--from-monitor', action='store_true', help='Use monitor accumulated data')
    parser.add_argument('--from-processed', action='store_true', help='Use combined_features.csv')
    
    args = parser.parse_args()
    
    if args.data:
        result = fine_tune_catboost(args.data, args.iterations)
    elif args.from_monitor:
        result = fine_tune_from_monitor_data(days=args.days, additional_iterations=args.iterations)
    elif args.from_processed:
        result = fine_tune_from_processed_data(args.iterations)
    else:
        print("Usage:")
        print("  python src/fine_tune_model.py --data path/to/new_data.csv")
        print("  python src/fine_tune_model.py --from-monitor --days 30")
        print("  python src/fine_tune_model.py --from-processed")
        exit(1)
    
    if result:
        print(f"\n✅ Fine-tuning completed successfully")
        print(f"   Duration: {result['duration_seconds']:.1f}s")
        print(f"   Samples: {result['samples_used']}")
