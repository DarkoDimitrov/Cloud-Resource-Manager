from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class InstanceResponse(BaseModel):
    """Schema for instance response."""
    id: str
    provider_id: str
    provider_instance_id: str
    name: str
    status: str
    instance_type: str
    vcpus: Optional[int] = None
    ram_mb: Optional[int] = None
    disk_gb: Optional[int] = None
    region: str
    availability_zone: Optional[str] = None
    private_ip: Optional[str] = None
    public_ip: Optional[str] = None
    launch_time: Optional[datetime] = None
    tags: Dict[str, Any] = {}
    monthly_cost: float = 0.0
    last_updated: datetime

    class Config:
        from_attributes = True


class InstanceListResponse(BaseModel):
    """Schema for paginated instance list response."""
    total: int
    limit: int
    offset: int
    instances: List[InstanceResponse]


class InstanceStatsResponse(BaseModel):
    """Schema for instance statistics."""
    total_instances: int
    running_instances: int
    stopped_instances: int
    total_monthly_cost: float
    by_provider: Dict[str, int]
    by_region: Dict[str, int]
