# Models Directory

## Production Model

**Current Version**: v6_optimized  
**Last Updated**: February 7, 2026

### Files
| File | Description |
|------|-------------|
| `rf_model.joblib` | Production CatBoost model (item_count + order_count) |
| `rf_model_metadata.json` | Model configuration and metrics |
| `prediction_interval_models.joblib` | Quantile models for prediction intervals |

### Performance
| Metric | item_count | order_count |
|--------|-----------|-------------|
| MAE | 3.32 | 1.71 |
| R² | 0.69 | 0.76 |
| Bias | +0.23 | +0.04 |

### Quick Usage
```python
import joblib
models = joblib.load('data/models/rf_model.joblib')
item_pred = models[0].predict(X)  # item_count
order_pred = models[1].predict(X)  # order_count
```

### Prediction Intervals
```python
from src.prediction_utils import predict_with_intervals
predictions = predict_with_intervals(X)
# Use predictions['item_count']['upper'] for safe staffing
```

**Full Documentation**: [docs/DEMAND_PREDICTION_MODEL.md](../../docs/DEMAND_PREDICTION_MODEL.md)

---

## Archive

Historical models preserved in `archive/`:
- `rf_model_asymmetric_v1.joblib` - v5.0 (original quantile loss)
- `rf_model_v5_backup.joblib` - Pre-optimization backup
- `rf_model_phase4_*.joblib` - Phase 4 development

## Analysis

Error analysis outputs in `analysis/`:
- `error_analysis_plots.png` - Diagnostic visualizations
- `calibration_results.png` - Calibration curves

---

*See comprehensive documentation for full details*
