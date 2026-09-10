import axios from 'axios';
import { appCheck } from '../config/firebase';

const API_URL = (import.meta.env.VITE_API_URL || 'http://127.0.0.1:8001').replace(/\/+$/, '');

export const apiClient = axios.create({
  baseURL: API_URL,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor: Inject Bearer token from localStorage/Zustand store & App Check token
apiClient.interceptors.request.use(
  async (config) => {
    try {
      const persistedAuth = localStorage.getItem('yojantra-auth') || localStorage.getItem('schemematch-auth');
      if (persistedAuth) {
        const parsed = JSON.parse(persistedAuth);
        const token = parsed?.state?.token;
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
      }

      // If Firebase App Check is initialized, dynamically attach token
      if (typeof window !== 'undefined' && appCheck && import.meta.env.VITE_FIREBASE_APP_CHECK_SITE_KEY) {
        try {
          const { getToken } = await import('firebase/app-check');
          const appCheckTokenResult = await getToken(appCheck, /* forceRefresh */ false);
          if (appCheckTokenResult?.token) {
            config.headers['X-Firebase-AppCheck'] = appCheckTokenResult.token;
          }
        } catch (_) {}
      }
    } catch (e) {
      console.warn('Failed in request interceptor:', e);
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Track 401 redirect to prevent redirect loops or multiple alerts
let isRedirecting401 = false;

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

    // Helper: extract a human-readable string from FastAPI `detail`
    // which may be a string, a list of validation errors, or a dict
    // (e.g. POST /applications/{id}/submit returns {message, errors, ...}).
    const detailToMessage = (detail, fallback) => {
      if (typeof detail === 'string' && detail) return detail;
      if (Array.isArray(detail)) {
        const joined = detail
          .map((err) => {
            if (typeof err === 'string') return err;
            const loc = Array.isArray(err?.loc) ? err.loc.join('.') : '';
            const msg = err?.msg || err?.message || JSON.stringify(err);
            return loc ? `${loc} ${msg}` : msg;
          })
          .join(', ');
        return joined || fallback;
      }
      if (detail && typeof detail === 'object') {
        const msg = detail.message || detail.msg;
        const errs = Array.isArray(detail.errors) ? detail.errors.join(', ') : '';
        if (msg && errs) return `${msg} (${errs})`;
        if (msg) return msg;
        return fallback;
      }
      return fallback;
    };

    if (error.response) {
      const { status, data } = error.response;
      customError.status = status;
      customError.details = data;
      // Axios-compatible shim: existing call sites read
      // err.response?.data?.detail and err.message. Keep both working.
      customError.response = error.response;
      customError.request = error.request;

      switch (status) {
        case 401:
          customError.message = detailToMessage(data?.detail, 'Session expired. Please log in again.');
          try {
            // 1. Clear stored Yojantra token & cache keys
            localStorage.removeItem('yojantra-auth');
            localStorage.removeItem('schemematch-auth');

            // 2. Dispatch auth-expired custom event to reset store state
            if (typeof window !== 'undefined') {
              window.dispatchEvent(new CustomEvent('yojantra-session-expired', {
                detail: { message: customError.message }
              }));

              // 3. Prevent duplicate redirects & redirect to /login
              if (!isRedirecting401 && !window.location.pathname.includes('/login')) {
                isRedirecting401 = true;
                const searchParams = new URLSearchParams(window.location.search);
                searchParams.set('session', 'expired');
                window.location.replace(`/login?${searchParams.toString()}`);
                setTimeout(() => {
                  isRedirecting401 = false;
                }, 3000);
              }
            }
          } catch (_) {}
          break;
        case 403:
          customError.message = detailToMessage(data?.detail, 'Access denied. You do not have permission for this resource.');
          break;
        case 404:
          customError.message = detailToMessage(data?.detail, 'The requested resource was not found.');
          break;
        case 422:
          customError.message = detailToMessage(data?.detail, 'Validation error in submitted data.');
          break;
        case 429:
          customError.message = detailToMessage(data?.detail, 'Too many requests. Please wait a moment before trying again.');
          break;
        case 500:
          customError.message = 'Internal server error. Please try again shortly.';
          break;
        default:
          customError.message = detailToMessage(data?.detail, error.message || 'An unexpected error occurred.');
      }
    }

    return Promise.reject(customError);
  }
);

export default apiClient;
