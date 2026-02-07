# Demand Prediction Model - Error Analysis Report

## Executive Summary

Comprehensive error analysis has been performed on the demand prediction model (CatBoost-based multi-output regressor). This report provides actionable insights for model improvement.

**Date**: February 7, 2026  
**Model**: CatBoost Multi-Output (2 estimators)  
**Dataset**: 82,011 samples (Train: 65,608 | Test: 16,403)

---

## 📊 Overall Performance Metrics

### Test Set Performance
- **MAE (Mean Absolute Error)**: 5.44 items
- **Median Absolute Error**: 2.25 items
- **RMSE**: 9.96 items
- **R² Score**: -0.29 (indicates poor fit)
- **Mean Bias**: -4.47 (systematic under-prediction)

### Prediction Quality Distribution
- ✅ **Excellent** (error ≤ 2): 39.5% of predictions
- ✅ **Good** (2 < error ≤ 5): 30.3% of predictions
- ⚠️ **Fair** (5 < error ≤ 10): 14.7% of predictions
- ❌ **Poor** (error > 10): 15.5% of predictions

**Key Takeaway**: 70% of predictions are within ±5 items, but the model struggles with high-demand periods.

---

## 🔍 Critical Issues Identified

### 1. **Severe Under-Prediction Bias** 🚨 HIGH PRIORITY
- Model systematically under-predicts by 4.47 items on average
- Bias increases dramatically with demand level:
  - Low demand (0-3): +1.69 over-prediction
  - Medium demand (7-15): -6.53 under-prediction
  - High demand (15-25): -15.25 under-prediction
  - Very high demand (25+): -32.33 under-prediction

**Impact**: Restaurant understaffing during peak times, lost revenue opportunities

### 2. **Poor Performance on High-Demand Periods** 🚨 HIGH PRIORITY
- Very High Demand (25+ items): MAE = 32.33, R² = -7.19
- High Demand (15-25 items): MAE = 15.25, R² = -31.50
- Medium Demand (7-15 items): MAE = 6.53, R² = -8.76

**Impact**: Critical business impact during peak revenue periods

### 3. **High Temporal Variance** ⚠️ MEDIUM PRIORITY
- Performance varies significantly by hour (MAE std: 2.27)
- Worst hours:
  - 0:00 (midnight): MAE = 9.22
  - 17:00 (5pm): MAE = 9.01
  - 23:00 (11pm): MAE = 8.60
- Best hours:
  - 6am-8am: MAE < 2.5
  - Off-peak morning hours

**Impact**: Inconsistent reliability across different business hours

### 4. **Weekend vs Weekday Gap** ⚠️ MEDIUM PRIORITY
- Weekend MAE: 6.43 (26% worse)
- Weekday MAE: 5.12
- Friday-Saturday show highest errors (MAE > 6.5)

---

## 📈 Detailed Analysis by Segment

### By Demand Level

| Demand Level | Samples | % | MAE | Bias | R² | MAPE |
|-------------|---------|---|-----|------|-----|------|
| Very Low (0-3) | 4,546 | 27.7% | 1.69 | +1.69 | -11.63 | 75.4% |
| Low (3-7) | 5,284 | 32.2% | 1.26 | -1.14 | -1.12 | 21.0% |
| Medium (7-15) | 4,332 | 26.4% | 6.53 | -6.53 | -8.76 | 59.5% |
| High (15-25) | 1,507 | 9.2% | 15.25 | -15.25 | -31.50 | 78.2% |
| Very High (25+) | 734 | 4.5% | 32.33 | -32.33 | -7.19 | 87.8% |

**Key Finding**: Model performs well on low-demand scenarios but catastrophically fails on high-demand predictions.

### By Time Period

#### Hour of Day (Worst 5)
1. **Hour 0 (midnight)**: MAE = 9.22, Bias = -8.74 (90 samples)
2. **Hour 17 (5pm)**: MAE = 9.01, Bias = -8.46 (1,711 samples) 🚨
3. **Hour 23 (11pm)**: MAE = 8.60, Bias = -7.92 (132 samples)
4. **Hour 16 (4pm)**: MAE = 7.84, Bias = -7.23 (1,782 samples) 🚨
5. **Hour 1 (1am)**: MAE = 7.21, Bias = -6.68 (51 samples)

**Critical**: Hours 16-17 (evening dinner rush) have both high error AND high volume.

#### Day of Week
1. **Saturday**: MAE = 6.99, Bias = -6.22 (2,280 samples)
2. **Friday**: MAE = 6.63, Bias = -5.75 (2,957 samples)
3. **Sunday**: MAE = 5.71, Bias = -4.67 (1,748 samples)
4. **Monday**: MAE = 4.12, Bias = -2.99 (1,930 samples) ✅ Best

**Pattern**: Errors increase throughout the week, peaking on weekends.

### By Restaurant

#### Worst Predicted Restaurants (min 10 samples)
1. **Place 686203**: MAE = 27.97 (49 samples, avg demand: 30.5)
2. **Place 559530**: MAE = 15.51 (428 samples, avg demand: 18.4)
3. **Place 770164**: MAE = 14.71 (86 samples, avg demand: 17.2)

**Pattern**: High-volume restaurants with variable demand are poorly predicted.

#### Best Predicted Restaurants
1. **Place 599700**: MAE = 1.52 (11 samples, avg demand: 1.9)
2. **Place 564937**: MAE = 1.58 (240 samples, avg demand: 2.8)

**Pattern**: Low-volume, stable restaurants are well predicted.

### By Restaurant Type
1. **Type 1336**: MAE = 7.92 (677 samples)
2. **Type 1333**: MAE = 6.04 (1,387 samples)
3. **Type 12191**: MAE = 5.44 (13,263 samples)
4. **Type 1335**: MAE = 3.50 (513 samples)
5. **Type 1332**: MAE = 2.91 (563 samples) ✅ Best

**20.7% of restaurants have MAE > 7**, indicating poor segment coverage.

---

## 🎯 Feature Importance Analysis

### Top 15 Most Important Features

| Rank | Feature | Importance |
|------|---------|-----------|
| 1 | cloud_cover | 36.64 |
| 2 | wind_speed_10m | 8.65 |
| 3 | month | 8.50 |
| 4 | prev_hour_items | 6.07 |
| 5 | is_rainy | 4.01 |
| 6 | rolling_30d_avg_items | 2.14 |
| 7 | hour_sin | 2.02 |
| 8 | avg_discount | 1.84 |
| 9 | is_cold | 1.82 |
| 10 | rolling_14d_avg_items | 1.80 |
| 11 | rolling_7d_std_items | 1.72 |
| 12 | accepting_orders | 1.66 |
| 13 | total_campaigns | 1.65 |
| 14 | is_holiday | 1.56 |
| 15 | demand_trend_7d | 1.51 |

**Surprising Finding**: Weather features (cloud_cover, wind_speed, is_rainy) dominate importance, suggesting strong weather-demand correlation.

### Features Correlated with High Errors

| Feature | Correlation with Error |
|---------|----------------------|
| venue_hour_avg | 0.710 |
| venue_dow_avg | 0.536 |
| prev_hour_items | 0.531 |
| rolling_3d_avg_items | 0.485 |
| rolling_7d_avg_items | 0.482 |

**Insight**: Historical demand features are most correlated with errors, suggesting the model struggles to extrapolate beyond historical patterns.

---

## 🔬 Statistical Diagnostics

### Residual Analysis
- **Normality test p-value**: 0.0000 ❌
- **Residuals are NOT normally distributed** - indicates model assumptions are violated
- Residuals show heteroscedasticity (variance increases with prediction magnitude)
- Q-Q plot shows heavy tails (more extreme errors than expected)

### Overfitting Check
- Training MAE: 6.21
- Test MAE: 5.44
- **No overfitting detected** ✅ - model actually performs better on test set
- Suggests consistent performance but systematic issues

---

## 💡 Actionable Recommendations

### 🚨 High Priority (Immediate Action Required)

#### 1. **Implement Demand-Stratified Modeling**
**Problem**: Single model fails catastrophically on high-demand scenarios  
**Solution**: Train separate models or use ensemble approach:
- **Low-demand model** (0-7 items): Optimize for precision on stable demand
- **High-demand model** (15+ items): Optimize for recall, accept wider error bands
- **Blend zone** (7-15 items): Use weighted ensemble

**Expected Impact**: 40-60% error reduction on high-demand predictions

#### 2. **Address Systematic Under-Prediction Bias**
**Problem**: Model under-predicts by 4.47 items on average, worsening at high demand  
**Solution**:
- Apply post-processing calibration curve
- Adjust sample weights during training (increase weight for under-predicted samples)
- Use asymmetric loss function (penalize under-prediction more heavily)

**Expected Impact**: Reduce mean bias to < 1 item

#### 3. **Enhance Temporal Features**
**Problem**: High variance across hours (std = 2.27) and poor evening performance  
**Solution**: Add features:
- `is_peak_dinner` (17:00-19:00 indicator)
- `is_peak_lunch` (12:00-14:00 indicator)
- `time_since_last_meal_period`
- `upcoming_meal_period` (forward-looking)
- Hour-day interaction features (e.g., `friday_evening`)

**Expected Impact**: 20-30% error reduction during peak hours

### ⚠️ Medium Priority (Plan for Next Sprint)

#### 4. **Add Restaurant-Specific Features**
**Problem**: 20.7% of restaurants have MAE > 7; high variance across restaurant types  
**Solution**: Enhance with:
- Historical volatility metrics per restaurant
- Cuisine type/category embeddings
- Price range indicators
- Restaurant capacity/size
- Years in operation (maturity metric)

**Expected Impact**: 15-25% error reduction for problematic restaurants

#### 5. **Try Alternative Model Architectures**
**Problem**: Non-normal residuals suggest violated assumptions  
**Solution**:
- Test **LightGBM** with custom objective function
- Try **Quantile Regression** for uncertainty estimates
- Experiment with **Neural Network** for complex interactions
- Consider **log-transform** of target variable

**Expected Impact**: 10-20% overall MAE improvement

#### 6. **Improve Weekend Prediction**
**Problem**: Weekend performance 26% worse than weekday  
**Solution**:
- Add weekend-specific features (event calendars, sports schedules)
- Train weekend-specific model or use day-of-week conditional model
- Include lagged weekend features (last weekend's demand)

**Expected Impact**: Close weekend-weekday gap by 50%

### 📝 Lower Priority (Future Improvements)

#### 7. **Feature Engineering for Weather**
- Weather features are highly important but may need interaction terms
- Add `weather x hour` interactions
- Include weather forecast error metrics

#### 8. **Ensemble with Complementary Models**
- Combine CatBoost with linear model (for stable predictions)
- Use gradient boosting for high-demand, tree model for low-demand

#### 9. **Add External Data Sources**
- Local events calendar (concerts, sports, festivals)
- School calendar (holidays affect family dining)
- Competitor restaurant data

---

## 📊 Worst Predictions Case Study

### Top 10 Worst Predictions

| Hour | Day | Place ID | Actual | Predicted | Error |
|------|-----|----------|--------|-----------|-------|
| 12 | Sat | 686203 | 113 | 3.1 | 109.9 |
| 11 | Sat | 686203 | 111 | 3.1 | 107.9 |
| 10 | Sun | 686203 | 95 | 3.1 | 91.9 |
| 11 | Sun | 686203 | 92 | 3.1 | 88.9 |
| 13 | Sat | 686203 | 89 | 3.1 | 85.9 |

**Pattern Analysis**:
- **Restaurant 686203** appears 6 times in top 10 - needs special treatment
- **Hours 10-17** (lunch/dinner) dominate worst predictions
- **Days 4-6** (Fri-Sun) account for 80% of worst cases
- Model predicts ~3 items when actual is 80-113 items

**Root Cause**: Likely a high-volume venue (stadium, mall, event space) not well-represented in training data.

---

## 🎯 Success Metrics for Improvements

### Target Metrics (6-month goals)

| Metric | Current | Target | Improvement |
|--------|---------|--------|-------------|
| Overall MAE | 5.44 | < 3.50 | 36% |
| High-demand MAE (15+) | 15.25 | < 8.00 | 48% |
| R² Score | -0.29 | > 0.40 | - |
| Mean Bias | -4.47 | < 1.00 | 78% |
| Weekend MAE | 6.43 | < 4.50 | 30% |
| Peak hour MAE (16-17) | 8.42 | < 5.00 | 41% |

---

## 📁 Generated Artifacts

1. **error_analysis_details.csv** - Row-level predictions and errors for deep debugging
2. **error_analysis_summary.json** - Structured summary for programmatic access
3. **error_analysis_plots.png** - 9-panel visual diagnostic dashboard
4. **error_analysis_extended.png** - Restaurant and segment-specific visualizations

---

## 🚀 Recommended Implementation Plan

### Week 1-2: Quick Wins
- [ ] Implement bias correction (post-processing calibration)
- [ ] Add peak hour indicator features
- [ ] Apply demand-based sample weighting

### Week 3-4: Model Architecture
- [ ] Train separate high-demand model
- [ ] Experiment with LightGBM
- [ ] Test log-transformed target

### Week 5-6: Feature Engineering
- [ ] Add restaurant metadata (cuisine, capacity)
- [ ] Create hour-day interaction features
- [ ] Add historical volatility metrics

### Week 7-8: Validation & Deployment
- [ ] A/B test new model vs baseline
- [ ] Monitor business metrics (understaffing rate)
- [ ] Deploy production pipeline

---

## 🔗 Next Steps

1. **Review this report** with stakeholders
2. **Prioritize recommendations** based on business impact
3. **Run experiments** on proposed improvements
4. **Establish monitoring** for new metrics
5. **Schedule follow-up analysis** in 30 days

---

## 📧 Contact

For questions or deep-dive sessions on specific findings, contact the ML team.

**Report Generated**: February 7, 2026  
**Analysis Scripts**: `src/error_analysis.py`, `src/visualize_errors.py`
