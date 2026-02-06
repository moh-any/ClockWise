import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.multioutput import MultiOutputRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer, TransformedTargetRegressor
import joblib
import sys

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
    'temperature_2m', 'relative_humidity_2m', 'precipitation', 
    'rain', 'snowfall', 'cloud_cover', 'wind_speed_10m', 'weather_severity'
]

preprocessor = ColumnTransformer(
    transformers=[('scaler', StandardScaler(), scale_features)],
    remainder='passthrough'
)

# Build pipeline (using your best hyperparameters)
pipeline = Pipeline([
    ('preprocessor', preprocessor),
    ('model', MultiOutputRegressor(RandomForestRegressor(
        n_jobs=-1,
        random_state=42,
        max_depth=12,
        min_samples_leaf=7,
        max_features=0.5,
        n_estimators=600,
        bootstrap=True
    )))
])

# Train with target transformation
model = TransformedTargetRegressor(
    regressor=pipeline,
    func=np.log1p,
    inverse_func=np.expm1
)

print("Training model...")
model.fit(x_train, y_train)

# Evaluate
y_pred = model.predict(x_test)
from sklearn.metrics import mean_absolute_error, r2_score

for i, target in enumerate(target_features):
    mae = mean_absolute_error(y_test.iloc[:, i], y_pred[:, i])
    r2 = r2_score(y_test.iloc[:, i], y_pred[:, i])
    print(f"{target}: MAE={mae:.4f}, R2={r2:.4f}")

# Save model
metadata = {
    'python_version': sys.version,
    'sklearn_version': sys.modules['sklearn'].__version__,
    'model_type': 'RandomForestRegressor',
    'features': list(x.columns),  # IMPORTANT: includes is_holiday
    'hyperparameters': {
        'max_depth': 12,
        'min_samples_leaf': 7,
        'max_features': 0.5,
        'n_estimators': 600,
        'bootstrap': True
    },
    'training_size': len(x_train),
    'test_size': len(x_test),
    'version': '2.0_with_holidays'
}

joblib.dump(model, 'data/models/rf_model.joblib')
joblib.dump(metadata, 'data/models/rf_model_metadata.json')

print("\nModel saved successfully!")
print(f"Features: {len(x.columns)} (including is_holiday)")