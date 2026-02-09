import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import beta

# Simulate realistic campaign performance evolution
np.random.seed(42)

campaigns = ['20% Discount Bundle', 'BOGO Deal', 'Seasonal Special']

# Simulate evolution over time (before and after learning)
fig, axes = plt.subplots(1, 3, figsize=(15, 4))
x = np.linspace(0, 1, 1000)

# Initial state (after 2-3 campaigns each)
initial_params = {
    '20% Discount Bundle': (3, 2),   # 3 successes, 2 failures (60% success)
    'BOGO Deal': (2, 3),              # 2 successes, 3 failures (40% success)
    'Seasonal Special': (2, 2)        # 2 successes, 2 failures (50% success)
}

# After 20+ campaigns each (learned state)
learned_params = {
    '20% Discount Bundle': (18, 5),   # Strong performer emerged
    'BOGO Deal': (8, 15),             # Clearly underperforming
    'Seasonal Special': (12, 10)      # Moderate performer
}

for idx, (campaign, ax) in enumerate(zip(campaigns, axes)):
    # Initial (weak knowledge)
    init_a, init_b = initial_params[campaign]
    init_dist = beta.pdf(x, init_a, init_b)
    
    # Learned (strong knowledge)
    learn_a, learn_b = learned_params[campaign]
    learn_dist = beta.pdf(x, learn_a, learn_b)
    
    ax.plot(x, init_dist, '--', label='Initial (weak prior)', linewidth=2, alpha=0.6, color='gray')
    ax.fill_between(x, learn_dist, alpha=0.6, label='After Learning', color='#2E86AB')
    ax.axvline(x=learn_a/(learn_a+learn_b), color='red', linestyle=':', 
               linewidth=2, label=f'Expected: {learn_a/(learn_a+learn_b):.2f}')
    
    ax.set_title(f'{campaign}\n(α={learn_a}, β={learn_b})', fontweight='bold', fontsize=11)
    ax.set_xlabel('Success Rate (ROI > 0)', fontsize=10)
    ax.set_ylabel('Probability Density', fontsize=10)
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

plt.suptitle('Thompson Sampling: Learning Campaign Performance Over Time', 
             fontsize=14, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig('thompson_sampling.png', dpi=300, bbox_inches='tight')
plt.show()