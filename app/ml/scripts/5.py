import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Simulated XGBoost feature importance (based on your campaign recommender features)
# These would come from the actual trained model
features = {
    'discount': 0.18,
    'avg_orders_before': 0.15,
    'duration_days': 0.12,
    'day_of_week': 0.11,
    'num_items': 0.09,
    'avg_temperature': 0.08,
    'season_summer': 0.07,
    'is_weekend': 0.06,
    'was_holiday': 0.05,
    'good_weather_ratio': 0.04,
    'hour_of_day': 0.03,
    'season_winter': 0.02,
}

# Create DataFrame
importance_df = pd.DataFrame({
    'feature': list(features.keys()),
    'importance': list(features.values())
}).sort_values('importance', ascending=False)

# Plot
plt.figure(figsize=(10, 7))
sns.barplot(data=importance_df, y='feature', x='importance', palette='rocket')
plt.title('Campaign ROI Predictor - XGBoost Feature Importance', 
          fontsize=14, fontweight='bold')
plt.xlabel('Gain Score', fontsize=12)
plt.ylabel('Feature', fontsize=12)
plt.tight_layout()
plt.savefig('campaign_feature_importance.png', dpi=300, bbox_inches='tight')
plt.show()