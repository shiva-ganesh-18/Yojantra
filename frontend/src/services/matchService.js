import apiClient from './api';

export const matchService = {
  findMatches: async (refresh = false) => {
    const response = await apiClient.post('/schemes/match', { refresh });
    return response.data;
  },

  getRecommended: async () => {
    const response = await apiClient.get('/schemes/recommended');
    return response.data;
  },

  compareSchemes: async (schemeIds) => {
    const response = await apiClient.post('/schemes/compare', { scheme_ids: schemeIds });
    return response.data;
  },

  toggleBookmark: async (schemeId) => {
    const response = await apiClient.post(`/schemes/${schemeId}/bookmark`);
    return response.data;
  },
};

export default matchService;
