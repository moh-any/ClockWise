"""
Generate Realistic Campaign Test Data
======================================
Creates comprehensive test datasets for campaign recommendation system.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
from pathlib import Path


def generate_realistic_orders(
    start_date: datetime,
    end_date: datetime,
    restaurant_id: str = "pizza_paradise_001"
) -> pd.DataFrame:
    """
    Generate realistic order data with patterns.
    
    Patterns:
    - Lunch rush: 11:00-14:00
    - Dinner rush: 18:00-21:00
    - Weekend boost: +30% orders
    - Friday/Saturday: +40% orders
    - Campaign periods: +25% orders with discount
    """
    
    orders = []
    order_id = 1000
    
    current_date = start_date
    while current_date <= end_date:
        day_of_week = current_date.weekday()  # 0=Monday, 6=Sunday
        
        # Closed on Sundays
        if day_of_week == 6:
            current_date += timedelta(days=1)
            continue
        
        # Base order count by hour (typical pattern)
        hourly_distribution = {
            10: 2, 11: 5, 12: 12, 13: 10, 14: 4,
            15: 2, 16: 3, 17: 5,
            18: 15, 19: 18, 20: 14, 21: 8, 22: 3
        }
        
        # Weekend multiplier
        if day_of_week >= 5:  # Saturday, Sunday
            weekend_multiplier = 1.4
        elif day_of_week == 4:  # Friday
            weekend_multiplier = 1.3
        else:
            weekend_multiplier = 1.0
        
        # Generate orders for each hour
        for hour, base_count in hourly_distribution.items():
            adjusted_count = int(base_count * weekend_multiplier)
            
            # Add some randomness
            actual_count = max(0, adjusted_count + np.random.randint(-2, 3))
            
            for _ in range(actual_count):
                # Random minute within the hour
                minute = np.random.randint(0, 60)
                order_time = current_date.replace(hour=hour, minute=minute, second=0)
                
                # Number of items (1-6, weighted towards 2-3)
                num_items = np.random.choice([1, 2, 3, 4, 5, 6], p=[0.1, 0.3, 0.3, 0.2, 0.08, 0.02])
                
                # Total amount (based on items)
                base_price = 12.5  # Average item price
                total_amount = round(num_items * base_price * np.random.uniform(0.8, 1.3), 2)
                
                # Discount (mostly 0, sometimes during campaigns)
                discount = 0.0
                
                orders.append({
                    'id': f'order_{order_id}',
                    'created': order_time.timestamp(),
                    'place_id': restaurant_id,
                    'total_amount': total_amount,
                    'item_count': num_items,
                    'status': 'completed',
                    'discount_amount': discount
                })
                
                order_id += 1
        
        current_date += timedelta(days=1)
    
    return pd.DataFrame(orders)


def generate_realistic_campaigns(
    start_date: datetime,
    end_date: datetime
) -> list:
    """
    Generate realistic campaign data with varied performance.
    
    Campaign types:
    1. High-performer: Pizza + Drink combo (15% discount)
    2. Medium-performer: Pasta + Salad (20% discount)
    3. Low-performer: Single item discount (25% discount)
    4. Weekend special: High discount, short duration
    5. Weekday lunch: Moderate discount, mid-week
    """
    
    campaigns = []
    
    # Calculate total days
    total_days = (end_date - start_date).days
    weeks = total_days // 7
    
    campaign_id = 1
    
    for week in range(weeks):
        week_start = start_date + timedelta(weeks=week)
        
        # Campaign 1: Pizza + Drink (runs every 3 weeks, high success)
        if week % 3 == 0:
            campaigns.append({
                'id': f'campaign_{campaign_id:03d}',
                'start_time': (week_start + timedelta(days=1)).isoformat(),
                'end_time': (week_start + timedelta(days=7)).isoformat(),
                'items_included': ['pizza_margherita', 'drink_cola'],
                'discount': 15.0,
                'performance': 'high',  # Metadata for simulation
                'expected_uplift': 28.5,
                'expected_roi': 185.0
            })
            campaign_id += 1
        
        # Campaign 2: Pasta + Salad (runs every 4 weeks, medium success)
        if week % 4 == 0:
            campaigns.append({
                'id': f'campaign_{campaign_id:03d}',
                'start_time': (week_start + timedelta(days=0)).isoformat(),
                'end_time': (week_start + timedelta(days=6)).isoformat(),
                'items_included': ['pasta_carbonara', 'salad_caesar'],
                'discount': 20.0,
                'performance': 'medium',
                'expected_uplift': 18.5,
                'expected_roi': 120.0
            })
            campaign_id += 1
        
        # Campaign 3: Weekend Pizza Special (every other week, variable)
        if week % 2 == 1:
            campaigns.append({
                'id': f'campaign_{campaign_id:03d}',
                'start_time': (week_start + timedelta(days=5)).isoformat(),  # Friday
                'end_time': (week_start + timedelta(days=6)).isoformat(),    # Saturday
                'items_included': ['pizza_pepperoni'],
                'discount': 25.0,
                'performance': 'medium',
                'expected_uplift': 35.0,
                'expected_roi': 95.0
            })
            campaign_id += 1
        
        # Campaign 4: Weekday Lunch Combo (every 5 weeks)
        if week % 5 == 0:
            campaigns.append({
                'id': f'campaign_{campaign_id:03d}',
                'start_time': (week_start + timedelta(days=1)).isoformat(),  # Tuesday
                'end_time': (week_start + timedelta(days=4)).isoformat(),    # Friday
                'items_included': ['pasta_bolognese', 'drink_water'],
                'discount': 12.0,
                'performance': 'low',
                'expected_uplift': 12.0,
                'expected_roi': 65.0
            })
            campaign_id += 1
    
    return campaigns


def generate_realistic_order_items(
    orders_df: pd.DataFrame,
    campaigns: list
) -> pd.DataFrame:
    """
    Generate realistic order-item relationships with affinity patterns.
    
    Item affinities:
    - Pizza + Cola: Very high (85% co-occurrence)
    - Pizza + Salad: Medium (40% co-occurrence)
    - Pasta + Salad: High (65% co-occurrence)
    - Any + Water: Low (20% co-occurrence)
    """
    
    menu_items = {
        'pizza_margherita': {'price': 12.0, 'category': 'pizza'},
        'pizza_pepperoni': {'price': 13.5, 'category': 'pizza'},
        'pizza_quattro_formaggi': {'price': 14.0, 'category': 'pizza'},
        'pasta_carbonara': {'price': 11.5, 'category': 'pasta'},
        'pasta_bolognese': {'price': 11.0, 'category': 'pasta'},
        'pasta_arrabbiata': {'price': 10.5, 'category': 'pasta'},
        'salad_caesar': {'price': 8.5, 'category': 'salad'},
        'salad_greek': {'price': 8.0, 'category': 'salad'},
        'drink_cola': {'price': 3.5, 'category': 'drink'},
        'drink_water': {'price': 2.0, 'category': 'drink'},
        'drink_juice': {'price': 4.0, 'category': 'drink'},
        'dessert_tiramisu': {'price': 6.5, 'category': 'dessert'},
        'dessert_panna_cotta': {'price': 6.0, 'category': 'dessert'}
    }
    
    order_items = []
    
    for _, order in orders_df.iterrows():
        order_id = order['id']
        num_items = order['item_count']
        
        # Start with a main item (pizza or pasta)
        if np.random.random() < 0.65:  # 65% pizza orders
            main_item = np.random.choice([
                'pizza_margherita', 'pizza_pepperoni', 'pizza_quattro_formaggi'
            ], p=[0.5, 0.35, 0.15])
        else:  # 35% pasta orders
            main_item = np.random.choice([
                'pasta_carbonara', 'pasta_bolognese', 'pasta_arrabbiata'
            ], p=[0.5, 0.3, 0.2])
        
        order_items.append({
            'order_id': order_id,
            'item_id': main_item,
            'quantity': 1
        })
        
        items_added = 1
        selected_items = {main_item}
        
        # Add complementary items based on affinity
        while items_added < num_items:
            category = menu_items[main_item]['category']
            
            # Add drink with high probability
            if 'drink' not in [menu_items[item]['category'] for item in selected_items]:
                if category == 'pizza' and np.random.random() < 0.85:
                    drink = np.random.choice(['drink_cola', 'drink_water', 'drink_juice'], 
                                            p=[0.7, 0.2, 0.1])
                    order_items.append({
                        'order_id': order_id,
                        'item_id': drink,
                        'quantity': 1
                    })
                    selected_items.add(drink)
                    items_added += 1
                    continue
                elif category == 'pasta' and np.random.random() < 0.65:
                    drink = np.random.choice(['drink_water', 'drink_cola', 'drink_juice'], 
                                            p=[0.5, 0.3, 0.2])
                    order_items.append({
                        'order_id': order_id,
                        'item_id': drink,
                        'quantity': 1
                    })
                    selected_items.add(drink)
                    items_added += 1
                    continue
            
            # Add salad
            if 'salad' not in [menu_items[item]['category'] for item in selected_items]:
                if category == 'pasta' and np.random.random() < 0.65:
                    salad = np.random.choice(['salad_caesar', 'salad_greek'], p=[0.7, 0.3])
                    order_items.append({
                        'order_id': order_id,
                        'item_id': salad,
                        'quantity': 1
                    })
                    selected_items.add(salad)
                    items_added += 1
                    continue
                elif category == 'pizza' and np.random.random() < 0.40:
                    salad = np.random.choice(['salad_caesar', 'salad_greek'], p=[0.6, 0.4])
                    order_items.append({
                        'order_id': order_id,
                        'item_id': salad,
                        'quantity': 1
                    })
                    selected_items.add(salad)
                    items_added += 1
                    continue
            
            # Add dessert (lower probability)
            if 'dessert' not in [menu_items[item]['category'] for item in selected_items]:
                if np.random.random() < 0.25:
                    dessert = np.random.choice(['dessert_tiramisu', 'dessert_panna_cotta'], 
                                              p=[0.6, 0.4])
                    order_items.append({
                        'order_id': order_id,
                        'item_id': dessert,
                        'quantity': 1
                    })
                    selected_items.add(dessert)
                    items_added += 1
                    continue
            
            # If still need items, add another main or random
            remaining_items = [item for item in menu_items.keys() if item not in selected_items]
            if remaining_items:
                random_item = np.random.choice(remaining_items)
                order_items.append({
                    'order_id': order_id,
                    'item_id': random_item,
                    'quantity': 1
                })
                selected_items.add(random_item)
                items_added += 1
            else:
                break
    
    return pd.DataFrame(order_items)


def apply_campaign_effects(
    orders_df: pd.DataFrame,
    campaigns: list
) -> pd.DataFrame:
    """
    Apply campaign effects to orders (increase volume, add discounts).
    """
    
    orders_with_campaigns = orders_df.copy()
    
    for campaign in campaigns:
        start_time = pd.to_datetime(campaign['start_time']).timestamp()
        end_time = pd.to_datetime(campaign['end_time']).timestamp()
        
        # Find orders during campaign
        campaign_mask = (
            (orders_with_campaigns['created'] >= start_time) &
            (orders_with_campaigns['created'] <= end_time)
        )
        
        # Apply discount to campaign orders
        discount_rate = campaign['discount'] / 100
        orders_with_campaigns.loc[campaign_mask, 'discount_amount'] = \
            orders_with_campaigns.loc[campaign_mask, 'total_amount'] * discount_rate
        
        # Simulate uplift by duplicating some orders (based on performance)
        if campaign['performance'] == 'high':
            uplift_rate = 0.25  # 25% more orders
        elif campaign['performance'] == 'medium':
            uplift_rate = 0.15  # 15% more orders
        else:
            uplift_rate = 0.08  # 8% more orders
        
        campaign_orders = orders_with_campaigns[campaign_mask]
        num_extra_orders = int(len(campaign_orders) * uplift_rate)
        
        if num_extra_orders > 0:
            # Sample and duplicate orders
            extra_orders = campaign_orders.sample(n=num_extra_orders, replace=True).copy()
            
            # Adjust timestamps slightly
            extra_orders['created'] = extra_orders['created'] + np.random.randint(60, 3600, size=len(extra_orders))
            
            # New order IDs
            max_order_id = int(orders_with_campaigns['id'].str.replace('order_', '').astype(int).max())
            extra_orders['id'] = [f'order_{max_order_id + i + 1}' for i in range(len(extra_orders))]
            
            # Append to main dataframe
            orders_with_campaigns = pd.concat([orders_with_campaigns, extra_orders], ignore_index=True)
    
    return orders_with_campaigns.sort_values('created').reset_index(drop=True)


def save_dataset(
    orders_df: pd.DataFrame,
    campaigns: list,
    order_items_df: pd.DataFrame,
    output_dir: str = "data/training"
):
    """Save dataset to files"""
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Save orders
    orders_df.to_csv(output_path / "orders.csv", index=False)
    print(f"✓ Saved {len(orders_df)} orders to {output_path / 'orders.csv'}")
    
    # Save campaigns
    campaigns_df = pd.DataFrame(campaigns)
    # Remove metadata columns
    campaigns_df = campaigns_df.drop(columns=['performance', 'expected_uplift', 'expected_roi'], errors='ignore')
    campaigns_df.to_csv(output_path / "campaigns.csv", index=False)
    print(f"✓ Saved {len(campaigns_df)} campaigns to {output_path / 'campaigns.csv'}")
    
    # Save order items
    order_items_df.to_csv(output_path / "order_items.csv", index=False)
    print(f"✓ Saved {len(order_items_df)} order-item relationships to {output_path / 'order_items.csv'}")
    
    # Save metadata
    metadata = {
        'generated_at': datetime.now().isoformat(),
        'date_range': {
            'start': datetime.fromtimestamp(orders_df['created'].min()).isoformat(),
            'end': datetime.fromtimestamp(orders_df['created'].max()).isoformat()
        },
        'statistics': {
            'total_orders': len(orders_df),
            'total_campaigns': len(campaigns_df),
            'total_order_items': len(order_items_df),
            'avg_order_value': float(orders_df['total_amount'].mean()),
            'avg_items_per_order': float(orders_df['item_count'].mean()),
            'total_revenue': float(orders_df['total_amount'].sum()),
            'total_discounts': float(orders_df['discount_amount'].sum())
        }
    }
    
    with open(output_path / "metadata.json", 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"✓ Saved metadata to {output_path / 'metadata.json'}")
    
    return metadata


def main():
    """Generate complete test dataset"""
    
    print("="*80)
    print("Generating Realistic Campaign Test Dataset")
    print("="*80)
    
    # Generate 6 months of data
    start_date = datetime(2023, 7, 1)
    end_date = datetime(2024, 1, 31)
    
    print(f"\n1. Generating orders from {start_date.date()} to {end_date.date()}...")
    orders_df_base = generate_realistic_orders(start_date, end_date)
    print(f"   Generated {len(orders_df_base)} base orders")
    
    print(f"\n2. Generating campaigns...")
    campaigns = generate_realistic_campaigns(start_date, end_date)
    print(f"   Generated {len(campaigns)} campaigns")
    
    print(f"\n3. Applying campaign effects to orders...")
    orders_df = apply_campaign_effects(orders_df_base, campaigns)
    print(f"   Final order count: {len(orders_df)} (uplift from campaigns)")
    
    print(f"\n4. Generating order items with realistic affinities...")
    order_items_df = generate_realistic_order_items(orders_df, campaigns)
    print(f"   Generated {len(order_items_df)} order-item relationships")
    
    print(f"\n5. Saving dataset...")
    metadata = save_dataset(orders_df, campaigns, order_items_df, "data/training")
    
    print("\n" + "="*80)
    print("DATASET GENERATION COMPLETE!")
    print("="*80)
    
    print(f"\n📊 Dataset Statistics:")
    print(f"   • Date Range: {metadata['date_range']['start'][:10]} to {metadata['date_range']['end'][:10]}")
    print(f"   • Total Orders: {metadata['statistics']['total_orders']:,}")
    print(f"   • Total Campaigns: {metadata['statistics']['total_campaigns']}")
    print(f"   • Avg Order Value: ${metadata['statistics']['avg_order_value']:.2f}")
    print(f"   • Avg Items/Order: {metadata['statistics']['avg_items_per_order']:.1f}")
    print(f"   • Total Revenue: ${metadata['statistics']['total_revenue']:,.2f}")
    print(f"   • Total Discounts: ${metadata['statistics']['total_discounts']:,.2f}")
    
    print(f"\n📁 Files created:")
    print(f"   • data/training/orders.csv")
    print(f"   • data/training/campaigns.csv")
    print(f"   • data/training/order_items.csv")
    print(f"   • data/training/metadata.json")
    
    print(f"\n🚀 Next Steps:")
    print(f"   1. Train the model:")
    print(f"      python scripts/train_campaign_model.py")
    print(f"   ")
    print(f"   2. Test with the API:")
    print(f"      python test_campaign_api.py")
    print(f"   ")
    print(f"   3. View results:")
    print(f"      cat data/models/campaign_recommender_metadata.json")


if __name__ == "__main__":
    main()