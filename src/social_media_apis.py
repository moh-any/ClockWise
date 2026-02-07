"""
Social Media API Aggregator for Surge Detection
Collects numeric signals from multiple social media platforms.
"""

import os
import requests
import time
from typing import Dict, Optional
from datetime import datetime, timedelta
from functools import lru_cache


class SocialMediaAggregator:
    """
    Aggregates signals from multiple social media APIs.
    All methods return numeric scores (no text analysis needed for basic version).
    
    Features:
    - Google Trends (search interest)
    - Twitter/X API (mentions, engagement)
    - Eventbrite (nearby events)
    - 15-minute caching to reduce API calls
    """
    
    def __init__(self, demo_mode: bool = False):
        """
        Initialize aggregator with API credentials from environment.
        
        Args:
            demo_mode: If True, use simulated data instead of real API calls
        """
        # API credentials (from environment variables)
        self.twitter_bearer = os.getenv('TWITTER_BEARER_TOKEN')
        self.eventbrite_key = os.getenv('EVENTBRITE_API_KEY')
        self.demo_mode = demo_mode
        
        # In-memory cache
        self._cache = {}
        self._cache_ttl = 900  # 15 minutes in seconds
        
        print("🔌 Social Media Aggregator initialized")
        if demo_mode:
            print("   🎭 DEMO MODE: Using simulated data")
        else:
            print(f"   Twitter API: {'✅' if self.twitter_bearer else '❌ (set TWITTER_BEARER_TOKEN)'}")
            print(f"   Eventbrite API: {'✅' if self.eventbrite_key else '❌ (set EVENTBRITE_API_KEY)'}")
    
    def get_composite_signal(self, 
                            place_id: int, 
                            venue_name: str,
                            latitude: float, 
                            longitude: float) -> Dict[str, float]:
        """
        Get all social signals and compute composite score.
        Results are cached for 15 minutes to reduce API costs.
        
        Args:
            place_id: Venue ID
            venue_name: Restaurant name for search queries
            latitude: Location latitude
            longitude: Location longitude
        
        Returns:
            {
                'google_trends': 0.75,       # 0-1 (normalized from 0-100)
                'twitter_mentions': 45,       # Raw count
                'twitter_virality': 0.82,     # 0-1 engagement rate
                'nearby_events': 2,           # Count of events
                'event_attendance': 1500,     # Total expected
                'composite_signal': 0.68      # Weighted average
            }
        """
        # Check cache (round to 10 minutes for better hit rate)
        cache_key = f"social:{place_id}:{datetime.now().strftime('%Y%m%d%H%M')[:-1]}0"
        
        if cache_key in self._cache:
            cache_time, cached_data = self._cache[cache_key]
            if time.time() - cache_time < self._cache_ttl:
                return cached_data
        
        # Collect signals
        signals = {}
        
        # Use demo data if in demo mode
        if self.demo_mode:
            signals = self._get_demo_signals(place_id, venue_name)
        else:
            # Google Trends (free, no rate limit)
            signals['google_trends'] = self._get_google_trends(venue_name)
            
            # Twitter (free tier: 500k tweets/month)
            twitter_data = self._get_twitter_metrics(venue_name)
            signals['twitter_mentions'] = twitter_data['mentions']
            signals['twitter_virality'] = twitter_data['virality']
            
            # Nearby events
            event_data = self._get_nearby_events(latitude, longitude)
            signals['nearby_events'] = event_data['count']
            signals['event_attendance'] = event_data['total_attendance']
        
        # Composite score (weighted average of signals)
        composite = self._calculate_composite_score(signals)
        signals['composite_signal'] = composite
        
        # Cache result
        self._cache[cache_key] = (time.time(), signals)
        
        return signals
    
    def _calculate_composite_score(self, signals: Dict[str, float]) -> float:
        """
        Calculate weighted composite score from all signals.
        
        Weights:
        - Twitter virality: 45% (strongest indicator of viral surge)
        - Google Trends: 30% (search interest)
        - Events: 25% (physical proximity events)
        
        Returns:
            Float between 0-1
        """
        composite = (
            signals['twitter_virality'] * 0.45 +
            (signals['google_trends'] / 100) * 0.30 +
            min(1.0, signals['event_attendance'] / 5000) * 0.25
        )
        return min(1.0, max(0.0, composite))
    
    def _get_demo_signals(self, place_id: int, venue_name: str) -> Dict[str, float]:
        """
        Generate simulated social media signals for demo/testing.
        
        Args:
            place_id: Venue ID
            venue_name: Restaurant name
        
        Returns:
            Dictionary with simulated signals
        """
        import random
        
        # Use place_id as seed for consistent results per venue
        random.seed(place_id + int(time.time() / 3600))  # Changes every hour
        
        # Simulate realistic signal ranges
        return {
            'google_trends': random.uniform(20, 85),  # 20-85 range
            'twitter_mentions': random.randint(5, 50),  # 5-50 mentions
            'twitter_virality': random.uniform(0.3, 0.9),  # 0.3-0.9 virality
            'nearby_events': random.randint(0, 3),  # 0-3 events
            'event_attendance': random.randint(0, 2000)  # 0-2000 people
        }
    
    def _get_google_trends(self, keyword: str) -> float:
        """
        Get Google Trends score (0-100) for keyword.
        Uses pytrends library (free, no API key needed).
        
        Args:
            keyword: Search term (venue name)
        
        Returns:
            Interest score 0-100 (0 = no interest, 100 = peak interest)
        """
        try:
            from pytrends.request import TrendReq
            
            pytrends = TrendReq(hl='en-US', tz=360, timeout=(10, 25))
            pytrends.build_payload([keyword], timeframe='now 1-d', geo='DK')
            
            interest = pytrends.interest_over_time()
            
            if not interest.empty and keyword in interest.columns:
                return float(interest[keyword].iloc[-1])
            
            return 0.0
            
        except ImportError:
            print("⚠️  pytrends not installed. Install with: pip install pytrends")
            return 0.0
        except Exception as e:
            print(f"⚠️  Google Trends error: {e}")
            return 0.0
    
    def _get_twitter_metrics(self, venue_name: str) -> Dict[str, float]:
        """
        Get Twitter mention count and engagement metrics.
        Uses Twitter API v2 (free tier: 500k tweets/month).
        
        Args:
            venue_name: Restaurant name to search for
        
        Returns:
            {
                'mentions': int (count of mentions),
                'virality': float (0-1 engagement rate)
            }
        """
        if not self.twitter_bearer:
            return {'mentions': 0, 'virality': 0.0}
        
        try:
            url = "https://api.twitter.com/2/tweets/search/recent"
            headers = {'Authorization': f'Bearer {self.twitter_bearer}'}
            
            # Query: mentions of venue in last 6 hours (excluding retweets)
            query = f'"{venue_name}" -is:retweet'
            start_time = (datetime.now() - timedelta(hours=6)).strftime('%Y-%m-%dT%H:%M:%SZ')
            
            params = {
                'query': query,
                'start_time': start_time,
                'tweet.fields': 'public_metrics',
                'max_results': 100
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code != 200:
                print(f"⚠️  Twitter API error: {response.status_code}")
                return {'mentions': 0, 'virality': 0.0}
            
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
            # Assumption: 50 engagements per mention = 1.0 virality score
            virality = min(1.0, total_engagement / (mention_count * 50))
            
            return {
                'mentions': mention_count,
                'virality': virality
            }
            
        except Exception as e:
            print(f"⚠️  Twitter metrics error: {e}")
            return {'mentions': 0, 'virality': 0.0}
    
    
    def _get_nearby_events(self, latitude: float, longitude: float) -> Dict[str, int]:
        """
        Get nearby events from Eventbrite API.
        
        Args:
            latitude: Location latitude
            longitude: Location longitude
        
        Returns:
            {
                'count': int (number of events),
                'total_attendance': int (sum of expected attendees)
            }
        """
        if not self.eventbrite_key:
            return {'count': 0, 'total_attendance': 0}
        
        try:
            url = "https://www.eventbriteapi.com/v3/events/search/"
            
            # Search for events today within 5km
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
            
            if response.status_code != 200:
                print(f"⚠️  Eventbrite API error: {response.status_code}")
                return {'count': 0, 'total_attendance': 0}
            
            events = response.json().get('events', [])
            
            # Sum expected attendance (default 200 if not specified)
            total_attendance = sum(
                e.get('capacity', 200) for e in events
            )
            
            return {
                'count': len(events),
                'total_attendance': total_attendance
            }
            
        except Exception as e:
            print(f"⚠️  Eventbrite error: {e}")
            return {'count': 0, 'total_attendance': 0}
    
    def clear_cache(self):
        """Clear the internal cache."""
        self._cache.clear()
    
    def get_cache_stats(self) -> Dict[str, int]:
        """
        Get cache statistics.
        
        Returns:
            {
                'cache_size': int,
                'cache_ttl_seconds': int
            }
        """
        return {
            'cache_size': len(self._cache),
            'cache_ttl_seconds': self._cache_ttl
        }


# Singleton instance
_aggregator = None


def get_social_aggregator(demo_mode: bool = False) -> SocialMediaAggregator:
    """
    Get or create social media aggregator singleton.
    
    Args:
        demo_mode: If True, use simulated data instead of real API calls
    
    Returns:
        SocialMediaAggregator instance
    """
    global _aggregator
    
    if _aggregator is None:
        _aggregator = SocialMediaAggregator(demo_mode=demo_mode)
    
    return _aggregator
