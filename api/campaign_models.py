"""
Pydantic models for campaign recommendation API
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Optional, TYPE_CHECKING
from datetime import datetime

# Use TYPE_CHECKING to avoid circular imports
if TYPE_CHECKING:
    from api.main import PlaceData, OrderData, CampaignData


class CampaignFeedback(BaseModel):
    """Feedback for a campaign that was executed"""
    campaign_id: str = Field(..., description="ID of the executed campaign")
    actual_uplift: float = Field(..., description="Actual uplift percentage achieved")
    actual_roi: float = Field(..., description="Actual ROI percentage achieved")
    actual_revenue: float = Field(..., description="Actual revenue generated")
    success: bool = Field(..., description="Whether campaign was successful")
    notes: Optional[str] = Field(None, description="Additional notes")


class OrderItemData(BaseModel):
    """Order-item relationship for affinity analysis"""
    order_id: str = Field(..., description="Order ID")
    item_id: str = Field(..., description="Item ID")
    quantity: int = Field(default=1, ge=1, description="Quantity ordered")


class CampaignRecommendationRequest(BaseModel):
    """Request for campaign recommendations"""
    
    # Restaurant information - use Any to avoid forward reference
    place: Dict = Field(..., description="Restaurant information")
    
    # Historical data (same as demand prediction)
    orders: List[Dict] = Field(..., description="Historical order data")
    campaigns: List[Dict] = Field(
        default_factory=list,
        description="Historical campaigns"
    )
    order_items: Optional[List[OrderItemData]] = Field(
        default_factory=list,
        description="Order-item relationships for affinity analysis"
    )
    
    # Context for recommendations
    recommendation_start_date: str = Field(
        ...,
        description="Date to start recommendations from (YYYY-MM-DD)"
    )
    num_recommendations: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of recommendations to return"
    )
    optimize_for: str = Field(
        default="roi",
        description="Metric to optimize: 'roi', 'revenue', 'uplift'"
    )
    
    # Constraints
    max_discount: float = Field(
        default=30.0,
        ge=5.0,
        le=50.0,
        description="Maximum discount percentage allowed"
    )
    min_campaign_duration_days: int = Field(
        default=3,
        ge=1,
        le=30,
        description="Minimum campaign duration in days"
    )
    max_campaign_duration_days: int = Field(
        default=14,
        ge=1,
        le=60,
        description="Maximum campaign duration in days"
    )
    available_items: Optional[List[str]] = Field(
        default=None,
        description="List of available items for campaigns. If null, extracts from order history"
    )
    
    # Optional: Weather forecast
    weather_forecast: Optional[Dict[str, float]] = Field(
        default=None,
        description="Weather forecast for recommendation period"
    )
    
    # Optional: Upcoming holidays
    upcoming_holidays: Optional[List[str]] = Field(
        default_factory=list,
        description="List of upcoming holiday dates (YYYY-MM-DD)"
    )
    
    @field_validator('optimize_for')
    @classmethod
    def validate_optimize_for(cls, v):
        allowed = ['roi', 'revenue', 'uplift']
        if v not in allowed:
            raise ValueError(f"optimize_for must be one of {allowed}")
        return v


class RecommendedCampaignItem(BaseModel):
    """A single recommended campaign"""
    campaign_id: str = Field(..., description="Unique campaign identifier")
    items: List[str] = Field(..., description="Items included in campaign")
    discount_percentage: float = Field(..., description="Recommended discount")
    start_date: str = Field(..., description="Recommended start date (YYYY-MM-DD)")
    end_date: str = Field(..., description="Recommended end date (YYYY-MM-DD)")
    duration_days: int = Field(..., description="Campaign duration in days")
    
    # Predictions
    expected_uplift: float = Field(..., description="Expected uplift percentage")
    expected_roi: float = Field(..., description="Expected ROI percentage")
    expected_revenue: float = Field(..., description="Expected revenue increase")
    confidence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence in prediction (0-1)"
    )
    
    # Explanation
    reasoning: str = Field(..., description="Why this campaign is recommended")
    priority_score: float = Field(..., description="Priority/ranking score")
    
    # Context
    recommended_for_context: Dict = Field(
        ...,
        description="Context for which this was recommended"
    )


class CampaignRecommendationResponse(BaseModel):
    """Response with campaign recommendations"""
    
    # Add config to avoid model_ namespace conflict
    model_config = {"protected_namespaces": ()}
    
    restaurant_name: str = Field(..., description="Restaurant name")
    recommendation_date: str = Field(..., description="Date recommendations generated")
    recommendations: List[RecommendedCampaignItem] = Field(
        ...,
        description="List of recommended campaigns"
    )
    
    # Analysis summary
    analysis_summary: Dict = Field(
        ...,
        description="Summary of historical campaign analysis"
    )
    
    # Insights
    insights: Dict = Field(
        default_factory=dict,
        description="Additional insights and patterns"
    )
    
    # Model info - Changed from model_confidence to avoid namespace conflict
    confidence_level: str = Field(
        ...,
        description="Overall model confidence: 'high', 'medium', 'low'"
    )


class CampaignFeedbackResponse(BaseModel):
    """Response after submitting campaign feedback"""
    status: str = Field(..., description="Status of feedback submission")
    message: str = Field(..., description="Confirmation message")
    updated_parameters: Optional[Dict] = Field(
        default=None,
        description="Updated model parameters"
    )