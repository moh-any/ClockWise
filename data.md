# API Documentation - Request & Response Examples

## Complete API Reference with Examples

---

## 1. Health Check

**Endpoint:** `GET /`

**Description:** Check API health and available features

### Request
```http
GET / HTTP/1.1
Host: localhost:8000
```

### Response
```json
{
  "status": "online",
  "model_loaded": true,
  "scheduler_available": true,
  "weather_api_available": true,
  "holiday_api_available": true,
  "campaign_recommender_available": true,
  "version": "3.1.0",
  "features": [
    "demand_prediction",
    "staff_scheduling",
    "campaign_recommendations"
  ]
}
```

---

## 2. Model Information

**Endpoint:** `GET /model/info`

**Description:** Get ML model metadata and performance metrics

### Request
```http
GET /model/info HTTP/1.1
Host: localhost:8000
```

### Response
```json
{
  "model_type": "RandomForestRegressor",
  "version": "1.0.0",
  "trained_date": "2024-01-10",
  "n_estimators": 600,
  "features": [
    "place_id",
    "hour",
    "day_of_week",
    "month",
    "week_of_year",
    "type_id",
    "waiting_time",
    "rating",
    "delivery",
    "accepting_orders",
    "total_campaigns",
    "avg_discount",
    "prev_hour_items",
    "prev_day_items",
    "prev_week_items",
    "prev_month_items",
    "rolling_7d_avg_items",
    "temperature_2m",
    "relative_humidity_2m",
    "precipitation",
    "rain",
    "snowfall",
    "weather_code",
    "cloud_cover",
    "wind_speed_10m",
    "is_rainy",
    "is_snowy",
    "is_cold",
    "is_hot",
    "is_cloudy",
    "is_windy",
    "good_weather",
    "weather_severity",
    "is_holiday"
  ],
  "target_variables": [
    "item_count",
    "order_count"
  ],
  "training_samples": 50000,
  "performance_metrics": {
    "mae": 3.2,
    "rmse": 5.1,
    "r2_score": 0.85
  }
}
```

---

## 3. Demand Prediction (Standalone)

**Endpoint:** `POST /predict/demand`

**Description:** Predict hourly demand for orders and items based on historical data

### Request
```json
{
  "place": {
    "place_id": "pl_12345",
    "place_name": "Pizza Paradise",
    "type": "restaurant",
    "latitude": 55.6761,
    "longitude": 12.5683,
    "waiting_time": 30,
    "receiving_phone": true,
    "delivery": true,
    "opening_hours": {
      "monday": {
        "from": "10:00",
        "to": "23:00"
      },
      "tuesday": {
        "from": "10:00",
        "to": "23:00"
      },
      "wednesday": {
        "from": "10:00",
        "to": "23:00"
      },
      "thursday": {
        "from": "10:00",
        "to": "23:00"
      },
      "friday": {
        "from": "10:00",
        "to": "23:00"
      },
      "saturday": {
        "from": "11:00",
        "to": "23:00"
      },
      "sunday": {
        "closed": true
      }
    },
    "fixed_shifts": true,
    "number_of_shifts_per_day": 3,
    "shift_times": [
      "10:00-15:00",
      "15:00-20:00",
      "20:00-23:00"
    ],
    "rating": 4.5,
    "accepting_orders": true
  },
  "orders": [
    {
      "time": "2024-01-01T12:30:00",
      "items": 3,
      "status": "completed",
      "total_amount": 45.5,
      "discount_amount": 5.0
    },
    {
      "time": "2024-01-01T13:15:00",
      "items": 2,
      "status": "completed",
      "total_amount": 32.0,
      "discount_amount": 0.0
    },
    {
      "time": "2024-01-01T18:45:00",
      "items": 5,
      "status": "completed",
      "total_amount": 67.5,
      "discount_amount": 10.0
    },
    {
      "time": "2024-01-02T12:00:00",
      "items": 2,
      "status": "completed",
      "total_amount": 28.0,
      "discount_amount": 0.0
    },
    {
      "time": "2024-01-02T19:30:00",
      "items": 4,
      "status": "completed",
      "total_amount": 52.0,
      "discount_amount": 5.0
    },
    {
      "time": "2024-01-03T11:45:00",
      "items": 3,
      "status": "completed",
      "total_amount": 41.0,
      "discount_amount": 0.0
    },
    {
      "time": "2024-01-03T20:15:00",
      "items": 6,
      "status": "completed",
      "total_amount": 78.0,
      "discount_amount": 12.0
    }
  ],
  "campaigns": [
    {
      "start_time": "2024-01-01T00:00:00",
      "end_time": "2024-01-07T23:59:59",
      "items_included": [
        "pizza_margherita",
        "pizza_pepperoni"
      ],
      "discount": 15.0
    }
  ],
  "prediction_start_date": "2024-01-15",
  "prediction_days": 7
}
```

### Response
```json
{
  "demand_output": {
    "restaurant_name": "Pizza Paradise",
    "prediction_period": "2024-01-15 to 2024-01-21",
    "days": [
      {
        "day_name": "monday",
        "date": "2024-01-15",
        "hours": [
          {
            "hour": 0,
            "order_count": 0,
            "item_count": 0
          },
          {
            "hour": 1,
            "order_count": 0,
            "item_count": 0
          },
          {
            "hour": 10,
            "order_count": 3,
            "item_count": 8
          },
          {
            "hour": 11,
            "order_count": 5,
            "item_count": 12
          },
          {
            "hour": 12,
            "order_count": 12,
            "item_count": 32
          },
          {
            "hour": 13,
            "order_count": 10,
            "item_count": 26
          },
          {
            "hour": 14,
            "order_count": 6,
            "item_count": 15
          },
          {
            "hour": 15,
            "order_count": 4,
            "item_count": 10
          },
          {
            "hour": 16,
            "order_count": 3,
            "item_count": 8
          },
          {
            "hour": 17,
            "order_count": 8,
            "item_count": 20
          },
          {
            "hour": 18,
            "order_count": 15,
            "item_count": 38
          },
          {
            "hour": 19,
            "order_count": 18,
            "item_count": 45
          },
          {
            "hour": 20,
            "order_count": 16,
            "item_count": 40
          },
          {
            "hour": 21,
            "order_count": 12,
            "item_count": 30
          },
          {
            "hour": 22,
            "order_count": 6,
            "item_count": 15
          },
          {
            "hour": 23,
            "order_count": 2,
            "item_count": 5
          }
        ]
      },
      {
        "day_name": "tuesday",
        "date": "2024-01-16",
        "hours": [
          {
            "hour": 12,
            "order_count": 11,
            "item_count": 28
          },
          {
            "hour": 13,
            "order_count": 9,
            "item_count": 23
          },
          {
            "hour": 18,
            "order_count": 16,
            "item_count": 40
          },
          {
            "hour": 19,
            "order_count": 20,
            "item_count": 50
          },
          {
            "hour": 20,
            "order_count": 18,
            "item_count": 45
          }
        ]
      },
      {
        "day_name": "wednesday",
        "date": "2024-01-17",
        "hours": [
          {
            "hour": 12,
            "order_count": 13,
            "item_count": 33
          },
          {
            "hour": 19,
            "order_count": 19,
            "item_count": 48
          }
        ]
      },
      {
        "day_name": "thursday",
        "date": "2024-01-18",
        "hours": [
          {
            "hour": 12,
            "order_count": 14,
            "item_count": 35
          },
          {
            "hour": 19,
            "order_count": 21,
            "item_count": 52
          }
        ]
      },
      {
        "day_name": "friday",
        "date": "2024-01-19",
        "hours": [
          {
            "hour": 12,
            "order_count": 16,
            "item_count": 40
          },
          {
            "hour": 18,
            "order_count": 22,
            "item_count": 55
          },
          {
            "hour": 19,
            "order_count": 28,
            "item_count": 70
          },
          {
            "hour": 20,
            "order_count": 25,
            "item_count": 62
          }
        ]
      },
      {
        "day_name": "saturday",
        "date": "2024-01-20",
        "hours": [
          {
            "hour": 12,
            "order_count": 18,
            "item_count": 45
          },
          {
            "hour": 13,
            "order_count": 20,
            "item_count": 50
          },
          {
            "hour": 18,
            "order_count": 25,
            "item_count": 62
          },
          {
            "hour": 19,
            "order_count": 30,
            "item_count": 75
          },
          {
            "hour": 20,
            "order_count": 28,
            "item_count": 70
          }
        ]
      },
      {
        "day_name": "sunday",
        "date": "2024-01-21",
        "hours": []
      }
    ]
  }
}
```

---

## 4. Schedule Generation (Standalone)

**Endpoint:** `POST /predict/schedule`

**Description:** Generate optimal staff schedules based on demand predictions

### Request
```json
{
  "place": {
    "place_id": "pl_12345",
    "place_name": "Pizza Paradise",
    "type": "restaurant",
    "latitude": 55.6761,
    "longitude": 12.5683,
    "waiting_time": 30,
    "receiving_phone": true,
    "delivery": true,
    "opening_hours": {
      "monday": {
        "from": "10:00",
        "to": "23:00"
      },
      "tuesday": {
        "from": "10:00",
        "to": "23:00"
      },
      "wednesday": {
        "from": "10:00",
        "to": "23:00"
      },
      "thursday": {
        "from": "10:00",
        "to": "23:00"
      },
      "friday": {
        "from": "10:00",
        "to": "23:00"
      },
      "saturday": {
        "from": "11:00",
        "to": "23:00"
      },
      "sunday": {
        "closed": true
      }
    },
    "fixed_shifts": true,
    "number_of_shifts_per_day": 3,
    "shift_times": [
      "10:00-15:00",
      "15:00-20:00",
      "20:00-23:00"
    ],
    "rating": 4.5,
    "accepting_orders": true
  },
  "schedule_input": {
    "roles": [
      {
        "role_id": "chef",
        "role_name": "Chef",
        "producing": true,
        "items_per_employee_per_hour": 15.0,
        "min_present": 2,
        "is_independent": false
      },
      {
        "role_id": "pizza_maker",
        "role_name": "Pizza Maker",
        "producing": true,
        "items_per_employee_per_hour": 12.0,
        "min_present": 1,
        "is_independent": false
      },
      {
        "role_id": "server",
        "role_name": "Server",
        "producing": false,
        "items_per_employee_per_hour": null,
        "min_present": 2,
        "is_independent": true
      },
      {
        "role_id": "cashier",
        "role_name": "Cashier",
        "producing": false,
        "items_per_employee_per_hour": null,
        "min_present": 1,
        "is_independent": true
      }
    ],
    "employees": [
      {
        "employee_id": "emp_001",
        "role_ids": [
          "chef",
          "pizza_maker"
        ],
        "available_days": [
          "monday",
          "tuesday",
          "wednesday",
          "thursday",
          "friday"
        ],
        "preferred_days": [
          "monday",
          "wednesday",
          "friday"
        ],
        "available_hours": {
          "monday": {
            "from": "10:00",
            "to": "23:00"
          },
          "tuesday": {
            "from": "10:00",
            "to": "23:00"
          },
          "wednesday": {
            "from": "10:00",
            "to": "23:00"
          },
          "thursday": {
            "from": "10:00",
            "to": "23:00"
          },
          "friday": {
            "from": "10:00",
            "to": "23:00"
          }
        },
        "preferred_hours": {
          "monday": {
            "from": "15:00",
            "to": "23:00"
          },
          "wednesday": {
            "from": "15:00",
            "to": "23:00"
          },
          "friday": {
            "from": "15:00",
            "to": "23:00"
          }
        },
        "hourly_wage": 25.5,
        "max_hours_per_week": 40.0,
        "max_consec_slots": 8,
        "pref_hours": 32.0
      },
      {
        "employee_id": "emp_002",
        "role_ids": [
          "chef"
        ],
        "available_days": [
          "monday",
          "tuesday",
          "wednesday",
          "thursday",
          "friday",
          "saturday"
        ],
        "preferred_days": [
          "tuesday",
          "thursday",
          "saturday"
        ],
        "available_hours": {
          "monday": {
            "from": "10:00",
            "to": "20:00"
          },
          "tuesday": {
            "from": "10:00",
            "to": "20:00"
          },
          "wednesday": {
            "from": "10:00",
            "to": "20:00"
          },
          "thursday": {
            "from": "10:00",
            "to": "20:00"
          },
          "friday": {
            "from": "10:00",
            "to": "20:00"
          },
          "saturday": {
            "from": "11:00",
            "to": "23:00"
          }
        },
        "preferred_hours": {
          "tuesday": {
            "from": "10:00",
            "to": "15:00"
          },
          "thursday": {
            "from": "10:00",
            "to": "15:00"
          },
          "saturday": {
            "from": "15:00",
            "to": "23:00"
          }
        },
        "hourly_wage": 28.0,
        "max_hours_per_week": 40.0,
        "max_consec_slots": 8,
        "pref_hours": 35.0
      },
      {
        "employee_id": "emp_003",
        "role_ids": [
          "server",
          "cashier"
        ],
        "available_days": [
          "wednesday",
          "thursday",
          "friday",
          "saturday"
        ],
        "preferred_days": [
          "friday",
          "saturday"
        ],
        "available_hours": {
          "wednesday": {
            "from": "14:00",
            "to": "23:00"
          },
          "thursday": {
            "from": "14:00",
            "to": "23:00"
          },
          "friday": {
            "from": "10:00",
            "to": "23:00"
          },
          "saturday": {
            "from": "11:00",
            "to": "23:00"
          }
        },
        "preferred_hours": {
          "friday": {
            "from": "18:00",
            "to": "23:00"
          },
          "saturday": {
            "from": "18:00",
            "to": "23:00"
          }
        },
        "hourly_wage": 18.0,
        "max_hours_per_week": 30.0,
        "max_consec_slots": 6,
        "pref_hours": 25.0
      }
    ],
    "production_chains": [
      {
        "chain_id": "kitchen_chain",
        "role_ids": [
          "chef",
          "pizza_maker"
        ],
        "contrib_factor": 1.0
      }
    ],
    "scheduler_config": {
      "slot_len_hour": 1.0,
      "min_rest_slots": 2,
      "min_shift_length_slots": 2,
      "meet_all_demand": false
    }
  },
  "demand_predictions": [
    {
      "day_name": "monday",
      "date": "2024-01-15",
      "hours": [
        {
          "hour": 10,
          "order_count": 3,
          "item_count": 8
        },
        {
          "hour": 11,
          "order_count": 5,
          "item_count": 12
        },
        {
          "hour": 12,
          "order_count": 12,
          "item_count": 32
        },
        {
          "hour": 13,
          "order_count": 10,
          "item_count": 26
        },
        {
          "hour": 18,
          "order_count": 15,
          "item_count": 38
        },
        {
          "hour": 19,
          "order_count": 18,
          "item_count": 45
        },
        {
          "hour": 20,
          "order_count": 16,
          "item_count": 40
        }
      ]
    },
    {
      "day_name": "friday",
      "date": "2024-01-19",
      "hours": [
        {
          "hour": 12,
          "order_count": 16,
          "item_count": 40
        },
        {
          "hour": 18,
          "order_count": 22,
          "item_count": 55
        },
        {
          "hour": 19,
          "order_count": 28,
          "item_count": 70
        },
        {
          "hour": 20,
          "order_count": 25,
          "item_count": 62
        }
      ]
    },
    {
      "day_name": "saturday",
      "date": "2024-01-20",
      "hours": [
        {
          "hour": 12,
          "order_count": 18,
          "item_count": 45
        },
        {
          "hour": 19,
          "order_count": 30,
          "item_count": 75
        },
        {
          "hour": 20,
          "order_count": 28,
          "item_count": 70
        }
      ]
    }
  ],
  "prediction_start_date": "2024-01-15"
}
```

### Response
```json
{
  "schedule_output": {
    "monday": [
      {
        "10:00-15:00": [
          "emp_001",
          "emp_002"
        ]
      },
      {
        "15:00-20:00": [
          "emp_001",
          "emp_002"
        ]
      },
      {
        "20:00-23:00": [
          "emp_001"
        ]
      }
    ],
    "tuesday": [
      {
        "10:00-15:00": [
          "emp_002"
        ]
      },
      {
        "15:00-20:00": [
          "emp_001"
        ]
      }
    ],
    "wednesday": [
      {
        "10:00-15:00": [
          "emp_001",
          "emp_002"
        ]
      },
      {
        "15:00-20:00": [
          "emp_001",
          "emp_003"
        ]
      },
      {
        "20:00-23:00": [
          "emp_003"
        ]
      }
    ],
    "thursday": [
      {
        "15:00-20:00": [
          "emp_002",
          "emp_003"
        ]
      },
      {
        "20:00-23:00": [
          "emp_003"
        ]
      }
    ],
    "friday": [
      {
        "10:00-15:00": [
          "emp_001",
          "emp_002"
        ]
      },
      {
        "15:00-20:00": [
          "emp_001",
          "emp_002",
          "emp_003"
        ]
      },
      {
        "20:00-23:00": [
          "emp_001",
          "emp_003"
        ]
      }
    ],
    "saturday": [
      {
        "11:00-15:00": [
          "emp_002"
        ]
      },
      {
        "15:00-20:00": [
          "emp_002",
          "emp_003"
        ]
      },
      {
        "20:00-23:00": [
          "emp_003"
        ]
      }
    ],
    "sunday": []
  },
  "schedule_status": "optimal",
  "schedule_message": "Optimal schedule found. All constraints satisfied.",
  "objective_value": 1250.75,
  "total_labor_cost": 1250.75,
  "employee_summary": {
    "emp_001": {
      "total_hours": 32.0,
      "days_worked": 5,
      "shifts": [
        "Monday 10:00-23:00",
        "Tuesday 15:00-20:00",
        "Wednesday 10:00-20:00",
        "Friday 10:00-23:00"
      ]
    },
    "emp_002": {
      "total_hours": 28.0,
      "days_worked": 6,
      "shifts": [
        "Monday 10:00-20:00",
        "Tuesday 10:00-15:00",
        "Wednesday 10:00-15:00",
        "Thursday 15:00-20:00",
        "Friday 10:00-20:00",
        "Saturday 11:00-20:00"
      ]
    },
    "emp_003": {
      "total_hours": 24.0,
      "days_worked": 4,
      "shifts": [
        "Wednesday 15:00-23:00",
        "Thursday 15:00-23:00",
        "Friday 15:00-23:00",
        "Saturday 15:00-23:00"
      ]
    }
  }
}
```

---

## 5. Campaign Recommendations

**Endpoint:** `POST /recommend/campaigns`

**Description:** Get AI-powered campaign recommendations based on historical data

### Request
```json
{
  "place": {
    "place_id": "pl_12345",
    "place_name": "Pizza Paradise",
    "type": "restaurant",
    "latitude": 55.6761,
    "longitude": 12.5683,
    "waiting_time": 30,
    "receiving_phone": true,
    "delivery": true,
    "opening_hours": {
      "monday": {
        "from": "10:00",
        "to": "23:00"
      },
      "tuesday": {
        "from": "10:00",
        "to": "23:00"
      },
      "wednesday": {
        "from": "10:00",
        "to": "23:00"
      },
      "thursday": {
        "from": "10:00",
        "to": "23:00"
      },
      "friday": {
        "from": "10:00",
        "to": "23:00"
      },
      "saturday": {
        "from": "11:00",
        "to": "23:00"
      },
      "sunday": {
        "closed": true
      }
    },
    "fixed_shifts": true,
    "number_of_shifts_per_day": 3,
    "shift_times": [
      "10:00-15:00",
      "15:00-20:00",
      "20:00-23:00"
    ],
    "rating": 4.5,
    "accepting_orders": true
  },
  "orders": [
    {
      "time": "2024-01-01T12:30:00",
      "items": 3,
      "status": "completed",
      "total_amount": 45.5,
      "discount_amount": 5.0
    },
    {
      "time": "2024-01-01T18:45:00",
      "items": 5,
      "status": "completed",
      "total_amount": 67.5,
      "discount_amount": 10.0
    },
    {
      "time": "2024-01-02T12:00:00",
      "items": 2,
      "status": "completed",
      "total_amount": 28.0,
      "discount_amount": 0.0
    },
    {
      "time": "2024-01-02T19:30:00",
      "items": 4,
      "status": "completed",
      "total_amount": 52.0,
      "discount_amount": 5.0
    },
    {
      "time": "2024-01-03T11:45:00",
      "items": 3,
      "status": "completed",
      "total_amount": 41.0,
      "discount_amount": 0.0
    }
  ],
  "campaigns": [
    {
      "start_time": "2024-01-01T00:00:00",
      "end_time": "2024-01-07T23:59:59",
      "items_included": [
        "pizza_margherita",
        "pizza_pepperoni"
      ],
      "discount": 15.0
    },
    {
      "start_time": "2024-01-15T00:00:00",
      "end_time": "2024-01-21T23:59:59",
      "items_included": [
        "pasta_carbonara",
        "salad_caesar"
      ],
      "discount": 20.0
    },
    {
      "start_time": "2024-02-01T00:00:00",
      "end_time": "2024-02-07T23:59:59",
      "items_included": [
        "pizza_margherita",
        "drink_cola"
      ],
      "discount": 18.0
    }
  ],
  "order_items": [
    {
      "order_id": "order_0",
      "item_id": "pizza_margherita",
      "quantity": 2
    },
    {
      "order_id": "order_0",
      "item_id": "drink_cola",
      "quantity": 2
    },
    {
      "order_id": "order_1",
      "item_id": "pizza_pepperoni",
      "quantity": 3
    },
    {
      "order_id": "order_1",
      "item_id": "drink_cola",
      "quantity": 1
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
    },
    {
      "order_id": "order_3",
      "item_id": "pizza_margherita",
      "quantity": 1
    },
    {
      "order_id": "order_3",
      "item_id": "dessert_tiramisu",
      "quantity": 1
    },
    {
      "order_id": "order_4",
      "item_id": "pizza_pepperoni",
      "quantity": 2
    }
  ],
  "recommendation_start_date": "2024-03-01",
  "num_recommendations": 5,
  "optimize_for": "roi",
  "max_discount": 30.0,
  "min_campaign_duration_days": 3,
  "max_campaign_duration_days": 14,
  "available_items": [
    "pizza_margherita",
    "pizza_pepperoni",
    "pasta_carbonara",
    "salad_caesar",
    "drink_cola",
    "drink_water",
    "dessert_tiramisu"
  ],
  "weather_forecast": {
    "avg_temperature": 18.0,
    "avg_precipitation": 0.2,
    "good_weather_ratio": 0.75
  },
  "upcoming_holidays": [
    "2024-03-17",
    "2024-03-25"
  ]
}
```

### Response
```json
{
  "restaurant_name": "Pizza Paradise",
  "recommendation_date": "2024-02-15 14:30:25",
  "recommendations": [
    {
      "campaign_id": "rec_template_0_1708009825",
      "items": [
        "pizza_margherita",
        "drink_cola"
      ],
      "discount_percentage": 15.0,
      "start_date": "2024-03-17",
      "end_date": "2024-03-20",
      "duration_days": 4,
      "expected_uplift": 28.5,
      "expected_roi": 185.3,
      "expected_revenue": 1420.0,
      "confidence_score": 0.87,
      "reasoning": "Recommended because: historically high ROI (185.3%), optimal day of week, upcoming holiday period, predicted ROI: 185.3%",
      "priority_score": 94.2,
      "recommended_for_context": {
        "day_of_week": 6,
        "season": "spring"
      }
    },
    {
      "campaign_id": "rec_template_1_1708009825",
      "items": [
        "pasta_carbonara",
        "salad_caesar"
      ],
      "discount_percentage": 20.0,
      "start_date": "2024-03-05",
      "end_date": "2024-03-11",
      "duration_days": 7,
      "expected_uplift": 22.3,
      "expected_roi": 156.8,
      "expected_revenue": 1180.0,
      "confidence_score": 0.82,
      "reasoning": "Recommended because: good historical ROI (156.8%), seasonally appropriate, predicted ROI: 156.8%",
      "priority_score": 88.5,
      "recommended_for_context": {
        "day_of_week": 1,
        "season": "spring"
      }
    },
    {
      "campaign_id": "rec_template_2_1708009825",
      "items": [
        "pizza_pepperoni",
        "dessert_tiramisu"
      ],
      "discount_percentage": 18.0,
      "start_date": "2024-03-08",
      "end_date": "2024-03-10",
      "duration_days": 3,
      "expected_uplift": 32.0,
      "expected_roi": 172.5,
      "expected_revenue": 920.0,
      "confidence_score": 0.75,
      "reasoning": "Recommended because: good historical ROI (172.5%), optimal day of week, predicted ROI: 172.5%",
      "priority_score": 85.0,
      "recommended_for_context": {
        "day_of_week": 4,
        "season": "spring"
      }
    },
    {
      "campaign_id": "novel_affinity_1708009825_pizza_margherita_drink_cola",
      "items": [
        "pizza_margherita",
        "drink_cola"
      ],
      "discount_percentage": 22.5,
      "start_date": "2024-03-02",
      "end_date": "2024-03-08",
      "duration_days": 7,
      "expected_uplift": 20.0,
      "expected_roi": 50.0,
      "expected_revenue": 1260.0,
      "confidence_score": 0.3,
      "reasoning": "Novel campaign combining high-affinity items (pizza_margherita, drink_cola) with lift score 2.85",
      "priority_score": 57.0,
      "recommended_for_context": {
        "day_of_week": 5,
        "season": "spring"
      }
    },
    {
      "campaign_id": "novel_affinity_1708009825_pizza_pepperoni_drink_cola",
      "items": [
        "pizza_pepperoni",
        "drink_cola"
      ],
      "discount_percentage": 18.3,
      "start_date": "2024-03-02",
      "end_date": "2024-03-09",
      "duration_days": 8,
      "expected_uplift": 20.0,
      "expected_roi": 50.0,
      "expected_revenue": 1440.0,
      "confidence_score": 0.3,
      "reasoning": "Novel campaign combining high-affinity items (pizza_pepperoni, drink_cola) with lift score 2.12",
      "priority_score": 42.4,
      "recommended_for_context": {
        "day_of_week": 5,
        "season": "spring"
      }
    }
  ],
  "analysis_summary": {
    "total_campaigns_analyzed": 3,
    "avg_uplift": 27.6,
    "median_uplift": 28.5,
    "avg_roi": 171.5,
    "median_roi": 172.5,
    "total_revenue_impact": 3520.0,
    "successful_campaigns": 3,
    "success_rate": 100.0
  },
  "insights": {
    "best_day_of_week": {
      "day": "Friday",
      "avg_revenue": 2850.0
    },
    "best_hours": [
      18,
      19,
      20
    ],
    "top_item_pairs": [
      {
        "items": [
          "drink_cola",
          "pizza_margherita"
        ],
        "affinity_score": 2.85
      },
      {
        "items": [
          "drink_cola",
          "pizza_pepperoni"
        ],
        "affinity_score": 2.12
      },
      {
        "items": [
          "pasta_carbonara",
          "salad_caesar"
        ],
        "affinity_score": 1.95
      }
    ]
  },
  "confidence_level": "medium"
}
```

---

## 6. Campaign Feedback

**Endpoint:** `POST /recommend/campaigns/feedback`

**Description:** Submit feedback on executed campaigns for model improvement

### Request
```json
{
  "campaign_id": "rec_template_0_1708009825",
  "actual_uplift": 32.8,
  "actual_roi": 198.5,
  "actual_revenue": 1580.0,
  "success": true,
  "notes": "Campaign exceeded expectations. St. Patrick's Day weekend drove strong performance. Pizza and cola combo was very popular. Recommend repeating for Easter weekend."
}
```

### Response
```json
{
  "status": "success",
  "message": "Feedback for campaign rec_template_0_1708009825 received successfully",
  "updated_parameters": {
    "status": "model_updated",
    "campaign_id": "rec_template_0_1708009825"
  }
}
```

---

## Common Error Responses

### 400 Bad Request
```json
{
  "detail": "At least some historical orders are required for campaign recommendations"
}
```

### 422 Validation Error
```json
{
  "detail": [
    {
      "type": "string_type",
      "loc": [
        "body",
        "prediction_start_date"
      ],
      "msg": "Input should be a valid string",
      "input": 20240115
    }
  ]
}
```

### 500 Internal Server Error
```json
{
  "detail": "Failed to generate campaign recommendations: 'dict' object has no attribute 'time'"
}
```

### 503 Service Unavailable
```json
{
  "detail": "Model not loaded. Please wait for initialization."
}
```

---

## Notes

- **Date Format**: All dates in ISO 8601 format (`YYYY-MM-DD` or `YYYY-MM-DDTHH:MM:SS`)
- **Time Format**: 24-hour format (`HH:MM`)
- **Timezone**: Use restaurant's local timezone for all timestamps
- **Currency**: All monetary values in restaurant's local currency
- **Authentication**: Currently no authentication required (add in production)
- **Rate Limiting**: No rate limiting currently (implement in production)
- **CORS**: All origins allowed (restrict in production)

---

**API Version**: 3.1.0  
**Last Updated**: 2024-02-06  
**Documentation**: http://localhost:8000/docs (Swagger UI)  
**ReDoc**: http://localhost:8000/redoc