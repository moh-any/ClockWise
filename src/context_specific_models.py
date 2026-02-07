import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.multioutput import MultiOutputRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer, TransformedTargetRegressor
from sklearn.metrics import mean_absolute_error, r2_score, mean_squared_error
from sklearn.cluster import KMeans
import joblib
import json
import warnings
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
warnings.filterwarnings('ignore')

# Try to import optional libraries
try:
    from lightgbm import LGBMRegressor
    LIGHTGBM_AVAILABLE = True
except ImportError:
    print("Warning: LightGBM not available. Using RandomForest instead.")
    LIGHTGBM_AVAILABLE = False

print("="*80)
print("CONTEXT-SPECIFIC MODELS: INTUITIVE vs K-MEANS CLUSTERING")
print("="*80)
print()

# ============================================================================
# SAMPLE WEIGHTING FUNCTION
# ============================================================================
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


def fit_model_with_weights(model, x_train, y_train, sample_weights=None):
    """
    Fit a model with sample weights, handling sklearn parameter routing properly
    
    Parameters:
    -----------
    model : sklearn estimator
        Model to fit (can be TransformedTargetRegressor with Pipeline)
    x_train : array-like
        Training features
    y_train : array-like
        Training targets
    sample_weights : array-like, optional
        Sample weights
        
    Returns:
    --------
    fitted model
    """
    if sample_weights is None:
        return model.fit(x_train, y_train)
    
    # For TransformedTargetRegressor, we need a different approach
    # to avoid sklearn's complex parameter routing with sample_weight
    if isinstance(model, TransformedTargetRegressor):
        # Transform targets manually
        if model.func is not None:
            y_transformed = model.func(y_train)
        else:
            y_transformed = y_train
        
        # Fit the underlying pipeline with transformed targets and weights
        # The pipeline has steps: ('preprocessor', ...), ('model', MultiOutputRegressor(...))
        # So we pass sample_weight with the step prefix 'model__'
        pipeline = model.regressor
        pipeline.fit(x_train, y_transformed, model__sample_weight=sample_weights)
        
        # Store the fitted pipeline
        model.regressor_ = pipeline
        
        # Set up the transformer for inverse transformation
        from sklearn.preprocessing import FunctionTransformer
        if model.func is not None:
            model.transformer_ = FunctionTransformer(
                func=model.func,
                inverse_func=model.inverse_func,
                check_inverse=False
            )
            # Fit transformer on y to set internal attributes
            model.transformer_.fit(y_train)
        
        # Set training dimension (needed for sklearn >= 1.0)
        if hasattr(y_train, 'shape'):
            model._training_dim = y_train.shape[1] if len(y_train.shape) > 1 else 1
        else:
            model._training_dim = 1
            
        return model
    else:
        # Simple model - pass weights directly
        return model.fit(x_train, y_train, sample_weight=sample_weights)

# ============================================================================
# LOAD DATA
# ============================================================================
print("Loading data...")
df = pd.read_csv('data/processed/combined_features.csv')
print(f"Loaded data with shape: {df.shape}")

# Prepare features and targets
target_cols = ['item_count', 'order_count']
useless_features = ['total_revenue', 'avg_order_value', 'avg_items_per_order']  # Derived from targets!
exclude_cols = ['datetime'] + target_cols + useless_features

x = df.drop(exclude_cols, axis=1, errors='ignore')
x = x.drop(['longitude', 'latitude'], axis=1, errors='ignore')  # Also exclude location coords
y = df[target_cols]

# Handle missing values (same as train_model.py)
x['type_id'] = x['type_id'].fillna(-1)
x['waiting_time'] = x['waiting_time'].fillna(x['waiting_time'].median())
x['rating'] = x['rating'].fillna(x['rating'].median())
x['delivery'] = x['delivery'].fillna(0)
x['accepting_orders'] = x['accepting_orders'].fillna(0)

feature_cols = x.columns.tolist()

print(f"Features: {len(feature_cols)} (after excluding target-derived features)")
print(f"Targets: {len(target_cols)}")
print(f"Samples: {len(x)}")
print(f"Excluded features: {useless_features} + longitude + latitude (prevent data leakage)")

# Split data (time-based split)
split_idx = int(len(x) * 0.8)
x_train, x_test = x.iloc[:split_idx], x.iloc[split_idx:]
y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

print(f"\nTrain samples: {len(x_train)}")
print(f"Test samples: {len(x_test)}")

# Calculate sample weights for training data
print("\n" + "="*80)
print("CALCULATING SAMPLE WEIGHTS")
print("="*80)
sample_weights = calculate_sample_weights(y_train, weight_type='combined', temporal_range=(0.5, 1.0))
print(f"Sample weights calculated: {len(sample_weights)} samples")
print(f"  Weight range: [{sample_weights.min():.4f}, {sample_weights.max():.4f}]")
print(f"  Weight mean: {sample_weights.mean():.4f}")
print(f"  Weight std: {sample_weights.std():.4f}")
print(f"  Strategy: Combined (temporal + demand-level)")
print(f"  >> Recent data and high-demand scenarios get higher weights")
print("="*80 + "\n")

# Setup preprocessing
scale_features = [
    'rating', 'waiting_time', 'total_campaigns', 'avg_discount',
    'prev_hour_items', 'prev_day_items', 'prev_week_items', 'prev_month_items',
    'rolling_7d_avg_items', 'temperature_2m', 'relative_humidity_2m',
    'precipitation', 'rain', 'snowfall', 'cloud_cover', 'wind_speed_10m',
    'weather_severity', 'rolling_3d_avg_items', 'rolling_14d_avg_items',
    'rolling_30d_avg_items', 'rolling_7d_std_items',
    'feels_like_temp', 'bad_weather_score', 'temp_change_1h', 'temp_change_3h'
]
scale_features = [f for f in scale_features if f in x.columns]

preprocessor = ColumnTransformer(
    transformers=[('scaler', StandardScaler(), scale_features)],
    remainder='passthrough'
)

# ============================================================================
# BASELINE: SINGLE MODEL FOR ALL DATA
# ============================================================================
print("\n" + "="*80)
print("BASELINE: SINGLE MODEL FOR ALL DATA")
print("="*80)

def create_model():
    """Create a model (LightGBM if available, otherwise RandomForest)"""
    if LIGHTGBM_AVAILABLE:
        return MultiOutputRegressor(LGBMRegressor(
            n_estimators=500,
            max_depth=9,
            learning_rate=0.029,
            num_leaves=29,
            subsample=0.91,
            colsample_bytree=0.82,
            min_child_samples=30,
            reg_alpha=0.086,
            reg_lambda=0.109,
            random_state=42,
            n_jobs=-1,
            verbose=-1
        ))
    else:
        return MultiOutputRegressor(RandomForestRegressor(
            n_estimators=600,
            max_depth=12,
            min_samples_leaf=7,
            max_features=0.5,
            bootstrap=True,
            random_state=42,
            n_jobs=-1,
            verbose=0
        ))

baseline_pipeline = Pipeline([
    ('preprocessor', preprocessor),
    ('model', create_model())
])

baseline_model = TransformedTargetRegressor(
    regressor=baseline_pipeline,
    func=np.log1p,
    inverse_func=np.expm1
)

print("Training baseline model...")
fit_model_with_weights(baseline_model, x_train, y_train, sample_weights)
baseline_pred = baseline_model.predict(x_test)

baseline_mae_items = mean_absolute_error(y_test['item_count'], baseline_pred[:, 0])
baseline_mae_orders = mean_absolute_error(y_test['order_count'], baseline_pred[:, 1])
baseline_r2_items = r2_score(y_test['item_count'], baseline_pred[:, 0])
baseline_r2_orders = r2_score(y_test['order_count'], baseline_pred[:, 1])

print(f"\nBaseline Results:")
print(f"  Item Count - MAE: {baseline_mae_items:.4f}, R²: {baseline_r2_items:.4f}")
print(f"  Order Count - MAE: {baseline_mae_orders:.4f}, R²: {baseline_r2_orders:.4f}")

# ============================================================================
# APPROACH 1: INTUITIVE CATEGORIZATION
# ============================================================================
print("\n" + "="*80)
print("APPROACH 1: INTUITIVE CATEGORIZATION")
print("="*80)

def determine_intuitive_context(df_subset):
    """
    Determine context based on time of day and day of week
    Categories:
    - weekday_breakfast (7-10)
    - weekday_lunch (11-14)
    - weekday_dinner (18-21)
    - weekday_other (all other weekday hours)
    - weekend_day (Sat/Sun 6-22)
    - weekend_night (Sat/Sun 22-6)
    """
    contexts = []
    for _, row in df_subset.iterrows():
        hour = row['hour']
        dow = row['day_of_week']
        
        is_weekend = dow >= 5  # Saturday=5, Sunday=6
        
        if is_weekend:
            if 6 <= hour < 22:
                contexts.append('weekend_day')
            else:
                contexts.append('weekend_night')
        else:
            if 7 <= hour <= 10:
                contexts.append('weekday_breakfast')
            elif 11 <= hour <= 14:
                contexts.append('weekday_lunch')
            elif 18 <= hour <= 21:
                contexts.append('weekday_dinner')
            else:
                contexts.append('weekday_other')
    
    return contexts

# Assign contexts
train_contexts = determine_intuitive_context(x_train)
test_contexts = determine_intuitive_context(x_test)

x_train_intuitive = x_train.copy()
x_test_intuitive = x_test.copy()
x_train_intuitive['context'] = train_contexts
x_test_intuitive['context'] = test_contexts

# Display context distribution
print("\nContext Distribution:")
print("\nTraining Set:")
print(pd.Series(train_contexts).value_counts().sort_index())
print("\nTest Set:")
print(pd.Series(test_contexts).value_counts().sort_index())

# Train separate models for each context
intuitive_models = {}
contexts = sorted(set(train_contexts))

print(f"\nTraining {len(contexts)} context-specific models...")
for context in contexts:
    print(f"\n  Training model for: {context}")
    
    # Get data for this context
    train_mask = x_train_intuitive['context'] == context
    x_train_ctx = x_train_intuitive[train_mask].drop('context', axis=1)
    y_train_ctx = y_train[train_mask]
    
    print(f"    Samples: {len(x_train_ctx)}")
    
    # Calculate sample weights for this context
    ctx_sample_weights = calculate_sample_weights(y_train_ctx, weight_type='combined', temporal_range=(0.5, 1.0))
    
    # Train model
    ctx_pipeline = Pipeline([
        ('preprocessor', preprocessor),
        ('model', create_model())
    ])
    
    ctx_model = TransformedTargetRegressor(
        regressor=ctx_pipeline,
        func=np.log1p,
        inverse_func=np.expm1
    )
    
    fit_model_with_weights(ctx_model, x_train_ctx, y_train_ctx, ctx_sample_weights)
    intuitive_models[context] = ctx_model

# Make predictions using context-specific models
print("\nMaking predictions with intuitive models...")
intuitive_pred = np.zeros((len(x_test), 2))

for context in contexts:
    test_mask = x_test_intuitive['context'] == context
    if test_mask.sum() > 0:
        x_test_ctx = x_test_intuitive[test_mask].drop('context', axis=1)
        intuitive_pred[test_mask] = intuitive_models[context].predict(x_test_ctx)

# Evaluate intuitive approach
intuitive_mae_items = mean_absolute_error(y_test['item_count'], intuitive_pred[:, 0])
intuitive_mae_orders = mean_absolute_error(y_test['order_count'], intuitive_pred[:, 1])
intuitive_r2_items = r2_score(y_test['item_count'], intuitive_pred[:, 0])
intuitive_r2_orders = r2_score(y_test['order_count'], intuitive_pred[:, 1])

print(f"\nIntuitive Approach Results:")
print(f"  Item Count - MAE: {intuitive_mae_items:.4f}, R²: {intuitive_r2_items:.4f}")
print(f"  Order Count - MAE: {intuitive_mae_orders:.4f}, R²: {intuitive_r2_orders:.4f}")

# Evaluate by context
print("\nPerformance by Context:")
for context in contexts:
    test_mask = x_test_intuitive['context'] == context
    if test_mask.sum() > 0:
        ctx_mae = mean_absolute_error(
            y_test[test_mask]['item_count'], 
            intuitive_pred[test_mask, 0]
        )
        ctx_r2 = r2_score(
            y_test[test_mask]['item_count'], 
            intuitive_pred[test_mask, 0]
        )
        print(f"  {context:20} - MAE: {ctx_mae:.4f}, R²: {ctx_r2:.4f}, Samples: {test_mask.sum()}")

# ============================================================================
# APPROACH 2: K-MEANS CLUSTERING
# ============================================================================
print("\n" + "="*80)
print("APPROACH 2: K-MEANS CLUSTERING")
print("="*80)

# Use key features for clustering (time, venue, weather, history)
cluster_features = [
    'hour', 'day_of_week', 'month', 'is_weekend',
    'is_breakfast_rush', 'is_lunch_rush', 'is_dinner_rush',
    'place_id', 'type_id', 'rating', 'waiting_time',
    'temperature_2m', 'relative_humidity_2m', 'weather_severity',
    'rolling_7d_avg_items', 'prev_week_items'
]

# Filter to available features
cluster_features = [f for f in cluster_features if f in x_train.columns]
print(f"\nUsing {len(cluster_features)} features for clustering:")
print(f"  {', '.join(cluster_features)}")

# Prepare clustering data
x_train_cluster = x_train[cluster_features].fillna(0)
x_test_cluster = x_test[cluster_features].fillna(0)

# Standardize for clustering
scaler_cluster = StandardScaler()
x_train_scaled = scaler_cluster.fit_transform(x_train_cluster)
x_test_scaled = scaler_cluster.transform(x_test_cluster)

# Try different numbers of clusters
print("\nFinding optimal number of clusters...")
inertias = []
silhouette_scores_list = []
k_range = range(3, 11)

from sklearn.metrics import silhouette_score

for k in k_range:
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    kmeans.fit(x_train_scaled)
    inertias.append(kmeans.inertia_)
    
    # Calculate silhouette score (on sample for speed)
    sample_size = min(5000, len(x_train_scaled))
    sample_idx = np.random.choice(len(x_train_scaled), sample_size, replace=False)
    score = silhouette_score(x_train_scaled[sample_idx], kmeans.labels_[sample_idx])
    silhouette_scores_list.append(score)
    
    print(f"  k={k}: inertia={kmeans.inertia_:.0f}, silhouette={score:.4f}")

# Use k=6 as it matches intuitive approach and has good silhouette score
optimal_k = 6
print(f"\nUsing k={optimal_k} clusters")

# Train K-Means with optimal k
kmeans_final = KMeans(n_clusters=optimal_k, random_state=42, n_init=20)
train_clusters = kmeans_final.fit_predict(x_train_scaled)
test_clusters = kmeans_final.predict(x_test_scaled)

# Display cluster distribution
print("\nCluster Distribution:")
print("\nTraining Set:")
print(pd.Series(train_clusters).value_counts().sort_index())
print("\nTest Set:")
print(pd.Series(test_clusters).value_counts().sort_index())

# Analyze cluster characteristics
print("\nCluster Characteristics:")
x_train_with_clusters = x_train.copy()
x_train_with_clusters['cluster'] = train_clusters

for cluster_id in range(optimal_k):
    cluster_data = x_train_with_clusters[x_train_with_clusters['cluster'] == cluster_id]
    
    avg_hour = cluster_data['hour'].mean() if 'hour' in cluster_data else 0
    avg_dow = cluster_data['day_of_week'].mean() if 'day_of_week' in cluster_data else 0
    avg_demand = y_train.iloc[cluster_data.index]['item_count'].mean()
    
    print(f"  Cluster {cluster_id}: avg_hour={avg_hour:.1f}, avg_dow={avg_dow:.1f}, "
          f"avg_demand={avg_demand:.1f}, samples={len(cluster_data)}")

# Train separate models for each cluster
kmeans_models = {}
print(f"\nTraining {optimal_k} cluster-specific models...")

for cluster_id in range(optimal_k):
    print(f"\n  Training model for: Cluster {cluster_id}")
    
    # Get data for this cluster
    cluster_mask = train_clusters == cluster_id
    x_train_cluster_subset = x_train[cluster_mask]
    y_train_cluster_subset = y_train[cluster_mask]
    
    print(f"    Samples: {len(x_train_cluster_subset)}")
    
    # Calculate sample weights for this cluster
    cluster_sample_weights = calculate_sample_weights(y_train_cluster_subset, weight_type='combined', temporal_range=(0.5, 1.0))
    
    # Train model
    cluster_pipeline = Pipeline([
        ('preprocessor', preprocessor),
        ('model', create_model())
    ])
    
    cluster_model = TransformedTargetRegressor(
        regressor=cluster_pipeline,
        func=np.log1p,
        inverse_func=np.expm1
    )
    
    fit_model_with_weights(cluster_model, x_train_cluster_subset, y_train_cluster_subset, cluster_sample_weights)
    kmeans_models[cluster_id] = cluster_model

# Make predictions using cluster-specific models
print("\nMaking predictions with K-Means models...")
kmeans_pred = np.zeros((len(x_test), 2))

for cluster_id in range(optimal_k):
    cluster_mask = test_clusters == cluster_id
    if cluster_mask.sum() > 0:
        x_test_cluster_subset = x_test[cluster_mask]
        kmeans_pred[cluster_mask] = kmeans_models[cluster_id].predict(x_test_cluster_subset)

# Evaluate K-Means approach
kmeans_mae_items = mean_absolute_error(y_test['item_count'], kmeans_pred[:, 0])
kmeans_mae_orders = mean_absolute_error(y_test['order_count'], kmeans_pred[:, 1])
kmeans_r2_items = r2_score(y_test['item_count'], kmeans_pred[:, 0])
kmeans_r2_orders = r2_score(y_test['order_count'], kmeans_pred[:, 1])

print(f"\nK-Means Approach Results:")
print(f"  Item Count - MAE: {kmeans_mae_items:.4f}, R²: {kmeans_r2_items:.4f}")
print(f"  Order Count - MAE: {kmeans_mae_orders:.4f}, R²: {kmeans_r2_orders:.4f}")

# Evaluate by cluster
print("\nPerformance by Cluster:")
for cluster_id in range(optimal_k):
    cluster_mask = test_clusters == cluster_id
    if cluster_mask.sum() > 0:
        cluster_mae = mean_absolute_error(
            y_test[cluster_mask]['item_count'], 
            kmeans_pred[cluster_mask, 0]
        )
        cluster_r2 = r2_score(
            y_test[cluster_mask]['item_count'], 
            kmeans_pred[cluster_mask, 0]
        )
        print(f"  Cluster {cluster_id:2} - MAE: {cluster_mae:.4f}, R²: {cluster_r2:.4f}, Samples: {cluster_mask.sum()}")

# ============================================================================
# COMPARISON SUMMARY
# ============================================================================
print("\n" + "="*80)
print("COMPARISON SUMMARY")
print("="*80)

results = {
    'Baseline (Single Model)': {
        'mae_items': baseline_mae_items,
        'mae_orders': baseline_mae_orders,
        'r2_items': baseline_r2_items,
        'r2_orders': baseline_r2_orders
    },
    'Intuitive Categories': {
        'mae_items': intuitive_mae_items,
        'mae_orders': intuitive_mae_orders,
        'r2_items': intuitive_r2_items,
        'r2_orders': intuitive_r2_orders
    },
    'K-Means Clustering': {
        'mae_items': kmeans_mae_items,
        'mae_orders': kmeans_mae_orders,
        'r2_items': kmeans_r2_items,
        'r2_orders': kmeans_r2_orders
    }
}

print("\nItem Count Predictions:")
print(f"{'Approach':<30} {'MAE':>12} {'R²':>12} {'Improvement':>15}")
print("-" * 70)

for approach, metrics in results.items():
    improvement = ((baseline_mae_items - metrics['mae_items']) / baseline_mae_items) * 100
    print(f"{approach:<30} {metrics['mae_items']:>12.4f} {metrics['r2_items']:>12.4f} {improvement:>14.2f}%")

print("\nOrder Count Predictions:")
print(f"{'Approach':<30} {'MAE':>12} {'R²':>12} {'Improvement':>15}")
print("-" * 70)

for approach, metrics in results.items():
    improvement = ((baseline_mae_orders - metrics['mae_orders']) / baseline_mae_orders) * 100
    print(f"{approach:<30} {metrics['mae_orders']:>12.4f} {metrics['r2_orders']:>12.4f} {improvement:>14.2f}%")

# ============================================================================
# SAVE RESULTS AND MODELS
# ============================================================================
print("\n" + "="*80)
print("SAVING RESULTS")
print("="*80)

results_dir = Path('data/models')
results_dir.mkdir(exist_ok=True)

# Save comparison results
comparison_df = pd.DataFrame({
    'approach': list(results.keys()),
    'mae_items': [r['mae_items'] for r in results.values()],
    'mae_orders': [r['mae_orders'] for r in results.values()],
    'r2_items': [r['r2_items'] for r in results.values()],
    'r2_orders': [r['r2_orders'] for r in results.values()]
})

comparison_df['improvement_mae_items'] = (
    (comparison_df['mae_items'].iloc[0] - comparison_df['mae_items']) / 
    comparison_df['mae_items'].iloc[0] * 100
)

comparison_file = results_dir / 'context_specific_comparison.csv'
comparison_df.to_csv(comparison_file, index=False)
print(f"Saved comparison to: {comparison_file}")

# Save best approach models
best_approach_items = min(results.items(), key=lambda x: x[1]['mae_items'])
print(f"\nBest approach for item_count: {best_approach_items[0]}")

if best_approach_items[0] == 'Intuitive Categories':
    print("Saving intuitive models...")
    for context, model in intuitive_models.items():
        model_file = results_dir / f'intuitive_model_{context}.joblib'
        joblib.dump(model, model_file)
    
    metadata = {
        'approach': 'intuitive',
        'contexts': list(intuitive_models.keys()),
        'mae_items': intuitive_mae_items,
        'r2_items': intuitive_r2_items
    }
    
    with open(results_dir / 'intuitive_metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)
        
elif best_approach_items[0] == 'K-Means Clustering':
    print("Saving K-Means models...")
    joblib.dump(kmeans_final, results_dir / 'kmeans_clusterer.joblib')
    joblib.dump(scaler_cluster, results_dir / 'kmeans_scaler.joblib')
    
    for cluster_id, model in kmeans_models.items():
        model_file = results_dir / f'kmeans_model_cluster{cluster_id}.joblib'
        joblib.dump(model, model_file)
    
    metadata = {
        'approach': 'kmeans',
        'n_clusters': optimal_k,
        'cluster_features': cluster_features,
        'mae_items': kmeans_mae_items,
        'r2_items': kmeans_r2_items
    }
    
    with open(results_dir / 'kmeans_metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)

print("\n" + "="*80)
print("CONTEXT-SPECIFIC MODELS EVALUATION COMPLETE")
print("="*80)
