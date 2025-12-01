from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime


class BaseCloudAdapter(ABC):
    """Abstract base class for cloud provider adapters."""

    def __init__(self, credentials: Dict[str, Any]):
        """Initialize adapter with credentials."""
        self.credentials = credentials
        self._client = None

    @abstractmethod
    def test_connection(self) -> bool:
        """Test connection to cloud provider.

        Returns:
            bool: True if connection successful, False otherwise
        """
        pass

    @abstractmethod
    def list_instances(self, region: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all VM instances.

        Args:
            region: Optional region filter

        Returns:
            List of instance dictionaries
        """
        pass

    @abstractmethod
    def get_instance(self, instance_id: str) -> Dict[str, Any]:
        """Get details for a specific instance.

        Args:
            instance_id: Instance identifier

        Returns:
            Instance details dictionary
        """
        pass

    @abstractmethod
    def get_instance_metrics(
        self,
        instance_id: str,
        metric_type: str,
        start_time: datetime,
        end_time: datetime,
        period: int = 300
    ) -> List[Dict[str, Any]]:
        """Get metrics for an instance.

        Args:
            instance_id: Instance identifier
            metric_type: Type of metric (cpu, memory, disk_io, network_io)
            start_time: Start time for metrics
            end_time: End time for metrics
            period: Aggregation period in seconds

        Returns:
            List of metric data points
        """
        pass

    @abstractmethod
    def stop_instance(self, instance_id: str) -> bool:
        """Stop a running instance.

        Args:
            instance_id: Instance identifier

        Returns:
            bool: True if successful
        """
        pass

    @abstractmethod
    def start_instance(self, instance_id: str) -> bool:
        """Start a stopped instance.

        Args:
            instance_id: Instance identifier

        Returns:
            bool: True if successful
        """
        pass

    @abstractmethod
    def resize_instance(self, instance_id: str, new_instance_type: str) -> bool:
        """Resize an instance to a different type.

        Args:
            instance_id: Instance identifier
            new_instance_type: New instance type/flavor

        Returns:
            bool: True if successful
        """
        pass

    @abstractmethod
    def get_cost_data(
        self,
        start_date: datetime,
        end_date: datetime,
        granularity: str = "DAILY"
    ) -> Dict[str, Any]:
        """Get cost and usage data.

        Args:
            start_date: Start date
            end_date: End date
            granularity: Granularity (DAILY, MONTHLY)

        Returns:
            Cost data dictionary
        """
        pass

    def normalize_instance_data(self, raw_instance: Any) -> Dict[str, Any]:
        """Normalize instance data to common format.

        Args:
            raw_instance: Raw instance object from provider

        Returns:
            Normalized instance dictionary
        """
        raise NotImplementedError("Subclass must implement normalize_instance_data")
