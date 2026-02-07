# Error Analysis Tools - Quick Reference

## Scripts Created

### 1. `src/error_analysis.py`
Comprehensive error analysis script that:
- Analyzes model errors across multiple dimensions
- Identifies patterns and problem areas
- Generates actionable recommendations
- Saves detailed results to CSV and JSON

**Usage**: 
```powershell
python src/error_analysis.py
```

**Outputs**:
- `data/models/error_analysis_details.csv` - Row-level predictions and errors
- `data/models/error_analysis_summary.json` - Structured summary metrics

### 2. `src/visualize_errors.py`
Creates comprehensive visualizations of model errors

**Usage**: 
```powershell
python src/visualize_errors.py
```

**Outputs**:
- `data/models/error_analysis_plots.png` - 9-panel diagnostic dashboard
- `data/models/error_analysis_extended.png` - Restaurant-specific analysis

## Key Findings Summary

### 🚨 Critical Issues
1. **Severe under-prediction bias**: -4.47 items on average
2. **Poor high-demand performance**: MAE = 32.3 for demand > 25 items
3. **High temporal variance**: 2.27 std across hours
4. **Weekend performance gap**: 26% worse than weekdays

### 📊 Performance by Segment

| Demand Level | MAE | Bias | Quality |
|-------------|-----|------|---------|
| Very Low (0-3) | 1.69 | +1.69 | ✅ Good |
| Low (3-7) | 1.26 | -1.14 | ✅ Good |
| Medium (7-15) | 6.53 | -6.53 | ⚠️ Fair |
| High (15-25) | 15.25 | -15.25 | ❌ Poor |
| Very High (25+) | 32.33 | -32.33 | ❌ Poor |

### 💡 Top 5 Recommendations

1. **[HIGH]** Implement demand-stratified modeling (separate models for high/low demand)
2. **[HIGH]** Address under-prediction bias with calibration or asymmetric loss
3. **[HIGH]** Add peak-period features (meal times, hour-day interactions)
4. **[MEDIUM]** Enhance restaurant-specific features (cuisine, capacity, volatility)
5. **[MEDIUM]** Try alternative models (LightGBM, Quantile Regression)

## Quick Commands

### Run Full Analysis Pipeline
```powershell
# 1. Error analysis
python src/error_analysis.py

# 2. Generate visualizations  
python src/visualize_errors.py

# 3. View report
code docs/ERROR_ANALYSIS_REPORT.md
```

### View Results
```powershell
# Open visualizations
start data/models/error_analysis_plots.png
start data/models/error_analysis_extended.png

# View detailed errors
code data/models/error_analysis_details.csv

# Check summary
code data/models/error_analysis_summary.json
```

## Files Generated

| File | Description | Size |
|------|-------------|------|
| `error_analysis_details.csv` | 16,403 rows of predictions + errors | ~2MB |
| `error_analysis_summary.json` | Structured metrics & recommendations | ~10KB |
| `error_analysis_plots.png` | 9-panel diagnostic dashboard | ~500KB |
| `error_analysis_extended.png` | Restaurant & segment analysis | ~400KB |
| `ERROR_ANALYSIS_REPORT.md` | Comprehensive written report | ~20KB |

## Next Steps

1. ✅ **Review** [ERROR_ANALYSIS_REPORT.md](ERROR_ANALYSIS_REPORT.md)
2. ✅ **Prioritize** recommendations with stakeholders  
3. ⏭️ **Implement** top 3 high-priority fixes
4. ⏭️ **Re-run analysis** after improvements
5. ⏭️ **Monitor** production metrics

## Common Analysis Tasks

### Find worst predictions
```python
import pandas as pd
df = pd.read_csv('data/models/error_analysis_details.csv')
worst = df.nlargest(20, 'abs_error')
print(worst[['hour', 'day_of_week', 'place_id', 'y_true', 'y_pred', 'abs_error']])
```

### Analyze specific restaurant
```python
place_id = 686203  # Replace with your restaurant
place_errors = df[df['place_id'] == place_id]
print(f"Restaurant {place_id} - MAE: {place_errors['abs_error'].mean():.2f}")
```

### Check specific time period
```python
dinner_rush = df[(df['hour'] >= 17) & (df['hour'] <= 19)]
print(f"Dinner rush (5-7pm) MAE: {dinner_rush['abs_error'].mean():.2f}")
```

## Updating Analysis

After model improvements, re-run the analysis:

```powershell
# 1. Train new model
python src/train_model.py

# 2. Re-run error analysis
python src/error_analysis.py

# 3. Regenerate visualizations
python src/visualize_errors.py

# 4. Compare with baseline
python -c "
import pandas as pd
import json

with open('data/models/error_analysis_summary.json') as f:
    metrics = json.load(f)
    
print(f\"Current MAE: {metrics['Overall Metrics']['MAE']:.2f}\")
print(f\"Target MAE: < 3.50 (36% improvement needed)\")
"
```

---

**Last Updated**: February 7, 2026
