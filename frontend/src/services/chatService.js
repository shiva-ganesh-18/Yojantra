import apiClient from './api';

export const chatService = {
  sendMessage: async (message, language = 'hi', channel = 'text') => {
    const response = await apiClient.post('/chat/message', {
      message,
      language,
      channel,
    });
    return response.data;
  },

  sendVoice: async (formData) => {
    const response = await apiClient.post('/chat/voice', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },
};

export default chatService;
