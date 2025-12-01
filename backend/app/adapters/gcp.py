from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json
from google.cloud import compute_v1
from google.cloud import monitoring_v3
from google.oauth2 import service_account
from google.api_core import exceptions as google_exceptions
from .base import BaseCloudAdapter


class GCPAdapter(BaseCloudAdapter):
    """Google Cloud Platform adapter implementation."""

    def __init__(self, credentials: Dict[str, Any]):
        """Initialize GCP adapter.

        Args:
            credentials: Dictionary containing:
                - service_account_json: Service account JSON key (as string or dict)
                - project_id: GCP project ID
                - region: Default region (e.g., 'us-central1')
        """
        super().__init__(credentials)

        try:
            # Parse service account JSON
            sa_json = credentials.get('service_account_json')
            if isinstance(sa_json, str):
                sa_info = json.loads(sa_json)
            else:
                sa_info = sa_json

            # Create credentials from service account info
            self.credentials = service_account.Credentials.from_service_account_info(sa_info)

            self.project_id = credentials.get('project_id')
            self.default_region = credentials.get('region', 'us-central1')
            self.default_zone = f"{self.default_region}-a"

            # Initialize GCP clients
            self.compute_client = compute_v1.InstancesClient(credentials=self.credentials)
            self.zones_client = compute_v1.ZonesClient(credentials=self.credentials)
            self.monitoring_client = monitoring_v3.MetricServiceClient(credentials=self.credentials)

        except Exception as e:
            print(f"Failed to initialize GCP adapter: {e}")
            raise

    def test_connection(self) -> bool:
        """Test connection to GCP by listing zones."""
        try:
            # Try to list zones in the project
            request = compute_v1.ListZonesRequest(project=self.project_id)
            zones = list(self.zones_client.list(request=request))
            return len(zones) > 0
        except google_exceptions.GoogleAPIError as e:
            print(f"GCP connection test failed: {e}")
            return False
        except Exception as e:
            print(f"GCP connection test error: {e}")
            return False

    def list_instances(self, region: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all GCP VM instances.

        Args:
            region: GCP region (e.g., 'us-central1'). If None, lists all instances.

        Returns:
            List of normalized instance dictionaries
        """
        try:
            instances = []

            # List all zones if no region specified
            if region:
                zones = [f"{region}-a", f"{region}-b", f"{region}-c", f"{region}-f"]
            else:
                # Get all zones in the project
                zones_request = compute_v1.ListZonesRequest(project=self.project_id)
                zones = [zone.name for zone in self.zones_client.list(request=zones_request)]

            # List instances in each zone
            for zone in zones:
                try:
                    request = compute_v1.ListInstancesRequest(
                        project=self.project_id,
                        zone=zone
                    )
                    zone_instances = self.compute_client.list(request=request)

                    for instance in zone_instances:
                        # Get instance status
                        status = self._map_status(instance.status)
                        normalized = self.normalize_instance_data(instance, status)
                        instances.append(normalized)
                except google_exceptions.GoogleAPIError:
                    # Zone might not exist or no instances in zone
                    continue

            return instances

        except google_exceptions.GoogleAPIError as e:
            print(f"Failed to list GCP instances: {e}")
            return []
        except Exception as e:
            print(f"Error listing GCP instances: {e}")
            return []

    def get_instance(self, instance_id: str) -> Dict[str, Any]:
        """Get specific GCP VM instance.

        Args:
            instance_id: Format "zone/instance_name" (e.g., "us-central1-a/my-instance")

        Returns:
            Normalized instance dictionary
        """
        try:
            parts = instance_id.split('/')
            if len(parts) != 2:
                raise ValueError(f"Invalid instance_id format. Expected 'zone/instance_name', got: {instance_id}")

            zone = parts[0]
            instance_name = parts[1]

            request = compute_v1.GetInstanceRequest(
                project=self.project_id,
                zone=zone,
                instance=instance_name
            )
            instance = self.compute_client.get(request=request)

            status = self._map_status(instance.status)
            return self.normalize_instance_data(instance, status)

        except google_exceptions.GoogleAPIError as e:
            print(f"Failed to get GCP instance {instance_id}: {e}")
            raise
        except Exception as e:
            print(f"Error getting GCP instance {instance_id}: {e}")
            raise

    def get_instance_metrics(
        self,
        instance_id: str,
        metric_type: str,
        start_time: datetime,
        end_time: datetime,
        period: int = 300
    ) -> List[Dict[str, Any]]:
        """Get metrics for GCP VM instance.

        Args:
            instance_id: Format "zone/instance_name"
            metric_type: Type of metric (cpu, memory, network, disk)
            start_time: Start time for metrics
            end_time: End time for metrics
            period: Metric interval in seconds (alignment period)

        Returns:
            List of metric data points
        """
        try:
            parts = instance_id.split('/')
            if len(parts) != 2:
                return []

            zone = parts[0]
            instance_name = parts[1]

            # Map metric types to GCP metric names
            metric_map = {
                'cpu': 'compute.googleapis.com/instance/cpu/utilization',
                'network_in': 'compute.googleapis.com/instance/network/received_bytes_count',
                'network_out': 'compute.googleapis.com/instance/network/sent_bytes_count',
                'disk_read': 'compute.googleapis.com/instance/disk/read_bytes_count',
                'disk_write': 'compute.googleapis.com/instance/disk/write_bytes_count'
            }

            metric_name = metric_map.get(metric_type, metric_map['cpu'])

            # Build time interval
            interval = monitoring_v3.TimeInterval()
            interval.end_time.FromDatetime(end_time)
            interval.start_time.FromDatetime(start_time)

            # Build the request
            project_name = f"projects/{self.project_id}"

            request = monitoring_v3.ListTimeSeriesRequest(
                name=project_name,
                filter=f'metric.type = "{metric_name}" AND resource.labels.instance_id = "{instance_name}" AND resource.labels.zone = "{zone}"',
                interval=interval,
                view=monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL
            )

            # Get the time series data
            results = self.monitoring_client.list_time_series(request=request)

            metric_data = []
            for result in results:
                for point in result.points:
                    value = point.value.double_value if hasattr(point.value, 'double_value') else point.value.int64_value

                    # Convert CPU utilization to percentage
                    if metric_type == 'cpu':
                        value = value * 100

                    metric_data.append({
                        'timestamp': point.interval.end_time.ToDatetime(),
                        'value': value,
                        'unit': 'percent' if metric_type == 'cpu' else 'bytes'
                    })

            return metric_data

        except google_exceptions.GoogleAPIError as e:
            print(f"Failed to get GCP metrics for {instance_id}: {e}")
            return []
        except Exception as e:
            print(f"Error getting GCP metrics: {e}")
            return []

    def stop_instance(self, instance_id: str) -> bool:
        """Stop a GCP VM instance.

        Args:
            instance_id: Format "zone/instance_name"

        Returns:
            True if successful, False otherwise
        """
        try:
            parts = instance_id.split('/')
            if len(parts) != 2:
                return False

            zone = parts[0]
            instance_name = parts[1]

            request = compute_v1.StopInstanceRequest(
                project=self.project_id,
                zone=zone,
                instance=instance_name
            )
            operation = self.compute_client.stop(request=request)
            operation.result()  # Wait for operation to complete

            return True

        except google_exceptions.GoogleAPIError as e:
            print(f"Failed to stop GCP instance {instance_id}: {e}")
            return False
        except Exception as e:
            print(f"Error stopping GCP instance: {e}")
            return False

    def start_instance(self, instance_id: str) -> bool:
        """Start a GCP VM instance.

        Args:
            instance_id: Format "zone/instance_name"

        Returns:
            True if successful, False otherwise
        """
        try:
            parts = instance_id.split('/')
            if len(parts) != 2:
                return False

            zone = parts[0]
            instance_name = parts[1]

            request = compute_v1.StartInstanceRequest(
                project=self.project_id,
                zone=zone,
                instance=instance_name
            )
            operation = self.compute_client.start(request=request)
            operation.result()  # Wait for operation to complete

            return True

        except google_exceptions.GoogleAPIError as e:
            print(f"Failed to start GCP instance {instance_id}: {e}")
            return False
        except Exception as e:
            print(f"Error starting GCP instance: {e}")
            return False

    def resize_instance(self, instance_id: str, new_instance_type: str) -> bool:
        """Resize a GCP VM instance (change machine type).

        Args:
            instance_id: Format "zone/instance_name"
            new_instance_type: New machine type (e.g., 'e2-medium', 'n1-standard-2')

        Returns:
            True if successful, False otherwise
        """
        try:
            parts = instance_id.split('/')
            if len(parts) != 2:
                return False

            zone = parts[0]
            instance_name = parts[1]

            # Instance must be stopped to change machine type
            # Stop instance first
            stop_request = compute_v1.StopInstanceRequest(
                project=self.project_id,
                zone=zone,
                instance=instance_name
            )
            stop_operation = self.compute_client.stop(request=stop_request)
            stop_operation.result()

            # Change machine type
            machine_type_url = f"zones/{zone}/machineTypes/{new_instance_type}"

            set_machine_type_request = compute_v1.SetMachineTypeInstanceRequest(
                project=self.project_id,
                zone=zone,
                instance=instance_name,
                instances_set_machine_type_request_resource=compute_v1.InstancesSetMachineTypeRequest(
                    machine_type=machine_type_url
                )
            )
            operation = self.compute_client.set_machine_type(request=set_machine_type_request)
            operation.result()

            # Start instance again
            start_request = compute_v1.StartInstanceRequest(
                project=self.project_id,
                zone=zone,
                instance=instance_name
            )
            start_operation = self.compute_client.start(request=start_request)
            start_operation.result()

            return True

        except google_exceptions.GoogleAPIError as e:
            print(f"Failed to resize GCP instance {instance_id}: {e}")
            return False
        except Exception as e:
            print(f"Error resizing GCP instance: {e}")
            return False

    def get_cost_data(
        self,
        start_date: datetime,
        end_date: datetime,
        granularity: str = "DAILY"
    ) -> Dict[str, Any]:
        """Get cost data for GCP project.

        Note: GCP Cloud Billing API requires additional setup and permissions.

        Args:
            start_date: Start date for cost data
            end_date: End date for cost data
            granularity: Cost granularity (DAILY or MONTHLY)

        Returns:
            Dictionary with total_cost and breakdown by service
        """
        try:
            # GCP Cloud Billing API requires separate setup
            # This is a placeholder that could be extended with actual billing data
            return {
                "total_cost": 0.0,
                "by_service": {},
                "note": "GCP cost data collection requires Cloud Billing API setup"
            }

        except Exception as e:
            print(f"Failed to get GCP cost data: {e}")
            return {"total_cost": 0.0, "by_service": {}, "error": str(e)}

    def normalize_instance_data(self, raw_instance: Any, status: str = None) -> Dict[str, Any]:
        """Normalize GCP VM data to common format.

        Args:
            raw_instance: GCP Instance object
            status: VM status string

        Returns:
            Normalized dictionary matching common instance format
        """
        try:
            instance = raw_instance

            # Extract zone from instance zone URL
            zone = instance.zone.split('/')[-1]
            region = '-'.join(zone.split('-')[:-1])

            # Extract machine type from URL
            machine_type = instance.machine_type.split('/')[-1]

            # Get network information
            private_ip = None
            public_ip = None

            if instance.network_interfaces:
                network_interface = instance.network_interfaces[0]
                private_ip = network_interface.network_i_p

                if network_interface.access_configs:
                    public_ip = network_interface.access_configs[0].nat_i_p

            # Parse machine type for CPU and RAM
            vcpus, ram_mb = self._parse_machine_type(machine_type)

            # Estimate cost
            monthly_cost = self._estimate_instance_cost(machine_type)

            # Parse creation timestamp
            launch_time = None
            if instance.creation_timestamp:
                launch_time = datetime.fromisoformat(instance.creation_timestamp.replace('Z', '+00:00'))

            return {
                'id': f"{zone}/{instance.name}",
                'name': instance.name,
                'provider': 'gcp',
                'provider_instance_id': str(instance.id),
                'status': status or 'unknown',
                'instance_type': machine_type,
                'region': region,
                'availability_zone': zone,
                'private_ip': private_ip,
                'public_ip': public_ip,
                'launch_time': launch_time,
                'tags': dict(instance.labels) if instance.labels else {},
                'vcpus': vcpus,
                'ram_mb': ram_mb,
                'monthly_cost': monthly_cost,
            }

        except Exception as e:
            print(f"Error normalizing GCP instance data: {e}")
            raise

    def _map_status(self, gcp_status: str) -> str:
        """Map GCP instance status to common status."""
        status_map = {
            'RUNNING': 'running',
            'TERMINATED': 'stopped',
            'STOPPING': 'stopping',
            'PROVISIONING': 'starting',
            'STAGING': 'starting',
            'SUSPENDING': 'stopping',
            'SUSPENDED': 'stopped',
        }
        return status_map.get(gcp_status, 'unknown')

    def _parse_machine_type(self, machine_type: str) -> tuple:
        """Parse machine type to get vCPUs and RAM.

        Args:
            machine_type: Machine type string (e.g., 'e2-medium', 'n1-standard-2')

        Returns:
            Tuple of (vcpus, ram_mb)
        """
        # Common GCP machine types
        machine_specs = {
            # E2 series
            'e2-micro': (2, 1024),
            'e2-small': (2, 2048),
            'e2-medium': (2, 4096),
            'e2-standard-2': (2, 8192),
            'e2-standard-4': (4, 16384),
            'e2-standard-8': (8, 32768),
            'e2-standard-16': (16, 65536),

            # N1 series
            'n1-standard-1': (1, 3840),
            'n1-standard-2': (2, 7680),
            'n1-standard-4': (4, 15360),
            'n1-standard-8': (8, 30720),
            'n1-standard-16': (16, 61440),
            'n1-standard-32': (32, 122880),

            # N2 series
            'n2-standard-2': (2, 8192),
            'n2-standard-4': (4, 16384),
            'n2-standard-8': (8, 32768),
            'n2-standard-16': (16, 65536),

            # F1/G1 series
            'f1-micro': (1, 614),
            'g1-small': (1, 1740),
        }

        return machine_specs.get(machine_type, (2, 4096))  # Default to 2 vCPUs, 4GB RAM

    def _estimate_instance_cost(self, machine_type: str) -> float:
        """Estimate monthly cost for instance type.

        Args:
            machine_type: Machine type string

        Returns:
            Estimated monthly cost in USD
        """
        # Approximate monthly costs (730 hours) for us-central1
        cost_map = {
            # E2 series
            'e2-micro': 6.11,
            'e2-small': 12.23,
            'e2-medium': 24.45,
            'e2-standard-2': 48.91,
            'e2-standard-4': 97.82,
            'e2-standard-8': 195.64,
            'e2-standard-16': 391.28,

            # N1 series
            'n1-standard-1': 24.27,
            'n1-standard-2': 48.54,
            'n1-standard-4': 97.09,
            'n1-standard-8': 194.18,
            'n1-standard-16': 388.36,
            'n1-standard-32': 776.72,

            # N2 series
            'n2-standard-2': 60.74,
            'n2-standard-4': 121.47,
            'n2-standard-8': 242.95,
            'n2-standard-16': 485.90,

            # F1/G1 series
            'f1-micro': 3.88,
            'g1-small': 13.23,
        }

        return cost_map.get(machine_type, 50.0)  # Default estimate
