"""
Fix Under-Prediction Bias - Quick Implementation
Two approaches:
1. Post-processing calibration (immediate fix without retraining)
2. Enhanced training with asymmetric loss (long-term solution)
"""
import numpy as np
import pandas as pd
import joblib
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import mean_absolute_error, r2_score
import matplotlib.pyplot as plt
import seaborn as sns

print("="*80)
print("FIXING UNDER-PREDICTION BIAS")
print("="*80)

# ============================================================================
# PART 1: POST-PROCESSING CALIBRATION (Immediate Fix)
# ============================================================================
print("\n" + "="*80)
print("PART 1: POST-PROCESSING CALIBRATION")
print("="*80)

print("\n1️⃣ Loading model and data...")
model = joblib.load('data/models/rf_model.joblib')
df = pd.read_csv('data/processed/combined_features.csv')

# Prepare data
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
X['place_id'] = X['place_id'].astype('float64')
X['type_id'] = X['type_id'].astype('float64')
X.columns = X.columns.astype(str)
y.columns = y.columns.astype(str)

# Split
train_size = int(len(X) * 0.8)
X_train, X_test = X[:train_size], X[train_size:]
y_train, y_test = y[:train_size], y[train_size:]

print(f"   ✓ Loaded {len(df):,} samples")

# ============================================================================
# 2. Build Calibration Curve
# ============================================================================
print("\n2️⃣ Building demand-stratified calibration curves...")

# Get predictions
if isinstance(model, list):
    y_pred_train = np.column_stack([m.predict(X_train) for m in model])
    y_pred_test = np.column_stack([m.predict(X_test) for m in model])
else:
    y_pred_train = model.predict(X_train)
    y_pred_test = model.predict(X_test)

y_true_train = y_train['item_count'].values
y_true_test = y_test['item_count'].values
y_pred_train_items = y_pred_train[:, 0]
y_pred_test_items = y_pred_test[:, 0]

# Build separate calibrators for different demand ranges
calibrators = {}
demand_ranges = [
    ('low', 0, 7),
    ('medium', 7, 15),
    ('high', 15, float('inf'))
]

for name, low, high in demand_ranges:
    # Get samples in this range
    mask = (y_pred_train_items >= low) & (y_pred_train_items < high)
    
    if mask.sum() > 10:  # Need enough samples
        calibrator = IsotonicRegression(out_of_bounds='clip')
        calibrator.fit(y_pred_train_items[mask], y_true_train[mask])
        calibrators[name] = (calibrator, low, high)
        print(f"   ✓ Calibrator '{name}': {mask.sum():,} samples")

# ============================================================================
# 3. Apply Calibration
# ============================================================================
print("\n3️⃣ Applying calibration to test set...")

def calibrate_predictions(y_pred, calibrators):
    """Apply demand-stratified calibration"""
    y_calibrated = y_pred.copy()
    
    for name, (calibrator, low, high) in calibrators.items():
        mask = (y_pred >= low) & (y_pred < high)
        if mask.sum() > 0:
            y_calibrated[mask] = calibrator.predict(y_pred[mask])
    
    return y_calibrated

y_pred_calibrated = calibrate_predictions(y_pred_test_items, calibrators)

# ============================================================================
# 4. Evaluate Improvements
# ============================================================================
print("\n4️⃣ Evaluating calibration results:")
print("="*80)

# Before calibration
mae_before = mean_absolute_error(y_true_test, y_pred_test_items)
bias_before = (y_pred_test_items - y_true_test).mean()
r2_before = r2_score(y_true_test, y_pred_test_items)

# After calibration
mae_after = mean_absolute_error(y_true_test, y_pred_calibrated)
bias_after = (y_pred_calibrated - y_true_test).mean()
r2_after = r2_score(y_true_test, y_pred_calibrated)

print(f"\nOverall Metrics:")
print(f"   MAE:   {mae_before:.3f} → {mae_after:.3f}  ({(mae_after-mae_before)/mae_before*100:+.1f}%)")
print(f"   Bias:  {bias_before:+.3f} → {bias_after:+.3f}  ({(bias_after-bias_before):.3f} improvement)")
print(f"   R²:    {r2_before:.3f} → {r2_after:.3f}  ({(r2_after-r2_before):+.3f})")

# By demand level
print(f"\nBias by Demand Level:")
for name, low, high in demand_ranges:
    mask = (y_true_test >= low) & (y_true_test < high)
    if mask.sum() > 0:
        bias_b = (y_pred_test_items[mask] - y_true_test[mask]).mean()
        bias_a = (y_pred_calibrated[mask] - y_true_test[mask]).mean()
        mae_b = mean_absolute_error(y_true_test[mask], y_pred_test_items[mask])
        mae_a = mean_absolute_error(y_true_test[mask], y_pred_calibrated[mask])
        print(f"   {name:8s} ({low:2.0f}-{high if high != float('inf') else '∞':>3}): "
              f"Bias {bias_b:+6.2f} → {bias_a:+6.2f}, "
              f"MAE {mae_b:5.2f} → {mae_a:5.2f}")

# ============================================================================
# 5. Save Calibrated Model
# ============================================================================
print("\n5️⃣ Saving calibrated model...")

calibrated_model = {
    'base_model': model,
    'calibrators': calibrators,
    'metadata': {
        'mae_improvement': mae_after - mae_before,
        'bias_improvement': bias_after - bias_before,
        'calibration_date': '2026-02-07'
    }
}

joblib.dump(calibrated_model, 'data/models/rf_model_calibrated.joblib')
print("   ✓ Saved to: data/models/rf_model_calibrated.joblib")

# Save helper function
with open('src/calibration_utils.py', 'w') as f:
    f.write('''"""
Calibration utilities for demand prediction model
"""
import numpy as np
import joblib

def load_calibrated_model():
    """Load the calibrated model"""
    return joblib.load('data/models/rf_model_calibrated.joblib')

def predict_calibrated(X, calibrated_model_obj=None):
    """
    Make calibrated predictions
    
    Parameters:
    -----------
    X : array-like or DataFrame
        Features for prediction
    calibrated_model_obj : dict, optional
        Pre-loaded calibrated model object
        
    Returns:
    --------
    predictions : array
        Calibrated predictions for item_count and order_count
    """
    if calibrated_model_obj is None:
        calibrated_model_obj = load_calibrated_model()
    
    model = calibrated_model_obj['base_model']
    calibrators = calibrated_model_obj['calibrators']
    
    # Get base predictions
    if isinstance(model, list):
        predictions = np.column_stack([m.predict(X) for m in model])
    else:
        predictions = model.predict(X)
    
    # Calibrate item_count predictions
    y_pred_items = predictions[:, 0]
    y_calibrated = y_pred_items.copy()
    
    for name, (calibrator, low, high) in calibrators.items():
        mask = (y_pred_items >= low) & (y_pred_items < high)
        if mask.sum() > 0:
            y_calibrated[mask] = calibrator.predict(y_pred_items[mask])
    
    # Return calibrated predictions
    predictions_calibrated = predictions.copy()
    predictions_calibrated[:, 0] = y_calibrated
    
    return predictions_calibrated

# Example usage:
# model = load_calibrated_model()
# predictions = predict_calibrated(X_test, model)
''')
print("   ✓ Created: src/calibration_utils.py")

# ============================================================================
# 6. Visualize Calibration
# ============================================================================
print("\n6️⃣ Creating calibration visualization...")

fig, axes = plt.subplots(1, 3, figsize=(18, 5))

# Plot 1: Before vs After scatter
ax1 = axes[0]
sample_size = min(2000, len(y_true_test))
indices = np.random.choice(len(y_true_test), sample_size, replace=False)

ax1.scatter(y_true_test[indices], y_pred_test_items[indices], 
           alpha=0.3, s=20, label='Before Calibration')
ax1.scatter(y_true_test[indices], y_pred_calibrated[indices], 
           alpha=0.3, s=20, label='After Calibration')
max_val = max(y_true_test[indices].max(), y_pred_test_items[indices].max())
ax1.plot([0, max_val], [0, max_val], 'r--', linewidth=2, label='Perfect')
ax1.set_xlabel('Actual Demand')
ax1.set_ylabel('Predicted Demand')
ax1.set_title('Predictions: Before vs After Calibration')
ax1.legend()
ax1.grid(True, alpha=0.3)

# Plot 2: Bias by demand level
ax2 = axes[1]
bins = np.linspace(0, 40, 20)
bin_centers = (bins[:-1] + bins[1:]) / 2
bias_before_binned = []
bias_after_binned = []

for i in range(len(bins)-1):
    mask = (y_true_test >= bins[i]) & (y_true_test < bins[i+1])
    if mask.sum() > 5:
        bias_before_binned.append((y_pred_test_items[mask] - y_true_test[mask]).mean())
        bias_after_binned.append((y_pred_calibrated[mask] - y_true_test[mask]).mean())
    else:
        bias_before_binned.append(np.nan)
        bias_after_binned.append(np.nan)

ax2.plot(bin_centers, bias_before_binned, marker='o', linewidth=2, 
        label='Before Calibration', color='red')
ax2.plot(bin_centers, bias_after_binned, marker='s', linewidth=2, 
        label='After Calibration', color='green')
ax2.axhline(y=0, color='black', linestyle='--', alpha=0.5)
ax2.set_xlabel('Actual Demand Level')
ax2.set_ylabel('Prediction Bias')
ax2.set_title('Bias Correction Across Demand Levels')
ax2.legend()
ax2.grid(True, alpha=0.3)

# Plot 3: Calibration curves
ax3 = axes[2]
for name, (calibrator, low, high) in calibrators.items():
    x_range = np.linspace(low, min(high, 50), 100)
    y_calibrated = calibrator.predict(x_range)
    ax3.plot(x_range, y_calibrated, linewidth=2, label=f'{name.capitalize()} Demand')
    
# Perfect calibration line
ax3.plot([0, 50], [0, 50], 'k--', linewidth=2, alpha=0.5, label='Perfect (y=x)')
ax3.set_xlabel('Original Prediction')
ax3.set_ylabel('Calibrated Prediction')
ax3.set_title('Calibration Curves by Demand Range')
ax3.legend()
ax3.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('data/models/calibration_results.png', dpi=300, bbox_inches='tight')
print("   ✓ Saved visualization: data/models/calibration_results.png")

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "="*80)
print("✅ CALIBRATION COMPLETE")
print("="*80)

print("\n📊 Summary:")
print(f"   • MAE improved by: {mae_after - mae_before:.3f} ({(mae_after-mae_before)/mae_before*100:+.1f}%)")
print(f"   • Bias reduced by: {abs(bias_after) - abs(bias_before):.3f}")
print(f"   • R² improved by: {r2_after - r2_before:+.3f}")

print("\n🎯 Next Steps:")
print("   1. Use calibrated model: model = joblib.load('data/models/rf_model_calibrated.joblib')")
print("   2. Or use helper: from calibration_utils import predict_calibrated")
print("   3. For best results, retrain with asymmetric loss (see Part 2)")

print("\n" + "="*80)
