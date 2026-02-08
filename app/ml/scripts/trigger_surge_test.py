import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from unittest.mock import MagicMock, patch

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.surge_orchestrator import SurgeOrchestrator, OrchestratorConfig, OrchestrationResult
from src.surge_detector import SurgeEvent, SurgeMetrics

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_manual_test():
    """
    Manually trigger a surge detection cycle with mocked data to verify:
    1. Data collection (simulated)
    2. Surge detection logic
    3. Alert generation
    4. Email dispatch attempt
    """
    print("=" * 70)
    print("SURGE SYSTEM MANUAL VERIFICATION")
    print("=" * 70)

    # 1. Setup Orchestrator
    config = OrchestratorConfig(
        check_interval_seconds=60,
        demo_mode=True,
        surge_threshold=1.5,
        window_hours=3
    )
    orchestrator = SurgeOrchestrator(config)
    
    # 2. Mock Dependent Components (since we might not have backend running)
    
    # Mock Active Venues
    orchestrator._get_active_venues = MagicMock(return_value=[
        {
            'place_id': 'test-venue-uuid-123',
            'name': 'Test Pizza User Venue', 
            'latitude': 40.7128, 
            'longitude': -74.0060
        }
    ])
    
    # Mock Email Fetching
    orchestrator._get_venue_manager_emails = MagicMock(return_value=[
        'admin@test.com', 'manager@test.com'
    ])
    
    # Mock Data Collector to return SURGE data
    # We want actual > predicted * threshold
    async def mock_collect_metrics(venue):
        print(f"   [Mock] Collecting metrics for {venue['name']}...")
        now = datetime.now()
        metrics = []
        for i in range(3): # 3 hours
            ts = now - timedelta(hours=2-i)
            # Create surge condition: Actual = 300, Predicted = 100 -> Ratio 3.0
            metrics.append(SurgeMetrics(
                timestamp=ts,
                actual=300.0,
                predicted=100.0,
                ratio=3.0,
                social_signals={'composite_signal': 0.8},
                excess_demand=200.0
            ))
        return metrics

    orchestrator._collect_venue_metrics = mock_collect_metrics

    # Mock Email Sender to avoid actual spam during test
    with patch('src.surge_orchestrator.send_surge_email') as mock_send_email:
        print("\n🚀 Starting Detection Cycle...")
        
        # 3. Run Cycle
        result = await orchestrator.run_detection_cycle()
        
        print("\n📊 Cycle Results:")
        print(f"   Venues Checked: {result.venues_checked}")
        print(f"   Surges Detected: {result.surges_detected}")
        print(f"   Alerts Generated: {result.alerts_generated}")
        print(f"   Errors: {len(result.errors)}")
        if result.errors:
            for err in result.errors:
                print(f"     - {err}")

        # 4. Verify Email Verification
        print("\n📧 Email Dispatch Verification:")
        if mock_send_email.called:
            print("   ✅ send_surge_email was CALLED")
            args, kwargs = mock_send_email.call_args
            print(f"   - Recipients: {kwargs.get('to_emails')}")
            print(f"   - Venue: {kwargs.get('venue_name')}")
            print(f"   - Alert Severity: {kwargs.get('alert_data', {}).get('severity')}")
        else:
            print("   ❌ send_surge_email was NOT CALLED")

        # 5. Output Logic Verification
        if result.surges_detected > 0 and mock_send_email.called:
            print("\n✅ VERIFICATION SUCCESSFUL: Surge detected and email trigger attempted.")
        else:
            print("\n❌ VERIFICATION FAILED: Logic did not execute as expected.")

if __name__ == "__main__":
    asyncio.run(run_manual_test())
