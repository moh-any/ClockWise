"""
Prediction utility for demand forecasting with intervals
"""
import joblib
import pandas as pd
import numpy as np

def load_prediction_models():
    """Load both point prediction and interval models"""
    point_model = joblib.load('data/models/rf_model.joblib')
    interval_models = joblib.load('data/models/prediction_interval_models.joblib')
    return point_model, interval_models

def predict_with_intervals(X, interval_models=None):
    """
    Make predictions with confidence intervals
    
    Parameters:
    -----------
    X : DataFrame
        Feature data
    interval_models : dict, optional
        Pre-loaded interval models
        
    Returns:
    --------
    dict with 'item_count' and 'order_count' predictions,
    each containing 'lower', 'median', 'upper' arrays
    """
    if interval_models is None:
        interval_models = joblib.load('data/models/prediction_interval_models.joblib')
    
    results = {}
    
    for target in ['item_count', 'order_count']:
        results[target] = {
            'lower': interval_models[target]['lower'].predict(X),
            'median': interval_models[target]['median'].predict(X),
            'upper': interval_models[target]['upper'].predict(X)
        }
    
    return results

def get_scheduling_recommendation(predictions, target='item_count'):
    """
    Get scheduling recommendation based on predictions
    
    Parameters:
    -----------
    predictions : dict
        Output from predict_with_intervals
    target : str
        'item_count' or 'order_count'
        
    Returns:
    --------
    dict with 'conservative', 'moderate', 'aggressive' staffing levels
    """
    pred = predictions[target]
    
    return {
        'conservative': pred['upper'],    # Staff for 80th percentile
        'moderate': pred['median'],        # Staff for median
        'aggressive': pred['lower']        # Minimum staffing (risky)
    }

# Example usage:
# models = load_prediction_models()
# predictions = predict_with_intervals(X_new, models[1])
# staffing = get_scheduling_recommendation(predictions)
