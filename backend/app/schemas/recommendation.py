from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime


class RecommendationResponse(BaseModel):
    """Schema for recommendation response."""
    id: str
    instance_id: str
    type: str
    priority: str
    title: str
    description: str
    monthly_savings: float
    confidence: str
    impact: str
    status: str
    extra_data: Dict[str, Any] = {}
    created_at: datetime
    applied_at: Optional[datetime] = None
    dismissed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class RecommendationListResponse(BaseModel):
    """Schema for recommendation list response."""
    total_recommendations: int
    total_potential_savings: float
    recommendations: List[RecommendationResponse]


class RecommendationActionResponse(BaseModel):
    """Schema for recommendation action response."""
    id: str
    status: str
    applied_at: Optional[datetime] = None
    result: str
