import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import joblib

# Load your trained Random Forest model
model = joblib.load('../data/models/rf_model.joblib')

# Extract the Random Forest from the pipeline
rf_model = model.regressor_.named_steps['model'].estimators_[0]  # First target (item_count)

# Get feature importance
feature_importance = rf_model.feature_importances_
feature_names = model.regressor_.named_steps['preprocessor'].get_feature_names_out()

# Create DataFrame
importance_df = pd.DataFrame({
    'feature': feature_names,
    'importance': feature_importance
}).sort_values('importance', ascending=False).head(15)

# Clean feature names (remove prefixes)
importance_df['feature'] = importance_df['feature'].str.replace('sclaler__', '').str.replace('remainder__', '')

# Plot
plt.figure(figsize=(10, 8))
sns.barplot(data=importance_df, y='feature', x='importance', palette='viridis')
plt.title('Top 15 Features - Random Forest Demand Prediction', fontsize=14, fontweight='bold')
plt.xlabel('Importance Score', fontsize=12)
plt.ylabel('Feature', fontsize=12)
plt.tight_layout()
plt.savefig('feature_importance.png', dpi=300, bbox_inches='tight')
plt.show()