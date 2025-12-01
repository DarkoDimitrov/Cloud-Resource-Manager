import React, { useEffect, useState } from 'react';
import { getProviders, createProvider, syncProviderInstances, testProviderConnection, deleteProvider } from '../services/api';
import type { Provider } from '../services/api';

export default function Providers() {
  const [providers, setProviders] = useState<Provider[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAddForm, setShowAddForm] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    provider_type: 'openstack',
    // OpenStack fields
    auth_url: '',
    username: '',
    password: '',
    project_name: '',
    user_domain_name: 'Default',
    project_domain_name: 'Default',
    // AWS fields
    access_key_id: '',
    secret_access_key: '',
    region: 'us-east-1',
    // Azure fields
    tenant_id: '',
    client_id: '',
    client_secret: '',
    subscription_id: '',
    // GCP fields
    project_id: '',
    service_account_json: '',
    gcp_region: 'us-central1',
  });

  useEffect(() => {
    loadProviders();
  }, []);

  const loadProviders = async () => {
    setLoading(true);
    try {
      const data = await getProviders();
      setProviders(data);
    } catch (error) {
      console.error('Failed to load providers:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      let credentials = {};
      let regions: string[] = [];

      // Build credentials object based on provider type
      if (formData.provider_type === 'openstack') {
        credentials = {
          auth_url: formData.auth_url,
          username: formData.username,
          password: formData.password,
          project_name: formData.project_name,
          user_domain_name: formData.user_domain_name,
          project_domain_name: formData.project_domain_name,
        };
        regions = ['RegionOne'];
      } else if (formData.provider_type === 'aws') {
        credentials = {
          access_key_id: formData.access_key_id,
          secret_access_key: formData.secret_access_key,
          region: formData.region,
        };
        regions = [formData.region];
      } else if (formData.provider_type === 'azure') {
        credentials = {
          tenant_id: formData.tenant_id,
          client_id: formData.client_id,
          client_secret: formData.client_secret,
          subscription_id: formData.subscription_id,
        };
        regions = ['eastus'];
      } else if (formData.provider_type === 'gcp') {
        credentials = {
          project_id: formData.project_id,
          service_account_json: formData.service_account_json,
          region: formData.gcp_region,
        };
        regions = [formData.gcp_region];
      }

      await createProvider({
        name: formData.name,
        provider_type: formData.provider_type,
        credentials,
        regions,
      });
      setShowAddForm(false);
      setFormData({
        name: '',
        provider_type: 'openstack',
        auth_url: '',
        username: '',
        password: '',
        project_name: '',
        user_domain_name: 'Default',
        project_domain_name: 'Default',
        access_key_id: '',
        secret_access_key: '',
        region: 'us-east-1',
        tenant_id: '',
        client_id: '',
        client_secret: '',
        subscription_id: '',
        project_id: '',
        service_account_json: '',
        gcp_region: 'us-central1',
      });
      loadProviders();
    } catch (error) {
      console.error('Failed to create provider:', error);
      alert('Failed to create provider. Check console for details.');
    }
  };

  const handleSync = async (providerId: string) => {
    try {
      await syncProviderInstances(providerId);
      alert('Sync started successfully!');
      loadProviders();
    } catch (error) {
      console.error('Failed to sync provider:', error);
      alert('Failed to sync provider');
    }
  };

  const handleTest = async (providerId: string) => {
    try {
      const result = await testProviderConnection(providerId);
      alert(`Connection test: ${result.status}\n${result.message}`);
    } catch (error) {
      console.error('Failed to test connection:', error);
      alert('Connection test failed');
    }
  };

  const handleDelete = async (providerId: string, providerName: string) => {
    if (window.confirm(`Are you sure you want to delete provider "${providerName}"?`)) {
      try {
        await deleteProvider(providerId);
        loadProviders();
      } catch (error) {
        console.error('Failed to delete provider:', error);
        alert('Failed to delete provider');
      }
    }
  };

  if (loading) {
    return <div className="flex items-center justify-center h-64">Loading...</div>;
  }

  return (
    <div className="px-4 sm:px-6 lg:px-8">
      <div className="sm:flex sm:items-center">
        <div className="sm:flex-auto">
          <h1 className="text-3xl font-bold text-gray-900">Cloud Providers</h1>
          <p className="mt-2 text-sm text-gray-700">
            Manage your cloud provider connections
          </p>
        </div>
        <div className="mt-4 sm:mt-0 sm:ml-16 sm:flex-none">
          <button
            onClick={() => setShowAddForm(!showAddForm)}
            className="inline-flex items-center justify-center rounded-md border border-transparent bg-primary-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-primary-700"
          >
            Add Provider
          </button>
        </div>
      </div>

      {/* Add Provider Form */}
      {showAddForm && (
        <div className="mt-8 bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Add New Provider</h3>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <label className="block text-sm font-medium text-gray-700">Name</label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm px-3 py-2 border"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Provider Type</label>
                <select
                  value={formData.provider_type}
                  onChange={(e) => setFormData({ ...formData, provider_type: e.target.value })}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm px-3 py-2 border"
                >
                  <option value="openstack">OpenStack</option>
                  <option value="aws">AWS</option>
                  <option value="azure">Azure</option>
                  <option value="gcp">Google Cloud Platform</option>
                </select>
              </div>
            </div>

            {formData.provider_type === 'openstack' && (
              <>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Auth URL</label>
                  <input
                    type="text"
                    required
                    value={formData.auth_url}
                    onChange={(e) => setFormData({ ...formData, auth_url: e.target.value })}
                    placeholder="https://openstack.example.com:5000/v3"
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm px-3 py-2 border"
                  />
                </div>
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Username</label>
                    <input
                      type="text"
                      required
                      value={formData.username}
                      onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm px-3 py-2 border"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Password</label>
                    <input
                      type="password"
                      required
                      value={formData.password}
                      onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm px-3 py-2 border"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Project Name</label>
                  <input
                    type="text"
                    required
                    value={formData.project_name}
                    onChange={(e) => setFormData({ ...formData, project_name: e.target.value })}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm px-3 py-2 border"
                  />
                </div>
              </>
            )}

            {formData.provider_type === 'aws' && (
              <>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Access Key ID</label>
                  <input
                    type="text"
                    required
                    value={formData.access_key_id}
                    onChange={(e) => setFormData({ ...formData, access_key_id: e.target.value })}
                    placeholder="AKIAIOSFODNN7EXAMPLE"
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm px-3 py-2 border"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Secret Access Key</label>
                  <input
                    type="password"
                    required
                    value={formData.secret_access_key}
                    onChange={(e) => setFormData({ ...formData, secret_access_key: e.target.value })}
                    placeholder="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm px-3 py-2 border"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Default Region</label>
                  <select
                    value={formData.region}
                    onChange={(e) => setFormData({ ...formData, region: e.target.value })}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm px-3 py-2 border"
                  >
                    <option value="us-east-1">US East (N. Virginia)</option>
                    <option value="us-east-2">US East (Ohio)</option>
                    <option value="us-west-1">US West (N. California)</option>
                    <option value="us-west-2">US West (Oregon)</option>
                    <option value="eu-west-1">EU (Ireland)</option>
                    <option value="eu-central-1">EU (Frankfurt)</option>
                    <option value="ap-southeast-1">Asia Pacific (Singapore)</option>
                    <option value="ap-northeast-1">Asia Pacific (Tokyo)</option>
                  </select>
                </div>
              </>
            )}

            {formData.provider_type === 'azure' && (
              <>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Tenant ID</label>
                  <input
                    type="text"
                    required
                    value={formData.tenant_id}
                    onChange={(e) => setFormData({ ...formData, tenant_id: e.target.value })}
                    placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm px-3 py-2 border"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Client ID (Application ID)</label>
                  <input
                    type="text"
                    required
                    value={formData.client_id}
                    onChange={(e) => setFormData({ ...formData, client_id: e.target.value })}
                    placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm px-3 py-2 border"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Client Secret</label>
                  <input
                    type="password"
                    required
                    value={formData.client_secret}
                    onChange={(e) => setFormData({ ...formData, client_secret: e.target.value })}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm px-3 py-2 border"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Subscription ID</label>
                  <input
                    type="text"
                    required
                    value={formData.subscription_id}
                    onChange={(e) => setFormData({ ...formData, subscription_id: e.target.value })}
                    placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm px-3 py-2 border"
                  />
                </div>
              </>
            )}

            {formData.provider_type === 'gcp' && (
              <>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Project ID</label>
                  <input
                    type="text"
                    required
                    value={formData.project_id}
                    onChange={(e) => setFormData({ ...formData, project_id: e.target.value })}
                    placeholder="my-gcp-project-12345"
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm px-3 py-2 border"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Service Account JSON</label>
                  <textarea
                    required
                    value={formData.service_account_json}
                    onChange={(e) => setFormData({ ...formData, service_account_json: e.target.value })}
                    placeholder='{"type": "service_account", "project_id": "...", "private_key": "...", ...}'
                    rows={6}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm px-3 py-2 border font-mono text-xs"
                  />
                  <p className="mt-1 text-xs text-gray-500">Paste the entire JSON key file contents from GCP Console</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Default Region</label>
                  <select
                    value={formData.gcp_region}
                    onChange={(e) => setFormData({ ...formData, gcp_region: e.target.value })}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm px-3 py-2 border"
                  >
                    <option value="us-central1">us-central1 (Iowa)</option>
                    <option value="us-east1">us-east1 (South Carolina)</option>
                    <option value="us-west1">us-west1 (Oregon)</option>
                    <option value="europe-west1">europe-west1 (Belgium)</option>
                    <option value="asia-east1">asia-east1 (Taiwan)</option>
                  </select>
                </div>
              </>
            )}

            <div className="flex justify-end space-x-3">
              <button
                type="button"
                onClick={() => setShowAddForm(false)}
                className="inline-flex justify-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="inline-flex justify-center rounded-md border border-transparent bg-primary-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-primary-700"
              >
                Add Provider
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Providers List */}
      <div className="mt-8 flex flex-col">
        <div className="-my-2 -mx-4 overflow-x-auto sm:-mx-6 lg:-mx-8">
          <div className="inline-block min-w-full py-2 align-middle md:px-6 lg:px-8">
            <div className="overflow-hidden shadow ring-1 ring-black ring-opacity-5 md:rounded-lg">
              <table className="min-w-full divide-y divide-gray-300 bg-white">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">Name</th>
                    <th className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">Type</th>
                    <th className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">Instances</th>
                    <th className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">Cost</th>
                    <th className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">Status</th>
                    <th className="relative py-3.5 pl-3 pr-4 sm:pr-6">
                      <span className="sr-only">Actions</span>
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {providers.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="px-3 py-8 text-center text-sm text-gray-500">
                        No providers configured. Click "Add Provider" to get started.
                      </td>
                    </tr>
                  ) : (
                    providers.map((provider) => (
                      <tr key={provider.id}>
                        <td className="whitespace-nowrap px-3 py-4 text-sm font-medium text-gray-900">
                          {provider.name}
                        </td>
                        <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500 capitalize">
                          {provider.provider_type}
                        </td>
                        <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                          {provider.instance_count || 0}
                        </td>
                        <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                          ${provider.monthly_cost?.toFixed(2) || '0.00'}
                        </td>
                        <td className="whitespace-nowrap px-3 py-4 text-sm">
                          <span className={`inline-flex rounded-full px-2 text-xs font-semibold leading-5 ${
                            provider.enabled ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                          }`}>
                            {provider.enabled ? 'Active' : 'Inactive'}
                          </span>
                        </td>
                        <td className="relative whitespace-nowrap py-4 pl-3 pr-4 text-right text-sm font-medium sm:pr-6">
                          <button
                            onClick={() => handleTest(provider.id)}
                            className="text-primary-600 hover:text-primary-900 mr-4"
                          >
                            Test
                          </button>
                          <button
                            onClick={() => handleSync(provider.id)}
                            className="text-primary-600 hover:text-primary-900 mr-4"
                          >
                            Sync
                          </button>
                          <button
                            onClick={() => handleDelete(provider.id, provider.name)}
                            className="text-red-600 hover:text-red-900"
                          >
                            Delete
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
