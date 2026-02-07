"""
Pydantic models for Campaign Recommendation API
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict


class OrderItemData(BaseModel):
    """Order item data for affinity analysis"""
    order_id: str
    item_id: str
    quantity: Optional[int] = 1


class RecommendedCampaignItem(BaseModel):
    """A single campaign recommendation"""
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
    
    # Reasoning
    reasoning: str
    priority_score: float
    recommended_for_context: Dict


class CampaignRecommendationResponse(BaseModel):
    """Response containing campaign recommendations"""
    restaurant_name: str
    recommendation_date: str
    recommendations: List[RecommendedCampaignItem]
    analysis_summary: Dict
    insights: Dict
    confidence_level: str


class CampaignRecommendationRequest(BaseModel):
    """
    Request for campaign recommendations.
    
    Weather and holiday data are automatically fetched based on restaurant location.
    """
    place: Dict  # Can be PlaceData or dict
    orders: List[Dict]  # Can be List[OrderData] or list of dicts
    campaigns: List[Dict] = []
    order_items: Optional[List[Dict]] = None
    
    recommendation_start_date: str = Field(
        ...,
        description="Start date for recommendations (YYYY-MM-DD)"
    )
    num_recommendations: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of campaign recommendations to generate"
    )
    optimize_for: str = Field(
        default="roi",
        description="Optimization metric (roi, revenue, uplift)"
    )
    
    # Business constraints
    max_discount: float = Field(default=30.0, ge=0, le=100)
    min_campaign_duration_days: int = Field(default=3, ge=1, le=30)
    max_campaign_duration_days: int = Field(default=14, ge=1, le=90)
    
    # Available items
    available_items: List[str] = Field(
        default_factory=list,
        description="List of menu items available for campaigns"
    )
    
    # ===== OPTIONAL - AUTO-FETCHED IF NOT PROVIDED =====
    weather_forecast: Optional[Dict[str, float]] = Field(
        default=None,
        description="Weather forecast (auto-fetched based on location if not provided). "
                    "Keys: avg_temperature, avg_precipitation, good_weather_ratio"
    )
    upcoming_holidays: Optional[List[str]] = Field(
        default=None,
        description="List of upcoming holiday dates in YYYY-MM-DD format "
                    "(auto-fetched based on location if not provided)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "place": {
                    "place_id": "pl_12345",
                    "place_name": "Pizza Paradise",
                    "type": "restaurant",
                    "latitude": 55.6761,
                    "longitude": 12.5683,
                    "waiting_time": 30,
                    "receiving_phone": True,
                    "delivery": True,
                    "opening_hours": {
                        "monday": {"from": "10:00", "to": "23:00"}
                    },
                    "rating": 4.5,
                    "accepting_orders": True
                },
                "orders": [
                    {
                        "time": "2024-01-01T12:30:00",
                        "items": 3,
                        "status": "completed",
                        "total_amount": 45.5,
                        "discount_amount": 5.0
                    }
                ],
                "campaigns": [
                    {
                        "start_time": "2024-01-01T00:00:00",
                        "end_time": "2024-01-07T23:59:59",
                        "items_included": ["pizza_margherita", "drink_cola"],
                        "discount": 15.0
                    }
                ],
                "recommendation_start_date": "2024-03-01",
                "num_recommendations": 5,
                "optimize_for": "roi",
                "available_items": ["pizza_margherita", "pasta_carbonara", "drink_cola"],
                # Note: weather_forecast and upcoming_holidays are optional
                # They will be automatically fetched based on restaurant location
            }
        }


class CampaignFeedback(BaseModel):
    """Feedback on executed campaign for online learning"""
    campaign_id: str = Field(..., description="ID of the executed campaign")
    actual_uplift: Optional[float] = Field(None, description="Actual uplift percentage achieved")
    actual_roi: Optional[float] = Field(None, description="Actual ROI percentage achieved")
    actual_revenue: Optional[float] = Field(None, description="Actual revenue generated")
    success: bool = Field(..., description="Whether the campaign was successful (ROI > 0)")
    notes: Optional[str] = Field(None, description="Additional notes or observations")


class CampaignFeedbackResponse(BaseModel):
    """Response after submitting campaign feedback"""
    status: str
    message: str
    updated_parameters: Optional[Dict] = None