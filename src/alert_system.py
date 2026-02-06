"""
Alert System - Layer 3
Formats alert messages for surge events.
Includes automatic LLM analysis for high-risk surges.
"""

import os
from typing import Dict, Optional, List
from datetime import datetime


class AlertDispatcher:
    """
    Alert message formatter for surge notifications.
    Returns formatted messages.
    
    Automatically analyzes high-risk surges (risk_score > 0.7) with FREE Gemini LLM.
    """
    
    def __init__(self, llm_threshold: float = 0.7, enable_llm: bool = True):
        """
        Initialize alert dispatcher.
        
        Args:
            llm_threshold: Risk score threshold for triggering LLM analysis (default: 0.7)
            enable_llm: Whether to enable LLM analysis (default: True)
        """
        self.severity_emoji = {
            'moderate': '⚡',
            'high': '⚠️',
            'critical': '🚨'
        }
        self.llm_threshold = llm_threshold
        self.enable_llm = enable_llm
        self.llm_analyzer = None
        
        # Initialize LLM analyzer if enabled and API key available
        if enable_llm and os.getenv('GEMINI_API_KEY'):
            try:
                from llm_analyzer_gemini import GeminiSurgeAnalyzer
                self.llm_analyzer = GeminiSurgeAnalyzer()
                print("✅ LLM analyzer enabled (FREE Gemini)")
            except Exception as e:
                print(f"⚠️  LLM analyzer initialization failed: {e}")
                self.llm_analyzer = None
        elif enable_llm:
            print("ℹ️  LLM analyzer disabled: GEMINI_API_KEY not set")
            print("   Set GEMINI_API_KEY for FREE deep surge analysis")
    
    def generate_alert(self,
                      surge_event: 'SurgeEvent',
                      venue_name: str = None,
                      emergency_schedule: Optional[Dict] = None,
                      social_posts: Optional[List[str]] = None) -> Dict[str, str]:
        """
        Generate surge alert with automatic LLM analysis for high-risk surges.
        
        This is the recommended method - it automatically calls LLM analyzer
        when risk_score exceeds threshold.
        
        Args:
            surge_event: Detected surge event with full context
            venue_name: Optional name of venue (defaults to place_id)
            emergency_schedule: Optional generated schedule info
            social_posts: Optional list of recent social media posts for LLM context
        
        Returns:
            Dictionary with formatted alert (same format as format_surge_alert)
        """
        llm_insights = None
        
        # Automatically analyze with LLM if risk score is high
        if (self.llm_analyzer and 
            surge_event.risk_score > self.llm_threshold):
            
            print(f"🤖 Running LLM analysis (risk score: {surge_event.risk_score:.2f} > {self.llm_threshold})")
            
            try:
                llm_insights = self.llm_analyzer.analyze_surge_context(
                    venue_name=venue_name or f"Venue {surge_event.place_id}",
                    surge_metrics=surge_event,
                    social_posts=social_posts
                )
                print(f"   ✅ LLM analysis complete (model: {llm_insights.get('model_used', 'unknown')})")
            except Exception as e:
                print(f"   ⚠️  LLM analysis failed: {e}")
                llm_insights = None
        elif self.llm_analyzer:
            print(f"ℹ️  Skipping LLM analysis (risk score: {surge_event.risk_score:.2f} <= {self.llm_threshold})")
        
        # Format alert with LLM insights (if available)
        return self.format_surge_alert(
            surge_event=surge_event,
            venue_name=venue_name,
            emergency_schedule=emergency_schedule,
            llm_insights=llm_insights
        )
    
    def format_surge_alert(self, 
                          surge_event: 'SurgeEvent',
                          venue_name: str = None,
                          emergency_schedule: Optional[Dict] = None,
                          llm_insights: Optional[Dict] = None) -> Dict[str, str]:
        """
        Format surge alert message based on severity.
        
        Args:
            surge_event: Detected surge event with full context
            venue_name: Optional name of venue (defaults to place_id)
            emergency_schedule: Optional generated schedule info
            llm_insights: Optional LLM analysis results
        
        Returns:
            Dictionary with:
                - severity: 'moderate', 'high', or 'critical'
                - subject: Short alert subject line
                - message: Full formatted alert message
                - channels: Recommended channels ['email', 'sms', 'slack', 'call']
        """
        venue_display = venue_name or f"Venue {surge_event.place_id}"
        emoji = self.severity_emoji.get(surge_event.severity, '⚡')
        
        # Format subject line
        severity_label = surge_event.severity.upper()
        subject = f"{emoji} {severity_label} SURGE ALERT - {venue_display}"
        
        # Build main message
        message = self._build_message_body(
            surge_event, 
            venue_display, 
            emoji,
            llm_insights,
            emergency_schedule
        )
        
        # Determine delivery channels based on severity
        channels = self._get_recommended_channels(surge_event.severity)
        
        return {
            'severity': surge_event.severity,
            'subject': subject,
            'message': message,
            'channels': channels,
            'timestamp': surge_event.detected_at.isoformat()
        }
    
    def _build_message_body(self, 
                           surge: 'SurgeEvent', 
                           venue_display: str,
                           emoji: str,
                           llm_insights: Optional[Dict],
                           emergency_schedule: Optional[Dict]) -> str:
        """Build the main alert message body."""
        
        # Header
        message = f"{emoji} SURGE ALERT - {venue_display}\n"
        message += "=" * 60 + "\n\n"
        
        # Current Status Section
        message += "CURRENT STATUS:\n"
        message += f"• Demand Level: {surge.avg_ratio:.1f}x normal ({surge.trend})\n"
        message += f"• Detected At: {surge.detected_at.strftime('%Y-%m-%d %H:%M')}\n"
        message += f"• Root Cause: {self._format_root_cause(surge.root_cause)}\n"
        message += f"• Risk Score: {surge.risk_score:.2f}/1.0\n"
        message += f"• Severity: {surge.severity.upper()}\n"
        message += "\n"
        
        # LLM Analysis Section (if available)
        if llm_insights:
            message += "DETAILED ANALYSIS:\n"
            message += f"• {llm_insights.get('root_cause_detailed', 'N/A')}\n"
            message += f"• Viral Potential: {llm_insights.get('viral_potential', 0):.0%}\n"
            message += f"• Estimated Duration: {llm_insights.get('estimated_duration_hours', 'Unknown')} hours\n"
            message += f"• Urgency Level: {llm_insights.get('urgency_level', 0):.0%}\n"
            message += "\n"
        
        # Recommendations Section
        message += "RECOMMENDED ACTIONS:\n"
        for i, rec in enumerate(surge.recommendations, 1):
            message += f"{i}. {rec}\n"
        message += "\n"
        
        # Emergency Schedule Section (if available)
        if emergency_schedule:
            message += "EMERGENCY SCHEDULE:\n"
            message += f"• Additional Staff Needed: {emergency_schedule.get('added_staff', 'N/A')}\n"
            message += f"• Additional Cost: ${emergency_schedule.get('additional_cost', 0):.2f}\n"
            message += f"• Coverage Improvement: {emergency_schedule.get('coverage_improvement', 'N/A')}\n"
            message += "• Schedule attached for review and activation\n"
            message += "\n"
        
        # Timeline Section
        message += "EXPECTED TIMELINE:\n"
        message += f"• Estimated Duration: {surge.estimated_duration}\n"
        message += f"• Action Required: {self._get_action_timeline(surge.severity)}\n"
        message += "\n"
        
        # Footer with instructions
        message += "-" * 60 + "\n"
        if surge.severity in ['high', 'critical']:
            message += "⏰ IMMEDIATE ACTION REQUIRED\n"
            message += "Review and activate emergency schedule as soon as possible.\n"
        else:
            message += "📊 Monitor situation closely and prepare contingency plans.\n"
        
        return message
    
    def _format_root_cause(self, root_cause: str) -> str:
        """Format root cause string for display."""
        cause_mapping = {
            'social_media_viral': 'Social Media Viral Post',
            'social_media_trending': 'Social Media Trending',
            'nearby_event': 'Nearby Event',
            'unknown': 'Unknown/Multiple Factors'
        }
        return cause_mapping.get(root_cause, root_cause.replace('_', ' ').title())
    
    def _get_action_timeline(self, severity: str) -> str:
        """Get action timeline based on severity."""
        timelines = {
            'moderate': 'Within 30 minutes',
            'high': 'Within 15 minutes',
            'critical': 'IMMEDIATELY (within 5 minutes)'
        }
        return timelines.get(severity, 'As soon as possible')
    
    def _get_recommended_channels(self, severity: str) -> list:
        """
        Determine which communication channels should be used.
        Backend team will handle actual delivery.
        
        Currently: Email only (all severities)
        """
        # Email is the single channel for all alert severities
        return ['email']
    
    def format_multiple_alerts(self, surge_events: list) -> list:
        """
        Format multiple surge alerts at once.
        Useful for batch processing multiple venues.
        
        Args:
            surge_events: List of (surge_event, venue_name, schedule) tuples
        
        Returns:
            List of formatted alert dictionaries
        """
        alerts = []
        for item in surge_events:
            if isinstance(item, tuple):
                surge_event, venue_name, schedule = item + (None,) * (3 - len(item))
            else:
                surge_event, venue_name, schedule = item, None, None
            
            alert = self.format_surge_alert(
                surge_event=surge_event,
                venue_name=venue_name,
                emergency_schedule=schedule
            )
            alerts.append(alert)
        
        return alerts


def create_test_alert():
    """
    Create a test alert for demonstration purposes.
    This helps backend team see the expected message format.
    """
    from datetime import datetime
    from surge_detector import SurgeEvent, SurgeMetrics
    
    # Create sample surge event
    test_metrics = [
        SurgeMetrics(
            timestamp=datetime.now(),
            actual=200,
            predicted=100,
            ratio=2.0,
            social_signals={'composite_signal': 0.75},
            excess_demand=100
        )
    ]
    
    test_event = SurgeEvent(
        place_id=123,
        detected_at=datetime.now(),
        severity='high',
        risk_score=0.72,
        avg_ratio=2.0,
        trend='accelerating',
        root_cause='social_media_viral',
        metrics_window=test_metrics,
        recommendations=[
            "⚠️ HIGH PRIORITY: Activate emergency staffing protocol",
            "Contact on-call employees from emergency list",
            "Extend current shifts with overtime pay if employees agree",
            "📱 Social media surge detected - expect continued high demand for 2-6 hours",
            "💼 Estimated staff needed: 1x current levels"
        ],
        estimated_duration="3-6 hours (viral peak pattern)"
    )
    
    # Format alert
    dispatcher = AlertDispatcher()
    alert = dispatcher.format_surge_alert(
        surge_event=test_event,
        venue_name="Downtown Restaurant",
        emergency_schedule={
            'added_staff': 2,
            'additional_cost': 450.00,
            'coverage_improvement': '2.0x capacity'
        }
    )
    
    return alert


if __name__ == "__main__":
    # Demo: Create and print test alert
    print("=" * 70)
    print("ALERT SYSTEM - TEST OUTPUT")
    print("=" * 70)
    print()
    
    test_alert = create_test_alert()
    
    print(f"Subject: {test_alert['subject']}")
    print(f"Severity: {test_alert['severity']}")
    print(f"Channels: {', '.join(test_alert['channels'])}")
    print(f"Timestamp: {test_alert['timestamp']}")
    print()
    print("Message Body:")
    print("-" * 70)
    print(test_alert['message'])
    print()
    print("=" * 70)
    print("Backend team: Use alert['message'] for delivery")
    print("=" * 70)
