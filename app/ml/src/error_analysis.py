"""
Deep Error Analysis for Demand Prediction Model
Provides comprehensive insights on model weaknesses and improvement opportunities
"""
import numpy as np
import pandas as pd
import joblib
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# Set visualization style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (14, 8)

print("="*80)
print("DEEP ERROR ANALYSIS - DEMAND PREDICTION MODEL")
print("="*80)

# ============================================================================
# 1. LOAD MODEL AND DATA
# ============================================================================
print("\n📊 Loading model and data...")

try:
    model = joblib.load('data/models/rf_model.joblib')
    metadata = joblib.load('data/models/rf_model_metadata.json')
    print(f"   ✓ Model loaded: {metadata.get('model_algorithm', 'Unknown')}")
except Exception as e:
    print(f"   ⚠ Could not load metadata: {e}")
    metadata = {}

df = pd.read_csv('data/processed/combined_features.csv')
print(f"   ✓ Dataset loaded: {df.shape[0]:,} rows × {df.shape[1]} columns")

# ============================================================================
# 2. PREPARE DATA
# ============================================================================
print("\n📋 Preparing data...")

target_features = ['item_count', 'order_count']
useless_features = ['total_revenue', 'avg_order_value', 'avg_items_per_order']

X = df.drop(target_features + useless_features + ['datetime'], axis=1)
y = df[target_features]

# Handle missing values
X = X.drop(['longitude', 'latitude'], axis=1, errors='ignore')
X['type_id'] = X['type_id'].fillna(-1)
X['waiting_time'] = X['waiting_time'].fillna(X['waiting_time'].median())
X['rating'] = X['rating'].fillna(X['rating'].median())
X['delivery'] = X['delivery'].fillna(0)
X['accepting_orders'] = X['accepting_orders'].fillna(0)

# Convert dtypes
X['place_id'] = X['place_id'].astype('float64')
X['type_id'] = X['type_id'].astype('float64')
X.columns = X.columns.astype(str)
y.columns = y.columns.astype(str)

# Time series split
train_size = int(len(X) * 0.8)
X_train, X_test = X[:train_size], X[train_size:]
y_train, y_test = y[:train_size], y[train_size:]

print(f"   ✓ Train: {len(X_train):,} | Test: {len(X_test):,}")

# ============================================================================
# 3. GENERATE PREDICTIONS
# ============================================================================
print("\n🔮 Generating predictions...")

# Handle both single model and list of models
if isinstance(model, list):
    print(f"   Model is a list of {len(model)} estimators (multi-output)")
    y_pred_train = np.column_stack([m.predict(X_train) for m in model])
    y_pred_test = np.column_stack([m.predict(X_test) for m in model])
else:
    y_pred_train = model.predict(X_train)
    y_pred_test = model.predict(X_test)

print("   ✓ Predictions complete")

# ============================================================================
# 4. RESIDUAL ANALYSIS
# ============================================================================
print("\n" + "="*80)
print("📈 RESIDUAL ANALYSIS")
print("="*80)

# Focus on item_count as primary target
y_true = y_test['item_count'].values
y_pred = y_pred_test[:, 0]
errors = y_pred - y_true
abs_errors = np.abs(errors)
pct_errors = 100 * errors / (y_true + 1)  # +1 to avoid division by zero

print("\n1️⃣ Error Distribution:")
print(f"   Mean Error (bias):          {errors.mean():>8.3f}")
print(f"   Median Error:               {np.median(errors):>8.3f}")
print(f"   Std Dev of Errors:          {errors.std():>8.3f}")
print(f"   Mean Absolute Error (MAE):  {abs_errors.mean():>8.3f}")
print(f"   Median Absolute Error:      {np.median(abs_errors):>8.3f}")
print(f"   95th Percentile Error:      {np.percentile(abs_errors, 95):>8.3f}")
print(f"   Max Absolute Error:         {abs_errors.max():>8.3f}")

# Check for normality of residuals
_, norm_p_value = stats.normaltest(errors)
print(f"\n   Normality test p-value:     {norm_p_value:.4f}")
if norm_p_value < 0.05:
    print("   ⚠ Residuals are NOT normally distributed (indicates model issues)")
else:
    print("   ✓ Residuals are approximately normal")

# ============================================================================
# 5. PREDICTION QUALITY SEGMENTS
# ============================================================================
print("\n2️⃣ Prediction Quality Segments:")

# Define quality levels based on absolute error
excellent = abs_errors <= 2
good = (abs_errors > 2) & (abs_errors <= 5)
fair = (abs_errors > 5) & (abs_errors <= 10)
poor = abs_errors > 10

print(f"\n   Excellent (error ≤ 2):      {excellent.sum():>6,} ({100*excellent.mean():>5.1f}%)")
print(f"   Good (2 < error ≤ 5):       {good.sum():>6,} ({100*good.mean():>5.1f}%)")
print(f"   Fair (5 < error ≤ 10):      {fair.sum():>6,} ({100*fair.mean():>5.1f}%)")
print(f"   Poor (error > 10):          {poor.sum():>6,} ({100*poor.mean():>5.1f}%)")

# ============================================================================
# 6. ERROR BY DEMAND LEVEL
# ============================================================================
print("\n" + "="*80)
print("📊 ERROR ANALYSIS BY DEMAND LEVEL")
print("="*80)

# Define demand buckets
demand_levels = [
    ("Very Low (0-3)", (y_true >= 0) & (y_true < 3)),
    ("Low (3-7)", (y_true >= 3) & (y_true < 7)),
    ("Medium (7-15)", (y_true >= 7) & (y_true < 15)),
    ("High (15-25)", (y_true >= 15) & (y_true < 25)),
    ("Very High (25+)", y_true >= 25)
]

demand_analysis = []
for level_name, mask in demand_levels:
    if mask.sum() > 0:
        level_mae = abs_errors[mask].mean()
        level_bias = errors[mask].mean()
        level_r2 = r2_score(y_true[mask], y_pred[mask])
        level_mape = np.mean(np.abs(pct_errors[mask]))
        
        print(f"\n{level_name}:")
        print(f"   Samples:        {mask.sum():>7,} ({100*mask.mean():>5.1f}%)")
        print(f"   MAE:            {level_mae:>7.3f}")
        print(f"   Bias:           {level_bias:>7.3f} {'(over-predict)' if level_bias > 0 else '(under-predict)'}")
        print(f"   R²:             {level_r2:>7.3f}")
        print(f"   MAPE:           {level_mape:>7.1f}%")
        
        demand_analysis.append({
            'Level': level_name,
            'Samples': mask.sum(),
            'MAE': level_mae,
            'Bias': level_bias,
            'R2': level_r2,
            'MAPE': level_mape
        })

# ============================================================================
# 7. TEMPORAL ERROR PATTERNS
# ============================================================================
print("\n" + "="*80)
print("⏰ TEMPORAL ERROR PATTERNS")
print("="*80)

X_test_copy = X_test.copy()
X_test_copy['y_true'] = y_true
X_test_copy['y_pred'] = y_pred
X_test_copy['error'] = errors
X_test_copy['abs_error'] = abs_errors

# By hour
print("\n1️⃣ Performance by Hour of Day:")
hour_analysis = X_test_copy.groupby('hour').agg({
    'abs_error': ['mean', 'count'],
    'error': 'mean'
}).round(3)
hour_analysis.columns = ['MAE', 'Count', 'Bias']
hour_analysis = hour_analysis.sort_values('MAE', ascending=False)

print("\n   Worst performing hours (highest MAE):")
for idx, row in hour_analysis.head(5).iterrows():
    print(f"   Hour {int(idx):2d}: MAE={row['MAE']:.3f}, Bias={row['Bias']:+.3f}, n={int(row['Count']):,}")

print("\n   Best performing hours (lowest MAE):")
for idx, row in hour_analysis.tail(5).iterrows():
    print(f"   Hour {int(idx):2d}: MAE={row['MAE']:.3f}, Bias={row['Bias']:+.3f}, n={int(row['Count']):,}")

# By day of week
print("\n2️⃣ Performance by Day of Week:")
dow_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
dow_analysis = X_test_copy.groupby('day_of_week').agg({
    'abs_error': ['mean', 'count'],
    'error': 'mean'
}).round(3)
dow_analysis.columns = ['MAE', 'Count', 'Bias']

for idx, row in dow_analysis.iterrows():
    day_name = dow_names[int(idx)]
    print(f"   {day_name:9s}: MAE={row['MAE']:.3f}, Bias={row['Bias']:+.3f}, n={int(row['Count']):,}")

# Weekend vs weekday
if 'is_weekend' in X_test_copy.columns:
    print("\n3️⃣ Weekend vs Weekday:")
    for is_wknd in [0, 1]:
        mask = X_test_copy['is_weekend'] == is_wknd
        label = "Weekend  " if is_wknd else "Weekday  "
        mae = X_test_copy.loc[mask, 'abs_error'].mean()
        bias = X_test_copy.loc[mask, 'error'].mean()
        count = mask.sum()
        print(f"   {label}: MAE={mae:.3f}, Bias={bias:+.3f}, n={count:,}")

# ============================================================================
# 8. ERROR BY RESTAURANT CHARACTERISTICS
# ============================================================================
print("\n" + "="*80)
print("🏪 ERROR BY RESTAURANT CHARACTERISTICS")
print("="*80)

# By place_id (top worst and best restaurants)
place_analysis = X_test_copy.groupby('place_id').agg({
    'abs_error': ['mean', 'count'],
    'error': 'mean',
    'y_true': 'mean'
}).round(3)
place_analysis.columns = ['MAE', 'Count', 'Bias', 'Avg_Demand']
place_analysis = place_analysis[place_analysis['Count'] >= 10]  # Filter for statistical significance

print("\n1️⃣ Worst Predicted Restaurants (MAE, min 10 samples):")
for idx, row in place_analysis.nlargest(5, 'MAE').iterrows():
    print(f"   Place {int(idx):3d}: MAE={row['MAE']:.3f}, Bias={row['Bias']:+.3f}, Avg_Demand={row['Avg_Demand']:.1f}, n={int(row['Count']):,}")

print("\n2️⃣ Best Predicted Restaurants (MAE, min 10 samples):")
for idx, row in place_analysis.nsmallest(5, 'MAE').iterrows():
    print(f"   Place {int(idx):3d}: MAE={row['MAE']:.3f}, Bias={row['Bias']:+.3f}, Avg_Demand={row['Avg_Demand']:.1f}, n={int(row['Count']):,}")

# By type_id
if 'type_id' in X_test_copy.columns:
    print("\n3️⃣ Performance by Restaurant Type:")
    type_analysis = X_test_copy.groupby('type_id').agg({
        'abs_error': ['mean', 'count'],
        'error': 'mean'
    }).round(3)
    type_analysis.columns = ['MAE', 'Count', 'Bias']
    type_analysis = type_analysis[type_analysis['Count'] >= 20]
    
    if len(type_analysis) > 0:
        for idx, row in type_analysis.sort_values('MAE', ascending=False).head(5).iterrows():
            type_id = int(idx) if idx >= 0 else 'Unknown'
            print(f"   Type {type_id}: MAE={row['MAE']:.3f}, Bias={row['Bias']:+.3f}, n={int(row['Count']):,}")

# ============================================================================
# 9. WORST PREDICTIONS ANALYSIS
# ============================================================================
print("\n" + "="*80)
print("🔍 WORST PREDICTIONS DEEP DIVE")
print("="*80)

# Get worst predictions
worst_predictions = X_test_copy.nlargest(20, 'abs_error')[
    ['hour', 'day_of_week', 'place_id', 'y_true', 'y_pred', 'abs_error']
].copy()
worst_predictions['y_true'] = worst_predictions['y_true'].astype(int)
worst_predictions['y_pred'] = worst_predictions['y_pred'].round(1)

print("\nTop 10 Worst Predictions:")
print(worst_predictions.head(10).to_string(index=False))

print("\n⚠️  Common patterns in worst predictions:")
# Analyze common characteristics
hour_dist = worst_predictions['hour'].value_counts().head(3)
print(f"   Most common hours: {dict(hour_dist)}")
dow_dist = worst_predictions['day_of_week'].value_counts().head(2)
print(f"   Most common days: {dict(dow_dist)}")

# ============================================================================
# 10. FEATURE CORRELATION WITH ERRORS
# ============================================================================
print("\n" + "="*80)
print("🔗 FEATURE CORRELATION WITH ERRORS")
print("="*80)

# Calculate correlation between features and absolute errors
correlations = []
for col in X_test.select_dtypes(include=[np.number]).columns:
    if col in X_test_copy.columns:
        corr = X_test_copy[col].corr(X_test_copy['abs_error'])
        correlations.append({'Feature': col, 'Correlation': corr})

corr_df = pd.DataFrame(correlations).sort_values('Correlation', key=abs, ascending=False)

print("\nTop features correlated with high errors:")
print(corr_df.head(10).to_string(index=False))

# ============================================================================
# 11. OVERFITTING ANALYSIS
# ============================================================================
print("\n" + "="*80)
print("📉 OVERFITTING ANALYSIS")
print("="*80)

y_true_train = y_train['item_count'].values
y_pred_train_items = y_pred_train[:, 0]

mae_train = mean_absolute_error(y_true_train, y_pred_train_items)
mae_test = mean_absolute_error(y_true, y_pred)
r2_train = r2_score(y_true_train, y_pred_train_items)
r2_test = r2_score(y_true, y_pred)

print(f"\nTraining Performance:")
print(f"   MAE:  {mae_train:.4f}")
print(f"   R²:   {r2_train:.4f}")

print(f"\nTest Performance:")
print(f"   MAE:  {mae_test:.4f}")
print(f"   R²:   {r2_test:.4f}")

print(f"\nOverfitting Indicators:")
print(f"   MAE difference:  {mae_test - mae_train:+.4f} ({'higher on test' if mae_test > mae_train else 'higher on train'})")
print(f"   R² difference:   {r2_test - r2_train:+.4f} ({'worse on test' if r2_test < r2_train else 'worse on train'})")

if (mae_test - mae_train) > 1.0 or (r2_train - r2_test) > 0.1:
    print("   ⚠ Significant overfitting detected!")
elif (mae_test - mae_train) > 0.5 or (r2_train - r2_test) > 0.05:
    print("   ⚠ Mild overfitting detected")
else:
    print("   ✓ Model generalizes well")

# ============================================================================
# 12. FEATURE IMPORTANCE ANALYSIS
# ============================================================================
print("\n" + "="*80)
print("🎯 FEATURE IMPORTANCE")
print("="*80)

try:
    # Try to get feature importance from model
    if isinstance(model, list):
        # For list of models, use the first model (item_count predictor)
        if hasattr(model[0], 'feature_importances_'):
            importances = model[0].feature_importances_
        elif hasattr(model[0], 'get_feature_importance'):
            importances = model[0].get_feature_importance()
        else:
            importances = None
    elif hasattr(model, 'feature_importances_'):
        importances = model.feature_importances_
    elif hasattr(model, 'estimators_'):
        # For MultiOutputRegressor, get importance from first estimator
        importances = model.estimators_[0].feature_importances_
    elif hasattr(model, 'get_feature_importance'):
        importances = model.get_feature_importance()
    else:
        importances = None
    
    if importances is not None:
        feature_importance = pd.DataFrame({
            'Feature': X_train.columns,
            'Importance': importances
        }).sort_values('Importance', ascending=False)
        
        print("\nTop 15 Most Important Features:")
        for idx, row in feature_importance.head(15).iterrows():
            print(f"   {row['Feature']:30s}: {row['Importance']:.4f}")
        
        # Check if important features are being underutilized
        low_importance = feature_importance[feature_importance['Importance'] < 0.001]
        print(f"\n   Features with very low importance (< 0.001): {len(low_importance)}")
        if len(low_importance) > 0:
            print("   Consider removing these features to reduce model complexity")
except Exception as e:
    print(f"   Could not extract feature importances: {e}")

# ============================================================================
# 13. ACTIONABLE RECOMMENDATIONS
# ============================================================================
print("\n" + "="*80)
print("💡 ACTIONABLE RECOMMENDATIONS")
print("="*80)

recommendations = []

# Based on demand level analysis
high_mae_levels = [item for item in demand_analysis if item['MAE'] > 5]
if high_mae_levels:
    recommendations.append({
        'Priority': 'HIGH',
        'Area': 'Demand Segmentation',
        'Issue': f"Poor performance on {len(high_mae_levels)} demand segments",
        'Action': 'Consider separate models for different demand ranges or use stratified sampling'
    })

# Based on temporal patterns
hour_std = hour_analysis['MAE'].std()
if hour_std > 1.5:
    recommendations.append({
        'Priority': 'HIGH',
        'Area': 'Temporal Features',
        'Issue': f"High variance in performance across hours (std={hour_std:.2f})",
        'Action': 'Add more time-based features (peak hours, meal periods, time since last order)'
    })

# Based on restaurant characteristics
if len(place_analysis) > 0:
    high_error_places = (place_analysis['MAE'] > 7).sum()
    pct_high_error = 100 * high_error_places / len(place_analysis)
    if pct_high_error > 20:
        recommendations.append({
            'Priority': 'MEDIUM',
            'Area': 'Restaurant Features',
            'Issue': f"{pct_high_error:.1f}% of restaurants have MAE > 7",
            'Action': 'Add restaurant-specific features (cuisine type, price range, historical volatility)'
        })

# Based on overfitting
if (mae_test - mae_train) > 1.0:
    recommendations.append({
        'Priority': 'HIGH',
        'Area': 'Model Complexity',
        'Issue': 'Significant overfitting detected',
        'Action': 'Increase regularization, reduce model complexity, or add more training data'
    })

# Based on residual distribution
if norm_p_value < 0.05:
    recommendations.append({
        'Priority': 'MEDIUM',
        'Area': 'Model Architecture',
        'Issue': 'Non-normal residuals suggest model assumptions violated',
        'Action': 'Try different models (e.g., quantile regression, LGBM) or transform target variable'
    })

# Based on bias
if abs(errors.mean()) > 0.5:
    direction = "over-predicting" if errors.mean() > 0 else "under-predicting"
    recommendations.append({
        'Priority': 'MEDIUM',
        'Area': 'Model Calibration',
        'Issue': f"Systematic bias detected (model is {direction})",
        'Action': 'Recalibrate model predictions or adjust sample weights during training'
    })

# Print recommendations
for i, rec in enumerate(recommendations, 1):
    print(f"\n{i}. [{rec['Priority']}] {rec['Area']}")
    print(f"   Issue:  {rec['Issue']}")
    print(f"   Action: {rec['Action']}")

if not recommendations:
    print("\n✓ Model performance is generally good. Focus on incremental improvements.")

# ============================================================================
# 14. SAVE ERROR ANALYSIS RESULTS
# ============================================================================
print("\n" + "="*80)
print("💾 SAVING RESULTS")
print("="*80)

# Save detailed error analysis
error_details = pd.DataFrame({
    'y_true': y_true,
    'y_pred': y_pred,
    'error': errors,
    'abs_error': abs_errors,
    'pct_error': pct_errors
})

# Add features for context
for col in ['hour', 'day_of_week', 'place_id', 'is_weekend']:
    if col in X_test.columns:
        error_details[col] = X_test[col].values

error_details.to_csv('data/models/error_analysis_details.csv', index=False)
print("   ✓ Saved detailed errors to data/models/error_analysis_details.csv")

# Save summary statistics
summary = {
    'Overall Metrics': {
        'MAE': float(mae_test),
        'RMSE': float(np.sqrt(mean_squared_error(y_true, y_pred))),
        'R2': float(r2_test),
        'Bias': float(errors.mean())
    },
    'Demand Level Analysis': [{k: float(v) if isinstance(v, (np.integer, np.floating)) else v 
                              for k, v in item.items()} for item in demand_analysis],
    'Recommendations': recommendations
}

import json
with open('data/models/error_analysis_summary.json', 'w') as f:
    json.dump(summary, f, indent=2, default=str)
print("   ✓ Saved summary to data/models/error_analysis_summary.json")

print("\n" + "="*80)
print("✅ ERROR ANALYSIS COMPLETE")
print("="*80)
print("\nNext steps:")
print("1. Review recommendations above")
print("2. Check error_analysis_details.csv for specific cases")
print("3. Generate visualizations with: python src/visualize_errors.py")
print("="*80)
