from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ProviderCredentials(BaseModel):
    """Base credentials schema."""
    pass


class OpenStackCredentials(ProviderCredentials):
    """OpenStack-specific credentials."""
    auth_url: str
    username: str
    password: str
    project_name: str
    user_domain_name: str = "Default"
    project_domain_name: str = "Default"


class AWSCredentials(ProviderCredentials):
    """AWS-specific credentials."""
    access_key_id: str
    secret_access_key: str
    session_token: Optional[str] = None


class AzureCredentials(ProviderCredentials):
    """Azure-specific credentials."""
    tenant_id: str
    client_id: str
    client_secret: str
    subscription_id: str


class ProviderCreate(BaseModel):
    """Schema for creating a provider."""
    name: str = Field(..., min_length=1, max_length=255)
    provider_type: str = Field(..., pattern="^(openstack|aws|azure)$")
    credentials: Dict[str, Any]
    regions: List[str] = Field(default_factory=list)
    enabled: bool = True


class ProviderUpdate(BaseModel):
    """Schema for updating a provider."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    credentials: Optional[Dict[str, Any]] = None
    regions: Optional[List[str]] = None
    enabled: Optional[bool] = None


class ProviderResponse(BaseModel):
    """Schema for provider response."""
    id: str
    name: str
    provider_type: str
    regions: List[str]
    enabled: bool
    last_sync: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    instance_count: Optional[int] = 0
    monthly_cost: Optional[float] = 0.0

    class Config:
        from_attributes = True
