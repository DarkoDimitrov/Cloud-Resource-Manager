from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from azure.identity import ClientSecretCredential
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.monitor import MonitorManagementClient
from azure.mgmt.costmanagement import CostManagementClient
from azure.core.exceptions import AzureError
from .base import BaseCloudAdapter


class AzureAdapter(BaseCloudAdapter):
    """Azure cloud adapter implementation."""

    def __init__(self, credentials: Dict[str, Any]):
        """Initialize Azure adapter.

        Args:
            credentials: Dictionary containing:
                - tenant_id: Azure AD tenant ID
                - client_id: Application (client) ID
                - client_secret: Client secret
                - subscription_id: Azure subscription ID
        """
        super().__init__(credentials)

        try:
            # Create credential object
            self.credential = ClientSecretCredential(
                tenant_id=credentials.get('tenant_id'),
                client_id=credentials.get('client_id'),
                client_secret=credentials.get('client_secret')
            )

            self.subscription_id = credentials.get('subscription_id')

            # Initialize Azure clients
            self.compute_client = ComputeManagementClient(
                credential=self.credential,
                subscription_id=self.subscription_id
            )

            self.monitor_client = MonitorManagementClient(
                credential=self.credential,
                subscription_id=self.subscription_id
            )

            # Cost management client (may not work for all subscription types)
            try:
                self.cost_client = CostManagementClient(
                    credential=self.credential
                )
            except:
                self.cost_client = None

        except Exception as e:
            print(f"Failed to initialize Azure adapter: {e}")
            raise

    def test_connection(self) -> bool:
        """Test connection to Azure by listing resource groups."""
        try:
            # Try to list VMs to test connection
            list(self.compute_client.virtual_machines.list_all())
            return True
        except AzureError as e:
            print(f"Azure connection test failed: {e}")
            return False
        except Exception as e:
            print(f"Azure connection test error: {e}")
            return False

    def list_instances(self, region: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all Azure VMs.

        Args:
            region: Azure location (e.g., 'eastus'). If None, lists all VMs.

        Returns:
            List of normalized instance dictionaries
        """
        try:
            instances = []
            vms = self.compute_client.virtual_machines.list_all()

            for vm in vms:
                # Filter by location if specified
                if region and vm.location != region:
                    continue

                # Get instance view for status
                try:
                    instance_view = self.compute_client.virtual_machines.instance_view(
                        resource_group_name=self._get_resource_group_from_id(vm.id),
                        vm_name=vm.name
                    )
                    status = self._get_vm_status(instance_view)
                except:
                    status = "unknown"

                normalized = self.normalize_instance_data(vm, status)
                instances.append(normalized)

            return instances

        except AzureError as e:
            print(f"Failed to list Azure VMs: {e}")
            return []
        except Exception as e:
            print(f"Error listing Azure VMs: {e}")
            return []

    def get_instance(self, instance_id: str) -> Dict[str, Any]:
        """Get specific Azure VM.

        Args:
            instance_id: Format "resource_group_name/vm_name"

        Returns:
            Normalized instance dictionary
        """
        try:
            parts = instance_id.split('/')
            if len(parts) != 2:
                raise ValueError(f"Invalid instance_id format. Expected 'resource_group/vm_name', got: {instance_id}")

            resource_group = parts[0]
            vm_name = parts[1]

            vm = self.compute_client.virtual_machines.get(
                resource_group_name=resource_group,
                vm_name=vm_name
            )

            # Get instance view for status
            instance_view = self.compute_client.virtual_machines.instance_view(
                resource_group_name=resource_group,
                vm_name=vm_name
            )
            status = self._get_vm_status(instance_view)

            return self.normalize_instance_data(vm, status)

        except AzureError as e:
            print(f"Failed to get Azure VM {instance_id}: {e}")
            raise
        except Exception as e:
            print(f"Error getting Azure VM {instance_id}: {e}")
            raise

    def get_instance_metrics(
        self,
        instance_id: str,
        metric_type: str,
        start_time: datetime,
        end_time: datetime,
        period: int = 300
    ) -> List[Dict[str, Any]]:
        """Get metrics for Azure VM.

        Args:
            instance_id: Format "resource_group_name/vm_name"
            metric_type: Type of metric (cpu, memory, network, disk)
            start_time: Start time for metrics
            end_time: End time for metrics
            period: Metric interval in seconds

        Returns:
            List of metric data points
        """
        try:
            parts = instance_id.split('/')
            if len(parts) != 2:
                return []

            resource_group = parts[0]
            vm_name = parts[1]

            # Get VM resource ID
            vm = self.compute_client.virtual_machines.get(
                resource_group_name=resource_group,
                vm_name=vm_name
            )
            resource_id = vm.id

            # Map metric types to Azure metric names
            metric_map = {
                'cpu': 'Percentage CPU',
                'memory': 'Available Memory Bytes',
                'network_in': 'Network In Total',
                'network_out': 'Network Out Total',
                'disk_read': 'Disk Read Bytes',
                'disk_write': 'Disk Write Bytes'
            }

            metric_name = metric_map.get(metric_type, 'Percentage CPU')

            # Calculate timespan
            timespan = f"{start_time.isoformat()}/{end_time.isoformat()}"

            # Get metrics
            metrics_data = self.monitor_client.metrics.list(
                resource_id,
                timespan=timespan,
                interval=f"PT{period}S",
                metricnames=metric_name,
                aggregation='Average'
            )

            result = []
            for metric in metrics_data.value:
                for timeseries in metric.timeseries:
                    for data_point in timeseries.data:
                        if data_point.average is not None:
                            result.append({
                                'timestamp': data_point.time_stamp,
                                'value': data_point.average,
                                'unit': metric.unit
                            })

            return result

        except AzureError as e:
            print(f"Failed to get Azure metrics for {instance_id}: {e}")
            return []
        except Exception as e:
            print(f"Error getting Azure metrics: {e}")
            return []

    def stop_instance(self, instance_id: str) -> bool:
        """Stop an Azure VM (deallocate).

        Args:
            instance_id: Format "resource_group_name/vm_name"

        Returns:
            True if successful, False otherwise
        """
        try:
            parts = instance_id.split('/')
            if len(parts) != 2:
                return False

            resource_group = parts[0]
            vm_name = parts[1]

            # Deallocate VM (stops billing)
            poller = self.compute_client.virtual_machines.begin_deallocate(
                resource_group_name=resource_group,
                vm_name=vm_name
            )
            poller.wait()

            return True

        except AzureError as e:
            print(f"Failed to stop Azure VM {instance_id}: {e}")
            return False
        except Exception as e:
            print(f"Error stopping Azure VM: {e}")
            return False

    def start_instance(self, instance_id: str) -> bool:
        """Start an Azure VM.

        Args:
            instance_id: Format "resource_group_name/vm_name"

        Returns:
            True if successful, False otherwise
        """
        try:
            parts = instance_id.split('/')
            if len(parts) != 2:
                return False

            resource_group = parts[0]
            vm_name = parts[1]

            poller = self.compute_client.virtual_machines.begin_start(
                resource_group_name=resource_group,
                vm_name=vm_name
            )
            poller.wait()

            return True

        except AzureError as e:
            print(f"Failed to start Azure VM {instance_id}: {e}")
            return False
        except Exception as e:
            print(f"Error starting Azure VM: {e}")
            return False

    def resize_instance(self, instance_id: str, new_instance_type: str) -> bool:
        """Resize an Azure VM.

        Args:
            instance_id: Format "resource_group_name/vm_name"
            new_instance_type: New VM size (e.g., 'Standard_B2s')

        Returns:
            True if successful, False otherwise
        """
        try:
            parts = instance_id.split('/')
            if len(parts) != 2:
                return False

            resource_group = parts[0]
            vm_name = parts[1]

            # Get current VM
            vm = self.compute_client.virtual_machines.get(
                resource_group_name=resource_group,
                vm_name=vm_name
            )

            # Update VM size
            vm.hardware_profile.vm_size = new_instance_type

            poller = self.compute_client.virtual_machines.begin_create_or_update(
                resource_group_name=resource_group,
                vm_name=vm_name,
                parameters=vm
            )
            poller.wait()

            return True

        except AzureError as e:
            print(f"Failed to resize Azure VM {instance_id}: {e}")
            return False
        except Exception as e:
            print(f"Error resizing Azure VM: {e}")
            return False

    def get_cost_data(
        self,
        start_date: datetime,
        end_date: datetime,
        granularity: str = "DAILY"
    ) -> Dict[str, Any]:
        """Get cost data for Azure subscription.

        Note: Cost Management API may not be available for all subscription types.

        Args:
            start_date: Start date for cost data
            end_date: End date for cost data
            granularity: Cost granularity (DAILY or MONTHLY)

        Returns:
            Dictionary with total_cost and breakdown by service
        """
        try:
            if not self.cost_client:
                return {"total_cost": 0.0, "by_service": {}, "error": "Cost Management API not available"}

            # Azure Cost Management API requires specific scope format
            scope = f"/subscriptions/{self.subscription_id}"

            # This is a simplified implementation
            # Full implementation would use cost_client.query.usage()
            return {
                "total_cost": 0.0,
                "by_service": {},
                "note": "Cost data collection requires additional Azure permissions"
            }

        except Exception as e:
            print(f"Failed to get Azure cost data: {e}")
            return {"total_cost": 0.0, "by_service": {}, "error": str(e)}

    def normalize_instance_data(self, raw_instance: Any, status: str = None) -> Dict[str, Any]:
        """Normalize Azure VM data to common format.

        Args:
            raw_instance: Azure VM object
            status: VM status string

        Returns:
            Normalized dictionary matching common instance format
        """
        try:
            vm = raw_instance
            resource_group = self._get_resource_group_from_id(vm.id)

            # Get network info
            private_ip = None
            public_ip = None

            if vm.network_profile and vm.network_profile.network_interfaces:
                # This is simplified - full implementation would fetch actual IPs
                private_ip = "N/A"
                public_ip = None

            # Estimate cost (this is very rough - actual costs vary)
            monthly_cost = self._estimate_vm_cost(vm.hardware_profile.vm_size)

            return {
                'id': f"{resource_group}/{vm.name}",
                'name': vm.name,
                'provider': 'azure',
                'provider_instance_id': vm.vm_id,
                'status': status or 'unknown',
                'instance_type': vm.hardware_profile.vm_size,
                'region': vm.location,
                'availability_zone': vm.zones[0] if vm.zones else None,
                'private_ip': private_ip,
                'public_ip': public_ip,
                'launch_time': None,  # Azure doesn't provide this directly
                'tags': vm.tags or {},
                'vcpus': self._get_vm_cores(vm.hardware_profile.vm_size),
                'ram_mb': self._get_vm_ram(vm.hardware_profile.vm_size),
                'monthly_cost': monthly_cost,
            }

        except Exception as e:
            print(f"Error normalizing Azure VM data: {e}")
            raise

    def _get_resource_group_from_id(self, resource_id: str) -> str:
        """Extract resource group name from Azure resource ID."""
        parts = resource_id.split('/')
        try:
            rg_index = parts.index('resourceGroups') + 1
            return parts[rg_index]
        except (ValueError, IndexError):
            return "unknown"

    def _get_vm_status(self, instance_view) -> str:
        """Extract VM power state from instance view."""
        if not instance_view or not instance_view.statuses:
            return "unknown"

        for status in instance_view.statuses:
            if status.code.startswith('PowerState/'):
                state = status.code.split('/')[-1]
                # Map Azure states to common states
                if state == 'running':
                    return 'running'
                elif state in ['stopped', 'deallocated']:
                    return 'stopped'
                elif state == 'starting':
                    return 'starting'
                elif state == 'stopping':
                    return 'stopping'

        return "unknown"

    def _get_vm_cores(self, vm_size: str) -> int:
        """Estimate vCPUs from VM size (rough approximation)."""
        # Very simplified mapping
        size_map = {
            'Standard_B1s': 1, 'Standard_B1ms': 1, 'Standard_B2s': 2, 'Standard_B2ms': 2,
            'Standard_B4ms': 4, 'Standard_B8ms': 8, 'Standard_D2s_v3': 2, 'Standard_D4s_v3': 4,
            'Standard_D8s_v3': 8, 'Standard_D16s_v3': 16, 'Standard_F2s_v2': 2,
            'Standard_F4s_v2': 4, 'Standard_F8s_v2': 8
        }
        return size_map.get(vm_size, 2)  # Default to 2 if unknown

    def _get_vm_ram(self, vm_size: str) -> int:
        """Estimate RAM in MB from VM size (rough approximation)."""
        # Very simplified mapping
        size_map = {
            'Standard_B1s': 1024, 'Standard_B1ms': 2048, 'Standard_B2s': 4096, 'Standard_B2ms': 8192,
            'Standard_B4ms': 16384, 'Standard_B8ms': 32768, 'Standard_D2s_v3': 8192,
            'Standard_D4s_v3': 16384, 'Standard_D8s_v3': 32768, 'Standard_D16s_v3': 65536
        }
        return size_map.get(vm_size, 4096)  # Default to 4GB if unknown

    def _estimate_vm_cost(self, vm_size: str) -> float:
        """Estimate monthly cost (very rough - actual costs vary by region and contract)."""
        # These are approximate Pay-As-You-Go prices in USD
        price_map = {
            'Standard_B1s': 7.59, 'Standard_B1ms': 15.18, 'Standard_B2s': 30.37,
            'Standard_B2ms': 60.74, 'Standard_B4ms': 121.47, 'Standard_B8ms': 242.95,
            'Standard_D2s_v3': 70.08, 'Standard_D4s_v3': 140.16, 'Standard_D8s_v3': 280.32,
            'Standard_F2s_v2': 62.78, 'Standard_F4s_v2': 125.56
        }
        return price_map.get(vm_size, 50.0)  # Default estimate
