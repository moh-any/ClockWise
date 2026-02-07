"""
Calibration utilities for demand prediction model
"""
import numpy as np
import joblib

def load_calibrated_model():
    """Load the calibrated model"""
    return joblib.load('data/models/rf_model_calibrated.joblib')

def predict_calibrated(X, calibrated_model_obj=None):
    """
    Make calibrated predictions
    
    Parameters:
    -----------
    X : array-like or DataFrame
        Features for prediction
    calibrated_model_obj : dict, optional
        Pre-loaded calibrated model object
        
    Returns:
    --------
    predictions : array
        Calibrated predictions for item_count and order_count
    """
    if calibrated_model_obj is None:
        calibrated_model_obj = load_calibrated_model()
    
    model = calibrated_model_obj['base_model']
    calibrators = calibrated_model_obj['calibrators']
    
    # Get base predictions
    if isinstance(model, list):
        predictions = np.column_stack([m.predict(X) for m in model])
    else:
        predictions = model.predict(X)
    
    # Calibrate item_count predictions
    y_pred_items = predictions[:, 0]
    y_calibrated = y_pred_items.copy()
    
    for name, (calibrator, low, high) in calibrators.items():
        mask = (y_pred_items >= low) & (y_pred_items < high)
        if mask.sum() > 0:
            y_calibrated[mask] = calibrator.predict(y_pred_items[mask])
    
    # Return calibrated predictions
    predictions_calibrated = predictions.copy()
    predictions_calibrated[:, 0] = y_calibrated
    
    return predictions_calibrated

# Example usage:
# model = load_calibrated_model()
# predictions = predict_calibrated(X_test, model)
