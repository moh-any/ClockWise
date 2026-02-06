"""
Campaign Performance Analysis Module
=====================================
Analyzes historical campaign effectiveness and extracts patterns.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class CampaignMetrics:
    """Metrics for a historical campaign"""
    campaign_id: str
    start_date: datetime
    end_date: datetime
    items_included: List[str]
    discount: float
    
    # Performance metrics
    avg_daily_orders_during: float
    avg_daily_orders_before: float
    avg_daily_orders_after: float
    uplift_percentage: float
    
    # Item-level metrics
    item_uplift: Dict[str, float]
    total_revenue_during: float
    total_revenue_before: float
    revenue_impact: float
    
    # Contextual features
    day_of_week_start: int
    hour_of_day_start: int
    season: str
    weather_during: Dict[str, float]
    was_holiday: bool
    
    # Profitability
    gross_margin: float
    roi: float


class CampaignAnalyzer:
    """Analyze historical campaign performance and extract patterns"""
    
    def __init__(self):
        self.campaign_metrics: List[CampaignMetrics] = []
        self.item_affinity: Dict[Tuple[str, str], float] = {}
        self.temporal_patterns: Dict[str, Dict] = {}
    
    def analyze_campaign_effectiveness(
        self,
        orders_df: pd.DataFrame,
        campaign_data: List[Dict],
        order_items_df: pd.DataFrame
    ) -> List[CampaignMetrics]:
        """
        Analyze effectiveness of historical campaigns.
        
        Args:
            orders_df: Historical orders with timestamps
            campaign_data: List of campaign definitions
            order_items_df: Order-item relationships
            
        Returns:
            List of campaign metrics
        """
        metrics_list = []
        
        for campaign in campaign_data:
            metrics = self._calculate_campaign_metrics(
                orders_df, campaign, order_items_df
            )
            metrics_list.append(metrics)
        
        self.campaign_metrics = metrics_list
        return metrics_list
    
    def _calculate_campaign_metrics(
        self,
        orders_df: pd.DataFrame,
        campaign: Dict,
        order_items_df: pd.DataFrame
    ) -> CampaignMetrics:
        """Calculate detailed metrics for a single campaign"""
        
        start_dt = pd.to_datetime(campaign['start_time'])
        end_dt = pd.to_datetime(campaign['end_time'])
        
        # Define time windows
        duration = (end_dt - start_dt).days
        before_start = start_dt - timedelta(days=duration)
        after_end = end_dt + timedelta(days=duration)
        
        # Filter orders by time periods
        orders_df['timestamp'] = pd.to_datetime(orders_df['created'], unit='s')
        
        before_orders = orders_df[
            (orders_df['timestamp'] >= before_start) & 
            (orders_df['timestamp'] < start_dt)
        ]
        during_orders = orders_df[
            (orders_df['timestamp'] >= start_dt) & 
            (orders_df['timestamp'] <= end_dt)
        ]
        after_orders = orders_df[
            (orders_df['timestamp'] > end_dt) & 
            (orders_df['timestamp'] <= after_end)
        ]
        
        # Calculate base metrics
        avg_orders_before = len(before_orders) / max(duration, 1)
        avg_orders_during = len(during_orders) / max(duration, 1)
        avg_orders_after = len(after_orders) / max(duration, 1)
        
        uplift = ((avg_orders_during - avg_orders_before) / max(avg_orders_before, 1)) * 100
        
        # Item-level analysis
        item_uplift = self._calculate_item_uplift(
            before_orders, during_orders, after_orders,
            order_items_df, campaign['items_included']
        )
        
        # Revenue analysis
        revenue_before = before_orders['total_amount'].sum()
        revenue_during = during_orders['total_amount'].sum()
        revenue_after = after_orders['total_amount'].sum()
        
        revenue_impact = revenue_during - revenue_before
        
        # Contextual features
        day_of_week = start_dt.dayofweek
        hour_of_day = start_dt.hour
        season = self._get_season(start_dt)
        
        # Weather during campaign (if available)
        weather_during = self._extract_weather_features(during_orders)
        
        # Holiday check
        was_holiday = self._check_holiday_overlap(start_dt, end_dt)
        
        # Profitability (simplified - assumes 30% margin before discount)
        base_margin = 0.30
        discount_rate = campaign['discount'] / 100
        effective_margin = base_margin - discount_rate
        gross_margin = revenue_during * effective_margin
        
        # ROI (assumes campaign cost is 5% of revenue)
        campaign_cost = revenue_during * 0.05
        roi = (gross_margin - campaign_cost) / max(campaign_cost, 1) * 100
        
        return CampaignMetrics(
            campaign_id=campaign.get('id', f"campaign_{start_dt.timestamp()}"),
            start_date=start_dt,
            end_date=end_dt,
            items_included=campaign['items_included'],
            discount=campaign['discount'],
            avg_daily_orders_during=avg_orders_during,
            avg_daily_orders_before=avg_orders_before,
            avg_daily_orders_after=avg_orders_after,
            uplift_percentage=uplift,
            item_uplift=item_uplift,
            total_revenue_during=revenue_during,
            total_revenue_before=revenue_before,
            revenue_impact=revenue_impact,
            day_of_week_start=day_of_week,
            hour_of_day_start=hour_of_day,
            season=season,
            weather_during=weather_during,
            was_holiday=was_holiday,
            gross_margin=gross_margin,
            roi=roi
        )
    
    def _calculate_item_uplift(
        self,
        before_orders: pd.DataFrame,
        during_orders: pd.DataFrame,
        after_orders: pd.DataFrame,
        order_items_df: pd.DataFrame,
        campaign_items: List[str]
    ) -> Dict[str, float]:
        """Calculate uplift for each item in campaign"""
        
        item_uplift = {}
        
        for item in campaign_items:
            # Count items in each period
            before_count = self._count_item_in_orders(before_orders, order_items_df, item)
            during_count = self._count_item_in_orders(during_orders, order_items_df, item)
            after_count = self._count_item_in_orders(after_orders, order_items_df, item)
            
            # Calculate uplift
            if before_count > 0:
                uplift = ((during_count - before_count) / before_count) * 100
            else:
                uplift = 100.0 if during_count > 0 else 0.0
            
            item_uplift[item] = uplift
        
        return item_uplift
    
    def _count_item_in_orders(
        self,
        orders: pd.DataFrame,
        order_items_df: pd.DataFrame,
        item_id: str
    ) -> int:
        """Count occurrences of an item in given orders"""
        
        if orders.empty:
            return 0
        
        order_ids = orders['id'].values
        item_orders = order_items_df[
            (order_items_df['order_id'].isin(order_ids)) &
            (order_items_df['item_id'] == item_id)
        ]
        
        return len(item_orders)
    
    def _get_season(self, dt: datetime) -> str:
        """Determine season from date"""
        month = dt.month
        
        if month in [12, 1, 2]:
            return "winter"
        elif month in [3, 4, 5]:
            return "spring"
        elif month in [6, 7, 8]:
            return "summer"
        else:
            return "fall"
    
    def _extract_weather_features(self, orders: pd.DataFrame) -> Dict[str, float]:
        """Extract average weather features during campaign"""
        
        weather_features = {
            'avg_temperature': 15.0,
            'avg_precipitation': 0.0,
            'good_weather_ratio': 0.7
        }
        
        if 'temperature_2m' in orders.columns:
            weather_features['avg_temperature'] = orders['temperature_2m'].mean()
        
        if 'precipitation' in orders.columns:
            weather_features['avg_precipitation'] = orders['precipitation'].mean()
        
        if 'good_weather' in orders.columns:
            weather_features['good_weather_ratio'] = orders['good_weather'].mean()
        
        return weather_features
    
    def _check_holiday_overlap(self, start_dt: datetime, end_dt: datetime) -> bool:
        """Check if campaign overlaps with holidays"""
        # Simplified - would integrate with holiday API
        # For now, check common holiday periods
        
        holiday_periods = [
            (12, 20, 12, 31),  # Christmas/New Year
            (7, 1, 7, 7),      # July 4th week
            (11, 20, 11, 30),  # Thanksgiving
        ]
        
        for h_start_m, h_start_d, h_end_m, h_end_d in holiday_periods:
            if (start_dt.month == h_start_m and start_dt.day >= h_start_d) or \
               (end_dt.month == h_end_m and end_dt.day <= h_end_d):
                return True
        
        return False
    
    def extract_item_affinity(
        self,
        order_items_df: pd.DataFrame,
        min_support: float = 0.01
    ) -> Dict[Tuple[str, str], float]:
        """
        Extract item-item affinity (items frequently bought together).
        Uses association rule mining.
        
        Args:
            order_items_df: Order-item relationships
            min_support: Minimum support threshold
            
        Returns:
            Dictionary of (item1, item2) -> affinity score
        """
        
        # Group items by order
        order_baskets = order_items_df.groupby('order_id')['item_id'].apply(list).values
        
        # Count item co-occurrences
        item_pairs = defaultdict(int)
        item_counts = defaultdict(int)
        total_orders = len(order_baskets)
        
        for basket in order_baskets:
            unique_items = list(set(basket))
            
            # Count individual items
            for item in unique_items:
                item_counts[item] += 1
            
            # Count pairs
            for i, item1 in enumerate(unique_items):
                for item2 in unique_items[i+1:]:
                    pair = tuple(sorted([item1, item2]))
                    item_pairs[pair] += 1
        
        # Calculate lift (affinity metric)
        affinity = {}
        
        for (item1, item2), pair_count in item_pairs.items():
            support = pair_count / total_orders
            
            if support >= min_support:
                # Lift = P(A and B) / (P(A) * P(B))
                prob_a = item_counts[item1] / total_orders
                prob_b = item_counts[item2] / total_orders
                prob_ab = pair_count / total_orders
                
                lift = prob_ab / (prob_a * prob_b)
                affinity[(item1, item2)] = lift
        
        self.item_affinity = affinity
        return affinity
    
    def extract_temporal_patterns(
        self,
        orders_df: pd.DataFrame
    ) -> Dict[str, Dict]:
        """
        Extract temporal patterns in demand.
        
        Returns:
            Dictionary with patterns by day_of_week, hour, season
        """
        
        orders_df['timestamp'] = pd.to_datetime(orders_df['created'], unit='s')
        orders_df['day_of_week'] = orders_df['timestamp'].dt.dayofweek
        orders_df['hour'] = orders_df['timestamp'].dt.hour
        orders_df['season'] = orders_df['timestamp'].apply(
            lambda x: self._get_season(x)
        )
        
        patterns = {
            'by_day_of_week': {},
            'by_hour': {},
            'by_season': {}
        }
        
        # Aggregate by day of week
        for dow in range(7):
            dow_orders = orders_df[orders_df['day_of_week'] == dow]
            patterns['by_day_of_week'][dow] = {
                'avg_orders': len(dow_orders) / max(len(orders_df['timestamp'].dt.date.unique()), 1),
                'avg_revenue': dow_orders['total_amount'].mean() if not dow_orders.empty else 0,
                'avg_items': dow_orders['item_count'].mean() if not dow_orders.empty else 0
            }
        
        # Aggregate by hour
        for hour in range(24):
            hour_orders = orders_df[orders_df['hour'] == hour]
            patterns['by_hour'][hour] = {
                'avg_orders': len(hour_orders) / max(len(orders_df['timestamp'].dt.date.unique()), 1),
                'avg_revenue': hour_orders['total_amount'].mean() if not hour_orders.empty else 0
            }
        
        # Aggregate by season
        for season in ['winter', 'spring', 'summer', 'fall']:
            season_orders = orders_df[orders_df['season'] == season]
            patterns['by_season'][season] = {
                'avg_daily_orders': len(season_orders) / max(len(season_orders['timestamp'].dt.date.unique()), 1) if not season_orders.empty else 0,
                'avg_revenue': season_orders['total_amount'].mean() if not season_orders.empty else 0
            }
        
        self.temporal_patterns = patterns
        return patterns
    
    def get_best_performing_campaigns(
        self,
        top_n: int = 5,
        metric: str = 'roi'
    ) -> List[CampaignMetrics]:
        """
        Get top performing campaigns by specified metric.
        
        Args:
            top_n: Number of top campaigns to return
            metric: Metric to sort by (roi, uplift_percentage, revenue_impact)
            
        Returns:
            List of top campaign metrics
        """
        
        if not self.campaign_metrics:
            return []
        
        sorted_campaigns = sorted(
            self.campaign_metrics,
            key=lambda x: getattr(x, metric),
            reverse=True
        )
        
        return sorted_campaigns[:top_n]
    
    def get_summary_statistics(self) -> Dict:
        """Get summary statistics of all analyzed campaigns"""
        
        if not self.campaign_metrics:
            return {}
        
        uplifts = [c.uplift_percentage for c in self.campaign_metrics]
        rois = [c.roi for c in self.campaign_metrics]
        revenues = [c.total_revenue_during for c in self.campaign_metrics]
        
        return {
            'total_campaigns_analyzed': len(self.campaign_metrics),
            'avg_uplift': np.mean(uplifts),
            'median_uplift': np.median(uplifts),
            'avg_roi': np.mean(rois),
            'median_roi': np.median(rois),
            'total_revenue_impact': sum([c.revenue_impact for c in self.campaign_metrics]),
            'successful_campaigns': len([c for c in self.campaign_metrics if c.roi > 0]),
            'success_rate': len([c for c in self.campaign_metrics if c.roi > 0]) / len(self.campaign_metrics) * 100
        }