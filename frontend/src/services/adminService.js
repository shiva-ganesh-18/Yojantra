import apiClient from './api';

export const adminService = {
  getDashboardMetrics: async () => {
    const response = await apiClient.get('/admin/analytics/dashboard');
    return response.data;
  },

  getBiasReport: async () => {
    const response = await apiClient.get('/admin/analytics/bias');
    return response.data;
  },

  listUsers: async (page = 1, pageSize = 20) => {
    const response = await apiClient.get('/admin/users', {
      params: { page, page_size: pageSize },
    });
    return response.data;
  },

  listSchemes: async () => {
    const response = await apiClient.get('/admin/schemes');
    return response.data;
  },

  triggerMatchingAll: async () => {
    const response = await apiClient.post('/admin/schemes/match-all');
    return response.data;
  },
};

export default adminService;
