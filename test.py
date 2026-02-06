"""
Complete Test Suite for Restaurant Demand Prediction & Scheduling API v3.0
===========================================================================

Tests all endpoints and features:
1. Health check
2. Model info
3. Demand prediction with minimal data
4. Demand prediction with full data
5. Schedule generation (fixed shifts)
6. Schedule generation (slot-based)
7. Error handling
8. Edge cases

Run with: pytest test_api.py -v
Or: python test_api.py
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List
import time

# Configuration
BASE_URL = "http://localhost:8000"
TIMEOUT = 120  # 2 minutes timeout for predictions


class Colors:
    """ANSI color codes for pretty printing"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_header(text: str):
    """Print a formatted header"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'=' * 80}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text.center(80)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'=' * 80}{Colors.END}\n")


def print_success(text: str):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")


def print_error(text: str):
    """Print error message"""
    print(f"{Colors.RED}✗ {text}{Colors.END}")


def print_warning(text: str):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")


def print_info(text: str):
    """Print info message"""
    print(f"{Colors.BLUE}ℹ {text}{Colors.END}")


# ============================================================================
# TEST DATA GENERATORS
# ============================================================================

def generate_historical_orders(start_date: str, num_days: int = 30) -> List[Dict]:
    """Generate realistic historical order data"""
    orders = []
    start = datetime.strptime(start_date, "%Y-%m-%d")
    
    for day in range(num_days):
        current_date = start + timedelta(days=day)
        
        # Different order patterns by day of week
        is_weekend = current_date.weekday() >= 5
        
        # Generate orders throughout the day
        for hour in range(8, 24):  # 8 AM to 11 PM
            # Peak hours: 12-14 (lunch), 18-21 (dinner)
            if 12 <= hour <= 14 or 18 <= hour <= 21:
                num_orders = 8 if not is_weekend else 12
            else:
                num_orders = 3 if not is_weekend else 5
            
            for _ in range(num_orders):
                order_time = current_date.replace(
                    hour=hour,
                    minute=int((60 / num_orders) * _),
                    second=0
                )
                
                orders.append({
                    "time": order_time.isoformat(),
                    "items": int(2 + (3 * (1.5 if is_weekend else 1))),
                    "status": "completed",
                    "total_amount": round(15 + (25 * (1.5 if is_weekend else 1)), 2),
                    "discount_amount": 0.0
                })
    
    return orders


def generate_minimal_request(prediction_start: str = None) -> Dict:
    """Generate minimal valid request for testing"""
    if prediction_start is None:
        prediction_start = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    
    history_start = (datetime.strptime(prediction_start, "%Y-%m-%d") - timedelta(days=30)).strftime("%Y-%m-%d")
    
    return {
        "demand_input": {
            "place": {
                "place_id": "pl_test_001",
                "place_name": "Test Pizzeria",
                "type": "restaurant",
                "latitude": 55.6761,
                "longitude": 12.5683,
                "waiting_time": 30,
                "receiving_phone": True,
                "delivery": True,
                "opening_hours": {
                    "monday": {"from": "10:00", "to": "22:00"},
                    "tuesday": {"from": "10:00", "to": "22:00"},
                    "wednesday": {"from": "10:00", "to": "22:00"},
                    "thursday": {"from": "10:00", "to": "22:00"},
                    "friday": {"from": "10:00", "to": "23:00"},
                    "saturday": {"from": "11:00", "to": "23:00"},
                    "sunday": {"closed": True}
                },
                "fixed_shifts": True,
                "number_of_shifts_per_day": 2,
                "shift_times": ["10:00-16:00", "16:00-22:00"],
                "rating": 4.2,
                "accepting_orders": True
            },
            "orders": generate_historical_orders(history_start, 30),
            "campaigns": [],
            "prediction_start_date": prediction_start,
            "prediction_days": 7
        },
        "schedule_input": {
            "roles": [
                {
                    "role_id": "chef",
                    "role_name": "Chef",
                    "producing": True,
                    "items_per_employee_per_hour": 20.0,
                    "min_present": 1,
                    "is_independent": True
                },
                {
                    "role_id": "cashier",
                    "role_name": "Cashier",
                    "producing": False,
                    "items_per_employee_per_hour": None,
                    "min_present": 1,
                    "is_independent": True
                }
            ],
            "employees": [
                {
                    "employee_id": "emp_alice",
                    "role_ids": ["chef"],
                    "available_days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
                    "preferred_days": ["monday", "wednesday", "friday"],
                    "available_hours": {
                        "monday": {"from": "09:00", "to": "22:00"},
                        "tuesday": {"from": "09:00", "to": "22:00"},
                        "wednesday": {"from": "09:00", "to": "22:00"},
                        "thursday": {"from": "09:00", "to": "22:00"},
                        "friday": {"from": "09:00", "to": "23:00"}
                    },
                    "preferred_hours": {
                        "monday": {"from": "10:00", "to": "18:00"},
                        "wednesday": {"from": "10:00", "to": "18:00"},
                        "friday": {"from": "10:00", "to": "18:00"}
                    },
                    "hourly_wage": 25.0,
                    "max_hours_per_week": 40.0,
                    "max_consec_slots": 8,
                    "pref_hours": 35.0
                },
                {
                    "employee_id": "emp_bob",
                    "role_ids": ["cashier"],
                    "available_days": ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday"],
                    "preferred_days": ["saturday"],
                    "available_hours": {
                        "monday": {"from": "10:00", "to": "22:00"},
                        "tuesday": {"from": "10:00", "to": "22:00"},
                        "wednesday": {"from": "10:00", "to": "22:00"},
                        "thursday": {"from": "10:00", "to": "22:00"},
                        "friday": {"from": "10:00", "to": "23:00"},
                        "saturday": {"from": "11:00", "to": "23:00"}
                    },
                    "preferred_hours": {
                        "saturday": {"from": "12:00", "to": "20:00"}
                    },
                    "hourly_wage": 20.0,
                    "max_hours_per_week": 35.0,
                    "max_consec_slots": 6,
                    "pref_hours": 30.0
                }
            ],
            "production_chains": [],
            "scheduler_config": {
                "slot_len_hour": 1.0,
                "min_rest_slots": 2,
                "min_shift_length_slots": 2,
                "meet_all_demand": False
            }
        }
    }


def generate_full_request_with_chains() -> Dict:
    """Generate comprehensive request with production chains"""
    prediction_start = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    history_start = (datetime.strptime(prediction_start, "%Y-%m-%d") - timedelta(days=30)).strftime("%Y-%m-%d")
    
    return {
        "demand_input": {
            "place": {
                "place_id": "pl_advanced_001",
                "place_name": "Advanced Restaurant",
                "type": "restaurant",
                "latitude": 55.6761,
                "longitude": 12.5683,
                "waiting_time": 25,
                "receiving_phone": True,
                "delivery": True,
                "opening_hours": {
                    "monday": {"from": "11:00", "to": "22:00"},
                    "tuesday": {"from": "11:00", "to": "22:00"},
                    "wednesday": {"from": "11:00", "to": "22:00"},
                    "thursday": {"from": "11:00", "to": "22:00"},
                    "friday": {"from": "11:00", "to": "23:00"},
                    "saturday": {"from": "12:00", "to": "23:00"},
                    "sunday": {"from": "12:00", "to": "21:00"}
                },
                "fixed_shifts": False,  # Slot-based scheduling
                "number_of_shifts_per_day": 3,
                "shift_times": ["11:00-16:00", "16:00-20:00", "20:00-23:00"],
                "rating": 4.6,
                "accepting_orders": True
            },
            "orders": generate_historical_orders(history_start, 45),
            "campaigns": [
                {
                    "start_time": prediction_start + "T00:00:00",
                    "end_time": (datetime.strptime(prediction_start, "%Y-%m-%d") + timedelta(days=3)).strftime("%Y-%m-%d") + "T23:59:59",
                    "items_included": ["pizza_special", "pasta_combo"],
                    "discount": 20.0
                }
            ],
            "prediction_start_date": prediction_start,
            "prediction_days": 7
        },
        "schedule_input": {
            "roles": [
                {
                    "role_id": "prep",
                    "role_name": "Prep Cook",
                    "producing": True,
                    "items_per_employee_per_hour": 25.0,
                    "min_present": 1,
                    "is_independent": False
                },
                {
                    "role_id": "cook",
                    "role_name": "Main Cook",
                    "producing": True,
                    "items_per_employee_per_hour": 20.0,
                    "min_present": 1,
                    "is_independent": False
                },
                {
                    "role_id": "server",
                    "role_name": "Server",
                    "producing": True,
                    "items_per_employee_per_hour": 30.0,
                    "min_present": 1,
                    "is_independent": True
                },
                {
                    "role_id": "cashier",
                    "role_name": "Cashier",
                    "producing": False,
                    "items_per_employee_per_hour": None,
                    "min_present": 1,
                    "is_independent": True
                }
            ],
            "employees": [
                {
                    "employee_id": "emp_001",
                    "role_ids": ["prep", "cook"],
                    "available_days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
                    "preferred_days": ["monday", "wednesday", "friday"],
                    "available_hours": {
                        "monday": {"from": "10:00", "to": "22:00"},
                        "tuesday": {"from": "10:00", "to": "22:00"},
                        "wednesday": {"from": "10:00", "to": "22:00"},
                        "thursday": {"from": "10:00", "to": "22:00"},
                        "friday": {"from": "10:00", "to": "23:00"}
                    },
                    "preferred_hours": {
                        "monday": {"from": "11:00", "to": "19:00"},
                        "wednesday": {"from": "11:00", "to": "19:00"},
                        "friday": {"from": "11:00", "to": "19:00"}
                    },
                    "hourly_wage": 26.0,
                    "max_hours_per_week": 40.0,
                    "max_consec_slots": 8,
                    "pref_hours": 32.0
                },
                {
                    "employee_id": "emp_002",
                    "role_ids": ["server", "cashier"],
                    "available_days": ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"],
                    "preferred_days": ["saturday", "sunday"],
                    "available_hours": {
                        "monday": {"from": "11:00", "to": "22:00"},
                        "tuesday": {"from": "11:00", "to": "22:00"},
                        "wednesday": {"from": "11:00", "to": "22:00"},
                        "thursday": {"from": "11:00", "to": "22:00"},
                        "friday": {"from": "11:00", "to": "23:00"},
                        "saturday": {"from": "12:00", "to": "23:00"},
                        "sunday": {"from": "12:00", "to": "21:00"}
                    },
                    "preferred_hours": {
                        "saturday": {"from": "14:00", "to": "22:00"},
                        "sunday": {"from": "14:00", "to": "20:00"}
                    },
                    "hourly_wage": 22.0,
                    "max_hours_per_week": 35.0,
                    "max_consec_slots": 7,
                    "pref_hours": 28.0
                },
                {
                    "employee_id": "emp_003",
                    "role_ids": ["prep"],
                    "available_days": ["thursday", "friday", "saturday", "sunday"],
                    "preferred_days": ["friday", "saturday"],
                    "available_hours": {
                        "thursday": {"from": "16:00", "to": "22:00"},
                        "friday": {"from": "16:00", "to": "23:00"},
                        "saturday": {"from": "12:00", "to": "23:00"},
                        "sunday": {"from": "12:00", "to": "21:00"}
                    },
                    "preferred_hours": {
                        "friday": {"from": "17:00", "to": "23:00"},
                        "saturday": {"from": "15:00", "to": "23:00"}
                    },
                    "hourly_wage": 24.0,
                    "max_hours_per_week": 25.0,
                    "max_consec_slots": 6,
                    "pref_hours": 20.0
                }
            ],
            "production_chains": [
                {
                    "chain_id": "kitchen_chain",
                    "role_ids": ["prep", "cook"],
                    "contrib_factor": 1.0
                }
            ],
            "scheduler_config": {
                "slot_len_hour": 1.0,
                "min_rest_slots": 2,
                "min_shift_length_slots": 3,
                "meet_all_demand": False
            }
        }
    }


# ============================================================================
# TEST FUNCTIONS
# ============================================================================

def test_health_check():
    """Test 1: Health Check Endpoint"""
    print_header("TEST 1: Health Check")
    
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Status: {response.status_code}")
            print_info(f"Response: {json.dumps(data, indent=2)}")
            
            # Validate response structure
            assert "status" in data, "Missing 'status' field"
            assert data["status"] == "online", "API not online"
            assert "model_loaded" in data, "Missing 'model_loaded' field"
            assert "scheduler_available" in data, "Missing 'scheduler_available' field"
            assert "version" in data, "Missing 'version' field"
            
            if data["model_loaded"]:
                print_success("Model is loaded ✓")
            else:
                print_warning("Model is NOT loaded")
            
            if data["scheduler_available"]:
                print_success("Scheduler is available ✓")
            else:
                print_warning("Scheduler is NOT available")
            
            return True
        else:
            print_error(f"Failed with status code: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Exception: {str(e)}")
        return False


def test_model_info():
    """Test 2: Model Info Endpoint"""
    print_header("TEST 2: Model Info")
    
    try:
        response = requests.get(f"{BASE_URL}/model/info", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Status: {response.status_code}")
            print_info(f"Model Type: {data.get('model_type', 'N/A')}")
            print_info(f"Training Size: {data.get('training_size', 'N/A')}")
            print_info(f"Test Size: {data.get('test_size', 'N/A')}")
            
            if 'features' in data:
                print_info(f"Number of Features: {len(data['features'])}")
            
            return True
        else:
            print_error(f"Failed with status code: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Exception: {str(e)}")
        return False


def test_example_request():
    """Test 3: Example Request Endpoint"""
    print_header("TEST 3: Example Request")
    
    try:
        response = requests.get(f"{BASE_URL}/example-request", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Status: {response.status_code}")
            print_info(f"Has demand_input: {'demand_input' in data}")
            print_info(f"Has schedule_input: {'schedule_input' in data}")
            
            # Validate structure
            assert "demand_input" in data, "Missing demand_input"
            assert "schedule_input" in data, "Missing schedule_input"
            assert "place" in data["demand_input"], "Missing place in demand_input"
            assert "roles" in data["schedule_input"], "Missing roles in schedule_input"
            
            print_success("Example request structure is valid ✓")
            return True
        else:
            print_error(f"Failed with status code: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Exception: {str(e)}")
        return False


def test_minimal_prediction():
    """Test 4: Minimal Prediction Request"""
    print_header("TEST 4: Minimal Prediction (Demand Only)")
    
    try:
        request_data = generate_minimal_request()
        
        print_info(f"Prediction Start: {request_data['demand_input']['prediction_start_date']}")
        print_info(f"Prediction Days: {request_data['demand_input']['prediction_days']}")
        print_info(f"Historical Orders: {len(request_data['demand_input']['orders'])}")
        print_info(f"Employees: {len(request_data['schedule_input']['employees'])}")
        
        print_info("Sending request... (this may take 30-60 seconds)")
        start_time = time.time()
        
        response = requests.post(
            f"{BASE_URL}/predict",
            json=request_data,
            timeout=TIMEOUT
        )
        
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Status: {response.status_code} (took {elapsed:.2f}s)")
            
            # Validate demand output
            assert "demand_output" in data, "Missing demand_output"
            assert "schedule_output" in data, "Missing schedule_output"
            
            demand = data["demand_output"]
            print_info(f"Restaurant: {demand['restaurant_name']}")
            print_info(f"Prediction Period: {demand['prediction_period']}")
            print_info(f"Days in prediction: {len(demand['days'])}")
            
            # Check first day predictions
            if demand['days']:
                first_day = demand['days'][0]
                print_info(f"First day: {first_day['day_name']} ({first_day['date']})")
                print_info(f"Hours predicted: {len(first_day['hours'])}")
                
                # Show sample predictions
                if first_day['hours']:
                    print_info("Sample predictions:")
                    for hour_pred in first_day['hours'][:5]:  # First 5 hours
                        print(f"    Hour {hour_pred['hour']:2d}: {hour_pred['order_count']:3d} orders, {hour_pred['item_count']:3d} items")
            
            # Check schedule output
            schedule = data["schedule_output"]
            total_shifts = sum(len(shifts) for shifts in schedule.values())
            print_info(f"Total shifts scheduled: {total_shifts}")
            
            # Show schedule for first working day
            for day in ["monday", "tuesday", "wednesday"]:
                if schedule[day]:
                    print_info(f"Schedule for {day}: {len(schedule[day])} shifts")
                    for shift in schedule[day][:2]:  # First 2 shifts
                        for time_range, employees in shift.items():
                            print(f"    {time_range}: {', '.join(employees)}")
                    break
            
            print_success("Prediction completed successfully ✓")
            return True
        else:
            print_error(f"Failed with status code: {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print_error(f"Exception: {str(e)}")
        return False


def test_full_prediction_with_chains():
    """Test 5: Full Prediction with Production Chains"""
    print_header("TEST 5: Full Prediction with Production Chains")
    
    try:
        request_data = generate_full_request_with_chains()
        
        print_info(f"Restaurant: {request_data['demand_input']['place']['place_name']}")
        print_info(f"Scheduling Mode: Slot-based (fixed_shifts=False)")
        print_info(f"Production Chains: {len(request_data['schedule_input']['production_chains'])}")
        print_info(f"Roles: {len(request_data['schedule_input']['roles'])}")
        print_info(f"Employees: {len(request_data['schedule_input']['employees'])}")
        print_info(f"Campaigns: {len(request_data['demand_input']['campaigns'])}")
        
        print_info("Sending request... (this may take 60-90 seconds)")
        start_time = time.time()
        
        response = requests.post(
            f"{BASE_URL}/predict",
            json=request_data,
            timeout=TIMEOUT
        )
        
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Status: {response.status_code} (took {elapsed:.2f}s)")
            
            # Analyze demand predictions
            demand = data["demand_output"]
            print_info(f"Prediction Period: {demand['prediction_period']}")
            
            # Calculate total predicted demand
            total_orders = 0
            total_items = 0
            for day in demand['days']:
                for hour in day['hours']:
                    total_orders += hour['order_count']
                    total_items += hour['item_count']
            
            print_info(f"Total predicted orders: {total_orders}")
            print_info(f"Total predicted items: {total_items}")
            print_info(f"Average items per order: {total_items/total_orders:.2f}")
            
            # Analyze schedule
            schedule = data["schedule_output"]
            
            # Count employee assignments
            employee_shifts = {}
            for day, shifts in schedule.items():
                for shift in shifts:
                    for time_range, employees in shift.items():
                        for emp in employees:
                            if emp not in employee_shifts:
                                employee_shifts[emp] = []
                            employee_shifts[emp].append(f"{day} {time_range}")
            
            print_info(f"Employees scheduled: {len(employee_shifts)}")
            for emp, shifts in employee_shifts.items():
                print(f"    {emp}: {len(shifts)} shifts")
            
            print_success("Full prediction with chains completed successfully ✓")
            return True
        else:
            print_error(f"Failed with status code: {response.status_code}")
            print_error(f"Response: {response.text[:500]}")
            return False
            
    except Exception as e:
        print_error(f"Exception: {str(e)}")
        return False


def test_edge_case_closed_day():
    """Test 6: Edge Case - Restaurant Closed on Sunday"""
    print_header("TEST 6: Edge Case - Closed Day Handling")
    
    try:
        request_data = generate_minimal_request()
        
        # Ensure Sunday is closed
        request_data['demand_input']['place']['opening_hours']['sunday'] = {"closed": True}
        
        print_info("Testing with Sunday closed")
        print_info("Verifying no Sunday shifts are created...")
        
        response = requests.post(
            f"{BASE_URL}/predict",
            json=request_data,
            timeout=TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Check that Sunday predictions exist but schedule is empty
            sunday_demand = [day for day in data['demand_output']['days'] if day['day_name'] == 'sunday']
            sunday_schedule = data['schedule_output']['sunday']
            
            if sunday_demand:
                print_success("Sunday demand predictions generated (24 hours)")
            else:
                print_warning("No Sunday in prediction period")
            
            if not sunday_schedule:
                print_success("No Sunday shifts scheduled (restaurant closed) ✓")
            else:
                print_warning(f"Sunday shifts exist: {sunday_schedule}")
            
            return True
        else:
            print_error(f"Failed with status code: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Exception: {str(e)}")
        return False


def test_edge_case_no_employees():
    """Test 7: Edge Case - No Employees"""
    print_header("TEST 7: Edge Case - No Employees (Demand Only)")
    
    try:
        request_data = generate_minimal_request()
        request_data['schedule_input']['employees'] = []  # No employees
        
        print_info("Testing demand prediction without employees...")
        
        response = requests.post(
            f"{BASE_URL}/predict",
            json=request_data,
            timeout=TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Demand should still work
            assert "demand_output" in data
            assert len(data['demand_output']['days']) > 0
            
            # Schedule should be empty
            total_shifts = sum(len(shifts) for shifts in data['schedule_output'].values())
            
            if total_shifts == 0:
                print_success("Demand predicted successfully without employees ✓")
                print_success("Schedule correctly empty ✓")
            else:
                print_warning(f"Unexpected shifts created: {total_shifts}")
            
            return True
        else:
            print_error(f"Failed with status code: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Exception: {str(e)}")
        return False


def test_error_handling_invalid_dates():
    """Test 8: Error Handling - Invalid Dates"""
    print_header("TEST 8: Error Handling - Invalid Date Format")
    
    try:
        request_data = generate_minimal_request()
        request_data['demand_input']['prediction_start_date'] = "invalid-date"
        
        print_info("Sending request with invalid date format...")
        
        response = requests.post(
            f"{BASE_URL}/predict",
            json=request_data,
            timeout=30
        )
        
        if response.status_code in [400, 422, 500]:
            print_success(f"Error correctly handled with status {response.status_code} ✓")
            return True
        else:
            print_warning(f"Expected error status, got: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Exception: {str(e)}")
        return False


def test_error_handling_missing_fields():
    """Test 9: Error Handling - Missing Required Fields"""
    print_header("TEST 9: Error Handling - Missing Required Fields")
    
    try:
        # Create request with missing 'place' field
        request_data = {
            "demand_input": {
                "orders": [],
                "prediction_start_date": "2024-01-15",
                "prediction_days": 7
            },
            "schedule_input": {
                "roles": [],
                "employees": []
            }
        }
        
        print_info("Sending request with missing 'place' field...")
        
        response = requests.post(
            f"{BASE_URL}/predict",
            json=request_data,
            timeout=30
        )
        
        if response.status_code == 422:  # Validation error
            print_success(f"Validation error correctly returned (422) ✓")
            return True
        else:
            print_warning(f"Expected 422, got: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Exception: {str(e)}")
        return False


def test_performance_large_request():
    """Test 10: Performance - Large Historical Data"""
    print_header("TEST 10: Performance - Large Historical Dataset")
    
    try:
        prediction_start = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        history_start = (datetime.strptime(prediction_start, "%Y-%m-%d") - timedelta(days=90)).strftime("%Y-%m-%d")
        
        request_data = generate_minimal_request(prediction_start)
        request_data['demand_input']['orders'] = generate_historical_orders(history_start, 90)  # 90 days
        request_data['demand_input']['prediction_days'] = 14  # 2 weeks
        
        num_orders = len(request_data['demand_input']['orders'])
        print_info(f"Historical orders: {num_orders}")
        print_info(f"Prediction days: 14")
        print_info("Sending large request... (may take up to 2 minutes)")
        
        start_time = time.time()
        
        response = requests.post(
            f"{BASE_URL}/predict",
            json=request_data,
            timeout=TIMEOUT
        )
        
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            print_success(f"Status: {response.status_code}")
            print_success(f"Processing time: {elapsed:.2f}s")
            
            if elapsed < 60:
                print_success("Performance: Excellent (<60s) ✓")
            elif elapsed < 90:
                print_success("Performance: Good (<90s) ✓")
            else:
                print_warning(f"Performance: Slow (>{elapsed:.0f}s)")
            
            return True
        else:
            print_error(f"Failed with status code: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Exception: {str(e)}")
        return False


# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

def run_all_tests():
    """Run all tests and generate report"""
    print_header("RESTAURANT API - COMPREHENSIVE TEST SUITE")
    print_info(f"Base URL: {BASE_URL}")
    print_info(f"Timeout: {TIMEOUT}s")
    print_info(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    tests = [
        ("Health Check", test_health_check),
        ("Model Info", test_model_info),
        ("Example Request", test_example_request),
        ("Minimal Prediction", test_minimal_prediction),
        ("Full Prediction with Chains", test_full_prediction_with_chains),
        ("Edge Case: Closed Day", test_edge_case_closed_day),
        ("Edge Case: No Employees", test_edge_case_no_employees),
        ("Error Handling: Invalid Dates", test_error_handling_invalid_dates),
        ("Error Handling: Missing Fields", test_error_handling_missing_fields),
        ("Performance: Large Dataset", test_performance_large_request),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print_error(f"Test crashed: {str(e)}")
            results.append((test_name, False))
        
        time.sleep(1)  # Brief pause between tests
    
    # Print summary
    print_header("TEST SUMMARY")
    
    passed = sum(1 for _, result in results if result)
    failed = len(results) - passed
    
    for test_name, result in results:
        status = f"{Colors.GREEN}PASS{Colors.END}" if result else f"{Colors.RED}FAIL{Colors.END}"
        print(f"  {status}  {test_name}")
    
    print(f"\n{Colors.BOLD}Total: {len(results)} tests{Colors.END}")
    print(f"{Colors.GREEN}Passed: {passed}{Colors.END}")
    print(f"{Colors.RED}Failed: {failed}{Colors.END}")
    
    if failed == 0:
        print(f"\n{Colors.BOLD}{Colors.GREEN}🎉 ALL TESTS PASSED! 🎉{Colors.END}\n")
    else:
        print(f"\n{Colors.BOLD}{Colors.YELLOW}⚠️  SOME TESTS FAILED{Colors.END}\n")
    
    return failed == 0


if __name__ == "__main__":
    import sys
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        if response.status_code != 200:
            print_error(f"Server returned status {response.status_code}")
            print_error("Make sure the API is running: uvicorn api.main:app --reload --host 0.0.0.0 --port 8000")
            sys.exit(1)
    except requests.exceptions.ConnectionError:
        print_error("Cannot connect to API server!")
        print_error("Make sure the API is running: uvicorn api.main:app --reload --host 0.0.0.0 --port 8000")
        sys.exit(1)
    
    # Run tests
    success = run_all_tests()
    sys.exit(0 if success else 1)