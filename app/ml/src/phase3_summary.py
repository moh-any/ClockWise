"""Phase 3 Summary Generator"""
import pandas as pd
import joblib

# Load Phase 3 comparison
phase3 = pd.read_csv('data/models/phase3_model_comparison.csv')

# Calculate average MAE per model
avg_mae = phase3.groupby('Model')['MAE'].mean().sort_values()

print("="*80)
print("PHASE 3 TRAINING COMPLETE (CATBOOST + OPTUNA)")
print("="*80)

print("\n📊 Model Performance Rankings:")
for rank, (model_name, mae) in enumerate(avg_mae.items(), 1):
    marker = " ⭐ BEST" if rank == 1 else ""
    print(f"  {rank}. {model_name}: MAE={mae:.4f}{marker}")

# Load metadata  
try:
    metadata = joblib.load('data/models/rf_model_metadata.json')
    print(f"\n✅ Saved Model: {metadata.get('model_type', 'Unknown')}")
    print(f"   Version: {metadata.get('version', 'Unknown')}")
    print(f"   Features: {metadata.get('num_features', 'Unknown')}")
    
    if 'phase_3_enhancements' in metadata:
        phase3_info = metadata['phase_3_enhancements']
        print(f"\n🚀 Phase 3 Enhancements:")
        print(f"   ✅ CatBoost: {phase3_info.get('catboost_model', False)}")
        print(f"   ✅ Optuna Optimization: {phase3_info.get('optuna_optimization', False)}")
        if phase3_info.get('optimized_lgbm_params'):
            print(f"   ✅ Optimized LightGBM hyperparameters")
            
except Exception as e:
    print(f"\n⚠️  Could not load metadata: {e}")

# Summary statistics
print("\n📈 Performance Summary:")
print(f"   Best Model: {avg_mae.index[0]}")
print(f"   Best MAE: {avg_mae.values[0]:.4f}")
print(f"   Models Compared: {len(avg_mae)}")

# Calculate improvement from Phase 2
phase2_best = 2.6894  # From previous runs
phase3_best = avg_mae.values[0]
improvement = ((phase2_best - phase3_best) / phase2_best) * 100

if improvement > 0:
    print(f"\n✅ Phase 2 → Phase 3 Improvement: {improvement:.2f}%")
else:
    print(f"\n⚠️  Phase 3 similar to Phase 2 (difference: {improvement:.2f}%)")

# Calculate cumulative improvement
baseline_mae = 4.80
cumulative_improvement = ((baseline_mae - phase3_best) / baseline_mae) * 100
print(f"\n🎯 Total Improvement from Baseline: {cumulative_improvement:.2f}%")
print(f"   Baseline MAE: {baseline_mae:.2f}")
print(f"   Phase 3 MAE: {phase3_best:.4f}")

print("\n" + "="*80)
print("✅ Phase 3 implementation complete!")
print("   - CatBoost added to ensemble")
print("   - Optuna hyperparameter optimization  for LightGBM")
print("   - 4 models + 1 ensemble compared")
print("="*80)
