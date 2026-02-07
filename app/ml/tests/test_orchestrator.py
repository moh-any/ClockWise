"""
Unit tests for Surge Orchestrator
Tests the integration of all three layers.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
import sys
import os

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.surge_orchestrator import (
    SurgeOrchestrator, 
    OrchestratorConfig, 
    OrchestrationResult,
    TaskStatus,
    get_orchestrator
)


class TestOrchestratorConfig:
    """Test OrchestratorConfig dataclass."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = OrchestratorConfig()
        
        assert config.check_interval_seconds == 300
        assert config.surge_threshold == 1.5
        assert config.window_hours == 3
        assert config.min_excess_items == 20
        assert config.cooldown_hours == 2
        assert config.llm_threshold == 0.7
        assert config.enable_llm == True
        assert config.demo_mode == False
    
    def test_custom_config(self):
        """Test custom configuration."""
        config = OrchestratorConfig(
            check_interval_seconds=60,
            surge_threshold=2.0,
            demo_mode=True
        )
        
        assert config.check_interval_seconds == 60
        assert config.surge_threshold == 2.0
        assert config.demo_mode == True


class TestOrchestrationResult:
    """Test OrchestrationResult dataclass."""
    
    def test_result_creation(self):
        """Test creating an orchestration result."""
        result = OrchestrationResult(
            cycle_id=1,
            timestamp=datetime.now(),
            venues_checked=10,
            surges_detected=2,
            alerts_generated=2,
            errors=[],
            duration_seconds=5.5
        )
        
        assert result.cycle_id == 1
        assert result.venues_checked == 10
        assert result.surges_detected == 2
        assert result.alerts_generated == 2
        assert result.duration_seconds == 5.5
        assert len(result.errors) == 0


class TestSurgeOrchestrator:
    """Test SurgeOrchestrator class."""
    
    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return OrchestratorConfig(
            check_interval_seconds=1,  # Fast for testing
            surge_threshold=1.5,
            window_hours=3,
            demo_mode=True  # Use demo data
        )
    
    @pytest.fixture
    def orchestrator(self, config):
        """Create orchestrator instance for testing."""
        return SurgeOrchestrator(config)
    
    def test_orchestrator_initialization(self, orchestrator):
        """Test orchestrator initializes correctly."""
        assert orchestrator.status == TaskStatus.STOPPED
        assert orchestrator._cycle_count == 0
        assert orchestrator._last_result is None
        assert orchestrator.data_collector is not None
        assert orchestrator.surge_detector is not None
        assert orchestrator.alert_dispatcher is not None
    
    def test_orchestrator_config(self, orchestrator):
        """Test orchestrator uses provided config."""
        assert orchestrator.config.check_interval_seconds == 1
        assert orchestrator.config.surge_threshold == 1.5
        assert orchestrator.config.demo_mode == True
    
    @pytest.mark.asyncio
    async def test_start_stop(self, orchestrator):
        """Test starting and stopping orchestrator."""
        # Start
        await orchestrator.start()
        assert orchestrator.status == TaskStatus.RUNNING
        
        # Wait a moment
        await asyncio.sleep(0.1)
        
        # Stop
        await orchestrator.stop()
        assert orchestrator.status == TaskStatus.STOPPED
    
    @pytest.mark.asyncio
    async def test_pause_resume(self, orchestrator):
        """Test pausing and resuming orchestrator."""
        await orchestrator.start()
        assert orchestrator.status == TaskStatus.RUNNING
        
        orchestrator.pause()
        assert orchestrator.status == TaskStatus.PAUSED
        
        orchestrator.resume()
        assert orchestrator.status == TaskStatus.RUNNING
        
        await orchestrator.stop()
    
    @pytest.mark.asyncio
    async def test_detection_cycle(self, orchestrator):
        """Test running a single detection cycle."""
        # Create test venues
        test_venues = [
            {'place_id': 1, 'name': 'Test Restaurant 1', 'latitude': 55.6761, 'longitude': 12.5683},
            {'place_id': 2, 'name': 'Test Restaurant 2', 'latitude': 55.6800, 'longitude': 12.5700}
        ]
        
        # Run detection cycle
        result = await orchestrator.run_detection_cycle(test_venues)
        
        # Verify result
        assert isinstance(result, OrchestrationResult)
        assert result.cycle_id == 1
        assert result.venues_checked == 2
        assert result.duration_seconds > 0
    
    def test_get_status(self, orchestrator):
        """Test getting orchestrator status."""
        status = orchestrator.get_status()
        
        assert 'status' in status
        assert 'cycle_count' in status
        assert 'config' in status
        assert status['status'] == 'stopped'
        assert status['cycle_count'] == 0
    
    def test_get_history(self, orchestrator):
        """Test getting orchestration history."""
        history = orchestrator.get_history()
        
        assert isinstance(history, list)
        assert len(history) == 0  # Empty at start
    
    def test_alert_callback(self, orchestrator):
        """Test setting alert callback."""
        callback_called = []
        
        def test_callback(alert, venue):
            callback_called.append((alert, venue))
        
        orchestrator.set_alert_callback(test_callback)
        assert orchestrator._alert_callback is not None
    
    def test_get_fallback_venues(self, orchestrator):
        """Test fallback venues."""
        venues = orchestrator._get_fallback_venues()
        
        assert isinstance(venues, list)
        assert len(venues) > 0
        assert 'place_id' in venues[0]
        assert 'name' in venues[0]
        assert 'latitude' in venues[0]
        assert 'longitude' in venues[0]


class TestSingletonOrchestrator:
    """Test singleton orchestrator pattern."""
    
    def test_get_orchestrator_singleton(self):
        """Test that get_orchestrator returns singleton."""
        # Reset global first (for testing)
        import src.surge_orchestrator
        src.surge_orchestrator._orchestrator = None
        
        # Get orchestrator twice
        orch1 = get_orchestrator()
        orch2 = get_orchestrator()
        
        # Should be same instance
        assert orch1 is orch2
    
    def test_get_orchestrator_with_config(self):
        """Test creating orchestrator with custom config."""
        import src.surge_orchestrator
        src.surge_orchestrator._orchestrator = None
        
        config = OrchestratorConfig(
            check_interval_seconds=60,
            demo_mode=True
        )
        
        orch = get_orchestrator(config)
        assert orch.config.check_interval_seconds == 60
        assert orch.config.demo_mode == True


@pytest.mark.asyncio
async def test_full_cycle_with_callback():
    """Integration test: Full cycle with alert callback."""
    import src.surge_orchestrator
    src.surge_orchestrator._orchestrator = None
    
    # Track alerts
    alerts_received = []
    
    def alert_handler(alert, venue):
        alerts_received.append({
            'alert': alert,
            'venue': venue,
            'timestamp': datetime.now()
        })
    
    # Create orchestrator
    config = OrchestratorConfig(
        check_interval_seconds=1,
        demo_mode=True,
        surge_threshold=1.5
    )
    orch = SurgeOrchestrator(config)
    orch.set_alert_callback(alert_handler)
    
    # Run one cycle
    test_venues = [
        {'place_id': 1, 'name': 'Test Venue', 'latitude': 55.6761, 'longitude': 12.5683}
    ]
    
    result = await orch.run_detection_cycle(test_venues)
    
    # Verify cycle ran
    assert result.venues_checked == 1
    assert result.cycle_id == 1
    
    # Note: Alerts only generated if actual surge detected
    # With demo/simulated data, may or may not trigger


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])
