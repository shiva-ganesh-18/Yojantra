import React, { createContext, useContext, useState, useEffect, useRef } from 'react';
import { useAuthStore } from './useAuth';
import { SUPPORTED_LANGUAGES, getTranslation } from '../utils/translations';

const LanguageContext = createContext({
  language: 'hi',
  setLanguage: () => {},
  t: (key, fallback, params) => key,
  supportedLanguages: SUPPORTED_LANGUAGES,
  currentLanguageMeta: SUPPORTED_LANGUAGES[0],
});

export const LanguageProvider = ({ children }) => {
  const { user, api, setUser } = useAuthStore();
  const [announcement, setAnnouncement] = useState('');
  const announcementTimeoutRef = useRef(null);
  
  // Initial language resolution priority:
  // 1. Logged in user profile `preferred_language`
  // 2. Saved `localStorage` language key `yojantra_lang`
  // 3. Default fallback: 'hi' (Hindi)
  const [language, setLanguageState] = useState(() => {
    try {
      const stored = localStorage.getItem('yojantra_lang');
      if (stored) return stored;
    } catch {}
    return user?.preferred_language || 'hi';
  });

  // Keep HTML document lang synchronized for screen readers & browser font rendering
  useEffect(() => {
    if (typeof document !== 'undefined' && document.documentElement) {
      document.documentElement.lang = language;
      document.documentElement.dir = 'ltr';
    }
  }, [language]);

  // Sync state if user profile preferred_language changes
  useEffect(() => {
    if (user?.preferred_language && user.preferred_language !== language) {
      setLanguageState(user.preferred_language);
      try {
        localStorage.setItem('yojantra_lang', user.preferred_language);
      } catch {}
    }
  }, [user?.preferred_language]);

  const setLanguage = async (newLang) => {
    if (!newLang) return;
    setLanguageState(newLang);
    try {
      localStorage.setItem('yojantra_lang', newLang);
    } catch {}

    const meta = SUPPORTED_LANGUAGES.find(l => l.code === newLang);
    const langLabel = meta ? `${meta.label} (${meta.englishName})` : newLang;

    // Announce to screen readers in the newly selected language
    setAnnouncement(getTranslation('a11y_language_switched', newLang, `Interface language switched to ${langLabel}`).replace('{lang}', langLabel));
    if (announcementTimeoutRef.current) clearTimeout(announcementTimeoutRef.current);
    announcementTimeoutRef.current = setTimeout(() => setAnnouncement(''), 3000);

    // If user is authenticated, persist to backend profile
    if (user && user.id) {
      try {
        await api().put('/users/me', { preferred_language: newLang });
        setUser({ ...user, preferred_language: newLang });
      } catch (err) {
        console.warn('[Yojantra Language] Failed to persist preferred language to backend:', err);
      }
    }
  };

  const t = (key, fallback = null, params = null) => {
    let text = getTranslation(key, language, fallback);
    if (params && typeof text === 'string') {
      Object.keys(params).forEach((paramKey) => {
        text = text.replace(new RegExp(`{${paramKey}}`, 'g'), params[paramKey]);
      });
    }
    return text;
  };

  const currentLanguageMeta = SUPPORTED_LANGUAGES.find(l => l.code === language) || SUPPORTED_LANGUAGES[0];

  return (
    <LanguageContext.Provider value={{ 
      language, 
      setLanguage, 
      t, 
      supportedLanguages: SUPPORTED_LANGUAGES,
      currentLanguageMeta 
    }}>
      {/* Screen reader live announcement area for assistive technology */}
      <div 
        role="status" 
        aria-live="polite" 
        aria-atomic="true" 
        className="sr-only"
      >
        {announcement}
      </div>
      {children}
    </LanguageContext.Provider>
  );
};

export const useLanguage = () => useContext(LanguageContext);

export default useLanguage;
