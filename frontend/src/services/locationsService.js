import apiClient from './api';

export const locationsService = {
  getStates: async () => {
    const res = await apiClient.get('/locations/states');
    return res.data;
  },

  getDistricts: async (state) => {
    const res = await apiClient.get(`/locations/districts?state=${encodeURIComponent(state)}`);
    return res.data;
  },

  getCities: async ({ state, district, q } = {}) => {
    const params = new URLSearchParams();
    if (state) params.append('state', state);
    if (district) params.append('district', district);
    if (q) params.append('q', q);
    const queryStr = params.toString() ? `?${params.toString()}` : '';
    const res = await apiClient.get(`/locations/cities${queryStr}`);
    return res.data;
  },
};

export default locationsService;
