# Model Development History

Records the key stages and lessons learned during the development of the demand prediction model.

---

## Version Timeline

| Version | Date | MAE | Key Change |
|---------|------|-----|------------|
| v1.0 | Feb 2026 | ~6.3 | Random Forest baseline |
| v2.0 | Feb 2026 | ~4.8 | Added holiday features |
| v3.0 | Feb 2026 | 3.99 | Cyclical encoding, time indicators |
| v4.0 | Feb 2026 | 2.69* | Venue features, ensemble (*flawed) |
| v5.0 | Feb 2026 | 3.37 | CatBoost, Quantile Loss |
| **v6.0** | Feb 2026 | **3.32** | Hyperparameter optimization |

*v4.0 used outlier capping which artificially lowered MAE on capped test data

---

## Phase 1: Feature Engineering (v3.0)

### What Worked
- **Cyclical time encoding**: `hour_sin`, `hour_cos` helped model understand hour 23 ≈ hour 0
- **Rush hour indicators**: Captured distinct demand patterns during lunch/dinner
- **Multiple rolling windows**: 3d, 7d, 14d, 30d averages

### Performance
- MAE improved 32% (4.8 → 3.99)
- Added 19 new features (34 → 54 total)

### Lesson Learned
Feature engineering provides significant gains early in model development.

---

## Phase 2: Venue-Specific Features (v4.0)

### What Worked
- **venue_hour_avg**: Became top feature at 28% importance
- **venue_volatility**: Captured predictability per venue
- **Simple ensemble**: RF + XGB + LGBM average

### Performance
- MAE improved 17% (3.99 → 2.69 on capped data)
- Added 15 features (54 → 69 total)

### What Failed (Important Lesson)
**Outlier capping was a critical mistake:**
- Capped targets to [0, 38] items before training
- Model tested on capped data → artificially good metrics
- Real-world predictions on uncapped data → MAE actually 5.44

### Lesson Learned
Always evaluate on unmodified real-world data. Preprocessing that changes target values can hide fundamental model weaknesses.

---

## Phase 3-5: Algorithm Change (v5.0)

### The Discovery
Independent verification revealed the "best" model was actually broken:
- Claimed MAE: 2.69 (on capped data)
- Actual MAE: 5.44 (on real data)
- R²: -0.26 (worse than predicting mean!)

### The Fix
1. Switched from Random Forest to CatBoost
2. Used **Quantile Loss (α=0.60)** instead of MSE
   - Predicts 60th percentile, not mean
   - Deliberately biases upward (better for staffing)
3. Added sample weighting:
   - High-demand samples get more weight
   - Recent data emphasized

### Performance
- MAE: 3.37 (real, honest metric)
- R²: 0.68 (model actually works)
- Bias: +0.26 (slight over-prediction, good for staffing)

### Lesson Learned
- Quantile regression is better than MSE for asymmetric costs
- Always verify metrics independently
- Archive working models before experiments

---

## Phase 6: Optimization (v6.0)

### Experiments Conducted
Tested 15+ configurations including:
- Different loss functions (MAE, Huber, Quantile 0.55)
- Tree depths (6, 8, 10, 12)
- Learning rates (0.02-0.08)
- Regularization (0.5-5.0)
- Ensemble methods
- Log-transform targets
- Segment-specific models

### What Didn't Work
| Approach | Result | Why |
|----------|--------|-----|
| Log-transform | +5% worse | Model handles scale natively |
| 3-model ensemble | +4% worse | CatBoost alone is optimal |
| Deeper trees (10+) | +5% worse | Overfitting |
| MAE/Huber loss | +4% worse | Quantile loss better suited |
| Heavy demand weighting | +8% worse | Distorted overall fit |

### What Did Work
Fine-tuning hyperparameters:
- Learning rate: 0.05 → 0.03 (slower convergence, better fit)
- L2 regularization: 3.0 → 2.5 (slightly less regularization)
- Iterations: 2000 → 3000 (more training)

### Performance
- MAE: 3.37 → 3.32 (1.63% improvement)
- R²: 0.68 → 0.69

### Lesson Learned
When a model is already well-tuned, gains become marginal. Further improvement requires new data sources, not algorithm changes.

---

## Key Insights for Future Development

### 1. Data Quality > Algorithm Choice
The biggest mistake (v4.0 outlier capping) wasn't about the algorithm—it was about data handling.

### 2. Independent Verification is Essential
Never trust metrics from training scripts. Always verify with independent code.

### 3. Asymmetric Costs Need Asymmetric Loss
For staffing: under-prediction is worse than over-prediction. Quantile loss handles this elegantly.

### 4. Feature Importance Reveals Reality
Top 3 features explain 50%+ of model:
- `venue_hour_avg` (28%)
- `prev_hour_items` (14%)
- `venue_dow_avg` (8%)

### 5. Know When to Stop
After v6.0, further algorithm improvements yielded <2% gains. The 32% unexplained variance is likely irreducible (random customer behavior, events, etc.)

---

## Archived Models

Located in `data/models/archive/`:

| File | Version | Purpose |
|------|---------|---------|
| `rf_model_asymmetric_v1.joblib` | v5.0 | Original quantile loss model |
| `rf_model_v5_backup.joblib` | v5.0 | Pre-optimization backup |
| `rf_model_phase4_*.joblib` | v4.0 | Phase 4 (flawed capping) |
| `rf_model_calibrated.joblib` | v3.0 | Calibration experiments |
| `rf_model_broken_*.joblib` | - | Failed experiments (reference) |

---

*Last Updated: February 7, 2026*
