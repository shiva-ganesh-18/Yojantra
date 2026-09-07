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

  verifyDocument: async (docId) => {
    const response = await apiClient.post(`/documents/${docId}/verify`);
    return response.data;
  },
};

export default documentService;
