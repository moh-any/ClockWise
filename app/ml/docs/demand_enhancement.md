# Demand Prediction Model Enhancement Plan

**Document Version**: 1.0  
**Date**: February 7, 2026  
**Current Model**: Random Forest v2.0 with Holiday Features

---

## 📊 Current Model State

### Performance Baseline
- **Model Type**: Random Forest Regressor with MultiOutput
- **Transformation**: Log1p (log-transform targets)
- **Features**: 34 features
- **Training Data**: 65,608 samples (80%)
- **Test Data**: 16,403 samples (20%)
- **Targets**: 
  - `item_count` (mean=8.25, std=9.42)
  - `order_count` (mean=4.88, std=5.63)

### Current Hyperparameters
```python
{
    'n_estimators': 600,
    'max_depth': 12,
    'min_samples_leaf': 7,
    'max_features': 0.5,
    'bootstrap': True
}
```

### Existing Features
- **Time features**: hour, day_of_week, month, week_of_year, is_holiday
- **Venue features**: place_id, type_id, waiting_time, rating, delivery, accepting_orders
- **Campaign features**: total_campaigns, avg_discount
- **Lag features**: prev_hour_items, prev_day_items, prev_week_items, prev_month_items, rolling_7d_avg_items
- **Weather features**: temperature_2m, relative_humidity_2m, precipitation, rain, snowfall, cloud_cover, wind_speed_10m, weather_severity, weather indicators (is_rainy, is_snowy, is_cold, is_hot, is_cloudy, is_windy, good_weather)

---

## 🚀 Enhancement Strategies

### 1. Feature Engineering Improvements

#### 1.1 Advanced Time-Based Features

**Cyclical Encoding** (High Priority)
```python
# Transform periodic features to capture cyclical nature
df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
df['day_of_week_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
df['day_of_week_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)
df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)
```

**Benefits**: Helps model understand that hour 23 is close to hour 0, day 6 is close to day 0

**Time Context Indicators**
```python
# Rush hour periods
df['is_breakfast_rush'] = ((df['hour'] >= 7) & (df['hour'] <= 9)).astype(int)
df['is_lunch_rush'] = ((df['hour'] >= 11) & (df['hour'] <= 13)).astype(int)
df['is_dinner_rush'] = ((df['hour'] >= 18) & (df['hour'] <= 20)).astype(int)
df['is_late_night'] = ((df['hour'] >= 22) | (df['hour'] <= 2)).astype(int)

# Weekend/weekday
df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)

# Special periods
df['is_month_start'] = (df['datetime'].dt.day <= 5).astype(int)
df['is_month_end'] = (df['datetime'].dt.day >= 25).astype(int)
```

**Expected Impact**: 5-8% MAE improvement

---

#### 1.2 Enhanced Lag and Rolling Features

**Multiple Rolling Windows**
```python
# Different time horizons
for window in [3, 7, 14, 30]:
    df[f'rolling_{window}d_avg_items'] = (
        df.groupby('place_id')['item_count']
        .transform(lambda x: x.rolling(window * 24, min_periods=1).mean())
    )
    
# Volatility features
df['rolling_7d_std_items'] = (
    df.groupby('place_id')['item_count']
    .transform(lambda x: x.rolling(7 * 24, min_periods=1).std())
)

# Trend features
df['demand_trend_7d'] = (
    df.groupby('place_id')['item_count']
    .transform(lambda x: x.rolling(7 * 24, min_periods=2).apply(
        lambda y: np.polyfit(range(len(y)), y, 1)[0] if len(y) > 1 else 0
    ))
)
```

**Same-Time Historical Lags**
```python
# More predictive: same hour last week/2 weeks
df['lag_same_hour_last_week'] = (
    df.groupby('place_id')['item_count'].shift(168)  # 7 * 24
)
df['lag_same_hour_2_weeks'] = (
    df.groupby('place_id')['item_count'].shift(336)  # 14 * 24
)
```

**Expected Impact**: 8-12% MAE improvement

---

#### 1.3 Venue-Specific Features

**Historical Performance by Context**
```python
# Average demand by hour for each venue
venue_hour_avg = df.groupby(['place_id', 'hour'])['item_count'].transform('mean')
df['venue_hour_avg'] = venue_hour_avg

# Average demand by day of week for each venue
venue_dow_avg = df.groupby(['place_id', 'day_of_week'])['item_count'].transform('mean')
df['venue_dow_avg'] = venue_dow_avg

# Venue volatility (consistency indicator)
venue_std = df.groupby('place_id')['item_count'].transform('std')
df['venue_volatility'] = venue_std

# Venue size/scale indicator
venue_total = df.groupby('place_id')['item_count'].transform('sum')
df['venue_total_items'] = venue_total

# Recent growth trend
df['venue_growth_recent_vs_historical'] = (
    df['rolling_7d_avg_items'] / df['rolling_30d_avg_items']
).fillna(1)
```

**Competitive Features** (if location data available)
```python
# Number of venues within 1km radius
# This would require spatial joins with place coordinates
df['nearby_venues_count'] = calculate_nearby_venues(df)

# Venue market share in area
df['venue_market_share'] = calculate_market_share(df)
```

**Expected Impact**: 10-15% MAE improvement

---

#### 1.4 Weather Interaction Features

**Comfort Index**
```python
# Feels-like temperature
df['feels_like_temp'] = (
    df['temperature_2m'] 
    - (df['wind_speed_10m'] * 0.5)
    + (df['relative_humidity_2m'] * 0.1)
)

# Bad weather composite score
df['bad_weather_score'] = (
    (df['precipitation'] > 0).astype(int) * 0.4 +
    (df['wind_speed_10m'] > 20).astype(int) * 0.3 +
    (df['cloud_cover'] > 70).astype(int) * 0.3
)
```

**Weather Change Features**
```python
# Temperature trend
df['temp_change_1h'] = df.groupby('place_id')['temperature_2m'].diff(1)
df['temp_change_3h'] = df.groupby('place_id')['temperature_2m'].diff(3)

# Weather deterioration
df['weather_getting_worse'] = (
    (df.groupby('place_id')['weather_severity'].diff(1) > 0).astype(int)
)
```

**Time-Weather Interactions**
```python
# Weekend and good weather (higher outdoor dining)
df['weekend_good_weather'] = df['is_weekend'] * df['good_weather']

# Rush hour in bad weather (delivery preference)
df['rush_bad_weather'] = (
    (df['is_lunch_rush'] | df['is_dinner_rush']) * df['bad_weather_score']
)

# Cold evening (comfort food demand)
df['cold_evening'] = (df['is_cold'] * (df['hour'] >= 18).astype(int))
```

**Expected Impact**: 5-10% MAE improvement

---

### 2. Model Architecture Improvements

#### 2.1 Try Alternative Algorithms

**XGBoost Implementation**
```python
from xgboost import XGBRegressor
from sklearn.multioutput import MultiOutputRegressor

xgb_model = MultiOutputRegressor(
    XGBRegressor(
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
        n_jobs=-1
    )
)
```

**Benefits**: Often outperforms Random Forest on structured data, better handling of feature interactions

**LightGBM Implementation**
```python
from lightgbm import LGBMRegressor

lgbm_model = MultiOutputRegressor(
    LGBMRegressor(
        n_estimators=1000,
        max_depth=10,
        learning_rate=0.05,
        num_leaves=31,
        subsample=0.8,
        colsample_bytree=0.8,
        min_child_samples=20,
        reg_alpha=0.1,
        reg_lambda=1.0,
        random_state=42,
        n_jobs=-1,
        verbose=-1
    )
)
```

**Benefits**: Faster training, handles large datasets efficiently, excellent with categorical features

**CatBoost Implementation**
```python
from catboost import CatBoostRegressor

catboost_model = MultiOutputRegressor(
    CatBoostRegressor(
        iterations=1000,
        depth=8,
        learning_rate=0.05,
        l2_leaf_reg=3.0,
        random_seed=42,
        verbose=False,
        # Automatic handling of categorical features
        cat_features=['place_id', 'type_id', 'hour', 'day_of_week']
    )
)
```

**Benefits**: Native categorical feature handling, often best out-of-the-box performance

**Expected Impact**: 10-15% MAE improvement (switching to XGBoost/LightGBM)

---

#### 2.2 Ensemble Approach

**Voting Ensemble**
```python
from sklearn.ensemble import VotingRegressor

ensemble = VotingRegressor(
    estimators=[
        ('rf', rf_pipeline),
        ('xgb', xgb_pipeline),
        ('lgbm', lgbm_pipeline),
        ('catboost', catboost_pipeline)
    ],
    weights=[0.25, 0.30, 0.30, 0.15]  # Tune based on validation performance
)
```

**Stacking Ensemble**
```python
from sklearn.ensemble import StackingRegressor
from sklearn.linear_model import Ridge

stacking = StackingRegressor(
    estimators=[
        ('rf', rf_model),
        ('xgb', xgb_model),
        ('lgbm', lgbm_model)
    ],
    final_estimator=Ridge(alpha=1.0),
    cv=TimeSeriesSplit(n_splits=5)
)
```

**Expected Impact**: 5-10% MAE improvement

---

#### 2.3 Hyperparameter Optimization

**Optuna Framework**
```python
import optuna

def objective(trial):
    params = {
        'n_estimators': trial.suggest_int('n_estimators', 400, 1200, step=100),
        'max_depth': trial.suggest_int('max_depth', 8, 20),
        'min_samples_leaf': trial.suggest_int('min_samples_leaf', 3, 15),
        'min_samples_split': trial.suggest_int('min_samples_split', 5, 25),
        'max_features': trial.suggest_float('max_features', 0.3, 0.8),
        'bootstrap': True
    }
    
    model = RandomForestRegressor(**params, random_state=42, n_jobs=-1)
    
    # Time series cross-validation
    tscv = TimeSeriesSplit(n_splits=5)
    scores = cross_val_score(
        model, X_train, y_train, 
        cv=tscv, 
        scoring='neg_mean_absolute_error'
    )
    
    return scores.mean()

study = optuna.create_study(direction='maximize')
study.optimize(objective, n_trials=100)
```

**Expected Impact**: 5-10% MAE improvement

---

### 3. Training Strategy Enhancements

#### 3.1 Time Series Cross-Validation

**Current Issue**: Single train/test split may not capture temporal patterns

**Solution**:
```python
from sklearn.model_selection import TimeSeriesSplit

tscv = TimeSeriesSplit(n_splits=5, test_size=8000)

# Evaluate with proper CV
scores = []
for train_idx, val_idx in tscv.split(X):
    X_train_fold, X_val_fold = X.iloc[train_idx], X.iloc[val_idx]
    y_train_fold, y_val_fold = y.iloc[train_idx], y.iloc[val_idx]
    
    model.fit(X_train_fold, y_train_fold)
    y_pred = model.predict(X_val_fold)
    
    mae = mean_absolute_error(y_val_fold, y_pred)
    scores.append(mae)

print(f"CV MAE: {np.mean(scores):.4f} ± {np.std(scores):.4f}")
```

**Expected Impact**: Better generalization, more reliable performance estimates

---

#### 3.2 Context-Specific Models

**Separate Models by Time Period**
```python
models = {
    'weekday_breakfast': train_model(df_weekday_breakfast),
    'weekday_lunch': train_model(df_weekday_lunch),
    'weekday_dinner': train_model(df_weekday_dinner),
    'weekday_other': train_model(df_weekday_other),
    'weekend_day': train_model(df_weekend_day),
    'weekend_night': train_model(df_weekend_night)
}

def predict(df_row):
    context = determine_context(df_row)
    return models[context].predict(df_row)
```

**Expected Impact**: 8-12% MAE improvement for specific contexts

---

#### 3.3 Sample Weighting

**Temporal Weighting** (give more importance to recent data)
```python
# Linear weighting: older data gets less weight
n = len(X_train)
sample_weights = np.linspace(0.5, 1.0, n)

model.fit(X_train, y_train, sample_weight=sample_weights)
```

**Demand-Level Weighting** (focus on predicting high demand)
```python
# Weight by log of demand (high demand gets more weight)
sample_weights = np.log1p(y_train['item_count']) + 1

model.fit(X_train, y_train, sample_weight=sample_weights)
```

**Expected Impact**: 3-5% MAE improvement, especially for high-demand scenarios

---

### 4. Data Quality Improvements

#### 4.1 Two-Stage Zero-Inflated Model

**Problem**: Many zero or low-demand hours distort predictions

**Solution**:
```python
# Stage 1: Binary classifier (will there be demand?)
classifier = RandomForestClassifier(...)
has_demand = (y_train['item_count'] > 0).astype(int)
classifier.fit(X_train, has_demand)

# Stage 2: Regressor (how much demand?)
X_train_positive = X_train[y_train['item_count'] > 0]
y_train_positive = y_train[y_train['item_count'] > 0]
regressor = RandomForestRegressor(...)
regressor.fit(X_train_positive, y_train_positive)

# Prediction
def predict_two_stage(X):
    has_demand_pred = classifier.predict_proba(X)[:, 1]
    demand_pred = regressor.predict(X)
    return has_demand_pred * demand_pred
```

**Expected Impact**: 10-15% MAE improvement

---

#### 4.2 Outlier Treatment

**Current Approach**: Implicit handling via log transform

**Enhanced Approach**:
```python
# Identify and cap outliers more conservatively
Q1 = df['item_count'].quantile(0.25)
Q3 = df['item_count'].quantile(0.75)
IQR = Q3 - Q1

lower_bound = max(0, Q1 - 2 * IQR)
upper_bound = Q3 + 3 * IQR

df['item_count_capped'] = df['item_count'].clip(lower_bound, upper_bound)

# Or use robust scaling
from sklearn.preprocessing import RobustScaler
scaler = RobustScaler(quantile_range=(5, 95))
```

**Expected Impact**: 2-5% MAE improvement

---

#### 4.3 Missing Value Strategies

**Current**: Simple median/zero imputation

**Enhanced**:
```python
from sklearn.impute import KNNImputer

# Use KNN imputation for better estimates
imputer = KNNImputer(n_neighbors=5, weights='distance')
X_imputed = imputer.fit_transform(X)

# Or predictive imputation
from sklearn.experimental import enable_iterative_imputer
from sklearn.impute import IterativeImputer

imputer = IterativeImputer(max_iter=10, random_state=42)
X_imputed = imputer.fit_transform(X)
```

**Expected Impact**: 2-4% MAE improvement

---

### 5. Evaluation & Monitoring Enhancements

#### 5.1 Comprehensive Metrics

**Additional Metrics**:
```python
# Mean Absolute Percentage Error
def mape(y_true, y_pred):
    return np.mean(np.abs((y_true - y_pred) / y_true)) * 100

# Weighted Absolute Percentage Error (better for zeros)
def wape(y_true, y_pred):
    return np.sum(np.abs(y_pred - y_true)) / np.sum(y_true) * 100

# Symmetric MAPE (bounded)
def smape(y_true, y_pred):
    return 100 * np.mean(2 * np.abs(y_pred - y_true) / (np.abs(y_true) + np.abs(y_pred)))

# Coverage at confidence levels
def coverage_80(y_true, y_pred_lower, y_pred_upper):
    return np.mean((y_true >= y_pred_lower) & (y_true <= y_pred_upper))
```

**Stratified Evaluation**:
```python
# Performance by demand level
low_demand = y_test['item_count'] < 5
medium_demand = (y_test['item_count'] >= 5) & (y_test['item_count'] < 15)
high_demand = y_test['item_count'] >= 15

print(f"Low demand MAE: {mae(y_test[low_demand], y_pred[low_demand])}")
print(f"Medium demand MAE: {mae(y_test[medium_demand], y_pred[medium_demand])}")
print(f"High demand MAE: {mae(y_test[high_demand], y_pred[high_demand])}")

# Performance by time period
for hour in [12, 18, 22]:  # Lunch, dinner, late night
    mask = X_test['hour'] == hour
    print(f"Hour {hour} MAE: {mae(y_test[mask], y_pred[mask])}")
```

---

#### 5.2 Error Analysis Framework

```python
# Create error analysis dataframe
error_df = X_test.copy()
error_df['y_true'] = y_test['item_count']
error_df['y_pred'] = y_pred[:, 0]
error_df['error'] = error_df['y_true'] - error_df['y_pred']
error_df['abs_error'] = np.abs(error_df['error'])
error_df['pct_error'] = 100 * error_df['error'] / (error_df['y_true'] + 1)

# Identify worst predictions
worst_predictions = error_df.nlargest(100, 'abs_error')

# Analyze error patterns
error_by_hour = error_df.groupby('hour')['abs_error'].mean()
error_by_dow = error_df.groupby('day_of_week')['abs_error'].mean()
error_by_venue = error_df.groupby('place_id')['abs_error'].mean().nlargest(20)

# Visualize
import matplotlib.pyplot as plt
fig, axes = plt.subplots(2, 2, figsize=(15, 10))
error_by_hour.plot(kind='bar', ax=axes[0, 0], title='MAE by Hour')
error_by_dow.plot(kind='bar', ax=axes[0, 1], title='MAE by Day of Week')
# ... more plots
```

---

### 6. Advanced Techniques

#### 6.1 Quantile Regression for Uncertainty

**Predict Intervals Instead of Points**:
```python
from sklearn.ensemble import GradientBoostingRegressor

# Train three models for different quantiles
model_lower = GradientBoostingRegressor(loss='quantile', alpha=0.1, ...)
model_median = GradientBoostingRegressor(loss='quantile', alpha=0.5, ...)
model_upper = GradientBoostingRegressor(loss='quantile', alpha=0.9, ...)

model_lower.fit(X_train, y_train)
model_median.fit(X_train, y_train)
model_upper.fit(X_train, y_train)

# Predictions with 80% confidence interval
pred_lower = model_lower.predict(X_test)
pred_median = model_median.predict(X_test)
pred_upper = model_upper.predict(X_test)
```

**Benefits**: 
- Uncertainty quantification for decision-making
- Better for inventory planning (use upper bound)
- Risk management

---

#### 6.2 Feature Selection

**Recursive Feature Elimination**:
```python
from sklearn.feature_selection import RFECV

rfecv = RFECV(
    estimator=RandomForestRegressor(n_estimators=100, random_state=42),
    step=1,
    cv=TimeSeriesSplit(n_splits=5),
    scoring='neg_mean_absolute_error',
    n_jobs=-1
)

rfecv.fit(X_train, y_train)
X_train_selected = X_train[:, rfecv.support_]

print(f"Optimal features: {rfecv.n_features_}")
print(f"Selected features: {X_train.columns[rfecv.support_].tolist()}")
```

**Permutation Importance**:
```python
from sklearn.inspection import permutation_importance

result = permutation_importance(
    model, X_test, y_test,
    n_repeats=10,
    random_state=42,
    scoring='neg_mean_absolute_error'
)

importance_df = pd.DataFrame({
    'feature': X_train.columns,
    'importance': result.importances_mean,
    'std': result.importances_std
}).sort_values('importance', ascending=False)
```

---

#### 6.3 Neural Network Approach

**When to Consider**: If tree-based models plateau

```python
import tensorflow as tf
from tensorflow import keras

def build_nn_model(input_dim, output_dim=2):
    model = keras.Sequential([
        keras.layers.Dense(128, activation='relu', input_shape=(input_dim,)),
        keras.layers.Dropout(0.3),
        keras.layers.Dense(64, activation='relu'),
        keras.layers.Dropout(0.2),
        keras.layers.Dense(32, activation='relu'),
        keras.layers.Dense(output_dim, activation='relu')  # Non-negative outputs
    ])
    
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=0.001),
        loss='mse',
        metrics=['mae']
    )
    
    return model

# Train with early stopping
early_stop = keras.callbacks.EarlyStopping(
    monitor='val_loss',
    patience=10,
    restore_best_weights=True
)

model = build_nn_model(X_train.shape[1])
history = model.fit(
    X_train, y_train,
    validation_split=0.2,
    epochs=100,
    batch_size=256,
    callbacks=[early_stop],
    verbose=0
)
```

---

## 📋 Implementation Roadmap

### Phase 1: Quick Wins (1-2 Days)
**Effort**: Low | **Impact**: High

1. ✅ **Add Cyclical Time Features**
   - Implement sin/cos encoding for hour, day_of_week, month
   - Expected: 5-8% improvement

2. ✅ **Create Time Context Indicators**
   - Add rush hour flags (breakfast, lunch, dinner)
   - Weekend indicator
   - Expected: 3-5% improvement

3. ✅ **Enhanced Rolling Features**
   - Add 3d, 14d, 30d rolling averages
   - Add rolling standard deviation (volatility)
   - Expected: 5-7% improvement

4. ✅ **Try XGBoost/LightGBM**
   - Quick model swap to compare performance
   - Expected: 10-15% improvement

**Total Expected**: 23-35% improvement

---

### Phase 2: Medium Effort (3-5 Days)
**Effort**: Medium | **Impact**: High

1. 📊 **Venue-Specific Historical Features**
   - Venue average by hour
   - Venue average by day of week
   - Venue volatility metrics
   - Expected: 10-15% improvement

2. 🌦️ **Weather Interaction Features**
   - Comfort index
   - Time-weather interactions
   - Weather change features
   - Expected: 5-10% improvement

3. ✅ **Time Series Cross-Validation**
   - Implement proper CV for evaluation
   - More reliable performance metrics
   - Expected: Better generalization

4. 🎯 **Build Model Ensemble**
   - Voting ensemble of top 3 models
   - Tune ensemble weights
   - Expected: 5-10% improvement

**Total Expected**: 20-35% improvement

---

### Phase 3: Advanced (1-2 Weeks)
**Effort**: High | **Impact**: Medium-High

1. 🎭 **Two-Stage Model**
   - Binary classifier for demand existence
   - Regressor for demand amount
   - Expected: 10-15% improvement

2. 📅 **Context-Specific Models**
   - Separate models for weekday/weekend
   - Separate models for different hours
   - Expected: 8-12% improvement

3. 📈 **Quantile Regression**
   - Prediction intervals for uncertainty
   - Better for operational planning
   - Expected: Improved decision-making

4. 🔬 **Hyperparameter Optimization**
   - Optuna for automated tuning
   - Expected: 5-10% improvement

5. 🧠 **Neural Network Experiment**
   - If tree models plateau
   - Capture complex interactions
   - Expected: 5-15% improvement (uncertain)

**Total Expected**: 28-52% improvement

---

## 📊 Expected Overall Impact

| Strategy | Conservative | Optimistic |
|----------|-------------|------------|
| **Phase 1** | 15% | 35% |
| **Phase 2** | 20% | 35% |
| **Phase 3** | 15% | 40% |
| **Total Potential** | **25-35%** | **40-60%** |

> **Note**: These improvements are **not fully additive**. Diminishing returns occur as multiple enhancements address overlapping patterns.

**Realistic Target**: 30-40% overall MAE improvement

---

## 🎯 Success Metrics

### Model Performance
- **Primary**: MAE reduction by 30%+
- **Secondary**: R² improvement to 0.75+
- **Tertiary**: WAPE < 25%

### Business Impact
- Prediction accuracy for surge detection: >85%
- False positive rate: <15%
- Coverage at 80% CI: >75%

### Operational
- Training time: <30 minutes
- Prediction latency: <100ms per batch
- Model size: <500MB

---

## 🔧 Technical Considerations

### Feature Engineering
- **Storage**: New features increase dataset size by ~40%
- **Computation**: Rolling features require sorted data by (place_id, datetime)
- **Memory**: Ensure sufficient RAM for CV with large feature set

### Model Training
- **Parallelization**: Use n_jobs=-1 for multi-core training
- **Early Stopping**: Implement for XGBoost/LightGBM to prevent overfitting
- **Checkpointing**: Save intermediate models during training

### Deployment
- **Feature Consistency**: Ensure production features match training
- **Versioning**: Track feature engineering pipeline versions
- **Monitoring**: Alert on feature drift or data quality issues

---

## 📚 References & Resources

### Libraries
- **scikit-learn**: Core ML framework
- **XGBoost**: `pip install xgboost`
- **LightGBM**: `pip install lightgbm`
- **CatBoost**: `pip install catboost`
- **Optuna**: `pip install optuna` (hyperparameter tuning)

### Documentation
- Time Series CV: [sklearn TimeSeriesSplit](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit.html)
- Feature Engineering: [featuretools](https://www.featuretools.com/)
- Ensemble Methods: [sklearn ensemble](https://scikit-learn.org/stable/modules/ensemble.html)

### Papers
- "XGBoost: A Scalable Tree Boosting System" (Chen & Guestrin, 2016)
- "LightGBM: A Highly Efficient Gradient Boosting Decision Tree" (Ke et al., 2017)
- "Forecasting at Scale" (Taylor & Letham, 2018) - Prophet methodology

---

## 🚦 Next Steps

### Immediate Actions
1. Review and prioritize enhancements based on business needs
2. Set up experiment tracking (MLflow or Weights & Biases)
3. Create baseline metrics for comparison
4. Begin Phase 1 implementation

### Long-term Considerations
- A/B testing framework for model comparison
- Automated retraining pipeline
- Real-time monitoring dashboard
- Feedback loop from actual vs predicted

---

**Document Owner**: Data Science Team  
**Last Updated**: February 7, 2026  
**Next Review**: After Phase 1 completion
