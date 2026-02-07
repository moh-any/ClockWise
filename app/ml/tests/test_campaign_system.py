"""
Comprehensive tests for Campaign Analysis and Recommendation System

Tests cover:
1. CampaignMetrics - Dataclass creation and validation
2. CampaignAnalyzer - Campaign effectiveness analysis, item affinity, temporal patterns
3. CampaignRecommender - Recommendation generation, Thompson Sampling, model training
4. RecommenderContext - Context creation and validation
5. Integration - End-to-end workflow from analysis to recommendations

Usage:
    pytest tests/test_campaign_system.py -v
    pytest tests/test_campaign_system.py::TestCampaignAnalyzer -v
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import sys
import os
import json
import tempfile

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.campaign_analyzer import CampaignAnalyzer, CampaignMetrics
from src.campaign_recommender import (
    CampaignRecommender, 
    CampaignRecommendation, 
    RecommenderContext
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def sample_orders_df():
    """Create sample orders DataFrame for testing."""
    base_time = datetime(2026, 1, 1, 12, 0, 0)
    
    orders = []
    for i in range(100):
        # Create orders over 30 days
        order_time = base_time + timedelta(days=i % 30, hours=i % 12)
        orders.append({
            'id': f'order_{i}',
            'created': int(order_time.timestamp()),
            'place_id': 'place_001',
            'total_amount': np.random.uniform(15, 50),
            'item_count': np.random.randint(1, 5)
        })
    
    return pd.DataFrame(orders)


@pytest.fixture
def sample_order_items_df():
    """Create sample order items DataFrame."""
    items = ['burger', 'pizza', 'salad', 'fries', 'drink', 'dessert']
    
    order_items = []
    for i in range(100):
        # Each order has 1-3 items
        num_items = np.random.randint(1, 4)
        for j in range(num_items):
            order_items.append({
                'order_id': f'order_{i}',
                'item_id': np.random.choice(items),
                'quantity': 1,
                'price': np.random.uniform(5, 15)
            })
    
    return pd.DataFrame(order_items)


@pytest.fixture
def sample_campaigns():
    """Create sample campaign data."""
    base_time = datetime(2026, 1, 10, 0, 0, 0)
    
    return [
        {
            'id': 'campaign_1',
            'start_time': base_time.isoformat(),
            'end_time': (base_time + timedelta(days=7)).isoformat(),
            'items_included': ['burger', 'fries'],
            'discount': 15.0
        },
        {
            'id': 'campaign_2',
            'start_time': (base_time + timedelta(days=10)).isoformat(),
            'end_time': (base_time + timedelta(days=17)).isoformat(),
            'items_included': ['pizza', 'drink'],
            'discount': 20.0
        }
    ]


@pytest.fixture
def analyzer():
    """Create CampaignAnalyzer instance."""
    return CampaignAnalyzer()


@pytest.fixture
def sample_campaign_metrics():
    """Create sample CampaignMetrics for testing."""
    return CampaignMetrics(
        campaign_id='test_campaign',
        start_date=datetime(2026, 1, 1),
        end_date=datetime(2026, 1, 7),
        items_included=['burger', 'fries'],
        discount=15.0,
        avg_daily_orders_during=50.0,
        avg_daily_orders_before=40.0,
        avg_daily_orders_after=45.0,
        uplift_percentage=25.0,
        item_uplift={'burger': 30.0, 'fries': 20.0},
        total_revenue_during=3500.0,
        total_revenue_before=2800.0,
        revenue_impact=700.0,
        day_of_week_start=0,
        hour_of_day_start=0,
        season='winter',
        weather_during={'avg_temperature': 5.0, 'avg_precipitation': 0.5},
        was_holiday=False,
        gross_margin=525.0,
        roi=85.0
    )


# =============================================================================
# TEST CAMPAIGN METRICS
# =============================================================================

class TestCampaignMetrics:
    """Test CampaignMetrics dataclass."""
    
    def test_campaign_metrics_creation(self, sample_campaign_metrics):
        """Test creating CampaignMetrics instance."""
        metrics = sample_campaign_metrics
        
        assert metrics.campaign_id == 'test_campaign'
        assert metrics.discount == 15.0
        assert metrics.uplift_percentage == 25.0
        assert metrics.roi == 85.0
    
    def test_campaign_metrics_items(self, sample_campaign_metrics):
        """Test items included in campaign."""
        metrics = sample_campaign_metrics
        
        assert 'burger' in metrics.items_included
        assert 'fries' in metrics.items_included
        assert len(metrics.items_included) == 2
    
    def test_campaign_metrics_item_uplift(self, sample_campaign_metrics):
        """Test item-level uplift metrics."""
        metrics = sample_campaign_metrics
        
        assert metrics.item_uplift['burger'] == 30.0
        assert metrics.item_uplift['fries'] == 20.0
    
    def test_campaign_metrics_dates(self, sample_campaign_metrics):
        """Test campaign date handling."""
        metrics = sample_campaign_metrics
        
        assert metrics.start_date < metrics.end_date
        duration = (metrics.end_date - metrics.start_date).days
        assert duration == 6


# =============================================================================
# TEST CAMPAIGN ANALYZER
# =============================================================================

class TestCampaignAnalyzer:
    """Test CampaignAnalyzer class."""
    
    def test_analyzer_initialization(self, analyzer):
        """Test analyzer initializes with empty state."""
        assert analyzer.campaign_metrics == []
        assert analyzer.item_affinity == {}
        assert analyzer.temporal_patterns == {}
    
    def test_analyze_campaign_effectiveness(self, analyzer, sample_orders_df, 
                                            sample_campaigns, sample_order_items_df):
        """Test campaign effectiveness analysis."""
        metrics_list = analyzer.analyze_campaign_effectiveness(
            sample_orders_df,
            sample_campaigns,
            sample_order_items_df
        )
        
        assert len(metrics_list) == 2
        assert metrics_list[0].campaign_id == 'campaign_1'
        assert metrics_list[1].campaign_id == 'campaign_2'
    
    def test_campaign_metrics_stored(self, analyzer, sample_orders_df,
                                      sample_campaigns, sample_order_items_df):
        """Test that metrics are stored in analyzer."""
        analyzer.analyze_campaign_effectiveness(
            sample_orders_df,
            sample_campaigns,
            sample_order_items_df
        )
        
        assert len(analyzer.campaign_metrics) == 2
    
    def test_campaign_discount_tracked(self, analyzer, sample_orders_df,
                                        sample_campaigns, sample_order_items_df):
        """Test campaign discount is tracked correctly."""
        metrics = analyzer.analyze_campaign_effectiveness(
            sample_orders_df,
            sample_campaigns,
            sample_order_items_df
        )
        
        assert metrics[0].discount == 15.0
        assert metrics[1].discount == 20.0
    
    def test_get_season_winter(self, analyzer):
        """Test season detection for winter."""
        winter_date = datetime(2026, 1, 15)
        season = analyzer._get_season(winter_date)
        assert season == 'winter'
    
    def test_get_season_summer(self, analyzer):
        """Test season detection for summer."""
        summer_date = datetime(2026, 7, 15)
        season = analyzer._get_season(summer_date)
        assert season == 'summer'
    
    def test_get_season_spring(self, analyzer):
        """Test season detection for spring."""
        spring_date = datetime(2026, 4, 15)
        season = analyzer._get_season(spring_date)
        assert season == 'spring'
    
    def test_get_season_fall(self, analyzer):
        """Test season detection for fall."""
        fall_date = datetime(2026, 10, 15)
        season = analyzer._get_season(fall_date)
        assert season == 'fall'
    
    def test_extract_item_affinity(self, analyzer, sample_order_items_df):
        """Test item affinity extraction."""
        affinity = analyzer.extract_item_affinity(sample_order_items_df, min_support=0.01)
        
        # Should have some item pairs
        assert isinstance(affinity, dict)
        # Affinity values should be positive (lift score)
        for pair, score in affinity.items():
            assert score >= 0
    
    def test_item_affinity_stored(self, analyzer, sample_order_items_df):
        """Test that item affinity is stored."""
        analyzer.extract_item_affinity(sample_order_items_df)
        
        assert analyzer.item_affinity is not None
    
    def test_extract_temporal_patterns(self, analyzer, sample_orders_df):
        """Test temporal pattern extraction."""
        sample_orders_df['item_count'] = 2  # Add required column
        
        patterns = analyzer.extract_temporal_patterns(sample_orders_df)
        
        assert 'by_day_of_week' in patterns
        assert 'by_hour' in patterns
        assert 'by_season' in patterns
    
    def test_temporal_patterns_by_day(self, analyzer, sample_orders_df):
        """Test patterns include all days of week."""
        sample_orders_df['item_count'] = 2
        
        patterns = analyzer.extract_temporal_patterns(sample_orders_df)
        
        # Should have patterns for all 7 days
        assert len(patterns['by_day_of_week']) == 7
    
    def test_temporal_patterns_by_hour(self, analyzer, sample_orders_df):
        """Test patterns include all hours."""
        sample_orders_df['item_count'] = 2
        
        patterns = analyzer.extract_temporal_patterns(sample_orders_df)
        
        # Should have patterns for all 24 hours
        assert len(patterns['by_hour']) == 24
    
    def test_holiday_check_christmas(self, analyzer):
        """Test holiday detection for Christmas period."""
        christmas = datetime(2026, 12, 25)
        new_year = datetime(2026, 12, 31)
        
        is_holiday = analyzer._check_holiday_overlap(christmas, new_year)
        assert is_holiday is True
    
    def test_holiday_check_regular_day(self, analyzer):
        """Test holiday detection for regular day."""
        regular_start = datetime(2026, 3, 10)
        regular_end = datetime(2026, 3, 17)
        
        is_holiday = analyzer._check_holiday_overlap(regular_start, regular_end)
        assert is_holiday is False


# =============================================================================
# TEST RECOMMENDER CONTEXT
# =============================================================================

class TestRecommenderContext:
    """Test RecommenderContext dataclass."""
    
    def test_context_creation(self):
        """Test creating RecommenderContext."""
        context = RecommenderContext(
            current_date=datetime.now(),
            day_of_week=1,
            hour=14,
            season='winter',
            recent_avg_daily_revenue=5000.0,
            recent_avg_daily_orders=150.0,
            recent_trend='stable'
        )
        
        assert context.day_of_week == 1
        assert context.hour == 14
        assert context.season == 'winter'
    
    def test_context_defaults(self):
        """Test context default values."""
        context = RecommenderContext(
            current_date=datetime.now(),
            day_of_week=0,
            hour=12,
            season='summer',
            recent_avg_daily_revenue=5000.0,
            recent_avg_daily_orders=150.0,
            recent_trend='stable'
        )
        
        assert context.max_discount == 30.0
        assert context.min_campaign_duration_days == 3
        assert context.max_campaign_duration_days == 14
    
    def test_context_with_weather(self):
        """Test context with weather forecast."""
        context = RecommenderContext(
            current_date=datetime.now(),
            day_of_week=2,
            hour=15,
            season='fall',
            recent_avg_daily_revenue=4500.0,
            recent_avg_daily_orders=120.0,
            recent_trend='decreasing',
            weather_forecast={'avg_temperature': 15.0, 'good_weather_ratio': 0.6}
        )
        
        assert context.weather_forecast['avg_temperature'] == 15.0
    
    def test_context_with_holidays(self):
        """Test context with upcoming holidays."""
        context = RecommenderContext(
            current_date=datetime.now(),
            day_of_week=4,
            hour=10,
            season='winter',
            recent_avg_daily_revenue=6000.0,
            recent_avg_daily_orders=180.0,
            recent_trend='increasing',
            upcoming_holidays=[datetime(2026, 12, 25), datetime(2026, 12, 31)]
        )
        
        assert len(context.upcoming_holidays) == 2


# =============================================================================
# TEST CAMPAIGN RECOMMENDER
# =============================================================================

class TestCampaignRecommender:
    """Test CampaignRecommender class."""
    
    @pytest.fixture
    def recommender_with_data(self, analyzer, sample_orders_df, 
                               sample_campaigns, sample_order_items_df):
        """Create recommender with analyzed data."""
        sample_orders_df['item_count'] = 2
        
        analyzer.analyze_campaign_effectiveness(
            sample_orders_df,
            sample_campaigns,
            sample_order_items_df
        )
        analyzer.extract_item_affinity(sample_order_items_df)
        
        recommender = CampaignRecommender(analyzer, exploration_rate=0.2)
        return recommender
    
    def test_recommender_initialization(self, analyzer):
        """Test recommender initializes correctly."""
        recommender = CampaignRecommender(analyzer)
        
        assert recommender.analyzer == analyzer
        assert recommender.exploration_rate == 0.1
        assert recommender.reward_model is None
    
    def test_recommender_custom_exploration_rate(self, analyzer):
        """Test custom exploration rate."""
        recommender = CampaignRecommender(analyzer, exploration_rate=0.3)
        
        assert recommender.exploration_rate == 0.3
    
    def test_fit_with_minimal_data(self, recommender_with_data):
        """Test fitting with minimal campaign data."""
        # With only 2 campaigns, should print warning
        recommender_with_data.fit(use_xgboost=False)
        
        # Templates should be extracted
        assert isinstance(recommender_with_data.campaign_templates, list)
    
    def test_recommend_without_training(self, analyzer):
        """Test recommendations work without training."""
        recommender = CampaignRecommender(analyzer)
        
        context = RecommenderContext(
            current_date=datetime.now(),
            day_of_week=1,
            hour=14,
            season='winter',
            recent_avg_daily_revenue=5000.0,
            recent_avg_daily_orders=150.0,
            recent_trend='stable'
        )
        
        # Should return empty list if no templates
        recommendations = recommender.recommend_campaigns(context, num_recommendations=3)
        assert isinstance(recommendations, list)
    
    def test_thompson_sampling_initialization(self, recommender_with_data):
        """Test Thompson Sampling parameters are initialized."""
        recommender_with_data.fit(use_xgboost=False)
        
        # Thompson params should be initialized for templates
        for template_id, params in recommender_with_data.thompson_params.items():
            alpha, beta = params
            assert alpha >= 1  # Prior is Beta(1, 1)
            assert beta >= 1
    
    def test_update_from_feedback_success(self, recommender_with_data):
        """Test updating from successful campaign feedback."""
        recommender_with_data.fit(use_xgboost=False)
        
        # Get a template ID
        if recommender_with_data.campaign_templates:
            template_id = recommender_with_data.campaign_templates[0]['template_id']
            campaign_id = f"rec_{template_id}_{int(datetime.now().timestamp())}"
            
            # Get initial params
            initial_alpha, initial_beta = recommender_with_data.thompson_params.get(template_id, (1, 1))
            
            # Update with success
            recommender_with_data.update_from_feedback(campaign_id, actual_roi=100.0, success=True)
            
            # Alpha should increase
            new_alpha, new_beta = recommender_with_data.thompson_params.get(template_id, (1, 1))
            assert new_alpha >= initial_alpha
    
    def test_update_from_feedback_failure(self, recommender_with_data):
        """Test updating from failed campaign feedback."""
        recommender_with_data.fit(use_xgboost=False)
        
        if recommender_with_data.campaign_templates:
            template_id = recommender_with_data.campaign_templates[0]['template_id']
            campaign_id = f"rec_{template_id}_{int(datetime.now().timestamp())}"
            
            initial_alpha, initial_beta = recommender_with_data.thompson_params.get(template_id, (1, 1))
            
            # Update with failure
            recommender_with_data.update_from_feedback(campaign_id, actual_roi=-10.0, success=False)
            
            # Beta should increase
            new_alpha, new_beta = recommender_with_data.thompson_params.get(template_id, (1, 1))
            assert new_beta >= initial_beta


# =============================================================================
# TEST CAMPAIGN RECOMMENDATION OUTPUT
# =============================================================================

class TestCampaignRecommendation:
    """Test CampaignRecommendation dataclass."""
    
    def test_recommendation_creation(self):
        """Test creating a recommendation."""
        rec = CampaignRecommendation(
            campaign_id='rec_001',
            items=['burger', 'fries'],
            discount_percentage=15.0,
            start_date='2026-02-01',
            end_date='2026-02-07',
            duration_days=7,
            expected_uplift=25.0,
            expected_roi=85.0,
            expected_revenue=5000.0,
            confidence_score=0.8,
            recommended_for_context={'season': 'winter'},
            reasoning='Test recommendation',
            priority_score=75.0
        )
        
        assert rec.campaign_id == 'rec_001'
        assert rec.discount_percentage == 15.0
        assert rec.expected_roi == 85.0
    
    def test_recommendation_items(self):
        """Test recommendation items list."""
        rec = CampaignRecommendation(
            campaign_id='rec_002',
            items=['pizza', 'drink', 'dessert'],
            discount_percentage=20.0,
            start_date='2026-02-10',
            end_date='2026-02-17',
            duration_days=7,
            expected_uplift=30.0,
            expected_roi=90.0,
            expected_revenue=6000.0,
            confidence_score=0.7,
            recommended_for_context={'season': 'summer'},
            reasoning='Summer special',
            priority_score=80.0
        )
        
        assert len(rec.items) == 3
        assert 'pizza' in rec.items


# =============================================================================
# TEST MODEL PERSISTENCE
# =============================================================================

class TestModelPersistence:
    """Test model save and load functionality."""
    
    def test_save_model(self, analyzer, sample_orders_df, 
                        sample_campaigns, sample_order_items_df):
        """Test saving recommender model."""
        sample_orders_df['item_count'] = 2
        
        analyzer.analyze_campaign_effectiveness(
            sample_orders_df,
            sample_campaigns,
            sample_order_items_df
        )
        
        recommender = CampaignRecommender(analyzer)
        recommender.fit(use_xgboost=False)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, 'campaign_model.json')
            recommender.save_model(filepath)
            
            assert os.path.exists(filepath)
            
            # Verify JSON is valid
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            assert 'campaign_templates' in data
            assert 'thompson_params' in data
    
    def test_load_model(self, analyzer, sample_orders_df,
                        sample_campaigns, sample_order_items_df):
        """Test loading recommender model."""
        sample_orders_df['item_count'] = 2
        
        analyzer.analyze_campaign_effectiveness(
            sample_orders_df,
            sample_campaigns,
            sample_order_items_df
        )
        
        recommender = CampaignRecommender(analyzer)
        recommender.fit(use_xgboost=False)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, 'campaign_model.json')
            recommender.save_model(filepath)
            
            # Create new recommender and load
            new_recommender = CampaignRecommender(analyzer)
            new_recommender.load_model(filepath)
            
            # Verify data loaded
            assert len(new_recommender.campaign_templates) == len(recommender.campaign_templates)
            assert len(new_recommender.thompson_params) == len(recommender.thompson_params)


# =============================================================================
# TEST EDGE CASES
# =============================================================================

class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_orders_dataframe(self, analyzer, sample_campaigns, sample_order_items_df):
        """Test handling empty orders DataFrame."""
        empty_orders = pd.DataFrame(columns=['id', 'created', 'place_id', 'total_amount'])
        
        # Should not crash
        metrics = analyzer.analyze_campaign_effectiveness(
            empty_orders,
            sample_campaigns,
            sample_order_items_df
        )
        
        assert len(metrics) == 2  # Still creates metrics for campaigns
    
    def test_empty_campaigns_list(self, analyzer, sample_orders_df, sample_order_items_df):
        """Test handling empty campaigns list."""
        metrics = analyzer.analyze_campaign_effectiveness(
            sample_orders_df,
            [],
            sample_order_items_df
        )
        
        assert len(metrics) == 0
    
    def test_campaign_with_no_orders_during(self, analyzer, sample_order_items_df):
        """Test campaign with no orders during period."""
        # Create orders only before the campaign
        base_time = datetime(2026, 1, 1, 12, 0, 0)
        orders = []
        for i in range(10):
            order_time = base_time + timedelta(hours=i)
            orders.append({
                'id': f'order_{i}',
                'created': int(order_time.timestamp()),
                'place_id': 'place_001',
                'total_amount': 25.0
            })
        orders_df = pd.DataFrame(orders)
        
        # Campaign is after all orders
        campaigns = [{
            'id': 'late_campaign',
            'start_time': (base_time + timedelta(days=30)).isoformat(),
            'end_time': (base_time + timedelta(days=37)).isoformat(),
            'items_included': ['burger'],
            'discount': 10.0
        }]
        
        metrics = analyzer.analyze_campaign_effectiveness(
            orders_df,
            campaigns,
            sample_order_items_df
        )
        
        assert metrics[0].avg_daily_orders_during == 0.0
    
    def test_context_with_zero_orders(self):
        """Test context with zero recent orders."""
        context = RecommenderContext(
            current_date=datetime.now(),
            day_of_week=1,
            hour=14,
            season='winter',
            recent_avg_daily_revenue=0.0,
            recent_avg_daily_orders=0.0,
            recent_trend='stable'
        )
        
        assert context.recent_avg_daily_orders == 0.0
    
    def test_item_affinity_no_pairs(self, analyzer):
        """Test item affinity with single-item orders only."""
        # Each order has only one item
        order_items = pd.DataFrame({
            'order_id': [f'order_{i}' for i in range(10)],
            'item_id': ['burger'] * 10
        })
        
        affinity = analyzer.extract_item_affinity(order_items, min_support=0.01)
        
        # No pairs should be found
        assert len(affinity) == 0


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestIntegration:
    """End-to-end integration tests."""
    
    def test_full_workflow(self, sample_orders_df, sample_campaigns, sample_order_items_df):
        """Test complete workflow from analysis to recommendations."""
        sample_orders_df['item_count'] = 2
        
        # Step 1: Analyze campaigns
        analyzer = CampaignAnalyzer()
        analyzer.analyze_campaign_effectiveness(
            sample_orders_df,
            sample_campaigns,
            sample_order_items_df
        )
        analyzer.extract_item_affinity(sample_order_items_df)
        
        # Step 2: Train recommender
        recommender = CampaignRecommender(analyzer, exploration_rate=0.2)
        recommender.fit(use_xgboost=False)
        
        # Step 3: Get recommendations
        context = RecommenderContext(
            current_date=datetime.now(),
            day_of_week=1,
            hour=14,
            season='winter',
            recent_avg_daily_revenue=5000.0,
            recent_avg_daily_orders=150.0,
            recent_trend='stable',
            available_items=['burger', 'fries', 'pizza', 'drink']
        )
        
        recommendations = recommender.recommend_campaigns(context, num_recommendations=3)
        
        # Should get recommendations
        assert isinstance(recommendations, list)
    
    def test_multiple_analysis_runs(self, analyzer, sample_orders_df,
                                     sample_campaigns, sample_order_items_df):
        """Test running analysis multiple times."""
        # First run
        metrics1 = analyzer.analyze_campaign_effectiveness(
            sample_orders_df,
            sample_campaigns,
            sample_order_items_df
        )
        
        # Second run should replace metrics
        metrics2 = analyzer.analyze_campaign_effectiveness(
            sample_orders_df,
            sample_campaigns,
            sample_order_items_df
        )
        
        assert len(analyzer.campaign_metrics) == 2
