from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import boto3
from botocore.exceptions import ClientError
from .base import BaseCloudAdapter


class AWSAdapter(BaseCloudAdapter):
    """AWS cloud adapter implementation."""

    def __init__(self, credentials: Dict[str, Any]):
        """Initialize AWS adapter."""
        super().__init__(credentials)
        self._ec2_client = None
        self._cloudwatch_client = None
        self._ce_client = None

    def _get_ec2_client(self, region: str = "us-east-1"):
        """Get or create EC2 client."""
        session = boto3.Session(
            aws_access_key_id=self.credentials.get("access_key_id"),
            aws_secret_access_key=self.credentials.get("secret_access_key"),
            aws_session_token=self.credentials.get("session_token"),
            region_name=region
        )
        return session.client("ec2")

    def _get_cloudwatch_client(self, region: str = "us-east-1"):
        """Get or create CloudWatch client."""
        session = boto3.Session(
            aws_access_key_id=self.credentials.get("access_key_id"),
            aws_secret_access_key=self.credentials.get("secret_access_key"),
            aws_session_token=self.credentials.get("session_token"),
            region_name=region
        )
        return session.client("cloudwatch")

    def _get_ce_client(self):
        """Get or create Cost Explorer client."""
        session = boto3.Session(
            aws_access_key_id=self.credentials.get("access_key_id"),
            aws_secret_access_key=self.credentials.get("secret_access_key"),
            aws_session_token=self.credentials.get("session_token"),
            region_name="us-east-1"  # Cost Explorer is only in us-east-1
        )
        return session.client("ce")

    def test_connection(self) -> bool:
        """Test connection to AWS."""
        try:
            client = self._get_ec2_client()
            client.describe_instances(MaxResults=5)
            return True
        except Exception as e:
            print(f"AWS connection failed: {e}")
            return False

    def list_instances(self, region: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all EC2 instances."""
        try:
            client = self._get_ec2_client(region or "us-east-1")
            response = client.describe_instances()

            instances = []
            for reservation in response.get("Reservations", []):
                for instance in reservation.get("Instances", []):
                    instances.append(self.normalize_instance_data(instance))

            return instances
        except Exception as e:
            print(f"Failed to list AWS instances: {e}")
            return []

    def get_instance(self, instance_id: str) -> Dict[str, Any]:
        """Get specific EC2 instance."""
        try:
            client = self._get_ec2_client()
            response = client.describe_instances(InstanceIds=[instance_id])

            if response["Reservations"]:
                instance = response["Reservations"][0]["Instances"][0]
                return self.normalize_instance_data(instance)
            raise ValueError(f"Instance {instance_id} not found")
        except Exception as e:
            print(f"Failed to get AWS instance {instance_id}: {e}")
            raise

    def get_instance_metrics(
        self,
        instance_id: str,
        metric_type: str,
        start_time: datetime,
        end_time: datetime,
        period: int = 300
    ) -> List[Dict[str, Any]]:
        """Get CloudWatch metrics for EC2 instance."""
        try:
            client = self._get_cloudwatch_client()

            # Map metric types to CloudWatch metric names
            metric_map = {
                "cpu": "CPUUtilization",
                "memory": "MemoryUtilization",  # Requires CloudWatch agent
                "disk_io": "DiskReadBytes",
                "network_io": "NetworkIn"
            }

            metric_name = metric_map.get(metric_type, "CPUUtilization")

            response = client.get_metric_statistics(
                Namespace="AWS/EC2",
                MetricName=metric_name,
                Dimensions=[{"Name": "InstanceId", "Value": instance_id}],
                StartTime=start_time,
                EndTime=end_time,
                Period=period,
                Statistics=["Average", "Minimum", "Maximum"]
            )

            return [
                {
                    "timestamp": dp["Timestamp"],
                    "value": dp.get("Average", 0),
                    "min": dp.get("Minimum", 0),
                    "max": dp.get("Maximum", 0),
                }
                for dp in response.get("Datapoints", [])
            ]
        except Exception as e:
            print(f"Failed to get AWS metrics for {instance_id}: {e}")
            return []

    def stop_instance(self, instance_id: str) -> bool:
        """Stop an EC2 instance."""
        try:
            client = self._get_ec2_client()
            client.stop_instances(InstanceIds=[instance_id])
            return True
        except Exception as e:
            print(f"Failed to stop AWS instance {instance_id}: {e}")
            return False

    def start_instance(self, instance_id: str) -> bool:
        """Start an EC2 instance."""
        try:
            client = self._get_ec2_client()
            client.start_instances(InstanceIds=[instance_id])
            return True
        except Exception as e:
            print(f"Failed to start AWS instance {instance_id}: {e}")
            return False

    def resize_instance(self, instance_id: str, new_instance_type: str) -> bool:
        """Resize an EC2 instance."""
        try:
            client = self._get_ec2_client()
            # Stop instance first
            client.stop_instances(InstanceIds=[instance_id])
            # Wait for stopped state (simplified)
            client.get_waiter("instance_stopped").wait(InstanceIds=[instance_id])
            # Modify instance type
            client.modify_instance_attribute(
                InstanceId=instance_id,
                InstanceType={"Value": new_instance_type}
            )
            # Start instance
            client.start_instances(InstanceIds=[instance_id])
            return True
        except Exception as e:
            print(f"Failed to resize AWS instance {instance_id}: {e}")
            return False

    def get_cost_data(
        self,
        start_date: datetime,
        end_date: datetime,
        granularity: str = "DAILY"
    ) -> Dict[str, Any]:
        """Get cost data from AWS Cost Explorer."""
        try:
            client = self._get_ce_client()

            response = client.get_cost_and_usage(
                TimePeriod={
                    "Start": start_date.strftime("%Y-%m-%d"),
                    "End": end_date.strftime("%Y-%m-%d")
                },
                Granularity=granularity,
                Metrics=["UnblendedCost"],
                GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}]
            )

            total_cost = 0.0
            by_service = {}

            for result in response.get("ResultsByTime", []):
                for group in result.get("Groups", []):
                    service = group["Keys"][0]
                    cost = float(group["Metrics"]["UnblendedCost"]["Amount"])
                    by_service[service] = by_service.get(service, 0.0) + cost
                    total_cost += cost

            return {
                "total_cost": total_cost,
                "by_service": by_service,
                "currency": "USD"
            }
        except Exception as e:
            print(f"Failed to get AWS cost data: {e}")
            return {"total_cost": 0.0, "by_service": {}}

    def normalize_instance_data(self, raw_instance: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize AWS EC2 instance data to common format."""
        try:
            # Extract tags
            tags = {}
            for tag in raw_instance.get("Tags", []):
                tags[tag["Key"]] = tag["Value"]

            # Get name from tags
            name = tags.get("Name", raw_instance.get("InstanceId", "unnamed"))

            # Estimate monthly cost
            instance_type = raw_instance["InstanceType"]
            monthly_cost = self._estimate_monthly_cost(instance_type)

            return {
                "provider_instance_id": raw_instance["InstanceId"],
                "name": name,
                "status": raw_instance["State"]["Name"],
                "instance_type": instance_type,
                "vcpus": None,  # Would need to lookup instance type details
                "ram_mb": None,
                "disk_gb": None,
                "region": raw_instance.get("Placement", {}).get("AvailabilityZone", "")[:-1],
                "availability_zone": raw_instance.get("Placement", {}).get("AvailabilityZone"),
                "private_ip": raw_instance.get("PrivateIpAddress"),
                "public_ip": raw_instance.get("PublicIpAddress"),
                "launch_time": raw_instance.get("LaunchTime"),
                "tags": tags,
                "monthly_cost": monthly_cost,
            }
        except Exception as e:
            print(f"Failed to normalize AWS instance data: {e}")
            raise

    def _estimate_monthly_cost(self, instance_type: str) -> float:
        """Estimate monthly cost for AWS EC2 instance type.

        These are approximate On-Demand prices in USD (us-east-1 region).
        Actual costs may vary by region, reserved instances, and spot pricing.
        """
        # Simplified pricing map for common instance types (monthly cost = hourly * 730)
        pricing = {
            # t2 instances (burstable)
            't2.micro': 8.47,
            't2.small': 16.79,
            't2.medium': 33.58,
            't2.large': 67.16,
            't2.xlarge': 134.32,
            't2.2xlarge': 268.64,

            # t3 instances (burstable)
            't3.micro': 7.52,
            't3.small': 15.04,
            't3.medium': 30.08,
            't3.large': 60.16,
            't3.xlarge': 120.32,
            't3.2xlarge': 240.64,

            # m5 instances (general purpose)
            'm5.large': 70.08,
            'm5.xlarge': 140.16,
            'm5.2xlarge': 280.32,
            'm5.4xlarge': 560.64,
            'm5.8xlarge': 1121.28,
            'm5.12xlarge': 1681.92,
            'm5.16xlarge': 2242.56,
            'm5.24xlarge': 3363.84,

            # c5 instances (compute optimized)
            'c5.large': 62.05,
            'c5.xlarge': 124.10,
            'c5.2xlarge': 248.20,
            'c5.4xlarge': 496.40,
            'c5.9xlarge': 1116.90,
            'c5.12xlarge': 1489.20,
            'c5.18xlarge': 2233.80,
            'c5.24xlarge': 2978.40,

            # r5 instances (memory optimized)
            'r5.large': 91.25,
            'r5.xlarge': 182.50,
            'r5.2xlarge': 365.00,
            'r5.4xlarge': 730.00,
            'r5.8xlarge': 1460.00,
            'r5.12xlarge': 2190.00,
            'r5.16xlarge': 2920.00,
            'r5.24xlarge': 4380.00,
        }

        # Return estimated cost or a default if instance type not in map
        return pricing.get(instance_type, 50.0)
