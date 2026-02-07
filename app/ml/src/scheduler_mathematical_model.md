# Scheduler

## 0: What is the problem?

We are given the demand data for some timeframe predicted by the demand-prediction model and expressed as item_count and order_count. We are also given the employee data including their time preferences. We aim to find the optimal shift schedule for the given timeframe that satisfies the demand constraints and maximizes employee satisfaction. There are also some other constraints to consider, e.g., operating hours, max shift length, etc.

### Optimization or feasibiliy?

The problem in hand is an optimization problem of the form **Among all possible solutions, which is optimal?**

## 1: Define sets and indices

- $E=$ Employees (indexed by $e$)
- $R=$ Roles (indexed by $r$) 
- $D=$ Days of week (indexed by $d$)
- $T=$ Times Slots per day (indexed by $t$)
- $K=$ Predefined shifts (indexed by $k$)
- $C=$ Production chains (indexed by $c$)
- $R^{ind} \subseteq R$ = Set of independent roles (not part of any chain)
- $R^{chain}_c \subseteq R$ = Ordered set of roles forming chain $c$

## 2: Define parameters

- role: producing_r $\in \{0,1\}$, items_r (items per hour if producing), min_present_r (integer)
- employee: availability: avail_{e,d,t} $\in \{0,1\}$ (1 if available that day/slot), pref_r_{e,d,t} $\in \{0,1\}$ (preferred).
- role_elig_{e,r} $\in \{0,1\}$ (1 if employee $e$ can serve role $r$).
- demand_{d,t} = expected items demanded in day $d$ slot $t$.
- slot_len_hour = length of each time slot in hours
- wage_e = hourly wage by employee
- max_hours_per_week_e, max_consec_slots_e, min_rest_slots
- $\text{pref\_hours}_e$ = preferred number of work hours per week for employee $e$

**Chain/Independent role parameters:**
- $\text{independent}_r \in \{0,1\}$ = 1 if role $r$ is independent (contributes directly to supply)
- $\text{in\_chain}_{r,c} \in \{0,1\}$ = 1 if role $r$ belongs to production chain $c$
- $\text{chain\_pos}_{r,c} \in \mathbb{Z}_{\geq 0}$ = position of role $r$ in chain $c$ (1 = first stage, 2 = second, etc.)
- $\text{chain\_contrib}_c \in \mathbb{R}_{>0}$ = contribution factor of chain $c$ to final supply (default = 1)

## 3: Define decision variables

Slot Based:
- $x_{e,d,t} \in \{0,1\}:$ employee $e$ is assigned day $d$ slot $t$.
- $y_{e,r,d,t} \in \{0,1\}:$ employee $e$ performs role $r$ day $d$ slot $t$.
- $v_{d,t} \geq 0$: unmet demand at day $d$ slot $t$

If ```fixed_shifts = True```
- $z_{e,k} \in \{0,1\}:$ employee $e$ assigned to shift $k$
- start_k, end_k, L_{k} (in slots)

Auxiliary:
- $\text{work\_hours}_e \geq 0$: total hours worked by employee $e$
- $\text{hours\_dev}_e \geq 0$: absolute deviation from preferred hours for employee $e$
- $\text{pref\_sat}_{e,d,t} \in \{0,1\}$: 1 if employee $e$ is scheduled at preferred slot $(d,t)$
- $\text{start}_{e,d,t} \in \{0,1\}$: 1 if employee $e$ starts a shift at day $d$ slot $t$
- $\text{avg\_hours} \geq 0$: average hours across all employees
- $\text{fairness\_dev} \geq 0$: max deviation from average (for fairness)

**Supply-related variables:**
- $\text{capacity}_{r,d,t} \geq 0$: production capacity of role $r$ in day $d$ slot $t$
- $\text{chain\_output}_{c,d,t} \geq 0$: output of production chain $c$ in day $d$ slot $t$ (limited by bottleneck)
- $\text{supply}^{ind}_{d,t} \geq 0$: total supply from independent roles
- $\text{supply}^{chain}_{d,t} \geq 0$: total supply from production chains
- $\text{supply}_{d,t} \geq 0$: total supply at day $d$ slot $t$

## 4: State the objective function

$$\min \;\; W_{wage} \cdot \sum_{e \in E} \text{wage}_e \cdot \text{work\_hours}_e + W_{unmet} \cdot \sum_{d \in D, t \in T} v_{d,t} + W_{hours} \cdot \sum_{e \in E} \text{hours\_dev}_e - W_{slot} \cdot \sum_{e,d,t} \text{pref\_sat}_{e,d,t} + W_{fair} \cdot \text{fairness\_dev}$$

**Auxiliary definitions for objective:**

- Work hours per employee:
$$\text{work\_hours}_e = \sum_{d \in D, t \in T} x_{e,d,t} \cdot \text{slot\_len\_hour} \;\;\;\; \forall e \in E$$

- Deviation from preferred hours (linearized absolute value):
$$\text{hours\_dev}_e \geq \text{work\_hours}_e - \text{pref\_hours}_e \;\;\;\; \forall e \in E$$
$$\text{hours\_dev}_e \geq \text{pref\_hours}_e - \text{work\_hours}_e \;\;\;\; \forall e \in E$$

- Slot preference satisfaction (1 if scheduled when preferred):
$$\text{pref\_sat}_{e,d,t} \leq x_{e,d,t} \;\;\;\; \forall e,d,t$$
$$\text{pref\_sat}_{e,d,t} \leq \text{pref}_{e,d,t} \;\;\;\; \forall e,d,t$$
$$\text{pref\_sat}_{e,d,t} \geq x_{e,d,t} + \text{pref}_{e,d,t} - 1 \;\;\;\; \forall e,d,t$$

- Fairness (minimize max deviation from average hours):
$$\text{avg\_hours} = \frac{1}{|E|} \sum_{e \in E} \text{work\_hours}_e$$
$$\text{fairness\_dev} \geq \text{work\_hours}_e - \text{avg\_hours} \;\;\;\; \forall e \in E$$
$$\text{fairness\_dev} \geq \text{avg\_hours} - \text{work\_hours}_e \;\;\;\; \forall e \in E$$

**Weight hierarchy:** $W_{unmet} \gg W_{wage} \gg W_{hours} \gg W_{fair} \gg W_{slot}$

*Note: $W_{hours}$ penalizes deviation from preferred hours per employee; $W_{slot}$ rewards scheduling at preferred time slots.*

## 5: Add constraints

1. Availability
$$x_{e,d,t} \leq avail_{e,d,t} \;\;\;\; \forall e,d,t$$

2. Role eligibility
$$y_{e,r,d,t} \leq \text{role-elig}_{e,r} \;\;\;\; \forall e,r,d,t$$
$$y_{e,r,d,t} \leq x_{e,d,t}$$
$$\sum_{r\in R}y_{e,r,d,t} \leq 1$$

3. Minimum present per role
$$\sum_{e \in E: \text{role\_elig}_{e,r} = 1} y_{e,r,d,t} \geq \text{min\_present}_r \;\;\;\; \forall r \in R, d \in D, t \in T$$

4. Production Capacity vs demand

**Step 4a: Compute capacity per role**

The production capacity of each role is determined by the employees performing that role:
$$\text{capacity}_{r,d,t} = \sum_{e \in E} y_{e,r,d,t} \cdot \text{items}_r \cdot \text{slot\_len\_hour} \;\;\;\; \forall r \in R, d \in D, t \in T$$

**Step 4b: Supply from independent roles**

Independent roles contribute directly to supply (no dependencies):
$$\text{supply}^{ind}_{d,t} = \sum_{r \in R^{ind}} \text{capacity}_{r,d,t} \;\;\;\; \forall d \in D, t \in T$$

**Step 4c: Supply from production chains (bottleneck constraint)**

For production chains, the output is limited by the *bottleneck* (the stage with minimum capacity). Since $\min$ is non-linear, we model it using auxiliary constraints:

$$\text{chain\_output}_{c,d,t} \leq \text{capacity}_{r,d,t} \;\;\;\; \forall c \in C, \forall r \in R^{chain}_c, d \in D, t \in T$$

This ensures chain output cannot exceed the capacity of any role in the chain.

Total supply from chains:
$$\text{supply}^{chain}_{d,t} = \sum_{c \in C} \text{chain\_contrib}_c \cdot \text{chain\_output}_{c,d,t} \;\;\;\; \forall d \in D, t \in T$$

**Step 4d: Total supply**

$$\text{supply}_{d,t} = \text{supply}^{ind}_{d,t} + \text{supply}^{chain}_{d,t} \;\;\;\; \forall d \in D, t \in T$$

**Step 4e: Demand satisfaction (with soft constraint for unmet demand)**

$$\text{supply}_{d,t} + v_{d,t} \geq \text{demand}_{d,t} \;\;\;\; \forall d \in D, t \in T$$

where $v_{d,t} \geq 0$ is the unmet demand (penalized in objective)

5. Maximum hours per week

$$\text{work\_hours}_e \leq \text{max\_hours\_per\_week}_e \;\;\;\; \forall e \in E$$

Equivalently in slots:
$$\sum_{d \in D, t \in T} x_{e,d,t} \leq \frac{\text{max\_hours\_per\_week}_e}{\text{slot\_len\_hour}} \;\;\;\; \forall e \in E$$

6. Consecutive slots / min shift length

Define shift start indicator (1 if employee starts working at this slot):
$$\text{start}_{e,d,t} \geq x_{e,d,t} - x_{e,d,t-1} \;\;\;\; \forall e \in E, d \in D, t \in T: t > 1$$
$$\text{start}_{e,d,1} \geq x_{e,d,1} \;\;\;\; \forall e \in E, d \in D \text{ (first slot of day)}$$

If a shift starts, it must last at least $L_{min}$ consecutive slots:
$$\sum_{\tau = t}^{\min(t+L_{min}-1, |T|)} x_{e,d,\tau} \geq L_{min} \cdot \text{start}_{e,d,t} \;\;\;\; \forall e,d,t: t + L_{min} - 1 \leq |T|$$

Maximum consecutive slots:
$$\sum_{\tau = t}^{t + \text{max\_consec\_slots}_e} x_{e,d,\tau} \leq \text{max\_consec\_slots}_e \;\;\;\; \forall e,d,t$$

7. Min rest slots

Between any two working periods, employee must have minimum rest:
$$x_{e,d,t} + x_{e,d',t'} \leq 1 \;\;\;\; \forall e, (d,t), (d',t'): \text{gap}((d,t),(d',t')) < \text{min\_rest\_slots}$$

Alternatively, for consecutive days at day boundary:
$$x_{e,d,T_{max}} + \sum_{\tau=1}^{\text{min\_rest\_slots}} x_{e,d+1,\tau} \leq 1 \;\;\;\; \forall e, d < |D|$$
8. Fixed shifts version

If `fixed_shifts = True`, replace slot-based assignment with shift-based:

**Additional parameters:**
- $\text{shift\_avail}_{e,k} \in \{0,1\}$ = 1 if employee $e$ is available for entire shift $k$
- $\text{demand}_k$ = aggregated demand during shift $k$

**Constraints:**

Shift availability:
$$z_{e,k} \leq \text{shift\_avail}_{e,k} \;\;\;\; \forall e \in E, k \in K$$

One shift per employee per day (if shifts don't overlap):
$$\sum_{k \in K_d} z_{e,k} \leq 1 \;\;\;\; \forall e \in E, d \in D$$

Demand satisfaction per shift:
$$\sum_{e \in E} \sum_{r \in R: \text{producing}_r = 1} z_{e,k} \cdot \text{role\_elig}_{e,r} \cdot \text{items}_r \cdot L_k \cdot \text{slot\_len\_hour} \geq \text{demand}_k \;\;\;\; \forall k \in K$$

Max hours per week:
$$\sum_{k \in K} z_{e,k} \cdot L_k \cdot \text{slot\_len\_hour} \leq \text{max\_hours\_per\_week}_e \;\;\;\; \forall e \in E$$