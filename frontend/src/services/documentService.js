import apiClient from './api';

export const documentService = {
  uploadDocument: async (formData) => {
    const response = await apiClient.post('/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  listMyDocuments: async () => {
    const response = await apiClient.get('/documents/my-documents');
    return response.data;
  },

  getReadiness: async (schemeId = null) => {
    const params = schemeId ? { scheme_id: schemeId } : {};
    const response = await apiClient.get('/documents/readiness', { params });
    return response.data;
  },

  autoFillProfile: async (docId = null) => {
    const url = docId ? `/documents/auto-fill/${docId}` : '/documents/auto-fill';
    const response = await apiClient.post(url);
    return response.data;
  },

  verifyDocument: async (docId) => {
    const response = await apiClient.post(`/documents/${docId}/verify`);
    return response.data;
  },

  deleteDocument: async (docId) => {
    const response = await apiClient.delete(`/documents/${docId}`);
    return response.data;
  },
};

export default documentService;

