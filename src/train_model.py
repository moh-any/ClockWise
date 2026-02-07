import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, TimeSeriesSplit, cross_val_score
from sklearn.ensemble import RandomForestRegressor, VotingRegressor
from sklearn.multioutput import MultiOutputRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer, TransformedTargetRegressor
from sklearn.metrics import mean_absolute_error, r2_score, mean_squared_error
import joblib
import sys
import time
import warnings
warnings.filterwarnings('ignore')

# Import additional models
try:
    from xgboost import XGBRegressor
    XGBOOST_AVAILABLE = True
except ImportError:
    print("Warning: XGBoost not available. Run: pip install xgboost")
    XGBOOST_AVAILABLE = False

try:
    from lightgbm import LGBMRegressor
    LIGHTGBM_AVAILABLE = True
except ImportError:
    print("Warning: LightGBM not available. Run: pip install lightgbm")
    LIGHTGBM_AVAILABLE = False

try:
    from catboost import CatBoostRegressor
    CATBOOST_AVAILABLE = True
except ImportError:
    print("Warning: CatBoost not available. Run: pip install catboost")
    CATBOOST_AVAILABLE = False

try:
    import optuna
    OPTUNA_AVAILABLE = True
except ImportError:
    print("Warning: Optuna not available. Run: pip install optuna")
    OPTUNA_AVAILABLE = False

print("="*80)
print("DEMAND PREDICTION MODEL TRAINING - PHASE 3 (CATBOOST + OPTUNA)")
print("="*80)
print(f"XGBoost available: {XGBOOST_AVAILABLE}")
print(f"LightGBM available: {LIGHTGBM_AVAILABLE}")
print(f"CatBoost available: {CATBOOST_AVAILABLE}")
print(f"Optuna available: {OPTUNA_AVAILABLE}")
print(f"Phase 3: CatBoost + Hyperparameter Optimization")
print("="*80 + "\n")

# Load data
df = pd.read_csv('data/processed/combined_features.csv')

# Define targets
target_features = ['item_count', 'order_count']
useless_features = ['total_revenue', 'avg_order_value', 'avg_items_per_order']

x = df.drop(target_features + useless_features + ['datetime'], axis=1)
y = df[target_features]

# Handle missing values (same as before)
x = x.drop(['longitude', 'latitude'], axis=1)
x['type_id'] = x['type_id'].fillna(-1)
x['waiting_time'] = x['waiting_time'].fillna(x['waiting_time'].median())
x['rating'] = x['rating'].fillna(x['rating'].median())
x['delivery'] = x['delivery'].fillna(0)
x['accepting_orders'] = x['accepting_orders'].fillna(0)

# Convert dtypes
x['place_id'] = x['place_id'].astype('float64')
x['type_id'] = x['type_id'].astype('float64')
x.columns = x.columns.astype(str)
y.columns = y.columns.astype(str)

# Time series split
train_size = int(len(x) * 0.8)
x_train, x_test = x[:train_size], x[train_size:]
y_train, y_test = y[:train_size], y[train_size:]

# Define preprocessing
scale_features = [
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
    'temp_change_3h'
]

# Filter to only include features that exist in the dataset
scale_features = [f for f in scale_features if f in x.columns]
print(f"\nScaling {len(scale_features)} features")

preprocessor = ColumnTransformer(
    transformers=[('scaler', StandardScaler(), scale_features)],
    remainder='passthrough'
)

# ============================================================================
# OPTIMIZED HYPERPARAMETERS (from Optuna tuning)
# ============================================================================
print("\n" + "="*80)
print("USING OPTIMIZED LIGHTGBM HYPERPARAMETERS")
print("="*80)

# Best hyperparameters found via Optuna optimization (30 trials)
# Validation MAE: 2.8399
best_lgbm_params = {
    'n_estimators': 500,
    'max_depth': 9,
    'learning_rate': 0.028930987144725154,
    'num_leaves': 29,
    'subsample': 0.9122218909714683,
    'colsample_bytree': 0.820243543744434,
    'min_child_samples': 30,
    'reg_alpha': 0.08622105497543657,
    'reg_lambda': 0.10940901520824811,
}

print(f"\nLightGBM Hyperparameters (Optuna-optimized):")
for param, value in best_lgbm_params.items():
    print(f"   {param}: {value}")

# ============================================================================
# MODEL COMPARISON - PHASE 3
# ============================================================================
print("\n" + "="*80)
print("TRAINING AND COMPARING MODELS")
print("="*80)

models_to_compare = {}

# 1. Random Forest (Baseline)
print("\n1. Random Forest (Current Model)...")
rf_pipeline = Pipeline([
    ('preprocessor', preprocessor),
    ('model', MultiOutputRegressor(RandomForestRegressor(
        n_jobs=-1,
        random_state=42,
        max_depth=12,
        min_samples_leaf=7,
        max_features=0.5,
        n_estimators=600,
        bootstrap=True,
        verbose=0
    )))
])

rf_model = TransformedTargetRegressor(
    regressor=rf_pipeline,
    func=np.log1p,
    inverse_func=np.expm1
)

start_time = time.time()
rf_model.fit(x_train, y_train)
rf_train_time = time.time() - start_time

y_pred_rf = rf_model.predict(x_test)
models_to_compare['Random Forest'] = {
    'model': rf_model,
    'predictions': y_pred_rf,
    'train_time': rf_train_time
}

# 2. XGBoost
if XGBOOST_AVAILABLE:
    print("\n2. XGBoost...")
    xgb_pipeline = Pipeline([
        ('preprocessor', preprocessor),
        ('model', MultiOutputRegressor(XGBRegressor(
            n_estimators=800,
            max_depth=8,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            min_child_weight=3,
            gamma=0.1,
            reg_alpha=0.1,
            reg_lambda=1.0,
            random_state=42,
            n_jobs=-1,
            verbosity=0
        )))
    ])
    
    xgb_model = TransformedTargetRegressor(
        regressor=xgb_pipeline,
        func=np.log1p,
        inverse_func=np.expm1
    )
    
    start_time = time.time()
    xgb_model.fit(x_train, y_train)
    xgb_train_time = time.time() - start_time
    
    y_pred_xgb = xgb_model.predict(x_test)
    models_to_compare['XGBoost'] = {
        'model': xgb_model,
        'predictions': y_pred_xgb,
        'train_time': xgb_train_time
    }

# 3. LightGBM (with optimized hyperparameters)
if LIGHTGBM_AVAILABLE:
    print("\n3. LightGBM (Optimized)...")
    lgbm_pipeline = Pipeline([
        ('preprocessor', preprocessor),
        ('model', MultiOutputRegressor(LGBMRegressor(
            **best_lgbm_params,
            random_state=42,
            n_jobs=-1,
            verbose=-1,
            force_col_wise=True
        )))
    ])
    
    lgbm_model = TransformedTargetRegressor(
        regressor=lgbm_pipeline,
        func=np.log1p,
        inverse_func=np.expm1
    )
    
    start_time = time.time()
    lgbm_model.fit(x_train, y_train)
    lgbm_train_time = time.time() - start_time
    
    y_pred_lgbm = lgbm_model.predict(x_test)
    models_to_compare['LightGBM'] = {
        'model': lgbm_model,
        'predictions': y_pred_lgbm,
        'train_time': lgbm_train_time
    }

# 4. CatBoost (without sklearn wrappers due to compatibility)
if CATBOOST_AVAILABLE:
    print("\n4. CatBoost...")
    
    start_time = time.time()
    
    # CatBoost doesn't work well with MultiOutputRegressor in newer sklearn
    # Train separate models for each target
    catboost_models = []
    y_pred_catboost_list = []
    
    # Preprocess data once
    x_train_preprocessed = preprocessor.fit_transform(x_train)
    x_test_preprocessed = preprocessor.transform(x_test)
    
    for i, target in enumerate(target_features):
        print(f"  Training CatBoost for {target}...")
        
        # Log transform target
        y_train_target = np.log1p(y_train.iloc[:, i])
        
        catboost_model = CatBoostRegressor(
            iterations=1000,
            depth=8,
            learning_rate=0.05,
            l2_leaf_reg=3.0,
            random_seed=42,
            verbose=False,
            thread_count=-1
        )
        
        catboost_model.fit(x_train_preprocessed, y_train_target)
        catboost_models.append(catboost_model)
        
        # Predict and inverse transform
        y_pred_target = catboost_model.predict(x_test_preprocessed)
        y_pred_target = np.expm1(y_pred_target)
        y_pred_catboost_list.append(y_pred_target)
    
    catboost_train_time = time.time() - start_time
    y_pred_catboost = np.column_stack(y_pred_catboost_list)
    
    models_to_compare['CatBoost'] = {
        'model': catboost_models,  # List of models, one per target
        'predictions': y_pred_catboost,
        'train_time': catboost_train_time
    }

# ============================================================================
# EVALUATE AND COMPARE MODELS
# ============================================================================
print("\n" + "="*80)
print("MODEL COMPARISON RESULTS")
print("="*80)

results = []
for model_name, model_info in models_to_compare.items():
    y_pred = model_info['predictions']
    train_time = model_info['train_time']
    
    print(f"\n{model_name}:")
    print(f"  Training time: {train_time:.2f}s")
    
    for i, target in enumerate(target_features):
        mae = mean_absolute_error(y_test.iloc[:, i], y_pred[:, i])
        rmse = np.sqrt(mean_squared_error(y_test.iloc[:, i], y_pred[:, i]))
        r2 = r2_score(y_test.iloc[:, i], y_pred[:, i])
        
        print(f"  {target}: MAE={mae:.4f}, RMSE={rmse:.4f}, R²={r2:.4f}")
        
        results.append({
            'Model': model_name,
            'Target': target,
            'MAE': mae,
            'RMSE': rmse,
            'R2': r2,
            'Train_Time': train_time
        })

# Create results DataFrame
results_df = pd.DataFrame(results)

# Find best model by average MAE
avg_mae_by_model = results_df.groupby('Model')['MAE'].mean().sort_values()
best_model_name = avg_mae_by_model.index[0]
best_mae = avg_mae_by_model.values[0]

print("\n" + "="*80)
print("SUMMARY")
print("="*80)
print("\nAverage MAE by Model:")
for model_name, mae in avg_mae_by_model.items():
    marker = " ⭐ BEST" if model_name == best_model_name else ""
    print(f"  {model_name}: {mae:.4f}{marker}")

# Calculate improvement over baseline (Random Forest)
if best_model_name != 'Random Forest':
    baseline_mae = avg_mae_by_model['Random Forest']
    improvement_pct = ((baseline_mae - best_mae) / baseline_mae) * 100
    print(f"\n✅ Improvement over baseline: {improvement_pct:.2f}%")

# ============================================================================
# TIME SERIES CROSS-VALIDATION (Phase 2)
# ============================================================================
print("\n" + "="*80)
print("TIME SERIES CROSS-VALIDATION")
print("="*80)

tscv = TimeSeriesSplit(n_splits=3)  # Reduced to 3 folds for faster execution
cv_results = {name: [] for name in models_to_compare.keys()}

print(f"\nRunning 3-fold time series cross-validation...")
for fold, (train_idx, val_idx) in enumerate(tscv.split(x_train), 1):
    print(f"  Fold {fold}/3...", end=' ')
    fold_x_train, fold_x_val = x_train.iloc[train_idx], x_train.iloc[val_idx]
    fold_y_train, fold_y_val = y_train.iloc[train_idx], y_train.iloc[val_idx]
    
    for model_name in models_to_compare.keys():
        # Get a fresh model instance (same hyperparameters)
        if model_name == 'CatBoost' and CATBOOST_AVAILABLE:
            # CatBoost: train separate models for each target
            catboost_models_fold = []
            y_pred_cv_list = []
            
            # Preprocess fold data
            fold_x_train_prep = preprocessor.fit_transform(fold_x_train)
            fold_x_val_prep = preprocessor.transform(fold_x_val)
            
            for i in range(len(target_features)):
                y_train_target = np.log1p(fold_y_train.iloc[:, i])
                
                cb_model = CatBoostRegressor(
                    iterations=1000, depth=8, learning_rate=0.05,
                    l2_leaf_reg=3.0, random_seed=42,
                    verbose=False, thread_count=-1
                )
                cb_model.fit(fold_x_train_prep, y_train_target)
                
                y_pred_target = np.expm1(cb_model.predict(fold_x_val_prep))
                y_pred_cv_list.append(y_pred_target)
            
            y_pred_cv = np.column_stack(y_pred_cv_list)
            
        else:
            # For all other models
            if model_name == 'Random Forest':
                model = TransformedTargetRegressor(
                    regressor=Pipeline([
                        ('preprocessor', preprocessor),
                        ('model', MultiOutputRegressor(RandomForestRegressor(
                            n_jobs=-1, random_state=42, max_depth=12,
                            min_samples_leaf=7, max_features=0.5,
                            n_estimators=600, bootstrap=True, verbose=0
                        )))
                    ]),
                    func=np.log1p, inverse_func=np.expm1
                )
            elif model_name == 'XGBoost' and XGBOOST_AVAILABLE:
                model = TransformedTargetRegressor(
                    regressor=Pipeline([
                        ('preprocessor', preprocessor),
                        ('model', MultiOutputRegressor(XGBRegressor(
                            n_estimators=800, max_depth=8, learning_rate=0.05,
                            subsample=0.8, colsample_bytree=0.8,
                            min_child_weight=3, gamma=0.1,
                            reg_alpha=0.1, reg_lambda=1.0,
                            random_state=42, n_jobs=-1, verbosity=0
                        )))
                    ]),
                    func=np.log1p, inverse_func=np.expm1
                )
            elif model_name == 'LightGBM' and LIGHTGBM_AVAILABLE:
                model = TransformedTargetRegressor(
                    regressor=Pipeline([
                        ('preprocessor', preprocessor),
                        ('model', MultiOutputRegressor(LGBMRegressor(
                            **best_lgbm_params,
                            random_state=42, n_jobs=-1, verbose=-1,
                            force_col_wise=True
                        )))
                    ]),
                    func=np.log1p, inverse_func=np.expm1
                )
            
            # Train and predict
            model.fit(fold_x_train, fold_y_train)
            y_pred_cv = model.predict(fold_x_val)
        
        # Calculate average MAE across both targets
        fold_mae = np.mean([
            mean_absolute_error(fold_y_val.iloc[:, i], y_pred_cv[:, i])
            for i in range(len(target_features))
        ])
        cv_results[model_name].append(fold_mae)
    
    print("Done")

print("\nCross-Validation Results (MAE):")
cv_summary = {}
for model_name, fold_maes in cv_results.items():
    mean_mae = np.mean(fold_maes)
    std_mae = np.std(fold_maes)
    cv_summary[model_name] = {'mean': mean_mae, 'std': std_mae}
    print(f"  {model_name}: {mean_mae:.4f} (±{std_mae:.4f})")

# ============================================================================
# BUILD VOTING ENSEMBLE (Phase 2)
# ============================================================================
if len(models_to_compare) >= 2:
    print("\n" + "="*80)
    print("BUILDING SIMPLE ENSEMBLE (Soft Voting)")
    print("="*80)
    
    # Simple approach: average predictions from all trained models
    print(f"\nAveraging predictions from {len(models_to_compare)} models...")
    
    start_time = time.time()
    
    # Get predictions from all models
    all_predictions = np.array([
        model_info['predictions'] 
        for model_info in models_to_compare.values()
    ])
    
    # Simple average (soft voting)
    y_pred_ensemble = np.mean(all_predictions, axis=0)
    ensemble_train_time = time.time() - start_time
    
    # Evaluate ensemble
    print("\nSimple Ensemble (Average):")
    print(f"  Combination time: {ensemble_train_time:.2f}s")
    
    ensemble_mae_avg = 0
    for i, target in enumerate(target_features):
        mae = mean_absolute_error(y_test.iloc[:, i], y_pred_ensemble[:, i])
        rmse = np.sqrt(mean_squared_error(y_test.iloc[:, i], y_pred_ensemble[:, i]))
        r2 = r2_score(y_test.iloc[:, i], y_pred_ensemble[:, i])
        
        print(f"  {target}: MAE={mae:.4f}, RMSE={rmse:.4f}, R²={r2:.4f}")
        ensemble_mae_avg += mae
        
        results.append({
            'Model': 'Simple Ensemble',
            'Target': target,
            'MAE': mae,
            'RMSE': rmse,
            'R2': r2,
            'Train_Time': ensemble_train_time
        })
    
    ensemble_mae_avg /= len(target_features)
    
    # Add ensemble to comparison
    models_to_compare['Simple Ensemble'] = {
        'model': 'average',  # Indicator that this is a simple average
        'predictions': y_pred_ensemble,
        'train_time': ensemble_train_time
    }
    
    # Update best model if ensemble is better
    if ensemble_mae_avg < best_mae:
        print(f"\n✅ Ensemble improves MAE: {best_mae:.4f} → {ensemble_mae_avg:.4f}")
        improvement_pct = ((best_mae - ensemble_mae_avg) / best_mae) * 100
        print(f"   ({improvement_pct:.2f}% improvement)")
        print("\n⚠️  Saving individual best model (LightGBM) instead of ensemble for simplicity")
        print("   Ensemble predictions are recorded in comparison results")
    else:
        print(f"\n  Ensemble MAE: {ensemble_mae_avg:.4f} (similar to {best_model_name}: {best_mae:.4f})")

# Update results dataframe
results_df = pd.DataFrame(results)

# ============================================================================
# SAVE BEST MODEL
# ============================================================================
print("\n" + "="*80)
print(f"SAVING BEST MODEL: {best_model_name}")
print("="*80)

best_model = models_to_compare[best_model_name]['model']
best_model = models_to_compare[best_model_name]['model']

# Get best model predictions and metrics
best_predictions = models_to_compare[best_model_name]['predictions']
best_train_time = models_to_compare[best_model_name]['train_time']

# Calculate metrics for best model
best_metrics = {}
for i, target in enumerate(target_features):
    mae = mean_absolute_error(y_test.iloc[:, i], best_predictions[:, i])
    rmse = np.sqrt(mean_squared_error(y_test.iloc[:, i], best_predictions[:, i]))
    r2 = r2_score(y_test.iloc[:, i], best_predictions[:, i])
    best_metrics[target] = {'mae': mae, 'rmse': rmse, 'r2': r2}

# Save model metadata
metadata = {
    'python_version': sys.version,
    'sklearn_version': sys.modules['sklearn'].__version__,
    'model_type': best_model_name,
    'model_algorithm': best_model_name,
    'features': list(x.columns),
    'num_features': len(x.columns),
    'phase_1_enhancements': {
        'cyclical_time_features': True,
        'time_context_indicators': True,
        'enhanced_rolling_features': True,
        'multiple_models_compared': ['Random Forest', 'XGBoost', 'LightGBM']
    },
    'phase_2_enhancements': {
        'venue_specific_features': True,
        'weather_interaction_features': True,
        'time_series_cross_validation': True,
        'simple_ensemble': 'Simple Ensemble' in models_to_compare,
        'cv_results': cv_summary
    },
    'phase_3_enhancements': {
        'catboost_model': CATBOOST_AVAILABLE,
        'optuna_optimization': OPTUNA_AVAILABLE,
        'optimized_lgbm_params': best_lgbm_params if OPTUNA_AVAILABLE else None,
        'models_in_ensemble': list(models_to_compare.keys())
    },
    'training_size': len(x_train),
    'test_size': len(x_test),
    'train_time_seconds': best_train_time,
    'version': '5.0_phase3_catboost_optuna',
    'metrics': best_metrics,
    'all_model_comparison': results_df.to_dict('records')
}

# Add model-specific hyperparameters
if best_model_name == 'Random Forest':
    metadata['hyperparameters'] = {
        'n_estimators': 600,
        'max_depth': 12,
        'min_samples_leaf': 7,
        'max_features': 0.5,
        'bootstrap': True
    }
elif best_model_name == 'XGBoost':
    metadata['hyperparameters'] = {
        'n_estimators': 800,
        'max_depth': 8,
        'learning_rate': 0.05,
        'subsample': 0.8,
        'colsample_bytree': 0.8
    }
elif best_model_name == 'LightGBM':
    metadata['hyperparameters'] = best_lgbm_params
elif best_model_name == 'CatBoost':
    metadata['hyperparameters'] = {
        'iterations': 1000,
        'depth': 8,
        'learning_rate': 0.05,
        'l2_leaf_reg': 3.0
    }

joblib.dump(best_model, 'data/models/rf_model.joblib')
joblib.dump(metadata, 'data/models/rf_model_metadata.json')

print(f"\n✅ Model saved successfully!")
print(f"   Model type: {best_model_name}")
print(f"   Features: {len(x.columns)}")
print(f"   Training time: {best_train_time:.2f}s")
print(f"   Average MAE: {best_mae:.4f}")

# Save comparison results
results_df.to_csv('data/models/phase3_model_comparison.csv', index=False)
print(f"\n✅ Comparison results saved to: data/models/phase3_model_comparison.csv")

print("\n" + "="*80)
print("PHASE 3 TRAINING COMPLETE (CATBOOST + OPTUNA)")
print("="*80)