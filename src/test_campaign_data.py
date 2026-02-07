"""
Test Campaign Recommendation API with Real Data
"""

import requests
import json
import pandas as pd
from datetime import datetime, timedelta

def load_training_data():
    """Load training data for testing"""
    orders_df = pd.read_csv('data/training/orders.csv')
    campaigns_df = pd.read_csv('data/training/campaigns.csv')
    order_items_df = pd.read_csv('data/training/order_items.csv')
    
    return orders_df, campaigns_df, order_items_df


def create_api_request(orders_df, campaigns_df, order_items_df):
    """Create API request from dataframes - WITHOUT weather/holiday data"""
    
    # Convert orders to API format (use last 60 days)
    cutoff_timestamp = orders_df['created'].max() - (60 * 24 * 3600)
    recent_orders = orders_df[orders_df['created'] >= cutoff_timestamp]
    
    orders_list = []
    for _, row in recent_orders.head(100).iterrows():  # Use 100 recent orders
        orders_list.append({
            'time': datetime.fromtimestamp(row['created']).isoformat(),
            'items': int(row['item_count']),
            'status': row['status'],
            'total_amount': float(row['total_amount']),
            'discount_amount': float(row['discount_amount'])
        })
    
    # Convert campaigns
    campaigns_list = []
    for _, row in campaigns_df.iterrows():
        campaigns_list.append({
            'start_time': row['start_time'],
            'end_time': row['end_time'],
            'items_included': eval(row['items_included']) if isinstance(row['items_included'], str) else row['items_included'],
            'discount': float(row['discount'])
        })
    
    # Convert order items (match with orders)
    order_ids = recent_orders.head(100)['id'].values
    matching_items = order_items_df[order_items_df['order_id'].isin(order_ids)]
    
    order_items_list = []
    for _, row in matching_items.head(200).iterrows():
        order_items_list.append({
            'order_id': row['order_id'],
            'item_id': row['item_id'],
            'quantity': int(row['quantity'])
        })
    
    # Build request WITHOUT weather/holiday data
    request = {
        'place': {
            'place_id': 'pizza_paradise_001',
            'place_name': 'Pizza Paradise',
            'type': 'restaurant',
            'latitude': 55.6761,  # Copenhagen - weather will be auto-fetched
            'longitude': 12.5683,
            'waiting_time': 30,
            'receiving_phone': True,
            'delivery': True,
            'opening_hours': {
                'monday': {'from': '10:00', 'to': '23:00'},
                'tuesday': {'from': '10:00', 'to': '23:00'},
                'wednesday': {'from': '10:00', 'to': '23:00'},
                'thursday': {'from': '10:00', 'to': '23:00'},
                'friday': {'from': '10:00', 'to': '23:00'},
                'saturday': {'from': '11:00', 'to': '23:00'},
                'sunday': {'closed': True}
            },
            'fixed_shifts': True,
            'number_of_shifts_per_day': 3,
            'shift_times': ['10:00-15:00', '15:00-20:00', '20:00-23:00'],
            'rating': 4.5,
            'accepting_orders': True
        },
        'orders': orders_list,
        'campaigns': campaigns_list,
        'order_items': order_items_list,
        'recommendation_start_date': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
        'num_recommendations': 5,
        'optimize_for': 'roi',
        'max_discount': 30.0,
        'min_campaign_duration_days': 3,
        'max_campaign_duration_days': 14,
        'available_items': [
            'pizza_margherita', 'pizza_pepperoni', 'pizza_quattro_formaggi',
            'pasta_carbonara', 'pasta_bolognese', 'pasta_arrabbiata',
            'salad_caesar', 'salad_greek',
            'drink_cola', 'drink_water', 'drink_juice',
            'dessert_tiramisu', 'dessert_panna_cotta'
        ]
        # NOTE: weather_forecast and upcoming_holidays NOT included!
        # They will be automatically fetched by the API based on coordinates
    }
    
    return request


def test_campaign_recommendations():
    """Test campaign recommendation endpoint"""
    
    print("="*80)
    print("TESTING CAMPAIGN RECOMMENDATION API")
    print("="*80)
    
    # Load data
    print("\n1. Loading training data...")
    orders_df, campaigns_df, order_items_df = load_training_data()
    print(f"   ✓ Loaded {len(orders_df)} orders")
    print(f"   ✓ Loaded {len(campaigns_df)} campaigns")
    print(f"   ✓ Loaded {len(order_items_df)} order items")
    
    # Create request
    print("\n2. Creating API request...")
    request = create_api_request(orders_df, campaigns_df, order_items_df)
    print(f"   ✓ Using {len(request['orders'])} recent orders")
    print(f"   ✓ Using {len(request['campaigns'])} historical campaigns")
    print(f"   ✓ Using {len(request['order_items'])} order items")
    print(f"   ✓ Location: {request['place']['latitude']}, {request['place']['longitude']}")
    print(f"   ✓ Weather & holidays will be auto-fetched by API")
    
    # Make API call
    print("\n3. Calling API...")
    try:
        response = requests.post(
            'http://localhost:8000/recommend/campaigns',
            json=request,
            timeout=60  # Increased timeout for weather/holiday API calls
        )
        
        if response.status_code == 200:
            print("   ✓ API call successful!")
            
            data = response.json()
            
            # Display results
            print("\n" + "="*80)
            print("RECOMMENDATIONS")
            print("="*80)
            
            print(f"\nRestaurant: {data['restaurant_name']}")
            print(f"Generated: {data['recommendation_date']}")
            print(f"Model Confidence: {data['confidence_level'].upper()}")
            
            # Analysis summary
            if 'analysis_summary' in data and data['analysis_summary'].get('total_campaigns_analyzed', 0) > 0:
                summary = data['analysis_summary']
                print(f"\n📊 Historical Analysis:")
                print(f"   • Campaigns Analyzed: {summary['total_campaigns_analyzed']}")
                print(f"   • Average ROI: {summary['avg_roi']:.1f}%")
                print(f"   • Success Rate: {summary['success_rate']:.1f}%")
            
            # Insights
            if 'insights' in data and data['insights']:
                insights = data['insights']
                if 'best_day_of_week' in insights:
                    print(f"\n💡 Key Insights:")
                    best_day = insights['best_day_of_week']
                    print(f"   • Best Day: {best_day['day']}")
                
                if 'top_item_pairs' in insights and insights['top_item_pairs']:
                    print(f"   • Top Item Pairs:")
                    for pair in insights['top_item_pairs'][:3]:
                        items = ' + '.join(pair['items'])
                        score = pair['affinity_score']
                        print(f"     - {items} (affinity: {score:.2f})")
            
            # Recommendations
            print(f"\n🎯 TOP {len(data['recommendations'])} RECOMMENDATIONS:\n")
            
            for idx, rec in enumerate(data['recommendations'], 1):
                print(f"{idx}. {', '.join(rec['items']).upper()}")
                print(f"   Discount: {rec['discount_percentage']:.1f}%")
                print(f"   Duration: {rec['start_date']} to {rec['end_date']} ({rec['duration_days']} days)")
                print(f"   Expected ROI: {rec['expected_roi']:.1f}%")
                print(f"   Expected Revenue: ${rec['expected_revenue']:,.2f}")
                print(f"   Confidence: {rec['confidence_score']:.0%}")
                print(f"   Reasoning: {rec['reasoning']}")
                print()
            
            # Save response
            import os
            os.makedirs('data/testing', exist_ok=True)
            
            with open('data/testing/campaign_recommendations.json', 'w') as f:
                json.dump(data, f, indent=2)
            
            print("="*80)
            print("✅ TEST SUCCESSFUL!")
            print(f"Full response saved to: data/testing/campaign_recommendations.json")
            print("="*80)
            print("\n🌦️  Weather data was automatically fetched from Open-Meteo API")
            print("🎉 Holiday data was automatically fetched from Nominatim + holidays library")
            
        else:
            print(f"   ❌ API Error: {response.status_code}")
            print(f"   {response.json()}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")


if __name__ == "__main__":
    test_campaign_recommendations()