import apiClient from './api';

export const schemeService = {
  listSchemes: async (params = {}) => {
    const response = await apiClient.get('/schemes', { params });
    return response.data;
  },

  searchSchemes: async (params = {}) => {
    const response = await apiClient.get('/schemes', { params });
    const data = response.data;
    if (Array.isArray(data)) {
      return { items: data, total: data.length };
    }
    return data;
  },

  getScheme: async (id) => {
    const response = await apiClient.get(`/schemes/${id}`);
    return response.data;
  },

  createScheme: async (schemeData) => {
    const response = await apiClient.post('/schemes', schemeData);
    return response.data;
  },

  simulateLoan: async (schemeId, simulationParams) => {
    const response = await apiClient.post(`/schemes/${schemeId}/simulate-loan`, simulationParams);
    return response.data;
  },

  calculateEmi: async (calcParams) => {
    const response = await apiClient.post('/schemes/calculate-emi', calcParams);
    return response.data;
  },
};

export default schemeService;
