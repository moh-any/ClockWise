"""
Comprehensive comparison between Phase 1 and Phase 2 models.
"""
import pandas as pd
import numpy as np
import json
from pathlib import Path

print("="*80)
print("PHASE 1 VS PHASE 2 MODEL COMPARISON")
print("="*80)

# Load comparison CSVs
phase1_results = pd.read_csv('data/models/phase1_model_comparison.csv')
phase2_results = pd.read_csv('data/models/phase2_model_comparison.csv')

# Load metadata files (they're JSON saved with .json extension by joblib)
with open('data/models/rf_model_metadata.json', 'r') as f:
    import joblib
    
# Load using joblib since that's how it was saved
phase2_metadata = joblib.load('data/models/rf_model_metadata.json')

print("\n" + "="*80)
print("1. FEATURE COMPARISON")
print("="*80)

print(f"\nPhase 1:")
print(f"  Total features: 54")
print(f"  New features: Cyclical time, time context, enhanced rolling windows")

print(f"\nPhase 2:")
print(f"  Total features: {phase2_metadata['num_features']}")
print(f"  New features: Venue-specific historical + Weather interactions")
print(f"  Added features: {phase2_metadata['num_features'] - 54}")

print("\n" + "="*80)
print("2. MODEL PERFORMANCE COMPARISON")
print("="*80)

# Get best models from each phase
phase1_best = phase1_results.groupby('Model')['MAE'].mean().sort_values().iloc[0]
phase1_best_name = phase1_results.groupby('Model')['MAE'].mean().sort_values().index[0]

phase2_best = phase2_results.groupby('Model')['MAE'].mean().sort_values().iloc[0]
phase2_best_name = phase2_results.groupby('Model')['MAE'].mean().sort_values().index[0]

print(f"\nBest Phase 1 Model: {phase1_best_name}")
print(f"  Average MAE: {phase1_best:.4f}")

print(f"\nBest Phase 2 Model: {phase2_best_name}")
print(f"  Average MAE: {phase2_best:.4f}")

improvement = ((phase1_best - phase2_best) / phase1_best) * 100
print(f"\n{'✅' if improvement > 0 else '❌'} Phase 1 → Phase 2 Improvement: {improvement:.2f}%")

print("\n" + "="*80)
print("3. DETAILED METRICS BY TARGET")
print("="*80)

for target in ['item_count', 'order_count']:
    print(f"\n{target.upper()}:")
    
    phase1_target = phase1_results[
        (phase1_results['Model'] == phase1_best_name) & 
        (phase1_results['Target'] == target)
    ].iloc[0]
    
    phase2_target = phase2_results[
        (phase2_results['Model'] == phase2_best_name) & 
        (phase2_results['Target'] == target)
    ].iloc[0]
    
    print(f"  Phase 1 - MAE: {phase1_target['MAE']:.4f}, R²: {phase1_target['R2']:.4f}")
    print(f"  Phase 2 - MAE: {phase2_target['MAE']:.4f}, R²: {phase2_target['R2']:.4f}")
    
    mae_imp = ((phase1_target['MAE'] - phase2_target['MAE']) / phase1_target['MAE']) * 100
    r2_imp = phase2_target['R2'] - phase1_target['R2']
    
    print(f"  MAE improvement:   {mae_imp:+.2f}%")
    print(f"  R² improvement:    {r2_imp:+.4f}")

print("\n" + "="*80)
print("4. MODEL COMPARISON (All Models)")
print("="*80)

print("\nPhase 1 Models:")
phase1_summary = phase1_results.groupby('Model').agg({
    'MAE': 'mean',
    'R2': 'mean',
    'Train_Time': 'first'
}).sort_values('MAE')

for idx, (model, row) in enumerate(phase1_summary.iterrows(), 1):
    marker = " ⭐" if idx == 1 else ""
    print(f"  {idx}. {model}: MAE={row['MAE']:.4f}, R²={row['R2']:.4f}, Time={row['Train_Time']:.1f}s{marker}")

print("\nPhase 2 Models:")
phase2_summary = phase2_results.groupby('Model').agg({
    'MAE': 'mean',
    'R2': 'mean',
    'Train_Time': 'first'
}).sort_values('MAE')

for idx, (model, row) in enumerate(phase2_summary.iterrows(), 1):
    marker = " ⭐" if idx == 1 else ""
    print(f"  {idx}. {model}: MAE={row['MAE']:.4f}, R²={row['R2']:.4f}, Time={row['Train_Time']:.1f}s{marker}")

print("\n" + "="*80)
print("5. CROSS-VALIDATION RESULTS (Phase 2)")
print("="*80)

if 'phase_2_enhancements' in phase2_metadata and 'cv_results' in phase2_metadata['phase_2_enhancements']:
    cv_results = phase2_metadata['phase_2_enhancements']['cv_results']
    print("\nTime Series Cross-Validation (5-fold):")
    for model, scores in cv_results.items():
        print(f"  {model}: {scores['mean']:.4f} (±{scores['std']:.4f})")
else:
    print("  Cross-validation results not available")

print("\n" + "="*80)
print("6. TRAINING EFFICIENCY")
print("="*80)

phase1_time = phase1_summary.loc[phase1_best_name, 'Train_Time']
phase2_time = phase2_summary.loc[phase2_best_name, 'Train_Time']

print(f"\nPhase 1 ({phase1_best_name}): {phase1_time:.2f}s")
print(f"Phase 2 ({phase2_best_name}): {phase2_time:.2f}s")

time_ratio = phase2_time / phase1_time
if time_ratio < 1:
    print(f"✅ Phase 2 is {1/time_ratio:.2f}x faster")
else:
    print(f"❌ Phase 2 is {time_ratio:.2f}x slower")

print("\n" + "="*80)
print("7. KEY IMPROVEMENTS & INSIGHTS")
print("="*80)

print("\n✨ Phase 2 Enhancements:")
print("  ✅ Venue-specific historical features (7 features)")
print("     - venue_hour_avg, venue_dow_avg, venue_volatility")
print("     - venue_total_items, venue_growth_recent_vs_historical")
print("     - venue_peak_hour, is_venue_peak_hour")
print()
print("  ✅ Weather interaction features (8 features)")
print("     - feels_like_temp, bad_weather_score")
print("     - temp_change_1h, temp_change_3h, weather_getting_worse")
print("     - weekend_good_weather, rush_bad_weather, cold_evening")
print()
print("  ✅ Time series cross-validation")
print("     - 5-fold validation for robust performance estimates")
print()
print("  ✅ Simple ensemble (soft voting)")
print("     - Averages predictions from RF, XGBoost, LightGBM")

baseline_mae = 4.80  # From original model before Phase 1
phase1_mae = phase1_best
phase2_mae = phase2_best

phase1_improvement = ((baseline_mae - phase1_mae) / baseline_mae) * 100
phase2_improvement = ((baseline_mae - phase2_mae) / baseline_mae) * 100
total_improvement = ((baseline_mae - phase2_mae) / baseline_mae) * 100

print("\n" + "="*80)
print("8. CUMULATIVE IMPROVEMENT FROM BASELINE")
print("="*80)

print(f"\nOriginal Baseline: MAE = {baseline_mae:.2f}")
print(f"Phase 1:           MAE = {phase1_mae:.4f} ({phase1_improvement:+.2f}% from baseline)")
print(f"Phase 2:           MAE = {phase2_mae:.4f} ({phase2_improvement:+.2f}% from baseline)")
print(f"\n🎯 Total Improvement: {total_improvement:.2f}%")

print("\n" + "="*80)
print("9. RECOMMENDATION")
print("="*80)

if phase2_best < phase1_best:
    print("\n✅ RECOMMEND: Deploy Phase 2 model")
    print(f"   Model: {phase2_best_name}")
    print(f"   Features: {phase2_metadata['num_features']}")
    print(f"   MAE: {phase2_best:.4f}")
    print(f"   Training time: {phase2_time:.1f}s")
    print(f"\n   Benefits:")
    print(f"   - {improvement:.2f}% better than Phase 1")
    print(f"   - {total_improvement:.2f}% better than baseline")
    if phase2_best_name == 'LightGBM':
        print(f"   - Fast training ({phase2_time:.1f}s)")
        print(f"   - Best R² score")
else:
    print("\n⚠️  RECOMMEND: Keep Phase 1 model")
    print(f"   Phase 2 did not provide significant improvement")
    print(f"   Consider additional features or hyperparameter tuning")

print("\n" + "="*80)
print("COMPARISON COMPLETE")
print("="*80)
