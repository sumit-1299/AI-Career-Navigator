import React, { createContext, useContext, useState, useEffect } from 'react';
import { api, setToken } from '../services/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try {
      const saved = localStorage.getItem('career_navigator_user');
      return saved ? JSON.parse(saved) : null;
    } catch (e) {
      return null;
    }
  });

  const [token, setTokenState] = useState(() => {
    try {
      return localStorage.getItem('career_navigator_token');
    } catch (e) {
      return null;
    }
  });

  const [profile, setProfile] = useState(null);
  const [preferences, setPreferences] = useState(null);
  const [targetCareerId, setTargetCareerId] = useState(() => {
    try {
      return parseInt(localStorage.getItem('career_navigator_target_career') || '1', 10);
    } catch (e) {
      return 1;
    }
  });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (token) {
      loadUserData();
    }
  }, [token]);

  useEffect(() => {
    try {
      localStorage.setItem('career_navigator_target_career', targetCareerId.toString());
    } catch (e) {
      // Ignore localStorage write error
    }
  }, [targetCareerId]);

  async function loadUserData() {
    try {
      setLoading(true);
      try {
        const profRes = await api.getProfile();
        if (profRes?.profile) setProfile(profRes.profile);
      } catch (e) {
        // Profile might not exist yet for new user
      }

      try {
        const prefRes = await api.getPreferences();
        if (prefRes?.career_preferences) {
          setPreferences(prefRes.career_preferences);
        }
      } catch (e) {
        // Preferences might not exist yet
      }
    } catch (err) {
      console.warn('User data loading note:', err);
    } finally {
      setLoading(false);
    }
  }

  async function login(email, password) {
    const res = await api.login(email, password);
    if (res?.access_token) {
      setToken(res.access_token);
      setTokenState(res.access_token);
      setUser(res.user);
      try {
        localStorage.setItem('career_navigator_user', JSON.stringify(res.user));
      } catch (e) {}
    }
    return res;
  }

  async function register(name, email, password) {
    const res = await api.register(name, email, password);
    if (res?.user) {
      await login(email, password);
    }
    return res;
  }

  function logout() {
    setToken(null);
    setTokenState(null);
    setUser(null);
    setProfile(null);
    setPreferences(null);
    try {
      localStorage.removeItem('career_navigator_user');
    } catch (e) {}
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!token,
        profile,
        setProfile,
        preferences,
        setPreferences,
        targetCareerId,
        setTargetCareerId,
        login,
        register,
        logout,
        loading,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    return {
      user: null,
      token: null,
      isAuthenticated: false,
      profile: null,
      preferences: null,
      targetCareerId: 1,
      setTargetCareerId: () => {},
      login: async () => {},
      register: async () => {},
      logout: () => {},
      loading: false,
    };
  }
  return context;
}
