/**
 * Offline Storage Utility for SchemeMatch AI
 * Provides local caching of schemes, profile drafts, and network status tracking.
 */

const SCHEMES_CACHE_KEY = 'schemematch_cached_schemes';
const ONBOARDING_DRAFT_KEY = 'schemematch_onboarding_draft';

export const offlineStorage = {
  // Check online status
  isOnline: () => navigator.onLine,

  // Cache schemes list locally
  cacheSchemes: (schemes) => {
    try {
      localStorage.setItem(SCHEMES_CACHE_KEY, JSON.stringify({
        data: schemes,
        cachedAt: new Date().toISOString(),
      }));
    } catch (e) {
      console.warn('Failed to cache schemes offline:', e);
    }
  },

  // Get cached schemes
  getCachedSchemes: () => {
    try {
      const raw = localStorage.getItem(SCHEMES_CACHE_KEY);
      if (!raw) return null;
      return JSON.parse(raw);
    } catch (e) {
      return null;
    }
  },

  // Save onboarding form draft
  saveOnboardingDraft: (draftData) => {
    try {
      localStorage.setItem(ONBOARDING_DRAFT_KEY, JSON.stringify({
        ...draftData,
        savedAt: new Date().toISOString(),
      }));
    } catch (e) {
      console.warn('Failed to save draft:', e);
    }
  },

  // Retrieve onboarding draft
  getOnboardingDraft: () => {
    try {
      const raw = localStorage.getItem(ONBOARDING_DRAFT_KEY);
      return raw ? JSON.parse(raw) : null;
    } catch (e) {
      return null;
    }
  },

  // Clear onboarding draft after successful submission
  clearOnboardingDraft: () => {
    try {
      localStorage.removeItem(ONBOARDING_DRAFT_KEY);
    } catch (_) {}
  },
};

export default offlineStorage;
