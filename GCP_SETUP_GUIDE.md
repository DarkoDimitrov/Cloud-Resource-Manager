# Google Cloud Platform (GCP) Setup Guide

Your Cloud Resource Manager now supports **Google Cloud Platform** in addition to OpenStack, AWS, and Azure!

## What Was Added

### Backend Changes
1. **GCP Adapter** - Full implementation at [`backend/app/adapters/gcp.py`](backend/app/adapters/gcp.py)
   - Service account authentication
   - List, get, start, stop, and resize VM instances
   - Metrics collection from Cloud Monitoring
   - Cost estimation
   - Data normalization to common format

2. **Dependencies** - Added to [`requirements.txt`](backend/requirements.txt):
   - `google-cloud-compute==1.14.1` - Compute Engine API
   - `google-cloud-monitoring==2.16.0` - Cloud Monitoring API

3. **Adapter Registration** - Updated [`backend/app/adapters/__init__.py`](backend/app/adapters/__init__.py)
   - Registered GCP adapter in factory method

### Frontend Changes
1. **Provider Form** - Updated [`frontend/src/components/Providers.tsx`](frontend/src/components/Providers.tsx)
   - Added "Google Cloud Platform" option to provider type dropdown
   - Added GCP-specific form fields:
     - Project ID
     - Service Account JSON
     - Default Region

2. **Instance Details Page** - New component at [`frontend/src/components/InstanceDetails.tsx`](frontend/src/components/InstanceDetails.tsx)
   - Comprehensive instance information display
   - Compute resources, network info, tags, and cost details
   - Accessible by clicking "Details" button on instance cards

3. **Routing** - Updated [`frontend/src/App.tsx`](frontend/src/App.tsx)
   - Added route for `/instances/:id` to show instance details

## How to Set Up GCP

### Step 1: Create a GCP Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click on the project dropdown at the top
3. Click "NEW PROJECT"
4. Enter a project name and click "CREATE"
5. Note your **Project ID** (not the project name) - you'll need this later

### Step 2: Enable Required APIs

1. Go to [APIs & Services > Library](https://console.cloud.google.com/apis/library)
2. Enable the following APIs:
   - **Compute Engine API** (for managing VMs)
   - **Cloud Monitoring API** (for metrics)

### Step 3: Create a Service Account

1. Go to [IAM & Admin > Service Accounts](https://console.cloud.google.com/iam-admin/serviceaccounts)
2. Click "CREATE SERVICE ACCOUNT"
3. Enter a name like "cloud-resource-manager"
4. Click "CREATE AND CONTINUE"
5. Grant the following roles:
   - **Compute Admin** (roles/compute.admin) - To manage VM instances
   - **Monitoring Viewer** (roles/monitoring.viewer) - To read metrics
6. Click "CONTINUE" then "DONE"

### Step 4: Create and Download Service Account Key

1. Find your newly created service account in the list
2. Click on it to open details
3. Go to the "KEYS" tab
4. Click "ADD KEY" > "Create new key"
5. Select "JSON" format
6. Click "CREATE"
7. The JSON key file will be downloaded to your computer
8. **Keep this file secure!** It contains credentials to access your GCP project

### Step 5: Add GCP Provider in the App

1. Open your Cloud Resource Manager UI at [http://localhost:3000](http://localhost:3000)
2. Navigate to **Providers** page
3. Click "Add Provider"
4. Fill in the form:
   - **Name**: Give it a friendly name (e.g., "My GCP Project")
   - **Provider Type**: Select "Google Cloud Platform"
   - **Project ID**: Enter your GCP Project ID from Step 1
   - **Service Account JSON**: Open the JSON key file you downloaded and copy/paste the **entire JSON contents**
   - **Default Region**: Select your preferred region (e.g., us-central1)
5. Click "Add Provider"

### Step 6: Test and Sync

1. After adding the provider, click **"Test"** to verify the connection
2. If successful, click **"Sync"** to discover your GCP VM instances
3. Navigate to the **Instances** page to see your GCP VMs

## Supported Features

### ✅ Fully Implemented
- **VM Discovery**: Lists all Compute Engine instances across all zones
- **Instance Details**: Get comprehensive information about any VM
- **Start/Stop**: Power on/off instances
- **Resize**: Change instance machine type
- **Metrics**: Collect CPU, memory, disk, and network metrics from Cloud Monitoring
- **Cost Estimation**: Approximate monthly costs based on machine types
- **Status Monitoring**: Track instance power states (running, stopped, etc.)

### 📊 Metrics Available
- CPU utilization (%)
- Memory utilization (bytes)
- Network traffic (in/out bytes)
- Disk I/O (read/write bytes)

### 💰 Cost Tracking
The GCP adapter includes cost estimation based on standard machine types. Note that actual costs may vary based on:
- Committed use discounts
- Sustained use discounts
- Preemptible/Spot instances
- Region-specific pricing

## Troubleshooting

### Problem: "GCP connection test failed"

**Possible Causes**:
1. Service account JSON is invalid or incomplete
2. Required APIs are not enabled
3. Service account lacks necessary permissions
4. Project ID is incorrect

**Solutions**:
1. Verify the entire JSON key is copied correctly (should start with `{` and end with `}`)
2. Go to [APIs & Services](https://console.cloud.google.com/apis) and ensure Compute Engine API and Cloud Monitoring API are enabled
3. Check service account has "Compute Admin" and "Monitoring Viewer" roles
4. Double-check the Project ID (not the project name or number)

### Problem: "No instances found"

**Possible Causes**:
1. No VM instances exist in the project
2. Service account doesn't have permission to list instances
3. Instances are in zones/regions not accessible

**Solutions**:
1. Create some test VMs in GCP Compute Engine
2. Verify service account has "Compute Admin" or "Compute Viewer" role
3. Check that instances exist: `gcloud compute instances list --project=YOUR_PROJECT_ID`

### Problem: "Metrics not available"

**Possible Causes**:
1. Cloud Monitoring API not enabled
2. Service account lacks monitoring permissions
3. Instance is too new (metrics take 1-2 minutes to appear)

**Solutions**:
1. Enable Cloud Monitoring API in [API Library](https://console.cloud.google.com/apis/library/monitoring.googleapis.com)
2. Grant "Monitoring Viewer" role to service account
3. Wait a few minutes after instance creation for metrics to populate

## Security Best Practices

🔒 **Important Security Notes**:

1. **Never commit service account keys to Git**
   - The JSON key file grants full access to your GCP project
   - Add `*.json` to `.gitignore`

2. **Use principle of least privilege**
   - Only grant necessary roles to the service account
   - For read-only operations, use "Compute Viewer" instead of "Compute Admin"

3. **Rotate keys regularly**
   - Create new service account keys periodically
   - Delete old keys after rotation

4. **Monitor service account usage**
   - Check [Cloud Audit Logs](https://console.cloud.google.com/logs) for service account activity
   - Set up alerts for unusual access patterns

5. **Enable MFA on your Google account**
   - Protects against unauthorized project access

## Cost Management

### Viewing Costs in GCP

1. Go to [Billing > Reports](https://console.cloud.google.com/billing)
2. Filter by:
   - Project
   - Service (select "Compute Engine")
   - SKU (specific machine types)

### Cost Optimization Tips

1. **Right-size instances**: Use the recommendations in the app to identify oversized VMs
2. **Use preemptible VMs**: For fault-tolerant workloads, save up to 80%
3. **Committed use discounts**: For predictable workloads, save up to 57%
4. **Stop unused instances**: The app can help identify idle instances
5. **Use custom machine types**: Match CPU/RAM to actual needs

## Advanced Configuration

### Accessing Multiple GCP Projects

To manage VMs across multiple GCP projects:

1. Create separate service accounts in each project
2. Add each project as a separate provider in the app
3. Each provider will appear independently in the dashboard

### Using Existing Service Accounts

If you already have a service account for other tools:

1. Go to [Service Accounts](https://console.cloud.google.com/iam-admin/serviceaccounts)
2. Find your existing service account
3. Verify it has required roles (Compute Admin, Monitoring Viewer)
4. Create a new JSON key for it
5. Use that key in the Cloud Resource Manager

### Regional Filtering

The app supports region filtering. To see instances in specific regions:

1. Navigate to Instances page
2. Use the filters to select specific regions
3. Or set the default region when adding the provider

## Instance Details Page

When you click "Details" on any instance card, you'll see:

### Overview Cards
- **Instance Type**: Machine type (e.g., n1-standard-2)
- **Region**: Geographic location
- **Provider**: Shows "gcp"
- **Monthly Cost**: Estimated cost

### Compute Resources
- vCPUs count
- RAM in GB
- Availability Zone

### Network Information
- Private IP address
- Public IP address (if assigned)

### Tags
- All labels/tags applied to the instance

### Additional Information
- Provider instance ID
- Launch time
- Status

## What's Next?

Now that GCP is set up:

1. ✅ Test the connection
2. ✅ Sync instances
3. ✅ View instances on the Dashboard
4. ✅ Click "Details" on any instance to see comprehensive information
5. ✅ Use AI Chat to ask about your GCP resources
6. ✅ View cost forecasts including GCP costs
7. ✅ Get AI-powered optimization recommendations

## API Reference

### GCP Adapter Methods

The GCP adapter (`backend/app/adapters/gcp.py`) implements:

```python
# Connection test
test_connection() -> bool

# Instance management
list_instances(region: Optional[str] = None) -> List[Dict]
get_instance(instance_id: str) -> Dict
start_instance(instance_id: str) -> bool
stop_instance(instance_id: str) -> bool
resize_instance(instance_id: str, new_instance_type: str) -> bool

# Metrics
get_instance_metrics(
    instance_id: str,
    metric_type: str,
    start_time: datetime,
    end_time: datetime,
    period: int = 300
) -> List[Dict]

# Data normalization
normalize_instance_data(raw_instance: Any, status: str = None) -> Dict
```

### Instance ID Format

GCP instance IDs in the app use the format: `{zone}/{instance_name}`

Example: `us-central1-a/web-server-01`

## Support Resources

- **GCP Documentation**: https://cloud.google.com/compute/docs
- **Service Account Best Practices**: https://cloud.google.com/iam/docs/best-practices-service-accounts
- **Compute Engine Pricing**: https://cloud.google.com/compute/pricing
- **Cloud Monitoring Docs**: https://cloud.google.com/monitoring/docs

---

**You can now manage GCP resources alongside OpenStack, AWS, and Azure!** 🚀
