from typing import List, Dict, Any, Optional
from datetime import datetime
import openstack
from openstack.connection import Connection
from .base import BaseCloudAdapter


class OpenStackAdapter(BaseCloudAdapter):
    """OpenStack cloud adapter implementation."""

    def __init__(self, credentials: Dict[str, Any]):
        """Initialize OpenStack adapter."""
        super().__init__(credentials)
        self._connection: Optional[Connection] = None

    def _get_connection(self) -> Connection:
        """Get or create OpenStack connection."""
        if self._connection is None:
            self._connection = openstack.connect(
                auth_url=self.credentials.get("auth_url"),
                username=self.credentials.get("username"),
                password=self.credentials.get("password"),
                project_name=self.credentials.get("project_name"),
                user_domain_name=self.credentials.get("user_domain_name", "Default"),
                project_domain_name=self.credentials.get("project_domain_name", "Default"),
            )
        return self._connection

    def test_connection(self) -> bool:
        """Test connection to OpenStack."""
        try:
            conn = self._get_connection()
            # Try to list projects to test connection
            list(conn.identity.projects())
            return True
        except Exception as e:
            print(f"OpenStack connection failed: {e}")
            return False

    def list_instances(self, region: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all instances in OpenStack."""
        try:
            conn = self._get_connection()
            servers = conn.compute.servers(details=True)
            return [self.normalize_instance_data(server) for server in servers]
        except Exception as e:
            print(f"Failed to list OpenStack instances: {e}")
            return []

    def get_instance(self, instance_id: str) -> Dict[str, Any]:
        """Get specific OpenStack instance."""
        try:
            conn = self._get_connection()
            server = conn.compute.get_server(instance_id)
            return self.normalize_instance_data(server)
        except Exception as e:
            print(f"Failed to get OpenStack instance {instance_id}: {e}")
            raise

    def get_instance_metrics(
        self,
        instance_id: str,
        metric_type: str,
        start_time: datetime,
        end_time: datetime,
        period: int = 300
    ) -> List[Dict[str, Any]]:
        """Get metrics for OpenStack instance.

        Note: This requires Gnocchi/Ceilometer or Prometheus integration.
        This is a placeholder implementation.
        """
        # TODO: Implement actual metrics collection from Gnocchi/Ceilometer
        print(f"Metrics collection not yet implemented for OpenStack")
        return []

    def stop_instance(self, instance_id: str) -> bool:
        """Stop an OpenStack instance."""
        try:
            conn = self._get_connection()
            conn.compute.stop_server(instance_id)
            return True
        except Exception as e:
            print(f"Failed to stop OpenStack instance {instance_id}: {e}")
            return False

    def start_instance(self, instance_id: str) -> bool:
        """Start an OpenStack instance."""
        try:
            conn = self._get_connection()
            conn.compute.start_server(instance_id)
            return True
        except Exception as e:
            print(f"Failed to start OpenStack instance {instance_id}: {e}")
            return False

    def resize_instance(self, instance_id: str, new_instance_type: str) -> bool:
        """Resize an OpenStack instance."""
        try:
            conn = self._get_connection()
            conn.compute.resize_server(instance_id, new_instance_type)
            return True
        except Exception as e:
            print(f"Failed to resize OpenStack instance {instance_id}: {e}")
            return False

    def get_cost_data(
        self,
        start_date: datetime,
        end_date: datetime,
        granularity: str = "DAILY"
    ) -> Dict[str, Any]:
        """Get cost data for OpenStack.

        Note: OpenStack doesn't have native billing API.
        This requires integration with a separate billing system.
        """
        # TODO: Implement billing system integration
        print("Cost data collection not yet implemented for OpenStack")
        return {
            "total_cost": 0.0,
            "by_service": {},
            "by_instance": {}
        }

    def normalize_instance_data(self, raw_instance: Any) -> Dict[str, Any]:
        """Normalize OpenStack server data to common format."""
        try:
            # Get flavor details
            flavor = raw_instance.flavor

            # Extract IPs
            addresses = raw_instance.addresses
            private_ip = None
            public_ip = None

            for network_name, ips in addresses.items():
                for ip_info in ips:
                    if ip_info.get("OS-EXT-IPS:type") == "fixed":
                        private_ip = ip_info.get("addr")
                    elif ip_info.get("OS-EXT-IPS:type") == "floating":
                        public_ip = ip_info.get("addr")

            return {
                "provider_instance_id": raw_instance.id,
                "name": raw_instance.name,
                "status": raw_instance.status.lower(),
                "instance_type": flavor.get("original_name", "unknown"),
                "vcpus": flavor.get("vcpus"),
                "ram_mb": flavor.get("ram"),
                "disk_gb": flavor.get("disk"),
                "region": getattr(raw_instance, "region", "RegionOne"),
                "availability_zone": getattr(raw_instance, "availability_zone", None),
                "private_ip": private_ip,
                "public_ip": public_ip,
                "launch_time": datetime.fromisoformat(raw_instance.created_at.replace('Z', '+00:00')) if raw_instance.created_at else None,
                "tags": getattr(raw_instance, "metadata", {}),
            }
        except Exception as e:
            print(f"Failed to normalize OpenStack instance data: {e}")
            raise
