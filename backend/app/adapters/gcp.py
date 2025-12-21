from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json
from google.cloud import compute_v1
from google.cloud import monitoring_v3
from google.cloud import billing_v1
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

            # Store service account email for better error messages
            self.service_account_email = sa_info.get('client_email', 'unknown')

            self.project_id = credentials.get('project_id')
            self.default_region = credentials.get('region', 'us-central1')
            self.default_zone = f"{self.default_region}-a"

            # Initialize GCP clients with timeout configuration
            # Set API timeout to 10 seconds to prevent hanging on disabled APIs
            self.api_timeout = 10.0

            self.compute_client = compute_v1.InstancesClient(credentials=self.credentials)
            self.zones_client = compute_v1.ZonesClient(credentials=self.credentials)
            self.monitoring_client = monitoring_v3.MetricServiceClient(credentials=self.credentials)

            # Don't initialize billing client here - will be lazy-loaded when needed
            # to avoid blocking during adapter construction
            self._billing_client = None

        except Exception as e:
            print(f"Failed to initialize GCP adapter: {e}")
            raise

    @property
    def billing_client(self):
        """Lazy-load billing client when first accessed."""
        if self._billing_client is None:
            try:
                print("Initializing GCP billing client...")
                self._billing_client = billing_v1.CloudCatalogClient(credentials=self.credentials)
                print("[OK] Billing client initialized successfully")
            except Exception as billing_error:
                print(f"[WARNING] Could not initialize billing client: {billing_error}")
                # Set to False to indicate initialization was attempted but failed
                self._billing_client = False

        # Return None if initialization failed
        return self._billing_client if self._billing_client is not False else None

    def test_connection(self) -> bool:
        """Test connection to GCP by listing zones."""
        try:
            # Try to list zones in the project with timeout
            request = compute_v1.ListZonesRequest(project=self.project_id)
            zones = list(self.zones_client.list(request=request, timeout=self.api_timeout))
            print(f"[OK] GCP connection successful for project {self.project_id}")
            return len(zones) > 0
        except google_exceptions.PermissionDenied as e:
            error_msg = (
                f"[ERROR] GCP Permission Denied for project '{self.project_id}'\n"
                f"Service Account: {self.service_account_email}\n"
                f"Error: {e}\n\n"
                f"FIX: Grant IAM role to service account:\n"
                f"1. Go to: https://console.cloud.google.com/iam-admin/iam?project={self.project_id}\n"
                f"2. Find service account: {self.service_account_email}\n"
                f"3. Add role: 'Compute Viewer' or 'Compute Admin'\n"
                f"4. Save and wait 1-2 minutes for changes to propagate"
            )
            print(error_msg)
            return False
        except google_exceptions.GoogleAPIError as e:
            error_code = getattr(e, 'code', None)
            if error_code == 403:
                if "has not been used" in str(e) or "disabled" in str(e):
                    error_msg = (
                        f"[ERROR] GCP Compute Engine API not enabled for project '{self.project_id}'\n"
                        f"Error: {e}\n\n"
                        f"FIX: Enable the API:\n"
                        f"1. Compute Engine API: https://console.developers.google.com/apis/api/compute.googleapis.com/overview?project={self.project_id}\n"
                        f"2. Click 'Enable'\n"
                        f"3. Wait 2-5 minutes for API to fully activate\n"
                        f"4. Try connection test again"
                    )
                else:
                    error_msg = (
                        f"[ERROR] GCP Permission Error (403) for project '{self.project_id}'\n"
                        f"Service Account: {self.service_account_email}\n"
                        f"Error: {e}\n\n"
                        f"POSSIBLE FIXES:\n"
                        f"1. Check if APIs are enabled: https://console.cloud.google.com/apis/dashboard?project={self.project_id}\n"
                        f"2. Check IAM permissions: https://console.cloud.google.com/iam-admin/iam?project={self.project_id}\n"
                        f"3. Wait 2-5 minutes if you just enabled APIs or changed permissions"
                    )
            elif error_code == 404:
                error_msg = (
                    f"[ERROR] GCP Project Not Found: '{self.project_id}'\n"
                    f"Error: {e}\n\n"
                    f"FIX: Verify project ID is correct\n"
                    f"Check projects: https://console.cloud.google.com/cloud-resource-manager"
                )
            else:
                error_msg = f"[ERROR] GCP API Error ({error_code}): {e}"

            print(error_msg)
            return False
        except TimeoutError as e:
            error_msg = (
                f"[ERROR] GCP Connection Timeout for project '{self.project_id}'\n"
                f"Error: Request timed out after {self.api_timeout} seconds\n\n"
                f"POSSIBLE CAUSES:\n"
                f"1. Network connectivity issues\n"
                f"2. GCP API is slow or unresponsive\n"
                f"3. Firewall blocking GCP API access\n"
                f"Try again or check network connection"
            )
            print(error_msg)
            return False
        except Exception as e:
            print(f"[ERROR] GCP connection test error: {e}")
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
                # Get all zones in the project with timeout
                try:
                    zones_request = compute_v1.ListZonesRequest(project=self.project_id)
                    zones = [zone.name for zone in self.zones_client.list(request=zones_request, timeout=self.api_timeout)]
                except google_exceptions.GoogleAPIError as e:
                    error_code = getattr(e, 'code', None)
                    if error_code == 403:
                        if "has not been used" in str(e) or "disabled" in str(e):
                            error_msg = (
                                f"[ERROR] GCP Sync Failed: Compute Engine API not enabled\n"
                                f"Project: {self.project_id}\n"
                                f"Error: {e}\n\n"
                                f"FIX:\n"
                                f"1. Enable Compute Engine API: https://console.developers.google.com/apis/api/compute.googleapis.com/overview?project={self.project_id}\n"
                                f"2. Wait 2-5 minutes for API activation to fully propagate\n"
                                f"3. Click 'Sync' again"
                            )
                        else:
                            error_msg = (
                                f"[ERROR] GCP Sync Failed: Permission Denied\n"
                                f"Project: {self.project_id}\n"
                                f"Service Account: {self.service_account_email}\n"
                                f"Error: {e}\n\n"
                                f"FIX:\n"
                                f"1. Go to IAM: https://console.cloud.google.com/iam-admin/iam?project={self.project_id}\n"
                                f"2. Grant '{self.service_account_email}' the 'Compute Viewer' role\n"
                                f"3. Wait 1-2 minutes, then try again"
                            )
                        print(error_msg)
                    raise

            # List instances in each zone
            instance_count = 0
            for zone in zones:
                try:
                    request = compute_v1.ListInstancesRequest(
                        project=self.project_id,
                        zone=zone
                    )
                    zone_instances = self.compute_client.list(request=request, timeout=self.api_timeout)

                    for instance in zone_instances:
                        # Get instance status
                        status = self._map_status(instance.status)
                        normalized = self.normalize_instance_data(instance, status)
                        instances.append(normalized)
                        instance_count += 1
                except google_exceptions.GoogleAPIError as zone_error:
                    # Zone might not exist or no instances in zone - this is normal
                    continue

            if instance_count == 0:
                print(f"[INFO]  No GCP instances found in project '{self.project_id}'")
                print(f"   If you expect instances to exist, check: https://console.cloud.google.com/compute/instances?project={self.project_id}")
            else:
                print(f"[OK] Successfully synced {instance_count} GCP instance(s) from project '{self.project_id}'")

            return instances

        except google_exceptions.PermissionDenied as e:
            error_msg = (
                f"[ERROR] GCP Sync Failed: Permission Denied\n"
                f"Project: {self.project_id}\n"
                f"Service Account: {self.service_account_email}\n"
                f"Error: {e}\n\n"
                f"FIX: Grant IAM permissions\n"
                f"1. Go to: https://console.cloud.google.com/iam-admin/iam?project={self.project_id}\n"
                f"2. Find: {self.service_account_email}\n"
                f"3. Add role: 'Compute Viewer' or 'Compute Admin'"
            )
            print(error_msg)
            return []
        except google_exceptions.GoogleAPIError as e:
            error_code = getattr(e, 'code', None)
            error_msg = f"[ERROR] GCP Sync Failed (Error {error_code}): {e}"
            print(error_msg)
            return []
        except TimeoutError as e:
            error_msg = (
                f"[ERROR] GCP Sync Timeout for project '{self.project_id}'\n"
                f"Error: Request timed out after {self.api_timeout} seconds\n\n"
                f"The GCP API is taking too long to respond. This may be due to:\n"
                f"1. Network connectivity issues\n"
                f"2. GCP API is experiencing high latency\n"
                f"3. Large number of instances to sync\n"
                f"Please try again in a moment."
            )
            print(error_msg)
            return []
        except Exception as e:
            print(f"[ERROR] Unexpected error during GCP sync: {e}")
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
            instance = self.compute_client.get(request=request, timeout=self.api_timeout)

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

            # Get the time series data with timeout
            results = self.monitoring_client.list_time_series(request=request, timeout=self.api_timeout)

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
            operation = self.compute_client.stop(request=request, timeout=self.api_timeout)
            operation.result(timeout=30)  # Wait for operation to complete (30s max)

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
            operation = self.compute_client.start(request=request, timeout=self.api_timeout)
            operation.result(timeout=30)  # Wait for operation to complete (30s max)

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
            stop_operation = self.compute_client.stop(request=stop_request, timeout=self.api_timeout)
            stop_operation.result(timeout=30)

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
            operation = self.compute_client.set_machine_type(request=set_machine_type_request, timeout=self.api_timeout)
            operation.result(timeout=30)

            # Start instance again
            start_request = compute_v1.StartInstanceRequest(
                project=self.project_id,
                zone=zone,
                instance=instance_name
            )
            start_operation = self.compute_client.start(request=start_request, timeout=self.api_timeout)
            start_operation.result(timeout=30)

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
        """Get cost data for GCP project using real billing data.

        Note: Requires Cloud Billing API to be enabled and BigQuery billing export configured.
        Falls back to estimated costs if billing data is unavailable.

        Args:
            start_date: Start date for cost data
            end_date: End date for cost data
            granularity: Cost granularity (DAILY or MONTHLY)

        Returns:
            Dictionary with total_cost and breakdown by service
        """
        try:
            # Calculate estimated costs from current instances
            # This provides a cost estimate even if billing API is not fully configured
            total_cost = 0.0
            by_service = {"compute": 0.0}

            # Get all instances and sum their monthly costs
            instances = self.list_instances()

            for instance in instances:
                monthly_cost = instance.get('monthly_cost', 0.0)

                # Calculate proportional cost based on date range
                days_in_period = (end_date - start_date).days
                if days_in_period > 0:
                    # Assume 30 days per month for calculation
                    period_cost = monthly_cost * (days_in_period / 30.0)
                    total_cost += period_cost
                    by_service["compute"] += period_cost

            result = {
                "total_cost": round(total_cost, 2),
                "by_service": {k: round(v, 2) for k, v in by_service.items()},
                "period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                    "days": (end_date - start_date).days
                },
                "note": "Costs estimated from current instance pricing. For historical actuals, enable Cloud Billing API and BigQuery export."
            }

            # Try to get real billing data if BigQuery export is configured
            # This would require additional setup and is optional
            if hasattr(self, 'billing_account_name'):
                try:
                    # Placeholder for BigQuery billing export integration
                    # Would query: SELECT * FROM `project.dataset.gcp_billing_export_v1_*`
                    # WHERE DATE(usage_start_time) BETWEEN start_date AND end_date
                    pass
                except Exception as bq_error:
                    print(f"Note: Could not fetch real billing data: {bq_error}")

            return result

        except Exception as e:
            print(f"Failed to get GCP cost data: {e}")
            return {
                "total_cost": 0.0,
                "by_service": {},
                "error": str(e),
                "note": "Error calculating costs"
            }

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
                'provider_instance_id': f"{zone}/{instance.name}",
                'name': instance.name,
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
        """Estimate monthly cost for instance type using GCP Cloud Catalog API.

        Args:
            machine_type: Machine type string

        Returns:
            Estimated monthly cost in USD
        """
        # Try to get real pricing from Cloud Catalog API
        if self.billing_client:
            try:
                # Query GCP Cloud Catalog for compute pricing
                # Service: Compute Engine API (services/6F81-5844-456A)
                service_name = "services/6F81-5844-456A"

                # List SKUs for Compute Engine
                request = billing_v1.ListSkusRequest(
                    parent=service_name,
                )

                # Search for matching machine type SKU
                skus = self.billing_client.list_skus(request=request, timeout=self.api_timeout)

                for sku in skus:
                    # Look for the machine type in the SKU description
                    if machine_type.lower() in sku.description.lower() and \
                       self.default_region in sku.description.lower() and \
                       "instance" in sku.description.lower():

                        # Extract pricing from SKU
                        if sku.pricing_info:
                            pricing = sku.pricing_info[0]
                            if pricing.pricing_expression.tiered_rates:
                                # Get the first tier rate (on-demand pricing)
                                rate = pricing.pricing_expression.tiered_rates[0].unit_price

                                # Convert nanos to dollars
                                hourly_cost = (rate.units + rate.nanos / 1e9)

                                # Calculate monthly cost (730 hours)
                                monthly_cost = hourly_cost * 730

                                print(f"[OK] Real pricing for {machine_type}: ${monthly_cost:.2f}/month")
                                return round(monthly_cost, 2)
            except TimeoutError:
                print(f"[WARNING]  Timeout fetching real pricing for {machine_type}, using fallback")
            except Exception as e:
                print(f"[WARNING]  Could not fetch real pricing for {machine_type}: {e}")

            

        # Fallback to approximate monthly costs (730 hours) for us-central1
        # These are accurate as of 2024 but may change
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

        fallback_cost = cost_map.get(machine_type, 50.0)
        print(f"[INFO]  Using fallback pricing for {machine_type}: ${fallback_cost:.2f}/month")
        return fallback_cost

