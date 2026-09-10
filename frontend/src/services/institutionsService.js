import apiClient from './api';

export const institutionsService = {
  getInstitutions: async (params = {}) => {
    const query = new URLSearchParams();
    if (params.q) query.append('q', params.q);
    if (params.state) query.append('state', params.state);
    if (params.district) query.append('district', params.district);
    if (params.city) query.append('city', params.city);
    if (params.institution_type) query.append('institution_type', params.institution_type);
    if (params.scheme_id) query.append('scheme_id', params.scheme_id);
    if (params.lat !== undefined && params.lat !== null) query.append('lat', params.lat);
    if (params.lng !== undefined && params.lng !== null) query.append('lng', params.lng);
    if (params.page) query.append('page', params.page);
    if (params.page_size) query.append('page_size', params.page_size || 50);

    const res = await apiClient.get(`/institutions?${query.toString()}`);
    return res.data;
  },

  getRecommendations: async (params = {}) => {
    const query = new URLSearchParams();
    if (params.scheme_id) query.append('scheme_id', params.scheme_id);
    if (params.state) query.append('state', params.state);
    if (params.district) query.append('district', params.district);
    if (params.city) query.append('city', params.city);
    if (params.institution_type) query.append('institution_type', params.institution_type);
    if (params.lat !== undefined && params.lat !== null) query.append('lat', params.lat);
    if (params.lng !== undefined && params.lng !== null) query.append('lng', params.lng);

    const res = await apiClient.get(`/institutions/recommendations?${query.toString()}`);
    return res.data;
  },

  getInstitution: async (id) => {
    const res = await apiClient.get(`/institutions/${id}`);
    return res.data;
  },

  requestInstitution: async (data) => {
    const res = await apiClient.post('/institutions/request', data);
    return res.data;
  },
};

export default institutionsService;

