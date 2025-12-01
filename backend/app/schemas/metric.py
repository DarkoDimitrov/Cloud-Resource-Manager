from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class MetricCreate(BaseModel):
    """Schema for creating a metric."""
    instance_id: str
    metric_type: str
    value: float
    unit: str
    timestamp: Optional[datetime] = None


class MetricDataPoint(BaseModel):
    """Schema for a single metric data point."""
    timestamp: datetime
    value: float
    min: Optional[float] = None
    max: Optional[float] = None
    avg: Optional[float] = None


class MetricStatistics(BaseModel):
    """Schema for metric statistics."""
    min: float
    max: float
    avg: float
    p95: Optional[float] = None


class MetricResponse(BaseModel):
    """Schema for metric response."""
    instance_id: str
    metric: str
    unit: str
    period: str
    interval: str
    data_points: List[MetricDataPoint]
    statistics: MetricStatistics
