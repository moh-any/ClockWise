# Surge Detection & Social Media Handler Architecture

**Component:** Real-time Surge Detection with Social Media Integration  
**Purpose:** Detect and respond to unexpected demand spikes from viral events  
**Status:** Implementation Plan  
**Date:** February 6, 2026

---

## Table of Contents

1. [Problem Statement](#problem-statement)
2. [System Architecture](#system-architecture)
3. [Component Breakdown](#component-breakdown)
4. [Data Flow](#data-flow)
5. [Implementation Plan](#implementation-plan)
6. [API Integration Details](#api-integration-details)
7. [Decision Logic](#decision-logic)
8. [Alert & Response System](#alert--response-system)
9. [Cost-Benefit Analysis](#cost-benefit-analysis)
10. [Testing Strategy](#testing-strategy)

---

## Problem Statement

### Challenge
Social media can cause **unpredictable demand surges** that exceed normal predictions by 2-10x within hours:
- Viral reviews or "secret menu" items
- Local events trending on Twitter
- Reddit/Facebook group recommendations

### Current Gap
- Standard ML model predicts based on historical patterns
- Cannot anticipate viral events before they happen
- No mechanism to detect when predictions are wrong in real-time

### Solution Requirements
1. **Real-time detection** when actual demand exceeds predictions
2. **Multi-signal monitoring** from social media platforms
3. **Fast response** - generate emergency schedules within minutes
4. **Cost-effective** - minimize API costs while maintaining accuracy
5. **Actionable insights** - clear recommendations for managers

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     SURGE DETECTION SYSTEM                               │
└─────────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────────────┐
│  LAYER 1: DATA COLLECTION (Continuous Background Process)                 │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌─────────────────┐  ┌───────────────────┐  ┌──────────────────┐         │
│  │ Real-time Orders│  │ Demand Predictions│  │ Social Media APIs│         │
│  │ Stream (POS)    │  │ (From ML Model)   │  │ (Background)     │         │
│  │                 │  │                   │  │                  │         │
│  │ • Order count   │  │ • Predicted items │  │ • Google Trends  │         │
│  │ • Items ordered │  │ • Predicted orders│  │ • Twitter counts │         │
│  │ • Timestamp     │  │ • Confidence bands│  │ • Event calendar │         │
│  │ • Place ID      │  │                   │  │                  │         │
│  └────────┬────────┘  └─────────┬─────────┘  └─────────┬────────┘         │
│           │                     │                      │                  │
│           └─────────────────────┼──────────────────────┘                  │
│                                 ▼                                         │
│                    ┌──────────────────────────┐                           │
│                    │  Data Collection Storage  │                           │
│                    │   (5-minute resolution)   │                           │
│                    │                          │                           │
│                    │  Key: place_id:YYYYMMDDHH│                           │
│                    │  Value: {                │                           │
│                    │    actual: 150,          │                           │
│                    │    predicted: 100,       │                           │
│                    │    ratio: 1.5,           │                           │
│                    │    social_signals: {...} │                           │
│                    │  }                       │                           │
│                    │  TTL: 7 days             │                           │
│                    └──────────────────────────┘                           │
└───────────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  LAYER 2: SURGE DETECTION ENGINE (Every 5 minutes)                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌────────────────────────────────────────────────────────────┐         │
│  │  SurgeDetector Class (src/surge_detector.py)               │         │
│  │                                                            │         │
│  │  For each active venue:                                    │         │
│  │    1. Fetch last 3 hours of actual vs predicted            │         │
│  │    2. Calculate rolling ratio                              │         │
│  │    3. Check surge conditions:                              │         │
│  │       ├─ All ratios > 1.5x threshold                       │         │
│  │       ├─ Min absolute excess > 20 items                    │         │
│  │       └─ Not in cooldown period                            │         │
│  │    4. If surge detected → compute risk_score               │         │
│  │    5. Route to appropriate handler                         │         │
│  │                                                            │         │
│  │  risk_score = weighted_average(                            │         │
│  │    ratio_severity * 0.4,                                   │         │
│  │    social_signals * 0.35,                                  │         │
│  │    trend_acceleration * 0.25                               │         │
│  │  )                                                         │         │
│  └────────────────────────────────────────────────────────────┘         │
│                                 │                                       │
│                    ┌────────────┴────────────┐                          │
│                    │                         │                          │
│           risk_score < 0.7          risk_score >= 0.7                   │
│                    │                         │                          │
│                    ▼                         ▼                          │
│      ┌──────────────────────┐   ┌──────────────────────────┐            │
│      │  NUMERIC HANDLER     │   │  LLM-ENHANCED HANDLER    │            │
│      │  (Fast, Low Cost)    │   │  (Deep Analysis)         │            │
│      └──────────────────────┘   └──────────────────────────┘            │
└─────────────────────────────────────────────────────────────────────────┘
                    │                         │
                    └────────────┬────────────┘
                                 ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  LAYER 3: ALERT & RESPONSE SYSTEM                                        │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌─────────────────────────────────────────────────────────┐            │
│  │  Alert Dispatcher (src/alert_system.py)                 │            │
│  │                                                          │            │
│  │  Severity Levels:                                       │            │
│  │  ├─ MODERATE (1.5-2.0x): SMS to shift manager          │            │
│  │  ├─ HIGH (2.0-3.0x): SMS + Call + Dashboard alert      │            │
│  │  └─ CRITICAL (>3.0x): Multi-channel + Escalation       │            │
│  │                                                          │            │
│  │  Alert Contents:                                        │            │
│  │  • Surge magnitude and trend                            │            │
│  │  • Root cause analysis (social media, event, other)     │            │
│  │  • Recommended actions (specific, actionable)           │            │
│  │  • Auto-generated emergency schedule (attached)         │            │
│  │  • ETA for when surge may subside                       │            │
│  └─────────────────────────────────────────────────────────┘            │
│                                 │                                         │
│                                 ▼                                         │
│  ┌─────────────────────────────────────────────────────────┐            │
│  │  Emergency Schedule Generator                            │            │
│  │                                                          │            │
│  │  Input: surge_factor, available_on_call_staff           │            │
│  │  Process:                                                │            │
│  │    1. Multiply demand by surge_factor                   │            │
│  │    2. Add on-call employees to pool                     │            │
│  │    3. Reduce wage weight (prioritize coverage)          │            │
│  │    4. Solve with 30-second time limit                   │            │
│  │  Output: Emergency schedule + cost estimate             │            │
│  └─────────────────────────────────────────────────────────┘            │
│                                 │                                         │
│                                 ▼                                         │
│              ┌──────────────────────────────────┐                        │
│              │   Manager Dashboard / Mobile App │                        │
│              │   • Accept/Modify schedule       │                        │
│              │   • Notify employees (SMS/Push)  │                        │
│              │   • Track response (who accepted)│                        │
│              └──────────────────────────────────┘                        │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Component Breakdown

### 1. Real-time Data Collector

**File:** `src/data_collector.py` (new)

```python
class RealTimeDataCollector:
    """
    Collects and aggregates real-time data from multiple sources.
    Runs as background service (Celery task or separate process).
    """
    
    def __init__(self, update_interval_seconds=300):
        self.interval = update_interval_seconds
        self.social_media_cache_ttl = 900  # 15 minutes
    
    def collect_actual_orders(self, place_id: int, time_window: timedelta) -> dict:
        """
        Query POS system or orders database for actual orders in time window.
        Returns: {timestamp: {item_count: int, order_count: int}}
        """
        pass
    
    def collect_predictions(self, place_id: int, time_window: timedelta) -> dict:
        """
        Fetch predictions from cache or recompute if needed.
        Returns: {timestamp: {item_count_pred: float, order_count_pred: float}}
        """
        pass
    
    def collect_social_signals(self, place_id: int) -> dict:
        """
        Fetch social media signals (cached, only refresh every 15 min).
        Returns: {
            google_trends: float,
            twitter_mentions: int,
            twitter_virality: float,
            nearby_events: int,
            composite_signal: float  # 0-1 score
        }
        """
        pass
    
    def aggregate_and_store(self, place_id: int):
        """
        Combine all data sources and store in database.
        Called every 5 minutes per active venue.
        """
        # Get current hour slot
        current_time = datetime.now()
        hour_key = current_time.strftime("%Y%m%d%H")
        
        # Fetch data
        actuals = self.collect_actual_orders(place_id, timedelta(hours=1))
        predictions = self.collect_predictions(place_id, timedelta(hours=1))
        social = self.collect_social_signals(place_id)
        
        # Aggregate
        actual_items = sum(a['item_count'] for a in actuals.values())
        predicted_items = sum(p['item_count_pred'] for p in predictions.values())
        
        ratio = actual_items / predicted_items if predicted_items > 0 else 0
        
        # Store in database
        key = f"surge:metrics:{place_id}:{hour_key}"
        data = {
            'timestamp': current_time.isoformat(),
            'actual_items': actual_items,
            'predicted_items': predicted_items,
            'ratio': ratio,
            'social_signals': social,
            'excess_demand': actual_items - predicted_items
        }
```

**Deployment:** 
- Celery beat task every 5 minutes
- One task per active venue (parallel execution)
- Estimated runtime: 2-3 seconds per venue

---

### 2. Surge Detector Core

**File:** `src/surge_detector.py` (implement)

```python
from dataclasses import dataclass
from typing import List, Dict, Optional
from collections import deque
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
    """
    
    def __init__(self, 
                 surge_threshold: float = 1.5,
                 window_hours: int = 3,
                 min_excess_items: int = 20,
                 cooldown_hours: int = 2):
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
            metrics: List of SurgeMetrics for last N hours
        
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
        additional_staff_needed = int(avg_ratio) - 1
        recommendations.append(f"💼 Estimated staff needed: {additional_staff_needed}x current levels")
        
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
```

---

### 3. Social Media Integrations

**File:** `src/social_media_apis.py` (new)

```python
import requests
import time
from typing import Dict, Optional
from datetime import datetime, timedelta

class SocialMediaAggregator:
    """
    Aggregates signals from multiple social media APIs.
    All methods return numeric scores (no text analysis needed for basic version).
    """
    
    def __init__(self):
        # API credentials from environment
        self.twitter_bearer = os.getenv('TWITTER_BEARER_TOKEN')
        self.eventbrite_key = os.getenv('EVENTBRITE_API_KEY')
        
        # In-memory cache to reduce API calls
        self.cache = {}
        self.cache_ttl = 900  # 15 minutes
    
    def get_composite_signal(self, place_id: int, venue_name: str, 
                            latitude: float, longitude: float) -> Dict[str, float]:
        """
        Get all social signals and compute composite score.
        
        Returns:
            {
                'google_trends': 0.75,      # 0-100 normalized to 0-1
                'twitter_mentions': 45,      # Raw count
                'twitter_virality': 0.82,    # 0-1 engagement rate
                'nearby_events': 2,          # Count of events
                'event_attendance': 1500,    # Total expected
                'composite_signal': 0.68     # Weighted average
            }
        """
        cache_key = f"social:{place_id}:{datetime.now().strftime('%Y%m%d%H%M')[:-1]}0"  # Round to 10min
        
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        signals = {}
        
        # Google Trends (free, no rate limit)
        signals['google_trends'] = self._get_google_trends(venue_name)
        
        # Twitter (free tier: 500k/month)
        twitter_data = self._get_twitter_metrics(venue_name)
        signals['twitter_mentions'] = twitter_data['mentions']
        signals['twitter_virality'] = twitter_data['virality']
        
        # Nearby events
        event_data = self._get_nearby_events(latitude, longitude)
        signals['nearby_events'] = event_data['count']
        signals['event_attendance'] = event_data['total_attendance']
        
        # Composite score (prioritize high-signal sources)
        composite = (
            signals['twitter_virality'] * 0.40 +
            (signals['google_trends'] / 100) * 0.30 +
            min(1.0, signals['event_attendance'] / 5000) * 0.30
        )
        signals['composite_signal'] = composite
        
        # Cache result
        self.cache[cache_key] = signals
        
        return signals
    
    def _get_google_trends(self, keyword: str) -> float:
        """Get Google Trends score (0-100) for keyword."""
        try:
            from pytrends.request import TrendReq
            pytrends = TrendReq(hl='en-US', tz=360)
            pytrends.build_payload([keyword], timeframe='now 1-d', geo='DK')
            interest = pytrends.interest_over_time()
            
            if not interest.empty:
                return float(interest[keyword].iloc[-1])
            return 0.0
        except Exception as e:
            print(f"Google Trends error: {e}")
            return 0.0
    
    def _get_twitter_metrics(self, venue_name: str) -> Dict[str, float]:
        """Get Twitter mention count and engagement metrics."""
        if not self.twitter_bearer:
            return {'mentions': 0, 'virality': 0.0}
        
        try:
            url = "https://api.twitter.com/2/tweets/search/recent"
            headers = {'Authorization': f'Bearer {self.twitter_bearer}'}
            
            query = f'"{venue_name}" -is:retweet'
            start_time = (datetime.utcnow() - timedelta(hours=6)).isoformat() + 'Z'
            
            params = {
                'query': query,
                'start_time': start_time,
                'tweet.fields': 'public_metrics',
                'max_results': 100
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            tweets = response.json().get('data', [])
            
            mention_count = len(tweets)
            if mention_count == 0:
                return {'mentions': 0, 'virality': 0.0}
            
            # Calculate engagement metrics
            total_engagement = sum(
                t.get('public_metrics', {}).get('retweet_count', 0) +
                t.get('public_metrics', {}).get('like_count', 0) +
                t.get('public_metrics', {}).get('reply_count', 0)
                for t in tweets
            )
            
            # Virality score: engagement per mention (normalized)
            virality = min(1.0, total_engagement / (mention_count * 50))
            
            return {
                'mentions': mention_count,
                'virality': virality
            }
            
        except Exception as e:
            print(f"Twitter API error: {e}")
            return {'mentions': 0, 'virality': 0.0}
    
    def _get_nearby_events(self, latitude: float, longitude: float) -> Dict[str, int]:
        """Get nearby events from Eventbrite."""
        if not self.eventbrite_key:
            return {'count': 0, 'total_attendance': 0}
        
        try:
            url = "https://www.eventbriteapi.com/v3/events/search/"
            
            today = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
            
            params = {
                'location.latitude': latitude,
                'location.longitude': longitude,
                'location.within': '5km',
                'start_date.range_start': today,
                'start_date.range_end': today,
                'token': self.eventbrite_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            events = response.json().get('events', [])
            
            total_attendance = sum(e.get('capacity', 200) for e in events)  # Default 200 if not specified
            
            return {
                'count': len(events),
                'total_attendance': total_attendance
            }
            
        except Exception as e:
            print(f"Eventbrite API error: {e}")
            return {'count': 0, 'total_attendance': 0}
```

---

### 4. LLM-Enhanced Analysis (Optional Layer)

**File:** `src/llm_analyzer.py` (new)

```python
from anthropic import Anthropic
from typing import List, Dict, Optional

class LLMSurgeAnalyzer:
    """
    Deep analysis using LLM for high-risk surges only.
    This is EXPENSIVE - only call when risk_score > 0.7.
    """
    
    def __init__(self, api_key: str):
        self.client = Anthropic(api_key=api_key)
        self.model = "claude-sonnet-4-5-20250514"
    
    def analyze_surge_context(self, 
                              venue_name: str,
                              surge_metrics: 'SurgeEvent',
                              social_posts: Optional[List[str]] = None) -> Dict[str, any]:
        """
        Deep analysis of surge using LLM.
        
        Only called when:
        - risk_score > 0.7
        - Budget allows (~$0.02-0.05 per call)
        
        Returns:
            {
                'root_cause_detailed': str,
                'viral_potential': float (0-1),
                'urgency_level': float (0-1),
                'recommended_response': str,
                'estimated_duration_hours': int,
                'confidence': float (0-1)
            }
        """
        if not social_posts:
            social_posts = []
        
        # Build context for LLM
        context = f"""Venue: {venue_name}
Current surge detected:
- Average ratio: {surge_metrics.avg_ratio:.2f}x normal
- Severity: {surge_metrics.severity}
- Trend: {surge_metrics.trend}
- Social signals: {surge_metrics.metrics_window[-1].social_signals}

Recent social media posts (top 10 by engagement):
"""
        for i, post in enumerate(social_posts[:10], 1):
            context += f"\n{i}. {post}"
        
        prompt = f"""{context}

Analyze this demand surge and provide:

1. **Root Cause** (detailed): What is driving this surge? (influencer post, viral trend, event, news, etc.)
2. **Viral Potential** (0-1): Likelihood this will continue spreading virally
3. **Urgency Level** (0-1): How soon manager must act (0=can wait, 1=immediate action needed)
4. **Recommended Response**: Specific, actionable steps for the manager
5. **Estimated Duration**: How many hours will this surge last?
6. **Confidence** (0-1): How confident are you in this analysis?

Respond ONLY in this exact JSON format (no markdown, no extra text):
{{
    "root_cause_detailed": "Brief explanation in 1-2 sentences",
    "viral_potential": 0.0,
    "urgency_level": 0.0,
    "recommended_response": "Concise action steps",
    "estimated_duration_hours": 0,
    "confidence": 0.0
}}"""
        
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )
            
            import json
            result = json.loads(message.content[0].text)
            
            return result
            
        except Exception as e:
            print(f"LLM analysis error: {e}")
            return {
                'root_cause_detailed': 'Analysis unavailable',
                'viral_potential': 0.0,
                'urgency_level': surge_metrics.risk_score,
                'recommended_response': 'Follow standard surge protocol',
                'estimated_duration_hours': 3,
                'confidence': 0.0
            }
```

---

### 5. Alert System

**File:** `src/alert_system.py` (new)

```python
import requests
from typing import List
from twilio.rest import Client  # For SMS

class AlertDispatcher:
    """
    Multi-channel alert system for surge notifications.
    """
    
    def __init__(self):
        # Twilio for SMS
        self.twilio_client = Client(
            os.getenv('TWILIO_ACCOUNT_SID'),
            os.getenv('TWILIO_AUTH_TOKEN')
        )
        self.twilio_from = os.getenv('TWILIO_PHONE_NUMBER')
        
        # Slack for team alerts
        self.slack_webhook = os.getenv('SLACK_WEBHOOK_URL')
        
        # Email
        self.sendgrid_key = os.getenv('SENDGRID_API_KEY')
    
    def dispatch_surge_alert(self, 
                            surge_event: 'SurgeEvent',
                            manager_contact: Dict[str, str],
                            emergency_schedule: Optional[dict] = None,
                            llm_insights: Optional[dict] = None):
        """
        Send alerts through appropriate channels based on severity.
        
        Args:
            surge_event: Detected surge event
            manager_contact: {'phone': '+45...', 'email': '...', 'name': '...'}
            emergency_schedule: Generated schedule (if available)
            llm_insights: LLM analysis (if performed)
        """
        # Format message
        message = self._format_alert_message(surge_event, llm_insights)
        
        if surge_event.severity == 'critical':
            # CRITICAL: All channels + escalation
            self._send_sms(manager_contact['phone'], message, urgent=True)
            self._send_email(manager_contact['email'], 
                           subject=f"🚨 CRITICAL SURGE ALERT - {surge_event.place_id}",
                           body=message,
                           attachment=emergency_schedule)
            self._send_slack_alert(message, channel='#critical-alerts')
            
            # Call manager (using Twilio voice call)
            self._make_voice_call(manager_contact['phone'], 
                                 "Critical demand surge detected. Check your messages immediately.")
        
        elif surge_event.severity == 'high':
            # HIGH: SMS + Email + Dashboard
            self._send_sms(manager_contact['phone'], message)
            self._send_email(manager_contact['email'],
                           subject=f"⚠️ HIGH SURGE ALERT - {surge_event.place_id}",
                           body=message,
                           attachment=emergency_schedule)
            self._send_slack_alert(message, channel='#surge-alerts')
        
        else:
            # MODERATE: Dashboard + Email only
            self._send_email(manager_contact['email'],
                           subject=f"⚡ Surge Detected - {surge_event.place_id}",
                           body=message,
                           attachment=emergency_schedule)
            self._send_slack_alert(message, channel='#surge-alerts')
    
    def _format_alert_message(self, surge: 'SurgeEvent', llm: Optional[dict]) -> str:
        """Format alert message with key information."""
        
        emoji_map = {
            'critical': '🚨',
            'high': '⚠️',
            'moderate': '⚡'
        }
        
        msg = f"""{emoji_map[surge.severity]} SURGE ALERT - Venue {surge.place_id}

CURRENT STATUS:
• Demand: {surge.avg_ratio:.1f}x normal ({surge.trend})
• Detected: {surge.detected_at.strftime('%H:%M')}
• Root cause: {surge.root_cause}
• Risk score: {surge.risk_score:.2f}

"""
        
        if llm:
            msg += f"""DETAILED ANALYSIS:
• {llm['root_cause_detailed']}
• Viral potential: {llm['viral_potential']:.0%}
• Est. duration: {llm['estimated_duration_hours']}h
• Urgency LEVEL: {llm['urgency_level']:.0%}

"""
        
        msg += f"""RECOMMENDATIONS:
"""
        for rec in surge.recommendations:
            msg += f"• {rec}\n"
        
        msg += f"""
Auto-generated emergency schedule attached.
Reply ACCEPT to activate schedule and notify staff.
"""
        
        return msg
    
    def _send_sms(self, phone: str, message: str, urgent: bool = False):
        """Send SMS via Twilio."""
        try:
            if urgent:
                message = f"🚨 URGENT 🚨\n{message}"
            
            self.twilio_client.messages.create(
                body=message[:1600],  # SMS limit
                from_=self.twilio_from,
                to=phone
            )
        except Exception as e:
            print(f"SMS send error: {e}")
    
    def _send_email(self, email: str, subject: str, body: str, attachment: any = None):
        """Send email via SendGrid."""
        # Implementation using SendGrid API
        pass
    
    def _send_slack_alert(self, message: str, channel: str = '#surge-alerts'):
        """Send Slack notification."""
        if not self.slack_webhook:
            return
        
        try:
            requests.post(self.slack_webhook, json={
                'channel': channel,
                'text': message,
                'username': 'Surge Alert Bot'
            })
        except Exception as e:
            print(f"Slack send error: {e}")
    
    def _make_voice_call(self, phone: str, message: str):
        """Make voice call via Twilio (critical alerts only)."""
        try:
            call = self.twilio_client.calls.create(
                twiml=f'<Response><Say>{message}</Say></Response>',
                from_=self.twilio_from,
                to=phone
            )
        except Exception as e:
            print(f"Voice call error: {e}")
```

---

### 6. Emergency Schedule Generator

**File:** `src/emergency_scheduler.py` (new)

```python
from scheduler_cpsat import solve_schedule, SchedulerInput
from typing import Dict, List

class EmergencyScheduler:
    """
    Rapid schedule generation for surge response.
    """
    
    def generate_emergency_schedule(self,
                                   base_schedule_input: SchedulerInput,
                                   surge_factor: float,
                                   surge_start_hour: int,
                                   surge_duration_hours: int,
                                   on_call_employees: List['Employee']) -> Dict:
        """
        Generate emergency schedule by:
        1. Increasing demand for surge period
        2. Adding on-call employees to pool
        3. Lowering wage weight (prioritize coverage)
        4. Fast solve (30-second limit)
        
        Args:
            base_schedule_input: Original schedule parameters
            surge_factor: Demand multiplier (e.g., 2.5 = 2.5x normal)
            surge_start_hour: Which hour surge starts (0-167 for weekly)
            surge_duration_hours: How long surge lasts
            on_call_employees: Additional staff available
        
        Returns:
            {
                'schedule': [...],
                'added_staff': int,
                'additional_cost': float,
                'coverage_improvement': float
            }
        """
        # Clone input
        emergency_input = self._clone_input(base_schedule_input)
        
        # Add on-call employees
        emergency_input.employees.extend(on_call_employees)
        
        # Increase demand for surge period
        for (d, t), demand in emergency_input.demand.items():
            hour_index = d * 24 + t
            if surge_start_hour <= hour_index < surge_start_hour + surge_duration_hours:
                emergency_input.demand[(d, t)] = demand * surge_factor
        
        # Adjust weights: prioritize coverage over cost
        emergency_input.w_wage = 10  # Reduce from default 100
        emergency_input.w_unmet = 100000  # Keep very high
        
        # Solve quickly
        solution, description, insights = solve_schedule(
            emergency_input, 
            time_limit_seconds=30  # Fast solve for real-time
        )
        
        if not solution:
            return None
        
        # Compare to base
        base_cost = sum(
            emp.wage * base_schedule_input.employees[i].max_hours_per_week
            for i, emp in enumerate(base_schedule_input.employees)
        )
        emergency_cost = insights['cost_analysis']['total_wage_cost']
        
        return {
            'schedule': solution['schedule'],
            'added_staff': len(on_call_employees),
            'additional_cost': emergency_cost - base_cost,
            'coverage_improvement': f"{surge_factor:.1f}x capacity",
            'insights': insights
        }
    
    def _clone_input(self, input_data: SchedulerInput) -> SchedulerInput:
        """Deep copy input data."""
        import copy
        return copy.deepcopy(input_data)
```

---

## Data Flow

### Continuous Monitoring Loop (Background Process)

```
┌─────────────────────────────────────────────────────────────┐
│ EVERY 5 MINUTES (Celery Beat Task)                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  For each active_venue in database:                         │
│                                                              │
│    1. RealTimeDataCollector.aggregate_and_store()           │
│       ├─ Fetch actual orders from last hour                 │
│       ├─ Fetch predictions from cache                       │
│       ├─ Fetch social media signals (15min cache)           │
│       └─ Store in database time-series                         │
│                                                              │
│    2. SurgeDetector.check_surge()                           │
│       ├─ Load last 3 hours of metrics from storage            │
│       ├─ Check surge conditions                             │
│       └─ Return SurgeEvent or None                          │
│                                                              │
│    3. IF surge detected:                                    │
│       ├─ Calculate risk_score                               │
│       │                                                      │
│       ├─ IF risk_score < 0.7: (99% of cases)                │
│       │   └─ Use numeric signals only                       │
│       │                                                      │
│       └─ IF risk_score >= 0.7: (1% of cases)                │
│           ├─ Fetch top social media posts                   │
│           ├─ Call LLMSurgeAnalyzer (~$0.03)                 │
│           └─ Enhance insights with LLM analysis             │
│                                                              │
│    4. EmergencyScheduler.generate_emergency_schedule()      │
│       └─ Solve schedule with surge demand                   │
│                                                              │
│    5. AlertDispatcher.dispatch_surge_alert()                │
│       ├─ Send SMS (if high/critical)                        │
│       ├─ Send email                                         │
│       ├─ Post to Slack                                      │
│       └─ Voice call (if critical)                           │
│                                                              │
│    6. Log event to database                                 │
│       └─ For historical analysis and ML training            │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Implementation Plan

### Phase 1: Foundation (Week 1-2)

**Goals:**
- [ ] Set up time-series data storage
- [ ] Implement RealTimeDataCollector (without social APIs)
- [ ] Implement SurgeDetector core logic
- [ ] Unit tests for detection algorithm

**Deliverables:**
1. `src/data_collector.py` - Collect actuals vs predictions
2. `src/surge_detector.py` - Detection algorithm
3. Database schema documentation
4. Test suite with synthetic surge data

**Testing:**
- Create synthetic surge scenarios (2x, 3x, 5x spikes)
- Verify detection within 15 minutes of surge start
- Test cooldown prevents alert spam
- Validate risk score calculation

---

### Phase 2: Social Media Integration (Week 3-4)

**Goals:**
- [ ] Integrate Google Trends API
- [ ] Integrate Twitter API (free tier)
- [ ] Integrate Eventbrite API
- [ ] Implement 15-minute caching layer

**Deliverables:**
1. `src/social_media_apis.py` - All numeric APIs
2. API credentials setup guide
3. Rate limit monitoring
4. Fallback handling (API down = degrade gracefully)

**Testing:**
- Verify API calls succeed
- Test cache reduces calls by 95%
- Validate composite signal calculation
- Test API failure handling

---

### Phase 3: Alert System (Week 5-6)

**Goals:**
- [ ] Implement SMS alerts (Twilio)
- [ ] Implement email alerts (SendGrid)
- [ ] Implement Slack webhooks
- [ ] Integrate with emergency scheduler

**Deliverables:**
1. `src/alert_system.py` - Multi-channel alerts
2. `src/emergency_scheduler.py` - Fast schedule generation
3. Alert templates (SMS, email, Slack)
4. Manager dashboard mockup

**Testing:**
- Send test alerts to dev team
- Verify severity routing works
- Test schedule generation under 30 seconds
- End-to-end surge detection → alert flow

---

### Phase 4: LLM Enhancement (Week 7-8) - OPTIONAL

**Goals:**
- [ ] Implement LLM analyzer (Claude API)
- [ ] Fetch social media post content (not just counts)
- [ ] Risk threshold tuning (when to call LLM)
- [ ] Cost monitoring and budget alerts

**Deliverables:**
1. `src/llm_analyzer.py` - Deep analysis
2. Social media post fetcher
3. Cost tracking dashboard
4. A/B test: LLM vs numeric-only accuracy

**Testing:**
- Compare LLM recommendations vs human expert
- Measure accuracy improvement vs cost
- Test budget circuit breaker (stop if $X/day exceeded)

---

### Phase 5: Production Deployment (Week 9-10)

**Goals:**
- [ ] Deploy background monitoring service
- [ ] Set up production data storage
- [ ] Configure alerting channels
- [ ] Train operations team

**Deliverables:**
1. Docker containers for all services
2. Kubernetes/ECS deployment configs
3. Monitoring dashboards (Grafana)
4. Runbook for oncall engineers
5. Manager training materials

**Testing:**
- Load testing (100 venues × 5min = stable?)
- Failure testing (storage down, API outage)
- End-to-end production test with staging data

---

## API Integration Details

### Required API Accounts

| API | Sign-up URL | Free Tier | Needed For |
|-----|-------------|-----------|------------|
| **Google Trends** | Use pytrends library | Unlimited | Search volume |
| **Twitter API** | developer.twitter.com | 500k tweets/month | Mentions, engagement |
| **Eventbrite** | www.eventbrite.com/platform | 1000 requests/day | Nearby events |
| **Twilio** | www.twilio.com | Trial credits | SMS alerts |
| **SendGrid** | sendgrid.com | 100 emails/day | Email alerts |
| **Slack** | api.slack.com | Unlimited webhooks | Team notifications |
| **Anthropic Claude** | console.anthropic.com | Pay-per-token | LLM analysis (optional) |

### Environment Variables Setup

```bash
# Social Media APIs
export TWITTER_BEARER_TOKEN="your_bearer_token_here"
export EVENTBRITE_API_KEY="your_eventbrite_key"

# Alert Channels
export TWILIO_ACCOUNT_SID="your_twilio_sid"
export TWILIO_AUTH_TOKEN="your_twilio_token"
export TWILIO_PHONE_NUMBER="+45xxxxxxxx"
export SENDGRID_API_KEY="your_sendgrid_key"
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."

# LLM (Optional)
export ANTHROPIC_API_KEY="your_anthropic_key"

# Twitter API
export TWITTER_BEARER_TOKEN="your_token"
```

### API Cost Estimates (Monthly)

**Numeric APIs (Always Running):**
- Google Trends: $0 (free)
- Twitter API: $0 (free tier, 500k tweets/month = ~70 venues × 100 checks/day)
- Eventbrite: $0 (free tier, 1000 req/day = plenty)
- **Total: $0/month**

**Alert System:**
- Twilio SMS: $0.075/SMS × 30 alerts/month = $2.25
- SendGrid: Free (100/day >> 5/day needed)
- Slack: Free
- **Total: ~$2-5/month**

**LLM Enhancement (Optional, High-Risk Only):**
- Claude API: $0.03/call × 10-20 calls/day = $9-18/month
- Only called when risk_score > 0.7 (top 1% of surges)
- **Total: $10-20/month**

**Grand Total: $12-25/month** for full system (or $2-5/month without LLM)

---

## Decision Logic

### When to Call LLM vs Numeric-Only

```python
def decide_analysis_depth(risk_score: float, budget_remaining: float) -> str:
    """
    Decide whether to use LLM analysis.
    
    Decision tree:
    1. risk_score < 0.5: No surge, skip
    2. 0.5 <= risk_score < 0.7: Numeric only (fast, free)
    3. risk_score >= 0.7 AND budget_ok: LLM analysis
    4. risk_score >= 0.7 AND budget_low: Numeric only (fallback)
    """
    if risk_score < 0.5:
        return 'skip'
    elif risk_score < 0.7:
        return 'numeric_only'
    elif budget_remaining > 0.10:  # At least $0.10 left today
        return 'llm_enhanced'
    else:
        return 'numeric_only'  # Budget exhausted
```

### Severity Thresholds

| Metric | Moderate | High | Critical |
|--------|----------|------|----------|
| **Ratio** | 1.5-2.0x | 2.0-3.0x | >3.0x |
| **Excess Demand** | 30-60 items/hr | 60-100 items/hr | >100 items/hr |
| **Social Virality** | 0.5-0.7 | 0.7-0.85 | >0.85 |
| **Response Time** | <30 minutes | <15 minutes | <5 minutes |
| **Manager Action** | Monitor & standby | Activate protocol | All hands on deck |

---

## Alert & Response System

### Alert Flow by Severity

```
MODERATE SURGE (1.5-2.0x)
  ├─ Email to shift manager (5-min delivery)
  ├─ Dashboard notification
  └─ Slack #surge-alerts channel
  
  Manager Action:
  ├─ Alert on-call staff to standby
  ├─ Consider extending current shifts
  └─ Monitor trend (check dashboard every 15min)

HIGH SURGE (2.0-3.0x)
  ├─ SMS to shift manager (instant)
  ├─ Email with emergency schedule attached
  ├─ Slack #surge-alerts with @channel mention
  └─ Dashboard high-priority badge
  
  Manager Action:
  ├─ Call in 1-2 on-call employees immediately
  ├─ Extend current shifts with overtime approval
  └─ Notify regional manager

CRITICAL SURGE (>3.0x)
  ├─ SMS to shift + regional manager (instant)
  ├─ Voice call to shift manager
  ├─ Email with actionable steps
  ├─ Slack #critical-alerts with @here
  └─ Dashboard red alert banner
  
  Manager Action:
  ├─ Execute full emergency protocol
  ├─ Call in ALL on-call staff
  ├─ Contact senior leadership
  ├─ Consider temporary pause on new orders
  └─ Prepare for extended operations (2-6 hours)
```

### Manager Response Interface

**SMS Response Commands:**
```
ACCEPT → Activate emergency schedule, notify employees
STATUS → Get current surge status update
DISMISS → Acknowledge alert, no schedule change
HELP → Get list of on-call employees with phone numbers
```

**Dashboard Actions:**
- Review emergency schedule (visual timeline)
- Modify schedule before activating
- Send push notifications to selected employees
- Track who accepted shifts (real-time status)
- View cost estimate and coverage improvement

---

## Cost-Benefit Analysis

### Without Surge Detection

**Scenario:** 3x surge occurs, manager discovers 45 minutes late

| Metric | Impact |
|--------|--------|
| Lost orders | ~150 items × $15 = **$2,250 lost revenue** |
| Poor service quality | Angry customers, bad reviews |
| Employee burnout | Overloaded staff, high stress |
| Response time | 45-60 minutes to mobilize staff |

### With Surge Detection

**Scenario:** Same 3x surge, detected in 10 minutes

| Metric | Impact |
|--------|--------|
| Early detection | Alert sent after 2nd consecutive high ratio |
| Staff mobilization | 10-15 minutes (automated schedule ready) |
| Revenue protected | ~80% of surge demand met = **$1,800 captured** |
| Implementation cost | $12-25/month |
| **ROI** | **One surge prevented pays for 6+ months** |

### Break-Even Analysis

```
Monthly cost: $25
Revenue per prevented surge: ~$1,500 (conservative)

Break-even: 1 surge prevented every 60 months
Expected: 2-5 surges/month across all venues
Actual ROI: 60:1 to 300:1
```

---

## Testing Strategy

### Unit Tests

```python
# tests/test_surge_detector.py

def test_surge_detection_positive():
    """Verify surge detected when all ratios > threshold."""
    detector = SurgeDetector(surge_threshold=1.5, window_hours=3)
    
    metrics = [
        SurgeMetrics(ratio=1.6, actual=160, predicted=100, ...),
        SurgeMetrics(ratio=1.8, actual=180, predicted=100, ...),
        SurgeMetrics(ratio=2.0, actual=200, predicted=100, ...)
    ]
    
    event = detector.check_surge(place_id=1, metrics=metrics)
    
    assert event is not None
    assert event.severity in ['moderate', 'high', 'critical']
    assert event.avg_ratio >= 1.5

def test_surge_detection_false_positive():
    """Verify no surge when ratios intermittent."""
    detector = SurgeDetector(surge_threshold=1.5, window_hours=3)
    
    metrics = [
        SurgeMetrics(ratio=1.6, ...),
        SurgeMetrics(ratio=1.1, ...),  # Drops below threshold
        SurgeMetrics(ratio=1.7, ...)
    ]
    
    event = detector.check_surge(place_id=1, metrics=metrics)
    
    assert event is None  # Not all above threshold

def test_cooldown_prevents_spam():
    """Verify cooldown period prevents repeated alerts."""
    detector = SurgeDetector(cooldown_hours=2)
    
    # First detection
    event1 = detector.check_surge(place_id=1, metrics=surge_metrics)
    assert event1 is not None
    
    # Second detection 30 minutes later (within cooldown)
    event2 = detector.check_surge(place_id=1, metrics=surge_metrics)
    assert event2 is None  # Blocked by cooldown

def test_risk_score_calculation():
    """Verify risk score weights components correctly."""
    # High ratio, low social signal
    metrics_1 = create_metrics(ratio=3.0, social=0.1, trend='stable')
    score_1 = calculator.calculate_risk_score(metrics_1)
    
    # Lower ratio, high social signal
    metrics_2 = create_metrics(ratio=1.6, social=0.9, trend='accelerating')
    score_2 = calculator.calculate_risk_score(metrics_2)
    
    # Verify social signal matters
    assert 0.5 < score_2 < score_1 < 1.0
```

### Integration Tests

```python
def test_end_to_end_surge_detection():
    """
    Full pipeline test: data collection → detection → alert.
    """
    # 1. Simulate high actual orders
    simulate_orders(place_id=1, hourly_count=200)  # 2x normal
    
    # 2. Run collector
    collector.aggregate_and_store(place_id=1)
    
    # 3. Wait for detection cycle
    time.sleep(5)
    
    # 4. Verify surge detected
    events = get_surge_events(place_id=1)
    assert len(events) == 1
    assert events[0].severity in ['high', 'critical']
    
    # 5. Verify alert sent
    alerts = get_sent_alerts(place_id=1)
    assert len(alerts) > 0
    assert 'SMS' in alerts[0].channels

def test_social_api_fallback():
    """
    Verify system degrades gracefully when APIs unavailable.
    """
    # Simulate Twitter API down
    mock_twitter_api_error()
    
    # System should still work with other signals
    signals = aggregator.get_composite_signal(place_id=1, ...)
    
    assert signals['twitter_mentions'] == 0  # Fallback value
    assert signals['composite_signal'] >= 0  # Still computes score
```

### Load Testing

```bash
# Simulate 100 venues being monitored every 5 minutes
locust -f tests/load_test.py --users 100 --spawn-rate 10

# Expected performance:
# - 95th percentile: <3 seconds per venue
# - Error rate: <0.1%
# - Database storage: Minimal for time-series data
```

---

## Monitoring & Observability

### Key Metrics to Track

**System Health:**
```
surge_detection.check_duration_ms - Time to check one venue
surge_detection.surge_events_count - Number of surges detected
surge_detection.false_positive_rate - Alerts dismissed by managers
social_api.call_count - API calls per hour
social_api.cache_hit_rate - % of requests served from cache
social_api.error_rate - Failed API calls
llm_analyzer.call_count - LLM API calls (budget tracking)
alert_system.delivery_time_ms - Time from detection to alert sent
emergency_schedule.solve_time_ms - Time to generate schedule
```

**Business Metrics:**
```
surge.avg_ratio - Average surge magnitude
surge.revenue_protected - Estimated revenue saved
surge.response_time_minutes - Manager action time
surge.coverage_improvement - Actual vs predicted coverage
```

### Alerts & Thresholds

```yaml
alerts:
  - name: High false positive rate
    condition: false_positive_rate > 0.3 for 1 hour
    action: Review detection thresholds, may need tuning
  
  - name: Social API down
    condition: social_api.error_rate > 0.5 for 5 minutes
    action: System degraded but functional, notify ops
  
  - name: LLM budget exceeded
    condition: llm_analyzer.daily_cost > $10
    action: Disable LLM calls, use numeric-only mode
  
  - name: Surge detection lag
    condition: surge_detection.check_duration_ms > 5000
    action: Scale up workers or optimize queries
```

---

## Future Enhancements

### Short-term (Next 3 months)
- [ ] Mobile app for manager surge responses
- [ ] Automated employee notification (SMS/push after manager accepts)
- [ ] Historical surge pattern learning (predict before they happen)
- [ ] Integration with POS systems for real-time order stream

### Medium-term (6-12 months)
- [ ] Predictive surge detection (predict 1-2 hours before peak)
- [ ] Multi-venue optimization (share staff between locations)
- [ ] Customer communication (auto-update delivery estimates during surge)
- [ ] Surge pricing recommendations (if business model allows)

### Long-term (1+ year)
- [ ] Image recognition for viral food photos
- [ ] Video analysis of TikTok trends
- [ ] Causal inference (what actions work best during surges?)
- [ ] Reinforcement learning for optimal response strategies

---

## Appendix: Example Surge Scenarios

### Scenario 1: Influencer TikTok Post

**Timeline:**
- 14:00 - Influencer posts "secret menu hack" video
- 14:30 - Video reaches 50k views, comments exploding
- 15:00 - Surge detector notices: ratio 1.4x (not yet triggered)
- 15:05 - ratio 1.7x (still 1 hour < 3-hour window)
- 15:10 - ratio 2.1x → **SURGE DETECTED** (3 consecutive hours >1.5x)
- 15:11 - Alert sent to manager: HIGH severity
- 15:15 - Manager activates emergency schedule, calls in 2 staff
- 15:45 - Additional staff arrive, surge handled
- 18:00 - Surge subsides as trend moves on

**Outcome:** Revenue protected, 4.5 star rating maintained

---

### Scenario 2: Nearby Concert Event

**Timeline:**
- 18:00 - Concert starts (detected by Eventbrite API)
- 19:00 - Concert break, surge begins
- 19:10 - **SURGE DETECTED**: ratio 3.2x, CRITICAL
- 19:11 - Multi-channel alert sent (SMS + call)
- 19:15 - Manager calls in all on-call staff
- 19:25 - Emergency schedule activated
- 20:00 - Concert resumes, demand drops
- 21:00 - Concert ends, second surge (but manager prepared)

**Outcome:** Captured 90% of surge demand, made $8K in 3 hours

---

**Document maintained by:** Engineering Team  
**Implementation Status:** Planning Phase  
**Target Launch:** Q2 2026  
**Expected ROI:** 60:1 to 300:1
