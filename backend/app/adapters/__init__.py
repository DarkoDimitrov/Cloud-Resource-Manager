from .base import BaseCloudAdapter
from .openstack import OpenStackAdapter
from .aws import AWSAdapter
from .azure import AzureAdapter
from .gcp import GCPAdapter

__all__ = ["BaseCloudAdapter", "OpenStackAdapter", "AWSAdapter", "AzureAdapter", "GCPAdapter"]


def get_adapter(provider_type: str, credentials: dict) -> BaseCloudAdapter:
    """Factory function to get the appropriate cloud adapter."""
    adapters = {
        "openstack": OpenStackAdapter,
        "aws": AWSAdapter,
        "azure": AzureAdapter,
        "gcp": GCPAdapter
    }

    adapter_class = adapters.get(provider_type)
    if not adapter_class:
        raise ValueError(f"Unknown provider type: {provider_type}")

    return adapter_class(credentials)
