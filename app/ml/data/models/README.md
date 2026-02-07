# Models Directory

## 📦 Production Model

**Current Version**: v5_asymmetric_loss  
**Last Updated**: February 7, 2026  
**Status**: ✅ Production Ready

### Files
- **rf_model.joblib** - Production CatBoost model (2 estimators for item_count + order_count)
- **rf_model_metadata.json** - Model configuration and performance metrics

### Performance Metrics
| Metric | Item Count | Order Count |
|--------|-----------|-------------|
| **MAE** | 3.26 | 2.14 |
| **RMSE** | 4.96 | - |
| **R²** | 0.65 | 0.53 |
| **Bias** | +0.12 | -0.05 |

### Key Features
- **Algorithm**: CatBoost with Quantile Loss (α=0.60)
- **Loss Function**: Quantile regression targeting 60th percentile
- **Sample Weighting**: Combined demand-based + temporal weighting
- **Bias Correction**: Near-zero bias (no systematic under/over-prediction)
- **Training Size**: 65,608 samples
- **Test Size**: 16,403 samples

### Improvements Over Previous Version
| Metric | Phase 4 (Old) | v5 (Current) | Improvement |
|--------|--------------|--------------|-------------|
| MAE | 5.44 | 3.26 | **40% better** |
| Bias | -4.47 | +0.12 | **97% reduction** |
| R² | -0.29 | 0.65 | **+0.94** |

## 📚 Directory Structure

```
data/models/
├── rf_model.joblib                    # Production model
├── rf_model_metadata.json             # Production metadata
│
├── archive/                           # Historical models
│   ├── rf_model_phase4_*.joblib      # Phase 4 model (outlier capping)
│   ├── rf_model_asymmetric_v1.joblib # Original asymmetric model
│   └── rf_model_calibrated.joblib    # Calibrated baseline model
│
├── analysis/                          # Error analysis results
│   ├── error_analysis_details.csv    # Row-level predictions
│   ├── error_analysis_summary.json   # Summary statistics
│   ├── error_analysis_plots.png      # 9-panel diagnostics
│   ├── error_analysis_extended.png   # Restaurant analysis
│   └── calibration_results.png       # Calibration curves
│
└── phase*_model_comparison.csv        # Phase comparison results
```

## 🔄 Model Evolution History

### Phase 1-3: Initial Development
- Random Forest baseline
- Feature engineering (weather, temporal)
- XGBoost experimentation

### Phase 4: Data Quality (Flawed)
- ❌ **Issue**: Applied outlier capping to targets
- **Claimed MAE**: 3.06 (on capped data)
- **Actual MAE**: 5.44 (on real data)
- **Problem**: Model couldn't handle real-world outliers

### Phase 5: Asymmetric Loss (Current) ✅
- ✅ **Solution**: Quantile loss without artificial capping
- **Handles outliers**: Trains on real uncapped data
- **Bias correction**: Targets 60th percentile to counter under-prediction
- **Real MAE**: 3.26 on actual data
- **Deployment**: February 7, 2026

## 🚀 Usage

### Load Production Model
```python
import joblib
import numpy as np

# Load model
model = joblib.load('data/models/rf_model.joblib')

# Make predictions (returns 2D array: [item_count, order_count])
if isinstance(model, list):
    predictions = np.column_stack([m.predict(X) for m in model])
else:
    predictions = model.predict(X)

item_count_pred = predictions[:, 0]
order_count_pred = predictions[:, 1]
```

### Load Metadata
```python
import json

with open('data/models/rf_model_metadata.json', 'r') as f:
    metadata = json.load(f)

print(f"Model version: {metadata['version']}")
print(f"Training date: {metadata['training_date']}")
print(f"MAE: {metadata['metrics']['item_count']['mae']:.2f}")
```

### Verify Model
```bash
python src/verify_production_model.py
```

## 📊 Analysis Tools

### Run Error Analysis
```bash
python src/error_analysis.py
```
Generates:
- Detailed error breakdown by demand level, time, restaurant
- Residual diagnostics
- Feature correlations with errors
- Actionable recommendations

### Visualize Errors
```bash
python src/visualize_errors.py
```
Creates:
- 9-panel diagnostic plots
- Restaurant-specific analysis
- Temporal error patterns

### Compare Models
```bash
python src/compare_models.py
```
Shows side-by-side comparison of baseline vs current model.

## 🔧 Maintenance

### Re-train Model
```bash
# Train new model with asymmetric loss
python src/train_with_asymmetric_loss.py

# This will create new files in archive/
# Review performance before deploying
```

### Deploy New Version
```bash
# 1. Backup current model
Copy-Item data/models/rf_model.joblib data/models/archive/rf_model_backup_$(Get-Date -Format 'yyyyMMdd').joblib

# 2. Deploy new model
Copy-Item data/models/rf_model_asymmetric.joblib data/models/rf_model.joblib -Force

# 3. Verify
python src/verify_production_model.py
```

## 📈 Performance Monitoring

Monitor these metrics in production:
- **MAE**: Should stay around 3.2-3.5
- **Bias**: Should stay near 0 (±0.5)
- **R²**: Should stay above 0.60
- **High-demand errors**: MAE < 6 for demand > 15

Warning signs:
- MAE increases above 4.0
- Bias exceeds ±1.0
- R² drops below 0.50
- Consistent under-prediction returns

## 🐛 Troubleshooting

### Model Not Loading
```python
# Check file integrity
import joblib
model = joblib.load('data/models/rf_model.joblib')
print(f"Model type: {type(model)}")
print(f"Is list: {isinstance(model, list)}")
```

### Poor Predictions
1. Check input data preprocessing matches training
2. Verify features are in same order
3. Check for missing value handling
4. Run error analysis to identify issues

### Bias Returns
If systematic bias reappears:
1. Check if data distribution has shifted
2. Consider retraining with updated data
3. Apply calibration as temporary fix:
   ```bash
   python src/fix_underprediction_bias.py
   ```

## 📚 Documentation

- **[ERROR_ANALYSIS_REPORT.md](../../docs/ERROR_ANALYSIS_REPORT.md)** - Comprehensive error analysis
- **[BIAS_FIX_RESULTS.md](../../docs/BIAS_FIX_RESULTS.md)** - Bias correction details
- **[ERROR_ANALYSIS_QUICKSTART.md](../../docs/ERROR_ANALYSIS_QUICKSTART.md)** - Quick reference

## 🔒 Archive Policy

- Keep last 3 production versions in archive/
- Keep all phase comparison results
- Analysis files are regenerated, safe to clean periodically
- Archive models older than 90 days can be compressed

## 📞 Contact

For model issues or retraining requests, see project README.

---

**Last Updated**: February 7, 2026  
**Model Version**: v5_asymmetric_loss  
**Status**: Production
