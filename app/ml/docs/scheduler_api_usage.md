# Scheduler CP-SAT API Usage Guide

## Overview

The `scheduler_cpsat` module provides a reusable API for solving employee scheduling problems using Google OR-Tools CP-SAT solver. It includes comprehensive management insights to help with hiring decisions and workforce planning.

**📚 Looking for REST API endpoints?** See:
- **[Documentation.md](Documentation.md)** - Section 4: "Schedule Generation" (full REST API reference)
- **[data.md](../data.md)** - Section 4: "Generate Schedule" (API examples with cURL)

This guide covers the **Python API** for direct module usage.

## Main Function

### `solve_schedule(input_data, time_limit_seconds=60, include_insights=True)`

Solves a scheduling problem and returns both the solution dictionary, a human-readable description, and actionable management insights.

**Parameters:**
- `input_data` (SchedulerInput): The scheduling input data
- `time_limit_seconds` (int): Maximum solving time in seconds (default: 60)
- `include_insights` (bool): Whether to generate management insights (default: True)

**Returns:**
- `solution` (Dict or None): Dictionary containing:
  - `'status'`: Solver status (OPTIMAL, FEASIBLE, INFEASIBLE, etc.)
  - `'objective_value'`: Objective function value
  - `'schedule'`: List of schedule entries with employee, day, slot, and role
  - `'unmet_demand'`: Dictionary of unmet demand by (day, slot)
  - `'employee_stats'`: Dictionary of employee statistics (hours worked, deviation, etc.)
  - `'supply'`: Dictionary of production supply by (day, slot)
- `description` (str): Human-readable formatted description of the solution
- `insights` (Dict or None): Management insights containing:
  - `'employee_utilization'`: Utilization rate and status per employee
  - `'role_demand'`: Demand coverage and bottlenecks per role
  - `'hiring_recommendations'`: Prioritized suggestions for hiring by role
  - `'coverage_gaps'`: Time slots with insufficient coverage
  - `'cost_analysis'`: Cost breakdown and opportunity costs
  - `'workload_distribution'`: Fairness and balance metrics
  - `'peak_periods'`: High-demand periods requiring attention

## Basic Usage Example

```python
from scheduler_cpsat import (
    solve_schedule,
    SchedulerInput,
    Employee,
    Role
)

# Define roles
roles = [
    Role(id='server', producing=True, items_per_hour=30, 
         min_present=1, is_independent=True),
]

# Define employees
employees = [
    Employee(id='john', wage=15, max_hours_per_week=40, 
             max_consec_slots=8, pref_hours=32,
             role_eligibility={'server'}),
    Employee(id='jane', wage=16, max_hours_per_week=35, 
             max_consec_slots=6, pref_hours=30,
             role_eligibility={'server'}),
]

# Define demand
demand = {}
for day in range(7):
    for slot in range(12):
        demand[(day, slot)] = 20  # 20 items per slot

# Create input
input_data = SchedulerInput(
    employees=employees,
    roles=roles,
    num_days=7,
    num_slots_per_day=12,
    chains=[],
    slot_len_hour=1.0,
    min_rest_slots=1,
    min_shift_length_slots=3,
    demand=demand,
    fixed_shifts=False,
    meet_all_demand=True  # Hard constraint
)

# Solve
solution, description, insights = solve_schedule(input_data, time_limit_seconds=30, include_insights=True)

# Print description
print(description)

# Access solution programmatically
if solution:
    print(f"Status: {solution['status']}")
    print(f"Objective: {solution['objective_value']}")
    print(f"Schedule entries: {len(solution['schedule'])}")
    
    # Analyze employee work hours
    for emp_id, stats in solution['employee_stats'].items():
        print(f"{emp_id}: {stats['work_hours']}h worked")
    
    # Display management insights
    if insights:
        print("\n=== MANAGEMENT INSIGHTS ===")
        
        # Hiring recommendations
        if insights['hiring_recommendations']:
            print("\nHiring Recommendations:")
            for rec in insights['hiring_recommendations']:
                print(f"  - Hire {rec['recommended_hires']} {rec['role']}: {rec['reason']}")
                print(f"    Priority: {rec['priority']}, Impact: {rec['expected_impact']}")
        
        # Employee utilization
        print("\nEmployee Utilization:")
        for emp in insights['employee_utilization']:
            print(f"  {emp['employee']}: {emp['utilization_rate']:.1%} ({emp['status']})")
        
        # Cost analysis
        cost = insights['cost_analysis']
        print(f"\nCost Analysis:")
        print(f"  Total wage cost: ${cost['total_wage_cost']:.2f}")
        print(f"  Cost per item: ${cost['cost_per_item']:.4f}")
        
        # Workload distribution
        dist = insights['workload_distribution']
        print(f"\nWorkload Distribution:")
        print(f"  Balance score: {dist['balance_score']:.1%}")
        print(f"  Overutilized: {dist['overutilized_count']}, Underutilized: {dist['underutilized_count']}")
```

## Key Data Structures

### SchedulerInput
Main input data class containing:
- `employees`: List of Employee objects
- `roles`: List of Role objects
- `num_days`: Number of days in scheduling horizon
- `num_slots_per_day`: Number of time slots per day
- `chains`: List of ProductionChain objects (for supply chain modeling)
- `demand`: Dict mapping (day, slot) to demand value
- `meet_all_demand`: Boolean - if True, demand satisfaction is a hard constraint

### Employee
- `id`: Unique identifier
- `wage`: Hourly wage
- `max_hours_per_week`: Maximum weekly hours
- `max_consec_slots`: Maximum consecutive slots in one shift
- `pref_hours`: Preferred weekly hours
- `role_eligibility`: Set of role IDs the employee can perform
- `availability`: Dict of (day, slot) -> bool
- `slot_preferences`: Dict of (day, slot) -> bool for preferred slots

### Role
- `id`: Unique identifier
- `producing`: Whether role produces items
- `items_per_hour`: Production rate if producing
- `min_present`: Minimum employees required for this role per slot
- `is_independent`: True if not part of a production chain

### ProductionChain
- `id`: Unique identifier
- `roles`: Ordered list of role IDs in the chain (e.g., ['prep', 'cook'])
- `contrib_factor`: Contribution factor to total supply

## Advanced Features

### Hard vs Soft Demand Constraint
- `meet_all_demand=True`: Demand must be fully satisfied (may be infeasible)
- `meet_all_demand=False`: Unmet demand is penalized in objective but allowed

### Production Chains
Model bottleneck scenarios where output is limited by the minimum capacity in a chain:
```python
chains = [
    ProductionChain(id='kitchen', roles=['prep', 'cook'], contrib_factor=1.0)
]
```

### Constraint Parameters
- `min_rest_slots`: Minimum rest slots between day boundaries
- `min_shift_length_slots`: Minimum consecutive slots per shift
- `slot_len_hour`: Length of each time slot in hours

## Management Insights

The `insights` dictionary returned by `solve_schedule()` contains 7 categories of actionable management information:

### 1. Employee Utilization
Track how employees are being utilized relative to their capacity:
```python
for emp in insights['employee_utilization']:
    print(f"{emp['employee']}: {emp['utilization_rate']:.1%}")
    print(f"  Status: {emp['status']}")  # overutilized/well_utilized/underutilized/unused
    print(f"  Hours: {emp['hours_worked']}/{emp['max_hours']}")
```

**Status Categories:**
- `overutilized`: Working at 100% capacity (risk of burnout)
- `well_utilized`: 50-99% capacity (healthy utilization)
- `underutilized`: 1-49% capacity (could work more)
- `unused`: 0% capacity (not scheduled)

### 2. Role Demand Analysis
Understand which roles are bottlenecks:
```python
for role_id, analysis in insights['role_demand'].items():
    print(f"{role_id}: {analysis['demand_coverage']:.1%} coverage")
    if analysis['is_bottleneck']:
        print(f"  ⚠️ BOTTLENECK: {analysis['capacity_utilization']:.1%} utilized")
```

### 3. Hiring Recommendations
Prioritized suggestions for expanding the workforce:
```python
for rec in insights['hiring_recommendations']:
    print(f"Priority {rec['priority']}: Hire {rec['recommended_hires']} {rec['role']}")
    print(f"  Reason: {rec['reason']}")
    print(f"  Impact: {rec['expected_impact']}")
```

**Recommendation Types:**
- Unmet demand (demand cannot be satisfied)
- Overutilization (existing employees at 100% capacity)
- Bottleneck roles (limiting overall capacity)

### 4. Coverage Gaps
Identify time slots with insufficient staffing:
```python
for gap in insights['coverage_gaps']:
    print(f"Day {gap['day']}, Slot {gap['slot']}: {gap['severity']}")
    print(f"  {gap['issue']}")
```

**Severity Levels:**
- `critical`: No coverage or unmet demand
- `warning`: Only minimum staffing (no buffer)

### 5. Cost Analysis
Track wage costs and efficiency metrics:
```python
cost = insights['cost_analysis']
print(f"Total wage cost: ${cost['total_wage_cost']:.2f}")
print(f"Cost per item served: ${cost['cost_per_item']:.4f}")
print(f"Opportunity cost (unmet demand): ${cost['opportunity_cost']:.2f}")

for role_id, cost_val in cost['cost_by_role'].items():
    print(f"  {role_id}: ${cost_val:.2f}")
```

### 6. Workload Distribution
Assess fairness and balance in work allocation:
```python
dist = insights['workload_distribution']
print(f"Balance score: {dist['balance_score']:.1%}")  # Higher is better
print(f"Average hours: {dist['avg_hours']:.1f}")
print(f"Range: {dist['min_hours']}-{dist['max_hours']} hours")
print(f"Overutilized: {dist['overutilized_count']}, Underutilized: {dist['underutilized_count']}")
```

### 7. Peak Periods
Identify high-demand time slots requiring extra attention:
```python
for period in insights['peak_periods']:
    print(f"Slot {period['slot']}: {period['avg_demand']:.0f} items/slot")
    print(f"  Recommendation: {period['recommendation']}")
```

## Insights Configuration

Control insights generation:
```python
# Disable insights for faster solving
solution, description, _ = solve_schedule(data, include_insights=False)

# Enable insights (default)
solution, description, insights = solve_schedule(data, include_insights=True)
```

### Constraint Parameters
- `min_rest_slots`: Minimum rest slots between day boundaries
- `min_shift_length_slots`: Minimum consecutive slots per shift
- `slot_len_hour`: Length of each time slot in hours

## REST API Endpoints

For HTTP API usage, the scheduler is exposed through FastAPI endpoints:

### Available Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/predict/schedule` | POST | Generate schedule from demand predictions |
| `/predict/demand-and-schedule` | POST | Combined demand prediction + scheduling |

**Full API Documentation:**
- **[Documentation.md](Documentation.md)** - Complete request/response schemas and examples
- **[data.md](../data.md)** - cURL examples and integration guides

### Quick REST API Example

```bash
# Generate schedule with demand predictions
curl -X POST "http://localhost:8000/predict/schedule" \
  -H "Content-Type: application/json" \
  -d @schedule_request.json
```

**Request Structure:**
```json
{
  "place": { /* venue details */ },
  "schedule_input": {
    "roles": [ /* role definitions */ ],
    "employees": [ /* employee data */ ],
    "production_chains": [ /* optional chains */ ],
    "scheduler_config": { /* optimization settings */ }
  },
  "demand_predictions": [ /* hourly demand by day */ ],
  "prediction_start_date": "2026-02-07"
}
```

**Response:**
```json
{
  "schedule_output": { /* shifts by day */ },
  "schedule_status": "optimal",
  "schedule_message": "Schedule generated successfully",
  "objective_value": 12543.75,
  "management_insights": { /* 7 insight categories */ }
}
```

See [Documentation.md](Documentation.md) for complete schemas.

---

## See Also

- Full implementation: [scheduler_cpsat.py](../src/scheduler_cpsat.py)
- Example usage: [example_usage.py](../src/example_usage.py)
- Mathematical model: [scheduler_mathematical_model.md](scheduler_mathematical_model.md)
- **REST API Reference**: [Documentation.md](Documentation.md) Section 4
- **API Integration Guide**: [data.md](../data.md) Section 4
