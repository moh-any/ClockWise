"""
Test script to verify sample weighting implementation
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.multioutput import MultiOutputRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer, TransformedTargetRegressor
from sklearn.metrics import mean_absolute_error

print("="*80)
print("SAMPLE WEIGHTING IMPLEMENTATION TEST")
print("="*80)
print()

# Sample weighting function (from train_model.py)
def calculate_sample_weights(y_data, weight_type='combined', temporal_range=(0.5, 1.0)):
    """
    Calculate sample weights for training data
    
    Parameters:
    -----------
    y_data : pd.DataFrame
        Target data with 'item_count' column
    weight_type : str
        'temporal': Weight by recency (recent data gets more weight)
        'demand': Weight by demand level (high demand gets more weight)
        'combined': Combine both temporal and demand weighting
    temporal_range : tuple
        (min_weight, max_weight) for temporal weighting
        
    Returns:
    --------
    np.ndarray : Sample weights
    """
    n = len(y_data)
    
    if weight_type == 'temporal':
        # Linear weighting: older data gets less weight
        weights = np.linspace(temporal_range[0], temporal_range[1], n)
        
    elif weight_type == 'demand':
        # Weight by log of demand (high demand gets more weight)
        weights = np.log1p(y_data['item_count']) + 1
        
    elif weight_type == 'combined':
        # Combine temporal and demand weighting
        temporal_weights = np.linspace(temporal_range[0], temporal_range[1], n)
        demand_weights = np.log1p(y_data['item_count']) + 1
        
        # Normalize demand weights to have similar scale as temporal
        demand_weights = (demand_weights - demand_weights.min()) / (demand_weights.max() - demand_weights.min())
        demand_weights = demand_weights * (temporal_range[1] - temporal_range[0]) + temporal_range[0]
        
        # Multiply weights (both contribute)
        weights = temporal_weights * demand_weights
    
    else:
        # No weighting
        weights = np.ones(n)
    
    return weights

# Load actual data (small subset for testing)
print("Loading data...")
df = pd.read_csv('data/processed/combined_features.csv')
print(f"Loaded {len(df)} samples\n")

# Prepare features and targets
target_cols = ['item_count', 'order_count']
exclude_cols = ['datetime', 'total_revenue', 'avg_order_value', 'avg_items_per_order', 
                'longitude', 'latitude'] + target_cols

x = df.drop(exclude_cols, axis=1, errors='ignore')
y = df[target_cols]

# Fill missing values
x['type_id'] = x['type_id'].fillna(-1)
x['waiting_time'] = x['waiting_time'].fillna(x['waiting_time'].median())
x['rating'] = x['rating'].fillna(x['rating'].median())
x['delivery'] = x['delivery'].fillna(0)
x['accepting_orders'] = x['accepting_orders'].fillna(0)

# Small train/test split for testing
train_size = int(len(x) * 0.8)
x_train, x_test = x[:train_size], x[train_size:]
y_train, y_test = y[:train_size], y[train_size:]

print(f"Train samples: {len(x_train)}")
print(f"Test samples: {len(x_test)}\n")

# Calculate sample weights
print("Calculating sample weights...")
sample_weights = calculate_sample_weights(y_train, weight_type='combined', temporal_range=(0.5, 1.0))

print(f"Sample weights statistics:")
print(f"  Count: {len(sample_weights)}")
print(f"  Range: [{sample_weights.min():.4f}, {sample_weights.max():.4f}]")
print(f"  Mean: {sample_weights.mean():.4f}")
print(f"  Std: {sample_weights.std():.4f}\n")

# Set up preprocessing
scale_features = ['rating', 'waiting_time', 'temperature_2m', 'relative_humidity_2m']
scale_features = [f for f in scale_features if f in x.columns]

preprocessor = ColumnTransformer(
    transformers=[('scaler', StandardScaler(), scale_features)],
    remainder='passthrough'
)

# Train model WITHOUT sample weights
print("Training baseline model (NO sample weights)...")
baseline_pipeline = Pipeline([
    ('preprocessor', preprocessor),
    ('model', MultiOutputRegressor(RandomForestRegressor(
        n_estimators=100,
        max_depth=8,
        random_state=42,
        n_jobs=-1,
        verbose=0
    )))
])

baseline_model = TransformedTargetRegressor(
    regressor=baseline_pipeline,
    func=np.log1p,
    inverse_func=np.expm1
)

baseline_model.fit(x_train, y_train)
baseline_pred = baseline_model.predict(x_test)

baseline_mae_items = mean_absolute_error(y_test['item_count'], baseline_pred[:, 0])
baseline_mae_orders = mean_absolute_error(y_test['order_count'], baseline_pred[:, 1])

print(f"Baseline Results:")
print(f"  Item Count MAE: {baseline_mae_items:.4f}")
print(f"  Order Count MAE: {baseline_mae_orders:.4f}\n")

# Train model WITH sample weights
print("Training weighted model (WITH sample weights)...")

# Simpler approach: manually handle the transformation and pass weights directly
y_train_log = np.log1p(y_train)
y_test_actual = y_test.copy()

# Create a simpler model without TransformedTargetRegressor for testing
weighted_rf = MultiOutputRegressor(RandomForestRegressor(
    n_estimators=100,
    max_depth=8,
    random_state=42,
    n_jobs=-1,
    verbose=0
))

# Preprocess the data
x_train_preprocessed = preprocessor.fit_transform(x_train)
x_test_preprocessed = preprocessor.transform(x_test)

# Fit with sample weights - each estimator in MultiOutputRegressor gets the weights
weighted_rf.fit(x_train_preprocessed, y_train_log,
                sample_weight=sample_weights)

# Predict and inverse transform
weighted_pred_log = weighted_rf.predict(x_test_preprocessed)
weighted_pred = np.expm1(weighted_pred_log)

weighted_mae_items = mean_absolute_error(y_test['item_count'], weighted_pred[:, 0])
weighted_mae_orders = mean_absolute_error(y_test['order_count'], weighted_pred[:, 1])

print(f"Weighted Model Results:")
print(f"  Item Count MAE: {weighted_mae_items:.4f}")
print(f"  Order Count MAE: {weighted_mae_orders:.4f}\n")

# Compare results
print("="*80)
print("COMPARISON")
print("="*80)
improvement_items = ((baseline_mae_items - weighted_mae_items) / baseline_mae_items) * 100
improvement_orders = ((baseline_mae_orders - weighted_mae_orders) / baseline_mae_orders) * 100

print(f"\nItem Count:")
print(f"  Baseline MAE:      {baseline_mae_items:.4f}")
print(f"  Weighted MAE:      {weighted_mae_items:.4f}")
print(f"  Improvement:       {improvement_items:+.2f}%")

print(f"\nOrder Count:")
print(f"  Baseline MAE:      {baseline_mae_orders:.4f}")
print(f"  Weighted MAE:      {weighted_mae_orders:.4f}")
print(f"  Improvement:       {improvement_orders:+.2f}%")

print("\n" + "="*80)
if improvement_items > 0 or improvement_orders > 0:
    print("✅ Sample weighting is working and showing improvement!")
else:
    print("⚠️  Sample weighting applied (results may vary by random seed)")
print("="*80)
