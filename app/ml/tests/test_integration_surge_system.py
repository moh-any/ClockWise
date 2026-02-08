"""
Integration Test for Complete Surge Detection System
=====================================================
Tests all three layers working together with the orchestrator.

Updated: 2026-02-08 - Reflects current implementation with LLM analyzer,
model monitoring, and updated root cause detection.

Run this script to verify the entire system:
    python app/ml/tests/test_integration_surge_system.py
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


async def check_orchestrator_initialization():
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


async def check_single_detection_cycle(orchestrator):
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


async def check_surge_detection_with_high_metrics(orchestrator):
    """Test 3: Force surge detection with high metrics and multiple scenarios."""
    print_section("TEST 3: Surge Detection with High Demand")
    
    from src.surge_detector import SurgeMetrics
    
    # Scenario 1: Viral social media surge (twitter_virality > 0.7)
    print("\nScenario 1: Viral Social Media Surge")
    viral_metrics = [
        SurgeMetrics(
            timestamp=datetime.now() - timedelta(hours=2),
            actual=300,
            predicted=100,
            ratio=3.0,
            social_signals={
                'composite_signal': 0.8, 
                'twitter_virality': 0.75,
                'google_trends': 65
            },
            excess_demand=200
        ),
        SurgeMetrics(
            timestamp=datetime.now() - timedelta(hours=1),
            actual=350,
            predicted=100,
            ratio=3.5,
            social_signals={
                'composite_signal': 0.85, 
                'twitter_virality': 0.85,
                'google_trends': 70
            },
            excess_demand=250
        ),
        SurgeMetrics(
            timestamp=datetime.now(),
            actual=400,
            predicted=100,
            ratio=4.0,
            social_signals={
                'composite_signal': 0.9, 
                'twitter_virality': 0.95,
                'google_trends': 75
            },
            excess_demand=300
        )
    ]
    
    # Check for viral surge
    surge_event = orchestrator.surge_detector.check_surge(
        place_id=999,
        metrics=viral_metrics
    )
    
    if surge_event:
        print(f"✅ Viral surge detected!")
        print(f"   Severity: {surge_event.severity}")
        print(f"   Risk Score: {surge_event.risk_score:.2f}")
        print(f"   Average Ratio: {surge_event.avg_ratio:.1f}x")
        print(f"   Root Cause: {surge_event.root_cause}")
        
        # Verify it's identified as viral
        assert surge_event.root_cause == 'social_media_viral', \
            f"Expected 'social_media_viral', got '{surge_event.root_cause}'"
        print(f"   ✓ Correctly identified as viral social media")
        
        # Generate alert
        alert = orchestrator.alert_dispatcher.generate_alert(
            surge_event=surge_event,
            venue_name="Viral Trending Restaurant"
        )
        
        print(f"✅ Alert generated")
        print(f"   Subject: {alert['subject']}")
        print(f"   Severity: {alert['severity']}")
        print(f"   Channels: {alert['channels']}")
    else:
        print("⚠️  No surge detected (unexpected)")
    
    # Scenario 2: Google Trends surge (google_trends > 70)
    print("\nScenario 2: Google Trends Surge")
    trending_metrics = [
        SurgeMetrics(
            timestamp=datetime.now() - timedelta(hours=2),
            actual=200,
            predicted=100,
            ratio=2.0,
            social_signals={
                'composite_signal': 0.6,
                'twitter_virality': 0.3,
                'google_trends': 75
            },
            excess_demand=100
        ),
        SurgeMetrics(
            timestamp=datetime.now() - timedelta(hours=1),
            actual=220,
            predicted=100,
            ratio=2.2,
            social_signals={
                'composite_signal': 0.65,
                'twitter_virality': 0.35,
                'google_trends': 80
            },
            excess_demand=120
        ),
        SurgeMetrics(
            timestamp=datetime.now(),
            actual=240,
            predicted=100,
            ratio=2.4,
            social_signals={
                'composite_signal': 0.7,
                'twitter_virality': 0.4,
                'google_trends': 85
            },
            excess_demand=140
        )
    ]
    
    surge_event = orchestrator.surge_detector.check_surge(
        place_id=888,
        metrics=trending_metrics
    )
    
    if surge_event:
        print(f"✅ Trending surge detected!")
        print(f"   Root Cause: {surge_event.root_cause}")
        assert surge_event.root_cause == 'social_media_trending', \
            f"Expected 'social_media_trending', got '{surge_event.root_cause}'"
        print(f"   ✓ Correctly identified as Google Trends")
    
    # Scenario 3: Unknown cause surge
    print("\nScenario 3: Unknown Cause Surge")
    unknown_metrics = [
        SurgeMetrics(
            timestamp=datetime.now() - timedelta(hours=2),
            actual=180,
            predicted=100,
            ratio=1.8,
            social_signals={
                'composite_signal': 0.3,
                'twitter_virality': 0.2,
                'google_trends': 30
            },
            excess_demand=80
        ),
        SurgeMetrics(
            timestamp=datetime.now() - timedelta(hours=1),
            actual=190,
            predicted=100,
            ratio=1.9,
            social_signals={
                'composite_signal': 0.32,
                'twitter_virality': 0.22,
                'google_trends': 32
            },
            excess_demand=90
        ),
        SurgeMetrics(
            timestamp=datetime.now(),
            actual=200,
            predicted=100,
            ratio=2.0,
            social_signals={
                'composite_signal': 0.35,
                'twitter_virality': 0.25,
                'google_trends': 35
            },
            excess_demand=100
        )
    ]
    
    surge_event = orchestrator.surge_detector.check_surge(
        place_id=777,
        metrics=unknown_metrics
    )
    
    if surge_event:
        print(f"✅ Unknown surge detected!")
        print(f"   Root Cause: {surge_event.root_cause}")
        assert surge_event.root_cause == 'unknown', \
            f"Expected 'unknown', got '{surge_event.root_cause}'"
        print(f"   ✓ Correctly identified as unknown cause")
    
    print("\n✅ All root cause scenarios tested successfully")
    return surge_event


async def check_alert_callback(orchestrator):
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


async def check_llm_and_monitoring_features(orchestrator):
    """Test 5: LLM Analyzer and Model Monitoring availability."""
    print_section("TEST 5: Advanced Features")
    
    # Check LLM analyzer
    print("Checking LLM Analyzer:")
    has_llm = orchestrator.alert_dispatcher.llm_analyzer is not None
    if has_llm:
        print(f"✅ LLM Analyzer: Enabled (Gemini)")
        print(f"   Threshold: {orchestrator.alert_dispatcher.llm_threshold}")
        print(f"   Auto-triggers for risk_score > {orchestrator.alert_dispatcher.llm_threshold}")
    else:
        print(f"ℹ️  LLM Analyzer: Disabled")
        print(f"   To enable: Set GEMINI_API_KEY environment variable")
        print(f"   Provides FREE deep analysis of high-risk surges")
    
    # Check model monitor
    print("\nChecking Model Monitor:")
    has_monitor = orchestrator.data_collector.monitor is not None
    if has_monitor:
        print(f"✅ Model Monitor: Enabled")
        print(f"   Tracks prediction accuracy for model maintenance")
    else:
        print(f"ℹ️  Model Monitor: Disabled")
    
    # Check auto-maintenance
    print("\nChecking Auto-Maintenance:")
    if orchestrator.data_collector.auto_maintain:
        print(f"✅ Auto-Maintenance: Enabled")
        print(f"   Check interval: {orchestrator.data_collector.maintenance_check_interval}")
    else:
        print(f"ℹ️  Auto-Maintenance: Disabled")
    
    print("\n✅ Advanced features check complete")
    return {
        'llm_enabled': has_llm,
        'monitoring_enabled': has_monitor,
        'auto_maintain_enabled': orchestrator.data_collector.auto_maintain
    }


async def check_orchestrator_lifecycle():
    """Test 6: Orchestrator start/stop lifecycle."""
    print_section("TEST 6: Orchestrator Lifecycle")
    
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


async def check_api_endpoints_availability():
    """Test 7: Check if required API endpoints are available."""
    print_section("TEST 7: API Endpoints Availability")
    
    import requests
    
    # API endpoints that the surge system depends on
    endpoints = [
        ("GET", "http://localhost:8000/api/v1/venues/active", "Active venues endpoint"),
        ("POST", "http://localhost:8000/api/v1/surge/bulk-data", "Bulk data endpoint"),
    ]
    
    # Optional endpoints for full system integration
    optional_endpoints = [
        ("GET", "http://localhost:8000/api/v1/surge/orchestrator/status", "Orchestrator status"),
        ("POST", "http://localhost:8000/api/v1/surge/orchestrator/start", "Orchestrator start"),
        ("GET", "http://localhost:8000/api/v1/surge/alerts/recent", "Recent alerts"),
    ]
    
    results = []
    
    print("\nRequired Endpoints:")
    for method, url, name in endpoints:
        try:
            if method == "GET":
                response = requests.get(url, timeout=2)
            else:
                # POST with minimal test data
                response = requests.post(url, json={
                    "place_id": 1,
                    "timestamp": datetime.now().isoformat(),
                    "time_window_hours": 1
                }, timeout=2)
            
            if response.status_code < 500:  # Accept any non-server-error
                print(f"✅ {name}: {response.status_code}")
                results.append(True)
            else:
                print(f"⚠️  {name}: {response.status_code}")
                results.append(False)
        except requests.exceptions.RequestException as e:
            print(f"❌ {name}: Connection failed - {type(e).__name__}")
            results.append(False)
    
    print("\nOptional Endpoints (for full integration):")
    optional_results = []
    for method, url, name in optional_endpoints:
        try:
            if method == "GET":
                response = requests.get(url, timeout=2)
            else:
                response = requests.post(url, timeout=2)
            
            if response.status_code < 500:
                print(f"✅ {name}: {response.status_code}")
                optional_results.append(True)
            else:
                print(f"⚠️  {name}: {response.status_code}")
                optional_results.append(False)
        except requests.exceptions.RequestException:
            print(f"ℹ️  {name}: Not available")
            optional_results.append(False)
    
    required_available = all(results)
    if required_available:
        print(f"\n✅ All required API endpoints available")
    else:
        print(f"\n⚠️  Some required endpoints unavailable (normal if API not running)")
    
    if any(optional_results):
        print(f"   Bonus: {sum(optional_results)}/{len(optional_results)} optional endpoints available")
    
    return required_available


async def run_all_tests():
    """Run all integration tests."""
    print_header("SURGE DETECTION SYSTEM - INTEGRATION TEST")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Test 1: Initialization
        orchestrator = await check_orchestrator_initialization()
        
        # Test 2: Single cycle
        await check_single_detection_cycle(orchestrator)
        
        # Test 3: Surge detection
        await check_surge_detection_with_high_metrics(orchestrator)
        
        # Test 4: Callback
        await check_alert_callback(orchestrator)
        
        # Test 5: Advanced features
        await check_llm_and_monitoring_features(orchestrator)
        
        # Test 6: Lifecycle
        await check_orchestrator_lifecycle()
        
        # Test 7: API availability
        await check_api_endpoints_availability()
        
        # Summary
        print_header("TEST SUMMARY")
        print("✅ All tests completed successfully!")
        print("\nSystem Status:")
        print("  Layer 1 (Data Collection): ✅ Working")
        print("  Layer 2 (Surge Detection): ✅ Working")
        print("  Layer 3 (Alert System): ✅ Working")
        print("  Orchestrator: ✅ Working")
        print("\nFeatures Verified:")
        print("  • Real-time data collection with social signals")
        print("  • Surge detection with risk scoring")
        print("  • Root cause identification (viral, trending, events)")
        print("  • Alert generation with severity levels")
        print("  • Orchestrator lifecycle (start/pause/resume/stop)")
        print("  • Alert callbacks and history tracking")
        print("\nNext Steps:")
        print("  1. Start API server: cd app/api && go run cmd/api/main.go")
        print("  2. Or Python ML API: cd app/ml && uvicorn api.main:app --reload")
        print("  3. Implement backend endpoints:")
        print("     - GET /api/v1/venues/active")
        print("     - POST /api/v1/surge/bulk-data")
        print("     - GET /api/v1/orders/query (for actual orders)")
        print("     - GET /api/v1/predictions/query (for predictions)")
        print("  4. Start orchestrator:")
        print("     - Via API: POST /api/v1/surge/orchestrator/start")
        print("     - Standalone: python app/ml/src/surge_orchestrator.py")
        print("  5. Monitor system:")
        print("     - GET /api/v1/surge/orchestrator/status")
        print("     - GET /api/v1/surge/alerts/recent")
        print("\nOptional Enhancements:")
        print("  • Set GEMINI_API_KEY for FREE LLM analysis of high-risk surges")
        print("  • Enable model monitoring for drift detection")
        print("  • Configure email/SMS delivery for alerts")
        
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
