import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Types
export interface Provider {
  id: string;
  name: string;
  provider_type: string;
  regions: string[];
  enabled: boolean;
  last_sync?: string;
  created_at: string;
  updated_at: string;
  instance_count?: number;
  monthly_cost?: number;
}

export interface Instance {
  id: string;
  provider: string;
  provider_id: string;
  provider_instance_id: string;
  name: string;
  status: string;
  instance_type: string;
  vcpus?: number;
  ram_mb?: number;
  disk_gb?: number;
  region: string;
  availability_zone?: string;
  private_ip?: string;
  public_ip?: string;
  launch_time?: string;
  tags: Record<string, any>;
  monthly_cost: number;
  last_updated: string;
}

export interface InstanceStats {
  total_instances: number;
  running_instances: number;
  stopped_instances: number;
  total_monthly_cost: number;
  by_provider: Record<string, number>;
  by_region: Record<string, number>;
}

export interface Anomaly {
  id: string;
  instance_id: string;
  metric_type: string;
  severity: string;
  anomaly_score: number;
  detected_at: string;
  title: string;
  description: string;
  recommended_action?: string;
  status: string;
}

export interface CostForecast {
  status: string;
  provider: string;
  forecast_days: number;
  predictions: Array<{
    date: string;
    cost: number;
    lower_bound: number;
    upper_bound: number;
  }>;
  trend: string;
  budget_alert: boolean;
  projected_overrun: number;
}

// API Functions

// Health Check
export const checkHealth = async () => {
  const response = await api.get('/');
  return response.data;
};

// Providers
export const getProviders = async (): Promise<Provider[]> => {
  const response = await api.get('/providers');
  return response.data;
};

export const createProvider = async (provider: any): Promise<Provider> => {
  const response = await api.post('/providers', provider);
  return response.data;
};

export const testProviderConnection = async (providerId: string) => {
  const response = await api.post(`/providers/${providerId}/test`);
  return response.data;
};

export const syncProviderInstances = async (providerId: string) => {
  const response = await api.post(`/providers/${providerId}/sync`);
  return response.data;
};

export const deleteProvider = async (providerId: string) => {
  await api.delete(`/providers/${providerId}`);
};

// Instances
export const getInstances = async (params?: {
  skip?: number;
  limit?: number;
  provider?: string;
  status?: string;
  region?: string;
  search?: string;
}) => {
  const response = await api.get('/instances', { params });
  return response.data;
};

export const getInstance = async (instanceId: string): Promise<Instance> => {
  const response = await api.get(`/instances/${instanceId}`);
  return response.data;
};

export const getInstanceStats = async (): Promise<InstanceStats> => {
  const response = await api.get('/instances/stats');
  return response.data;
};

export const startInstance = async (instanceId: string) => {
  const response = await api.post(`/instances/${instanceId}/start`);
  return response.data;
};

export const stopInstance = async (instanceId: string) => {
  const response = await api.post(`/instances/${instanceId}/stop`);
  return response.data;
};

export const refreshInstance = async (instanceId: string) => {
  const response = await api.post(`/instances/${instanceId}/refresh`);
  return response.data;
};

// AI Features
export const queryAI = async (query: string) => {
  const response = await api.post('/ai/query', { query });
  return response.data;
};

export const getAnomalies = async (params?: {
  severity?: string;
  last_hours?: number;
}) => {
  const response = await api.get('/ai/anomalies', { params });
  return response.data;
};

export const detectAnomalies = async (instanceId: string, metricType: string = 'cpu') => {
  const response = await api.post(`/ai/anomalies/detect/${instanceId}`, null, {
    params: { metric_type: metricType }
  });
  return response.data;
};

export const getCostForecast = async (params?: {
  provider?: string;
  days?: number;
}): Promise<CostForecast> => {
  const response = await api.get('/ai/forecast', { params });
  return response.data;
};

export default api;
