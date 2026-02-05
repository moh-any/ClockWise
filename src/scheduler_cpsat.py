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
        
        # Scale factor for converting hours to integer slots
        # (We work in slots internally, convert at output)
        
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
        max_capacity = int(len(data.employees) * max(r.items_per_hour for r in data.roles) * data.slot_len_hour * 100)
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
        
        # Fairness: max and min slots for range-based fairness (avoids integer division issues)
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
                    avail = emp.availability.get((d, t), True)  # Default available
                    if not avail:
                        self.model.Add(self.x[e_idx, d, t] == 0)
        
        # ----- Constraint 2: Role eligibility -----
        for e_idx, emp in enumerate(data.employees):
            for r_idx, role in enumerate(data.roles):
                for d in D:
                    for t in T:
                        # y[e,r,d,t] <= role_elig[e,r]
                        if role.id not in emp.role_eligibility:
                            self.model.Add(self.y[e_idx, r_idx, d, t] == 0)
                        
                        # y[e,r,d,t] <= x[e,d,t]
                        self.model.Add(self.y[e_idx, r_idx, d, t] <= self.x[e_idx, d, t])
            
            # At most one role per slot: sum_r y[e,r,d,t] <= 1
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
                # Define start indicator
                for t in T:
                    if t == 0:
                        # First slot: start if working
                        self.model.Add(self.start[e_idx, d, t] >= self.x[e_idx, d, t])
                    else:
                        # start[e,d,t] >= x[e,d,t] - x[e,d,t-1]
                        self.model.Add(
                            self.start[e_idx, d, t] >= self.x[e_idx, d, t] - self.x[e_idx, d, t - 1]
                        )
                
                # Minimum shift length
                L_min = data.min_shift_length_slots
                for t in T:
                    if t + L_min <= data.num_slots_per_day:
                        # If start, must work at least L_min slots
                        self.model.Add(
                            sum(self.x[e_idx, d, tau] for tau in range(t, t + L_min)) 
                            >= L_min * self.start[e_idx, d, t]
                        )
                
                # Maximum consecutive slots
                max_consec = emp.max_consec_slots
                for t in T:
                    if t + max_consec + 1 <= data.num_slots_per_day:
                        # Cannot work more than max_consec consecutive slots
                        self.model.Add(
                            sum(self.x[e_idx, d, tau] for tau in range(t, t + max_consec + 1)) 
                            <= max_consec
                        )
        
        # ----- Constraint 7: Min rest slots (at day boundary) -----
        min_rest = data.min_rest_slots
        for e_idx in E:
            for d in range(data.num_days - 1):
                # If working last slot of day d, cannot work first min_rest slots of day d+1
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
        
        # Shift availability
        for e_idx, emp in enumerate(data.employees):
            for k_idx, shift in enumerate(data.shifts):
                # Check if employee is available for entire shift
                available = all(
                    emp.availability.get((shift.day, t), True) 
                    for t in range(shift.start_slot, shift.end_slot)
                )
                if not available:
                    self.model.Add(self.z[e_idx, k_idx] == 0)
        
        # One shift per employee per day
        for e_idx in E:
            for d in D:
                shifts_on_day = [k for k, s in enumerate(data.shifts) if s.day == d]
                if shifts_on_day:
                    self.model.Add(sum(self.z[e_idx, k] for k in shifts_on_day) <= 1)
        
        # Max hours per week
        for e_idx, emp in enumerate(data.employees):
            max_slots = int(emp.max_hours_per_week / data.slot_len_hour)
            self.model.Add(
                sum(self.z[e_idx, k] * data.shifts[k].length_slots for k in K) <= max_slots
            )
    
    def _add_supply_constraints(self):
        """Add production capacity and supply constraints."""
        E, R, D, T = self._get_sets()
        data = self.data
        
        # Scale factor for floating point -> integer (x100)
        SCALE = 100
        
        # ----- Step 4a: Compute capacity per role -----
        for r_idx, role in enumerate(data.roles):
            items_scaled = int(role.items_per_hour * data.slot_len_hour * SCALE)
            for d in D:
                for t in T:
                    if not data.fixed_shifts:
                        # capacity = sum_e y[e,r,d,t] * items_r * slot_len
                        self.model.Add(
                            self.capacity[r_idx, d, t] == 
                            sum(self.y[e, r_idx, d, t] * items_scaled for e in E)
                        )
                    else:
                        # For fixed shifts, capacity is based on z variables
                        # Simplified: count eligible employees assigned to overlapping shifts
                        overlapping_shifts = [
                            k for k, s in enumerate(data.shifts) 
                            if s.day == d and s.start_slot <= t < s.end_slot
                        ]
                        eligible = [e for e, emp in enumerate(data.employees) if role.id in emp.role_eligibility]
                        self.model.Add(
                            self.capacity[r_idx, d, t] == 
                            sum(self.z[e, k] * items_scaled for e in eligible for k in overlapping_shifts)
                        )
        
        # ----- Step 4b & 4c: Supply from independent roles and chains -----
        independent_roles = [r for r, role in enumerate(data.roles) if role.is_independent]
        
        for d in D:
            for t in T:
                supply_terms = []
                
                # Independent roles contribute directly
                for r_idx in independent_roles:
                    supply_terms.append(self.capacity[r_idx, d, t])
                
                # Chain output (bottleneck)
                for c_idx, chain in enumerate(data.chains):
                    chain_role_indices = [self.role_idx[rid] for rid in chain.roles if rid in self.role_idx]
                    
                    # chain_output <= capacity of each role in chain
                    for r_idx in chain_role_indices:
                        self.model.Add(
                            self.chain_output[c_idx, d, t] <= self.capacity[r_idx, d, t]
                        )
                    
                    # Add to supply with contribution factor
                    contrib_scaled = int(chain.contrib_factor * SCALE)
                    # chain_output is already scaled, so we divide by SCALE to avoid double-scaling
                    supply_terms.append(self.chain_output[c_idx, d, t] * chain.contrib_factor)
                
                # Total supply
                if supply_terms:
                    self.model.Add(self.supply[d, t] == sum(supply_terms))
                else:
                    self.model.Add(self.supply[d, t] == 0)
        
        # ----- Step 4e: Demand satisfaction -----
        for d in D:
            for t in T:
                demand_scaled = int(data.demand.get((d, t), 0) * SCALE)
                if data.meet_all_demand:
                    # Hard constraint: supply must meet demand exactly
                    self.model.Add(self.supply[d, t] >= demand_scaled)
                    # Force unmet to zero
                    self.model.Add(self.v[d, t] == 0)
                else:
                    # Soft constraint: supply + unmet >= demand (unmet penalized in objective)
                    self.model.Add(self.supply[d, t] + self.v[d, t] >= demand_scaled)
    
    def _add_auxiliary_constraints(self):
        """Add auxiliary variable definitions for objective."""
        E, R, D, T = self._get_sets()
        data = self.data
        
        # Work slots per employee
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
        
        # Hours deviation (in slots)
        for e_idx, emp in enumerate(data.employees):
            pref_slots = int(emp.pref_hours / data.slot_len_hour)
            # hours_dev >= work_slots - pref_slots
            self.model.Add(self.hours_dev[e_idx] >= self.work_slots[e_idx] - pref_slots)
            # hours_dev >= pref_slots - work_slots
            self.model.Add(self.hours_dev[e_idx] >= pref_slots - self.work_slots[e_idx])
        
        # Preference satisfaction (slot-based only)
        if not data.fixed_shifts:
            for e_idx, emp in enumerate(data.employees):
                for d in D:
                    for t in T:
                        pref = 1 if emp.slot_preferences.get((d, t), False) else 0
                        if pref:
                            # pref_sat <= x (can only be satisfied if scheduled)
                            self.model.Add(self.pref_sat[e_idx, d, t] <= self.x[e_idx, d, t])
                            # pref_sat >= x + pref - 1 = x (since pref=1)
                            self.model.Add(self.pref_sat[e_idx, d, t] >= self.x[e_idx, d, t])
                        else:
                            # No preference, satisfaction is 0
                            self.model.Add(self.pref_sat[e_idx, d, t] == 0)
        
        # Fairness: range-based (max - min work slots)
        # This avoids integer division issues with avg_slots * |E| = sum
        for e_idx in E:
            self.model.Add(self.max_work_slots >= self.work_slots[e_idx])
            self.model.Add(self.min_work_slots <= self.work_slots[e_idx])
        
        # fairness_dev = max - min (minimizing this spreads work evenly)
        self.model.Add(self.fairness_dev >= self.max_work_slots - self.min_work_slots)
    
    def _set_objective(self):
        """Set the objective function."""
        E, R, D, T = self._get_sets()
        data = self.data
        
        objective_terms = []
        
        # W_wage * sum(wage[e] * work_hours[e])
        # work_hours = work_slots * slot_len_hour, wage is per hour
        for e_idx, emp in enumerate(data.employees):
            wage_per_slot = int(emp.wage * data.slot_len_hour * 100)  # Scale by 100
            objective_terms.append(data.w_wage * wage_per_slot * self.work_slots[e_idx])
        
        # W_unmet * sum(unmet[d,t])
        for d in D:
            for t in T:
                objective_terms.append(data.w_unmet * self.v[d, t])
        
        # W_hours * sum(hours_dev[e])
        for e_idx in E:
            objective_terms.append(data.w_hours * self.hours_dev[e_idx])
        
        # -W_slot * sum(pref_sat[e,d,t]) (negative because we maximize satisfaction)
        if not data.fixed_shifts:
            for e_idx in E:
                for d in D:
                    for t in T:
                        objective_terms.append(-data.w_slot * self.pref_sat[e_idx, d, t])
        
        # W_fair * fairness_dev
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
        
        # Extract schedule
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
        
        # Extract unmet demand
        for d in D:
            for t in T:
                unmet = solver.Value(self.v[d, t]) / 100  # Unscale
                if unmet > 0:
                    solution['unmet_demand'][(d, t)] = unmet
        
        # Extract employee stats
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
        
        # Extract supply
        for d in D:
            for t in T:
                solution['supply'][(d, t)] = solver.Value(self.supply[d, t]) / 100  # Unscale
        
        return solution


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

def create_sample_data() -> SchedulerInput:
    """Create sample input data for testing."""
    
    # Define roles
    # Note: min_present=0 for roles that are optional (covered by demand instead)
    # Only production roles contribute to supply; cashier is non-producing
    roles = [
        Role(id='cashier', producing=False, items_per_hour=0, min_present=0, is_independent=True),
        Role(id='prep', producing=True, items_per_hour=20, min_present=0, is_independent=False),
        Role(id='cook', producing=True, items_per_hour=15, min_present=0, is_independent=False),
        Role(id='server', producing=True, items_per_hour=30, min_present=0, is_independent=True),
    ]
    
    # Define production chain: prep -> cook
    chains = [
        ProductionChain(id='kitchen', roles=['prep', 'cook'], contrib_factor=1.0)
    ]
    
    # Mark chain roles as non-independent
    for role in roles:
        if role.id in ['prep', 'cook']:
            role.is_independent = False
    
    # Define employees with broader role eligibility for feasibility
    employees = [
        Employee(
            id='alice',
            wage=15.0,
            max_hours_per_week=40,
            max_consec_slots=8,
            pref_hours=32,
            role_eligibility={'cashier', 'server', 'prep'},  # Added prep
            availability={(d, t): True for d in range(7) for t in range(12)},
            slot_preferences={(0, 0): True, (0, 1): True, (1, 0): True}
        ),
        Employee(
            id='bob',
            wage=18.0,
            max_hours_per_week=40,
            max_consec_slots=8,
            pref_hours=40,
            role_eligibility={'prep', 'cook', 'server'},  # Added server
            availability={(d, t): True for d in range(7) for t in range(12)},
            slot_preferences={(0, 4): True, (0, 5): True}
        ),
        Employee(
            id='charlie',
            wage=16.0,
            max_hours_per_week=40,  # Increased from 30
            max_consec_slots=8,     # Increased from 6
            pref_hours=32,          # Adjusted
            role_eligibility={'cashier', 'prep', 'server', 'cook'},  # Added cook
            availability={(d, t): True for d in range(7) for t in range(12)},  # Now available all days
            slot_preferences={(2, 2): True, (2, 3): True}
        ),
        Employee(
            id='diana',
            wage=17.0,
            max_hours_per_week=40,
            max_consec_slots=8,
            pref_hours=36,
            role_eligibility={'cook', 'server', 'cashier'},  # Added cashier
            availability={(d, t): True for d in range(7) for t in range(12)},
            slot_preferences={(3, 0): True, (4, 0): True}
        ),
        Employee(
            id='diana2',
            wage=17.0,
            max_hours_per_week=40,
            max_consec_slots=8,
            pref_hours=36,
            role_eligibility={'cook', 'server', 'cashier'},  # Added cashier
            availability={(d, t): True for d in range(7) for t in range(12)},
            slot_preferences={(3, 0): True, (4, 0): True}
        ),
        Employee(
            id='diana3',
            wage=17.0,
            max_hours_per_week=40,
            max_consec_slots=8,
            pref_hours=36,
            role_eligibility={'cook', 'server', 'cashier'},  # Added cashier
            availability={(d, t): True for d in range(7) for t in range(12)},
            slot_preferences={(3, 0): True, (4, 0): True}
        ),
        Employee(
            id='diana4',
            wage=17.0,
            max_hours_per_week=40,
            max_consec_slots=8,
            pref_hours=36,
            role_eligibility={'cook', 'server', 'cashier'},  # Added cashier
            availability={(d, t): True for d in range(7) for t in range(12)},
            slot_preferences={(3, 0): True, (4, 0): True}
        ),
        Employee(
            id='diana5',
            wage=17.0,
            max_hours_per_week=40,
            max_consec_slots=8,
            pref_hours=36,
            role_eligibility={'cook', 'server', 'cashier'},  # Added cashier
            availability={(d, t): True for d in range(7) for t in range(12)},
            slot_preferences={(3, 0): True, (4, 0): True}
        ),
        Employee(
            id='diana6',
            wage=17.0,
            max_hours_per_week=40,
            max_consec_slots=8,
            pref_hours=36,
            role_eligibility={'cook', 'server', 'cashier'},  # Added cashier
            availability={(d, t): True for d in range(7) for t in range(12)},
            slot_preferences={(3, 0): True, (4, 0): True}
        ),
        Employee(
            id='diana7',
            wage=17.0,
            max_hours_per_week=40,
            max_consec_slots=8,
            pref_hours=36,
            role_eligibility={'cook', 'server', 'cashier'},  # Added cashier
            availability={(d, t): True for d in range(7) for t in range(12)},
            slot_preferences={(3, 0): True, (4, 0): True}
        ),
        Employee(
            id='diana8',
            wage=17.0,
            max_hours_per_week=40,
            max_consec_slots=8,
            pref_hours=36,
            role_eligibility={'cook', 'server', 'cashier'},  # Added cashier
            availability={(d, t): True for d in range(7) for t in range(12)},
            slot_preferences={(3, 0): True, (4, 0): True}
        ),
        Employee(
            id='diana9',
            wage=17.0,
            max_hours_per_week=40,
            max_consec_slots=8,
            pref_hours=36,
            role_eligibility={'cook', 'server', 'cashier'},  # Added cashier
            availability={(d, t): True for d in range(7) for t in range(12)},
            slot_preferences={(3, 0): True, (4, 0): True}
        ),
        Employee(
            id='diana10',
            wage=17.0,
            max_hours_per_week=40,
            max_consec_slots=8,
            pref_hours=36,
            role_eligibility={'cook', 'server', 'cashier'},  # Added cashier
            availability={(d, t): True for d in range(7) for t in range(12)},
            slot_preferences={(3, 0): True, (4, 0): True}
        ),
        Employee(
            id='diana11',
            wage=17.0,
            max_hours_per_week=40,
            max_consec_slots=8,
            pref_hours=36,
            role_eligibility={'cook', 'server', 'cashier'},  # Added cashier
            availability={(d, t): True for d in range(7) for t in range(12)},
            slot_preferences={(3, 0): True, (4, 0): True}
        ),
        Employee(
            id='diana12',
            wage=17.0,
            max_hours_per_week=40,
            max_consec_slots=8,
            pref_hours=36,
            role_eligibility={'cook', 'server', 'cashier'},  # Added cashier
            availability={(d, t): True for d in range(7) for t in range(12)},
            slot_preferences={(3, 0): True, (4, 0): True}
        ),
        Employee(
            id='diana13',
            wage=17.0,
            max_hours_per_week=40,
            max_consec_slots=8,
            pref_hours=36,
            role_eligibility={'cook', 'server', 'cashier'},  # Added cashier
            availability={(d, t): True for d in range(7) for t in range(12)},
            slot_preferences={(3, 0): True, (4, 0): True}
        ),
        Employee(
            id='diana14',
            wage=17.0,
            max_hours_per_week=40,
            max_consec_slots=8,
            pref_hours=36,
            role_eligibility={'cook', 'server', 'cashier'},  # Added cashier
            availability={(d, t): True for d in range(7) for t in range(12)},
            slot_preferences={(3, 0): True, (4, 0): True}
        ),
        Employee(
            id='diana15',
            wage=17.0,
            max_hours_per_week=40,
            max_consec_slots=8,
            pref_hours=36,
            role_eligibility={'cook', 'server', 'cashier'},  # Added cashier
            availability={(d, t): True for d in range(7) for t in range(12)},
            slot_preferences={(3, 0): True, (4, 0): True}
        ),
        Employee(
            id='diana16',
            wage=17.0,
            max_hours_per_week=40,
            max_consec_slots=8,
            pref_hours=36,
            role_eligibility={'cook', 'server', 'cashier'},  # Added cashier
            availability={(d, t): True for d in range(7) for t in range(12)},
            slot_preferences={(3, 0): True, (4, 0): True}
        ),
        Employee(
            id='diana17',
            wage=17.0,
            max_hours_per_week=40,
            max_consec_slots=8,
            pref_hours=36,
            role_eligibility={'cook', 'server', 'cashier'},  # Added cashier
            availability={(d, t): True for d in range(7) for t in range(12)},
            slot_preferences={(3, 0): True, (4, 0): True}
        ),
        Employee(
            id='diana18',
            wage=17.0,
            max_hours_per_week=40,
            max_consec_slots=8,
            pref_hours=36,
            role_eligibility={'cook', 'server', 'cashier'},  # Added cashier
            availability={(d, t): True for d in range(7) for t in range(12)},
            slot_preferences={(3, 0): True, (4, 0): True}
        ),
        Employee(
            id='diana19',
            wage=17.0,
            max_hours_per_week=40,
            max_consec_slots=8,
            pref_hours=36,
            role_eligibility={'cook', 'server', 'cashier'},  # Added cashier
            availability={(d, t): True for d in range(7) for t in range(12)},
            slot_preferences={(3, 0): True, (4, 0): True}
        ),
        Employee(
            id='diana20',
            wage=17.0,
            max_hours_per_week=40,
            max_consec_slots=8,
            pref_hours=36,
            role_eligibility={'cook', 'server', 'cashier'},  # Added cashier
            availability={(d, t): True for d in range(7) for t in range(12)},
            slot_preferences={(3, 0): True, (4, 0): True}
        ),
        Employee(
            id='diana21',
            wage=17.0,
            max_hours_per_week=40,
            max_consec_slots=8,
            pref_hours=36,
            role_eligibility={'cook', 'server', 'cashier'},  # Added cashier
            availability={(d, t): True for d in range(7) for t in range(12)},
            slot_preferences={(3, 0): True, (4, 0): True}
        ),
        Employee(
            id='diana22',
            wage=17.0,
            max_hours_per_week=40,
            max_consec_slots=8,
            pref_hours=36,
            role_eligibility={'cook', 'server', 'cashier'},  # Added cashier
            availability={(d, t): True for d in range(7) for t in range(12)},
            slot_preferences={(3, 0): True, (4, 0): True}
        ),
        Employee(
            id='diana23',
            wage=17.0,
            max_hours_per_week=40,
            max_consec_slots=8,
            pref_hours=36,
            role_eligibility={'cook', 'server', 'cashier'},  # Added cashier
            availability={(d, t): True for d in range(7) for t in range(12)},
            slot_preferences={(3, 0): True, (4, 0): True}
        ),
        Employee(
            id='diana24',
            wage=17.0,
            max_hours_per_week=40,
            max_consec_slots=8,
            pref_hours=36,
            role_eligibility={'cook', 'server', 'cashier'},  # Added cashier
            availability={(d, t): True for d in range(7) for t in range(12)},
            slot_preferences={(3, 0): True, (4, 0): True}
        ),
    ]
    
    # Define demand (items per slot)
    demand = {}
    for d in range(7):
        for t in range(12):
            # Higher demand during lunch (slots 4-6) and dinner (slots 8-10)
            if 4 <= t <= 6 or 8 <= t <= 10:
                demand[(d, t)] = 300.0
            else:
                demand[(d, t)] = 150.0
    
    return SchedulerInput(
        employees=employees,
        roles=roles,
        num_days=7,
        num_slots_per_day=12,
        chains=chains,
        slot_len_hour=1.0,
        min_rest_slots=1,
        min_shift_length_slots=3,
        demand=demand,
        w_unmet=10000,
        w_wage=100,
        w_hours=50,
        w_fair=10,
        w_slot=1,
        fixed_shifts=False,
        meet_all_demand=True  # Hard constraint
    )


def main():
    print("=" * 60)
    print("SCHEDULER CP-SAT MODEL")
    print("=" * 60)
    
    # Create sample data
    data = create_sample_data()
    print(f"\nEmployees: {[e.id for e in data.employees]}")
    print(f"Roles: {[r.id for r in data.roles]}")
    print(f"Days: {data.num_days}, Slots/day: {data.num_slots_per_day}")
    print(f"Production chains: {[c.id for c in data.chains]}")
    
    # Build and solve model
    print("\nBuilding model...")
    scheduler = SchedulerCPSAT(data)
    
    print("Solving...")
    solution = scheduler.solve(time_limit_seconds=30)
    
    if solution:
        print("\n" + "=" * 60)
        print("SOLUTION FOUND")
        print("=" * 60)
        print(f"Status: {solution['status']}")
        print(f"Objective: {solution['objective_value']:.2f}")
        
        print("\n--- Employee Stats ---")
        for emp_id, stats in solution['employee_stats'].items():
            print(f"{emp_id}: {stats['work_hours']:.1f}h worked "
                  f"(pref: {stats['pref_hours']}h, dev: {stats['hours_deviation']:.1f}h, "
                  f"slots satisfied: {stats['preferences_satisfied']})")
        
        print("\n--- Schedule (first 3 days) ---")
        for entry in sorted(solution['schedule'], key=lambda x: (x['day'], x['slot'], x['employee'])):
            if entry['day'] < 3:
                print(f"  Day {entry['day']}, Slot {entry['slot']}: "
                      f"{entry['employee']} -> {entry.get('role', 'N/A')}")
        
        if solution['unmet_demand']:
            print("\n--- Unmet Demand ---")
            for (d, t), unmet in sorted(solution['unmet_demand'].items()):
                print(f"  Day {d}, Slot {t}: {unmet:.1f} items")
        else:
            print("\n--- All demand satisfied! ---")
    else:
        print("No solution found.")


if __name__ == '__main__':
    main()
