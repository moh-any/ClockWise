import joblib
import json

metadata = joblib.load('data/models/rf_model_metadata.json')

print('='*80)
print('PHASE 4 SAVED MODEL METRICS')
print('='*80)

print(f"\nModel: {metadata.get('model_name', 'Unknown')}")
print(f"Version: {metadata.get('version', 'Unknown')}")

if 'metrics' in metadata:
    metrics = metadata['metrics']
    print(f"\nItem Count:")
    print(f"  MAE:  {metrics.get('item_count_mae', 'N/A')}")
    print(f"  RMSE: {metrics.get('item_count_rmse', 'N/A')}")
    print(f"  R2:   {metrics.get('item_count_r2', 'N/A')}")
    print(f"  WAPE: {metrics.get('item_count_wape', 'N/A')}%")
    
    print(f"\nOrder Count:")
    print(f"  MAE:  {metrics.get('order_count_mae', 'N/A')}")
    print(f"  R2:   {metrics.get('order_count_r2', 'N/A')}")

print('='*80)

# Now test the actual model predictions to see current state
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error

df = pd.read_csv('data/processed/combined_features.csv')
target_features = ['item_count', 'order_count']
useless_features = ['total_revenue', 'avg_order_value', 'avg_items_per_order']
X = df.drop(target_features + useless_features + ['datetime'], axis=1)
y = df[target_features]

X = X.drop(['longitude', 'latitude'], axis=1, errors='ignore')
X['type_id'] = X['type_id'].fillna(-1)
X['waiting_time'] = X['waiting_time'].fillna(X['waiting_time'].median())
X['rating'] = X['rating'].fillna(X['rating'].median())
X['delivery'] = X['delivery'].fillna(0)
X['accepting_orders'] = X['accepting_orders'].fillna(0)
X['place_id'] = X['place_id'].astype('float64')
X['type_id'] = X['type_id'].astype('float64')

train_size = int(len(X) * 0.8)
X_test = X[train_size:]
y_test = y[train_size:]

model = joblib.load('data/models/rf_model.joblib')
if isinstance(model, list):
    y_pred = np.column_stack([m.predict(X_test) for m in model])
else:
    y_pred = model.predict(X_test)

mae_test = mean_absolute_error(y_test['item_count'], y_pred[:, 0])
bias_test = (y_pred[:, 0] - y_test['item_count']).mean()

print("\nACTUAL CURRENT PERFORMANCE ON TEST SET:")
print(f"  MAE:  {mae_test:.4f}")
print(f"  Bias: {bias_test:+.4f}")

print("\n" + "="*80)
print("CONCLUSION:")
if abs(mae_test - metrics.get('item_count_mae', 0)) < 0.1:
    print("✅ Model performance matches Phase 4 saved metrics")
else:
    print(f"⚠️  Performance mismatch!")
    print(f"   Saved: {metrics.get('item_count_mae', 'N/A')}")
    print(f"   Current: {mae_test:.4f}")
    print("   Model may have been trained differently than expected")
print('='*80)
