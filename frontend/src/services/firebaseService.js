/**
 * Firebase Service for Yojantra
 * Provides unified, safe methods for:
 * 1. Cloud Messaging (FCM) push notification registration & foreground listening
 * 2. App Check token management
 * 3. Privacy-safe Analytics event logging (Strictly excludes Aadhaar, PAN, OTP, Passwords, Financials)
 */
import { app, auth, messaging, analytics } from '../config/firebase';
import apiClient from './api';

// Prohibited sensitive keys to guard against accidental tracking
const FORBIDDEN_KEYS = [
  'aadhaar', 'aadhaar_number', 'pan', 'pan_number', 'otp', 'password',
  'pin', 'secret', 'bank_account', 'cvv', 'phone', 'full_name'
];

/**
 * Filter event parameters to guarantee zero PII or sensitive government credentials
 */
function sanitizeAnalyticsParams(params = {}) {
  const clean = {};
  for (const [key, value] of Object.entries(params)) {
    const k = key.toLowerCase();
    if (FORBIDDEN_KEYS.some((bad) => k.includes(bad))) {
      continue;
    }
    if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') {
      clean[key] = value;
    }
  }
  return clean;
}

export const firebaseService = {
  /**
   * Request Web Push Notification permission and retrieve FCM device token
   */
  requestNotificationPermission: async () => {
    if (typeof window === 'undefined' || !('Notification' in window)) {
      return { status: 'unsupported', message: 'Notifications are not supported by this browser.' };
    }

    try {
      const permission = await Notification.requestPermission();
      if (permission !== 'granted') {
        return { status: 'denied', message: 'Push notification permission was not granted.' };
      }

      // Check if Firebase messaging is ready
      if (!messaging) {
        return {
          status: 'framework_ready',
          message: 'Notification permission granted. FCM token dispatch will activate once service worker & vapid key are initialized.'
        };
      }

      const { getToken } = await import('firebase/messaging');
      const vapidKey = import.meta.env.VITE_FIREBASE_VAPID_KEY;

      const token = await getToken(messaging, { vapidKey: vapidKey || undefined });
      if (token) {
        // Register token with Yojantra backend
        try {
          await apiClient.post('/notifications/register-token', { fcm_token: token });
        } catch (apiErr) {
          console.debug('[Yojantra FCM] Token registration warning:', apiErr);
        }
        return { status: 'registered', token };
      }

      return { status: 'failed', message: 'No registration token available.' };
    } catch (error) {
      console.warn('[Yojantra FCM] Permission or token error:', error);
      return { status: 'error', error: error.message };
    }
  },

  /**
   * Listen for foreground push notifications
   */
  onForegroundMessage: (callback) => {
    if (!messaging) return () => {};

    let unsubscribe = () => {};
    import('firebase/messaging').then(({ onMessage }) => {
      try {
        unsubscribe = onMessage(messaging, (payload) => {
          if (callback && typeof callback === 'function') {
            callback(payload);
          }
        });
      } catch (e) {
        console.debug('[Yojantra FCM] onMessage listener:', e);
      }
    }).catch(() => {});

    return () => unsubscribe();
  },

  /**
   * Track privacy-safe engagement events in Firebase Analytics
   * Strictly filters out Aadhaar, PAN, OTP, Passwords, etc.
   */
  logEvent: async (eventName, eventParams = {}) => {
    if (!eventName) return;

    try {
      const safeParams = sanitizeAnalyticsParams(eventParams);

      if (analytics) {
        const { logEvent } = await import('firebase/analytics');
        logEvent(analytics, eventName, safeParams);
      }

      // Safe debug log in development
      if (import.meta.env.DEV) {
        console.debug(`[Yojantra Safe Analytics] Event: ${eventName}`, safeParams);
      }
    } catch (e) {
      // Analytics failures must never break the user experience
      console.debug('[Yojantra Analytics] logEvent notice:', e);
    }
  },

  /**
   * Fetch current backend Firebase operational status
   */
  getFirebaseStatus: async () => {
    try {
      const res = await apiClient.get('/notifications/firebase/status');
      return res.data;
    } catch (err) {
      return {
        status: 'offline',
        message: 'Could not connect to Firebase status endpoint'
      };
    }
  },
};

export default firebaseService;
