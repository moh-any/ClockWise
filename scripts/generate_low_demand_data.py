"""Generate test data for a low-demand restaurant with plenty of employees."""
import csv
import random
import os
from datetime import datetime, timedelta

random.seed(42)
OUT = os.path.join(os.path.dirname(os.path.dirname(__file__)), "test-data")

# ============================================================
# EMPLOYEES - 35 employees (plenty for low demand)
# ============================================================
first_names = [
    "Sofia", "Emma", "Lukas", "Oliver", "Amelia", "Mason", "Isabella", "Evelyn",
    "Abigail", "Ava", "Lucas", "Olivia", "Noah", "Mia", "Harper", "James",
    "Charlotte", "Liam", "Ella", "Benjamin", "Aria", "Ethan", "Lily", "Alexander",
    "Chloe", "William", "Grace", "Daniel", "Nora", "Sebastian", "Hannah", "Leo",
    "Zoe", "Henry", "Victoria",
]
last_names = [
    "Jensen", "Nielsen", "Hansen", "Pedersen", "Andersen", "Christensen", "Larsen",
    "Sorensen", "Rasmussen", "Olsen", "Thomsen", "Kristensen", "Jorgensen", "Madsen",
    "Mortensen", "Frederiksen", "Berg", "Lund", "Holm", "Moller", "Dahl", "Eriksen",
    "Bakke", "Strand", "Aas", "Haugen", "Lie", "Berge", "Vik", "Solberg", "Dale",
    "Nygaard", "Brun", "Hagen", "Roed",
]
roles_pool = ["waiter", "cook", "bartender", "host", "delivery", "cleaner"]

with open(os.path.join(OUT, "employees.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["full_name", "email", "role", "hourly_salary", "roles"])
    for i in range(35):
        fn = first_names[i]
        ln = last_names[i]
        full = f"{fn} {ln}"
        email = f"{fn.lower()}.{ln.lower()}{i+1}@example.com"
        if i < 2:
            role = "admin"
        elif i < 5:
            role = "manager"
        else:
            role = "employee"
        salary = round(random.uniform(12.0, 26.0), 2)
        n_roles = random.randint(1, 3)
        eroles = random.sample(roles_pool, min(n_roles, len(roles_pool)))
        roles_str = "[" + ", ".join(f'"{r}"' for r in eroles) + "]"
        w.writerow([full, email, role, salary, roles_str])

print("Employees: 35 rows")

# ============================================================
# ORDERS - LOW DEMAND: ~1-3 orders/hour during open hours
# 38 days: Jan 1 - Feb 7, 2026
# Open 10:00-22:00, ~2 orders/hour avg = ~24/day
# Total ~900 orders (vs original ~8700)
# ============================================================
order_rows = []
order_idx = 0
start_date = datetime(2026, 1, 1)
num_days = 38
user_base = 50

for day_offset in range(num_days):
    current = start_date + timedelta(days=day_offset)
    dow = current.weekday()

    for hour in range(10, 22):
        if hour in [12, 13]:
            avg_orders = 3
        elif hour in [18, 19, 20]:
            avg_orders = 3
        else:
            avg_orders = 1

        if dow >= 5:
            avg_orders = int(avg_orders * 1.3)

        n_orders = max(0, random.randint(max(0, avg_orders - 1), avg_orders + 1))

        for _ in range(n_orders):
            order_idx += 1
            oid = f"770e8400-e29b-41d4-a716-{order_idx:012d}"
            uid_num = random.randint(1, user_base)
            uid = f"550e8400-e29b-41d4-a716-{uid_num:012d}"
            minute = random.randint(0, 59)
            ts = current.replace(hour=hour, minute=minute)
            ts_str = ts.strftime("%Y-%m-%dT%H:%M:%SZ")
            otype = random.choice(["dine in", "dine in", "dine in", "takeaway", "delivery"])
            amount = round(random.uniform(12.0, 45.0), 2)
            discount = round(amount * random.uniform(0, 0.15), 2)
            rating = round(random.uniform(3.5, 5.0), 1)
            order_rows.append([oid, uid, ts_str, otype, "completed", amount, discount, rating])

with open(os.path.join(OUT, "orders.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["order_id", "user_id", "create_time", "order_type", "order_status", "total_amount", "discount_amount", "rating"])
    for row in order_rows:
        w.writerow(row)

print(f"Orders: {len(order_rows)} rows")

# ============================================================
# ORDER_ITEMS - 1-3 items per order (low quantity)
# ============================================================
item_prices = {
    1: 15.99, 2: 17.99, 3: 18.99, 4: 16.99, 5: 17.49, 6: 19.99, 7: 16.99, 8: 18.49,
    9: 14.99, 10: 15.99, 11: 13.99, 12: 16.99, 13: 15.49, 14: 18.99, 15: 5.99, 16: 7.99,
    17: 8.99, 18: 11.99, 19: 9.99, 20: 6.99, 21: 10.99, 22: 11.99, 23: 8.99, 24: 13.99,
    25: 7.99, 26: 6.99, 27: 5.99, 28: 7.49, 29: 2.99, 30: 3.49, 31: 2.99, 32: 4.99,
    33: 8.99, 34: 5.99, 35: 2.49, 36: 5.49,
}

oi_count = 0
with open(os.path.join(OUT, "order_items.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["order_id", "item_id", "quantity", "total_price"])
    for row in order_rows:
        oid = row[0]
        n_items = random.randint(1, 3)
        chosen = random.sample(range(1, 37), n_items)
        for item_num in chosen:
            iid = f"660e8400-e29b-41d4-a716-{item_num:012d}"
            qty = random.randint(1, 2)
            price = round(item_prices[item_num] * qty, 2)
            w.writerow([oid, iid, qty, price])
            oi_count += 1

print(f"Order items: {oi_count} rows")

# ============================================================
# DELIVERIES - only for delivery orders
# ============================================================
driver_ids = [f"990e8400-e29b-41d4-a716-{i:012d}" for i in range(1, 11)]
del_count = 0
with open(os.path.join(OUT, "deliveries.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["order_id", "driver_id", "delivery_latitude", "delivery_longitude", "out_for_delivery_time", "delivered_time", "status"])
    for row in order_rows:
        if row[3] == "delivery":
            oid = row[0]
            ts = datetime.strptime(row[2], "%Y-%m-%dT%H:%M:%SZ")
            driver = random.choice(driver_ids)
            lat = round(55.67 + random.uniform(-0.02, 0.02), 4)
            lon = round(12.57 + random.uniform(-0.02, 0.02), 4)
            out_time = ts + timedelta(minutes=random.randint(10, 25))
            delivered_time = out_time + timedelta(minutes=random.randint(15, 35))
            w.writerow([
                oid, driver, lat, lon,
                out_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                delivered_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "delivered",
            ])
            del_count += 1

print(f"Deliveries: {del_count} rows")

# ============================================================
# CAMPAIGNS - fewer/smaller campaigns
# ============================================================
camp_rows = [
    ["550e8400-e29b-41d4-a716-000000000001", "Valentines Day Special", "active", "2026-02-01T10:00:00Z", "2026-02-14T23:59:59Z", 15.0],
    ["550e8400-e29b-41d4-a716-000000000002", "Weekend Brunch Deal", "active", "2026-02-06T00:00:00Z", "2026-02-08T23:59:59Z", 10.0],
    ["550e8400-e29b-41d4-a716-000000000003", "Lunch Special", "active", "2026-02-01T11:00:00Z", "2026-02-28T15:00:00Z", 10.0],
    ["550e8400-e29b-41d4-a716-000000000004", "Happy Hour", "active", "2026-02-01T16:00:00Z", "2026-02-28T19:00:00Z", 15.0],
    ["550e8400-e29b-41d4-a716-000000000005", "New Year Special", "completed", "2026-01-01T00:00:00Z", "2026-01-07T23:59:59Z", 20.0],
]

with open(os.path.join(OUT, "campaigns.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["id", "name", "status", "start_time", "end_time", "discount_percent"])
    for row in camp_rows:
        w.writerow(row)

print(f"Campaigns: {len(camp_rows)} rows")

# ============================================================
# CAMPAIGN_ITEMS
# ============================================================
camp_item_map = {
    "550e8400-e29b-41d4-a716-000000000001": list(range(1, 15)),
    "550e8400-e29b-41d4-a716-000000000002": list(range(1, 9)),
    "550e8400-e29b-41d4-a716-000000000003": [9, 10, 11, 12, 13, 21, 22, 23],
    "550e8400-e29b-41d4-a716-000000000004": [29, 30, 31, 32, 33, 34, 35],
    "550e8400-e29b-41d4-a716-000000000005": list(range(1, 37)),
}

ci_count = 0
with open(os.path.join(OUT, "campaign_items.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["campaign_id", "item_id"])
    for cid, items in camp_item_map.items():
        for item_num in items:
            iid = f"660e8400-e29b-41d4-a716-{item_num:012d}"
            w.writerow([cid, iid])
            ci_count += 1

print(f"Campaign items: {ci_count} rows")
print("\nDone! All test-data CSVs regenerated for low-demand restaurant with plenty of employees.")
