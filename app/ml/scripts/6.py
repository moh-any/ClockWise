import numpy as np
import matplotlib.pyplot as plt

# Simulate Thompson Sampling decision-making over time
np.random.seed(42)

n_rounds = 100
campaigns = ['High ROI (known)', 'Medium ROI (known)', 'Unknown Campaign']

# True success rates (unknown to algorithm)
true_success_rates = [0.65, 0.45, 0.55]

# Thompson Sampling parameters evolution
alphas = [[1, 1, 1]]  # Start with uniform prior
betas = [[1, 1, 1]]
selections = [[], [], []]
cumulative_rewards = [[], [], []]

for round_num in range(n_rounds):
    current_alpha = alphas[-1].copy()
    current_beta = betas[-1].copy()
    
    # Thompson Sampling: sample from each Beta distribution
    samples = [np.random.beta(current_alpha[i], current_beta[i]) for i in range(3)]
    
    # Select campaign with highest sample
    selected = np.argmax(samples)
    selections[selected].append(round_num)
    
    # Simulate outcome
    success = np.random.random() < true_success_rates[selected]
    
    # Update parameters
    if success:
        current_alpha[selected] += 1
    else:
        current_beta[selected] += 1
    
    alphas.append(current_alpha)
    betas.append(current_beta)
    
    # Track cumulative rewards
    for i in range(3):
        if i in cumulative_rewards and len(cumulative_rewards[i]) > 0:
            cumulative_rewards[i].append(cumulative_rewards[i][-1])
        else:
            cumulative_rewards[i].append(0)
    
    if success:
        cumulative_rewards[selected][-1] += 1

# Plot selection frequency over time
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))

# Selection counts over time
window = 10
for i, (campaign, color) in enumerate(zip(campaigns, ['#2E86AB', '#A23B72', '#F18F01'])):
    selection_rate = []
    for r in range(window, n_rounds):
        rate = sum(1 for s in selections[i] if s >= r - window and s < r) / window
        selection_rate.append(rate)
    
    ax1.plot(range(window, n_rounds), selection_rate, label=campaign, 
             linewidth=2, color=color)

ax1.set_xlabel('Campaign Rounds', fontsize=12)
ax1.set_ylabel('Selection Rate (10-round window)', fontsize=12)
ax1.set_title('Exploration → Exploitation: Thompson Sampling Learning', 
              fontsize=14, fontweight='bold')
ax1.legend(loc='best', fontsize=10)
ax1.grid(True, alpha=0.3)
ax1.axhline(y=0.33, color='gray', linestyle='--', alpha=0.5, label='Random (33%)')

# Cumulative rewards
for i, (campaign, color) in enumerate(zip(campaigns, ['#2E86AB', '#A23B72', '#F18F01'])):
    ax2.plot(cumulative_rewards[i], label=campaign, linewidth=2, color=color)

ax2.set_xlabel('Campaign Rounds', fontsize=12)
ax2.set_ylabel('Cumulative Successful Campaigns', fontsize=12)
ax2.set_title('Cumulative Performance: Exploitation of Best Campaign', 
              fontsize=14, fontweight='bold')
ax2.legend(loc='best', fontsize=10)
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('exploration_exploitation.png', dpi=300, bbox_inches='tight')
plt.show()

print(f"\nFinal selection counts:")
for i, campaign in enumerate(campaigns):
    print(f"{campaign}: {len(selections[i])} times ({len(selections[i])/n_rounds*100:.1f}%)")