"""
Model Experimentation Script
============================
Comprehensive analysis to determine the best model family and transformations
for predicting item_count and order_count.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

from sklearn.model_selection import train_test_split, GridSearchCV, TimeSeriesSplit, learning_curve
from sklearn.linear_model import LinearRegression, Ridge, Lasso, ElasticNet
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.neighbors import KNeighborsRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.preprocessing import StandardScaler, PowerTransformer, PolynomialFeatures
from sklearn.pipeline import Pipeline
from sklearn.multioutput import MultiOutputRegressor
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor


def load_and_preprocess_data(filepath: str) -> tuple:
    """Load data and perform preprocessing."""
    df = pd.read_csv(filepath)
    
    target_features = ['item_count', 'order_count']
    useless_features = ['total_revenue', 'avg_order_value', 'avg_items_per_order']
    
    x, y = df.drop(target_features, axis=1), df[target_features]
    x = x.drop(useless_features, axis=1)
    x = x.drop('datetime', axis=1)
    
    # Drop columns with too many missing values
    x = x.drop(['longitude', 'latitude'], axis=1)
    
    # Fill missing values
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
    
    return x, y, target_features


def time_series_split(x, y, train_ratio=0.8):
    """Split data maintaining temporal order."""
    train_size = int(len(x) * train_ratio)
    x_train, x_test = x[:train_size], x[train_size:]
    y_train, y_test = y[:train_size], y[train_size:]
    return x_train, x_test, y_train, y_test


# =============================================================================
# 1. TARGET DISTRIBUTION ANALYSIS
# =============================================================================
def analyze_target_distribution(y, target_features):
    """Analyze target variable distributions."""
    print("\n" + "="*80)
    print("1. TARGET DISTRIBUTION ANALYSIS")
    print("="*80)
    
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    
    for i, target in enumerate(target_features):
        # Histogram
        axes[0, i].hist(y[target], bins=50, edgecolor='black', alpha=0.7)
        axes[0, i].set_title(f'{target} Distribution')
        axes[0, i].set_xlabel(target)
        
        # Q-Q plot
        stats.probplot(y[target], dist="norm", plot=axes[1, i])
        axes[1, i].set_title(f'{target} Q-Q Plot')
    
    # Statistics text
    axes[0, 2].axis('off')
    stats_text = "Target Statistics:\n\n"
    for target in target_features:
        skew = y[target].skew()
        kurt = y[target].kurtosis()
        stats_text += f"{target}:\n"
        stats_text += f"  Skewness: {skew:.3f}\n"
        stats_text += f"  Kurtosis: {kurt:.3f}\n"
        stats_text += f"  Min: {y[target].min():.1f}\n"
        stats_text += f"  Max: {y[target].max():.1f}\n"
        stats_text += f"  Mean: {y[target].mean():.1f}\n\n"
    axes[0, 2].text(0.1, 0.5, stats_text, fontsize=12, verticalalignment='center', family='monospace')
    axes[1, 2].axis('off')
    
    plt.tight_layout()
    plt.savefig('../data/models/target_distribution.png', dpi=150, bbox_inches='tight')
    plt.show()
    
    print("\nInterpretation:")
    print("- High skewness (>1) suggests log or sqrt transformation may help")
    print("- Heavy tails (high kurtosis) indicate outliers that may affect linear models")


# =============================================================================
# 2. TRANSFORMATION COMPARISON
# =============================================================================
def compare_transformations(y, target_features):
    """Compare different target transformations."""
    print("\n" + "="*80)
    print("2. TRANSFORMATION COMPARISON")
    print("="*80)
    
    fig, axes = plt.subplots(2, 4, figsize=(16, 8))
    
    results = {}
    
    for i, target in enumerate(target_features):
        original = y[target].values.reshape(-1, 1)
        
        # Transformations
        log_transformed = np.log1p(y[target])
        sqrt_transformed = np.sqrt(y[target])
        
        pt = PowerTransformer(method='yeo-johnson')
        yj_transformed = pt.fit_transform(original).flatten()
        
        results[target] = {
            'original_skew': y[target].skew(),
            'log_skew': log_transformed.skew(),
            'sqrt_skew': sqrt_transformed.skew(),
            'yj_skew': pd.Series(yj_transformed).skew()
        }
        
        # Plot
        axes[i, 0].hist(y[target], bins=50, alpha=0.7)
        axes[i, 0].set_title(f'{target} - Original (skew={y[target].skew():.2f})')
        
        axes[i, 1].hist(log_transformed, bins=50, alpha=0.7, color='green')
        axes[i, 1].set_title(f'{target} - Log1p (skew={log_transformed.skew():.2f})')
        
        axes[i, 2].hist(sqrt_transformed, bins=50, alpha=0.7, color='orange')
        axes[i, 2].set_title(f'{target} - Sqrt (skew={sqrt_transformed.skew():.2f})')
        
        axes[i, 3].hist(yj_transformed, bins=50, alpha=0.7, color='red')
        axes[i, 3].set_title(f'{target} - Yeo-Johnson (skew={pd.Series(yj_transformed).skew():.2f})')
    
    plt.tight_layout()
    plt.savefig('../data/models/transformation_comparison.png', dpi=150, bbox_inches='tight')
    plt.show()
    
    print("\nTransformation Results:")
    for target, skews in results.items():
        print(f"\n{target}:")
        best = min(skews.items(), key=lambda x: abs(x[1]))
        for name, skew in skews.items():
            marker = " <-- BEST" if name == best[0] else ""
            print(f"  {name}: {skew:.3f}{marker}")
    
    return results


# =============================================================================
# 3. FEATURE CORRELATION ANALYSIS
# =============================================================================
def analyze_feature_correlations(x_train):
    """Analyze feature correlations for multicollinearity."""
    print("\n" + "="*80)
    print("3. FEATURE CORRELATION ANALYSIS")
    print("="*80)
    
    correlation_matrix = x_train.corr()
    
    # Find highly correlated pairs
    high_corr_pairs = []
    for i in range(len(correlation_matrix.columns)):
        for j in range(i+1, len(correlation_matrix.columns)):
            if abs(correlation_matrix.iloc[i, j]) > 0.8:
                high_corr_pairs.append((
                    correlation_matrix.columns[i],
                    correlation_matrix.columns[j],
                    correlation_matrix.iloc[i, j]
                ))
    
    print("\nHighly Correlated Feature Pairs (|r| > 0.8):")
    print("=" * 70)
    for f1, f2, corr in sorted(high_corr_pairs, key=lambda x: abs(x[2]), reverse=True):
        print(f"{f1:30s} <-> {f2:30s}: {corr:.3f}")
    
    print(f"\nTotal: {len(high_corr_pairs)} highly correlated pairs")
    print("\nNote: High multicollinearity can make linear models unstable")
    print("but doesn't affect tree-based models.")
    
    return high_corr_pairs


# =============================================================================
# 4. MODEL FAMILY COMPARISON
# =============================================================================
def compare_model_families(x_train, x_test, y_train, y_test, target_features):
    """Compare different model families with log-transformed targets."""
    print("\n" + "="*80)
    print("4. MODEL FAMILY COMPARISON (with log-transformed targets)")
    print("="*80)
    
    # Transform targets using log1p (handles zeros better than YJ for count data)
    y_train_transformed = np.log1p(y_train)
    y_test_transformed = np.log1p(y_test)
    
    # Define features that need scaling
    from sklearn.compose import ColumnTransformer
    
    scale_features = [
        'waiting_time', 'rating', 'avg_discount',
        'prev_hour_items', 'prev_day_items', 'prev_week_items', 'prev_month_items',
        'rolling_7d_avg_items', 'temperature_2m', 'relative_humidity_2m',
        'precipitation', 'rain', 'snowfall', 'cloud_cover', 'wind_speed_10m',
        'weather_severity'
    ]
    
    # Filter to only include features that exist in the dataset
    scale_features = [f for f in scale_features if f in x_train.columns]
    
    preprocessor = ColumnTransformer(
        transformers=[('scaler', StandardScaler(), scale_features)],
        remainder='passthrough'
    )
    
    models = {
        'Linear Regression': MultiOutputRegressor(LinearRegression()),
        'Ridge (α=1)': MultiOutputRegressor(Ridge(alpha=1.0)),
        'Ridge (α=10)': MultiOutputRegressor(Ridge(alpha=10.0)),
        'Lasso (α=0.1)': MultiOutputRegressor(Lasso(alpha=0.1, max_iter=5000)),
        'ElasticNet': MultiOutputRegressor(ElasticNet(alpha=0.1, l1_ratio=0.5, max_iter=5000)),
        'Random Forest': MultiOutputRegressor(RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1)),
        'Gradient Boosting': MultiOutputRegressor(GradientBoostingRegressor(n_estimators=100, max_depth=5, random_state=42)),
        'KNN (k=10)': MultiOutputRegressor(KNeighborsRegressor(n_neighbors=10)),
        'XGBoost': MultiOutputRegressor(XGBRegressor(n_estimators=100, max_depth=5, random_state=42)),
        'LightGBM': MultiOutputRegressor(LGBMRegressor(n_estimators=100, max_depth=5, random_state=42, verbose=-1, force_col_wise=True)),
    }
    
    results = []
    
    for name, model in models.items():
        print(f"Training {name}...")
        
        pipeline = Pipeline([
            ('preprocessor', preprocessor),
            ('model', model)
        ])
        
        pipeline.fit(x_train, y_train_transformed)
        
        # Predict and inverse transform
        y_pred_transformed = pipeline.predict(x_test)
        y_pred = np.expm1(y_pred_transformed)
        y_pred = np.maximum(y_pred, 0)
        
        for i, target in enumerate(target_features):
            rmse = np.sqrt(mean_squared_error(y_test.iloc[:, i], y_pred[:, i]))
            mae = mean_absolute_error(y_test.iloc[:, i], y_pred[:, i])
            r2 = r2_score(y_test.iloc[:, i], y_pred[:, i])
            
            results.append({
                'Model': name,
                'Target': target,
                'RMSE': rmse,
                'MAE': mae,
                'R2': r2
            })
    
    results_df = pd.DataFrame(results)
    
    # Visualize
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    
    for i, metric in enumerate(['RMSE', 'MAE', 'R2']):
        pivot_df = results_df.pivot(index='Model', columns='Target', values=metric)
        pivot_df.plot(kind='barh', ax=axes[i], width=0.8)
        title = f'{metric} by Model ({"higher" if metric == "R2" else "lower"} is better)'
        axes[i].set_title(title)
        axes[i].set_xlabel(metric)
        axes[i].legend(title='Target')
        axes[i].grid(axis='x', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('../data/models/model_comparison.png', dpi=150, bbox_inches='tight')
    plt.show()
    
    # Summary
    print("\nSummary - Average metrics across both targets:")
    summary = results_df.groupby('Model')[['RMSE', 'MAE', 'R2']].mean().round(4)
    summary = summary.sort_values('MAE')
    print(summary.to_string())
    
    return results_df


# =============================================================================
# 5. RESIDUAL ANALYSIS
# =============================================================================
def analyze_residuals(x_train, x_test, y_train, y_test, target_features):
    """Analyze residuals to understand model failures."""
    print("\n" + "="*80)
    print("5. RESIDUAL ANALYSIS")
    print("="*80)
    
    # Transform targets using log1p
    y_train_transformed = np.log1p(y_train)
    
    # Define selective scaling
    from sklearn.compose import ColumnTransformer
    scale_features = [
        'waiting_time', 'rating', 'avg_discount',
        'prev_hour_items', 'prev_day_items', 'prev_week_items', 'prev_month_items',
        'rolling_7d_avg_items', 'temperature_2m', 'relative_humidity_2m',
        'precipitation', 'rain', 'snowfall', 'cloud_cover', 'wind_speed_10m',
        'weather_severity'
    ]
    scale_features = [f for f in scale_features if f in x_train.columns]
    
    preprocessor = ColumnTransformer(
        transformers=[('scaler', StandardScaler(), scale_features)],
        remainder='passthrough'
    )
    
    # Train models
    lr_pipeline = Pipeline([
        ('preprocessor', preprocessor),
        ('model', MultiOutputRegressor(LinearRegression()))
    ])
    xgb_pipeline = Pipeline([
        ('preprocessor', preprocessor),
        ('model', MultiOutputRegressor(XGBRegressor(n_estimators=100, max_depth=5, random_state=42)))
    ])
    
    lr_pipeline.fit(x_train, y_train_transformed)
    xgb_pipeline.fit(x_train, y_train_transformed)
    
    lr_pred = np.expm1(lr_pipeline.predict(x_test))
    xgb_pred = np.expm1(xgb_pipeline.predict(x_test))
    lr_pred = np.maximum(lr_pred, 0)
    xgb_pred = np.maximum(xgb_pred, 0)
    
    fig, axes = plt.subplots(2, 4, figsize=(18, 10))
    
    for i, target in enumerate(target_features):
        y_true = y_test.iloc[:, i].values
        lr_resid = y_true - lr_pred[:, i]
        xgb_resid = y_true - xgb_pred[:, i]
        
        # LR Residuals vs Predicted
        axes[i, 0].scatter(lr_pred[:, i], lr_resid, alpha=0.3, s=10)
        axes[i, 0].axhline(y=0, color='r', linestyle='--')
        axes[i, 0].set_xlabel('Predicted')
        axes[i, 0].set_ylabel('Residual')
        axes[i, 0].set_title(f'LR Residuals - {target}')
        
        # XGB Residuals vs Predicted
        axes[i, 1].scatter(xgb_pred[:, i], xgb_resid, alpha=0.3, s=10)
        axes[i, 1].axhline(y=0, color='r', linestyle='--')
        axes[i, 1].set_xlabel('Predicted')
        axes[i, 1].set_ylabel('Residual')
        axes[i, 1].set_title(f'XGB Residuals - {target}')
        
        # Actual vs Predicted
        axes[i, 2].scatter(y_true, lr_pred[:, i], alpha=0.3, s=10, label='Linear Reg')
        axes[i, 2].scatter(y_true, xgb_pred[:, i], alpha=0.3, s=10, label='XGBoost')
        axes[i, 2].plot([y_true.min(), y_true.max()], [y_true.min(), y_true.max()], 'r--', label='Perfect')
        axes[i, 2].set_xlabel('Actual')
        axes[i, 2].set_ylabel('Predicted')
        axes[i, 2].set_title(f'Actual vs Predicted - {target}')
        axes[i, 2].legend()
        
        # Residual distribution
        axes[i, 3].hist(lr_resid, bins=50, alpha=0.5, label='LR')
        axes[i, 3].hist(xgb_resid, bins=50, alpha=0.5, label='XGB')
        axes[i, 3].set_xlabel('Residual')
        axes[i, 3].set_title(f'Residual Distribution - {target}')
        axes[i, 3].legend()
    
    plt.tight_layout()
    plt.savefig('../data/models/residual_analysis.png', dpi=150, bbox_inches='tight')
    plt.show()
    
    print("\nInterpretation:")
    print("- Patterns in residuals (curves, heteroscedasticity) suggest non-linear relationships")
    print("- Similar residual distributions indicate models capture similar patterns")


# =============================================================================
# 6. FEATURE IMPORTANCE ANALYSIS
# =============================================================================
def analyze_feature_importance(x_train, y_train, target_features):
    """Analyze feature importance from tree-based models."""
    print("\n" + "="*80)
    print("6. FEATURE IMPORTANCE ANALYSIS")
    print("="*80)
    
    scaler = StandardScaler()
    x_train_scaled = scaler.fit_transform(x_train)
    
    rf_model = MultiOutputRegressor(RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1))
    xgb_model = MultiOutputRegressor(XGBRegressor(n_estimators=100, max_depth=5, random_state=42))
    
    rf_model.fit(x_train_scaled, y_train)
    xgb_model.fit(x_train_scaled, y_train)
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    importance_results = {}
    
    for i, target in enumerate(target_features):
        # Random Forest
        rf_importance = rf_model.estimators_[i].feature_importances_
        rf_imp_df = pd.DataFrame({'feature': x_train.columns, 'importance': rf_importance})
        rf_imp_df = rf_imp_df.sort_values('importance', ascending=True).tail(15)
        
        axes[i, 0].barh(rf_imp_df['feature'], rf_imp_df['importance'])
        axes[i, 0].set_title(f'Random Forest - {target}')
        axes[i, 0].set_xlabel('Importance')
        
        # XGBoost
        xgb_importance = xgb_model.estimators_[i].feature_importances_
        xgb_imp_df = pd.DataFrame({'feature': x_train.columns, 'importance': xgb_importance})
        xgb_imp_df = xgb_imp_df.sort_values('importance', ascending=True).tail(15)
        
        axes[i, 1].barh(xgb_imp_df['feature'], xgb_imp_df['importance'])
        axes[i, 1].set_title(f'XGBoost - {target}')
        axes[i, 1].set_xlabel('Importance')
        
        importance_results[target] = {
            'rf_top5': rf_imp_df.tail(5)['feature'].tolist(),
            'xgb_top5': xgb_imp_df.tail(5)['feature'].tolist()
        }
    
    plt.tight_layout()
    plt.savefig('../data/models/feature_importance.png', dpi=150, bbox_inches='tight')
    plt.show()
    
    print("\nTop 5 Features by Model:")
    for target, features in importance_results.items():
        print(f"\n{target}:")
        print(f"  Random Forest: {features['rf_top5']}")
        print(f"  XGBoost: {features['xgb_top5']}")
    
    print("\nKey Insight: If lag features dominate, the relationship is autoregressive (linear in nature).")
    
    return importance_results


# =============================================================================
# 7. POLYNOMIAL FEATURES TEST
# =============================================================================
def test_polynomial_features(x_train, x_test, y_train, y_test, target_features):
    """Test if polynomial features help linear models."""
    print("\n" + "="*80)
    print("7. POLYNOMIAL FEATURES TEST")
    print("="*80)
    
    # Transform targets using log1p
    y_train_transformed = np.log1p(y_train)
    
    # Select top features for polynomial expansion
    top_features = ['prev_hour_items', 'prev_day_items', 'rolling_7d_avg_items',
                    'hour', 'day_of_week', 'temperature_2m']
    
    available_features = [f for f in top_features if f in x_train.columns]
    print(f"Using features for polynomial expansion: {available_features}")
    
    x_train_subset = x_train[available_features]
    x_test_subset = x_test[available_features]
    
    poly_results = []
    
    for degree in [1, 2, 3]:
        poly = PolynomialFeatures(degree=degree, include_bias=False, interaction_only=(degree > 1))
        
        x_train_poly = poly.fit_transform(x_train_subset)
        x_test_poly = poly.transform(x_test_subset)
        
        print(f"\nDegree {degree}: {x_train_poly.shape[1]} features")
        
        model = MultiOutputRegressor(Ridge(alpha=1.0))
        
        scaler = StandardScaler()
        x_train_poly_scaled = scaler.fit_transform(x_train_poly)
        x_test_poly_scaled = scaler.transform(x_test_poly)
        
        model.fit(x_train_poly_scaled, y_train_transformed)
        y_pred = np.expm1(model.predict(x_test_poly_scaled))
        y_pred = np.maximum(y_pred, 0)
        
        for i, target in enumerate(target_features):
            mae = mean_absolute_error(y_test.iloc[:, i], y_pred[:, i])
            r2 = r2_score(y_test.iloc[:, i], y_pred[:, i])
            poly_results.append({'Degree': degree, 'Target': target, 'MAE': mae, 'R2': r2})
            print(f"  {target}: MAE={mae:.4f}, R2={r2:.4f}")
    
    print("\nIf polynomial features significantly improve R2, there are non-linear relationships")
    print("that tree-based models should capture (check if they need more depth/estimators).")
    
    return pd.DataFrame(poly_results)


# =============================================================================
# 8. LEARNING CURVE ANALYSIS
# =============================================================================
def analyze_learning_curves(x_train, y_train):
    """Analyze learning curves to detect overfitting/underfitting."""
    print("\n" + "="*80)
    print("8. LEARNING CURVE ANALYSIS")
    print("="*80)
    
    # Transform targets using log1p
    y_train_transformed = np.log1p(y_train)
    
    # Define selective scaling
    from sklearn.compose import ColumnTransformer
    scale_features = [
        'waiting_time', 'rating', 'avg_discount',
        'prev_hour_items', 'prev_day_items', 'prev_week_items', 'prev_month_items',
        'rolling_7d_avg_items', 'temperature_2m', 'relative_humidity_2m',
        'precipitation', 'rain', 'snowfall', 'cloud_cover', 'wind_speed_10m',
        'weather_severity'
    ]
    scale_features = [f for f in scale_features if f in x_train.columns]
    
    preprocessor = ColumnTransformer(
        transformers=[('scaler', StandardScaler(), scale_features)],
        remainder='passthrough'
    )
    
    models_for_lc = {
        'Linear Regression': Pipeline([
            ('preprocessor', preprocessor),
            ('model', MultiOutputRegressor(LinearRegression()))
        ]),
        'XGBoost': Pipeline([
            ('preprocessor', preprocessor),
            ('model', MultiOutputRegressor(XGBRegressor(n_estimators=100, max_depth=5, random_state=42)))
        ]),
        'Random Forest': Pipeline([
            ('preprocessor', preprocessor),
            ('model', MultiOutputRegressor(RandomForestRegressor(n_estimators=50, max_depth=10, random_state=42, n_jobs=-1)))
        ]),
        'LightGBM': Pipeline([
            ('preprocessor', preprocessor),
            ('model', MultiOutputRegressor(LGBMRegressor(n_estimators=100, max_depth=5, random_state=42, verbose=-1, force_col_wise=True)))
        ])
    }
    
    fig, axes = plt.subplots(1, 4, figsize=(20, 5))
    train_sizes = np.linspace(0.1, 1.0, 8)
    
    for idx, (name, model) in enumerate(models_for_lc.items()):
        print(f"Computing learning curve for {name}...")
        
        train_sizes_abs, train_scores, val_scores = learning_curve(
            model, x_train, y_train_transformed,
            train_sizes=train_sizes,
            cv=TimeSeriesSplit(n_splits=3),
            scoring='neg_mean_absolute_error',
            n_jobs=-1
        )
        
        train_mean = -train_scores.mean(axis=1)
        train_std = train_scores.std(axis=1)
        val_mean = -val_scores.mean(axis=1)
        val_std = val_scores.std(axis=1)
        
        axes[idx].plot(train_sizes_abs, train_mean, 'o-', label='Training')
        axes[idx].fill_between(train_sizes_abs, train_mean - train_std, train_mean + train_std, alpha=0.1)
        axes[idx].plot(train_sizes_abs, val_mean, 'o-', label='Validation')
        axes[idx].fill_between(train_sizes_abs, val_mean - val_std, val_mean + val_std, alpha=0.1)
        
        axes[idx].set_xlabel('Training Examples')
        axes[idx].set_ylabel('MAE')
        axes[idx].set_title(f'{name} Learning Curve')
        axes[idx].legend()
        axes[idx].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('../data/models/learning_curves.png', dpi=150, bbox_inches='tight')
    plt.show()
    
    print("\nInterpretation:")
    print("- Gap between train/val: High gap = overfitting, need more data or regularization")
    print("- Converging curves: Model has learned what it can from the data")
    print("- High error on both: Underfitting, need more features or model complexity")


# =============================================================================
# 9. SUMMARY
# =============================================================================
def print_summary(results_df):
    """Print final summary and recommendations."""
    print("\n" + "="*80)
    print("EXPERIMENTATION SUMMARY")
    print("="*80)
    
    print("""
KEY FINDINGS TO CHECK:

1. TARGET DISTRIBUTION:
   - If targets are highly skewed → Use log/sqrt transformation
   - If targets have many zeros → Consider zero-inflated models or Tweedie regression

2. FEATURE RELATIONSHIPS:
   - If lag features dominate importance → Data is autoregressive (linear models work well)
   - If many features have similar importance → Complex interactions exist (tree models better)

3. MODEL COMPARISON:
   - If Linear ≈ XGBoost → Relationship is mostly linear, simpler model is better
   - If regularized linear (Ridge/Lasso) beats plain Linear → Multicollinearity issue
   - If polynomial features help significantly → Non-linear relationships exist

4. LEARNING CURVES:
   - High gap (train << val error) → Overfitting, need regularization
   - Both errors high → Underfitting, need more features/complexity
   - Converging → Model capacity is appropriate

RECOMMENDED NEXT STEPS:
- If linear relationship dominates: Use Ridge/Lasso with feature selection
- If non-linear but tree models not helping: Try neural networks or feature engineering
- If autoregressive: Consider dedicated time series models (ARIMA, Prophet, LSTM)
""")
    
    print("\nBest performing models from comparison:")
    print(results_df.groupby('Model')['MAE'].mean().sort_values().head(5).to_string())


# =============================================================================
# MAIN
# =============================================================================
def run_all_experiments(data_path: str = 'data/processed/combined_features.csv'):
    """Run all experiments."""
    import os
    os.makedirs('data/models', exist_ok=True)
    
    print("Loading and preprocessing data...")
    x, y, target_features = load_and_preprocess_data(data_path)
    x_train, x_test, y_train, y_test = time_series_split(x, y)
    
    print(f"Training set: {len(x_train)} samples")
    print(f"Test set: {len(x_test)} samples")
    print(f"Features: {len(x_train.columns)}")
    
    # Run all analyses
    analyze_target_distribution(y, target_features)
    compare_transformations(y, target_features)
    analyze_feature_correlations(x_train)
    results_df = compare_model_families(x_train, x_test, y_train, y_test, target_features)
    analyze_residuals(x_train, x_test, y_train, y_test, target_features)
    analyze_feature_importance(x_train, y_train, target_features)
    test_polynomial_features(x_train, x_test, y_train, y_test, target_features)
    analyze_learning_curves(x_train, y_train)
    print_summary(results_df)
    
    return results_df


if __name__ == '__main__':
    results = run_all_experiments()
