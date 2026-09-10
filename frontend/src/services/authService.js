import apiClient from './api';

export const authService = {
  loginWithGoogle: async (idToken) => {
    const response = await apiClient.post('/auth/google', { id_token: idToken });
    return response.data;
  },

  linkGoogleAccount: async (idToken) => {
    const response = await apiClient.post('/auth/link/google', { id_token: idToken });
    return response.data;
  },

  getAuthConfig: async () => {
    const response = await apiClient.get('/auth/config');
    return response.data;
  },
};

export const {
  loginWithGoogle,
  linkGoogleAccount,
  getAuthConfig,
} = authService;

export default authService;
