"""
Visualization script for error analysis
Generates comprehensive visualizations of model errors and performance
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# Set style
sns.set_style("whitegrid")
sns.set_palette("husl")
plt.rcParams['figure.figsize'] = (15, 10)
plt.rcParams['font.size'] = 10

print("="*80)
print("ERROR ANALYSIS VISUALIZATIONS")
print("="*80)

# Load error details
print("\n📊 Loading error analysis data...")
error_df = pd.read_csv('data/models/error_analysis_details.csv')
print(f"   ✓ Loaded {len(error_df):,} predictions")

# Main figure with subplots
fig = plt.figure(figsize=(20, 12))

# ============================================================================
# 1. RESIDUAL PLOT
# ============================================================================
print("\n1️⃣ Creating residual plot...")
ax1 = plt.subplot(3, 3, 1)
ax1.scatter(error_df['y_pred'], error_df['error'], alpha=0.3, s=20)
ax1.axhline(y=0, color='r', linestyle='--', linewidth=2)
ax1.set_xlabel('Predicted Value')
ax1.set_ylabel('Residual (Predicted - Actual)')
ax1.set_title('Residual Plot')
ax1.grid(True, alpha=0.3)

# Add reference lines at ±5
ax1.axhline(y=5, color='orange', linestyle=':', alpha=0.5)
ax1.axhline(y=-5, color='orange', linestyle=':', alpha=0.5)

# ============================================================================
# 2. PREDICTED VS ACTUAL
# ============================================================================
print("2️⃣ Creating predicted vs actual plot...")
ax2 = plt.subplot(3, 3, 2)
ax2.scatter(error_df['y_true'], error_df['y_pred'], alpha=0.3, s=20)
# Perfect prediction line
max_val = max(error_df['y_true'].max(), error_df['y_pred'].max())
ax2.plot([0, max_val], [0, max_val], 'r--', linewidth=2, label='Perfect Prediction')
ax2.set_xlabel('Actual Value')
ax2.set_ylabel('Predicted Value')
ax2.set_title('Predicted vs Actual')
ax2.legend()
ax2.grid(True, alpha=0.3)

# ============================================================================
# 3. ERROR DISTRIBUTION
# ============================================================================
print("3️⃣ Creating error distribution...")
ax3 = plt.subplot(3, 3, 3)
ax3.hist(error_df['error'], bins=50, edgecolor='black', alpha=0.7)
ax3.axvline(x=0, color='r', linestyle='--', linewidth=2)
ax3.axvline(x=error_df['error'].mean(), color='orange', linestyle='--', linewidth=2, label=f"Mean: {error_df['error'].mean():.2f}")
ax3.set_xlabel('Error (Predicted - Actual)')
ax3.set_ylabel('Frequency')
ax3.set_title('Error Distribution')
ax3.legend()
ax3.grid(True, alpha=0.3)

# ============================================================================
# 4. ABSOLUTE ERROR BY ACTUAL VALUE
# ============================================================================
print("4️⃣ Creating error by actual value...")
ax4 = plt.subplot(3, 3, 4)

# Bin the actual values and compute mean absolute error
bins = np.linspace(0, error_df['y_true'].quantile(0.95), 20)
error_df['y_true_binned'] = pd.cut(error_df['y_true'], bins=bins)
binned_errors = error_df.groupby('y_true_binned')['abs_error'].mean()

bin_centers = [interval.mid for interval in binned_errors.index]
ax4.plot(bin_centers, binned_errors.values, marker='o', linewidth=2, markersize=6)
ax4.set_xlabel('Actual Demand Level')
ax4.set_ylabel('Mean Absolute Error')
ax4.set_title('Error vs Demand Level')
ax4.grid(True, alpha=0.3)

# ============================================================================
# 5. ERROR BY HOUR OF DAY
# ============================================================================
print("5️⃣ Creating hourly error pattern...")
ax5 = plt.subplot(3, 3, 5)

hourly_stats = error_df.groupby('hour').agg({
    'abs_error': ['mean', 'std'],
    'error': 'mean'
})
hourly_stats.columns = ['MAE', 'StdErr', 'Bias']

ax5.plot(hourly_stats.index, hourly_stats['MAE'], marker='o', linewidth=2, label='MAE', color='blue')
ax5.fill_between(hourly_stats.index, 
                  hourly_stats['MAE'] - hourly_stats['StdErr'], 
                  hourly_stats['MAE'] + hourly_stats['StdErr'], 
                  alpha=0.3)
ax5_twin = ax5.twinx()
ax5_twin.plot(hourly_stats.index, hourly_stats['Bias'], marker='s', linewidth=2, 
              label='Bias', color='red', linestyle='--')
ax5_twin.axhline(y=0, color='gray', linestyle=':', alpha=0.5)

ax5.set_xlabel('Hour of Day')
ax5.set_ylabel('Mean Absolute Error', color='blue')
ax5_twin.set_ylabel('Bias (Over/Under Prediction)', color='red')
ax5.set_title('Error Pattern by Hour')
ax5.grid(True, alpha=0.3)
ax5.legend(loc='upper left')
ax5_twin.legend(loc='upper right')

# ============================================================================
# 6. ERROR BY DAY OF WEEK
# ============================================================================
print("6️⃣ Creating day-of-week error pattern...")
ax6 = plt.subplot(3, 3, 6)

dow_stats = error_df.groupby('day_of_week').agg({
    'abs_error': 'mean',
    'error': 'mean'
})
dow_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

x = np.arange(len(dow_names))
width = 0.35

bars1 = ax6.bar(x - width/2, dow_stats['abs_error'], width, label='MAE', alpha=0.8)
bars2 = ax6.bar(x + width/2, dow_stats['error'].abs(), width, label='|Bias|', alpha=0.8)

ax6.set_xlabel('Day of Week')
ax6.set_ylabel('Error Magnitude')
ax6.set_title('Error by Day of Week')
ax6.set_xticks(x)
ax6.set_xticklabels(dow_names)
ax6.legend()
ax6.grid(True, alpha=0.3, axis='y')

# ============================================================================
# 7. Q-Q PLOT FOR RESIDUALS
# ============================================================================
print("7️⃣ Creating Q-Q plot...")
ax7 = plt.subplot(3, 3, 7)
stats.probplot(error_df['error'], dist="norm", plot=ax7)
ax7.set_title('Q-Q Plot (Normality Check)')
ax7.grid(True, alpha=0.3)

# ============================================================================
# 8. CUMULATIVE ERROR DISTRIBUTION
# ============================================================================
print("8️⃣ Creating cumulative error distribution...")
ax8 = plt.subplot(3, 3, 8)

sorted_abs_errors = np.sort(error_df['abs_error'])
cumulative = np.arange(1, len(sorted_abs_errors) + 1) / len(sorted_abs_errors) * 100

ax8.plot(sorted_abs_errors, cumulative, linewidth=2)
ax8.axvline(x=2, color='green', linestyle='--', alpha=0.7, label='Error = 2')
ax8.axvline(x=5, color='orange', linestyle='--', alpha=0.7, label='Error = 5')
ax8.axvline(x=10, color='red', linestyle='--', alpha=0.7, label='Error = 10')
ax8.axhline(y=50, color='gray', linestyle=':', alpha=0.5)
ax8.axhline(y=80, color='gray', linestyle=':', alpha=0.5)
ax8.axhline(y=95, color='gray', linestyle=':', alpha=0.5)

ax8.set_xlabel('Absolute Error')
ax8.set_ylabel('Cumulative Percentage (%)')
ax8.set_title('Cumulative Error Distribution')
ax8.legend(loc='lower right')
ax8.grid(True, alpha=0.3)

# Find percentiles
median_error = np.median(sorted_abs_errors)
p80_error = np.percentile(sorted_abs_errors, 80)
p95_error = np.percentile(sorted_abs_errors, 95)

ax8.text(0.05, 0.95, f'50th percentile: {median_error:.2f}\n80th percentile: {p80_error:.2f}\n95th percentile: {p95_error:.2f}',
         transform=ax8.transAxes, verticalalignment='top',
         bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

# ============================================================================
# 9. ERROR HEATMAP (HOUR x DAY)
# ============================================================================
print("9️⃣ Creating hour-day heatmap...")
ax9 = plt.subplot(3, 3, 9)

# Create pivot table
heatmap_data = error_df.pivot_table(
    values='abs_error', 
    index='hour', 
    columns='day_of_week', 
    aggfunc='mean'
)

# Rename columns
heatmap_data.columns = dow_names

sns.heatmap(heatmap_data, annot=True, fmt='.2f', cmap='YlOrRd', 
            ax=ax9, cbar_kws={'label': 'Mean Absolute Error'})
ax9.set_title('Error Heatmap: Hour × Day')
ax9.set_xlabel('Day of Week')
ax9.set_ylabel('Hour of Day')

plt.tight_layout()
plt.savefig('data/models/error_analysis_plots.png', dpi=300, bbox_inches='tight')
print("\n✅ Saved main plot to: data/models/error_analysis_plots.png")

# ============================================================================
# ADDITIONAL PLOTS: ERROR BY RESTAURANT
# ============================================================================
print("\n📊 Creating restaurant-specific analysis...")
fig2, axes = plt.subplots(2, 2, figsize=(16, 10))

# Top 10 places by volume
ax_a = axes[0, 0]
place_counts = error_df['place_id'].value_counts().head(10)
place_errors = error_df.groupby('place_id')['abs_error'].mean()
top_places_errors = place_errors[place_counts.index]

ax_a.bar(range(len(top_places_errors)), top_places_errors.values, alpha=0.7)
ax_a.set_xlabel('Restaurant (Top 10 by Volume)')
ax_a.set_ylabel('Mean Absolute Error')
ax_a.set_title('Error for Busiest Restaurants')
ax_a.set_xticks(range(len(top_places_errors)))
ax_a.set_xticklabels([f'P{int(p)}' for p in top_places_errors.index], rotation=45)
ax_a.grid(True, alpha=0.3, axis='y')

# Error distribution by restaurant
ax_b = axes[0, 1]
place_error_dist = error_df.groupby('place_id')['abs_error'].mean()
ax_b.hist(place_error_dist, bins=30, edgecolor='black', alpha=0.7)
ax_b.set_xlabel('Mean Absolute Error per Restaurant')
ax_b.set_ylabel('Number of Restaurants')
ax_b.set_title('Distribution of Restaurant-Level Errors')
ax_b.axvline(x=place_error_dist.mean(), color='r', linestyle='--', 
             linewidth=2, label=f'Mean: {place_error_dist.mean():.2f}')
ax_b.legend()
ax_b.grid(True, alpha=0.3)

# Weekend vs Weekday comparison
if 'is_weekend' in error_df.columns:
    ax_c = axes[1, 0]
    
    weekend_errors = error_df[error_df['is_weekend'] == 1]['abs_error']
    weekday_errors = error_df[error_df['is_weekend'] == 0]['abs_error']
    
    ax_c.hist([weekday_errors, weekend_errors], bins=30, label=['Weekday', 'Weekend'], 
              alpha=0.6, edgecolor='black')
    ax_c.set_xlabel('Absolute Error')
    ax_c.set_ylabel('Frequency')
    ax_c.set_title('Error Distribution: Weekday vs Weekend')
    ax_c.legend()
    ax_c.grid(True, alpha=0.3)
else:
    axes[1, 0].text(0.5, 0.5, 'Weekend data not available', 
                    ha='center', va='center', transform=axes[1, 0].transAxes)

# Error by prediction magnitude
ax_d = axes[1, 1]
pred_bins = pd.qcut(error_df['y_pred'], q=10, duplicates='drop')
binned_analysis = error_df.groupby(pred_bins).agg({
    'abs_error': 'mean',
    'y_true': 'count'
})

x_labels = [f'{int(interval.left)}-{int(interval.right)}' for interval in binned_analysis.index]
x_pos = np.arange(len(x_labels))

color = ['green' if e < 3 else 'orange' if e < 5 else 'red' for e in binned_analysis['abs_error']]
ax_d.bar(x_pos, binned_analysis['abs_error'], color=color, alpha=0.7)
ax_d.set_xlabel('Predicted Demand Range')
ax_d.set_ylabel('Mean Absolute Error')
ax_d.set_title('Error by Prediction Magnitude')
ax_d.set_xticks(x_pos)
ax_d.set_xticklabels(x_labels, rotation=45, ha='right')
ax_d.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig('data/models/error_analysis_extended.png', dpi=300, bbox_inches='tight')
print("✅ Saved extended plots to: data/models/error_analysis_extended.png")

# ============================================================================
# PRINT SUMMARY STATISTICS
# ============================================================================
print("\n" + "="*80)
print("📈 VISUALIZATION SUMMARY")
print("="*80)

print("\nKey Insights from Visualizations:")
print(f"   • Median absolute error: {np.median(error_df['abs_error']):.2f}")
print(f"   • 80% of predictions within: ±{np.percentile(error_df['abs_error'], 80):.2f}")
print(f"   • 95% of predictions within: ±{np.percentile(error_df['abs_error'], 95):.2f}")

# Find worst hour
worst_hour = hourly_stats['MAE'].idxmax()
print(f"   • Worst performing hour: {int(worst_hour)}:00 (MAE: {hourly_stats.loc[worst_hour, 'MAE']:.2f})")

# Find worst day
worst_day = dow_stats['abs_error'].idxmax()
print(f"   • Worst performing day: {dow_names[int(worst_day)]} (MAE: {dow_stats.loc[worst_day, 'abs_error']:.2f})")

# Restaurant variance
place_error_std = place_error_dist.std()
print(f"   • Restaurant error variance: {place_error_std:.2f} (higher = more inconsistent)")

print("\n" + "="*80)
print("✅ VISUALIZATION COMPLETE")
print("="*80)
print("\nGenerated files:")
print("   • data/models/error_analysis_plots.png")
print("   • data/models/error_analysis_extended.png")
print("\nOpen these images to visually explore model errors and patterns.")
print("="*80)
