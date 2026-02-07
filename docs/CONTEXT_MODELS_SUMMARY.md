# Context-Specific Models Experiment - Executive Summary

**Date**: February 7, 2026  
**Experiment**: Testing Dataset Segmentation Approaches for Demand Prediction  
**Status**: ❌ **COMPLETED - NEGATIVE RESULTS**

---

## 🎯 Objective

Evaluate whether splitting the dataset into smaller segments and training separate models for each segment would improve prediction quality compared to a single unified model.

---

## 🧪 Approaches Tested

### 1. Intuitive Categorization
Split based on domain knowledge about time patterns:
- **weekday_breakfast** (7-10am Mon-Fri)
- **weekday_lunch** (11am-2pm Mon-Fri)
- **weekday_dinner** (6-9pm Mon-Fri)
- **weekday_other** (all other weekday hours)
- **weekend_day** (6am-10pm Sat-Sun)
- **weekend_night** (10pm-6am Sat-Sun)

**Rationale**: Different times of day have different demand patterns

### 2. K-Means Clustering
Automated data-driven segmentation using 16 features:
- Time features: hour, day_of_week, month, time-of-day flags
- Venue features: place_id, type_id, rating, waiting_time
- Weather features: temperature, humidity, weather_severity
- History features: rolling_7d_avg_items, prev_week_items

**Rationale**: Let the algorithm discover natural groupings in the data

---

## 📊 Results Summary

| Approach | MAE (Item Count) | R² | Change vs Baseline |
|----------|------------------|----|--------------------|
| **Baseline (Single Model)** | **0.3706** | **0.9861** | **0.00%** ✓ |
| Intuitive Categories | 0.4588 | 0.9755 | **-23.80%** ↓ |
| K-Means Clustering | 0.4308 | 0.9800 | **-16.24%** ↓ |

### Interpretation
- **Both approaches performed WORSE than baseline**
- Intuitive categories: 23.8% increase in MAE (worse)
- K-Means clustering: 16.2% increase in MAE (worse)
- Baseline remains the best model

---

## 🔍 Root Cause Analysis

### Why Did Context-Specific Models Fail?

#### 1. Sample Size Reduction ⚠️
| Context | Training Samples | % of Total |
|---------|-----------------|------------|
| Baseline | 65,608 | 100% |
| weekday_lunch | 15,133 | 23% |
| weekday_other | 17,629 | 27% |
| **weekend_night** | **648** | **1%** ← Critical issue |

**Impact**: 
- `weekend_night` had only 648 training samples
- This context showed MAE=1.41 (vs 0.37 baseline) - **4x worse!**
- Tree-based models need substantial data (typically 10,000+ samples)

#### 2. Feature Redundancy 🔄
The baseline model already has context features:
- `hour`, `day_of_week`, `month`
- `is_weekend`, `is_breakfast_rush`, `is_lunch_rush`, `is_dinner_rush`

**Impact**: Single unified model can already learn context-specific patterns internally without splitting the data.

#### 3. Distribution Misalignment 📉
K-Means clustering issues:
- Trained 6 clusters, but only 4 appeared in test set
- Clusters 3 & 5 had **zero test samples**
- Models trained on those clusters were never used
- Wasted computation and potential overfitting

#### 4. Loss of Shared Learning 🧠
Separate models cannot share knowledge:
- A venue's popularity patterns might span multiple contexts
- Weather impact on demand might be consistent across times
- Campaign effectiveness might follow similar patterns

**Impact**: Each context model "reinvents the wheel" instead of leveraging cross-context patterns.

---

## 📈 Detailed Performance Breakdown

### Intuitive Categories - By Context

| Context | MAE | R² | Test Samples | Performance |
|---------|-----|----|--------------| ------------|
| weekday_dinner | 0.3609 | 0.9838 | 2,527 | ✓ Comparable |
| weekday_lunch | 0.3945 | 0.9787 | 4,206 | ✓ Acceptable |
| weekday_breakfast | 0.4121 | 0.9690 | 1,506 | ⚠️ Below baseline |
| weekday_other | 0.4695 | 0.9810 | 4,136 | ⚠️ Below baseline |
| weekend_day | 0.5451 | 0.9731 | 3,801 | ⚠️ Poor |
| **weekend_night** | **1.4115** | **0.8659** | **227** | **❌ Catastrophic** |

**Key Finding**: The tiny `weekend_night` segment dragged down overall performance.

### K-Means Clustering - By Cluster

| Cluster | Description | MAE | R² | Test Samples |
|---------|-------------|-----|----|--------------| 
| 0 | Morning rush | 0.3679 | 0.9630 | 777 |
| 1 | Afternoon (largest) | 0.3993 | 0.9837 | 9,464 |
| 2 | Evening/dinner | 0.3527 | 0.9860 | 3,047 |
| 4 | Weekend lunch | 0.6186 | 0.9715 | 3,115 |
| 3 | Early afternoon | N/A | N/A | **0** ← Missing! |
| 5 | Low demand | N/A | N/A | **0** ← Missing! |

**Key Finding**: Better than intuitive approach but still worse than baseline. Cluster imbalance and missing test clusters problematic.

---

## 💡 Key Insights & Lessons Learned

### ✅ What We Learned

1. **More Data Usually Beats Clever Segmentation**
   - For tree-based models, a larger unified dataset is often better
   - Splitting reduces sample size → worse generalization
   
2. **Context Features Work Better Than Context Models**
   - Including `hour`, `day_of_week`, `rush_hour_flags` as features
   - Let the model learn context interactions internally
   
3. **Validate Enhancement Plans**
   - Enhancement document suggested 8-12% improvement
   - Reality: 16-24% degradation
   - Always empirically test assumptions
   
4. **Small Segments Are Dangerous**
   - 648 samples insufficient for robust tree ensemble
   - Rule of thumb: >10,000 samples per model for production use
   
5. **Baseline Was Already Strong**
   - MAE=0.3706 is excellent performance
   - R²=0.9861 indicates model captures patterns well
   - Sometimes the simple approach is best

### ❌ When Context-Specific Models Don't Work

Our situation had all the warning signs:
- ✗ Unified model already has context features
- ✗ Splitting creates small sample sizes (<10K)
- ✗ No fundamental process changes between contexts
- ✗ Cross-context patterns are important

### ✅ When Context-Specific Models MIGHT Work

Future scenarios to consider:
- ✓ Fundamentally different processes (e.g., B2C vs B2B)
- ✓ Clear regime changes (e.g., pre/during/post major event)
- ✓ Sufficient data per context (>10,000 samples minimum)
- ✓ Context boundaries are clear and stable
- ✓ No cross-context learning needed

---

## 🎯 Recommendations

### ✅ **KEEP: Baseline Single Model**
- **Best performance**: MAE=0.3706, R²=0.9861
- Already captures context through features
- Benefits from full 65,608 training samples
- **Action**: Continue using current model

### ✅ **NEXT: Focus on Alternative Enhancements**

Based on [demand_enhancement.md](demand_enhancement.md), prioritize:

**Phase 2 Enhancements** (Expected: 20-35% improvement):
1. **Venue-Specific Historical Features** (High Priority)
   ```python
   df['venue_hour_avg'] = df.groupby(['place_id', 'hour'])['item_count'].transform('mean')
   df['venue_dow_avg'] = df.groupby(['place_id', 'day_of_week'])['item_count'].transform('mean')
   df['venue_volatility'] = df.groupby('place_id')['item_count'].transform('std')
   ```
   - Adds context awareness WITHOUT splitting data
   - Expected: 10-15% MAE improvement

2. **Weather Interaction Features**
   ```python
   df['weekend_good_weather'] = df['is_weekend'] * df['good_weather']
   df['rush_bad_weather'] = (df['is_lunch_rush'] | df['is_dinner_rush']) * df['bad_weather_score']
   ```
   - Expected: 5-10% MAE improvement

3. **Model Ensemble** (RF + XGBoost + LightGBM + CatBoost)
   - Voting ensemble with optimized weights
   - Expected: 5-10% MAE improvement

### ❌ **ABANDON: Pure Context-Specific Models**
- Not effective for this use case
- May revisit with hierarchical approach if other enhancements plateau

---

## 📁 Deliverables

All files saved to `data/models/`:

| File | Description |
|------|-------------|
| `context_specific_comparison.csv` | Numerical comparison of all approaches |
| `context_models_comparison.png` | Visualization of MAE, R², improvements |
| `context_models_detailed.png` | Per-context and per-cluster performance |
| `src/context_specific_models.py` | Complete implementation code |
| `docs/CONTEXT_MODELS_ANALYSIS.md` | Detailed technical analysis |
| `docs/CONTEXT_MODELS_SUMMARY.md` | This executive summary |

---

## 🚀 Next Steps

### Immediate Actions (This Week)
1. ✅ Archive context-specific model experiment
2. ⏭️ Implement venue-specific historical features (Phase 2)
3. ⏭️ Implement weather interaction features (Phase 2)
4. ⏭️ Build model ensemble (Phase 2)

### Medium-Term (Next 2 Weeks)  
1. Evaluate Phase 2 improvements
2. Consider hyperparameter optimization (Optuna)
3. Implement quantile regression for uncertainty estimates

### Long-Term Considerations
- A/B test new features in production
- Set up automated retraining pipeline
- Real-time monitoring dashboard

---

## 📚 References

1. **Original Enhancement Plan**: [demand_enhancement.md](demand_enhancement.md)
2. **Detailed Analysis**: [CONTEXT_MODELS_ANALYSIS.md](CONTEXT_MODELS_ANALYSIS.md)
3. **Implementation Code**: [src/context_specific_models.py](../src/context_specific_models.py)

---

## 🏁 Conclusion

While context-specific models are a popular technique in ML literature, they **did not work for our use case**. The experiment provided valuable insights:

- ✅ **Validated**: Baseline model is strong (MAE=0.3706)
- ✅ **Learned**: Feature engineering > model segmentation for our data
- ✅ **Saved time**: Won't pursue this direction further
- ✅ **Next steps clear**: Focus on Phase 2 enhancements instead

**Impact**: This negative result saved us from implementing a worse model in production. Now we can confidently pursue more promising enhancement strategies.

---

**Experiment Owner**: Data Science Team  
**Experiment Status**: ❌ Completed - Negative Results  
**Decision**: Continue with baseline single model  
**Next Experiment**: Venue-specific historical features (Phase 2)

---

*"Negative results are still results. We learned what doesn't work, which is just as valuable as learning what does."*
