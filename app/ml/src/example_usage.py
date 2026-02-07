"""
Example of how to use the scheduler_cpsat module from other modules.

This demonstrates:
1. Basic API usage with a feasible problem
2. Comprehensive insights display when solution is found
3. Infeasible problem with insights showing why it failed
"""

from scheduler_cpsat import (
    solve_schedule,
    create_sample_data,
    SchedulerInput,
    Employee,
    Role,
    ProductionChain
)


def print_detailed_insights(insights, solution_found=True):
    """Print comprehensive insights in a formatted way."""
    if not insights:
        print("No insights available")
        return
    
    print("\n" + "=" * 80)
    if solution_found:
        print("COMPLETE MANAGEMENT INSIGHTS")
    else:
        print("INSIGHTS (NO SOLUTION FOUND)")
    print("=" * 80)
    
    # Feasibility analysis (only when no solution)
    if not solution_found and 'feasibility_analysis' in insights:
        print("\n### FEASIBILITY ANALYSIS ###")
        if insights['feasibility_analysis']:
            for issue in insights['feasibility_analysis']:
                print(f"  [{issue['severity'].upper()}] {issue['issue']}")
                print(f"    {issue['details']}")
        else:
            print("  No obvious feasibility issues detected.")
    
    # Capacity analysis (always available)
    if 'capacity_analysis' in insights:
        print("\n### CAPACITY ANALYSIS ###")
        for role_id, data in insights['capacity_analysis'].items():
            print(f"  {role_id}:")
            print(f"    Eligible employees: {data['eligible_employees']}")
            print(f"    Total available hours: {data['total_available_hours']:.1f}h")
            if data['potential_output'] > 0:
                print(f"    Potential output: {data['potential_output']:.1f} items")
                print(f"    Capacity ratio: {data['capacity_ratio']:.2f} (need ≥1.0)")
                print(f"    Sufficient: {'✓' if data['is_sufficient'] else '✗'}")
    
    # Hiring Recommendations
    print("\n### HIRING RECOMMENDATIONS ###")
    if insights.get('hiring_recommendations'):
        for i, rec in enumerate(insights['hiring_recommendations'], 1):
            print(f"\n{i}. [{rec['priority'].upper()}] Hire {rec['recommended_hires']} {rec['role']}(s)")
            print(f"   Reason: {rec['reason']}")
            print(f"   Impact: {rec['expected_impact']}")
    else:
        print("No hiring recommendations - current staffing is sufficient")
    
    # Employee Utilization (only with solution)
    if solution_found and 'employee_utilization' in insights:
        print("\n### EMPLOYEE UTILIZATION (Top 5) ###")
        for emp in insights['employee_utilization'][:5]:
            status_emoji = {"overutilized": "🔴", "well_utilized": "🟢", 
                          "underutilized": "🟡", "unused": "⚪"}.get(emp['status'], "")
            print(f"{status_emoji} {emp['employee']:12s}: {emp['utilization_rate']:5.1%} "
                  f"({emp['hours_worked']:.1f}h / {emp['max_hours']:.1f}h) - {emp['status']}")
    
    # Workload Balance (only with solution)
    if solution_found and 'workload_distribution' in insights:
        print("\n### WORKLOAD DISTRIBUTION ###")
        wb = insights['workload_distribution']
        print(f"Average hours:     {wb['average_hours']:.1f}h")
        print(f"Range:             {wb['min_hours']:.1f}h - {wb['max_hours']:.1f}h (spread: {wb['range']:.1f}h)")
        print(f"Balance score:     {wb['balance_score']:.1%}")
        print(f"")
        print(f"Unused:            {wb['unused_employees']} employees (0 hours)")
        print(f"Underutilized:     {wb['underutilized_employees']} employees (<50% capacity)")
        print(f"Well-utilized:     {wb['well_utilized_employees']} employees (50-85% capacity)")
        print(f"Overutilized:      {wb['overutilized_employees']} employees (>85% capacity)")
    
    # Cost Analysis (only with solution)
    if solution_found and 'cost_analysis' in insights:
        print("\n### COST ANALYSIS ###")
        ca = insights['cost_analysis']
        print(f"Total wage cost:              ${ca['total_wage_cost']:.2f}")
        print(f"Opportunity cost (unmet):     ${ca['opportunity_cost_unmet_demand']:.2f}")
        print(f"Total cost:                   ${ca['total_cost']:.2f}")
        if ca['cost_per_item_served'] > 0:
            print(f"Cost per item served:         ${ca['cost_per_item_served']:.4f}")
        
        print("\nCost breakdown by role:")
        for role, cost in sorted(ca['cost_by_role'].items(), key=lambda x: x[1], reverse=True):
            print(f"  {role:12s}: ${cost:8.2f}")
    
    # Coverage Gaps (only with solution)
    if solution_found and 'coverage_gaps' in insights:
        print(f"\n### COVERAGE GAPS ###")
        if insights['coverage_gaps']:
            print(f"Total slots with coverage issues: {len(insights['coverage_gaps'])}")
            print("\nWorst 5 coverage gaps:")
            for gap in insights['coverage_gaps'][:5]:
                print(f"  Day {gap['day']}, Slot {gap['slot']:2d}: {gap['coverage_rate']:5.1%} coverage "
                      f"({gap['employees_working']} emp, demand: {gap['demand']:.0f}) [{gap['severity']}]")
        else:
            print("No coverage gaps - all slots adequately staffed!")
    
    # Peak Periods (always available)
    print(f"\n### PEAK DEMAND PERIODS ###")
    if insights.get('peak_periods'):
        for period in insights['peak_periods'][:5]:
            print(f"  Slot {period['slot']:2d}: avg demand {period['average_demand']:.1f}, "
                  f"max {period['max_demand']:.1f}")
            print(f"    → {period['recommendation']}")
    else:
        print("Demand is relatively balanced across all time slots")
    
    # Role Analysis (only with solution)
    if solution_found and 'role_demand' in insights:
        print(f"\n### ROLE DEMAND ANALYSIS ###")
        for role_id, stats in insights['role_demand'].items():
            bottleneck = "⚠️ BOTTLENECK" if stats['is_bottleneck'] else ""
            print(f"\n{role_id.upper()} {bottleneck}")
            print(f"  Eligible employees:   {stats['eligible_employees']}")
            print(f"  Working employees:    {stats['working_employees']}")
            print(f"  Total hours worked:   {stats['total_hours_worked']:.1f}h")
            print(f"  Capacity utilization: {stats['capacity_utilization']:.1%}")


def example_feasible_problem():
    """Example 1: Basic usage with a feasible problem."""
    print("\n" + "=" * 80)
    print("EXAMPLE 1: FEASIBLE PROBLEM WITH FULL INSIGHTS")
    print("=" * 80)
    
    # Use the built-in sample data
    print("\nUsing sample data with 27 employees, 4 roles, 7 days...")
    input_data = create_sample_data()
    
    # Solve the problem
    solution, description, insights = solve_schedule(input_data, time_limit_seconds=10)
    
    # Print the description
    print(description)
    
    # Access solution details programmatically
    if solution:
        print("\n" + "=" * 60)
        print("PROGRAMMATIC ACCESS EXAMPLE")
        print("=" * 60)
        
        print(f"\nObjective value: {solution['objective_value']:.2f}")
        print(f"Status: {solution['status']}")
        print(f"Number of schedule entries: {len(solution['schedule'])}")
        
        # Calculate total hours worked by all employees
        total_hours = sum(stats['work_hours'] for stats in solution['employee_stats'].values())
        print(f"Total hours worked: {total_hours:.1f}h")
        
        # Find which employee worked the most
        if solution['employee_stats']:
            max_worker = max(solution['employee_stats'].items(), key=lambda x: x[1]['work_hours'])
            print(f"Most hours worked by: {max_worker[0]} ({max_worker[1]['work_hours']:.1f}h)")
        
        # Check if any demand was unmet
        if solution['unmet_demand']:
            print(f"Unmet demand at {len(solution['unmet_demand'])} time slots")
        else:
            print("All demand was satisfied!")
    
    # Print detailed insights
    print_detailed_insights(insights, solution_found=(solution is not None))


def example_infeasible_problem():
    """Example 2: Infeasible problem showing insights without solution."""
    print("\n" + "=" * 80)
    print("EXAMPLE 2: INFEASIBLE PROBLEM - INSIGHTS SHOW WHY IT FAILED")
    print("=" * 80)
    
    # Create infeasible data: very high demand, insufficient capacity
    roles = [
        Role(id='server', producing=True, items_per_hour=30, min_present=2, is_independent=True),
        Role(id='chef', producing=True, items_per_hour=25, min_present=1, is_independent=True),
    ]
    
    # Only 2 employees for 84 slots with high demand
    employees = [
        Employee(id='alice', wage=15, max_hours_per_week=40, max_consec_slots=8, pref_hours=32,
                 role_eligibility={'server'}),
        Employee(id='bob', wage=20, max_hours_per_week=40, max_consec_slots=8, pref_hours=40,
                 role_eligibility={'server'}),
    ]
    
    # Very high demand
    demand = {}
    for d in range(7):
        for t in range(12):
            demand[(d, t)] = 1000  # 1000 items per slot - way too high
    
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
        meet_all_demand=True  # Hard constraint - makes it infeasible
    )
    
    print(f"\nProblem Setup:")
    print(f"  Employees: {len(input_data.employees)} ({', '.join(e.id for e in input_data.employees)})")
    print(f"  Roles: {[r.id for r in input_data.roles]}")
    print(f"  Total demand: {sum(input_data.demand.values()):,.0f} items")
    print(f"  Total slots: {input_data.num_days * input_data.num_slots_per_day}")
    print(f"  Max employee capacity: {sum(e.max_hours_per_week for e in input_data.employees)}h")
    
    # Try to solve (will fail)
    print("\nAttempting to solve (expected to fail)...")
    solution, description, insights = solve_schedule(input_data, time_limit_seconds=5)
    
    print("\n" + description)
    
    # Print insights even though no solution was found
    print_detailed_insights(insights, solution_found=False)
    
    print("\n" + "=" * 80)
    print("KEY TAKEAWAY")
    print("=" * 80)
    print("Even without a solution, insights help identify:")
    print("  • Why the problem is infeasible")
    print("  • What capacity is available vs needed")
    print("  • How many employees to hire and in which roles")
    print("  • Which time periods are most challenging")


def main():
    """Run all examples."""
    print("=" * 80)
    print("SCHEDULER API USAGE EXAMPLES")
    print("=" * 80)
    print("\nThis demonstrates the scheduler_cpsat module API with:")
    print("  1. A feasible problem with complete insights")
    print("  2. An infeasible problem showing diagnostic insights")
    
    # Run Example 1: Feasible problem
    example_feasible_problem()
    
    # Run Example 2: Infeasible problem
    example_infeasible_problem()
    
    print("\n" + "=" * 80)
    print("EXAMPLES COMPLETE")
    print("=" * 80)


if __name__ == '__main__':
    main()
