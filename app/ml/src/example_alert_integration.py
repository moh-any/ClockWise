"""
Example: End-to-End Surge Detection to Alert Generation

This demonstrates the complete flow from surge detection to formatted alert message.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from datetime import datetime, timedelta
from surge_detector import SurgeDetector, SurgeMetrics
from alert_system import AlertDispatcher


def simulate_surge_detection_and_alert():
    """
    Simulate the complete surge detection → alert flow.
    This is what would run every 5 minutes in production.
    """
    print("="*70)
    print("SURGE DETECTION → ALERT SYSTEM DEMO (with automatic LLM)")
    print("="*70)
    
    # Step 1: Initialize components
    print("\n1. Initializing surge detector and alert dispatcher...")
    detector = SurgeDetector(
        surge_threshold=1.5,
        window_hours=3,
        min_excess_items=20,
        cooldown_hours=2
    )
    # AlertDispatcher now automatically uses LLM for high-risk surges!
    dispatcher = AlertDispatcher(llm_threshold=0.7, enable_llm=True)
    
    # Step 2: Simulate real-time metrics collection
    print("\n2. Collecting metrics for last 3 hours...")
    metrics = []
    base_time = datetime.now()
    
    # Simulate 3 hours of metrics (climbing to HIGH risk)
    for hour_offset in range(-3, 0):
        timestamp = base_time + timedelta(hours=hour_offset)
        
        # Simulating HIGH-RISK surge: 2.0x → 2.6x → 3.2x with strong social signals
        actual = 200 + (hour_offset + 3) * 60  # 200, 260, 320
        predicted = 100
        ratio = actual / predicted
        
        # Strong social signals to trigger LLM (composite > 0.7)
        social_strength = 0.6 + (hour_offset + 3) * 0.1  # 0.6, 0.7, 0.8
        
        metric = SurgeMetrics(
            timestamp=timestamp,
            actual=actual,
            predicted=predicted,
            ratio=ratio,
            social_signals={
                'google_trends': 75 + (hour_offset + 3) * 5,
                'twitter_mentions': 45 + (hour_offset + 3) * 30,
                'twitter_virality': 0.75 + (hour_offset + 3) * 0.05,
                'composite_signal': social_strength
            },
            excess_demand=actual - predicted
        )
        metrics.append(metric)
        print(f"   Hour {hour_offset}: {actual} items (predicted: {predicted}) = {ratio:.2f}x, social: {social_strength:.2f}")
    
    # Step 3: Run surge detection
    print("\n3. Running surge detection algorithm...")
    surge_event = detector.check_surge(place_id=123, metrics=metrics)
    
    if surge_event is None:
        print("   ❌ No surge detected")
        return
    
    print(f"   ✅ SURGE DETECTED!")
    print(f"      - Severity: {surge_event.severity}")
    print(f"      - Risk Score: {surge_event.risk_score:.2f} (LLM threshold: 0.7)")
    print(f"      - Average Ratio: {surge_event.avg_ratio:.2f}x")
    print(f"      - Trend: {surge_event.trend}")
    print(f"      - Root Cause: {surge_event.root_cause}")
    
    # Step 4: Simulate emergency schedule generation
    print("\n4. Generating emergency schedule...")
    emergency_schedule = {
        'added_staff': int(surge_event.avg_ratio) - 1,
        'additional_cost': (surge_event.avg_ratio - 1) * 500,
        'coverage_improvement': f'{surge_event.avg_ratio:.1f}x capacity'
    }
    print(f"   Staff needed: {emergency_schedule['added_staff']}")
    print(f"   Estimated cost: ${emergency_schedule['additional_cost']:.2f}")
    
    # Step 5: Simulate social media posts (for LLM context)
    print("\n5. Collecting social media context...")
    social_posts = [
        "OMG the line at Demo Restaurant is INSANE! Best burger ever though 🔥 #foodie",
        "Just discovered this place from TikTok - totally worth the wait! 😍",
        "@foodinfluencer thanks for the rec! This place is packed but amazing 💯"
    ]
    print(f"   Collected {len(social_posts)} social media posts")
    
    # Step 6: Generate alert (LLM analysis runs automatically!)
    print("\n6. Generating alert with automatic LLM analysis...")
    alert = dispatcher.generate_alert(
        surge_event=surge_event,
        venue_name="Demo Restaurant",
        emergency_schedule=emergency_schedule,
        social_posts=social_posts  # Passed to LLM for context
    )
    
    print(f"\n   Subject: {alert['subject']}")
    print(f"   Channels: {', '.join(alert['channels'])}")
    print(f"   Severity: {alert['severity']}")
    
    # Step 7: Display formatted message
    print("\n7. Final Alert Message for Backend:")
    print("-"*70)
    print(alert['message'])
    print("-"*70)
    
    # Step 8: Backend integration point
    print("\n8. Backend Integration Point:")
    print("   >>> Your backend code would receive this alert dictionary:")
    print(f"   >>> alert['subject'] = \"{alert['subject']}\"")
    print(f"   >>> alert['severity'] = \"{alert['severity']}\"")
    print(f"   >>> alert['channels'] = {alert['channels']}")
    print(f"   >>> alert['message'] = <Full formatted message with LLM insights>")
    print()
    print("   >>> Now your backend sends via appropriate channels:")
    
    for channel in alert['channels']:
        if channel == 'sms':
            print(f"   >>> send_sms(manager_phone, alert['message'][:500])")
        elif channel == 'email':
            print(f"   >>> send_email(manager_email, alert['subject'], alert['message'])")
        elif channel == 'slack':
            print(f"   >>> post_slack('#surge-alerts', alert['message'])")
        elif channel == 'call':
            print(f"   >>> make_call(manager_phone, 'Check surge alert now')")
    
    print("\n" + "="*70)
    print("✅ End-to-end flow complete with automatic LLM analysis!")
    print("="*70)
    
    return alert


def compare_severity_levels():
    """
    Generate alerts at different severity levels for comparison.
    """
    print("\n\n" + "="*70)
    print("SEVERITY LEVEL COMPARISON")
    print("="*70)
    
    dispatcher = AlertDispatcher()
    
    severity_scenarios = [
        {
            'name': 'Moderate (1.5x)',
            'ratio': 1.5,
            'severity': 'moderate',
            'risk': 0.45,
            'trend': 'stable',
            'cause': 'unknown'
        },
        {
            'name': 'High (2.5x)',
            'ratio': 2.5,
            'severity': 'high',
            'risk': 0.68,
            'trend': 'accelerating',
            'cause': 'nearby_event'
        },
        {
            'name': 'Critical (3.5x)',
            'ratio': 3.5,
            'severity': 'critical',
            'risk': 0.87,
            'trend': 'accelerating',
            'cause': 'social_media_viral'
        }
    ]
    
    for scenario in severity_scenarios:
        print(f"\n{scenario['name']}:")
        print("-" * 50)
        
        # Create minimal surge event
        from surge_detector import SurgeEvent, SurgeMetrics
        
        metrics = [SurgeMetrics(
            timestamp=datetime.now(),
            actual=100 * scenario['ratio'],
            predicted=100,
            ratio=scenario['ratio'],
            social_signals={'composite_signal': scenario['risk']},
            excess_demand=100 * (scenario['ratio'] - 1)
        )]
        
        event = SurgeEvent(
            place_id=999,
            detected_at=datetime.now(),
            severity=scenario['severity'],
            risk_score=scenario['risk'],
            avg_ratio=scenario['ratio'],
            trend=scenario['trend'],
            root_cause=scenario['cause'],
            metrics_window=metrics,
            recommendations=[f"Action for {scenario['severity']} surge"],
            estimated_duration="2-4 hours"
        )
        
        alert = dispatcher.format_surge_alert(event, venue_name="Test Venue")
        
        print(f"Channels: {', '.join(alert['channels'])}")
        print(f"Subject: {alert['subject']}")
        print(f"Message excerpt: {alert['message'][:200]}...")


if __name__ == "__main__":
    # Run the main demo
    alert = simulate_surge_detection_and_alert()
    
    # Show severity comparison
    compare_severity_levels()
    
    print("\n\n" + "="*70)
    print("🎯 KEY TAKEAWAYS FOR BACKEND TEAM")
    print("="*70)
    print("""
1. Import: from alert_system import AlertDispatcher
2. Initialize: dispatcher = AlertDispatcher(enable_llm=True)
3. Generate Alert: alert = dispatcher.generate_alert(surge_event, venue_name, schedule, social_posts)
   - LLM automatically analyzes high-risk surges (risk_score > 0.7)
   - Uses FREE Google Gemini (1,500 calls/day)
4. Access: alert['message'], alert['subject'], alert['channels']
5. Deliver: Use your existing SMS/email/Slack infrastructure
6. Done! The system handles detection, LLM analysis, and formatting automatically.

Alert Flow:
  Surge Detection → Check Risk Score → Auto LLM Analysis (if high-risk) → Format Alert → Send

LLM Integration:
  ✅ Automatic: No manual LLM calls needed
  ✅ Smart: Only analyzes high-risk surges to save quota
  ✅ Free: Google Gemini free tier (1,500/day)
  ✅ Graceful: Falls back to numeric analysis if LLM unavailable

Next Steps:
- Set GEMINI_API_KEY environment variable for FREE LLM analysis
- Review docs/ALERT_SYSTEM_INTEGRATION.md for detailed guide
- Run tests/test_alert_system.py to see all examples
- Integrate alert['channels'] routing into your backend
- Test with staging environment before production
    """)
    print("="*70)
