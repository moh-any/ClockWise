import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Set style
sns.set_style('whitegrid')
plt.rcParams['figure.figsize'] = (15, 10)

# Load results
comparison = pd.read_csv('data/models/context_specific_comparison.csv')

# Create comprehensive visualization
fig, axes = plt.subplots(2, 3, figsize=(18, 10))
fig.suptitle('Context-Specific Models Evaluation', fontsize=16, fontweight='bold')

# 1. MAE Comparison - Item Count
ax1 = axes[0, 0]
bars = ax1.bar(range(len(comparison)), comparison['mae_items'], 
               color=['green', 'orange', 'red'])
ax1.set_xticks(range(len(comparison)))
ax1.set_xticklabels(comparison['approach'], rotation=15, ha='right')
ax1.set_ylabel('MAE (Item Count)')
ax1.set_title('MAE Comparison - Item Count\n(Lower is Better)')
ax1.axhline(y=comparison['mae_items'].iloc[0], color='green', 
            linestyle='--', alpha=0.5, label='Baseline')

# Add values on bars
for i, (bar, val) in enumerate(zip(bars, comparison['mae_items'])):
    ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
             f'{val:.4f}', ha='center', va='bottom', fontweight='bold')

# 2. R² Comparison - Item Count
ax2 = axes[0, 1]
bars = ax2.bar(range(len(comparison)), comparison['r2_items'], 
               color=['green', 'orange', 'red'])
ax2.set_xticks(range(len(comparison)))
ax2.set_xticklabels(comparison['approach'], rotation=15, ha='right')
ax2.set_ylabel('R² Score')
ax2.set_title('R² Comparison - Item Count\n(Higher is Better)')
ax2.set_ylim([0.97, 0.99])

# Add values on bars
for i, (bar, val) in enumerate(zip(bars, comparison['r2_items'])):
    ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() - 0.001,
             f'{val:.4f}', ha='center', va='top', fontweight='bold', color='white')

# 3. Improvement Percentage
ax3 = axes[0, 2]
improvements = comparison['improvement_mae_items'].values
colors = ['green' if x >= 0 else 'red' for x in improvements]
bars = ax3.barh(range(len(comparison)), improvements, color=colors)
ax3.set_yticks(range(len(comparison)))
ax3.set_yticklabels(comparison['approach'])
ax3.set_xlabel('Improvement vs Baseline (%)')
ax3.set_title('MAE Improvement Percentage\n(Positive = Better)')
ax3.axvline(x=0, color='black', linestyle='-', linewidth=1)

# Add values on bars
for i, (bar, val) in enumerate(zip(bars, improvements)):
    x_pos = val + (1 if val < 0 else -1)
    ax3.text(x_pos, bar.get_y() + bar.get_height()/2,
             f'{val:.1f}%', ha='left' if val < 0 else 'right', 
             va='center', fontweight='bold')

# 4. MAE Comparison - Order Count
ax4 = axes[1, 0]
bars = ax4.bar(range(len(comparison)), comparison['mae_orders'], 
               color=['green', 'orange', 'red'])
ax4.set_xticks(range(len(comparison)))
ax4.set_xticklabels(comparison['approach'], rotation=15, ha='right')
ax4.set_ylabel('MAE (Order Count)')
ax4.set_title('MAE Comparison - Order Count\n(Lower is Better)')

# Add values on bars
for i, (bar, val) in enumerate(zip(bars, comparison['mae_orders'])):
    ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.003,
             f'{val:.4f}', ha='center', va='bottom', fontweight='bold')

# 5. R² Comparison - Order Count
ax5 = axes[1, 1]
bars = ax5.bar(range(len(comparison)), comparison['r2_orders'], 
               color=['green', 'orange', 'red'])
ax5.set_xticks(range(len(comparison)))
ax5.set_xticklabels(comparison['approach'], rotation=15, ha='right')
ax5.set_ylabel('R² Score')
ax5.set_title('R² Comparison - Order Count\n(Higher is Better)')
ax5.set_ylim([0.975, 0.995])

# Add values on bars
for i, (bar, val) in enumerate(zip(bars, comparison['r2_orders'])):
    ax5.text(bar.get_x() + bar.get_width()/2, bar.get_height() - 0.0005,
             f'{val:.4f}', ha='center', va='top', fontweight='bold', color='white')

# 6. Summary Table
ax6 = axes[1, 2]
ax6.axis('tight')
ax6.axis('off')

table_data = []
for _, row in comparison.iterrows():
    table_data.append([
        row['approach'].replace(' ', '\n'),
        f"{row['mae_items']:.4f}",
        f"{row['r2_items']:.4f}",
        f"{row['improvement_mae_items']:.1f}%"
    ])

table = ax6.table(cellText=table_data, 
                  colLabels=['Approach', 'MAE\n(Items)', 'R²\n(Items)', 'Improvement'],
                  cellLoc='center',
                  loc='center',
                  colWidths=[0.35, 0.2, 0.2, 0.25])

table.auto_set_font_size(False)
table.set_fontsize(9)
table.scale(1, 2.5)

# Color code the improvement column
for i in range(1, len(table_data) + 1):
    improvement = comparison.iloc[i-1]['improvement_mae_items']
    color = 'lightgreen' if improvement >= 0 else 'lightcoral'
    table[(i, 3)].set_facecolor(color)

# Header styling
for j in range(4):
    table[(0, j)].set_facecolor('lightblue')
    table[(0, j)].set_text_props(weight='bold')

ax6.set_title('Summary Table', fontweight='bold', pad=20)

plt.tight_layout()
plt.savefig('data/models/context_models_comparison.png', dpi=300, bbox_inches='tight')
print("Visualization saved to: data/models/context_models_comparison.png")
plt.show()

# Now create a detailed analysis visualization - Per-context/cluster performance
fig2, axes2 = plt.subplots(2, 1, figsize=(14, 10))
fig2.suptitle('Detailed Performance by Context/Cluster', fontsize=16, fontweight='bold')

# Intuitive categories performance
ax_intuitive = axes2[0]
contexts = ['weekday_breakfast', 'weekday_dinner', 'weekday_lunch', 
            'weekday_other', 'weekend_day', 'weekend_night']
context_mae = [0.4121, 0.3609, 0.3945, 0.4695, 0.5451, 1.4115]
context_samples = [1506, 2527, 4206, 4136, 3801, 227]

colors_context = ['green' if mae < 0.5 else 'orange' if mae < 0.8 else 'red' 
                  for mae in context_mae]
bars = ax_intuitive.bar(range(len(contexts)), context_mae, color=colors_context)

# Add sample size as text
for i, (bar, mae, samples) in enumerate(zip(bars, context_mae, context_samples)):
    ax_intuitive.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05,
                      f'MAE: {mae:.4f}\nn={samples:,}', 
                      ha='center', va='bottom', fontsize=9, fontweight='bold')

ax_intuitive.set_xticks(range(len(contexts)))
ax_intuitive.set_xticklabels([c.replace('_', '\n') for c in contexts], fontsize=10)
ax_intuitive.set_ylabel('MAE (Item Count)')
ax_intuitive.set_title('Intuitive Categories - MAE by Context')
ax_intuitive.axhline(y=0.3706, color='blue', linestyle='--', 
                     linewidth=2, label='Baseline MAE (0.3706)')
ax_intuitive.legend()
ax_intuitive.set_ylim([0, 1.6])

# K-Means clusters performance
ax_kmeans = axes2[1]
clusters = ['Cluster 0\n(Morning)', 'Cluster 1\n(Afternoon)', 
            'Cluster 2\n(Evening)', 'Cluster 4\n(Weekend)']
cluster_mae = [0.3679, 0.3993, 0.3527, 0.6186]
cluster_samples = [777, 9464, 3047, 3115]

colors_cluster = ['green' if mae < 0.5 else 'orange' if mae < 0.8 else 'red' 
                  for mae in cluster_mae]
bars = ax_kmeans.bar(range(len(clusters)), cluster_mae, color=colors_cluster)

# Add sample size as text
for i, (bar, mae, samples) in enumerate(zip(bars, cluster_mae, cluster_samples)):
    ax_kmeans.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
                   f'MAE: {mae:.4f}\nn={samples:,}', 
                   ha='center', va='bottom', fontsize=9, fontweight='bold')

ax_kmeans.set_xticks(range(len(clusters)))
ax_kmeans.set_xticklabels(clusters, fontsize=10)
ax_kmeans.set_ylabel('MAE (Item Count)')
ax_kmeans.set_title('K-Means Clustering - MAE by Cluster')
ax_kmeans.axhline(y=0.3706, color='blue', linestyle='--', 
                  linewidth=2, label='Baseline MAE (0.3706)')
ax_kmeans.legend()
ax_kmeans.set_ylim([0, 0.8])

# Add note about missing clusters
ax_kmeans.text(0.5, 0.95, 'Note: Clusters 3 & 5 had no test samples',
               transform=ax_kmeans.transAxes, ha='center', va='top',
               bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.5),
               fontsize=10, style='italic')

plt.tight_layout()
plt.savefig('data/models/context_models_detailed.png', dpi=300, bbox_inches='tight')
print("Detailed visualization saved to: data/models/context_models_detailed.png")
plt.show()

print("\nVisualization complete!")
