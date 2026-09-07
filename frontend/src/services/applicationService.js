import apiClient from './api';

export const applicationService = {
  listApplications: async (status) => {
    const response = await apiClient.get('/applications', { params: status ? { status } : {} });
    return response.data;
  },

  getApplication: async (id) => {
    const response = await apiClient.get(`/applications/${id}`);
    return response.data;
  },

  createApplication: async (applicationData) => {
    const response = await apiClient.post('/applications', applicationData);
    return response.data;
  },

  updateApplication: async (id, updateData) => {
    const response = await apiClient.put(`/applications/${id}`, updateData);
    return response.data;
  },

  submitApplication: async (id) => {
    const response = await apiClient.post(`/applications/${id}/submit`);
    return response.data;
  },
};

export default applicationService;
