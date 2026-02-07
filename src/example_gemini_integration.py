"""
Complete Integration Example: Surge Detection → LLM Analysis → Alert

Demonstrates end-to-end flow with FREE Google Gemini LLM.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

import os
from datetime import datetime, timedelta
from surge_detector import SurgeDetector, SurgeMetrics
from llm_analyzer_gemini import GeminiSurgeAnalyzer
from alert_system import AlertDispatcher


def complete_surge_flow_with_llm():
    """
    Complete surge detection flow with FREE Gemini LLM analysis.
    """
    print("=" * 70)
    print("COMPLETE SURGE DETECTION WITH FREE GEMINI LLM")
    print("=" * 70)
    
    # Check API key
    if not os.getenv('GEMINI_API_KEY'):
        print("\n⚠️  GEMINI_API_KEY not set - running without LLM analysis")
        print("\n📝 To enable FREE LLM analysis:")
        print("   1. Get key: https://makersuite.google.com/app/apikey")
        print("   2. Set: $env:GEMINI_API_KEY='your_key_here'")
        print("\nContinuing with numeric analysis only...\n")
        use_llm = False
    else:
        use_llm = True
        print("✅ Gemini API key found - LLM analysis enabled (FREE)")
    
    # Initialize components
    print("\n1. Initializing components...")
    detector = SurgeDetector(surge_threshold=1.5, window_hours=3)
    dispatcher = AlertDispatcher()
    
    if use_llm:
        try:
            llm_analyzer = GeminiSurgeAnalyzer()
            print("   ✅ Surge detector ready")
            print("   ✅ Alert dispatcher ready")
            print("   ✅ Gemini LLM analyzer ready (FREE tier)")
        except Exception as e:
            print(f"   ⚠️  LLM initialization failed: {e}")
            use_llm = False
    
    # Simulate metrics collection
    print("\n2. Collecting surge metrics (simulated)...")
    metrics = []
    base_time = datetime.now()
    
    for hour_offset in range(-3, 0):
        timestamp = base_time + timedelta(hours=hour_offset)
        
        # Simulate HIGH surge: 1.8x → 2.4x → 3.0x
        actual = 180 + (hour_offset + 3) * 60
        predicted = 100
        ratio = actual / predicted
        
        metric = SurgeMetrics(
            timestamp=timestamp,
            actual=actual,
            predicted=predicted,
            ratio=ratio,
            social_signals={
                'google_trends': 88,
                'twitter_mentions': 156,
                'twitter_virality': 0.91,
                'instagram_engagement': 0.15,
                'nearby_events': 0,
                'composite_signal': 0.78
            },
            excess_demand=actual - predicted
        )
        metrics.append(metric)
        print(f"   Hour {hour_offset}: {actual} items (pred: {predicted}) = {ratio:.2f}x")
    
    # Run surge detection
    print("\n3. Running surge detection...")
    surge_event = detector.check_surge(place_id=789, metrics=metrics)
    
    if not surge_event:
        print("   ❌ No surge detected")
        return
    
    print(f"   ✅ SURGE DETECTED!")
    print(f"      Severity: {surge_event.severity.upper()}")
    print(f"      Risk Score: {surge_event.risk_score:.2f}")
    print(f"      Avg Ratio: {surge_event.avg_ratio:.2f}x")
    print(f"      Trend: {surge_event.trend}")
    
    # Decide: Use LLM or not?
    llm_insights = None
    
    if use_llm and surge_event.risk_score > 0.7:
        print("\n4. Running LLM analysis (FREE Gemini)...")
        print(f"   Risk score {surge_event.risk_score:.2f} > 0.7 threshold")
        print("   Calling Gemini API for deep analysis...")
        
        # Simulate social media posts
        social_posts = [
            "Just tried this place from TikTok viral video! Line is INSANE 🔥",
            "Best burger in the city! Thanks to @foodinfluencer for the rec 😍",
            "30 minute wait but totally worth it! Everyone is here today!",
            "The secret menu item is REAL and it's amazing! 🍔💯"
        ]
        
        try:
            llm_insights = llm_analyzer.analyze_surge_context(
                venue_name="Viral Burger Spot",
                surge_metrics=surge_event,
                social_posts=social_posts
            )
            
            print("   ✅ LLM analysis complete!")
            print(f"      Root Cause: {llm_insights['root_cause_detailed']}")
            print(f"      Viral Potential: {llm_insights['viral_potential']:.0%}")
            print(f"      Urgency: {llm_insights['urgency_level']:.0%}")
            print(f"      Duration: {llm_insights['estimated_duration_hours']}h")
            print(f"      Model: {llm_insights.get('model_used', 'N/A')}")
            
            # Show usage stats
            stats = llm_analyzer.get_usage_stats()
            print(f"\n   📊 Usage: {stats['total_calls']}/{stats['daily_limit']} calls today (FREE)")
            
        except Exception as e:
            print(f"   ⚠️  LLM analysis failed: {e}")
            print("   Continuing with numeric analysis...")
    
    elif surge_event.risk_score <= 0.7:
        print("\n4. Skipping LLM analysis")
        print(f"   Risk score {surge_event.risk_score:.2f} <= 0.7 threshold")
        print("   Using numeric signals only (cost-effective)")
    else:
        print("\n4. LLM analysis not available")
        print("   Set GEMINI_API_KEY for FREE deep analysis")
    
    # Simulate emergency schedule
    print("\n5. Generating emergency schedule...")
    emergency_schedule = {
        'added_staff': int(surge_event.avg_ratio) - 1,
        'additional_cost': (surge_event.avg_ratio - 1) * 550,
        'coverage_improvement': f'{surge_event.avg_ratio:.1f}x capacity'
    }
    print(f"   Additional staff: {emergency_schedule['added_staff']}")
    print(f"   Estimated cost: ${emergency_schedule['additional_cost']:.2f}")
    
    # Format alert
    print("\n6. Formatting alert message...")
    alert = dispatcher.format_surge_alert(
        surge_event=surge_event,
        venue_name="Viral Burger Spot",
        emergency_schedule=emergency_schedule,
        llm_insights=llm_insights  # Will be None if not used
    )
    
    print(f"   Subject: {alert['subject']}")
    print(f"   Channels: {', '.join(alert['channels'])}")
    
    # Display final alert
    print("\n7. Final Alert Message:")
    print("=" * 70)
    print(alert['message'])
    print("=" * 70)
    
    # Show comparison
    print("\n8. LLM Analysis Impact:")
    if llm_insights:
        print("   ✅ WITH LLM Analysis:")
        print("      • Detailed root cause explanation")
        print("      • Viral potential assessment")
        print("      • Precise duration estimate")
        print("      • Higher confidence recommendations")
        print("      • Cost: $0 (FREE Gemini)")
    else:
        print("   📊 WITHOUT LLM Analysis:")
        print("      • Basic root cause (numeric signals)")
        print("      • General recommendations")
        print("      • Estimated duration from patterns")
        print("      • Still effective, just less detailed")
        print("      • Cost: $0")
    
    print("\n" + "=" * 70)
    print("✅ Complete flow finished!")
    print("=" * 70)
    
    if use_llm:
        print("\n💡 TIP: LLM analysis is FREE (1,500 calls/day)")
        print("    Only used for high-risk surges (risk_score > 0.7)")
    else:
        print("\n💡 TIP: Enable FREE LLM analysis:")
        print("    Get key: https://makersuite.google.com/app/apikey")
        print("    Set: $env:GEMINI_API_KEY='your_key'")


def show_cost_comparison():
    """Show cost comparison: Gemini vs Claude vs GPT-4."""
    print("\n\n" + "=" * 70)
    print("COST COMPARISON: FREE GEMINI vs PAID OPTIONS")
    print("=" * 70)
    
    print("\nScenario: 50 venues, 2 surges/day, 15% use LLM (high-risk only)")
    print("Expected LLM calls: 50 × 2 × 0.15 = 15 calls/day = 450 calls/month")
    print()
    
    print("Option 1: Google Gemini (Current Implementation)")
    print("  • Cost per call: $0")
    print("  • Monthly cost: $0")
    print("  • Quality: Good")
    print("  • Speed: Fast (2-3 seconds)")
    print("  • Limit: 1,500 calls/day (plenty!)")
    print("  ✅ RECOMMENDED FOR MOST USERS")
    print()
    
    print("Option 2: Anthropic Claude")
    print("  • Cost per call: $0.03-0.05")
    print("  • Monthly cost: $13.50-22.50")
    print("  • Quality: Excellent")
    print("  • Speed: Medium (3-5 seconds)")
    print("  • Limit: Pay per use")
    print("  💡 Consider if quality is critical")
    print()
    
    print("Option 3: OpenAI GPT-4")
    print("  • Cost per call: $0.02-0.04")
    print("  • Monthly cost: $9-18")
    print("  • Quality: Excellent")
    print("  • Speed: Medium (3-4 seconds)")
    print("  • Limit: Pay per use")
    print("  💡 Good middle ground")
    print()
    
    print("💰 SAVINGS: Use Gemini to save $9-23/month")
    print("📊 For 450 calls/month, that's $108-270 saved annually!")
    print("=" * 70)


if __name__ == "__main__":
    # Run complete flow
    complete_surge_flow_with_llm()
    
    # Show cost comparison
    show_cost_comparison()
    
    print("\n\n🎯 INTEGRATION SUMMARY")
    print("=" * 70)
    print("""
✅ Surge Detection: Monitors 50+ venues every 5 minutes
✅ LLM Analysis: FREE Google Gemini for high-risk surges
✅ Alert System: Multi-channel notifications
✅ Emergency Schedule: Auto-generated staffing plan

Total Monthly Cost:
  • Surge Detection: $0 (Redis + social APIs free tier)
  • LLM Analysis: $0 (Gemini free tier: 1,500/day)
  • Alerts: $2-5 (SMS/Twilio minimal usage)
  
  TOTAL: $2-5/month (vs $30-50/month with paid LLM)

ROI: One prevented surge saves $1,500+ revenue
     System pays for itself instantly!
    """)
    print("=" * 70)
