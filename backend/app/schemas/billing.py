from pydantic import BaseModel
from typing import Dict, List
from datetime import date


class BillingResponse(BaseModel):
    """Schema for current billing information."""
    period: str
    start_date: date
    end_date: date
    total_cost: float
    by_provider: Dict[str, float]
    by_service: Dict[str, float]
    projected_month_end: float


class CostBreakdownItem(BaseModel):
    """Schema for cost breakdown item."""
    instance_id: str
    instance_name: str
    cost: float
    percentage: float


class CostBreakdownResponse(BaseModel):
    """Schema for cost breakdown response."""
    group_by: str
    items: List[CostBreakdownItem]


class CostForecastResponse(BaseModel):
    """Schema for cost forecast response."""
    provider: str
    forecast_days: int
    predictions: List[Dict[str, float]]  # [{date, cost, lower_bound, upper_bound}]
    trend: str  # increasing, decreasing, stable
    budget_alert: bool
    projected_overrun: float
