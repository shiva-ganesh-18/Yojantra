import apiClient from './api';

export const schemeService = {
  listSchemes: async (params = {}) => {
    const response = await apiClient.get('/schemes', { params });
    return response.data;
  },

  getScheme: async (id) => {
    const response = await apiClient.get(`/schemes/${id}`);
    return response.data;
  },

  createScheme: async (schemeData) => {
    const response = await apiClient.post('/schemes', schemeData);
    return response.data;
  },
};

export default schemeService;
