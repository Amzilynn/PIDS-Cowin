import React, { useState } from 'react';
import { motion } from 'framer-motion';
import {
  Eye, EyeOff, ArrowRight, Lock, Globe, Activity, AlertCircle
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import Logo from '../../components/Logo';

export default function LoginPage() {
  const { login } = useAuth();

  const [email, setEmail]           = useState('');
  const [password, setPassword]     = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading]       = useState(false);
  const [error, setError]           = useState('');

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    const result = await login(email, password);

    if (!result.ok) {
      setError(result.error || 'Identifiants invalides.');
      setLoading(false);
    }
    // Si ok → AuthContext redirige automatiquement via navigate()
  };

  return (
    <div className="h-screen bg-md-surface flex flex-col items-center justify-center p-4 md:p-6 relative overflow-hidden font-sans">

      {/* Formes de fond */}
      <div className="absolute top-[-10%] right-[-10%] w-[600px] h-[600px] organic-glow bg-md-primary/10" />
      <div className="absolute bottom-[-20%] left-[-10%] w-[800px] h-[800px] organic-glow bg-md-tertiary/10" />

      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.8, ease: [0.2, 0, 0, 1] }}
        className="w-full max-w-md relative p-8 md:p-10 bg-white/40 backdrop-blur-3xl rounded-[48px] border border-white/50 shadow-2xl"
      >
        {/* Logo */}
        <div className="flex flex-col items-center mb-8 -mt-2">
          <Logo className="h-44 md:h-56 -mb-4 drop-shadow-xl" showText={false} />
          <div className="text-center relative z-10">
            <h1 className="text-4xl font-black tracking-tighter text-md-on-background mb-1 leading-tight">
              Connectez-vous
            </h1>
            <p className="text-xs font-medium text-md-on-surface-variant opacity-60 tracking-tight">
              Intelligence terrain &amp; formation pharmaceutique
            </p>
          </div>
        </div>

        <form onSubmit={handleLogin} className="space-y-5">

          {/* Champ Email */}
          <div className="flex flex-col gap-1">
            <label
              htmlFor="login-email"
              className="text-[9px] font-black uppercase tracking-[0.3em] text-md-primary pl-1"
            >
              Adresse e-mail
            </label>
            <div className="relative group">
              <div className="absolute left-4 top-1/2 -translate-y-1/2 text-md-outline/50 group-focus-within:text-md-primary transition-colors">
                <Globe size={16} />
              </div>
              <input
                id="login-email"
                type="email"
                placeholder="votre@email.com"
                value={email}
                onChange={(e) => { setEmail(e.target.value); setError(''); }}
                className="w-full h-12 bg-md-surface-container-low rounded-xl border-b-2 border-md-outline px-4 pl-12 focus:border-md-primary focus:outline-none placeholder:text-md-on-surface-variant/50 text-sm font-medium transition-all"
                required
                autoComplete="email"
              />
            </div>
          </div>

          {/* Champ Mot de passe */}
          <div className="flex flex-col gap-1">
            <label
              htmlFor="login-password"
              className="text-[9px] font-black uppercase tracking-[0.3em] text-md-primary pl-1"
            >
              Mot de passe
            </label>
            <div className="relative group">
              <div className="absolute left-4 top-1/2 -translate-y-1/2 text-md-outline/50 group-focus-within:text-md-primary transition-colors">
                <Lock size={16} />
              </div>
              <input
                id="login-password"
                type={showPassword ? 'text' : 'password'}
                placeholder="••••••••"
                value={password}
                onChange={(e) => { setPassword(e.target.value); setError(''); }}
                className="w-full h-12 bg-md-surface-container-low rounded-xl border-b-2 border-md-outline px-4 pl-12 pr-12 focus:border-md-primary focus:outline-none placeholder:text-md-on-surface-variant/50 text-sm font-medium transition-all"
                required
                autoComplete="current-password"
              />
              <button
                type="button"
                id="toggle-password-visibility"
                onClick={() => setShowPassword((v) => !v)}
                className="absolute right-4 top-1/2 -translate-y-1/2 text-md-outline/50 hover:text-md-primary transition-colors"
                aria-label={showPassword ? 'Masquer le mot de passe' : 'Afficher le mot de passe'}
              >
                {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>

          {/* Message d'erreur */}
          {error && (
            <motion.div
              initial={{ opacity: 0, y: -6 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex items-center gap-2 px-4 py-3 bg-red-50 border border-red-200 rounded-xl text-red-600 text-xs font-semibold"
            >
              <AlertCircle size={14} className="shrink-0" />
              {error}
            </motion.div>
          )}

          {/* Bouton connexion */}
          <button
            id="btn-login-submit"
            type="submit"
            disabled={loading}
            className="group w-full btn-primary h-14 rounded-pill text-xs font-black uppercase tracking-[0.3em] shadow-lg shadow-md-primary/20 active:scale-95 transition-all flex items-center justify-center gap-3 disabled:opacity-40 disabled:scale-100 mt-2 relative overflow-hidden"
          >
            {loading ? (
              <Activity className="animate-spin" size={20} />
            ) : (
              <>
                Se connecter
                <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform" />
              </>
            )}
            {!loading && (
              <div className="absolute inset-0 shimmer-anim opacity-10 pointer-events-none" />
            )}
          </button>
        </form>

        {/* Info bas de page */}
        <p className="mt-8 text-center text-[9px] font-bold text-md-outline/40 uppercase tracking-[0.4em]">
          Avalive — Accès Sécurisé · Tous droits réservés
        </p>
      </motion.div>
    </div>
  );
}
