import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';

// ─── API Configuration ────────────────────────────────────────────────────────
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8001';

// ─── Contexte ─────────────────────────────────────────────────────────────────
const AuthContext = createContext(null);

// ─── Provider ─────────────────────────────────────────────────────────────────
export function AuthProvider({ children }) {
  const navigate = useNavigate();

  const [user, setUser] = useState(null);       // données utilisateur
  const [token, setToken] = useState(null);     // JWT string
  const [loading, setLoading] = useState(true); // vérification initiale

  // Retourne les infos stockées dans localStorage au démarrage
  useEffect(() => {
    const stored = localStorage.getItem('avalive_token');
    const storedUser = localStorage.getItem('avalive_user');
    if (stored && storedUser) {
      setToken(stored);
      setUser(JSON.parse(storedUser));
    }
    setLoading(false);
  }, []);

  /**
   * login() — appelle POST /api/auth/login, stocke le JWT, redirige.
   * @param {string} email
   * @param {string} password
   * @returns {{ ok: boolean, error?: string }}
   */
  const login = useCallback(async (email, password) => {
    try {
      const res = await fetch(`${API_BASE}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email.trim().toLowerCase(), password }),
      });

      if (!res.ok) {
        const err = await res.json();
        return { ok: false, error: err.detail || 'Identifiants invalides.' };
      }

      const data = await res.json();

      // Sauvegarder dans l'état et localStorage
      const userData = {
        user_id: data.user_id,
        email: data.email,
        type: data.type,
        sub_role: data.sub_role,
        display_name: data.display_name,
        redirect_to: data.redirect_to,
        new_recommendations_count: data.new_recommendations_count || 0,
        new_recommendations: data.new_recommendations || [],
      };

      setToken(data.access_token);
      setUser(userData);
      localStorage.setItem('avalive_token', data.access_token);
      localStorage.setItem('avalive_user', JSON.stringify(userData));

      // Redirection automatique selon le rôle retourné par l'API
      navigate(data.redirect_to);

      return { ok: true };
    } catch (e) {
      return { ok: false, error: 'Impossible de contacter le serveur.' };
    }
  }, [navigate]);

  /**
   * logout() — efface la session et redirige vers /
   */
  const logout = useCallback(() => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('avalive_token');
    localStorage.removeItem('avalive_user');
    navigate('/');
  }, [navigate]);

  /**
   * isAuthenticated — true si un token valide est présent
   */
  const isAuthenticated = !!token && !!user;

  /**
   * hasRole(role) — vérifie si l'utilisateur a un type donné
   * @param {'delegue'|'medecin'|'pharmacien'|'admin'} role
   */
  const hasRole = (role) => user?.type === role;

  return (
    <AuthContext.Provider value={{
      user,
      token,
      loading,
      isAuthenticated,
      login,
      logout,
      hasRole,
    }}>
      {children}
    </AuthContext.Provider>
  );
}

// ─── Hook ─────────────────────────────────────────────────────────────────────
export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth doit être utilisé dans un <AuthProvider>');
  return ctx;
}

export default AuthContext;
