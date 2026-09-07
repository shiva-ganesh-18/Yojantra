import apiClient from './api';

export const authService = {
  sendOtp: async (phone) => {
    const response = await apiClient.post('/auth/otp/send', { phone });
    return response.data;
  },

  verifyOtp: async (phone, otp) => {
    const response = await apiClient.post('/auth/otp/verify', { phone, otp });
    return response.data;
  },
};

export default authService;
