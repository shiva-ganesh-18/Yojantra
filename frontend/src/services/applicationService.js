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

  validateApplication: async (id) => {
    const response = await apiClient.get(`/applications/${id}/validate`);
    return response.data;
  },

  getApplicationChecklist: async (id) => {
    const response = await apiClient.get(`/applications/${id}/checklist`);
    return response.data;
  },

  listPartnerApplications: async (params = {}) => {
    const response = await apiClient.get('/admin/partner/applications', { params });
    return response.data;
  },

  getPartnerApplicationDetail: async (id) => {
    const response = await apiClient.get(`/admin/partner/applications/${id}`);
    return response.data;
  },

  submitPartnerAction: async (id, actionData) => {
    const response = await apiClient.post(`/admin/partner/applications/${id}/action`, actionData);
    return response.data;
  },

  getPartnerOverviewKPIs: async () => {
    const response = await apiClient.get('/admin/partner/overview');
    return response.data;
  },

  getApplicationTracking: async (id) => {
    const response = await apiClient.get(`/applications/${id}/tracking`);
    return response.data;
  },

  resolveDocumentRequest: async (id, data) => {
    const response = await apiClient.post(`/applications/${id}/resolve-document-request`, data);
    return response.data;
  },
};

export default applicationService;
