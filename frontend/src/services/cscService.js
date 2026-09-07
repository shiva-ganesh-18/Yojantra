import apiClient from './api';

export const cscService = {
  getNearby: async (latitude, longitude, radiusKm = 15, services = null) => {
    const params = { lat: latitude, lng: longitude, radius_km: radiusKm };
    if (services && services.length) {
      params.services = services;
    }
    const response = await apiClient.get('/csc/nearby', { params });
    return response.data;
  },

  getByDistrict: async (state, district) => {
    const response = await apiClient.get('/csc/by-district', {
      params: { state, district },
    });
    return response.data;
  },
};

export default cscService;
