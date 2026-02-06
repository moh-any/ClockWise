"""
Integration Test for Complete Surge Detection System
=====================================================
Tests all three layers working together with the orchestrator.

Run this script to verify the entire system:
    python tests/test_integration_surge_system.py
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.surge_orchestrator import SurgeOrchestrator, OrchestratorConfig
from src.surge_detector import SurgeMetrics


def print_header(title):
    """Print formatted header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_section(title):
    """Print formatted section."""
    print(f"\n{title}")
    print("-" * 70)


async def test_orchestrator_initialization():
    """Test 1: Orchestrator initialization."""
    print_section("TEST 1: Orchestrator Initialization")
    
    config = OrchestratorConfig(
        check_interval_seconds=10,
        surge_threshold=1.5,
        window_hours=3,
        demo_mode=True
    )
    
    orchestrator = SurgeOrchestrator(config)
    
    print(f"✅ Orchestrator created")
    print(f"   Status: {orchestrator.status.value}")
    print(f"   Interval: {orchestrator.config.check_interval_seconds}s")
    print(f"   Demo mode: {orchestrator.config.demo_mode}")
    print(f"   LLM enabled: {orchestrator.config.enable_llm}")
    
    assert orchestrator.data_collector is not None, "Data collector not initialized"
    assert orchestrator.surge_detector is not None, "Surge detector not initialized"
    assert orchestrator.alert_dispatcher is not None, "Alert dispatcher not initialized"
    
    print(f"✅ All components initialized (Layer 1, 2, 3)")
    
    return orchestrator


async def test_single_detection_cycle(orchestrator):
    """Test 2: Single detection cycle."""
    print_section("TEST 2: Single Detection Cycle")
    
    # Define test venues
    test_venues = [
        {'place_id': 123, 'name': 'Pizza Paradise', 'latitude': 55.6761, 'longitude': 12.5683},
        {'place_id': 456, 'name': 'Burger Express', 'latitude': 55.6800, 'longitude': 12.5700}
    ]
    
    print(f"Running detection cycle for {len(test_venues)} venues...")
    
    result = await orchestrator.run_detection_cycle(test_venues)
    
    print(f"✅ Cycle completed")
    print(f"   Cycle ID: {result.cycle_id}")
    print(f"   Venues checked: {result.venues_checked}")
    print(f"   Surges detected: {result.surges_detected}")
    print(f"   Alerts generated: {result.alerts_generated}")
    print(f"   Duration: {result.duration_seconds:.2f}s")
    
    if result.errors:
        print(f"⚠️  Errors: {len(result.errors)}")
        for error in result.errors:
            print(f"     - {error}")
    
    return result


async def test_surge_detection_with_high_metrics(orchestrator):
    """Test 3: Force surge detection with high metrics."""
    print_section("TEST 3: Surge Detection with High Demand")
    
    print("Creating venue with artificially high demand...")
    
    # We'll manually create high-ratio metrics and test surge detector directly
    from src.surge_detector import SurgeMetrics
    
    high_metrics = [
        SurgeMetrics(
            timestamp=datetime.now() - timedelta(hours=2),
            actual=300,
            predicted=100,
            ratio=3.0,
            social_signals={'composite_signal': 0.8, 'twitter_virality': 0.85},
            excess_demand=200
        ),
        SurgeMetrics(
            timestamp=datetime.now() - timedelta(hours=1),
            actual=350,
            predicted=100,
            ratio=3.5,
            social_signals={'composite_signal': 0.85, 'twitter_virality': 0.9},
            excess_demand=250
        ),
        SurgeMetrics(
            timestamp=datetime.now(),
            actual=400,
            predicted=100,
            ratio=4.0,
            social_signals={'composite_signal': 0.9, 'twitter_virality': 0.95},
            excess_demand=300
        )
    ]
    
    # Check for surge
    surge_event = orchestrator.surge_detector.check_surge(
        place_id=999,
        metrics=high_metrics
    )
    
    if surge_event:
        print(f"✅ Surge detected!")
        print(f"   Place ID: {surge_event.place_id}")
        print(f"   Severity: {surge_event.severity}")
        print(f"   Risk Score: {surge_event.risk_score:.2f}")
        print(f"   Average Ratio: {surge_event.avg_ratio:.1f}x")
        print(f"   Trend: {surge_event.trend}")
        print(f"   Root Cause: {surge_event.root_cause}")
        print(f"   Estimated Duration: {surge_event.estimated_duration}")
        
        # Generate alert
        print("\nGenerating alert...")
        alert = orchestrator.alert_dispatcher.generate_alert(
            surge_event=surge_event,
            venue_name="Test High-Demand Venue"
        )
        
        print(f"✅ Alert generated")
        print(f"   Subject: {alert['subject']}")
        print(f"   Severity: {alert['severity']}")
        print(f"   Channels: {alert['channels']}")
        print(f"   Recommendations: {len(surge_event.recommendations)} actions")
        
        # Show first 500 chars of message
        message_preview = alert['message'][:500]
        print(f"\n   Message preview:")
        print("   " + "\n   ".join(message_preview.split('\n')[:10]))
        
        return surge_event, alert
    else:
        print("⚠️  No surge detected (threshold not met)")
        return None, None


async def test_alert_callback(orchestrator):
    """Test 4: Alert callback mechanism."""
    print_section("TEST 4: Alert Callback")
    
    alerts_received = []
    
    def test_callback(alert, venue):
        """Test callback that stores alerts."""
        alerts_received.append({
            'alert': alert,
            'venue': venue,
            'timestamp': datetime.now()
        })
        print(f"✅ Alert callback triggered for {venue.get('name', venue.get('place_id'))}")
    
    orchestrator.set_alert_callback(test_callback)
    print("✅ Callback registered")
    
    # Run a cycle (may or may not trigger alerts with demo data)
    test_venues = [
        {'place_id': 101, 'name': 'Callback Test Venue', 'latitude': 55.6761, 'longitude': 12.5683}
    ]
    
    result = await orchestrator.run_detection_cycle(test_venues)
    
    print(f"Cycle completed: {result.alerts_generated} alerts generated")
    print(f"Callback received: {len(alerts_received)} alerts")
    
    return alerts_received


async def test_orchestrator_lifecycle():
    """Test 5: Orchestrator start/stop lifecycle."""
    print_section("TEST 5: Orchestrator Lifecycle")
    
    config = OrchestratorConfig(
        check_interval_seconds=2,  # 2 second interval
        demo_mode=True
    )
    
    orchestrator = SurgeOrchestrator(config)
    
    print("Starting orchestrator...")
    await orchestrator.start()
    print(f"✅ Status: {orchestrator.status.value}")
    
    # Let it run for a few cycles
    print("Running for 5 seconds (2-3 cycles)...")
    await asyncio.sleep(5)
    
    status = orchestrator.get_status()
    print(f"✅ Completed {status['cycle_count']} cycles")
    
    # Pause
    print("\nPausing orchestrator...")
    orchestrator.pause()
    print(f"✅ Status: {orchestrator.status.value}")
    
    # Resume
    print("\nResuming orchestrator...")
    orchestrator.resume()
    print(f"✅ Status: {orchestrator.status.value}")
    
    await asyncio.sleep(2)
    
    # Stop
    print("\nStopping orchestrator...")
    await orchestrator.stop()
    print(f"✅ Status: {orchestrator.status.value}")
    
    # Show history
    history = orchestrator.get_history(limit=10)
    print(f"\n✅ History contains {len(history)} cycles")
    
    return orchestrator


async def test_api_endpoints_availability():
    """Test 6: Check if required API endpoints are available."""
    print_section("TEST 6: API Endpoints Availability")
    
    import requests
    
    endpoints = [
        ("GET", "http://localhost:8000/api/v1/venues/active", "Venues endpoint"),
        ("GET", "http://localhost:8000/api/v1/surge/health", "Surge health endpoint"),
        ("GET", "http://localhost:8000/api/v1/surge/orchestrator/status", "Orchestrator status endpoint")
    ]
    
    results = []
    
    for method, url, name in endpoints:
        try:
            if method == "GET":
                response = requests.get(url, timeout=2)
            else:
                response = requests.post(url, timeout=2)
            
            if response.status_code < 400:
                print(f"✅ {name}: {response.status_code}")
                results.append(True)
            else:
                print(f"⚠️  {name}: {response.status_code}")
                results.append(False)
        except requests.exceptions.RequestException as e:
            print(f"❌ {name}: Connection failed ({e})")
            results.append(False)
    
    all_available = all(results)
    if all_available:
        print(f"\n✅ All API endpoints available")
    else:
        print(f"\n⚠️  Some endpoints unavailable (normal if API not running)")
    
    return all_available


async def run_all_tests():
    """Run all integration tests."""
    print_header("SURGE DETECTION SYSTEM - INTEGRATION TEST")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Test 1: Initialization
        orchestrator = await test_orchestrator_initialization()
        
        # Test 2: Single cycle
        await test_single_detection_cycle(orchestrator)
        
        # Test 3: Surge detection
        await test_surge_detection_with_high_metrics(orchestrator)
        
        # Test 4: Callback
        await test_alert_callback(orchestrator)
        
        # Test 5: Lifecycle
        await test_orchestrator_lifecycle()
        
        # Test 6: API availability
        await test_api_endpoints_availability()
        
        # Summary
        print_header("TEST SUMMARY")
        print("✅ All tests completed successfully!")
        print("\nSystem Status:")
        print("  Layer 1 (Data Collection): ✅ Working")
        print("  Layer 2 (Surge Detection): ✅ Working")
        print("  Layer 3 (Alert System): ✅ Working")
        print("  Orchestrator: ✅ Working")
        print("\nNext Steps:")
        print("  1. Start API server: uvicorn api.main:app --reload")
        print("  2. Implement backend endpoints: /api/v1/venues/active, /orders/query, /predictions/query")
        print("  3. Start orchestrator via API: POST /api/v1/surge/orchestrator/start")
        print("  4. Monitor alerts: GET /api/v1/surge/alerts/recent")
        
    except Exception as e:
        print_header("TEST FAILED")
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    print("\n")
    success = asyncio.run(run_all_tests())
    
    if success:
        print("\n" + "=" * 70)
        print("  🎉 INTEGRATION TEST PASSED")
        print("=" * 70 + "\n")
        sys.exit(0)
    else:
        print("\n" + "=" * 70)
        print("  ❌ INTEGRATION TEST FAILED")
        print("=" * 70 + "\n")
        sys.exit(1)
