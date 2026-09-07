import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: API_URL,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor: Inject Bearer token from localStorage/Zustand store
apiClient.interceptors.request.use(
  (config) => {
    try {
      const persistedAuth = localStorage.getItem('schemematch-auth');
      if (persistedAuth) {
        const parsed = JSON.parse(persistedAuth);
        const token = parsed?.state?.token;
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
      }
    } catch (e) {
      console.warn('Failed to parse auth token:', e);
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor: Uniform error handling (401, 403, 404, 422, 500, network)
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const customError = {
      status: error.response?.status || 0,
      message: 'Network error or server unreachable. Please check your connection.',
      details: null,
      raw: error,
    };

    if (error.response) {
      const { status, data } = error.response;
      customError.status = status;
      customError.details = data;

      switch (status) {
        case 401:
          customError.message = data?.detail || 'Session expired. Please log in again.';
          try {
            // Clear expired auth
            localStorage.removeItem('schemematch-auth');
          } catch (_) {}
          break;
        case 403:
          customError.message = data?.detail || 'Access denied. You do not have permission for this resource.';
          break;
        case 404:
          customError.message = data?.detail || 'The requested resource was not found.';
          break;
        case 422:
          if (Array.isArray(data?.detail)) {
            customError.message = data.detail.map((err) => `${err.loc?.join('.')} ${err.msg}`).join(', ');
          } else {
            customError.message = data?.detail || 'Validation error in submitted data.';
          }
          break;
        case 500:
          customError.message = 'Internal server error. Please try again shortly.';
          break;
        default:
          customError.message = data?.detail || error.message || 'An unexpected error occurred.';
      }
    }

    return Promise.reject(customError);
  }
);

export default apiClient;
