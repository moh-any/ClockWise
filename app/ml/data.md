# 📋 Complete API Documentation

**File: `docs/API_DOCUMENTATION.md`**

```markdown
# Restaurant Management API Documentation

**Version:** 3.1.0  
**Base URL:** `http://localhost:8000`

## Overview

This API provides three main services for restaurant management:
1. **Demand Prediction** - Predict hourly item and order counts
2. **Staff Scheduling** - Generate optimal staff schedules with management insights
3. **Campaign Recommendations** - AI-powered marketing campaign suggestions

---

## Table of Contents

1. [Authentication](#authentication)
2. [Health & Status Endpoints](#health--status-endpoints)
3. [Demand Prediction](#demand-prediction)
4. [Staff Scheduling](#staff-scheduling)
5. [Campaign Recommendations](#campaign-recommendations)
6. [Error Handling](#error-handling)
7. [Data Models Reference](#data-models-reference)

---

## Authentication

Currently, the API does not require authentication. For production deployment, implement JWT or API key authentication.

---

## Health & Status Endpoints

### 1. Health Check

**Endpoint:** `GET /`

**Description:** Check API health and feature availability.

**Response:**

```json
{
  "status": "online",
  "model_loaded": true,
  "scheduler_available": true,
  "weather_api_available": true,
  "holiday_api_available": true,
  "campaign_available": true,
  "version": "3.1.0",
  "features": [
    "demand_prediction",
    "staff_scheduling",
    "campaign_recommendations",
    "management_insights"
  ]
}
```

---

### 2. Model Information

**Endpoint:** `GET /model/info`

**Description:** Get demand prediction model metadata.

**Response:**

```json
{
  "python_version": "3.12.0",
  "sklearn_version": "1.3.0",
  "model_type": "RandomForestRegressor",
  "features": ["place_id", "hour", "day_of_week", "..."],
  "hyperparameters": {
    "max_depth": 12,
    "min_samples_leaf": 7,
    "max_features": 0.5,
    "n_estimators": 600,
    "bootstrap": true
  },
  "training_size": 65608,
  "test_size": 16403,
  "version": "2.1_fixed_lag_features"
}
```

---

## Demand Prediction

### 3. Predict Demand

**Endpoint:** `POST /predict/demand`

**Description:** Predict hourly demand (item_count and order_count) for specified days.

**Request Body:**

```json
{
  "place": {
    "place_id": "rest_001",
    "place_name": "Pizza Paradise",
    "type": "restaurant",
    "latitude": 55.6761,
    "longitude": 12.5683,
    "waiting_time": 30,
    "receiving_phone": true,
    "delivery": true,
    "opening_hours": {
      "monday": {"from": "10:00", "to": "22:00"},
      "tuesday": {"from": "10:00", "to": "22:00"},
      "wednesday": {"from": "10:00", "to": "22:00"},
      "thursday": {"from": "10:00", "to": "22:00"},
      "friday": {"from": "10:00", "to": "23:00"},
      "saturday": {"from": "11:00", "to": "23:00"},
      "sunday": {"closed": true}
    },
    "fixed_shifts": true,
    "number_of_shifts_per_day": 3,
    "shift_times": ["10:00-14:00", "14:00-18:00", "18:00-22:00"],
    "rating": 4.5,
    "accepting_orders": true
  },
  "orders": [
    {
      "time": "2024-01-15T12:30:00",
      "items": 3,
      "status": "completed",
      "total_amount": 45.50,
      "discount_amount": 5.00
    },
    {
      "time": "2024-01-15T13:15:00",
      "items": 2,
      "status": "completed",
      "total_amount": 32.00,
      "discount_amount": 0.00
    }
  ],
  "campaigns": [
    {
      "start_time": "2024-01-10T00:00:00",
      "end_time": "2024-01-17T23:59:59",
      "items_included": ["pizza_margherita", "drink_cola"],
      "discount": 15.0
    }
  ],
  "prediction_start_date": "2024-02-01",
  "prediction_days": 7
}
```

**Response:**

```json
{
  "demand_output": {
    "restaurant_name": "Pizza Paradise",
    "prediction_period": "2024-02-01 to 2024-02-07",
    "days": [
      {
        "day_name": "thursday",
        "date": "2024-02-01",
        "hours": [
          {
            "hour": 0,
            "order_count": 2,
            "item_count": 5
          },
          {
            "hour": 1,
            "order_count": 1,
            "item_count": 3
          },
          {
            "hour": 10,
            "order_count": 8,
            "item_count": 18
          },
          {
            "hour": 11,
            "order_count": 12,
            "item_count": 28
          },
          {
            "hour": 12,
            "order_count": 25,
            "item_count": 58
          },
          {
            "hour": 13,
            "order_count": 22,
            "item_count": 51
          },
          {
            "hour": 18,
            "order_count": 35,
            "item_count": 82
          },
          {
            "hour": 19,
            "order_count": 30,
            "item_count": 70
          },
          {
            "hour": 20,
            "order_count": 20,
            "item_count": 45
          },
          {
            "hour": 21,
            "order_count": 15,
            "item_count": 35
          },
          {
            "hour": 22,
            "order_count": 8,
            "item_count": 18
          },
          {
            "hour": 23,
            "order_count": 3,
            "item_count": 7
          }
        ]
      }
    ]
  }
}
```

**Notes:**
- Minimum 7 days of historical orders recommended
- Weather and holiday data automatically fetched based on coordinates
- Predictions are hourly (24 hours per day)

---

## Staff Scheduling

### 4. Generate Schedule

**Endpoint:** `POST /predict/schedule`

**Description:** Generate optimized staff schedule with management insights.

**Request Body:**

```json
{
  "place": {
    "place_id": "rest_001",
    "place_name": "Pizza Paradise",
    "type": "restaurant",
    "latitude": 55.6761,
    "longitude": 12.5683,
    "waiting_time": 30,
    "receiving_phone": true,
    "delivery": true,
    "opening_hours": {
      "monday": {"from": "10:00", "to": "22:00"},
      "tuesday": {"from": "10:00", "to": "22:00"},
      "wednesday": {"from": "10:00", "to": "22:00"},
      "thursday": {"from": "10:00", "to": "22:00"},
      "friday": {"from": "10:00", "to": "23:00"},
      "saturday": {"from": "11:00", "to": "23:00"},
      "sunday": {"closed": true}
    },
    "fixed_shifts": true,
    "number_of_shifts_per_day": 3,
    "shift_times": ["10:00-14:00", "14:00-18:00", "18:00-22:00"],
    "rating": 4.5,
    "accepting_orders": true
  },
  "schedule_input": {
    "roles": [
      {
        "role_id": "chef",
        "role_name": "Chef",
        "producing": true,
        "items_per_employee_per_hour": 20.0,
        "min_present": 1,
        "is_independent": true
      },
      {
        "role_id": "waiter",
        "role_name": "Waiter",
        "producing": false,
        "items_per_employee_per_hour": null,
        "min_present": 1,
        "is_independent": true
      }
    ],
    "employees": [
      {
        "employee_id": "emp_001",
        "role_ids": ["chef"],
        "available_days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
        "preferred_days": ["monday", "wednesday", "friday"],
        "available_hours": {
          "monday": {"from": "10:00", "to": "22:00"},
          "tuesday": {"from": "10:00", "to": "22:00"},
          "wednesday": {"from": "10:00", "to": "22:00"},
          "thursday": {"from": "10:00", "to": "22:00"},
          "friday": {"from": "10:00", "to": "22:00"}
        },
        "preferred_hours": {
          "monday": {"from": "10:00", "to": "18:00"},
          "wednesday": {"from": "10:00", "to": "18:00"},
          "friday": {"from": "10:00", "to": "18:00"}
        },
        "hourly_wage": 25.0,
        "max_hours_per_week": 40.0,
        "max_consec_slots": 8,
        "pref_hours": 32.0
      },
      {
        "employee_id": "emp_002",
        "role_ids": ["waiter"],
        "available_days": ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday"],
        "preferred_days": ["tuesday", "thursday", "saturday"],
        "available_hours": {
          "monday": {"from": "14:00", "to": "22:00"},
          "tuesday": {"from": "14:00", "to": "22:00"},
          "wednesday": {"from": "14:00", "to": "22:00"},
          "thursday": {"from": "14:00", "to": "22:00"},
          "friday": {"from": "14:00", "to": "23:00"},
          "saturday": {"from": "14:00", "to": "23:00"}
        },
        "preferred_hours": {
          "tuesday": {"from": "14:00", "to": "22:00"},
          "thursday": {"from": "14:00", "to": "22:00"},
          "saturday": {"from": "14:00", "to": "23:00"}
        },
        "hourly_wage": 18.0,
        "max_hours_per_week": 35.0,
        "max_consec_slots": 8,
        "pref_hours": 28.0
      }
    ],
    "production_chains": [],
    "scheduler_config": {
      "slot_len_hour": 1.0,
      "min_rest_slots": 2,
      "min_shift_length_slots": 4,
      "meet_all_demand": false
    }
  },
  "demand_predictions": [
    {
      "day_name": "monday",
      "date": "2024-02-05",
      "hours": [
        {"hour": 10, "order_count": 8, "item_count": 18},
        {"hour": 11, "order_count": 12, "item_count": 28},
        {"hour": 12, "order_count": 25, "item_count": 58},
        {"hour": 13, "order_count": 22, "item_count": 51},
        {"hour": 18, "order_count": 35, "item_count": 82},
        {"hour": 19, "order_count": 30, "item_count": 70},
        {"hour": 20, "order_count": 20, "item_count": 45},
        {"hour": 21, "order_count": 15, "item_count": 35}
      ]
    }
  ],
  "prediction_start_date": "2024-02-05"
}
```

**Response:**

```json
{
  "schedule_output": {
    "monday": [
      {
        "10:00-14:00": ["emp_001"]
      },
      {
        "14:00-18:00": ["emp_001", "emp_002"]
      },
      {
        "18:00-22:00": ["emp_002"]
      }
    ],
    "tuesday": [
      {
        "10:00-14:00": ["emp_001"]
      },
      {
        "14:00-18:00": ["emp_001", "emp_002"]
      },
      {
        "18:00-22:00": ["emp_002"]
      }
    ],
    "wednesday": [],
    "thursday": [],
    "friday": [],
    "saturday": [],
    "sunday": []
  },
  "schedule_status": "OPTIMAL",
  "schedule_message": "Schedule generated successfully",
  "objective_value": 1250.5,
  "management_insights": {
    "has_solution": true,
    "peak_periods": [
      {
        "slot": 18,
        "average_demand": 82.0,
        "max_demand": 82.0,
        "recommendation": "Consider scheduling more staff during this time slot"
      },
      {
        "slot": 19,
        "average_demand": 70.0,
        "max_demand": 70.0,
        "recommendation": "Consider scheduling more staff during this time slot"
      }
    ],
    "capacity_analysis": {
      "chef": {
        "eligible_employees": 1,
        "total_available_hours": 40.0,
        "potential_output": 800.0,
        "capacity_ratio": 2.4,
        "is_sufficient": true
      },
      "waiter": {
        "eligible_employees": 1,
        "total_available_hours": 35.0,
        "potential_output": 0.0,
        "capacity_ratio": 0.0,
        "is_sufficient": true
      }
    },
    "employee_utilization": [
      {
        "employee": "emp_001",
        "hours_worked": 32.0,
        "max_hours": 40.0,
        "utilization_rate": 0.8,
        "hours_deviation": 0.0,
        "status": "well_utilized"
      },
      {
        "employee": "emp_002",
        "hours_worked": 28.0,
        "max_hours": 35.0,
        "utilization_rate": 0.8,
        "hours_deviation": 0.0,
        "status": "well_utilized"
      }
    ],
    "role_demand": {
      "chef": {
        "eligible_employees": 1,
        "working_employees": 1,
        "total_hours_worked": 32.0,
        "capacity_utilization": 0.85,
        "is_bottleneck": false
      },
      "waiter": {
        "eligible_employees": 1,
        "working_employees": 1,
        "total_hours_worked": 28.0,
        "capacity_utilization": 0.0,
        "is_bottleneck": false
      }
    },
    "hiring_recommendations": [],
    "coverage_gaps": [],
    "cost_analysis": {
      "total_wage_cost": 1304.0,
      "cost_by_role": {
        "chef": 800.0,
        "waiter": 504.0
      },
      "opportunity_cost_unmet_demand": 0.0,
      "total_cost": 1304.0,
      "cost_per_item_served": 3.25
    },
    "workload_distribution": {
      "average_hours": 30.0,
      "max_hours": 32.0,
      "min_hours": 28.0,
      "range": 4.0,
      "unused_employees": 0,
      "underutilized_employees": 0,
      "well_utilized_employees": 2,
      "overutilized_employees": 0,
      "balance_score": 0.88
    },
    "feasibility_analysis": null
  }
}
```

**Management Insights Fields:**

| Field | Description | Available When |
|-------|-------------|----------------|
| `has_solution` | Whether a feasible schedule was found | Always |
| `peak_periods` | High-demand time slots | Always |
| `capacity_analysis` | Role-by-role capacity analysis | Always |
| `employee_utilization` | Per-employee work hours and utilization rates | With solution |
| `role_demand` | Role coverage and bottleneck analysis | With solution |
| `hiring_recommendations` | Suggested hiring by role with reasoning | With solution or no solution |
| `coverage_gaps` | Time slots with insufficient staff | With solution |
| `cost_analysis` | Wage costs and opportunity costs | With solution |
| `workload_distribution` | Fairness and balance metrics | With solution |
| `feasibility_analysis` | Why no solution was found | Without solution |

---

## Campaign Recommendations

### 5. Get Campaign Recommendations

**Endpoint:** `POST /recommend/campaigns`

**Description:** Generate AI-powered marketing campaign recommendations. Weather and holiday data automatically fetched.

**Request Body:**

```json
{
  "place": {
    "place_id": "rest_001",
    "place_name": "Pizza Paradise",
    "type": "restaurant",
    "latitude": 55.6761,
    "longitude": 12.5683,
    "waiting_time": 30,
    "receiving_phone": true,
    "delivery": true,
    "opening_hours": {
      "monday": {"from": "10:00", "to": "22:00"},
      "tuesday": {"from": "10:00", "to": "22:00"},
      "wednesday": {"from": "10:00", "to": "22:00"},
      "thursday": {"from": "10:00", "to": "22:00"},
      "friday": {"from": "10:00", "to": "23:00"},
      "saturday": {"from": "11:00", "to": "23:00"},
      "sunday": {"closed": true}
    },
    "fixed_shifts": true,
    "number_of_shifts_per_day": 3,
    "shift_times": ["10:00-14:00", "14:00-18:00", "18:00-22:00"],
    "rating": 4.5,
    "accepting_orders": true
  },
  "orders": [
    {
      "time": "2024-01-15T12:30:00",
      "items": 3,
      "status": "completed",
      "total_amount": 45.50,
      "discount_amount": 0.00
    },
    {
      "time": "2024-01-15T13:15:00",
      "items": 2,
      "status": "completed",
      "total_amount": 32.00,
      "discount_amount": 0.00
    }
  ],
  "campaigns": [
    {
      "start_time": "2024-01-10T00:00:00",
      "end_time": "2024-01-17T23:59:59",
      "items_included": ["pizza_margherita", "drink_cola"],
      "discount": 15.0
    }
  ],
  "order_items": [
    {
      "order_id": "order_1",
      "item_id": "pizza_margherita",
      "quantity": 1
    },
    {
      "order_id": "order_1",
      "item_id": "drink_cola",
      "quantity": 2
    },
    {
      "order_id": "order_2",
      "item_id": "pasta_carbonara",
      "quantity": 1
    },
    {
      "order_id": "order_2",
      "item_id": "salad_caesar",
      "quantity": 1
    }
  ],
  "recommendation_start_date": "2024-02-01",
  "num_recommendations": 5,
  "optimize_for": "roi",
  "max_discount": 30.0,
  "min_campaign_duration_days": 3,
  "max_campaign_duration_days": 14,
  "available_items": [
    "pizza_margherita",
    "pizza_pepperoni",
    "pasta_carbonara",
    "pasta_bolognese",
    "salad_caesar",
    "drink_cola",
    "drink_water",
    "dessert_tiramisu"
  ]
}
```

**Response:**

```json
{
  "restaurant_name": "Pizza Paradise",
  "recommendation_date": "2024-01-20 14:30:45",
  "recommendations": [
    {
      "campaign_id": "rec_template_0_1705758645",
      "items": ["pizza_margherita", "drink_cola"],
      "discount_percentage": 15.0,
      "start_date": "2024-02-02",
      "end_date": "2024-02-08",
      "duration_days": 6,
      "expected_uplift": 25.5,
      "expected_roi": 185.3,
      "expected_revenue": 4500.0,
      "confidence_score": 0.85,
      "reasoning": "Recommended because: historically high ROI (185.3%), optimal day of week, predicted ROI: 185.3%",
      "priority_score": 142.5,
      "recommended_for_context": {
        "day_of_week": 4,
        "season": "winter"
      }
    },
    {
      "campaign_id": "rec_template_1_1705758645",
      "items": ["pasta_carbonara", "salad_caesar"],
      "discount_percentage": 20.0,
      "start_date": "2024-02-02",
      "end_date": "2024-02-09",
      "duration_days": 7,
      "expected_uplift": 18.2,
      "expected_roi": 120.5,
      "expected_revenue": 3800.0,
      "confidence_score": 0.75,
      "reasoning": "Recommended because: good historical ROI (120.5%), seasonally appropriate, predicted ROI: 120.5%",
      "priority_score": 118.3,
      "recommended_for_context": {
        "day_of_week": 4,
        "season": "winter"
      }
    },
    {
      "campaign_id": "novel_affinity_1705758645_pasta_carbonara_salad_caesar",
      "items": ["pasta_carbonara", "salad_caesar"],
      "discount_percentage": 18.5,
      "start_date": "2024-02-02",
      "end_date": "2024-02-10",
      "duration_days": 8,
      "expected_uplift": 20.0,
      "expected_roi": 50.0,
      "expected_revenue": 4200.0,
      "confidence_score": 0.3,
      "reasoning": "Novel campaign combining high-affinity items (pasta_carbonara, salad_caesar) with lift score 2.15",
      "priority_score": 43.0,
      "recommended_for_context": {
        "day_of_week": 4,
        "season": "winter"
      }
    }
  ],
  "analysis_summary": {
    "total_campaigns_analyzed": 15,
    "avg_uplift": 22.3,
    "median_uplift": 18.5,
    "avg_roi": 125.7,
    "median_roi": 110.2,
    "total_revenue_impact": 45000.0,
    "successful_campaigns": 12,
    "success_rate": 80.0
  },
  "insights": {
    "best_day_of_week": {
      "day": "Friday",
      "avg_revenue": 5200.0
    },
    "best_hours": [18, 19, 12],
    "top_item_pairs": [
      {
        "items": ["pasta_carbonara", "salad_caesar"],
        "affinity_score": 2.15
      },
      {
        "items": ["pizza_margherita", "drink_cola"],
        "affinity_score": 1.85
      },
      {
        "items": ["pizza_pepperoni", "drink_water"],
        "affinity_score": 1.72
      }
    ]
  },
  "confidence_level": "high"
}
```

**Notes:**
- Weather forecast automatically fetched from Open-Meteo API
- Holidays automatically detected using Nominatim + holidays library
- User-provided weather/holiday data is ignored in favor of real-time data
- `order_items` field is optional but recommended for better item affinity analysis

---

### 6. Submit Campaign Feedback

**Endpoint:** `POST /recommend/campaigns/feedback`

**Description:** Submit actual campaign performance for model improvement (online learning).

**Request Body:**

```json
{
  "campaign_id": "rec_template_0_1705758645",
  "actual_uplift": 28.3,
  "actual_roi": 195.7,
  "actual_revenue": 4850.0,
  "success": true,
  "notes": "Campaign exceeded expectations, especially on Friday evening"
}
```

**Response:**

```json
{
  "status": "success",
  "message": "Feedback for rec_template_0_1705758645 received",
  "updated_parameters": {
    "status": "feedback_stored"
  }
}
```

---

## Error Handling

### Error Response Format

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Common HTTP Status Codes

| Code | Meaning | Common Causes |
|------|---------|---------------|
| 200 | Success | Request processed successfully |
| 400 | Bad Request | Invalid input data, missing required fields |
| 503 | Service Unavailable | Model not loaded, scheduler unavailable |
| 500 | Internal Server Error | Unexpected error during processing |

### Example Error Responses

**Missing Required Field:**
```json
{
  "detail": "At least some historical orders are required for campaign recommendations"
}
```

**Model Not Loaded:**
```json
{
  "detail": "Model not loaded"
}
```

**Invalid Date Format:**
```json
{
  "detail": "Demand prediction failed: time data '2024-13-01' does not match format '%Y-%m-%d'"
}
```

---