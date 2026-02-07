"""
Scheduler CP-SAT Model using Google OR-Tools
Translates the mathematical model from scheduler_mathematical_model.md
"""

from ortools.sat.python import cp_model
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple, Optional
import json


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class Role:
    id: str
    producing: bool  # True if role produces items
    items_per_hour: float  # Production rate if producing
    min_present: int  # Minimum employees required
    is_independent: bool = True  # True if not part of a chain


@dataclass
class Employee:
    id: str
    wage: float
    max_hours_per_week: float
    max_consec_slots: int
    pref_hours: float  # Preferred work hours per week
    role_eligibility: Set[str] = field(default_factory=set)  # Set of role IDs
    availability: Dict[Tuple[int, int], bool] = field(default_factory=dict)  # (day, slot) -> available
    slot_preferences: Dict[Tuple[int, int], bool] = field(default_factory=dict)  # (day, slot) -> preferred


@dataclass
class ProductionChain:
    id: str
    roles: List[str]  # Ordered list of role IDs in chain
    contrib_factor: float = 1.0  # Contribution factor to supply


@dataclass
class Shift:
    id: str
    day: int
    start_slot: int
    end_slot: int  # Exclusive
    
    @property
    def length_slots(self) -> int:
        return self.end_slot - self.start_slot


@dataclass
class SchedulerInput:
    # Sets
    employees: List[Employee]
    roles: List[Role]
    num_days: int
    num_slots_per_day: int
    shifts: List[Shift] = field(default_factory=list)
    chains: List[ProductionChain] = field(default_factory=list)
    
    # Parameters
    slot_len_hour: float = 1.0
    min_rest_slots: int = 2
    min_shift_length_slots: int = 2
    demand: Dict[Tuple[int, int], float] = field(default_factory=dict)  # (day, slot) -> demand
    
    # Weights for objective (scaled to integers for CP-SAT)
    w_unmet: int = 100000
    w_wage: int = 100
    w_hours: int = 50
    w_fair: int = 10
    w_slot: int = 1
    
    # Mode
    fixed_shifts: bool = False
    meet_all_demand: bool = False  # If True, demand satisfaction is a hard constraint


# =============================================================================
# CP-SAT MODEL BUILDER
# =============================================================================

class SchedulerCPSAT:
    def __init__(self, input_data: SchedulerInput):
        self.data = input_data
        self.model = cp_model.CpModel()
        
        # Index mappings
        self.emp_idx = {e.id: i for i, e in enumerate(input_data.employees)}
        self.role_idx = {r.id: i for i, r in enumerate(input_data.roles)}
        
        # Decision variables storage
        self.x: Dict[Tuple[int, int, int], cp_model.IntVar] = {}  # (e, d, t) -> assigned
        self.y: Dict[Tuple[int, int, int, int], cp_model.IntVar] = {}  # (e, r, d, t) -> role assignment
        self.v: Dict[Tuple[int, int], cp_model.IntVar] = {}  # (d, t) -> unmet demand
        self.z: Dict[Tuple[int, int], cp_model.IntVar] = {}  # (e, k) -> shift assignment (if fixed_shifts)
        
        # Auxiliary variables
        self.work_slots: Dict[int, cp_model.IntVar] = {}  # e -> total slots worked
        self.hours_dev: Dict[int, cp_model.IntVar] = {}  # e -> deviation from preferred hours
        self.pref_sat: Dict[Tuple[int, int, int], cp_model.IntVar] = {}  # (e, d, t) -> preference satisfied
        self.start: Dict[Tuple[int, int, int], cp_model.IntVar] = {}  # (e, d, t) -> shift start indicator
        self.capacity: Dict[Tuple[int, int, int], cp_model.IntVar] = {}  # (r, d, t) -> capacity
        self.chain_output: Dict[Tuple[int, int, int], cp_model.IntVar] = {}  # (c, d, t) -> chain output
        self.supply: Dict[Tuple[int, int], cp_model.IntVar] = {}  # (d, t) -> total supply
        
        self.avg_slots: Optional[cp_model.IntVar] = None
        self.fairness_dev: Optional[cp_model.IntVar] = None
        
        # Build the model
        self._create_variables()
        self._add_constraints()
        self._set_objective()
    
    def _get_sets(self):
        """Return commonly used index ranges."""
        E = range(len(self.data.employees))
        R = range(len(self.data.roles))
        D = range(self.data.num_days)
        T = range(self.data.num_slots_per_day)
        return E, R, D, T
    
    def _create_variables(self):
        """Create all decision variables."""
        E, R, D, T = self._get_sets()
        data = self.data
        
        if not data.fixed_shifts:
            # ===== Slot-based variables =====
            
            # x[e,d,t]: employee e assigned to day d, slot t
            for e in E:
                for d in D:
                    for t in T:
                        self.x[e, d, t] = self.model.NewBoolVar(f'x_{e}_{d}_{t}')
            
            # y[e,r,d,t]: employee e performs role r on day d, slot t
            for e in E:
                for r in R:
                    for d in D:
                        for t in T:
                            self.y[e, r, d, t] = self.model.NewBoolVar(f'y_{e}_{r}_{d}_{t}')
            
            # start[e,d,t]: employee e starts a shift at day d, slot t
            for e in E:
                for d in D:
                    for t in T:
                        self.start[e, d, t] = self.model.NewBoolVar(f'start_{e}_{d}_{t}')
            
            # pref_sat[e,d,t]: preference satisfaction
            for e in E:
                for d in D:
                    for t in T:
                        self.pref_sat[e, d, t] = self.model.NewBoolVar(f'pref_sat_{e}_{d}_{t}')
        
        else:
            # ===== Fixed shift variables =====
            K = range(len(data.shifts))
            for e in E:
                for k in K:
                    self.z[e, k] = self.model.NewBoolVar(f'z_{e}_{k}')
        
        # ===== Supply-related variables =====
        
        # Capacity per role (scaled by 100 for precision)
        max_capacity = int(len(data.employees) * max(r.items_per_hour for r in data.roles if r.producing) * data.slot_len_hour * 100) if any(r.producing for r in data.roles) else 1000
        for r in R:
            for d in D:
                for t in T:
                    self.capacity[r, d, t] = self.model.NewIntVar(0, max_capacity, f'cap_{r}_{d}_{t}')
        
        # Chain output
        for c_idx, chain in enumerate(data.chains):
            for d in D:
                for t in T:
                    self.chain_output[c_idx, d, t] = self.model.NewIntVar(0, max_capacity, f'chain_out_{c_idx}_{d}_{t}')
        
        # Total supply per slot
        max_supply = max_capacity * len(data.roles)
        for d in D:
            for t in T:
                self.supply[d, t] = self.model.NewIntVar(0, max_supply, f'supply_{d}_{t}')
        
        # Unmet demand (scaled by 100)
        max_demand = int(max(data.demand.values(), default=0) * 100) + 1
        for d in D:
            for t in T:
                self.v[d, t] = self.model.NewIntVar(0, max_demand, f'unmet_{d}_{t}')
        
        # ===== Auxiliary variables for objective =====
        
        # Work slots per employee
        max_slots = data.num_days * data.num_slots_per_day
        for e in E:
            self.work_slots[e] = self.model.NewIntVar(0, max_slots, f'work_slots_{e}')
        
        # Hours deviation (in slots for simplicity)
        for e in E:
            self.hours_dev[e] = self.model.NewIntVar(0, max_slots, f'hours_dev_{e}')
        
        # Fairness: max and min slots for range-based fairness
        self.max_work_slots = self.model.NewIntVar(0, max_slots, 'max_work_slots')
        self.min_work_slots = self.model.NewIntVar(0, max_slots, 'min_work_slots')
        self.fairness_dev = self.model.NewIntVar(0, max_slots, 'fairness_dev')
    
    def _add_constraints(self):
        """Add all constraints to the model."""
        if self.data.fixed_shifts:
            self._add_fixed_shift_constraints()
        else:
            self._add_slot_based_constraints()
        
        self._add_supply_constraints()
        self._add_auxiliary_constraints()
    
    def _add_slot_based_constraints(self):
        """Add constraints for slot-based scheduling."""
        E, R, D, T = self._get_sets()
        data = self.data
        
        # ----- Constraint 1: Availability -----
        for e_idx, emp in enumerate(data.employees):
            for d in D:
                for t in T:
                    avail = emp.availability.get((d, t), True)
                    if not avail:
                        self.model.Add(self.x[e_idx, d, t] == 0)
        
        # ----- Constraint 2: Role eligibility -----
        for e_idx, emp in enumerate(data.employees):
            for r_idx, role in enumerate(data.roles):
                for d in D:
                    for t in T:
                        if role.id not in emp.role_eligibility:
                            self.model.Add(self.y[e_idx, r_idx, d, t] == 0)
                        
                        self.model.Add(self.y[e_idx, r_idx, d, t] <= self.x[e_idx, d, t])
            
            for d in D:
                for t in T:
                    self.model.Add(sum(self.y[e_idx, r, d, t] for r in R) <= 1)
        
        # ----- Constraint 3: Minimum present per role -----
        for r_idx, role in enumerate(data.roles):
            for d in D:
                for t in T:
                    eligible = [e for e, emp in enumerate(data.employees) if role.id in emp.role_eligibility]
                    if eligible and role.min_present > 0:
                        self.model.Add(
                            sum(self.y[e, r_idx, d, t] for e in eligible) >= role.min_present
                        )
        
        # ----- Constraint 5: Maximum hours per week -----
        for e_idx, emp in enumerate(data.employees):
            max_slots = int(emp.max_hours_per_week / data.slot_len_hour)
            self.model.Add(
                sum(self.x[e_idx, d, t] for d in D for t in T) <= max_slots
            )
        
        # ----- Constraint 6: Consecutive slots / min-max shift length -----
        for e_idx, emp in enumerate(data.employees):
            for d in D:
                for t in T:
                    if t == 0:
                        self.model.Add(self.start[e_idx, d, t] >= self.x[e_idx, d, t])
                    else:
                        self.model.Add(
                            self.start[e_idx, d, t] >= self.x[e_idx, d, t] - self.x[e_idx, d, t - 1]
                        )
                
                L_min = data.min_shift_length_slots
                for t in T:
                    if t + L_min <= data.num_slots_per_day:
                        self.model.Add(
                            sum(self.x[e_idx, d, tau] for tau in range(t, t + L_min)) 
                            >= L_min * self.start[e_idx, d, t]
                        )
                
                max_consec = emp.max_consec_slots
                for t in T:
                    if t + max_consec + 1 <= data.num_slots_per_day:
                        self.model.Add(
                            sum(self.x[e_idx, d, tau] for tau in range(t, t + max_consec + 1)) 
                            <= max_consec
                        )
        
        # ----- Constraint 7: Min rest slots -----
        min_rest = data.min_rest_slots
        for e_idx in E:
            for d in range(data.num_days - 1):
                T_max = data.num_slots_per_day - 1
                rest_slots = min(min_rest, data.num_slots_per_day)
                self.model.Add(
                    self.x[e_idx, d, T_max] + sum(self.x[e_idx, d + 1, tau] for tau in range(rest_slots)) <= 1
                )
    
    def _add_fixed_shift_constraints(self):
        """Add constraints for fixed-shift scheduling."""
        E, R, D, T = self._get_sets()
        data = self.data
        K = range(len(data.shifts))
        
        for e_idx, emp in enumerate(data.employees):
            for k_idx, shift in enumerate(data.shifts):
                available = all(
                    emp.availability.get((shift.day, t), True) 
                    for t in range(shift.start_slot, shift.end_slot)
                )
                if not available:
                    self.model.Add(self.z[e_idx, k_idx] == 0)
        
        for e_idx in E:
            for d in D:
                shifts_on_day = [k for k, s in enumerate(data.shifts) if s.day == d]
                if shifts_on_day:
                    self.model.Add(sum(self.z[e_idx, k] for k in shifts_on_day) <= 1)
        
        for e_idx, emp in enumerate(data.employees):
            max_slots = int(emp.max_hours_per_week / data.slot_len_hour)
            self.model.Add(
                sum(self.z[e_idx, k] * data.shifts[k].length_slots for k in K) <= max_slots
            )
    
    def _add_supply_constraints(self):
        """Add production capacity and supply constraints."""
        E, R, D, T = self._get_sets()
        data = self.data
        
        SCALE = 100
        
        # ----- Compute capacity per role -----
        for r_idx, role in enumerate(data.roles):
            items_scaled = int(role.items_per_hour * data.slot_len_hour * SCALE)
            for d in D:
                for t in T:
                    if not data.fixed_shifts:
                        self.model.Add(
                            self.capacity[r_idx, d, t] == 
                            sum(self.y[e, r_idx, d, t] * items_scaled for e in E)
                        )
                    else:
                        overlapping_shifts = [
                            k for k, s in enumerate(data.shifts) 
                            if s.day == d and s.start_slot <= t < s.end_slot
                        ]
                        eligible = [e for e, emp in enumerate(data.employees) if role.id in emp.role_eligibility]
                        self.model.Add(
                            self.capacity[r_idx, d, t] == 
                            sum(self.z[e, k] * items_scaled for e in eligible for k in overlapping_shifts)
                        )
        
        # ----- Supply from independent roles and chains -----
        independent_roles = [r for r, role in enumerate(data.roles) if role.is_independent]
        
        for d in D:
            for t in T:
                supply_terms = []
                
                for r_idx in independent_roles:
                    supply_terms.append(self.capacity[r_idx, d, t])
                
                for c_idx, chain in enumerate(data.chains):
                    chain_role_indices = [self.role_idx[rid] for rid in chain.roles if rid in self.role_idx]
                    
                    if len(chain_role_indices) == 0:
                        continue
                    
                    capacity_vars = [self.capacity[r_idx, d, t] for r_idx in chain_role_indices]
                    self.model.AddMinEquality(self.chain_output[c_idx, d, t], capacity_vars)
                    
                    contrib_scaled = int(chain.contrib_factor * SCALE)
                    supply_terms.append((self.chain_output[c_idx, d, t] * contrib_scaled) // SCALE)
                
                if supply_terms:
                    self.model.Add(self.supply[d, t] == sum(supply_terms))
                else:
                    self.model.Add(self.supply[d, t] == 0)
        
        # ----- Demand satisfaction -----
        for d in D:
            for t in T:
                demand_scaled = int(data.demand.get((d, t), 0) * SCALE)
                if data.meet_all_demand:
                    self.model.Add(self.supply[d, t] >= demand_scaled)
                    self.model.Add(self.v[d, t] == 0)
                else:
                    self.model.Add(self.supply[d, t] + self.v[d, t] >= demand_scaled)
    
    def _add_auxiliary_constraints(self):
        """Add auxiliary variable definitions for objective."""
        E, R, D, T = self._get_sets()
        data = self.data
        
        for e_idx in E:
            if not data.fixed_shifts:
                self.model.Add(
                    self.work_slots[e_idx] == sum(self.x[e_idx, d, t] for d in D for t in T)
                )
            else:
                K = range(len(data.shifts))
                self.model.Add(
                    self.work_slots[e_idx] == sum(
                        self.z[e_idx, k] * data.shifts[k].length_slots for k in K
                    )
                )
        
        for e_idx, emp in enumerate(data.employees):
            pref_slots = int(emp.pref_hours / data.slot_len_hour)
            self.model.Add(self.hours_dev[e_idx] >= self.work_slots[e_idx] - pref_slots)
            self.model.Add(self.hours_dev[e_idx] >= pref_slots - self.work_slots[e_idx])
        
        if not data.fixed_shifts:
            for e_idx, emp in enumerate(data.employees):
                for d in D:
                    for t in T:
                        pref = 1 if emp.slot_preferences.get((d, t), False) else 0
                        if pref:
                            self.model.Add(self.pref_sat[e_idx, d, t] <= self.x[e_idx, d, t])
                            self.model.Add(self.pref_sat[e_idx, d, t] >= self.x[e_idx, d, t])
                        else:
                            self.model.Add(self.pref_sat[e_idx, d, t] == 0)
        
        for e_idx in E:
            self.model.Add(self.max_work_slots >= self.work_slots[e_idx])
            self.model.Add(self.min_work_slots <= self.work_slots[e_idx])
        
        self.model.Add(self.fairness_dev >= self.max_work_slots - self.min_work_slots)
    
    def _set_objective(self):
        """Set the objective function."""
        E, R, D, T = self._get_sets()
        data = self.data
        
        objective_terms = []
        
        for e_idx, emp in enumerate(data.employees):
            wage_per_slot = int(emp.wage * data.slot_len_hour * 100)
            objective_terms.append(data.w_wage * wage_per_slot * self.work_slots[e_idx])
        
        for d in D:
            for t in T:
                objective_terms.append(data.w_unmet * self.v[d, t])
        
        for e_idx in E:
            objective_terms.append(data.w_hours * self.hours_dev[e_idx])
        
        if not data.fixed_shifts:
            for e_idx in E:
                for d in D:
                    for t in T:
                        objective_terms.append(-data.w_slot * self.pref_sat[e_idx, d, t])
        
        objective_terms.append(data.w_fair * self.fairness_dev)
        
        self.model.Minimize(sum(objective_terms))
    
    def solve(self, time_limit_seconds: int = 60) -> Optional[Dict]:
        """Solve the model and return the solution."""
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = time_limit_seconds
        solver.parameters.log_search_progress = True
        
        status = solver.Solve(self.model)
        
        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            return self._extract_solution(solver, status)
        else:
            print(f"No solution found. Status: {solver.StatusName(status)}")
            return None
    
    def _extract_solution(self, solver: cp_model.CpSolver, status: int) -> Dict:
        """Extract solution from solver."""
        E, R, D, T = self._get_sets()
        data = self.data
        
        solution = {
            'status': solver.StatusName(status),
            'objective_value': solver.ObjectiveValue(),
            'schedule': [],
            'unmet_demand': {},
            'employee_stats': {},
            'supply': {}
        }
        
        if not data.fixed_shifts:
            for e_idx, emp in enumerate(data.employees):
                for d in D:
                    for t in T:
                        if solver.Value(self.x[e_idx, d, t]) == 1:
                            role_assigned = None
                            for r_idx, role in enumerate(data.roles):
                                if solver.Value(self.y[e_idx, r_idx, d, t]) == 1:
                                    role_assigned = role.id
                                    break
                            solution['schedule'].append({
                                'employee': emp.id,
                                'day': d,
                                'slot': t,
                                'role': role_assigned
                            })
        else:
            for e_idx, emp in enumerate(data.employees):
                for k_idx, shift in enumerate(data.shifts):
                    if solver.Value(self.z[e_idx, k_idx]) == 1:
                        solution['schedule'].append({
                            'employee': emp.id,
                            'shift': shift.id,
                            'day': shift.day,
                            'start_slot': shift.start_slot,
                            'end_slot': shift.end_slot
                        })
        
        for d in D:
            for t in T:
                unmet = solver.Value(self.v[d, t]) / 100
                if unmet > 0:
                    solution['unmet_demand'][(d, t)] = unmet
        
        for e_idx, emp in enumerate(data.employees):
            work_slots = solver.Value(self.work_slots[e_idx])
            work_hours = work_slots * data.slot_len_hour
            hours_dev = solver.Value(self.hours_dev[e_idx]) * data.slot_len_hour
            
            pref_satisfied = 0
            if not data.fixed_shifts:
                pref_satisfied = sum(
                    solver.Value(self.pref_sat[e_idx, d, t]) 
                    for d in D for t in T
                )
            
            solution['employee_stats'][emp.id] = {
                'work_hours': work_hours,
                'pref_hours': emp.pref_hours,
                'hours_deviation': hours_dev,
                'preferences_satisfied': pref_satisfied
            }
        
        for d in D:
            for t in T:
                solution['supply'][(d, t)] = solver.Value(self.supply[d, t]) / 100
        
        return solution


def generate_management_insights(solution: Optional[Dict], input_data: SchedulerInput) -> Dict:
    """
    Generate management insights from the solution to help with hiring and workforce decisions.
    
    Returns complete insights dictionary with all 8 insight categories:
    - has_solution, peak_periods, capacity_analysis (always)
    - employee_utilization, role_demand, hiring_recommendations, coverage_gaps, 
      cost_analysis, workload_distribution (with solution)
    - feasibility_analysis (without solution)
    """
    insights = {
        'has_solution': solution is not None
    }
    
    # === PEAK PERIODS (Always available) ===
    peak_periods = []
    demand_by_slot = {}
    
    for d in range(input_data.num_days):
        for t in range(input_data.num_slots_per_day):
            demand = input_data.demand.get((d, t), 0)
            if t not in demand_by_slot:
                demand_by_slot[t] = []
            demand_by_slot[t].append(demand)
    
    avg_total_demand = sum(input_data.demand.values()) / (input_data.num_days * input_data.num_slots_per_day) if input_data.demand else 0
    
    for slot, demands in demand_by_slot.items():
        avg_demand = sum(demands) / len(demands) if demands else 0
        max_demand = max(demands) if demands else 0
        
        if avg_demand > avg_total_demand * 1.2:
            peak_periods.append({
                'slot': slot,
                'average_demand': avg_demand,
                'max_demand': max_demand,
                'recommendation': 'Consider scheduling more staff during this time slot'
            })
    
    insights['peak_periods'] = sorted(peak_periods, key=lambda x: x['average_demand'], reverse=True)
    
    # === CAPACITY ANALYSIS (Always available) ===
    total_demand = sum(input_data.demand.values())
    
    capacity_by_role = {}
    for role in input_data.roles:
        eligible_employees = [emp for emp in input_data.employees if role.id in emp.role_eligibility]
        total_available_hours = sum(emp.max_hours_per_week for emp in eligible_employees)
        
        if role.producing:
            potential_output = total_available_hours * role.items_per_hour
            capacity_ratio = potential_output / total_demand if total_demand > 0 else float('inf')
        else:
            potential_output = 0
            capacity_ratio = 0
        
        capacity_by_role[role.id] = {
            'eligible_employees': len(eligible_employees),
            'total_available_hours': total_available_hours,
            'potential_output': potential_output,
            'capacity_ratio': capacity_ratio,
            'is_sufficient': capacity_ratio >= 1.0 if role.producing else True
        }
    
    insights['capacity_analysis'] = capacity_by_role
    
    # === WITHOUT SOLUTION: FEASIBILITY ANALYSIS ===
    if solution is None:
        feasibility_issues = []
        
        total_capacity = sum(data['potential_output'] for data in capacity_by_role.values())
        if total_capacity < total_demand:
            shortfall = total_demand - total_capacity
            feasibility_issues.append({
                'issue': 'Insufficient total capacity',
                'details': f'Need {shortfall:.1f} more items. Total capacity: {total_capacity:.1f}, Total demand: {total_demand:.1f}',
                'severity': 'critical'
            })
        
        for role_id, data in capacity_by_role.items():
            if not data['is_sufficient'] and data['potential_output'] > 0:
                feasibility_issues.append({
                    'issue': f'Insufficient {role_id} capacity',
                    'details': f'Only {data["eligible_employees"]} eligible employees, can produce {data["potential_output"]:.1f} items',
                    'severity': 'high'
                })
        
        for role in input_data.roles:
            if role.min_present > 0:
                eligible_count = sum(1 for emp in input_data.employees if role.id in emp.role_eligibility)
                if eligible_count < role.min_present:
                    feasibility_issues.append({
                        'issue': f'Not enough employees for {role.id}',
                        'details': f'Requires {role.min_present} minimum, only {eligible_count} eligible',
                        'severity': 'critical'
                    })
        
        insights['feasibility_analysis'] = feasibility_issues
        
        hiring_recommendations = []
        for role_id, data in capacity_by_role.items():
            if not data['is_sufficient'] and data['potential_output'] > 0:
                role = next(r for r in input_data.roles if r.id == role_id)
                shortfall = total_demand - data['potential_output']
                if role.items_per_hour > 0:
                    recommended_hires = int(shortfall / (role.items_per_hour * 40) + 1)
                else:
                    recommended_hires = 1
                
                hiring_recommendations.append({
                    'role': role_id,
                    'recommended_hires': recommended_hires,
                    'reason': f'Insufficient capacity to meet demand (shortfall: {shortfall:.1f} items)',
                    'expected_impact': f'Would add {recommended_hires * 40 * role.items_per_hour:.1f} items capacity',
                    'priority': 'critical'
                })
        
        insights['hiring_recommendations'] = sorted(hiring_recommendations,
                                                   key=lambda x: x['recommended_hires'],
                                                   reverse=True)
        
        return insights
    
    # === WITH SOLUTION: COMPREHENSIVE INSIGHTS ===
    
    # Employee utilization
    employee_utilization = []
    for emp in input_data.employees:
        stats = solution['employee_stats'][emp.id]
        utilization_rate = stats['work_hours'] / emp.max_hours_per_week if emp.max_hours_per_week > 0 else 0
        
        employee_utilization.append({
            'employee': emp.id,
            'hours_worked': stats['work_hours'],
            'max_hours': emp.max_hours_per_week,
            'utilization_rate': utilization_rate,
            'hours_deviation': stats['hours_deviation'],
            'status': 'overutilized' if utilization_rate > 0.9 else 
                     'well_utilized' if utilization_rate > 0.6 else
                     'underutilized' if utilization_rate > 0 else 'unused'
        })
    
    insights['employee_utilization'] = sorted(employee_utilization, key=lambda x: x['utilization_rate'], reverse=True)
    
    # Role demand
    role_demand = {}
    for role in input_data.roles:
        eligible_count = sum(1 for emp in input_data.employees if role.id in emp.role_eligibility)
        total_hours_role = sum(
            input_data.slot_len_hour
            for entry in solution['schedule']
            if entry.get('role') == role.id
        )
        
        working_employees = len(set(
            entry['employee']
            for entry in solution['schedule']
            if entry.get('role') == role.id
        ))
        
        if role.producing:
            capacity_utilization = (total_hours_role * role.items_per_hour) / total_demand if total_demand > 0 else 0
        else:
            capacity_utilization = 0
        
        role_demand[role.id] = {
            'eligible_employees': eligible_count,
            'working_employees': working_employees,
            'total_hours_worked': total_hours_role,
            'capacity_utilization': capacity_utilization,
            'is_bottleneck': capacity_utilization < 0.5 and eligible_count < 3
        }
    
    insights['role_demand'] = role_demand
    
    # Hiring recommendations
    hiring_recommendations = []
    
    if solution['unmet_demand']:
        total_unmet = sum(solution['unmet_demand'].values())
        
        for role in input_data.roles:
            if role.producing:
                potential_coverage = role.items_per_hour * input_data.slot_len_hour
                if potential_coverage > 0 and input_data.num_days > 0:
                    recommended_hires = int(total_unmet / (potential_coverage * input_data.num_days) + 0.5)
                else:
                    recommended_hires = 1
                
                if recommended_hires > 0:
                    hiring_recommendations.append({
                        'role': role.id,
                        'recommended_hires': recommended_hires,
                        'reason': f'Unmet demand: {total_unmet:.1f} items total',
                        'expected_impact': f'Could cover {recommended_hires * potential_coverage * input_data.num_days:.1f} additional items',
                        'priority': 'high'
                    })
    
    insights['hiring_recommendations'] = hiring_recommendations
    
    # Coverage gaps
    coverage_gaps = []
    for d in range(input_data.num_days):
        for t in range(input_data.num_slots_per_day):
            employees_working = sum(
                1 for entry in solution['schedule']
                if entry['day'] == d and entry.get('slot') == t
            )
            
            demand = input_data.demand.get((d, t), 0)
            supply = solution['supply'].get((d, t), 0)
            coverage_rate = supply / demand if demand > 0 else 1.0
            
            if coverage_rate < 0.8:
                coverage_gaps.append({
                    'day': d,
                    'slot': t,
                    'employees_working': employees_working,
                    'coverage_rate': coverage_rate,
                    'demand': demand,
                    'supply': supply,
                    'severity': 'critical' if coverage_rate < 0.5 else 'warning'
                })
    
    insights['coverage_gaps'] = sorted(coverage_gaps, key=lambda x: x['coverage_rate'])
    
    # Cost analysis
    total_wage_cost = 0
    cost_by_role = {}
    
    for emp in input_data.employees:
        hours = solution['employee_stats'][emp.id]['work_hours']
        cost = emp.wage * hours
        total_wage_cost += cost
        
        for entry in solution['schedule']:
            if entry['employee'] == emp.id:
                role = entry.get('role', 'unknown')
                if role not in cost_by_role:
                    cost_by_role[role] = 0
                cost_by_role[role] += emp.wage * input_data.slot_len_hour
    
    opportunity_cost = sum(solution['unmet_demand'].values()) * 10
    
    insights['cost_analysis'] = {
        'total_wage_cost': total_wage_cost,
        'cost_by_role': cost_by_role,
        'opportunity_cost_unmet_demand': opportunity_cost,
        'total_cost': total_wage_cost + opportunity_cost,
        'cost_per_item_served': total_wage_cost / sum(solution['supply'].values()) if solution['supply'] else 0
    }
    
    # Workload distribution
    hours_list = [stats['work_hours'] for stats in solution['employee_stats'].values()]
    avg_hours = sum(hours_list) / len(hours_list) if hours_list else 0
    max_hours = max(hours_list) if hours_list else 0
    min_hours = min(hours_list) if hours_list else 0
    
    unused = sum(1 for h in hours_list if h == 0)
    underutilized = sum(1 for emp in input_data.employees 
                       if emp.max_hours_per_week > 0 and 0 < solution['employee_stats'][emp.id]['work_hours'] / emp.max_hours_per_week < 0.5)
    well_utilized = sum(1 for emp in input_data.employees 
                       if emp.max_hours_per_week > 0 and 0.5 <= solution['employee_stats'][emp.id]['work_hours'] / emp.max_hours_per_week <= 0.85)
    overutilized = sum(1 for emp in input_data.employees 
                      if emp.max_hours_per_week > 0 and solution['employee_stats'][emp.id]['work_hours'] / emp.max_hours_per_week > 0.85)
    
    insights['workload_distribution'] = {
        'average_hours': avg_hours,
        'max_hours': max_hours,
        'min_hours': min_hours,
        'range': max_hours - min_hours,
        'unused_employees': unused,
        'underutilized_employees': underutilized,
        'well_utilized_employees': well_utilized,
        'overutilized_employees': overutilized,
        'balance_score': 1 - (max_hours - min_hours) / (max_hours + 1)
    }
    
    return insights


def solve_schedule(input_data: SchedulerInput, time_limit_seconds: int = 60, include_insights: bool = True) -> Tuple[Optional[Dict], str, Optional[Dict]]:
    """Solve the scheduling problem and return solution with insights."""
    scheduler = SchedulerCPSAT(input_data)
    solution = scheduler.solve(time_limit_seconds=time_limit_seconds)
    description = format_solution_description(solution, input_data)
    insights = generate_management_insights(solution, input_data) if include_insights else None
    
    return solution, description, insights


def format_solution_description(solution: Optional[Dict], input_data: SchedulerInput) -> str:
    """Format solution into a human-readable description."""
    lines = []
    lines.append("=" * 60)
    
    if solution is None:
        lines.append("NO SOLUTION FOUND")
        lines.append("=" * 60)
        return "\n".join(lines)
    
    lines.append("SOLUTION FOUND")
    lines.append("=" * 60)
    lines.append(f"Status: {solution['status']}")
    lines.append(f"Objective: {solution['objective_value']:.2f}")
    
    lines.append("\n--- Employee Stats ---")
    for emp_id, stats in solution['employee_stats'].items():
        lines.append(
            f"{emp_id}: {stats['work_hours']:.1f}h worked "
            f"(pref: {stats['pref_hours']}h, dev: {stats['hours_deviation']:.1f}h, "
            f"slots satisfied: {stats['preferences_satisfied']})"
        )
    
    lines.append("\n--- Schedule (first 3 days) ---")
    for entry in sorted(solution['schedule'], key=lambda x: (x['day'], x.get('slot', 0), x['employee'])):
        if entry['day'] < 3:
            lines.append(
                f"  Day {entry['day']}, Slot {entry.get('slot', 'N/A')}: "
                f"{entry['employee']} -> {entry.get('role', 'N/A')}"
            )
    
    if solution['unmet_demand']:
        lines.append("\n--- Unmet Demand ---")
        for (d, t), unmet in sorted(solution['unmet_demand'].items()):
            lines.append(f"  Day {d}, Slot {t}: {unmet:.1f} items")
    else:
        lines.append("\n--- All demand satisfied! ---")
    
    return "\n".join(lines)