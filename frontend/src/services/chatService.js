import apiClient from './api';

export const chatService = {
  getChatStatus: async () => {
    const response = await apiClient.get('/chat/status');
    return response.data;
  },

  sendMessage: async (message, language = 'en', channel = 'text', sessionId = null) => {
    const response = await apiClient.post('/chat/message', {
      message,
      language,
      channel,
      session_id: sessionId,
    });
    return response.data;
  },

  explainEligibility: async (schemeId, customProfile = null) => {
    const response = await apiClient.post('/chat/explain-eligibility', {
      scheme_id: schemeId,
      custom_profile: customProfile,
    });
    return response.data;
  },

  calculateLoanEMI: async (schemeId, loanAmountInr, tenureMonths = null) => {
    const response = await apiClient.post('/chat/calculate-loan', {
      scheme_id: schemeId,
      loan_amount_inr: loanAmountInr,
      tenure_months: tenureMonths,
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

