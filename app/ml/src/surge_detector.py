"""
Surge Detection Engine - Layer 2 (Core Layer)
Detects unexpected demand surges by analyzing real-time vs predicted demand.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
from collections import deque
from datetime import datetime, timedelta
import numpy as np


@dataclass
class SurgeMetrics:
    """Metrics for a single time period."""
    timestamp: datetime
    actual: float
    predicted: float
    ratio: float
    social_signals: Dict[str, float]
    excess_demand: float


@dataclass
class SurgeEvent:
    """Detected surge event with full context."""
    place_id: int
    detected_at: datetime
    severity: str  # 'moderate', 'high', 'critical'
    risk_score: float
    avg_ratio: float
    trend: str  # 'accelerating', 'stable', 'decelerating'
    root_cause: str  # 'social_media', 'event', 'unknown'
    metrics_window: List[SurgeMetrics]
    recommendations: List[str]
    estimated_duration: str


class SurgeDetector:
    """
    Detects surges by analyzing sliding window of metrics.
    Runs every 5 minutes to check for demand surges.
    """
    
    def __init__(self, 
                 surge_threshold: float = 1.5,
                 window_hours: int = 3,
                 min_excess_items: int = 20,
                 cooldown_hours: int = 2):
        """
        Initialize surge detector.
        
        Args:
            surge_threshold: Minimum ratio (actual/predicted) to consider surge
            window_hours: Hours of history to analyze
            min_excess_items: Minimum absolute excess demand per hour
            cooldown_hours: Hours to wait before alerting same venue again
        """
        self.surge_threshold = surge_threshold
        self.window_hours = window_hours
        self.min_excess_items = min_excess_items
        self.cooldown_hours = cooldown_hours
        
        # Track alert history
        self.alert_history: Dict[int, deque] = {}  # place_id -> timestamps
    
    def check_surge(self, place_id: int, metrics: List[SurgeMetrics]) -> Optional[SurgeEvent]:
        """
        Primary detection logic.
        
        Args:
            place_id: Venue ID
            metrics: List of SurgeMetrics for last N hours (from Redis)
        
        Returns:
            SurgeEvent if detected, None otherwise
        """
        # Filter to window size
        metrics = metrics[-self.window_hours:]
        
        if len(metrics) < self.window_hours:
            return None  # Not enough data
        
        # Check cooldown
        if self._in_cooldown(place_id):
            return None
        
        # Condition 1: All ratios above threshold
        ratios = [m.ratio for m in metrics]
        if min(ratios) < self.surge_threshold:
            return None
        
        # Condition 2: Minimum absolute excess
        total_excess = sum(m.excess_demand for m in metrics)
        if total_excess < self.min_excess_items * self.window_hours:
            return None
        
        # SURGE DETECTED!
        
        # Calculate risk score
        risk_score = self._calculate_risk_score(metrics)
        
        # Determine severity
        avg_ratio = np.mean(ratios)
        if avg_ratio >= 3.0:
            severity = 'critical'
        elif avg_ratio >= 2.0:
            severity = 'high'
        else:
            severity = 'moderate'
        
        # Analyze trend
        trend = self._analyze_trend(ratios)
        
        # Identify root cause
        root_cause = self._identify_root_cause(metrics)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(severity, avg_ratio, root_cause)
        
        # Estimate duration
        estimated_duration = self._estimate_duration(trend, root_cause)
        
        # Record alert
        self._record_alert(place_id)
        
        return SurgeEvent(
            place_id=place_id,
            detected_at=datetime.now(),
            severity=severity,
            risk_score=risk_score,
            avg_ratio=avg_ratio,
            trend=trend,
            root_cause=root_cause,
            metrics_window=metrics,
            recommendations=recommendations,
            estimated_duration=estimated_duration
        )
    
    def _calculate_risk_score(self, metrics: List[SurgeMetrics]) -> float:
        """
        Composite risk score (0-1).
        
        Components:
        - Ratio severity (40%): How far above threshold
        - Social signals (35%): Strength of social media buzz
        - Trend acceleration (25%): Rate of increase
        """
        ratios = [m.ratio for m in metrics]
        
        # Ratio severity: normalized above threshold
        ratio_severity = min(1.0, (np.mean(ratios) - 1.0) / 2.0)  # 3.0x = 1.0
        
        # Social signals: latest composite score
        latest_social = metrics[-1].social_signals.get('composite_signal', 0.0)
        
        # Trend acceleration: positive slope = higher risk
        if len(ratios) >= 2:
            slope = np.polyfit(range(len(ratios)), ratios, 1)[0]
            trend_acceleration = min(1.0, max(0.0, slope))
        else:
            trend_acceleration = 0.0
        
        risk_score = (
            ratio_severity * 0.40 +
            latest_social * 0.35 +
            trend_acceleration * 0.25
        )
        
        return risk_score
    
    def _analyze_trend(self, ratios: List[float]) -> str:
        """Determine if surge is accelerating, stable, or decelerating."""
        if len(ratios) < 2:
            return 'stable'
        
        slope = np.polyfit(range(len(ratios)), ratios, 1)[0]
        
        if slope > 0.1:
            return 'accelerating'
        elif slope < -0.1:
            return 'decelerating'
        else:
            return 'stable'
    
    def _identify_root_cause(self, metrics: List[SurgeMetrics]) -> str:
        """
        Identify most likely root cause.
        
        Priority:
        1. Social media (twitter_virality > 0.7 OR google_trends > 70)
        2. Nearby events (nearby_events > 0)
        3. Unknown (no clear signal)
        """
        latest = metrics[-1].social_signals
        
        if latest.get('twitter_virality', 0) > 0.7:
            return 'social_media_viral'
        elif latest.get('google_trends', 0) > 70:
            return 'social_media_trending'
        elif latest.get('nearby_events', 0) > 0:
            return 'nearby_event'
        else:
            return 'unknown'
    
    def _generate_recommendations(self, severity: str, avg_ratio: float, root_cause: str) -> List[str]:
        """Generate actionable recommendations based on surge characteristics."""
        recommendations = []
        
        # Severity-based actions
        if severity == 'critical':
            recommendations.append("🚨 URGENT: Call in ALL available on-call staff immediately")
            recommendations.append("Consider pausing online orders if quality cannot be maintained")
            recommendations.append("Notify senior management and prepare for extended hours")
        elif severity == 'high':
            recommendations.append("⚠️ HIGH PRIORITY: Activate emergency staffing protocol")
            recommendations.append("Contact on-call employees from emergency list")
            recommendations.append("Extend current shifts with overtime pay if employees agree")
        else:
            recommendations.append("⚡ Monitor closely and prepare to extend shifts")
            recommendations.append("Alert on-call staff to standby for potential call-in")
        
        # Root cause specific
        if 'social_media' in root_cause:
            recommendations.append("📱 Social media surge detected - expect continued high demand for 2-6 hours")
            recommendations.append("Monitor social media channels for updates and respond to posts")
        elif root_cause == 'nearby_event':
            recommendations.append("🎉 Nearby event detected - surge should subside when event ends")
            recommendations.append("Check event schedule for estimated end time")
        
        # Staffing math
        if avg_ratio != float('inf') and not np.isnan(avg_ratio):
            additional_staff_needed = int(avg_ratio) - 1
            recommendations.append(f"💼 Estimated staff needed: {additional_staff_needed}x current levels")
        else:
            recommendations.append("💼 Unable to estimate staffing needs - review demand data")
        
        return recommendations
    
    def _estimate_duration(self, trend: str, root_cause: str) -> str:
        """Estimate how long surge will last."""
        if trend == 'decelerating':
            return "1-2 hours (already declining)"
        elif root_cause == 'nearby_event':
            return "2-4 hours (event-dependent)"
        elif 'social_media' in root_cause:
            return "3-6 hours (viral peak pattern)"
        else:
            return "Unknown - monitor closely"
    
    def _in_cooldown(self, place_id: int) -> bool:
        """Check if venue is in cooldown period after recent alert."""
        if place_id not in self.alert_history:
            return False
        
        recent_alerts = self.alert_history[place_id]
        if not recent_alerts:
            return False
        
        last_alert = recent_alerts[-1]
        hours_since = (datetime.now() - last_alert).total_seconds() / 3600
        
        return hours_since < self.cooldown_hours
    
    def _record_alert(self, place_id: int):
        """Record alert timestamp for cooldown tracking."""
        if place_id not in self.alert_history:
            self.alert_history[place_id] = deque(maxlen=10)
        
        self.alert_history[place_id].append(datetime.now())


def route_to_handler(surge_event: SurgeEvent) -> str:
    """
    Route surge event to appropriate handler based on risk score.
    
    Args:
        surge_event: Detected surge event
    
    Returns:
        'numeric' for fast numeric handler (risk < 0.7)
        'llm' for LLM-enhanced handler (risk >= 0.7)
    """
    if surge_event.risk_score < 0.7:
        return 'numeric'
    else:
        return 'llm'


if __name__ == "__main__":
    # Example usage
    print("Surge Detection Engine - Layer 2")
    print("=" * 50)
    
    # Initialize detector
    detector = SurgeDetector(
        surge_threshold=1.5,
        window_hours=3,
        min_excess_items=20,
        cooldown_hours=2
    )
    
    # Create sample metrics (simulating a surge)
    sample_metrics = [
        SurgeMetrics(
            timestamp=datetime.now() - timedelta(hours=2),
            actual=180,
            predicted=100,
            ratio=1.8,
            social_signals={
                'google_trends': 65,
                'twitter_virality': 0.5,
                'composite_signal': 0.6
            },
            excess_demand=80
        ),
        SurgeMetrics(
            timestamp=datetime.now() - timedelta(hours=1),
            actual=220,
            predicted=100,
            ratio=2.2,
            social_signals={
                'google_trends': 75,
                'twitter_virality': 0.65,
                'composite_signal': 0.7
            },
            excess_demand=120
        ),
        SurgeMetrics(
            timestamp=datetime.now(),
            actual=280,
            predicted=100,
            ratio=2.8,
            social_signals={
                'google_trends': 85,
                'twitter_virality': 0.8,
                'composite_signal': 0.82
            },
            excess_demand=180
        )
    ]
    
    # Check for surge
    surge_event = detector.check_surge(place_id=1, metrics=sample_metrics)
    
    if surge_event:
        print(f"\n🚨 SURGE DETECTED!")
        print(f"Place ID: {surge_event.place_id}")
        print(f"Severity: {surge_event.severity.upper()}")
        print(f"Risk Score: {surge_event.risk_score:.2f}")
        print(f"Average Ratio: {surge_event.avg_ratio:.2f}x")
        print(f"Trend: {surge_event.trend}")
        print(f"Root Cause: {surge_event.root_cause}")
        print(f"Estimated Duration: {surge_event.estimated_duration}")
        print(f"\nRecommendations:")
        for i, rec in enumerate(surge_event.recommendations, 1):
            print(f"  {i}. {rec}")
        
        # Determine handler
        handler = route_to_handler(surge_event)
        print(f"\nRouted to: {handler.upper()} HANDLER")
    else:
        print("\nNo surge detected.")
