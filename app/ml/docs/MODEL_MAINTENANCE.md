# ML Model Maintenance System

This document describes the hybrid model maintenance strategy for the demand prediction system.

## Overview

The maintenance system implements a 3-tier approach:
- **Tier 1**: Weekly fine-tuning on new data (incremental learning)
- **Tier 2**: Quarterly full retraining (scheduled refresh)
- **Tier 3**: Emergency retraining on drift detection (reactive)

## Components

### 1. Model Monitor (`src/model_monitor.py`)

Tracks model performance by comparing predictions vs actuals.

```python
from src.model_monitor import ModelMonitor

monitor = ModelMonitor()

# Log prediction vs actual (called during data collection)
monitor.log_prediction_vs_actual(
    place_id=123,
    timestamp="2025-01-24T12:00:00",
    predicted=42.5,
    actual=38.0
)

# Check model health
health = monitor.get_model_health(days=7)
print(health)
# {
#     'status': 'healthy',
#     'mae': 2.45,
#     'baseline_mae': 2.31,
#     'degradation': 0.06,
#     'needs_retrain': False,
#     'healthy': True
# }

# Get training data for fine-tuning
training_data = monitor.get_training_data(days=30, min_samples=100)
```

**Files Created:**
- `logs/predictions_log.csv` - Raw predictions log
- `logs/training_data_new.csv` - Curated training data
- `logs/performance_metrics.json` - Rolling performance metrics

**Thresholds:**
- 15%+ degradation → Suggest retraining
- 25%+ degradation → Critical alert

### 2. Fine-Tune Model (`src/fine_tune_model.py`)

Performs incremental model updates using CatBoost warm start.

```python
from src.fine_tune_model import (
    fine_tune_from_monitor_data,
    fine_tune_from_processed_data,
    FineTuner
)

# Fine-tune from monitored predictions
result = fine_tune_from_monitor_data(
    days=30,          # Use last 30 days of data
    min_samples=100   # Require at least 100 samples
)

# Or fine-tune from processed data files
result = fine_tune_from_processed_data()

# Advanced: Use FineTuner class directly
tuner = FineTuner(
    base_model_path='data/models/rf_model.joblib',
    output_dir='data/models/finetuned'
)
tuner.fine_tune(X_new, y_new, learning_rate=0.03, iterations=100)
```

**Key Features:**
- Uses CatBoost `init_model` for warm starting
- Lower learning rate (0.03) to preserve learned patterns
- 10% validation split to monitor overfitting
- Creates new versioned model in staging area

### 3. Model Manager (`src/model_manager.py`)

Orchestrates the hybrid training lifecycle.

```bash
# Check current status
python src/model_manager.py --status

# Run automatic update (fine-tune or retrain as needed)
python src/model_manager.py --update

# Force fine-tune
python src/model_manager.py --fine-tune

# Force full retrain
python src/model_manager.py --full-retrain
```

```python
from src.model_manager import HybridModelManager

manager = HybridModelManager(
    full_retrain_interval_days=90,
    fine_tune_interval_days=7
)

# Automatic decision
result = manager.update_model()

# Check what action is needed
should_retrain, reason = manager.should_full_retrain()
should_fine_tune, reason = manager.should_fine_tune()
```

**Decision Logic:**
1. Critical drift (>25%)? → Full retrain
2. 90+ days since last full retrain? → Full retrain
3. 5+ fine-tunes since last retrain? → Full retrain
4. Moderate drift (>15%)? → Fine-tune
5. 7+ days since last update? → Fine-tune
6. Otherwise → No action needed

### 4. Model Deployer (`src/deploy_model.py`)

Handles safe deployment with archiving and rollback.

```bash
# Check current deployment status
python src/deploy_model.py --status

# Deploy a fine-tuned model
python src/deploy_model.py --deploy data/models/finetuned/rf_model_finetuned_20250124.joblib

# Rollback to previous version
python src/deploy_model.py --rollback

# Show deployment history
python src/deploy_model.py --history
```

```python
from src.deploy_model import ModelDeployer, deploy_finetuned_model

# Full deployment with validation
deployer = ModelDeployer()
success, message = deployer.deploy(
    new_model_path='data/models/finetuned/latest.joblib',
    new_metadata_path='data/models/finetuned/latest_metadata.json'
)

# Quick deployment for fine-tuned models
deploy_finetuned_model('data/models/finetuned')
```

**Safety Features:**
- Auto-archives current model before deployment
- Validates new model structure and features
- Compares performance metrics before deployment
- Maintains deployment history for audit
- One-command rollback to previous version

## Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                     Data Collection                          │
│  (data_collector.py with enable_monitoring=True)            │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    Model Monitor                             │
│  - Logs predictions vs actuals                              │
│  - Calculates drift metrics                                  │
│  - Stores training data                                      │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                   Model Manager                              │
│  - Checks health                                             │
│  - Decides: fine-tune vs retrain vs wait                    │
│  - Orchestrates update                                       │
└──────────────────────┬──────────────────────────────────────┘
                       │
          ┌────────────┴────────────┐
          ▼                         ▼
┌─────────────────────┐   ┌─────────────────────┐
│    Fine-Tune        │   │   Full Retrain      │
│  (warm start)       │   │  (train_model.py)   │
└─────────┬───────────┘   └──────────┬──────────┘
          │                          │
          └────────────┬─────────────┘
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    Deploy Model                              │
│  - Archive current                                           │
│  - Validate new                                              │
│  - Deploy to production                                      │
└─────────────────────────────────────────────────────────────┘
```

## Integration with Data Collector

The `data_collector.py` has been extended to integrate with the model monitor and optionally run automatic maintenance:

```python
from src.data_collector import RealTimeDataCollector

# Enable monitoring and automatic maintenance
collector = RealTimeDataCollector(
    enable_monitoring=True,   # Logs predictions vs actuals
    auto_maintain=True,       # Automatically check/run maintenance
    maintenance_check_interval_hours=6  # Check every 6 hours
)

# Run collection (automatically logs to monitor + runs maintenance if needed)
result = collector.collect_for_all_venues(venues)

# Check maintenance result
if result.get('maintenance'):
    print(f"Maintenance status: {result['maintenance']['status']}")
```

### Command Line Usage

```bash
# Run data collector with automatic maintenance
python src/data_collector.py --auto-maintain

# Force maintenance check now
python src/data_collector.py --force-maintenance

# Customize maintenance interval
python src/data_collector.py --auto-maintain --maintenance-interval 12
```

### How Automatic Maintenance Works

1. After each `collect_for_all_venues()` call, the collector checks if enough time has passed since the last maintenance check
2. If maintenance interval has elapsed (default: 6 hours), it runs `model_manager.update_model()`
3. If a fine-tune or retrain is performed, the collector automatically reloads the new model
4. The maintenance result is included in the collection response

## Manual Scheduled Maintenance

If you prefer manual scheduling instead of automatic maintenance:

### Weekly Schedule (Cron/Task Scheduler)

```bash
# Run every Sunday at 2 AM
0 2 * * 0 cd /path/to/app/ml && python src/model_manager.py --update
```

### PowerShell Task Scheduler (Windows)

```powershell
$action = New-ScheduledTaskAction -Execute "python" -Argument "src/model_manager.py --update" -WorkingDirectory "C:\path\to\app\ml"
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At 2AM
Register-ScheduledTask -TaskName "MLModelMaintenance" -Action $action -Trigger $trigger
```

## File Locations

| File | Purpose |
|------|---------|
| `data/models/rf_model.joblib` | Production model |
| `data/models/rf_model_metadata.json` | Model metadata |
| `data/models/finetuned/` | Staging for fine-tuned models |
| `data/models/archive/` | Archived model versions |
| `logs/predictions_log.csv` | Raw predictions log |
| `logs/training_data_new.csv` | Training data from monitoring |
| `logs/performance_metrics.json` | Performance history |
| `logs/model_manager_state.json` | Manager state |
| `logs/deployment_history.json` | Deployment audit log |

## Metrics & Thresholds

| Metric | Threshold | Action |
|--------|-----------|--------|
| MAE Degradation | >15% | Recommend fine-tune |
| MAE Degradation | >25% | Critical - recommend full retrain |
| Days Since Retrain | >90 | Scheduled full retrain |
| Fine-tunes Count | >5 | Force full retrain |

## Troubleshooting

### Common Issues

1. **"No predictions log found"**
   - The monitor hasn't collected any data yet
   - Run data collection with `enable_monitoring=True`

2. **"Insufficient data for fine-tuning"**
   - Need at least 100 samples (configurable)
   - Use `fine_tune_from_processed_data()` as fallback

3. **"CatBoost not available"**
   - Install with: `pip install catboost`

4. **Model deployment fails**
   - Check that new model has correct feature count (69)
   - Validate metadata exists alongside model file

### Manual Commands

```bash
# Force deploy without validation
python -c "from src.deploy_model import ModelDeployer; d=ModelDeployer(); d._archive_current(); d._do_deploy('path/to/model.joblib', 'path/to/metadata.json')"

# Check monitor data
python -c "from src.model_monitor import ModelMonitor; m=ModelMonitor(); print(m.get_training_data(days=90))"

# Reset manager state
rm logs/model_manager_state.json
```
