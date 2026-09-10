/**
 * Firebase Client Configuration for Yojantra
 * Official Firebase Web SDK initialization with Google Auth Provider.
 */
import { initializeApp, getApps, getApp } from 'firebase/app';
import { getAuth, GoogleAuthProvider, signInWithPopup, signOut } from 'firebase/auth';

const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
  appId: import.meta.env.VITE_FIREBASE_APP_ID,
};

const REQUIRED_FIREBASE_KEYS = [
  'VITE_FIREBASE_API_KEY',
  'VITE_FIREBASE_AUTH_DOMAIN',
  'VITE_FIREBASE_PROJECT_ID',
  'VITE_FIREBASE_STORAGE_BUCKET',
  'VITE_FIREBASE_MESSAGING_SENDER_ID',
  'VITE_FIREBASE_APP_ID'
];

/**
 * Validates all required client Firebase configuration parameters.
 */
export const getFirebaseConfigStatus = () => {
  const missing = [];
  
  if (!firebaseConfig.apiKey || firebaseConfig.apiKey.includes('your-') || firebaseConfig.apiKey.includes('Placeholder')) {
    missing.push('VITE_FIREBASE_API_KEY');
  }
  if (!firebaseConfig.authDomain || firebaseConfig.authDomain.includes('your-')) {
    missing.push('VITE_FIREBASE_AUTH_DOMAIN');
  }
  if (!firebaseConfig.projectId || firebaseConfig.projectId.includes('your-')) {
    missing.push('VITE_FIREBASE_PROJECT_ID');
  }
  if (!firebaseConfig.storageBucket || firebaseConfig.storageBucket.includes('your-')) {
    missing.push('VITE_FIREBASE_STORAGE_BUCKET');
  }
  if (!firebaseConfig.messagingSenderId || firebaseConfig.messagingSenderId.includes('your-')) {
    missing.push('VITE_FIREBASE_MESSAGING_SENDER_ID');
  }
  if (!firebaseConfig.appId || firebaseConfig.appId.includes('your-')) {
    missing.push('VITE_FIREBASE_APP_ID');
  }

  const configured = missing.length === 0;

  // Safe developer diagnostics (NEVER log keys or secrets)
  if (import.meta.env.DEV) {
    console.debug('[Yojantra Firebase Diagnostics]', {
      projectConfigured: Boolean(firebaseConfig.projectId && !missing.includes('VITE_FIREBASE_PROJECT_ID')),
      authDomainConfigured: Boolean(firebaseConfig.authDomain && !missing.includes('VITE_FIREBASE_AUTH_DOMAIN')),
      providerReady: configured,
      missingCount: missing.length
    });
  }

  return {
    configured,
    missingKeys: missing
  };
};

const configStatus = getFirebaseConfigStatus();
export const isFirebaseConfigured = configStatus.configured;

let app = null;
let auth = null;
let googleProvider = null;
let appCheck = null;
let messaging = null;
let analytics = null;

if (isFirebaseConfigured) {
  try {
    app = getApps().length > 0 ? getApp() : initializeApp(firebaseConfig);
    auth = getAuth(app);
    googleProvider = new GoogleAuthProvider();
    googleProvider.setCustomParameters({ prompt: 'select_account' });

    // Initialize Firebase App Check (reCAPTCHA v3 or Enterprise / Debug token)
    if (typeof window !== 'undefined') {
      const appCheckSiteKey = import.meta.env.VITE_FIREBASE_APP_CHECK_SITE_KEY;
      if (appCheckSiteKey) {
        import('firebase/app-check').then(({ initializeAppCheck, ReCaptchaV3Provider }) => {
          try {
            appCheck = initializeAppCheck(app, {
              provider: new ReCaptchaV3Provider(appCheckSiteKey),
              isTokenAutoRefreshEnabled: true
            });
          } catch (e) {
            console.debug('[Yojantra Firebase] AppCheck optional init:', e);
          }
        }).catch(() => {});
      }

      // Initialize Firebase Cloud Messaging (FCM)
      import('firebase/messaging').then(({ getMessaging, isSupported }) => {
        isSupported().then((supported) => {
          if (supported) {
            try {
              messaging = getMessaging(app);
            } catch (e) {
              console.debug('[Yojantra Firebase] FCM messaging init:', e);
            }
          }
        }).catch(() => {});
      }).catch(() => {});

      // Initialize Firebase Analytics for non-sensitive measurement
      import('firebase/analytics').then(({ getAnalytics, isSupported }) => {
        isSupported().then((supported) => {
          if (supported) {
            try {
              analytics = getAnalytics(app);
            } catch (e) {
              console.debug('[Yojantra Firebase] Analytics init:', e);
            }
          }
        }).catch(() => {});
      }).catch(() => {});
    }
  } catch (err) {
    console.warn('[Yojantra Firebase] Initialization warning:', err);
  }
}

export { app, auth, googleProvider, appCheck, messaging, analytics };

/**
 * Trigger official Google Popup authentication flow
 * Returns authenticated Google user and Firebase ID Token
 */
export const signInWithGooglePopup = async () => {
  if (!isFirebaseConfigured || !auth || !googleProvider) {
    const error = new Error('FIREBASE_NOT_CONFIGURED');
    error.userMessage = 'Google Sign-In is not configured on this environment. Please configure Firebase client variables in .env.';
    throw error;
  }

  try {
    const result = await signInWithPopup(auth, googleProvider);
    const idToken = await result.user.getIdToken();
    return {
      firebaseUser: result.user,
      idToken
    };
  } catch (err) {
    // Map Firebase auth errors to user-friendly messages without exposing raw internals
    const error = new Error(err.code || 'AUTH_ERROR');
    if (err.code === 'auth/popup-closed-by-user' || err.code === 'auth/cancelled-popup-request') {
      error.userMessage = 'Google sign-in was cancelled.';
    } else if (err.code === 'auth/network-request-failed') {
      error.userMessage = 'Unable to connect to authentication service. Please check your internet connection.';
    } else if (err.code === 'auth/popup-blocked') {
      error.userMessage = 'Sign-in popup was blocked by your browser. Please allow popups for this site.';
    } else {
      error.userMessage = 'Google sign-in failed. Please try again.';
    }
    error.original = err;
    throw error;
  }
};

/**
 * Sign out cleanly from Firebase client session
 */
export const signOutFirebase = async () => {
  if (auth) {
    try {
      await signOut(auth);
    } catch (e) {
      console.warn('[Yojantra Firebase] SignOut warning:', e);
    }
  }
};
