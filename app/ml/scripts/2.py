import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import mean_absolute_error, r2_score
import joblib

# Load model and data
model = joblib.load('../data/models/rf_model.joblib')
df = pd.read_csv('../data/processed/combined_features.csv')

# Prepare data (same preprocessing as training)
target_features = ['item_count', 'order_count']
useless_features = ['total_revenue', 'avg_order_value', 'avg_items_per_order']
x, y = df.drop(target_features, axis=1), df[target_features]
x = x.drop(useless_features + ['datetime'], axis=1)

# Handle nulls (same as training)
x = x.drop(['longitude', 'latitude'], axis=1)
x['type_id'] = x['type_id'].fillna(-1)
x['waiting_time'] = x['waiting_time'].fillna(x['waiting_time'].median())
x['rating'] = x['rating'].fillna(x['rating'].median())
x['delivery'] = x['delivery'].fillna(0)
x['accepting_orders'] = x['accepting_orders'].fillna(0)
x['place_id'] = x['place_id'].astype('float64')
x['type_id'] = x['type_id'].astype('float64')
x['is_holiday'] = x['is_holiday'].astype('int')

# Split
train_size = int(len(x) * 0.8)
x_test = x[train_size:]
y_test = y[train_size:]

# Predict
y_pred = model.predict(x_test)

# Focus on item_count (first target)
y_test_items = y_test.iloc[:, 0].values
y_pred_items = y_pred[:, 0]

# Plot
plt.figure(figsize=(10, 8))
plt.scatter(y_test_items, y_pred_items, alpha=0.4, s=20, color='#2E86AB', edgecolors='none')

# Perfect prediction line
max_val = max(y_test_items.max(), y_pred_items.max())
plt.plot([0, max_val], [0, max_val], 'r--', linewidth=2, label='Perfect Prediction')

# Calculate metrics
mae = mean_absolute_error(y_test_items, y_pred_items)
r2 = r2_score(y_test_items, y_pred_items)

# Median bias (due to log transform)
median_bias = np.median(y_pred_items - y_test_items)

textstr = f'MAE: {mae:.2f}\nR²: {r2:.2f}\nLog-transform with expm1'
plt.text(0.05, 0.95, textstr, transform=plt.gca().transAxes, 
         fontsize=11, verticalalignment='top', bbox=dict(boxstyle='round', 
         facecolor='wheat', alpha=0.8))

plt.xlabel('Actual Item Count', fontsize=12)
plt.ylabel('Predicted Item Count', fontsize=12)
plt.title('Demand Prediction: Actual vs Predicted (Random Forest)', 
          fontsize=14, fontweight='bold')
plt.legend(loc='lower right', fontsize=10)
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('actual_vs_predicted.png', dpi=300, bbox_inches='tight')
plt.show()

print(f"Test Set MAE: {mae:.2f}")
print(f"Test Set R²: {r2:.2f}")