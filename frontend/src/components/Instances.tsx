import React, { useEffect, useState } from 'react';
import { getInstances, startInstance, stopInstance } from '../services/api';
import type { Instance } from '../services/api';

export default function Instances() {
  const [instances, setInstances] = useState<Instance[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState({
    status: '',
    search: '',
  });

  useEffect(() => {
    loadInstances();
  }, []);

  const loadInstances = async () => {
    setLoading(true);
    try {
      const data = await getInstances({
        status: filter.status || undefined,
        search: filter.search || undefined,
      });
      setInstances(data.instances || []);
    } catch (error) {
      console.error('Failed to load instances:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleStart = async (instanceId: string) => {
    try {
      await startInstance(instanceId);
      alert('Instance start initiated');
      loadInstances();
    } catch (error) {
      console.error('Failed to start instance:', error);
      alert('Failed to start instance');
    }
  };

  const handleStop = async (instanceId: string) => {
    try {
      await stopInstance(instanceId);
      alert('Instance stop initiated');
      loadInstances();
    } catch (error) {
      console.error('Failed to stop instance:', error);
      alert('Failed to stop instance');
    }
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'running':
      case 'active':
        return 'bg-green-100 text-green-800';
      case 'stopped':
      case 'shutoff':
        return 'bg-red-100 text-red-800';
      case 'starting':
      case 'stopping':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return <div className="flex items-center justify-center h-64">Loading instances...</div>;
  }

  return (
    <div className="px-4 sm:px-6 lg:px-8">
      <div className="sm:flex sm:items-center">
        <div className="sm:flex-auto">
          <h1 className="text-3xl font-bold text-gray-900">Instances</h1>
          <p className="mt-2 text-sm text-gray-700">
            View and manage your cloud instances
          </p>
        </div>
        <div className="mt-4 sm:mt-0 sm:ml-16 sm:flex-none">
          <button
            onClick={loadInstances}
            className="inline-flex items-center justify-center rounded-md border border-transparent bg-primary-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-primary-700"
          >
            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Refresh
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="mt-6 flex gap-4">
        <div className="flex-1 max-w-lg">
          <input
            type="text"
            placeholder="Search instances..."
            value={filter.search}
            onChange={(e) => setFilter({ ...filter, search: e.target.value })}
            onKeyPress={(e) => e.key === 'Enter' && loadInstances()}
            className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm px-3 py-2 border"
          />
        </div>
        <select
          value={filter.status}
          onChange={(e) => setFilter({ ...filter, status: e.target.value })}
          className="rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm px-3 py-2 border"
        >
          <option value="">All Status</option>
          <option value="running">Running</option>
          <option value="stopped">Stopped</option>
          <option value="shutoff">Shutoff</option>
        </select>
        <button
          onClick={loadInstances}
          className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
        >
          Apply
        </button>
      </div>

      {/* Instances Grid */}
      <div className="mt-8 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {instances.length === 0 ? (
          <div className="col-span-full text-center py-12 bg-white rounded-lg shadow">
            <svg
              className="mx-auto h-12 w-12 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01"
              />
            </svg>
            <p className="mt-2 text-sm text-gray-500">No instances found</p>
            <p className="text-xs text-gray-400">Add a provider and sync to see instances</p>
          </div>
        ) : (
          instances.map((instance) => (
            <div key={instance.id} className="bg-white overflow-hidden shadow rounded-lg">
              <div className="p-5">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-medium text-gray-900 truncate">{instance.name}</h3>
                  <span className={`inline-flex rounded-full px-2 text-xs font-semibold leading-5 ${getStatusColor(instance.status)}`}>
                    {instance.status}
                  </span>
                </div>
                <div className="mt-4 space-y-2">
                  <div className="flex items-center text-sm text-gray-500">
                    <svg className="flex-shrink-0 mr-1.5 h-4 w-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
                    </svg>
                    {instance.instance_type}
                  </div>
                  <div className="flex items-center text-sm text-gray-500">
                    <svg className="flex-shrink-0 mr-1.5 h-4 w-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                    </svg>
                    {instance.region}
                  </div>
                  {instance.public_ip && (
                    <div className="flex items-center text-sm text-gray-500">
                      <svg className="flex-shrink-0 mr-1.5 h-4 w-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
                      </svg>
                      {instance.public_ip}
                    </div>
                  )}
                  <div className="flex items-center text-sm font-medium text-gray-900">
                    <svg className="flex-shrink-0 mr-1.5 h-4 w-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    ${instance.monthly_cost.toFixed(2)}/month
                  </div>
                </div>
              </div>
              <div className="bg-gray-50 px-5 py-3 flex justify-end space-x-3">
                {instance.status.toLowerCase() === 'running' ? (
                  <button
                    onClick={() => handleStop(instance.id)}
                    className="text-sm text-red-600 hover:text-red-900 font-medium"
                  >
                    Stop
                  </button>
                ) : (
                  <button
                    onClick={() => handleStart(instance.id)}
                    className="text-sm text-green-600 hover:text-green-900 font-medium"
                  >
                    Start
                  </button>
                )}
                <a
                  href={`/instances/${instance.id}`}
                  className="text-sm text-primary-600 hover:text-primary-900 font-medium"
                >
                  Details
                </a>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
