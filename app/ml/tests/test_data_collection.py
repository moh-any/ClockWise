"""
Test Suite for Layer 1: Data Collection Components
Tests social media APIs and data collector.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import json

from src.social_media_apis import SocialMediaAggregator
from src.data_collector import RealTimeDataCollector


# ============================================================================
# Social Media Aggregator Tests
# ============================================================================

class TestSocialMediaAggregator:
    """Test social media signal collection."""
    
    def test_initialization(self):
        """Test aggregator initialization."""
        aggregator = SocialMediaAggregator()
        
        assert aggregator._cache_ttl == 900  # 15 minutes
        assert isinstance(aggregator._cache, dict)
    
    def test_composite_signal_calculation(self):
        """Test composite score calculation."""
        aggregator = SocialMediaAggregator()
        
        signals = {
            'twitter_virality': 0.8,
            'google_trends': 80,
            'event_attendance': 2000
        }
        
        composite = aggregator._calculate_composite_score(signals)
        
        assert 0.0 <= composite <= 1.0
        assert composite > 0.3  # Should be positive with these signals
    
    def test_google_trends_fallback(self):
        """Test Google Trends with missing library."""
        aggregator = SocialMediaAggregator()
        
        # Should return 0 if pytrends not available
        result = aggregator._get_google_trends("test venue")
        
        assert result >= 0.0
        assert result <= 100.0
    
    def test_twitter_metrics_no_token(self):
        """Test Twitter metrics without API token."""
        aggregator = SocialMediaAggregator()
        aggregator.twitter_bearer = None
        
        result = aggregator._get_twitter_metrics("test venue")
        
        assert result == {'mentions': 0, 'virality': 0.0}
    
    @patch('requests.get')
    def test_twitter_metrics_success(self, mock_get):
        """Test successful Twitter API call."""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': [
                {
                    'public_metrics': {
                        'retweet_count': 10,
                        'like_count': 50,
                        'reply_count': 5
                    }
                }
            ]
        }
        mock_get.return_value = mock_response
        
        aggregator = SocialMediaAggregator()
        aggregator.twitter_bearer = "fake_token"
        
        result = aggregator._get_twitter_metrics("test venue")
        
        assert result['mentions'] == 1
        assert 0.0 <= result['virality'] <= 1.0
    
    @patch('requests.get')
    def test_twitter_metrics_api_error(self, mock_get):
        """Test Twitter API error handling."""
        mock_response = Mock()
        mock_response.status_code = 429  # Rate limit
        mock_get.return_value = mock_response
        
        aggregator = SocialMediaAggregator()
        aggregator.twitter_bearer = "fake_token"
        
        result = aggregator._get_twitter_metrics("test venue")
        
        assert result == {'mentions': 0, 'virality': 0.0}
    
    @patch('requests.get')
    def test_eventbrite_success(self, mock_get):
        """Test successful Eventbrite API call."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'events': [
                {'capacity': 500},
                {'capacity': 1000}
            ]
        }
        mock_get.return_value = mock_response
        
        aggregator = SocialMediaAggregator()
        aggregator.eventbrite_key = "fake_key"
        
        result = aggregator._get_nearby_events(55.6761, 12.5683)
        
        assert result['count'] == 2
        assert result['total_attendance'] == 1500
    
    def test_eventbrite_no_token(self):
        """Test Eventbrite without API key."""
        aggregator = SocialMediaAggregator()
        aggregator.eventbrite_key = None
        
        result = aggregator._get_nearby_events(55.6761, 12.5683)
        
        assert result == {'count': 0, 'total_attendance': 0}
    
    def test_cache_functionality(self):
        """Test caching reduces API calls."""
        aggregator = SocialMediaAggregator()
        
        # First call - should fetch
        with patch.object(aggregator, '_get_google_trends', return_value=50.0):
            with patch.object(aggregator, '_get_twitter_metrics', return_value={'mentions': 10, 'virality': 0.5}):
                with patch.object(aggregator, '_get_nearby_events', return_value={'count': 1, 'total_attendance': 200}):
                    signals1 = aggregator.get_composite_signal(1, "venue", 55.6761, 12.5683)
        
        # Second call - should use cache
        with patch.object(aggregator, '_get_google_trends') as mock_trends:
            signals2 = aggregator.get_composite_signal(1, "venue", 55.6761, 12.5683)
            
            # Should not call API again
            mock_trends.assert_not_called()
        
        assert signals1 == signals2
    
    def test_clear_cache(self):
        """Test cache clearing."""
        aggregator = SocialMediaAggregator()
        aggregator._cache['test'] = (1234, {'data': 'test'})
        
        aggregator.clear_cache()
        
        assert len(aggregator._cache) == 0
    
    def test_get_cache_stats(self):
        """Test cache statistics."""
        aggregator = SocialMediaAggregator()
        
        stats = aggregator.get_cache_stats()
        
        assert 'cache_size' in stats
        assert 'cache_ttl_seconds' in stats
        assert stats['cache_ttl_seconds'] == 900


# ============================================================================
# Data Collector Tests
# ============================================================================

class TestRealTimeDataCollector:
    """Test real-time data collection and aggregation."""
    
    def test_initialization(self):
        """Test collector initialization."""
        collector = RealTimeDataCollector()
        
        assert collector.update_interval == 300
        assert collector.social is not None
    
    def test_simulate_actual_orders(self):
        """Test order simulation generates realistic data."""
        collector = RealTimeDataCollector()
        
        orders = collector._simulate_actual_orders(
            place_id=1,
            time_window=timedelta(hours=3)
        )
        
        assert len(orders) == 3  # 3 hours
        
        for timestamp, data in orders.items():
            assert 'item_count' in data
            assert 'order_count' in data
            assert data['item_count'] > 0
            assert data['order_count'] > 0
    
    def test_predict_with_model(self):
        """Test predictions when model not available."""
        collector = RealTimeDataCollector()
        collector.model = None
        
        predictions = collector._predict_with_model(
            place_id=1,
            time_window=timedelta(hours=2)
        )
        
        assert len(predictions) == 2
        
        for timestamp, data in predictions.items():
            assert 'item_count_pred' in data
            assert 'order_count_pred' in data
            assert data['item_count_pred'] > 0
    
    def test_aggregate_and_collect_success(self):
        """Test successful data aggregation and collection."""
        collector = RealTimeDataCollector()
        
        # Mock social media aggregator
        collector.social = Mock()
        collector.social.get_composite_signal.return_value = {
            'composite_score': 0.5,
            'twitter_virality': 0.3
        }
        
        result = collector.aggregate_and_collect(
            place_id=1,
            venue_name="Test Venue",
            latitude=55.6761,
            longitude=12.5683
        )
        
        # Should return metrics dict
        assert result is not None
        assert isinstance(result, dict)
        assert 'place_id' in result
        assert 'timestamp' in result
        assert 'actual_items' in result
        assert 'predicted_items' in result
        assert 'ratio' in result
        assert 'social_signals' in result
        assert result['place_id'] == 1
    
    def test_aggregate_and_collect_handles_error(self):
        """Test error handling in aggregation."""
        collector = RealTimeDataCollector()
        
        # Mock social media aggregator to raise error
        collector.social = Mock()
        collector.social.get_composite_signal.side_effect = Exception("API error")
        
        result = collector.aggregate_and_collect(
            place_id=1,
            venue_name="Test Venue",
            latitude=55.6761,
            longitude=12.5683
        )
        
        # Should return None on error
        assert result is None
    
    def test_collect_for_all_venues(self):
        """Test batch collection for multiple venues."""
        collector = RealTimeDataCollector()
        
        # Mock social media aggregator
        collector.social = Mock()
        collector.social.get_composite_signal.return_value = {'composite_score': 0.5}
        
        venues = [
            {'place_id': 1, 'name': 'Venue 1', 'latitude': 55.6761, 'longitude': 12.5683},
            {'place_id': 2, 'name': 'Venue 2', 'latitude': 55.6861, 'longitude': 12.5700}
        ]
        
        result = collector.collect_for_all_venues(venues)
        
        # Check result structure
        assert 'metrics' in result
        assert 'summary' in result
        
        # Check summary stats
        assert result['summary']['total_venues'] == 2
        assert result['summary']['successful'] == 2
        assert result['summary']['failed'] == 0
        assert result['summary']['duration_seconds'] >= 0
        
        # Check metrics list
        assert len(result['metrics']) == 2
        assert result['metrics'][0]['place_id'] == 1
        assert result['metrics'][1]['place_id'] == 2
    
    def test_ratio_calculation(self):
        """Test demand ratio calculation."""
        collector = RealTimeDataCollector()
        
        # Mock social media aggregator
        collector.social = Mock()
        collector.social.get_composite_signal.return_value = {'composite_score': 0.5}
        
        # Mock specific values
        with patch.object(collector, 'collect_actual_orders', return_value={
            datetime.now(): {'item_count': 200, 'order_count': 50}
        }):
            with patch.object(collector, 'collect_predictions', return_value={
                datetime.now(): {'item_count_pred': 100, 'order_count_pred': 25}
            }):
                result = collector.aggregate_and_collect(1, "Test", 55.6761, 12.5683)
        
        # Check calculated ratio
        assert result is not None
        assert result['ratio'] == 2.0
        assert result['excess_demand'] == 100
        assert result['actual_items'] == 200
        assert result['predicted_items'] == 100
    
    def test_get_single_venue_metrics(self):
        """Test convenience method for single venue."""
        collector = RealTimeDataCollector()
        
        # Mock social media aggregator
        collector.social = Mock()
        collector.social.get_composite_signal.return_value = {'composite_score': 0.7}
        
        result = collector.get_single_venue_metrics(
            place_id=123,
            venue_name="Test Restaurant",
            latitude=55.6761,
            longitude=12.5683
        )
        
        # Should return same as aggregate_and_collect
        assert result is not None
        assert result['place_id'] == 123
        assert 'timestamp' in result
        assert 'ratio' in result


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
