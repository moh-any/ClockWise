"""
Unit tests for Surge Detection Engine (Layer 2)
Tests all core functionality of the SurgeDetector class.
"""

import pytest
from datetime import datetime, timedelta
import sys
import os

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.surge_detector import SurgeDetector, SurgeMetrics, SurgeEvent, route_to_handler


class TestSurgeMetrics:
    """Test SurgeMetrics dataclass."""
    
    def test_surge_metrics_creation(self):
        """Test creating a SurgeMetrics instance."""
        metrics = SurgeMetrics(
            timestamp=datetime.now(),
            actual=200,
            predicted=100,
            ratio=2.0,
            social_signals={'google_trends': 75},
            excess_demand=100
        )
        
        assert metrics.actual == 200
        assert metrics.predicted == 100
        assert metrics.ratio == 2.0
        assert metrics.excess_demand == 100


class TestSurgeDetector:
    """Test SurgeDetector class."""
    
    @pytest.fixture
    def detector(self):
        """Create a detector instance for testing."""
        return SurgeDetector(
            surge_threshold=1.5,
            window_hours=3,
            min_excess_items=20,
            cooldown_hours=2
        )
    
    @pytest.fixture
    def surge_metrics(self):
        """Create sample surge metrics (all above threshold)."""
        return [
            SurgeMetrics(
                timestamp=datetime.now() - timedelta(hours=2),
                actual=160,
                predicted=100,
                ratio=1.6,
                social_signals={'google_trends': 60, 'twitter_virality': 0.5, 'composite_signal': 0.55},
                excess_demand=60
            ),
            SurgeMetrics(
                timestamp=datetime.now() - timedelta(hours=1),
                actual=180,
                predicted=100,
                ratio=1.8,
                social_signals={'google_trends': 70, 'twitter_virality': 0.6, 'composite_signal': 0.65},
                excess_demand=80
            ),
            SurgeMetrics(
                timestamp=datetime.now(),
                actual=200,
                predicted=100,
                ratio=2.0,
                social_signals={'google_trends': 80, 'twitter_virality': 0.7, 'composite_signal': 0.75},
                excess_demand=100
            )
        ]
    
    @pytest.fixture
    def non_surge_metrics(self):
        """Create sample non-surge metrics (some below threshold)."""
        return [
            SurgeMetrics(
                timestamp=datetime.now() - timedelta(hours=2),
                actual=160,
                predicted=100,
                ratio=1.6,
                social_signals={'google_trends': 30, 'composite_signal': 0.3},
                excess_demand=60
            ),
            SurgeMetrics(
                timestamp=datetime.now() - timedelta(hours=1),
                actual=110,
                predicted=100,
                ratio=1.1,  # Below threshold
                social_signals={'google_trends': 25, 'composite_signal': 0.25},
                excess_demand=10
            ),
            SurgeMetrics(
                timestamp=datetime.now(),
                actual=170,
                predicted=100,
                ratio=1.7,
                social_signals={'google_trends': 40, 'composite_signal': 0.4},
                excess_demand=70
            )
        ]
    
    def test_surge_detection_positive(self, detector, surge_metrics):
        """Verify surge detected when all ratios > threshold."""
        event = detector.check_surge(place_id=1, metrics=surge_metrics)
        
        assert event is not None
        assert isinstance(event, SurgeEvent)
        assert event.place_id == 1
        assert event.severity in ['moderate', 'high', 'critical']
        assert event.avg_ratio >= 1.5
        assert event.trend in ['accelerating', 'stable', 'decelerating']
        assert len(event.recommendations) > 0
    
    def test_surge_detection_negative(self, detector, non_surge_metrics):
        """Verify no surge when ratios intermittent."""
        event = detector.check_surge(place_id=1, metrics=non_surge_metrics)
        
        assert event is None
    
    def test_insufficient_data(self, detector):
        """Verify no surge when insufficient data."""
        metrics = [
            SurgeMetrics(
                timestamp=datetime.now(),
                actual=200,
                predicted=100,
                ratio=2.0,
                social_signals={},
                excess_demand=100
            )
        ]
        
        event = detector.check_surge(place_id=1, metrics=metrics)
        assert event is None
    
    def test_min_excess_threshold(self, detector):
        """Verify minimum excess demand requirement."""
        # High ratios but low absolute excess
        metrics = [
            SurgeMetrics(
                timestamp=datetime.now() - timedelta(hours=i),
                actual=15,
                predicted=10,
                ratio=1.5,
                social_signals={},
                excess_demand=5  # Too low
            )
            for i in range(3)
        ]
        
        event = detector.check_surge(place_id=1, metrics=metrics)
        assert event is None
    
    def test_cooldown_prevents_spam(self, detector, surge_metrics):
        """Verify cooldown period prevents repeated alerts."""
        # First detection
        event1 = detector.check_surge(place_id=1, metrics=surge_metrics)
        assert event1 is not None
        
        # Second detection immediately after (within cooldown)
        event2 = detector.check_surge(place_id=1, metrics=surge_metrics)
        assert event2 is None  # Blocked by cooldown
    
    def test_severity_levels(self, detector):
        """Test severity classification."""
        # Moderate surge (1.5-2.0x)
        moderate_metrics = [
            SurgeMetrics(
                timestamp=datetime.now() - timedelta(hours=i),
                actual=175,
                predicted=100,
                ratio=1.75,
                social_signals={'composite_signal': 0.5},
                excess_demand=75
            )
            for i in range(3)
        ]
        
        event = detector.check_surge(place_id=2, metrics=moderate_metrics)
        assert event.severity == 'moderate'
        
        # High surge (2.0-3.0x)
        high_metrics = [
            SurgeMetrics(
                timestamp=datetime.now() - timedelta(hours=i),
                actual=250,
                predicted=100,
                ratio=2.5,
                social_signals={'composite_signal': 0.6},
                excess_demand=150
            )
            for i in range(3)
        ]
        
        event = detector.check_surge(place_id=3, metrics=high_metrics)
        assert event.severity == 'high'
        
        # Critical surge (>3.0x)
        critical_metrics = [
            SurgeMetrics(
                timestamp=datetime.now() - timedelta(hours=i),
                actual=350,
                predicted=100,
                ratio=3.5,
                social_signals={'composite_signal': 0.8},
                excess_demand=250
            )
            for i in range(3)
        ]
        
        event = detector.check_surge(place_id=4, metrics=critical_metrics)
        assert event.severity == 'critical'
    
    def test_risk_score_calculation(self, detector, surge_metrics):
        """Verify risk score is computed correctly."""
        event = detector.check_surge(place_id=5, metrics=surge_metrics)
        
        assert event is not None
        assert 0.0 <= event.risk_score <= 1.0
    
    def test_trend_analysis(self, detector):
        """Test trend detection (accelerating, stable, decelerating)."""
        # Accelerating trend
        accelerating = [
            SurgeMetrics(
                timestamp=datetime.now() - timedelta(hours=2-i),
                actual=150 + i*50,
                predicted=100,
                ratio=1.5 + i*0.5,
                social_signals={'composite_signal': 0.5},
                excess_demand=50 + i*50
            )
            for i in range(3)
        ]
        
        event = detector.check_surge(place_id=6, metrics=accelerating)
        assert event.trend == 'accelerating'
        
        # Decelerating trend
        decelerating = [
            SurgeMetrics(
                timestamp=datetime.now() - timedelta(hours=2-i),
                actual=250 - i*30,
                predicted=100,
                ratio=2.5 - i*0.3,
                social_signals={'composite_signal': 0.5},
                excess_demand=150 - i*30
            )
            for i in range(3)
        ]
        
        event = detector.check_surge(place_id=7, metrics=decelerating)
        assert event.trend == 'decelerating'
    
    def test_root_cause_identification(self, detector):
        """Test root cause identification."""
        # Social media viral
        viral_metrics = [
            SurgeMetrics(
                timestamp=datetime.now() - timedelta(hours=i),
                actual=200,
                predicted=100,
                ratio=2.0,
                social_signals={'twitter_virality': 0.8, 'composite_signal': 0.7},
                excess_demand=100
            )
            for i in range(3)
        ]
        
        event = detector.check_surge(place_id=8, metrics=viral_metrics)
        assert event.root_cause == 'social_media_viral'
        
        # Nearby event
        event_metrics = [
            SurgeMetrics(
                timestamp=datetime.now() - timedelta(hours=i),
                actual=200,
                predicted=100,
                ratio=2.0,
                social_signals={'nearby_events': 2, 'composite_signal': 0.5},
                excess_demand=100
            )
            for i in range(3)
        ]
        
        event = detector.check_surge(place_id=9, metrics=event_metrics)
        assert event.root_cause == 'nearby_event'
    
    def test_recommendations_generated(self, detector, surge_metrics):
        """Verify recommendations are generated."""
        event = detector.check_surge(place_id=10, metrics=surge_metrics)
        
        assert event is not None
        assert len(event.recommendations) > 0
        assert any('staff' in rec.lower() for rec in event.recommendations)


class TestRouting:
    """Test handler routing logic."""
    
    def test_route_to_numeric_handler(self):
        """Test routing to numeric handler for low risk."""
        event = SurgeEvent(
            place_id=1,
            detected_at=datetime.now(),
            severity='moderate',
            risk_score=0.5,  # Below 0.7 threshold
            avg_ratio=1.8,
            trend='stable',
            root_cause='unknown',
            metrics_window=[],
            recommendations=[],
            estimated_duration='2-4 hours'
        )
        
        handler = route_to_handler(event)
        assert handler == 'numeric'
    
    def test_route_to_llm_handler(self):
        """Test routing to LLM handler for high risk."""
        event = SurgeEvent(
            place_id=1,
            detected_at=datetime.now(),
            severity='critical',
            risk_score=0.85,  # Above 0.7 threshold
            avg_ratio=3.5,
            trend='accelerating',
            root_cause='social_media_viral',
            metrics_window=[],
            recommendations=[],
            estimated_duration='3-6 hours'
        )
        
        handler = route_to_handler(event)
        assert handler == 'llm'
    
    def test_boundary_routing(self):
        """Test routing at exactly 0.7 threshold."""
        event = SurgeEvent(
            place_id=1,
            detected_at=datetime.now(),
            severity='high',
            risk_score=0.7,  # Exactly at threshold
            avg_ratio=2.5,
            trend='stable',
            root_cause='social_media_trending',
            metrics_window=[],
            recommendations=[],
            estimated_duration='2-4 hours'
        )
        
        handler = route_to_handler(event)
        assert handler == 'llm'  # >= 0.7 goes to LLM


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_metrics(self):
        """Test with empty metrics list."""
        detector = SurgeDetector()
        event = detector.check_surge(place_id=1, metrics=[])
        assert event is None
    
    def test_zero_predictions(self):
        """Test handling of zero predictions."""
        detector = SurgeDetector()
        metrics = [
            SurgeMetrics(
                timestamp=datetime.now() - timedelta(hours=i),
                actual=100,
                predicted=0,  # Zero prediction
                ratio=float('inf'),
                social_signals={},
                excess_demand=100
            )
            for i in range(3)
        ]
        
        # Should not crash
        event = detector.check_surge(place_id=1, metrics=metrics)
    
    def test_missing_social_signals(self):
        """Test with empty social signals."""
        detector = SurgeDetector()
        metrics = [
            SurgeMetrics(
                timestamp=datetime.now() - timedelta(hours=i),
                actual=200,
                predicted=100,
                ratio=2.0,
                social_signals={},  # Empty
                excess_demand=100
            )
            for i in range(3)
        ]
        
        event = detector.check_surge(place_id=1, metrics=metrics)
        assert event is not None
        assert event.root_cause == 'unknown'


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, '-v'])
