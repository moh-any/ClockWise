# Context-Specific Models Analysis

**Date**: February 7, 2026  
**Experiment**: Comparing Single Model vs Intuitive Categories vs K-Means Clustering

---

## Executive Summary

We evaluated two approaches for splitting the dataset into smaller segments with separate models:
1. **Intuitive Categorization**: Based on time context (weekday breakfast/lunch/dinner/other, weekend day/night)
2. **K-Means Clustering**: Automated segmentation using 16 features

**Result**: Both context-specific approaches performed **worse** than the baseline single model.

---

## Results Comparison

### Item Count Predictions

| Approach | MAE | R² | Improvement vs Baseline |
|----------|-----|----|-----------------------|
| **Baseline (Single Model)** | **0.3706** | **0.9861** | **0.00%** |
| Intuitive Categories | 0.4588 | 0.9755 | **-23.80%** ↓ |
| K-Means Clustering | 0.4308 | 0.9800 | **-16.24%** ↓ |

### Order Count Predictions

| Approach | MAE | R² | Improvement vs Baseline |
|----------|-----|----|-----------------------|
| **Baseline (Single Model)** | **0.1523** | **0.9933** | **0.00%** |
| Intuitive Categories | 0.2227 | 0.9776 | **-46.21%** ↓ |
| K-Means Clustering | 0.1934 | 0.9888 | **-27.00%** ↓ |

---

## Detailed Analysis

### 1. Context Distribution

#### Intuitive Categories
```
Training Set:
- weekday_lunch:      15,133 (23.1%)
- weekday_other:      17,629 (26.9%)
- weekend_day:        15,566 (23.7%)
- weekday_dinner:      8,616 (13.1%)
- weekday_breakfast:   8,016 (12.2%)
- weekend_night:         648 (1.0%)  ← Very small!

Test Set:
- weekday_lunch:       4,206 (25.6%)
- weekday_other:       4,136 (25.2%)
- weekend_day:         3,801 (23.2%)
- weekday_dinner:      2,527 (15.4%)
- weekday_breakfast:   1,506 (9.2%)
- weekend_night:         227 (1.4%)  ← Very small!
```

**Key Issues**:
- `weekend_night` has only **648 training samples** and **227 test samples**
- This category showed the worst performance: MAE=1.4115 (vs 0.3706 baseline)
- Small sample sizes lead to **poor generalization**

#### K-Means Clustering
```
Training Set:
- Cluster 1:          27,148 (41.4%)  ← Largest
- Cluster 3:          11,594 (17.7%)
- Cluster 2:          10,218 (15.6%)
- Cluster 4:          10,157 (15.5%)
- Cluster 0:           5,936 (9.0%)
- Cluster 5:             555 (0.8%)   ← Very small!

Test Set:
- Cluster 1:           9,464 (57.7%)
- Cluster 4:           3,115 (19.0%)
- Cluster 2:           3,047 (18.6%)
- Cluster 0:             777 (4.7%)
- Clusters 3 & 5:          0 (0.0%)   ← Missing!
```

**Key Issues**:
- Clusters 3 and 5 have **zero test samples**
- Imbalanced cluster sizes (555 vs 27,148)
- Model trained on Cluster 3 never used for prediction
- Distribution shift between train and test sets

### 2. Performance by Segment

#### Intuitive Categories Performance
| Context | MAE | R² | Test Samples |
|---------|-----|----|--------------| 
| weekday_dinner | 0.3609 | 0.9838 | 2,527 |
| weekday_lunch | 0.3945 | 0.9787 | 4,206 |
| weekday_breakfast | 0.4121 | 0.9690 | 1,506 |
| weekday_other | 0.4695 | 0.9810 | 4,136 |
| weekend_day | 0.5451 | 0.9731 | 3,801 |
| **weekend_night** | **1.4115** | **0.8659** | **227** ↓ |

- 5 out of 6 contexts perform comparably (MAE 0.36-0.55)
- `weekend_night` is a catastrophic outlier due to insufficient data

#### K-Means Clustering Performance
| Cluster | MAE | R² | Test Samples |
|---------|-----|----|--------------| 
| 2 | 0.3527 | 0.9860 | 3,047 |
| 0 | 0.3679 | 0.9630 | 777 |
| 1 | 0.3993 | 0.9837 | 9,464 |
| 4 | 0.6186 | 0.9715 | 3,115 |
| 3 | N/A | N/A | **0** ← No test data! |
| 5 | N/A | N/A | **0** ← No test data! |

- Cluster 4 performs worse (MAE=0.6186)
- Clusters 3 & 5 trained but never used

---

## Why Did Context-Specific Models Fail?

### 1. **Sample Size Reduction**
- **Problem**: Splitting reduces training data per model
- **Baseline**: 65,608 samples for single model
- **Contexts**: 648-17,629 samples per model (mean: ~10,935)
- **Impact**: Smaller datasets → worse generalization, especially for tree-based models

### 2. **Feature Redundancy**
- **Problem**: The baseline model already has context features
- **Existing Features**: `hour`, `day_of_week`, `is_weekend`, `is_breakfast_rush`, `is_lunch_rush`, `is_dinner_rush`
- **Impact**: Single model can learn context-specific patterns naturally
- Splitting into contexts doesn't provide new information

### 3. **Distribution Misalignment**
- **Problem**: Test distribution differs from training (especially K-Means)
- **K-Means Issue**: Clusters 3 & 5 absent from test set
- **Impact**: Some trained models are wasted; cluster assignments may be unstable

### 4. **Loss of Cross-Context Learning**
- **Problem**: Separate models can't learn shared patterns
- **Example**: A venue's popularity might have patterns that span multiple contexts
- **Impact**: Each context model reinvents the wheel instead of sharing knowledge

### 5. **Hyperparameter Mismatch**
- **Problem**: Same hyperparameters used for all models
- **Reality**: Smaller datasets need different tuning (less depth, more regularization)
- **Impact**: Models may overfit their smaller training sets

---

## Cluster Characteristics (K-Means)

| Cluster | Avg Hour | Avg Day of Week | Avg Demand | Samples | Interpretation |
|---------|----------|-----------------|------------|---------|----------------|
| 0 | 8.3 | 2.8 (Wed) | 10.2 | 5,936 | **Morning rush** |
| 1 | 14.1 | 2.2 (Tue) | 8.4 | 27,148 | **Afternoon (largest)** |
| 2 | 18.6 | 3.0 (Wed) | 7.2 | 10,218 | **Evening/dinner** |
| 3 | 13.5 | 2.7 (Wed) | 7.5 | 11,594 | **Early afternoon** |
| 4 | 13.8 | 5.4 (Sat) | 10.0 | 10,157 | **Weekend lunch** |
| 5 | 14.2 | 2.9 (Wed) | 2.9 | 555 | **Low demand venues** |

**Insight**: K-Means discovered similar patterns to intuitive categories but with odd splits (Clusters 1 & 3 overlap)

---

## When Do Context-Specific Models Work?

Based on this experiment and ML literature:

### ✅ Use Context-Specific Models When:
1. **Fundamentally Different Processes**: 
   - Example: B2C vs B2B sales have completely different drivers
   - Our case: Same food delivery process across all times
   
2. **Clear Regime Changes**:
   - Example: Pre-pandemic vs during-pandemic vs post-pandemic
   - Our case: No such regime changes identified
   
3. **Sufficient Data Per Context**:
   - Rule of thumb: >10,000 samples per model for tree ensembles
   - Our case: `weekend_night` has only 648 samples
   
4. **Non-Linear Context Interactions**:
   - When context interacts with features in complex ways
   - Our case: Features like `is_weekend`, `hour` already capture this

### ❌ Avoid Context-Specific Models When:
1. **Unified Model Already Has Context Features** ← Our situation
2. **Splitting Creates Small Samples** ← Our situation
3. **Context Boundaries Are Unclear**
4. **Cross-context patterns matter** ← Our situation

---

## Alternative Strategies (Not Yet Tested)

### 1. **Hierarchical Models**
Instead of completely separate models, use a two-stage approach:
```
Stage 1: Base model predicts using all data
Stage 2: Context-specific "adjustment" models correct the base prediction
```

**Potential Benefits**:
- Share learning across contexts
- Smaller adjustment models need less data
- Can fall back to base model for rare contexts

### 2. **Model Ensembles with Context Weighting**
Train multiple models on overlapping subsets and weight predictions by context relevance:
```python
prediction = weighted_avg([
    model_weekday.predict() * is_weekday,
    model_weekend.predict() * is_weekend,
    model_baseline.predict() * 0.3  # Always include baseline
])
```

### 3. **Feature Interactions Instead of Splitting**
Add explicit context interaction features to a single model:
```python
# Instead of separate models, create:
df['venue_hour_avg'] = df.groupby(['place_id', 'hour'])['item_count'].transform('mean')
df['venue_dow_avg'] = df.groupby(['place_id', 'day_of_week'])['item_count'].transform('mean')
df['venue_weekend_avg'] = df.groupby(['place_id', 'is_weekend'])['item_count'].transform('mean')
```

### 4. **Tree Model with Context as Feature**
Use context as a categorical feature and let the model decide when to split:
```python
# Explicitly encode context
df['time_context'] = determine_intuitive_context(df)

# Use CatBoost which handles categoricals naturally
model = CatBoostRegressor(cat_features=['time_context', 'place_id', 'type_id'])
```

This lets the tree ensemble learn: "For this context, treat features differently"

---

## Recommendations

### ✅ Keep the Baseline Single Model
- **Best performance**: MAE=0.3706, R²=0.9861
- Already captures context through existing features
- Benefits from larger training set

### ✅ Focus on Feature Engineering Instead
Priority improvements from [demand_enhancement.md](demand_enhancement.md):
1. **Venue-specific historical features** (Phase 2)
   - `venue_hour_avg`, `venue_dow_avg`
   - This adds context-aware information without splitting data
   
2. **Enhanced rolling features** (Phase 1)
   - Better capture temporal patterns
   
3. **Weather interaction features** (Phase 2)
   - `weekend_good_weather`, `rush_bad_weather`

### ✅ Try Ensemble Approach
- Voting ensemble of RF + XGBoost + LightGBM + CatBoost
- Expected 5-10% improvement (Phase 2)
- Maintains large training set advantage

### ❌ Abandon Pure Context-Specific Models
- Not effective for this use case
- May revisit with hierarchical approach if needed

---

## Lessons Learned

1. **More data usually beats clever segmentation** for tree-based models
2. **Context features in a unified model** are often more effective than separate models
3. **Sample size matters**: 648 samples insufficient for robust tree ensemble
4. **Test assumptions**: Enhancement plans should be validated, not assumed to work
5. **Baseline is strong**: Current model (MAE=0.3706) is already excellent

---

## Next Steps

Based on this analysis, recommend:

1. **Proceed with Phase 2 from enhancement plan**:
   - Venue-specific historical features
   - Weather interaction features
   - Model ensembles
   
2. **Skip context-specific models** unless:
   - We identify a true regime change
   - We have 10x more data
   - Hierarchical approach shows promise in experiments

3. **Continue with hyperparameter optimization**
   - Optuna tuning (Phase 3)
   - May yield 5-10% improvement

---

**Analysis Owner**: Data Science Team  
**Experiment Status**: ❌ Negative results - do not implement  
**Next Experiment**: Venue-specific historical features (Phase 2)
