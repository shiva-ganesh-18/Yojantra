import apiClient from './api';

export const userService = {
  getProfile: async () => {
    const response = await apiClient.get('/users/me');
    return response.data;
  },

  updateProfile: async (userData) => {
    const response = await apiClient.put('/users/me', userData);
    return response.data;
  },

  getBusiness: async () => {
    const response = await apiClient.get('/users/me/business');
    return response.data;
  },

  saveBusiness: async (businessData) => {
    const response = await apiClient.post('/users/me/business', businessData);
    return response.data;
  },
};

export default userService;
