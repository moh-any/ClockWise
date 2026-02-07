import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, TimeSeriesSplit, cross_val_score
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier, VotingRegressor
from sklearn.multioutput import MultiOutputRegressor
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer, TransformedTargetRegressor
from sklearn.metrics import mean_absolute_error, r2_score, mean_squared_error, accuracy_score, classification_report
from sklearn.impute import KNNImputer
import joblib
import sys
import time
import warnings
warnings.filterwarnings('ignore')

# Import additional models
try:
    from xgboost import XGBRegressor, XGBClassifier
    XGBOOST_AVAILABLE = True
except ImportError:
    print("Warning: XGBoost not available. Run: pip install xgboost")
    XGBOOST_AVAILABLE = False

try:
    from lightgbm import LGBMRegressor, LGBMClassifier
    LIGHTGBM_AVAILABLE = True
except ImportError:
    print("Warning: LightGBM not available. Run: pip install lightgbm")
    LIGHTGBM_AVAILABLE = False

try:
    from catboost import CatBoostRegressor, CatBoostClassifier
    CATBOOST_AVAILABLE = True
except ImportError:
    print("Warning: CatBoost not available. Run: pip install catboost")
    CATBOOST_AVAILABLE = False

print("="*80)
print("DEMAND PREDICTION MODEL TRAINING - PHASE 4 (DATA QUALITY IMPROVEMENTS)")
print("="*80)
print(f"XGBoost available: {XGBOOST_AVAILABLE}")
print(f"LightGBM available: {LIGHTGBM_AVAILABLE}")
print(f"CatBoost available: {CATBOOST_AVAILABLE}")
print(f"Phase 4: Outlier Treatment + KNN Imputation + Robust Scaling")
print("="*80 + "\n")

# ============================================================================
# DATA QUALITY IMPROVEMENT FUNCTIONS
# ============================================================================

def apply_outlier_treatment(df, columns, method='iqr', lower_multiplier=2, upper_multiplier=3):
    """
    Apply outlier treatment to specified columns using IQR method
    
    Parameters:
    -----------
    df : pd.DataFrame
        Input dataframe
    columns : list
        Columns to apply outlier treatment
    method : str
        'iqr' for IQR-based capping
    lower_multiplier : float
        Multiplier for lower bound (default 2)
    upper_multiplier : float
        Multiplier for upper bound (default 3)
        
    Returns:
    --------
    pd.DataFrame : DataFrame with capped outliers
    dict : Statistics about outliers
    """
    df_treated = df.copy()
    stats = {}
    
    for col in columns:
        if col not in df.columns:
            continue
            
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        
        lower_bound = max(0, Q1 - lower_multiplier * IQR)
        upper_bound = Q3 + upper_multiplier * IQR
        
        # Count outliers
        outliers = ((df[col] < lower_bound) | (df[col] > upper_bound)).sum()
        
        # Cap outliers
        df_treated[col] = df[col].clip(lower_bound, upper_bound)
        
        stats[col] = {
            'outliers_count': outliers,
            'outliers_pct': 100 * outliers / len(df),
            'lower_bound': lower_bound,
            'upper_bound': upper_bound,
            'original_min': df[col].min(),
            'original_max': df[col].max(),
            'capped_min': df_treated[col].min(),
            'capped_max': df_treated[col].max()
        }
    
    return df_treated, stats


def apply_knn_imputation(x_data, n_neighbors=5):
    """
    Apply KNN imputation for missing values
    
    Parameters:
    -----------
    x_data : pd.DataFrame
        Features with missing values
    n_neighbors : int
        Number of neighbors for KNN imputation
        
    Returns:
    --------
    pd.DataFrame : Imputed features
    """
    imputer = KNNImputer(n_neighbors=n_neighbors, weights='distance')
    
    # Store column names and index
    columns = x_data.columns
    index = x_data.index
    
    # Apply imputation
    x_imputed = imputer.fit_transform(x_data)
    
    # Convert back to DataFrame
    x_imputed_df = pd.DataFrame(x_imputed, columns=columns, index=index)
    
    return x_imputed_df, imputer


# ============================================================================
# SAMPLE WEIGHTING FUNCTION
# ============================================================================
def calculate_sample_weights(y_data, weight_type='combined', temporal_range=(0.5, 1.0)):
    """Calculate sample weights for training data"""
    n = len(y_data)
    
    if weight_type == 'temporal':
        weights = np.linspace(temporal_range[0], temporal_range[1], n)
    elif weight_type == 'demand':
        weights = np.log1p(y_data.iloc[:, 0]) + 1
    elif weight_type == 'combined':
        temporal_weights = np.linspace(temporal_range[0], temporal_range[1], n)
        demand_weights = np.log1p(y_data.iloc[:, 0]) + 1
        demand_weights = (demand_weights - demand_weights.min()) / (demand_weights.max() - demand_weights.min())
        demand_weights = demand_weights * (temporal_range[1] - temporal_range[0]) + temporal_range[0]
        weights = temporal_weights * demand_weights
    else:
        weights = np.ones(n)
    
    return weights


# ============================================================================
# LOAD AND PREPARE DATA
# ============================================================================
print("\n" + "="*80)
print("LOADING DATA")
print("="*80)

df = pd.read_csv('data/processed/combined_features.csv')
print(f"Loaded {len(df)} samples with {len(df.columns)} columns")

# Define targets
target_features = ['item_count', 'order_count']
useless_features = ['total_revenue', 'avg_order_value', 'avg_items_per_order']

# Separate features and targets
x = df.drop(target_features + useless_features + ['datetime'], axis=1)
y = df[target_features].copy()

print(f"\nFeatures: {len(x.columns)}")
print(f"Targets: {target_features}")
print(f"Target statistics:")
for col in target_features:
    print(f"  {col}: mean={y[col].mean():.2f}, std={y[col].std():.2f}, median={y[col].median():.2f}")

# ============================================================================
# PHASE 4.2: OUTLIER TREATMENT
# ============================================================================
print("\n" + "="*80)
print("PHASE 4.2: OUTLIER TREATMENT")
print("="*80)

# Apply outlier treatment to target variables
outlier_columns = ['item_count', 'order_count']
y_treated, outlier_stats = apply_outlier_treatment(
    y, 
    outlier_columns, 
    method='iqr',
    lower_multiplier=2,
    upper_multiplier=3
)

print("\nOutlier Treatment Results:")
for col, stats in outlier_stats.items():
    print(f"\n{col}:")
    print(f"  Outliers found: {stats['outliers_count']} ({stats['outliers_pct']:.2f}%)")
    print(f"  Original range: [{stats['original_min']:.2f}, {stats['original_max']:.2f}]")
    print(f"  Capped range: [{stats['capped_min']:.2f}, {stats['capped_max']:.2f}]")
    print(f"  Bounds: [{stats['lower_bound']:.2f}, {stats['upper_bound']:.2f}]")

# Use treated targets
y = y_treated

# ============================================================================
# PHASE 4.3: BETTER MISSING VALUE HANDLING
# ============================================================================
print("\n" + "="*80)
print("PHASE 4.3: MISSING VALUE HANDLING (KNN IMPUTATION)")
print("="*80)

# Drop features with too many missing values
x = x.drop(['longitude', 'latitude'], axis=1, errors='ignore')

# Check missing values
missing_counts = x.isnull().sum()
missing_features = missing_counts[missing_counts > 0]

if len(missing_features) > 0:
    print(f"\nFeatures with missing values:")
    for feat, count in missing_features.items():
        pct = 100 * count / len(x)
        print(f"  {feat}: {count} ({pct:.2f}%)")
    
    print(f"\nApplying KNN imputation (k=5)...")
    
    # First, handle categorical features that need simple imputation
    if 'type_id' in x.columns:
        x['type_id'] = x['type_id'].fillna(-1)
    if 'delivery' in x.columns:
        x['delivery'] = x['delivery'].fillna(0)
    if 'accepting_orders' in x.columns:
        x['accepting_orders'] = x['accepting_orders'].fillna(0)
    
    # Then apply KNN imputation to remaining features with missing values
    missing_mask = x.isnull().any(axis=1)
    if missing_mask.sum() > 0:
        x_imputed, imputer = apply_knn_imputation(x, n_neighbors=5)
        x = x_imputed
        print(f"✅ KNN imputation completed")
    else:
        print(f"✅ No missing values remaining after simple imputation")
else:
    print("No missing values found in features")

# Convert dtypes
x['place_id'] = x['place_id'].astype('float64')
if 'type_id' in x.columns:
    x['type_id'] = x['type_id'].astype('float64')
x.columns = x.columns.astype(str)
y.columns = y.columns.astype(str)

# ============================================================================
# TRAIN/TEST SPLIT
# ============================================================================
print("\n" + "="*80)
print("TRAIN/TEST SPLIT")
print("="*80)

# Time series split (80/20)
train_size = int(len(x) * 0.8)
x_train, x_test = x[:train_size].copy(), x[train_size:].copy()
y_train, y_test = y[:train_size].copy(), y[train_size:].copy()

print(f"Training samples: {len(x_train)} ({100*len(x_train)/len(x):.1f}%)")
print(f"Test samples: {len(x_test)} ({100*len(x_test)/len(x):.1f}%)")

# Calculate sample weights
sample_weights = calculate_sample_weights(y_train, weight_type='combined', temporal_range=(0.5, 1.0))
print(f"\nSample weights:")
print(f"  Range: [{sample_weights.min():.4f}, {sample_weights.max():.4f}]")
print(f"  Mean: {sample_weights.mean():.4f}")

# ============================================================================
# PREPROCESSING PIPELINE
# ============================================================================
print("\n" + "="*80)
print("PREPROCESSING PIPELINE")
print("="*80)

# Using RobustScaler for better outlier handling
scale_features = [
    'waiting_time', 'rating', 'avg_discount',
    'prev_hour_items', 'prev_day_items', 'prev_week_items', 
    'prev_month_items', 'rolling_7d_avg_items',
    'rolling_3d_avg_items', 'rolling_14d_avg_items', 'rolling_30d_avg_items',
    'rolling_7d_std_items', 'demand_trend_7d',
    'lag_same_hour_last_week', 'lag_same_hour_2_weeks',
    'temperature_2m', 'relative_humidity_2m', 'precipitation', 
    'rain', 'snowfall', 'cloud_cover', 'wind_speed_10m', 'weather_severity',
    'venue_hour_avg', 'venue_dow_avg', 'venue_volatility', 
    'venue_total_items', 'venue_growth_recent_vs_historical',
    'feels_like_temp', 'bad_weather_score', 'temp_change_1h', 
    'temp_change_3h'
]

# Filter to only include features that exist
scale_features = [f for f in scale_features if f in x.columns]
print(f"Scaling {len(scale_features)} features using RobustScaler")

preprocessor = ColumnTransformer(
    transformers=[
        ('robust_scaler', RobustScaler(quantile_range=(5, 95)), scale_features)
    ],
    remainder='passthrough'
)

# ============================================================================
# MODEL TRAINING WITH PHASE 4 IMPROVEMENTS
# ============================================================================
print("\n" + "="*80)
print("MODEL TRAINING WITH PHASE 4 IMPROVEMENTS")
print("="*80)

models_to_compare = {}

# Fit preprocessor once for all models
print("\nPreprocessing data...")
x_train_preprocessed = preprocessor.fit_transform(x_train)
x_test_preprocessed = preprocessor.transform(x_test)
y_train_transformed = np.log1p(y_train)
print(f"  Preprocessed shape: {x_train_preprocessed.shape}")

# Model 1: LightGBM (optimized hyperparameters)
if LIGHTGBM_AVAILABLE:
    print("\n1. LightGBM (optimized hyperparameters)...")
    
    lgbm_multioutput = MultiOutputRegressor(LGBMRegressor(
        n_estimators=500,
        max_depth=9,
        learning_rate=0.029,
        num_leaves=29,
        subsample=0.91,
        colsample_bytree=0.82,
        min_child_samples=30,
        reg_alpha=0.09,
        reg_lambda=0.11,
        random_state=42,
        n_jobs=-1,
        verbose=-1,
        force_col_wise=True
    ))
    
    start_time = time.time()
    lgbm_multioutput.fit(x_train_preprocessed, y_train_transformed, sample_weight=sample_weights)
    y_pred_transformed = lgbm_multioutput.predict(x_test_preprocessed)
    y_pred = np.expm1(y_pred_transformed)
    train_time = time.time() - start_time
    
    models_to_compare['LightGBM'] = {
        'model': lgbm_multioutput,
        'predictions': y_pred,
        'train_time': train_time
    }
    
    print(f"  Training time: {train_time:.2f}s")

# Model 2: Random Forest
print("\n2. Random Forest...")

rf_multioutput = MultiOutputRegressor(RandomForestRegressor(
    n_estimators=600,
    max_depth=12,
    min_samples_leaf=7,
    max_features=0.5,
    random_state=42,
    n_jobs=-1,
    verbose=0
))

start_time = time.time()
rf_multioutput.fit(x_train_preprocessed, y_train_transformed, sample_weight=sample_weights)
y_pred_transformed = rf_multioutput.predict(x_test_preprocessed)
y_pred = np.expm1(y_pred_transformed)
train_time = time.time() - start_time

models_to_compare['Random Forest'] = {
    'model': rf_multioutput,
    'predictions': y_pred,
    'train_time': train_time
}

print(f"  Training time: {train_time:.2f}s")

# Model 3: XGBoost
if XGBOOST_AVAILABLE:
    print("\n3. XGBoost...")
    
    xgb_multioutput = MultiOutputRegressor(XGBRegressor(
        n_estimators=500,
        max_depth=9,
        learning_rate=0.03,
        subsample=0.9,
        colsample_bytree=0.8,
        random_state=42,
        n_jobs=-1,
        verbosity=0
    ))
    
    start_time = time.time()
    xgb_multioutput.fit(x_train_preprocessed, y_train_transformed, sample_weight=sample_weights)
    y_pred_transformed = xgb_multioutput.predict(x_test_preprocessed)
    y_pred = np.expm1(y_pred_transformed)
    train_time = time.time() - start_time
    
    models_to_compare['XGBoost'] = {
        'model': xgb_multioutput,
        'predictions': y_pred,
        'train_time': train_time
    }
    
    print(f"  Training time: {train_time:.2f}s")

# Model 4: CatBoost (train separate models for each target)
if CATBOOST_AVAILABLE:
    print("\n4. CatBoost...")
    
    start_time = time.time()
    
    # Train separate models for each target
    catboost_models = []
    for i, target in enumerate(target_features):
        model = CatBoostRegressor(
            iterations=500,
            depth=9,
            learning_rate=0.03,
            l2_leaf_reg=3,
            random_state=42,
            verbose=0,
            thread_count=-1
        )
        model.fit(x_train_preprocessed, y_train_transformed.iloc[:, i], sample_weight=sample_weights)
        catboost_models.append(model)
    
    # Make predictions
    y_pred_transformed = np.column_stack([
        model.predict(x_test_preprocessed) for model in catboost_models
    ])
    y_pred = np.expm1(y_pred_transformed)
    train_time = time.time() - start_time
    
    models_to_compare['CatBoost'] = {
        'model': catboost_models,  # List of models instead of MultiOutputRegressor
        'predictions': y_pred,
        'train_time': train_time
    }
    
    print(f"  Training time: {train_time:.2f}s")

# ============================================================================
# MODEL EVALUATION
# ============================================================================
print("\n" + "="*80)
print("MODEL EVALUATION")
print("="*80)

results = []

for model_name, model_info in models_to_compare.items():
    y_pred = model_info['predictions']
    
    # Calculate metrics for each target
    metrics = {}
    for i, target in enumerate(target_features):
        y_true = y_test.iloc[:, i]
        y_pred_target = y_pred[:, i]
        
        mae = mean_absolute_error(y_true, y_pred_target)
        rmse = np.sqrt(mean_squared_error(y_true, y_pred_target))
        r2 = r2_score(y_true, y_pred_target)
        
        # WAPE (Weighted Absolute Percentage Error)
        wape = 100 * np.sum(np.abs(y_pred_target - y_true)) / np.sum(y_true)
        
        metrics[f'{target}_mae'] = mae
        metrics[f'{target}_rmse'] = rmse
        metrics[f'{target}_r2'] = r2
        metrics[f'{target}_wape'] = wape
    
    # Average MAE across both targets
    avg_mae = np.mean([metrics[f'{t}_mae'] for t in target_features])
    
    results.append({
        'model': model_name,
        'avg_mae': avg_mae,
        'item_count_mae': metrics['item_count_mae'],
        'item_count_rmse': metrics['item_count_rmse'],
        'item_count_r2': metrics['item_count_r2'],
        'item_count_wape': metrics['item_count_wape'],
        'order_count_mae': metrics['order_count_mae'],
        'order_count_rmse': metrics['order_count_rmse'],
        'order_count_r2': metrics['order_count_r2'],
        'order_count_wape': metrics['order_count_wape'],
        'train_time': model_info['train_time']
    })

# Create results DataFrame
results_df = pd.DataFrame(results).sort_values('avg_mae')

print("\n" + "="*80)
print("MODEL COMPARISON RESULTS")
print("="*80)
print(results_df.to_string(index=False))

# Select best model
best_idx = results_df['avg_mae'].idxmin()
best_row = results_df.loc[best_idx]
best_model_name = best_row['model']
best_model = models_to_compare[best_model_name]['model']
best_metrics = best_row.to_dict()

print("\n" + "="*80)
print(f"BEST MODEL: {best_model_name}")
print("="*80)
print(f"Average MAE: {best_row['avg_mae']:.4f}")
print(f"Item Count MAE: {best_row['item_count_mae']:.4f}")
print(f"Item Count R²: {best_row['item_count_r2']:.4f}")
print(f"Item Count WAPE: {best_row['item_count_wape']:.2f}%")
print(f"Order Count MAE: {best_row['order_count_mae']:.4f}")
print(f"Order Count R²: {best_row['order_count_r2']:.4f}")
print(f"Order Count WAPE: {best_row['order_count_wape']:.2f}%")
print(f"Training Time: {best_row['train_time']:.2f}s")

# ============================================================================
# SAVE MODEL
# ============================================================================
print("\n" + "="*80)
print("SAVING MODEL")
print("="*80)

metadata = {
    'model_name': best_model_name,
    'features': x.columns.tolist(),
    'targets': target_features,
    'training_size': len(x_train),
    'test_size': len(x_test),
    'train_time_seconds': best_row['train_time'],
    'version': '6.0_phase4_data_quality',
    'metrics': best_metrics,
    'all_model_comparison': results_df.to_dict('records'),
    'phase4_improvements': {
        'outlier_treatment': outlier_stats,
        'imputation_method': 'KNN (k=5)',
        'scaler': 'RobustScaler (quantile_range=(5, 95))',
        'sample_weighting': 'Combined temporal + demand-level'
    }
}

joblib.dump(best_model, 'data/models/rf_model.joblib')
joblib.dump(metadata, 'data/models/rf_model_metadata.json')

print(f"\n✅ Model saved successfully!")
print(f"   Model: {best_model_name}")
print(f"   Features: {len(x.columns)}")
print(f"   Training time: {best_row['train_time']:.2f}s")
print(f"   Average MAE: {best_row['avg_mae']:.4f}")

# Save comparison results
results_df.to_csv('data/models/phase4_model_comparison.csv', index=False)
print(f"\n✅ Comparison results saved to: data/models/phase4_model_comparison.csv")

print("\n" + "="*80)
print("PHASE 4 TRAINING COMPLETE (DATA QUALITY IMPROVEMENTS)")
print("="*80)
print("\nPhase 4 Implementations:")
print("  ✅ 4.2: Outlier Treatment (IQR-based capping)")
print("  ✅ 4.3: KNN Imputation for Missing Values")
print("  ✅ Robust Scaler for better outlier handling")
print("  ✅ Sample Weighting (combined temporal + demand-level)")
print("\nExpected improvements: 10-20% MAE reduction")
print("="*80)
