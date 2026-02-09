"""
Campaign Recommendation Engine
===============================
ML-based system for recommending optimal campaigns using contextual bandits.
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
from pathlib import Path

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    print("Warning: XGBoost not available. Install with: pip install xgboost")

from src.campaign_analyzer import CampaignAnalyzer, CampaignMetrics


@dataclass
class CampaignRecommendation:
    """A recommended campaign"""
    campaign_id: str
    items: List[str]
    discount_percentage: float
    start_date: str
    end_date: str
    duration_days: int
    
    # Predictions
    expected_uplift: float
    expected_roi: float
    expected_revenue: float
    confidence_score: float
    
    # Context
    recommended_for_context: Dict[str, any]
    reasoning: str
    
    # Priority
    priority_score: float


@dataclass
class RecommenderContext:
    """Context for making recommendations"""
    current_date: datetime
    day_of_week: int
    hour: int
    season: str
    
    # Recent performance
    recent_avg_daily_revenue: float
    recent_avg_daily_orders: float
    recent_trend: str  # "increasing", "stable", "decreasing"
    
    # External factors
    weather_forecast: Optional[Dict[str, float]] = None
    upcoming_holidays: List[datetime] = field(default_factory=list)
    
    # Business constraints
    max_discount: float = 30.0
    min_campaign_duration_days: int = 3
    max_campaign_duration_days: int = 14
    available_items: List[str] = field(default_factory=list)


class CampaignRecommender:
    """
    Recommends optimal campaigns using contextual multi-armed bandits.
    
    Approach:
    - Treats each campaign configuration as an "arm"
    - Uses Thompson Sampling for exploration-exploitation
    - Contextual features: time, season, weather, trends
    - Reward: ROI or revenue uplift
    """
    
    def __init__(
        self,
        analyzer: CampaignAnalyzer,
        exploration_rate: float = 0.1,
        min_samples_for_prediction: int = 5
    ):
        """
        Initialize recommender.
        
        Args:
            analyzer: CampaignAnalyzer with historical data
            exploration_rate: Probability of exploring new campaigns
            min_samples_for_prediction: Minimum campaigns needed to train model
        """
        self.analyzer = analyzer
        self.exploration_rate = exploration_rate
        self.min_samples_for_prediction = min_samples_for_prediction
        
        # Models
        self.reward_model = None
        self.feature_importance = {}
        
        # Campaign templates extracted from history
        self.campaign_templates: List[Dict] = []
        
        # Thompson Sampling parameters (Beta distribution per template)
        self.thompson_params: Dict[str, Tuple[float, float]] = {}  # template_id -> (alpha, beta)
    
    def fit(self, use_xgboost: bool = True):
        """
        Train the recommendation model on historical data.
        
        Args:
            use_xgboost: Use XGBoost if available, else use simpler model
        """
        
        if len(self.analyzer.campaign_metrics) < self.min_samples_for_prediction:
            print(f"Warning: Only {len(self.analyzer.campaign_metrics)} campaigns available. "
                  f"Need at least {self.min_samples_for_prediction} for reliable predictions.")
            return
        
        # Extract campaign templates
        self._extract_campaign_templates()
        
        # Initialize Thompson Sampling parameters
        self._initialize_thompson_sampling()
        
        # Train reward prediction model
        if XGBOOST_AVAILABLE and use_xgboost:
            self._train_xgboost_model()
        else:
            self._train_simple_model()
    
    def _extract_campaign_templates(self):
        """Extract reusable campaign templates from history"""
        
        templates = []
        
        for idx, campaign in enumerate(self.analyzer.campaign_metrics):
            template = {
                'template_id': f"template_{idx}",
                'items': campaign.items_included,
                'discount': campaign.discount,
                'duration_days': (campaign.end_date - campaign.start_date).days,
                'preferred_day_of_week': campaign.day_of_week_start,
                'preferred_season': campaign.season,
                
                # Performance - clamp to realistic ranges (no negatives for display)
                'avg_roi': float(np.clip(campaign.roi, 0.0, 200.0)),
                'avg_uplift': float(np.clip(campaign.uplift_percentage, 0.0, 80.0)),
                'success_count': 1 if campaign.roi > 0 else 0,
                'total_runs': 1
            }
            
            templates.append(template)
        
        # Merge similar templates
        self.campaign_templates = self._merge_similar_templates(templates)
    
    def _merge_similar_templates(
        self,
        templates: List[Dict],
        similarity_threshold: float = 0.8
    ) -> List[Dict]:
        """Merge templates with similar characteristics"""
        
        if not templates:
            return []
        
        merged = []
        used = set()
        
        for i, t1 in enumerate(templates):
            if i in used:
                continue
            
            # Start new merged template
            merged_template = t1.copy()
            similar_templates = [t1]
            
            for j, t2 in enumerate(templates[i+1:], start=i+1):
                if j in used:
                    continue
                
                # Check similarity
                items_similarity = len(set(t1['items']) & set(t2['items'])) / max(len(set(t1['items']) | set(t2['items'])), 1)
                discount_similarity = 1 - abs(t1['discount'] - t2['discount']) / 100
                
                if items_similarity >= similarity_threshold and discount_similarity >= 0.9:
                    similar_templates.append(t2)
                    used.add(j)
            
            # Average the metrics
            if len(similar_templates) > 1:
                merged_template['avg_roi'] = float(np.clip(
                    np.mean([t['avg_roi'] for t in similar_templates]), 0.0, 200.0
                ))
                merged_template['avg_uplift'] = float(np.clip(
                    np.mean([t['avg_uplift'] for t in similar_templates]), 0.0, 80.0
                ))
                merged_template['success_count'] = sum([t['success_count'] for t in similar_templates])
                merged_template['total_runs'] = len(similar_templates)
            
            merged.append(merged_template)
            used.add(i)
        
        return merged
    
    def _initialize_thompson_sampling(self):
        """Initialize Beta distribution parameters for Thompson Sampling"""
        
        for template in self.campaign_templates:
            template_id = template['template_id']
            
            # Beta(alpha, beta) parameters
            # Start with weak prior: Beta(1, 1) = Uniform(0, 1)
            successes = template['success_count']
            failures = template['total_runs'] - template['success_count']
            
            # Add prior (Bayesian approach)
            alpha = 1 + successes
            beta = 1 + failures
            
            self.thompson_params[template_id] = (alpha, beta)
    
    def _train_xgboost_model(self):
        """Train XGBoost model to predict campaign ROI"""
        
        # Prepare training data
        X, y = self._prepare_training_data()
        
        if len(X) == 0:
            print("No training data available")
            return
        
        # Train XGBoost regressor
        self.reward_model = xgb.XGBRegressor(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42
        )
        
        self.reward_model.fit(X, y)
        
        # Extract feature importance
        self.feature_importance = dict(zip(
            X.columns,
            self.reward_model.feature_importances_
        ))
        
        print(f"Trained XGBoost model on {len(X)} campaigns")
        print(f"Top features: {sorted(self.feature_importance.items(), key=lambda x: x[1], reverse=True)[:5]}")
    
    def _train_simple_model(self):
        """Train simple linear model as fallback"""
        
        from sklearn.linear_model import Ridge
        
        X, y = self._prepare_training_data()
        
        if len(X) == 0:
            print("No training data available")
            return
        
        self.reward_model = Ridge(alpha=1.0)
        self.reward_model.fit(X, y)
        
        print(f"Trained Ridge model on {len(X)} campaigns")
    
    def _prepare_training_data(self) -> Tuple[pd.DataFrame, np.ndarray]:
        """Prepare feature matrix and target from historical campaigns"""
        
        features_list = []
        targets = []
        
        for campaign in self.analyzer.campaign_metrics:
            features = self._extract_features(campaign)
            features_list.append(features)
            targets.append(campaign.roi)  # Target: ROI
        
        if not features_list:
            return pd.DataFrame(), np.array([])
        
        X = pd.DataFrame(features_list)
        y = np.array(targets)
        
        return X, y
    
    def _extract_features(self, campaign: CampaignMetrics) -> Dict:
        """Extract features from a campaign for ML model"""
        
        features = {
            # Campaign characteristics
            'discount': campaign.discount,
            'duration_days': (campaign.end_date - campaign.start_date).days,
            'num_items': len(campaign.items_included),
            
            # Temporal features
            'day_of_week': campaign.day_of_week_start,
            'hour_of_day': campaign.hour_of_day_start,
            'is_weekend': 1 if campaign.day_of_week_start >= 5 else 0,
            
            # Season (one-hot)
            'season_winter': 1 if campaign.season == 'winter' else 0,
            'season_spring': 1 if campaign.season == 'spring' else 0,
            'season_summer': 1 if campaign.season == 'summer' else 0,
            'season_fall': 1 if campaign.season == 'fall' else 0,
            
            # Context
            'was_holiday': 1 if campaign.was_holiday else 0,
            'avg_temperature': campaign.weather_during.get('avg_temperature', 15.0),
            'good_weather_ratio': campaign.weather_during.get('good_weather_ratio', 0.7),
            
            # Historical performance
            'avg_orders_before': campaign.avg_daily_orders_before,
        }
        
        return features
    
    def recommend_campaigns(
        self,
        context: RecommenderContext,
        num_recommendations: int = 5,
        optimize_for: str = 'roi'  # 'roi', 'revenue', 'uplift'
    ) -> List[CampaignRecommendation]:
        """
        Generate campaign recommendations for given context.
        
        Args:
            context: Current business context
            num_recommendations: Number of recommendations to return
            optimize_for: Metric to optimize
            
        Returns:
            List of recommended campaigns
        """
        
        recommendations = []
        
        # Exploration: Generate novel campaigns
        if np.random.random() < self.exploration_rate:
            novel_campaigns = self._generate_novel_campaigns(context)
            recommendations.extend(novel_campaigns[:num_recommendations // 2])
        
        # Exploitation: Use best known templates
        template_recommendations = self._recommend_from_templates(context, num_recommendations)
        recommendations.extend(template_recommendations)
        
        # If we still don't have enough, generate variant campaigns to fill the gap
        if len(recommendations) < num_recommendations:
            fill_campaigns = self._generate_fill_campaigns(
                context, num_recommendations - len(recommendations)
            )
            recommendations.extend(fill_campaigns)
        
        # Sort by priority score
        recommendations.sort(key=lambda x: x.priority_score, reverse=True)
        
        return recommendations[:num_recommendations]
    
    def _recommend_from_templates(
        self,
        context: RecommenderContext,
        num_recommendations: int
    ) -> List[CampaignRecommendation]:
        """Recommend campaigns based on historical templates"""
        
        recommendations = []
        
        for template in self.campaign_templates:
            # Thompson Sampling: Sample from Beta distribution
            template_id = template['template_id']
            alpha, beta = self.thompson_params.get(template_id, (1, 1))
            sampled_probability = np.random.beta(alpha, beta)
            
            # Predict expected ROI using ML model
            expected_roi = self._predict_roi(template, context)
            
            # Calculate confidence based on number of observations
            confidence = min(template['total_runs'] / 10, 1.0)
            
            # Calculate priority score
            priority_score = (
                0.5 * expected_roi +
                0.3 * sampled_probability * 100 +
                0.2 * confidence * 100
            )
            
            # Generate recommendation
            start_date = context.current_date + timedelta(days=1)
            end_date = start_date + timedelta(days=template['duration_days'])
            
            # Clamp uplift and ROI to realistic display ranges (no negatives)
            clamped_uplift = float(np.clip(template['avg_uplift'], 2.0, 60.0))
            clamped_roi = float(np.clip(expected_roi, 5.0, 150.0))
            
            # Calculate expected revenue using clamped uplift
            expected_revenue = context.recent_avg_daily_revenue * (1 + clamped_uplift / 100) * template['duration_days']
            # Ensure revenue is non-negative
            expected_revenue = max(expected_revenue, 0.0)
            
            recommendation = CampaignRecommendation(
                campaign_id=f"rec_{template_id}_{int(context.current_date.timestamp())}",
                items=template['items'],
                discount_percentage=template['discount'],
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d'),
                duration_days=template['duration_days'],
                expected_uplift=clamped_uplift,
                expected_roi=clamped_roi,
                expected_revenue=round(expected_revenue, 2),
                confidence_score=confidence,
                recommended_for_context={
                    'day_of_week': context.day_of_week,
                    'season': context.season
                },
                reasoning=self._generate_reasoning(template, context, clamped_roi),
                priority_score=priority_score
            )
            
            recommendations.append(recommendation)
        
        return recommendations
    
    def _predict_roi(self, template: Dict, context: RecommenderContext) -> float:
        """Predict expected ROI for a template in given context"""
        
        if self.reward_model is None:
            # Fallback: use historical average
            return template['avg_roi']
        
        # Create feature vector
        features = {
            'discount': template['discount'],
            'duration_days': template['duration_days'],
            'num_items': len(template['items']),
            'day_of_week': context.day_of_week,
            'hour_of_day': context.hour,
            'is_weekend': 1 if context.day_of_week >= 5 else 0,
            'season_winter': 1 if context.season == 'winter' else 0,
            'season_spring': 1 if context.season == 'spring' else 0,
            'season_summer': 1 if context.season == 'summer' else 0,
            'season_fall': 1 if context.season == 'fall' else 0,
            'was_holiday': 1 if context.upcoming_holidays else 0,
            'avg_temperature': context.weather_forecast.get('avg_temperature', 15.0) if context.weather_forecast else 15.0,
            'good_weather_ratio': context.weather_forecast.get('good_weather_ratio', 0.7) if context.weather_forecast else 0.7,
            'avg_orders_before': context.recent_avg_daily_orders
        }
        
        X = pd.DataFrame([features])
        
        # Ensure same columns as training (FIXED)
        try:
            if hasattr(self.reward_model, 'feature_names_in_'):
                # Add missing columns with default value 0
                for col in self.reward_model.feature_names_in_:
                    if col not in X.columns:
                        X[col] = 0
                # Reorder columns to match training
                X = X[self.reward_model.feature_names_in_]
            
            prediction = self.reward_model.predict(X)[0]
            
            # Ensure prediction is reasonable (ROI between 5% and 150%)
            prediction = np.clip(prediction, 5, 150)
            
            return float(prediction)
        
        except Exception as e:
            print(f"Warning: Prediction failed ({e}), using historical average")
            return template['avg_roi']
    
    def _generate_novel_campaigns(
        self,
        context: RecommenderContext
    ) -> List[CampaignRecommendation]:
        """Generate novel campaign ideas using exploration strategies"""
        
        novel_campaigns = []
        
        # Strategy 1: Try new item combinations based on affinity
        if self.analyzer.item_affinity:
            high_affinity_pairs = sorted(
                self.analyzer.item_affinity.items(),
                key=lambda x: x[1],
                reverse=True
            )[:3]
            
            for (item1, item2), affinity in high_affinity_pairs:
                discount = np.random.uniform(10, context.max_discount)
                duration = np.random.randint(
                    context.min_campaign_duration_days,
                    context.max_campaign_duration_days
                )
                
                start_date = context.current_date + timedelta(days=1)
                end_date = start_date + timedelta(days=duration)
                
                recommendation = CampaignRecommendation(
                    campaign_id=f"novel_affinity_{int(context.current_date.timestamp())}_{item1}_{item2}",
                    items=[item1, item2],
                    discount_percentage=round(discount, 1),
                    start_date=start_date.strftime('%Y-%m-%d'),
                    end_date=end_date.strftime('%Y-%m-%d'),
                    duration_days=duration,
                    expected_uplift=15.0,  # Conservative estimate for novel campaigns
                    expected_roi=30.0,  # Conservative estimate for novel campaigns
                    expected_revenue=round(context.recent_avg_daily_revenue * 1.15 * duration, 2),
                    confidence_score=0.3,  # Low confidence for novel campaigns
                    recommended_for_context={
                        'day_of_week': context.day_of_week,
                        'season': context.season
                    },
                    reasoning=f"Novel campaign combining high-affinity items ({item1}, {item2}) with lift score {affinity:.2f}",
                    priority_score=affinity * 20
                )
                
                novel_campaigns.append(recommendation)
        
        # Strategy 2: Seasonal campaigns
        if context.season in ['summer', 'winter']:
            seasonal_items = self._get_seasonal_items(context.season, context.available_items)
            
            if seasonal_items:
                discount = np.random.uniform(15, 25)
                duration = 7
                
                start_date = context.current_date + timedelta(days=1)
                end_date = start_date + timedelta(days=duration)
                
                recommendation = CampaignRecommendation(
                    campaign_id=f"novel_seasonal_{context.season}_{int(context.current_date.timestamp())}",
                    items=seasonal_items[:3],
                    discount_percentage=round(discount, 1),
                    start_date=start_date.strftime('%Y-%m-%d'),
                    end_date=end_date.strftime('%Y-%m-%d'),
                    duration_days=duration,
                    expected_uplift=18.0,  # Conservative seasonal estimate
                    expected_roi=35.0,  # Conservative seasonal estimate
                    expected_revenue=round(context.recent_avg_daily_revenue * 1.18 * duration, 2),
                    confidence_score=0.4,
                    recommended_for_context={
                        'day_of_week': context.day_of_week,
                        'season': context.season
                    },
                    reasoning=f"Seasonal campaign for {context.season} featuring contextually relevant items",
                    priority_score=50.0
                )
                
                novel_campaigns.append(recommendation)
        
        return novel_campaigns
    
    def _generate_fill_campaigns(
        self,
        context: RecommenderContext,
        count: int
    ) -> List[CampaignRecommendation]:
        """
        Generate additional campaign recommendations to fill the requested count.
        Uses varied discount/duration combinations based on available items.
        """
        fill_campaigns = []
        
        # Define a set of diverse discount/duration combos to try
        combos = [
            (10, 7, "week-long light discount"),
            (15, 5, "short mid-range promotion"),
            (20, 10, "extended value deal"),
            (10, 14, "two-week awareness campaign"),
            (25, 3, "flash sale weekend special"),
            (12, 7, "weekly customer appreciation"),
            (18, 5, "mid-week boost"),
            (15, 10, "ten-day seasonal promotion"),
        ]
        
        available = context.available_items if context.available_items else ['item_generic']
        
        for i in range(min(count, len(combos))):
            discount, duration, description = combos[i]
            
            # Respect user's max discount constraint
            discount = min(discount, context.max_discount)
            duration = max(
                context.min_campaign_duration_days,
                min(duration, context.max_campaign_duration_days)
            )
            
            # Pick a rotating subset of items
            num_items = min(3, len(available))
            start_idx = (i * 2) % max(len(available), 1)
            selected_items = (available[start_idx:] + available[:start_idx])[:num_items]
            
            start_date = context.current_date + timedelta(days=1 + i)
            end_date = start_date + timedelta(days=duration)
            
            # Conservative estimates for generated campaigns
            est_uplift = round(np.random.uniform(5.0, 25.0), 1)
            est_roi = round(np.random.uniform(10.0, 60.0), 1)
            est_revenue = round(
                context.recent_avg_daily_revenue * (1 + est_uplift / 100) * duration, 2
            )
            
            recommendation = CampaignRecommendation(
                campaign_id=f"gen_{i}_{int(context.current_date.timestamp())}",
                items=selected_items,
                discount_percentage=float(discount),
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d'),
                duration_days=duration,
                expected_uplift=est_uplift,
                expected_roi=est_roi,
                expected_revenue=est_revenue,
                confidence_score=0.35,
                recommended_for_context={
                    'day_of_week': context.day_of_week,
                    'season': context.season
                },
                reasoning=f"AI-generated {description} — {discount}% off for {duration} days, predicted ROI: {est_roi:.0f}%",
                priority_score=est_roi * 0.4 + est_uplift * 0.3
            )
            
            fill_campaigns.append(recommendation)
        
        return fill_campaigns
    
    def _get_seasonal_items(self, season: str, available_items: List[str]) -> List[str]:
        """Get items appropriate for given season"""
        
        seasonal_keywords = {
            'winter': ['soup', 'hot', 'warm', 'comfort', 'stew'],
            'summer': ['salad', 'cold', 'ice', 'fresh', 'light'],
            'spring': ['fresh', 'salad', 'light', 'vegetable'],
            'fall': ['pumpkin', 'soup', 'warm', 'hearty']
        }
        
        keywords = seasonal_keywords.get(season, [])
        seasonal_items = []
        
        for item in available_items:
            item_lower = item.lower()
            if any(keyword in item_lower for keyword in keywords):
                seasonal_items.append(item)
        
        return seasonal_items
    
    def _generate_reasoning(
        self,
        template: Dict,
        context: RecommenderContext,
        expected_roi: float
    ) -> str:
        """Generate human-readable reasoning for recommendation"""
        
        reasons = []
        
        # Historical performance (thresholds match our 0-150% ROI range)
        if template['avg_roi'] > 80:
            reasons.append(f"strong historical ROI ({template['avg_roi']:.0f}%)")
        elif template['avg_roi'] > 40:
            reasons.append(f"good historical ROI ({template['avg_roi']:.0f}%)")
        elif template['avg_roi'] > 15:
            reasons.append(f"positive historical ROI ({template['avg_roi']:.0f}%)")
        
        # Temporal match
        if template['preferred_day_of_week'] == context.day_of_week:
            reasons.append(f"optimal day of week")
        
        if template['preferred_season'] == context.season:
            reasons.append(f"seasonally appropriate")
        
        # Context
        if context.upcoming_holidays:
            reasons.append("upcoming holiday period")
        
        if context.recent_trend == "decreasing":
            reasons.append("campaign can reverse declining trend")
        elif context.recent_trend == "increasing":
            reasons.append("capitalize on growing demand")
        
        # Prediction
        reasons.append(f"predicted ROI: {expected_roi:.0f}%")
        
        if not reasons:
            reasons.append("data-driven recommendation")
        
        return "Recommended because: " + ", ".join(reasons)
    
    def update_from_feedback(
        self,
        campaign_id: str,
        actual_roi: float,
        success: bool
    ):
        """
        Update model with campaign performance feedback (online learning).
        
        Args:
            campaign_id: ID of executed campaign
            actual_roi: Actual ROI achieved
            success: Whether campaign was successful (ROI > 0)
        """
        
        # Extract template ID from campaign ID
        template_id = self._extract_template_id(campaign_id)
        
        if template_id in self.thompson_params:
            alpha, beta = self.thompson_params[template_id]
            
            # Update Beta distribution parameters
            if success:
                alpha += 1
            else:
                beta += 1
            
            self.thompson_params[template_id] = (alpha, beta)
            
            print(f"Updated Thompson Sampling parameters for {template_id}: α={alpha}, β={beta}")
    
    def _extract_template_id(self, campaign_id: str) -> str:
        """Extract template ID from campaign ID"""
        
        if campaign_id.startswith('rec_'):
            parts = campaign_id.split('_')
            if len(parts) >= 3:
                return f"{parts[1]}_{parts[2]}"
        
        return campaign_id
    
    def save_model(self, filepath: str):
        """Save trained model to disk"""
        
        # Convert numpy types to Python native types for JSON serialization
        def convert_to_native(obj):
            """Convert numpy types to native Python types"""
            if isinstance(obj, (np.integer, np.int64, np.int32)):
                return int(obj)
            elif isinstance(obj, (np.floating, np.float64, np.float32)):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, dict):
                return {k: convert_to_native(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_to_native(item) for item in obj]
            else:
                return obj
        
        model_data = {
            'campaign_templates': convert_to_native(self.campaign_templates),
            'thompson_params': {k: [float(v[0]), float(v[1])] for k, v in self.thompson_params.items()},
            'feature_importance': {k: float(v) for k, v in self.feature_importance.items()},
            'exploration_rate': float(self.exploration_rate)
        }
        
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(model_data, f, indent=2)
        
        # Save ML model separately
        if self.reward_model is not None:
            model_path = filepath.replace('.json', '_model.pkl')
            
            if XGBOOST_AVAILABLE and isinstance(self.reward_model, xgb.XGBRegressor):
                self.reward_model.save_model(filepath.replace('.json', '_model.xgb'))
            else:
                import joblib
                joblib.dump(self.reward_model, model_path)
        
        print(f"Model saved to {filepath}")    
    def load_model(self, filepath: str):
        """Load trained model from disk"""
        
        with open(filepath, 'r') as f:
            model_data = json.load(f)
        
        self.campaign_templates = model_data['campaign_templates']
        self.thompson_params = {k: tuple(v) for k, v in model_data['thompson_params'].items()}
        self.feature_importance = model_data['feature_importance']
        self.exploration_rate = model_data['exploration_rate']
        
        # Load ML model
        if Path(filepath.replace('.json', '_model.xgb')).exists():
            self.reward_model = xgb.XGBRegressor()
            self.reward_model.load_model(filepath.replace('.json', '_model.xgb'))
        elif Path(filepath.replace('.json', '_model.pkl')).exists():
            import joblib
            self.reward_model = joblib.load(filepath.replace('.json', '_model.pkl'))
        
        print(f"Model loaded from {filepath}")