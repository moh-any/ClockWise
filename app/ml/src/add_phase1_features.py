"""
Script to add Phase 1 enhancement features to existing dataset
without re-fetching weather data.
"""
import numpy as np
import pandas as pd

print("="*80)
print("ADDING PHASE 1 ENHANCEMENT FEATURES")
print("="*80)

# Load existing dataset
print("\nLoading existing dataset...")
df = pd.read_csv('data/processed/combined_features.csv')
print(f"Loaded: {df.shape[0]:,} rows × {df.shape[1]} columns")

# Ensure datetime is parsed
df['datetime'] = pd.to_datetime(df['datetime'])

# ============================================================================
# 1. CYCLICAL TIME FEATURES
# ============================================================================
print("\n1. Adding cyclical time features...")

# Hour cyclical encoding (0-23)
df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)

# Day of week cyclical encoding (0-6)
df['day_of_week_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
df['day_of_week_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)

# Month cyclical encoding (1-12)
df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)

print("   ✓ Added: hour_sin/cos, day_of_week_sin/cos, month_sin/cos")

# ============================================================================
# 2. TIME CONTEXT INDICATORS
# ============================================================================
print("\n2. Adding time context indicators...")

# Rush hour periods
df['is_breakfast_rush'] = ((df['hour'] >= 7) & (df['hour'] <= 9)).astype(int)
df['is_lunch_rush'] = ((df['hour'] >= 11) & (df['hour'] <= 13)).astype(int)
df['is_dinner_rush'] = ((df['hour'] >= 18) & (df['hour'] <= 20)).astype(int)
df['is_late_night'] = ((df['hour'] >= 22) | (df['hour'] <= 2)).astype(int)

# Weekend indicator
df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)

# Month start/end indicators
df['is_month_start'] = (df['datetime'].dt.day <= 5).astype(int)
df['is_month_end'] = (df['datetime'].dt.day >= 25).astype(int)

print("   ✓ Added: breakfast/lunch/dinner rush, late night, weekend, month start/end")

# ============================================================================
# 3. ENHANCED LAG & ROLLING FEATURES
# ============================================================================
print("\n3. Adding enhanced lag and rolling features...")

# Sort by place and time for lag calculations
df = df.sort_values(['place_id', 'datetime'])

# Same-time historical lags (if not already present)
if 'lag_same_hour_last_week' not in df.columns:
    df['lag_same_hour_last_week'] = df.groupby('place_id')['item_count'].shift(168)
    df['lag_same_hour_2_weeks'] = df.groupby('place_id')['item_count'].shift(336)
    print("   ✓ Added: lag_same_hour_last_week, lag_same_hour_2_weeks")

# Additional rolling windows
for window_days in [3, 14, 30]:
    col_name = f'rolling_{window_days}d_avg_items'
    if col_name not in df.columns:
        window_hours = window_days * 24
        df[col_name] = df.groupby('place_id')['item_count'].transform(
            lambda x: x.rolling(window=window_hours, min_periods=1).mean()
        )
        print(f"   ✓ Added: {col_name}")

# Volatility feature
if 'rolling_7d_std_items' not in df.columns:
    df['rolling_7d_std_items'] = df.groupby('place_id')['item_count'].transform(
        lambda x: x.rolling(window=168, min_periods=1).std()
    )
    print("   ✓ Added: rolling_7d_std_items")

# Trend feature
if 'demand_trend_7d' not in df.columns:
    def calculate_trend(series):
        if len(series) < 2:
            return 0
        try:
            return np.polyfit(range(len(series)), series, 1)[0]
        except:
            return 0
    
    df['demand_trend_7d'] = df.groupby('place_id')['item_count'].transform(
        lambda x: x.rolling(window=168, min_periods=2).apply(calculate_trend, raw=True)
    )
    print("   ✓ Added: demand_trend_7d")

# Fill NaN values
lag_cols = [
    'lag_same_hour_last_week', 'lag_same_hour_2_weeks',
    'rolling_7d_std_items', 'demand_trend_7d'
]
for col in lag_cols:
    if col in df.columns:
        df[col] = df[col].fillna(0)

# ============================================================================
# SAVE ENHANCED DATASET
# ============================================================================
print("\n" + "="*80)
print(f"Final dataset: {df.shape[0]:,} rows × {df.shape[1]} columns")
print(f"Feature count: {df.shape[1]}")

# List new Phase 1 features
new_features = [c for c in df.columns if any(x in c for x in [
    '_sin', '_cos', 'rush', 'is_weekend', 'is_month',
    'rolling_3d', 'rolling_14d', 'rolling_30d', '_std_', 'trend',
    'lag_same_hour'
])]

print(f"\nPhase 1 new features ({len(new_features)}):")
for feat in sorted(new_features):
    print(f"  - {feat}")

# Save
df.to_csv('data/processed/combined_features.csv', index=False)
print("\n✅ Enhanced dataset saved to: data/processed/combined_features.csv")
print("="*80)
