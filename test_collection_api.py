"""
Test script for Data Collection API
Backend team can use this as reference for integration
"""

import requests
import json
from datetime import datetime


API_BASE_URL = "http://localhost:8000/api/v1/collect"


def test_health_check():
    """Test 1: Check if API is healthy"""
    print("=" * 60)
    print("TEST 1: Health Check")
    print("=" * 60)
    
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_single_venue():
    """Test 2: Collect metrics for single venue"""
    print("\n" + "=" * 60)
    print("TEST 2: Single Venue Collection")
    print("=" * 60)
    
    payload = {
        "place_id": 123,
        "name": "Test Restaurant",
        "latitude": 55.6761,
        "longitude": 12.5683
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/venue",
            json=payload,
            timeout=30
        )
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Metrics collected successfully:")
            print(f"   Place ID: {data['place_id']}")
            print(f"   Timestamp: {data['timestamp']}")
            print(f"   Actual Items: {data['actual_items']}")
            print(f"   Predicted Items: {data['predicted_items']:.0f}")
            print(f"   Ratio: {data['ratio']:.2f}x")
            print(f"   Excess Demand: {data['excess_demand']:.0f}")
            print(f"   Social Score: {data['social_signals'].get('composite_score', 0):.2f}")
            
            # This is what backend should store
            print(f"\n📝 Store this in database:")
            print(json.dumps(data, indent=2))
            return True
        else:
            print(f"❌ Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_batch_venues():
    """Test 3: Collect metrics for multiple venues (recommended)"""
    print("\n" + "=" * 60)
    print("TEST 3: Batch Venue Collection (RECOMMENDED)")
    print("=" * 60)
    
    payload = {
        "venues": [
            {
                "place_id": 123,
                "name": "Restaurant A",
                "latitude": 55.6761,
                "longitude": 12.5683
            },
            {
                "place_id": 124,
                "name": "Restaurant B",
                "latitude": 55.6867,
                "longitude": 12.5700
            },
            {
                "place_id": 125,
                "name": "Restaurant C",
                "latitude": 55.6950,
                "longitude": 12.5800
            }
        ]
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/batch",
            json=payload,
            timeout=60
        )
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"\n✅ Batch collection successful!")
            print(f"\n📊 Summary:")
            print(f"   Total venues: {data['summary']['total_venues']}")
            print(f"   Successful: {data['summary']['successful']}")
            print(f"   Failed: {data['summary']['failed']}")
            print(f"   Duration: {data['summary']['duration_seconds']:.2f}s")
            print(f"   Avg time per venue: {data['summary']['avg_time_per_venue']:.3f}s")
            
            print(f"\n📈 Collected metrics for {len(data['metrics'])} venues:")
            for metrics in data['metrics']:
                print(f"\n   - Place {metrics['place_id']}:")
                print(f"     Actual: {metrics['actual_items']} items | Predicted: {metrics['predicted_items']:.0f}")
                print(f"     Ratio: {metrics['ratio']:.2f}x | Excess: {metrics['excess_demand']:.0f}")
                
                # Detect surge
                ratio = metrics['ratio']
                if ratio > 2.0:
                    print(f"     🚨 CRITICAL SURGE!")
                elif ratio > 1.5:
                    print(f"     ⚠️  Strong surge")
                elif ratio > 1.3:
                    print(f"     ⚡ Possible surge")
            
            print(f"\n📝 Backend should store {len(data['metrics'])} records in database")
            return True
        else:
            print(f"❌ Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def simulate_backend_integration():
    """Example: How backend should integrate this"""
    print("\n" + "=" * 60)
    print("EXAMPLE: Backend Integration Pattern")
    print("=" * 60)
    
    print("""
    # Pseudo-code for backend integration:
    
    def scheduled_collection_job():
        '''Run this every 5 minutes'''
        
        # 1. Get active venues from database
        venues = db.query('''
            SELECT id as place_id, name, latitude, longitude
            FROM dim_places
            WHERE accepting_orders = true AND active = true
        ''')
        
        # 2. Call batch API
        response = requests.post(
            'http://localhost:8000/api/v1/collect/batch',
            json={'venues': venues},
            timeout=60
        )
        
        # 3. Store results
        if response.status_code == 200:
            data = response.json()
            for metrics in data['metrics']:
                db.execute('''
                    INSERT INTO surge_metrics (
                        place_id, timestamp, actual_items, predicted_items,
                        ratio, excess_demand, social_composite_score
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    metrics['place_id'],
                    metrics['timestamp'],
                    metrics['actual_items'],
                    metrics['predicted_items'],
                    metrics['ratio'],
                    metrics['excess_demand'],
                    metrics['social_signals']['composite_score']
                ))
            
            # 4. Check for surges and send alerts
            for metrics in data['metrics']:
                if metrics['ratio'] > 1.5:
                    send_surge_alert(metrics['place_id'], metrics['ratio'])
    """)


def main():
    """Run all tests"""
    print("\n🚀 Data Collection API Tests")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Before running tests, make sure API server is running:
    print("⚠️  Make sure API server is running:")
    print("   python -m uvicorn api.main:app --reload --port 8000\n")
    
    input("Press Enter to continue with tests...")
    
    # Run tests
    results = []
    results.append(("Health Check", test_health_check()))
    results.append(("Single Venue", test_single_venue()))
    results.append(("Batch Venues", test_batch_venues()))
    
    # Show example integration
    simulate_backend_integration()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    passed_count = sum(1 for _, passed in results if passed)
    print(f"\n{passed_count}/{len(results)} tests passed")
    
    if passed_count == len(results):
        print("\n🎉 All tests passed! API is ready for backend integration.")
    else:
        print("\n⚠️  Some tests failed. Check API server logs.")


if __name__ == "__main__":
    main()
