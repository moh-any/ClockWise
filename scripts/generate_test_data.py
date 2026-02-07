"""
Comprehensive Test Data Generator for End-to-End Testing
=========================================================
Generates realistic test data covering various scenarios:
- Normal weekdays vs weekend peaks
- Lunch/dinner rush hours
- Campaign effects (discounts, promotions)
- Delivery vs dine-in patterns
- Surge events (holidays, flash sales, viral moments)
- Seasonal variations

Output: CSV files matching the format in test-data/
"""

import csv
import uuid
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Tuple
import math

# Configuration
OUTPUT_DIR = Path(__file__).parent.parent / "test-data"
RANDOM_SEED = 42

# Date range for test data (2 months of data)
START_DATE = datetime(2026, 1, 1)
END_DATE = datetime(2026, 2, 28)

# Restaurant operating hours
OPEN_HOUR = 10
CLOSE_HOUR = 23

random.seed(RANDOM_SEED)


def generate_uuid(prefix: str, index: int) -> str:
    """Generate consistent UUID-like strings for reproducibility."""
    # Format: prefix followed by padded index
    base = f"{prefix}-e29b-41d4-a716-"
    suffix = f"{index:012d}"
    return base + suffix


# ============================================================================
# MENU ITEMS
# ============================================================================

MENU_CATEGORIES = {
    "Pizza": {
        "items": [
            ("Margherita Pizza", 15.99, 2),
            ("Pepperoni Pizza", 17.99, 2),
            ("BBQ Chicken Pizza", 18.99, 2),
            ("Veggie Supreme Pizza", 16.99, 2),
            ("Hawaiian Pizza", 17.49, 2),
            ("Meat Lovers Pizza", 19.99, 2),
            ("Four Cheese Pizza", 16.99, 2),
            ("Buffalo Chicken Pizza", 18.49, 2),
        ],
        "popularity": 0.35,  # 35% of orders include pizza
    },
    "Pasta": {
        "items": [
            ("Spaghetti Bolognese", 14.99, 1),
            ("Fettuccine Alfredo", 15.99, 1),
            ("Penne Arrabiata", 13.99, 1),
            ("Lasagna", 16.99, 2),
            ("Carbonara", 15.49, 1),
            ("Seafood Linguine", 18.99, 2),
        ],
        "popularity": 0.25,
    },
    "Appetizers": {
        "items": [
            ("Garlic Bread", 5.99, 1),
            ("Bruschetta", 7.99, 1),
            ("Mozzarella Sticks", 8.99, 1),
            ("Calamari", 11.99, 1),
            ("Caprese Salad", 9.99, 1),
            ("Soup of the Day", 6.99, 1),
        ],
        "popularity": 0.40,
    },
    "Salads": {
        "items": [
            ("Caesar Salad", 10.99, 1),
            ("Greek Salad", 11.99, 1),
            ("Garden Salad", 8.99, 1),
            ("Chicken Salad", 13.99, 1),
        ],
        "popularity": 0.20,
    },
    "Desserts": {
        "items": [
            ("Tiramisu", 7.99, 1),
            ("Panna Cotta", 6.99, 1),
            ("Gelato", 5.99, 1),
            ("Chocolate Cake", 7.49, 1),
        ],
        "popularity": 0.30,
    },
    "Beverages": {
        "items": [
            ("Soft Drink", 2.99, 0),
            ("Coffee", 3.49, 0),
            ("Iced Tea", 2.99, 0),
            ("Fresh Juice", 4.99, 0),
            ("Wine Glass", 8.99, 0),
            ("Beer", 5.99, 0),
            ("Sparkling Water", 2.49, 0),
            ("Milkshake", 5.49, 1),
        ],
        "popularity": 0.60,
    },
}


def generate_items() -> List[Dict]:
    """Generate menu items with realistic pricing and employee requirements."""
    items = []
    item_index = 1
    
    for category, data in MENU_CATEGORIES.items():
        for name, price, needed_employees in data["items"]:
            items.append({
                "item_id": generate_uuid("660e8400", item_index),
                "name": name,
                "needed_employees": needed_employees,
                "price": price,
                "category": category,  # Extra field for internal use
                "popularity": data["popularity"],
            })
            item_index += 1
    
    return items


# ============================================================================
# CAMPAIGNS
# ============================================================================

def generate_campaigns() -> List[Dict]:
    """Generate various campaign scenarios."""
    campaigns = [
        # Active high-impact campaigns
        {
            "id": generate_uuid("550e8400", 1),
            "name": "Valentine's Day Special",
            "status": "active",
            "start_time": "2026-02-01T10:00:00Z",
            "end_time": "2026-02-14T23:59:59Z",
            "discount_percent": 20.0,
            "impact_multiplier": 1.8,  # 80% more orders
        },
        {
            "id": generate_uuid("550e8400", 2),
            "name": "Weekend Pizza Deal",
            "status": "active",
            "start_time": "2026-02-06T00:00:00Z",
            "end_time": "2026-02-08T23:59:59Z",
            "discount_percent": 15.0,
            "impact_multiplier": 1.4,
        },
        {
            "id": generate_uuid("550e8400", 3),
            "name": "Lunch Hour Special",
            "status": "active",
            "start_time": "2026-02-01T11:00:00Z",
            "end_time": "2026-02-28T15:00:00Z",
            "discount_percent": 10.0,
            "impact_multiplier": 1.25,
        },
        {
            "id": generate_uuid("550e8400", 4),
            "name": "Happy Hour Drinks",
            "status": "active",
            "start_time": "2026-02-01T16:00:00Z",
            "end_time": "2026-02-28T19:00:00Z",
            "discount_percent": 25.0,
            "impact_multiplier": 1.5,
        },
        # Past campaigns (for historical data)
        {
            "id": generate_uuid("550e8400", 5),
            "name": "New Year Special",
            "status": "completed",
            "start_time": "2026-01-01T00:00:00Z",
            "end_time": "2026-01-07T23:59:59Z",
            "discount_percent": 30.0,
            "impact_multiplier": 2.0,
        },
        {
            "id": generate_uuid("550e8400", 6),
            "name": "January Flash Sale",
            "status": "completed",
            "start_time": "2026-01-15T12:00:00Z",
            "end_time": "2026-01-15T20:00:00Z",
            "discount_percent": 40.0,
            "impact_multiplier": 2.5,
        },
        # Upcoming campaigns
        {
            "id": generate_uuid("550e8400", 7),
            "name": "Spring Break Promo",
            "status": "scheduled",
            "start_time": "2026-03-01T00:00:00Z",
            "end_time": "2026-03-15T23:59:59Z",
            "discount_percent": 20.0,
            "impact_multiplier": 1.6,
        },
        # Low impact campaign
        {
            "id": generate_uuid("550e8400", 8),
            "name": "Loyalty Member Discount",
            "status": "active",
            "start_time": "2026-01-01T00:00:00Z",
            "end_time": "2026-12-31T23:59:59Z",
            "discount_percent": 5.0,
            "impact_multiplier": 1.05,
        },
        # High discount weekend
        {
            "id": generate_uuid("550e8400", 9),
            "name": "Super Bowl Sunday",
            "status": "completed",
            "start_time": "2026-02-08T15:00:00Z",
            "end_time": "2026-02-08T23:59:59Z",
            "discount_percent": 25.0,
            "impact_multiplier": 3.0,  # Massive surge
        },
        # Pasta week
        {
            "id": generate_uuid("550e8400", 10),
            "name": "Pasta Lovers Week",
            "status": "completed",
            "start_time": "2026-01-20T00:00:00Z",
            "end_time": "2026-01-26T23:59:59Z",
            "discount_percent": 15.0,
            "impact_multiplier": 1.3,
        },
    ]
    
    return campaigns


def generate_campaign_items(campaigns: List[Dict], items: List[Dict]) -> List[Dict]:
    """Link campaigns to specific items."""
    campaign_items = []
    
    # Map campaign types to item categories
    campaign_category_map = {
        "Valentine's Day Special": ["Pizza", "Pasta", "Desserts"],
        "Weekend Pizza Deal": ["Pizza"],
        "Lunch Hour Special": ["Pasta", "Salads", "Appetizers"],
        "Happy Hour Drinks": ["Beverages"],
        "New Year Special": ["Pizza", "Pasta", "Desserts", "Beverages"],
        "January Flash Sale": ["Pizza", "Pasta", "Appetizers"],
        "Spring Break Promo": ["Pizza", "Beverages"],
        "Loyalty Member Discount": ["Pizza", "Pasta"],
        "Super Bowl Sunday": ["Pizza", "Appetizers", "Beverages"],
        "Pasta Lovers Week": ["Pasta"],
    }
    
    for campaign in campaigns:
        categories = campaign_category_map.get(campaign["name"], ["Pizza"])
        
        for item in items:
            if item.get("category") in categories:
                campaign_items.append({
                    "campaign_id": campaign["id"],
                    "item_id": item["item_id"],
                })
    
    return campaign_items


# ============================================================================
# DEMAND PATTERNS
# ============================================================================

def get_base_hourly_demand(hour: int) -> float:
    """Base demand multiplier by hour of day."""
    # Model realistic restaurant traffic patterns
    patterns = {
        10: 0.3,   # Opening - slow
        11: 0.6,   # Pre-lunch
        12: 1.0,   # Lunch peak
        13: 0.9,   # Lunch
        14: 0.5,   # Post-lunch lull
        15: 0.3,   # Afternoon slow
        16: 0.4,   # Pre-dinner
        17: 0.7,   # Early dinner
        18: 1.0,   # Dinner peak
        19: 1.2,   # Dinner peak
        20: 0.9,   # Late dinner
        21: 0.6,   # Winding down
        22: 0.3,   # Late night
    }
    return patterns.get(hour, 0.2)


def get_day_of_week_multiplier(day: int) -> float:
    """Demand multiplier by day of week (0=Monday)."""
    multipliers = {
        0: 0.8,   # Monday - slow
        1: 0.85,  # Tuesday
        2: 0.9,   # Wednesday
        3: 0.95,  # Thursday
        4: 1.2,   # Friday - busy
        5: 1.4,   # Saturday - busiest
        6: 1.1,   # Sunday
    }
    return multipliers.get(day, 1.0)


def get_special_event_multiplier(dt: datetime) -> Tuple[float, str]:
    """Check for special events and return multiplier."""
    # Special dates with surge events
    special_events = {
        (1, 1): (2.0, "New Year's Day"),
        (1, 15): (2.5, "Flash Sale"),
        (2, 8): (3.0, "Super Bowl Sunday"),
        (2, 14): (2.5, "Valentine's Day"),
        (2, 21): (1.5, "Presidents Day Weekend"),
    }
    
    key = (dt.month, dt.day)
    if key in special_events:
        return special_events[key]
    
    return (1.0, None)


def get_weather_effect(dt: datetime) -> float:
    """Simulate weather effects on demand (random but seeded)."""
    # Use date as seed for consistent "weather"
    day_seed = dt.toordinal()
    random.seed(day_seed)
    
    # 10% chance of bad weather reducing demand
    # 5% chance of great weather increasing demand
    roll = random.random()
    
    random.seed(RANDOM_SEED + len(str(dt)))  # Reset to main seed variation
    
    if roll < 0.10:
        return 0.7  # Bad weather
    elif roll > 0.95:
        return 1.15  # Great weather
    return 1.0


def calculate_orders_for_hour(dt: datetime, base_orders: int = 15) -> int:
    """Calculate number of orders for a given hour."""
    hour = dt.hour
    day = dt.weekday()
    
    # Base hourly pattern
    demand = base_orders * get_base_hourly_demand(hour)
    
    # Day of week effect
    demand *= get_day_of_week_multiplier(day)
    
    # Special events
    event_mult, event_name = get_special_event_multiplier(dt)
    demand *= event_mult
    
    # Weather
    demand *= get_weather_effect(dt)
    
    # Add some randomness (+/- 20%)
    demand *= random.uniform(0.8, 1.2)
    
    return max(1, int(round(demand)))


# ============================================================================
# ORDER GENERATION
# ============================================================================

def generate_order_items_for_order(items: List[Dict], order_type: str, 
                                   campaign_items_set: set) -> List[Tuple[str, int]]:
    """Generate items for a single order."""
    order_items = []
    
    # Determine number of items based on order type
    if order_type == "delivery":
        num_items = random.choices([2, 3, 4, 5], weights=[0.2, 0.4, 0.3, 0.1])[0]
    elif order_type == "dine in":
        num_items = random.choices([2, 3, 4, 5, 6], weights=[0.1, 0.3, 0.35, 0.2, 0.05])[0]
    else:  # takeaway
        num_items = random.choices([1, 2, 3, 4], weights=[0.2, 0.4, 0.3, 0.1])[0]
    
    # Select items based on category popularity
    selected = []
    attempts = 0
    
    while len(selected) < num_items and attempts < 50:
        item = random.choice(items)
        
        # Check popularity
        if random.random() < item["popularity"]:
            # Boost items in active campaigns
            if item["item_id"] in campaign_items_set:
                boost = 1.5  # 50% more likely
            else:
                boost = 1.0
            
            if random.random() < boost * 0.7:  # Base selection rate
                quantity = random.choices([1, 2, 3], weights=[0.7, 0.25, 0.05])[0]
                selected.append((item["item_id"], quantity, item["price"]))
        
        attempts += 1
    
    # Ensure at least one item
    if not selected:
        item = random.choice(items)
        selected.append((item["item_id"], 1, item["price"]))
    
    return selected


def generate_orders_and_items(items: List[Dict], campaigns: List[Dict], 
                              campaign_items: List[Dict]) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """Generate orders, order_items, and deliveries."""
    orders = []
    all_order_items = []
    deliveries = []
    
    # Build campaign items set for quick lookup
    campaign_items_by_date = {}
    for camp in campaigns:
        start = datetime.fromisoformat(camp["start_time"].replace("Z", "+00:00")).replace(tzinfo=None)
        end = datetime.fromisoformat(camp["end_time"].replace("Z", "+00:00")).replace(tzinfo=None)
        
        if camp["id"] not in campaign_items_by_date:
            campaign_items_by_date[camp["id"]] = (start, end, set())
        
        for ci in campaign_items:
            if ci["campaign_id"] == camp["id"]:
                campaign_items_by_date[camp["id"]][2].add(ci["item_id"])
    
    order_index = 1
    user_index = 1
    driver_index = 1
    
    current = START_DATE
    
    while current <= END_DATE:
        # Skip non-operating hours
        for hour in range(OPEN_HOUR, CLOSE_HOUR):
            dt = current.replace(hour=hour)
            
            # Get active campaign items for this datetime
            active_campaign_items = set()
            for camp_id, (start, end, item_set) in campaign_items_by_date.items():
                if start <= dt <= end:
                    active_campaign_items.update(item_set)
            
            # Calculate orders for this hour
            num_orders = calculate_orders_for_hour(dt)
            
            for _ in range(num_orders):
                # Random minute within the hour
                minute = random.randint(0, 59)
                order_time = dt.replace(minute=minute, second=0)
                
                # Order type distribution
                order_type = random.choices(
                    ["dine in", "delivery", "takeaway"],
                    weights=[0.45, 0.35, 0.20]
                )[0]
                
                # Generate order items
                order_item_list = generate_order_items_for_order(
                    items, order_type, active_campaign_items
                )
                
                # Calculate totals
                total = sum(qty * price for _, qty, price in order_item_list)
                
                # Apply discount if in campaign
                discount = 0.0
                for camp in campaigns:
                    start = datetime.fromisoformat(camp["start_time"].replace("Z", "+00:00")).replace(tzinfo=None)
                    end = datetime.fromisoformat(camp["end_time"].replace("Z", "+00:00")).replace(tzinfo=None)
                    
                    if start <= order_time <= end:
                        # Check if any ordered item is in this campaign
                        camp_item_ids = {ci["item_id"] for ci in campaign_items 
                                        if ci["campaign_id"] == camp["id"]}
                        ordered_ids = {item_id for item_id, _, _ in order_item_list}
                        
                        if camp_item_ids & ordered_ids:
                            discount = max(discount, camp["discount_percent"])
                
                discount_amount = total * (discount / 100)
                final_total = total - discount_amount
                
                # Rating based on various factors
                base_rating = 4.2
                if order_type == "delivery":
                    base_rating -= 0.2  # Delivery slightly lower
                if discount > 15:
                    base_rating += 0.2  # Happy about discounts
                
                rating = min(5.0, max(1.0, base_rating + random.uniform(-0.5, 0.5)))
                rating = round(rating, 1)
                
                # Order status
                status = "completed" if random.random() < 0.95 else "cancelled"
                
                order_id = generate_uuid("770e8400", order_index)
                user_id = generate_uuid("550e8400", (user_index % 1000) + 1)
                
                orders.append({
                    "order_id": order_id,
                    "user_id": user_id,
                    "create_time": order_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "order_type": order_type,
                    "order_status": status,
                    "total_amount": round(final_total, 2),
                    "discount_amount": round(discount_amount, 2),
                    "rating": rating if status == "completed" else "",
                })
                
                # Add order items
                for item_id, quantity, price in order_item_list:
                    all_order_items.append({
                        "order_id": order_id,
                        "item_id": item_id,
                        "quantity": quantity,
                        "total_price": round(quantity * price, 2),
                    })
                
                # Generate delivery record
                if order_type == "delivery" and status == "completed":
                    # Delivery time varies
                    prep_time = random.randint(10, 25)  # minutes
                    delivery_time = random.randint(15, 45)  # minutes
                    
                    out_time = order_time + timedelta(minutes=prep_time)
                    delivered_time = out_time + timedelta(minutes=delivery_time)
                    
                    # Location around Copenhagen
                    base_lat, base_lon = 55.6761, 12.5683
                    lat = base_lat + random.uniform(-0.02, 0.02)
                    lon = base_lon + random.uniform(-0.02, 0.02)
                    
                    driver_id = generate_uuid("990e8400", (driver_index % 10) + 1)
                    
                    deliveries.append({
                        "order_id": order_id,
                        "driver_id": driver_id,
                        "delivery_latitude": round(lat, 4),
                        "delivery_longitude": round(lon, 4),
                        "out_for_delivery_time": out_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "delivered_time": delivered_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "status": "delivered",
                    })
                    
                    driver_index += 1
                
                order_index += 1
                user_index += 1
        
        current += timedelta(days=1)
    
    return orders, all_order_items, deliveries


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def save_csv(data: List[Dict], filename: str, fieldnames: List[str]):
    """Save data to CSV file."""
    filepath = OUTPUT_DIR / filename
    
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(data)
    
    print(f"  Saved {len(data)} records to {filename}")


def main():
    """Generate all test data."""
    print("=" * 60)
    print("GENERATING COMPREHENSIVE TEST DATA")
    print("=" * 60)
    print(f"Date range: {START_DATE.date()} to {END_DATE.date()}")
    print(f"Output directory: {OUTPUT_DIR}")
    print()
    
    # Create output directory if needed
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Generate items
    print("Generating menu items...")
    items = generate_items()
    save_csv(items, "items.csv", ["item_id", "name", "needed_employees", "price"])
    
    # Generate campaigns
    print("Generating campaigns...")
    campaigns = generate_campaigns()
    save_csv(campaigns, "campaigns.csv", 
             ["id", "name", "status", "start_time", "end_time", "discount_percent"])
    
    # Generate campaign items
    print("Generating campaign-item links...")
    campaign_items = generate_campaign_items(campaigns, items)
    save_csv(campaign_items, "campaign_items.csv", ["campaign_id", "item_id"])
    
    # Generate orders, order items, and deliveries
    print("Generating orders (this may take a moment)...")
    orders, order_items, deliveries = generate_orders_and_items(
        items, campaigns, campaign_items
    )
    
    save_csv(orders, "orders.csv", 
             ["order_id", "user_id", "create_time", "order_type", 
              "order_status", "total_amount", "discount_amount", "rating"])
    
    save_csv(order_items, "order_items.csv",
             ["order_id", "item_id", "quantity", "total_price"])
    
    save_csv(deliveries, "deliveries.csv",
             ["order_id", "driver_id", "delivery_latitude", "delivery_longitude",
              "out_for_delivery_time", "delivered_time", "status"])
    
    # Summary statistics
    print()
    print("=" * 60)
    print("GENERATION COMPLETE - SUMMARY")
    print("=" * 60)
    print(f"  Items: {len(items)}")
    print(f"  Campaigns: {len(campaigns)}")
    print(f"  Campaign-Item links: {len(campaign_items)}")
    print(f"  Orders: {len(orders)}")
    print(f"  Order items: {len(order_items)}")
    print(f"  Deliveries: {len(deliveries)}")
    
    # Scenario coverage
    print()
    print("SCENARIO COVERAGE:")
    
    # Order type distribution
    order_types = {}
    for o in orders:
        order_types[o["order_type"]] = order_types.get(o["order_type"], 0) + 1
    print(f"  Order types: {order_types}")
    
    # Orders by day of week
    from collections import Counter
    days = Counter()
    for o in orders:
        dt = datetime.fromisoformat(o["create_time"].replace("Z", ""))
        days[dt.strftime("%A")] += 1
    print(f"  By day of week: {dict(days)}")
    
    # Orders with discounts
    discounted = sum(1 for o in orders if float(o["discount_amount"]) > 0)
    print(f"  Orders with discounts: {discounted} ({100*discounted/len(orders):.1f}%)")
    
    # Surge events (high volume days)
    daily_counts = Counter()
    for o in orders:
        dt = datetime.fromisoformat(o["create_time"].replace("Z", ""))
        daily_counts[dt.date()] += 1
    
    avg_daily = sum(daily_counts.values()) / len(daily_counts)
    surge_days = [(d, c) for d, c in daily_counts.items() if c > avg_daily * 1.5]
    print(f"  Average daily orders: {avg_daily:.1f}")
    print(f"  Surge days (>1.5x avg): {len(surge_days)}")
    for d, c in sorted(surge_days, key=lambda x: -x[1])[:5]:
        print(f"    {d}: {c} orders")
    
    print()
    print("Test data ready for end-to-end testing!")


if __name__ == "__main__":
    main()
