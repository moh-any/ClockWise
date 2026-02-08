"""
Tests for Alert System (Layer 3 - Minimal Version)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from datetime import datetime
from alert_system import AlertDispatcher, create_test_alert
from surge_detector import SurgeEvent, SurgeMetrics


def test_format_moderate_alert():
    """Test formatting of moderate severity alert."""
    print("\n" + "="*70)
    print("TEST 1: Moderate Severity Alert")
    print("="*70)
    
    # Create moderate surge
    metrics = [
        SurgeMetrics(
            timestamp=datetime.now(),
            actual=150,
            predicted=100,
            ratio=1.5,
            social_signals={'composite_signal': 0.45},
            excess_demand=50
        )
    ]
    
    event = SurgeEvent(
        place_id=101,
        detected_at=datetime.now(),
        severity='moderate',
        risk_score=0.48,
        avg_ratio=1.5,
        trend='stable',
        root_cause='unknown',
        metrics_window=metrics,
        recommendations=[
            "⚡ Monitor closely and prepare to extend shifts",
            "Alert on-call staff to standby for potential call-in",
            "💼 Estimated staff needed: 0x current levels"
        ],
        estimated_duration="2-3 hours"
    )
    
    dispatcher = AlertDispatcher()
    alert = dispatcher.format_surge_alert(event, venue_name="Suburban Cafe")
    
    print(f"\nSubject: {alert['subject']}")
    print(f"Severity: {alert['severity']}")
    print(f"Channels: {alert['channels']}")
    print(f"\nMessage:\n{alert['message']}")
    
    assert alert['severity'] == 'moderate'
    assert 'email' in alert['channels']
    assert 'sms' not in alert['channels']
    print("\n✅ Moderate alert test passed")


def test_format_high_alert():
    """Test formatting of high severity alert."""
    print("\n" + "="*70)
    print("TEST 2: High Severity Alert")
    print("="*70)
    
    metrics = [
        SurgeMetrics(
            timestamp=datetime.now(),
            actual=250,
            predicted=100,
            ratio=2.5,
            social_signals={'composite_signal': 0.68},
            excess_demand=150
        )
    ]
    
    event = SurgeEvent(
        place_id=102,
        detected_at=datetime.now(),
        severity='high',
        risk_score=0.71,
        avg_ratio=2.5,
        trend='accelerating',
        root_cause='nearby_event',
        metrics_window=metrics,
        recommendations=[
            "⚠️ HIGH PRIORITY: Activate emergency staffing protocol",
            "Contact on-call employees from emergency list",
            "🎉 Nearby event detected - surge should subside when event ends",
            "💼 Estimated staff needed: 1x current levels"
        ],
        estimated_duration="2-4 hours (event-dependent)"
    )
    
    dispatcher = AlertDispatcher()
    alert = dispatcher.format_surge_alert(
        event, 
        venue_name="Stadium District Restaurant",
        emergency_schedule={
            'added_staff': 3,
            'additional_cost': 675.00,
            'coverage_improvement': '2.5x capacity'
        }
    )
    
    print(f"\nSubject: {alert['subject']}")
    print(f"Severity: {alert['severity']}")
    print(f"Channels: {alert['channels']}")
    print(f"\nMessage:\n{alert['message']}")
    
    assert alert['severity'] == 'high'
    assert 'email' in alert['channels']
    print("\n✅ High alert test passed")


def test_format_critical_alert():
    """Test formatting of critical severity alert with LLM insights."""
    print("\n" + "="*70)
    print("TEST 3: Critical Severity Alert with LLM Analysis")
    print("="*70)
    
    metrics = [
        SurgeMetrics(
            timestamp=datetime.now(),
            actual=350,
            predicted=100,
            ratio=3.5,
            social_signals={'composite_signal': 0.89, 'twitter_virality': 0.92},
            excess_demand=250
        )
    ]
    
    event = SurgeEvent(
        place_id=103,
        detected_at=datetime.now(),
        severity='critical',
        risk_score=0.87,
        avg_ratio=3.5,
        trend='accelerating',
        root_cause='social_media_viral',
        metrics_window=metrics,
        recommendations=[
            "🚨 URGENT: Call in ALL available on-call staff immediately",
            "Consider pausing online orders if quality cannot be maintained",
            "Notify senior management and prepare for extended hours",
            "📱 Social media surge detected - expect continued high demand for 2-6 hours",
            "💼 Estimated staff needed: 2x current levels"
        ],
        estimated_duration="3-6 hours (viral peak pattern)"
    )
    
    llm_analysis = {
        'root_cause_detailed': 'TikTok influencer posted viral video featuring secret menu item',
        'viral_potential': 0.92,
        'urgency_level': 0.95,
        'estimated_duration_hours': 5,
        'confidence': 0.88
    }
    
    dispatcher = AlertDispatcher()
    alert = dispatcher.format_surge_alert(
        event,
        venue_name="Trendy Downtown Spot",
        emergency_schedule={
            'added_staff': 5,
            'additional_cost': 1250.00,
            'coverage_improvement': '3.5x capacity'
        },
        llm_insights=llm_analysis
    )
    
    print(f"\nSubject: {alert['subject']}")
    print(f"Severity: {alert['severity']}")
    print(f"Channels: {alert['channels']}")
    print(f"\nMessage:\n{alert['message']}")
    
    assert alert['severity'] == 'critical'
    assert 'email' in alert['channels']
    assert 'TikTok' in alert['message']
    print("\n✅ Critical alert test passed")


def test_multiple_alerts():
    """Test batch formatting of multiple alerts."""
    print("\n" + "="*70)
    print("TEST 4: Multiple Alerts Batch Processing")
    print("="*70)
    
    # Create 3 surge events
    events = []
    for i in range(3):
        metrics = [
            SurgeMetrics(
                timestamp=datetime.now(),
                actual=200,
                predicted=100,
                ratio=2.0,
                social_signals={'composite_signal': 0.6},
                excess_demand=100
            )
        ]
        
        event = SurgeEvent(
            place_id=200 + i,
            detected_at=datetime.now(),
            severity='high',
            risk_score=0.65,
            avg_ratio=2.0,
            trend='stable',
            root_cause='unknown',
            metrics_window=metrics,
            recommendations=["Contact on-call staff"],
            estimated_duration="2-4 hours"
        )
        events.append((event, f"Venue_{200+i}", None))
    
    dispatcher = AlertDispatcher()
    alerts = dispatcher.format_multiple_alerts(events)
    
    print(f"\nFormatted {len(alerts)} alerts:")
    for i, alert in enumerate(alerts, 1):
        print(f"\n{i}. {alert['subject']}")
        print(f"   Severity: {alert['severity']}, Channels: {alert['channels']}")
    
    assert len(alerts) == 3
    print("\n✅ Multiple alerts test passed")


def test_demo_output():
    """Run the built-in demo."""
    print("\n" + "="*70)
    print("TEST 5: Built-in Demo Function")
    print("="*70)
    
    alert = create_test_alert()
    
    print(f"\nDemo Alert Generated:")
    print(f"Subject: {alert['subject']}")
    print(f"Message Preview (first 300 chars):")
    print(alert['message'][:300] + "...")
    
    assert 'subject' in alert
    assert 'message' in alert
    assert 'channels' in alert
    print("\n✅ Demo test passed")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("ALERT SYSTEM TEST SUITE")
    print("="*70)
    
    try:
        test_format_moderate_alert()
        test_format_high_alert()
        test_format_critical_alert()
        test_multiple_alerts()
        test_demo_output()
        
        print("\n" + "="*70)
        print("✅ ALL TESTS PASSED")
        print("="*70)
        print("\nBackend Integration Notes:")
        print("• Use alert['message'] for message body")
        print("• Use alert['subject'] for email/SMS subject")
        print("• Use alert['channels'] to route to correct delivery systems")
        print("• alert['severity'] helps prioritize delivery")
        print("• alert['timestamp'] for logging and tracking")
        print("="*70)
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
