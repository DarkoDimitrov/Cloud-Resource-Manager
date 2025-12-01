from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime


class AnomalyResponse(BaseModel):
    """Schema for anomaly response."""
    id: str
    instance_id: str
    metric_type: str
    severity: str
    anomaly_score: float
    detected_at: datetime
    resolved_at: Optional[datetime] = None
    title: str
    description: str
    root_cause: Optional[str] = None
    recommended_action: Optional[str] = None
    extra_data: Dict[str, Any] = {}
    status: str

    class Config:
        from_attributes = True


class AnomalyListResponse(BaseModel):
    """Schema for anomaly list response."""
    total_anomalies: int
    critical_count: int
    warning_count: int
    anomalies: List[AnomalyResponse]


class NLQueryRequest(BaseModel):
    """Schema for natural language query request."""
    query: str
    user_id: Optional[str] = None


class NLQueryResponse(BaseModel):
    """Schema for natural language query response."""
    query: str
    answer: str
    data: Optional[Dict[str, Any]] = None
    suggestions: List[str] = []
