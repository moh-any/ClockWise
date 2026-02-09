import pandas as pd
import matplotlib.pyplot as plt
import joblib

# Load model and data
model = joblib.load('../data/models/rf_model.joblib')
df = pd.read_csv('../data/processed/combined_features.csv')

# Prepare data (same preprocessing)
target_features = ['item_count', 'order_count']
useless_features = ['total_revenue', 'avg_order_value', 'avg_items_per_order']
x, y = df.drop(target_features, axis=1), df[target_features]

# Keep datetime for plotting
datetime_col = x['datetime'].copy()
x = x.drop(useless_features + ['datetime'], axis=1)

# Handle nulls
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
datetime_test = datetime_col[train_size:]

# Predict
y_pred = model.predict(x_test)

# Calculate residuals for item_count
residuals = y_pred[:, 0] - y_test.iloc[:, 0].values

# Create DataFrame with dates
residual_df = pd.DataFrame({
    'datetime': pd.to_datetime(datetime_test),
    'residual': residuals
})
residual_df['date'] = residual_df['datetime'].dt.date

# Daily average residuals
daily_residuals = residual_df.groupby('date')['residual'].mean()

# Plot
plt.figure(figsize=(12, 6))
plt.plot(daily_residuals.index, daily_residuals.values, linewidth=2, color='#A23B72')
plt.axhline(y=0, color='black', linestyle='--', linewidth=1, alpha=0.5)
plt.fill_between(daily_residuals.index, 0, daily_residuals.values, 
                 where=(daily_residuals.values > 0), alpha=0.3, color='green', 
                 label='Over-prediction (log-transform bias)')
plt.fill_between(daily_residuals.index, 0, daily_residuals.values, 
                 where=(daily_residuals.values <= 0), alpha=0.3, color='red', 
                 label='Under-prediction')

plt.xlabel('Date', fontsize=12)
plt.ylabel('Average Residual (Predicted - Actual)', fontsize=12)
plt.title('Residuals Over Time: Log Transform Impact on Predictions', 
          fontsize=14, fontweight='bold')
plt.legend(loc='best', fontsize=10)
plt.grid(True, alpha=0.3)
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('residuals_over_time.png', dpi=300, bbox_inches='tight')
plt.show()