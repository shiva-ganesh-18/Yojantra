import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import apiClient from '../services/api';
import { signOutFirebase } from '../config/firebase';

// Helper to migrate legacy storage key if needed
const getInitialState = () => {
  try {
    const existing = localStorage.getItem('yojantra-auth');
    if (existing) return JSON.parse(existing)?.state || {};
    const legacy = localStorage.getItem('schemematch-auth');
    if (legacy) return JSON.parse(legacy)?.state || {};
  } catch (e) {
    console.warn('[Yojantra Auth] Failed parsing existing auth state:', e);
  }
  return {};
};

const initial = getInitialState();

export const useAuthStore = create(
  persist(
    (set, get) => ({
      token: initial.token || null,
      user: initial.user || null,
      setToken: (token) => set({ token }),
      setUser: (user) => set({ user }),
      logout: async () => {
        try {
          await signOutFirebase();
        } catch (e) {
          console.warn('[Yojantra Auth] Error signing out of Firebase:', e);
        }
        localStorage.removeItem('yojantra-auth');
        localStorage.removeItem('schemematch-auth');
        set({ token: null, user: null });
      },

      api: () => apiClient
    }),
    { name: 'yojantra-auth' }
  )
);

// Global event listener for session expiration triggered by api interceptor
if (typeof window !== 'undefined') {
  window.addEventListener('yojantra-session-expired', () => {
    useAuthStore.setState({ token: null, user: null });
  });
}

export default useAuthStore;
