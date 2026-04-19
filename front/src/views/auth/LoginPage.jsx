import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  ShieldCheck, 
  User, 
  Stethoscope, 
  ChevronRight, 
  Eye, 
  EyeOff, 
  ArrowRight,
  Lock,
  Globe,
  PlusSquare,
  Activity,
  HeartPulse,
  Store
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import Logo from '../../components/Logo';

const roles = [
  {
    id: 'admin',
    label: 'Administrateur',
    desc: 'Gestion globale & supervision analytique',
    icon: ShieldCheck,
    color: 'bg-md-primary/10 text-md-primary',
  },
  {
    id: 'delegate',
    label: 'Délégué Professionnel',
    desc: 'Formation clinique & intelligence terrain',
    icon: User,
    color: 'bg-md-secondary-container text-md-on-secondary-container',
  },
  {
    id: 'medecin',
    label: 'Médecin',
    desc: 'Espace de réception & évaluation',
    icon: Stethoscope,
    color: 'bg-sky-100 text-sky-700',
  }
];

const DSO3_API_URL = import.meta.env.VITE_DSO3_API_URL || 'http://127.0.0.1:8000';

export default function LoginPage() {
  const navigate = useNavigate();
  const [authMode, setAuthMode] = useState('login');
  const [selectedRole, setSelectedRole] = useState(null);
  const [subRole, setSubRole] = useState(null);
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [delegateName, setDelegateName] = useState('');
  const [delegateExpertise, setDelegateExpertise] = useState('');
  const [delegateInterests, setDelegateInterests] = useState('');

  const selectedRoleId = selectedRole?.id || 'delegate';

  const resetMessages = () => {
    setError('');
    setSuccess('');
  };

  const handleSignUp = async (e) => {
    e.preventDefault();
    resetMessages();

    if (!selectedRole) {
      setError('Choisissez un profil avant de continuer');
      return;
    }

    if (password !== confirmPassword) {
      setError('Les mots de passe ne correspondent pas');
      return;
    }

    const payload = {
      email,
      password,
      role: selectedRoleId,
    };

    if (selectedRoleId === 'delegate' && delegateName.trim()) {
      payload.delegate_name = delegateName.trim();
    }

    if (selectedRoleId === 'delegate') {
      payload.expertise = (delegateExpertise || (subRole === 'commercial' ? 'commercial' : 'medical')).trim();
      payload.interests = (delegateInterests || 'field activities').trim();
    }

    setLoading(true);
    try {
      const response = await fetch(`${DSO3_API_URL}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const apiPayload = await response.json().catch(() => ({}));
        throw new Error(apiPayload?.detail || 'Échec de création de compte');
      }

      setSuccess('Compte créé avec succès. Connectez-vous maintenant.');
      setAuthMode('login');
      setPassword('');
      setConfirmPassword('');
      setDelegateName('');
      setDelegateExpertise('');
      setDelegateInterests('');
    } catch (signUpError) {
      setError(signUpError.message || 'Erreur lors de la création du compte');
    } finally {
      setLoading(false);
    }
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    resetMessages();
    setLoading(true);

    try {
      const response = await fetch(`${DSO3_API_URL}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email,
          password,
          role: selectedRoleId,
        }),
      });

      if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(payload?.detail || 'Échec de connexion');
      }

      const payload = await response.json();
      localStorage.setItem('cw_auth', JSON.stringify(payload));

      const sub = selectedRoleId === 'delegate' ? (subRole || 'medical') : 'none';
      const delegateIdParam = payload.delegate_id ? `&id=${payload.delegate_id}` : '';

      setLoading(false);
      navigate(`/${selectedRoleId}?role=${selectedRoleId}&sub=${sub}${delegateIdParam}`);
    } catch (loginError) {
      setLoading(false);
      setError(loginError.message || 'Erreur de connexion');
    }
  };

  return (
    <div className="h-screen bg-md-surface flex flex-col items-center justify-center p-4 md:p-6 relative overflow-hidden font-sans">
      {/* Signature MD3 Background Shapes */}
      <div className="absolute top-[-10%] right-[-10%] w-[600px] h-[600px] organic-glow bg-md-primary/10" />
      <div className="absolute bottom-[-20%] left-[-10%] w-[800px] h-[800px] organic-glow bg-md-tertiary/10" />
      
      <motion.div 
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.8, ease: [0.2, 0, 0, 1] }}
        className="w-full max-w-xl relative p-6 md:p-8 bg-white/40 backdrop-blur-3xl rounded-[48px] border border-white/50 shadow-2xl max-h-[95vh] overflow-y-auto hide-scrollbar"
      >
        {/* Logo Section - Ajusté pour visibilité optimale */}
        <div className="flex flex-col items-center mb-6 -mt-2 md:-mt-6">
          <Logo className="h-48 md:h-64 -mb-4 md:-mb-6 drop-shadow-xl justify-center" showText={false} />
          <div className="text-center relative z-10">
            <h1 className="text-4xl font-black tracking-tighter text-md-on-background mb-2 leading-tight">
              {authMode === 'login' ? 'Connectez-vous' : 'Créer un compte'}
            </h1>
            <p className="text-xs font-medium text-md-on-surface-variant opacity-60 tracking-tight">Intelligence terrain & formation pharmaceutique</p>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-2 p-1 rounded-2xl bg-white/60 border border-md-outline/10 mb-4">
          <button
            type="button"
            onClick={() => {
              setAuthMode('login');
              resetMessages();
            }}
            className={`h-10 rounded-xl text-[10px] font-black uppercase tracking-widest transition ${authMode === 'login' ? 'bg-md-primary text-white' : 'text-md-on-surface-variant'}`}
          >
            Connexion
          </button>
          <button
            type="button"
            onClick={() => {
              setAuthMode('signup');
              resetMessages();
            }}
            className={`h-10 rounded-xl text-[10px] font-black uppercase tracking-widest transition ${authMode === 'signup' ? 'bg-md-primary text-white' : 'text-md-on-surface-variant'}`}
          >
            Inscription
          </button>
        </div>

        <form onSubmit={authMode === 'login' ? handleLogin : handleSignUp} className="space-y-4">
          
          {/* Sélection du Rôle */}
          <div className="space-y-3">
             <label className="text-[9px] font-black uppercase tracking-[0.3em] text-md-primary pl-1">Choisir votre profil</label>
             <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {roles.map((role) => (
                   <button
                     key={role.id}
                     type="button"
                     onClick={() => { setSelectedRole(role); setSubRole(null); }}
                     className={`flex flex-col items-center p-4 rounded-[24px] border-2 transition-all duration-300 relative overflow-hidden group active:scale-95 ${
                       selectedRole?.id === role.id 
                         ? 'bg-white border-md-primary shadow-lg ring-4 ring-md-primary/5' 
                         : 'bg-md-surface-container-low border-transparent hover:bg-white hover:border-md-outline/10'
                     }`}
                   >
                     <div className={`w-10 h-10 rounded-xl ${role.color} flex items-center justify-center mb-2 transition-transform group-hover:scale-110 duration-500`}>
                        <role.icon size={18} />
                     </div>
                     <span className="text-[10px] font-black uppercase tracking-widest text-center leading-tight">{role.label}</span>
                     
                     {selectedRole?.id === role.id && (
                        <motion.div layoutId="activeRole" className="absolute top-2 right-2 w-1.5 h-1.5 bg-md-primary rounded-full" />
                     )}
                   </button>
                ))}
             </div>
          </div>

          {/* Sous-rôles Cascade */}
          <AnimatePresence mode="wait">
            {selectedRole && selectedRole.id === 'delegate' && (
              <motion.div 
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="space-y-3"
              >
                 <label className="text-[9px] font-black uppercase tracking-[0.3em] text-md-primary pl-1">
                   Secteur d’activité
                 </label>
                 <div className="flex gap-3">
                      <>
                       <button 
                         type="button"
                         onClick={() => setSubRole('medical')}
                         className={`flex-1 h-10 rounded-pill border-2 transition-all font-black text-[9px] uppercase tracking-widest ${subRole === 'medical' ? 'bg-md-primary text-white border-md-primary shadow-md' : 'bg-white text-md-on-surface-variant border-md-outline/10'}`}
                       >
                         <HeartPulse size={12} className="mr-1 inline" /> Médical
                       </button>
                       <button 
                         type="button"
                         onClick={() => setSubRole('commercial')}
                         className={`flex-1 h-10 rounded-pill border-2 transition-all font-black text-[9px] uppercase tracking-widest ${subRole === 'commercial' ? 'bg-md-primary text-white border-md-primary shadow-md' : 'bg-white text-md-on-surface-variant border-md-outline/10'}`}
                       >
                         <Store size={12} className="mr-1 inline" /> Commercial
                       </button>
                      </>
                 </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Champs de Saisie */}
          <div className="space-y-4">
            <div className="flex flex-col gap-1">
              <label className="text-[9px] font-black uppercase tracking-[0.3em] text-md-primary pl-1">Identifiants protégés</label>
              <div className="relative group">
                <div className="absolute left-4 top-1/2 -translate-y-1/2 text-md-outline/50 group-focus-within:text-md-primary transition-colors">
                  <Globe size={16} />
                </div>
                <input 
                  type="email" 
                  placeholder="E-mail professionnel" 
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full h-12 bg-md-surface-container-low rounded-xl border-b-2 border-md-outline px-4 pl-12 focus:border-md-primary focus:outline-none placeholder:text-md-on-surface-variant/50 text-sm font-medium transition-all"
                  required
                />
              </div>
            </div>

            <div className="relative group">
              <div className="absolute left-4 top-1/2 -translate-y-1/2 text-md-outline/50 group-focus-within:text-md-primary transition-colors">
                <Lock size={16} />
              </div>
              <input 
                type={showPassword ? "text" : "password"} 
                placeholder="Mot de passe" 
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full h-12 bg-md-surface-container-low rounded-xl border-b-2 border-md-outline px-4 pl-12 pr-12 focus:border-md-primary focus:outline-none placeholder:text-md-on-surface-variant/50 text-sm font-medium transition-all"
                required
              />
              <button 
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-4 top-1/2 -translate-y-1/2 text-md-outline/50 hover:text-md-primary transition-colors"
              >
                {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>

            {authMode === 'signup' && (
              <>
                <div className="relative group">
                  <div className="absolute left-4 top-1/2 -translate-y-1/2 text-md-outline/50 group-focus-within:text-md-primary transition-colors">
                    <Lock size={16} />
                  </div>
                  <input
                    type={showPassword ? "text" : "password"}
                    placeholder="Confirmer le mot de passe"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    className="w-full h-12 bg-md-surface-container-low rounded-xl border-b-2 border-md-outline px-4 pl-12 focus:border-md-primary focus:outline-none placeholder:text-md-on-surface-variant/50 text-sm font-medium transition-all"
                    required
                  />
                </div>

                {selectedRoleId === 'delegate' && (
                  <>
                    <div className="relative group">
                      <div className="absolute left-4 top-1/2 -translate-y-1/2 text-md-outline/50 group-focus-within:text-md-primary transition-colors">
                        <User size={16} />
                      </div>
                      <input
                        type="text"
                        placeholder="Nom du délégué (optionnel)"
                        value={delegateName}
                        onChange={(e) => setDelegateName(e.target.value)}
                        className="w-full h-12 bg-md-surface-container-low rounded-xl border-b-2 border-md-outline px-4 pl-12 focus:border-md-primary focus:outline-none placeholder:text-md-on-surface-variant/50 text-sm font-medium transition-all"
                      />
                    </div>

                    <div className="relative group">
                      <div className="absolute left-4 top-1/2 -translate-y-1/2 text-md-outline/50 group-focus-within:text-md-primary transition-colors">
                        <PlusSquare size={16} />
                      </div>
                      <input
                        type="text"
                        placeholder="Expertise (ex: diabétologie)"
                        value={delegateExpertise}
                        onChange={(e) => setDelegateExpertise(e.target.value)}
                        className="w-full h-12 bg-md-surface-container-low rounded-xl border-b-2 border-md-outline px-4 pl-12 focus:border-md-primary focus:outline-none placeholder:text-md-on-surface-variant/50 text-sm font-medium transition-all"
                      />
                    </div>

                    <div className="relative group">
                      <div className="absolute left-4 top-1/2 -translate-y-1/2 text-md-outline/50 group-focus-within:text-md-primary transition-colors">
                        <Store size={16} />
                      </div>
                      <input
                        type="text"
                        placeholder="Interests (ex: cardiologie, congrès)"
                        value={delegateInterests}
                        onChange={(e) => setDelegateInterests(e.target.value)}
                        className="w-full h-12 bg-md-surface-container-low rounded-xl border-b-2 border-md-outline px-4 pl-12 focus:border-md-primary focus:outline-none placeholder:text-md-on-surface-variant/50 text-sm font-medium transition-all"
                      />
                    </div>
                  </>
                )}
              </>
            )}
          </div>

          {/* Action Connexion */}
          <button 
            type="submit"
            disabled={loading || !selectedRole}
            className="group w-full btn-primary h-14 rounded-pill text-xs font-black uppercase tracking-[0.3em] shadow-lg shadow-md-primary/20 active:scale-95 transition-all flex items-center justify-center gap-3 disabled:opacity-30 disabled:scale-100 mt-2 relative overflow-hidden"
          >
            {loading ? (
              <Activity className="animate-spin" size={20} />
            ) : (
              <>
                {authMode === 'login' ? 'Se connecter' : 'Créer le compte'}
                <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform" />
              </>
            )}
            
            {!loading && <div className="absolute inset-0 shimmer-anim opacity-10 pointer-events-none" />}
          </button>
        </form>

        {error ? (
          <div className="mt-4 p-3 rounded-xl border border-rose-200 bg-rose-50 text-rose-700 text-xs font-black uppercase tracking-wide">
            {error}
          </div>
        ) : null}

        {success ? (
          <div className="mt-4 p-3 rounded-xl border border-emerald-200 bg-emerald-50 text-emerald-700 text-xs font-black uppercase tracking-wide">
            {success}
          </div>
        ) : null}

        <div className="mt-8 p-4 bg-md-primary/5 rounded-2xl border border-md-primary/10">
           <p className="text-[9px] font-black text-md-primary uppercase tracking-widest mb-2 border-b border-md-primary/10 pb-2">Accès Test Rapide</p>
           <div className="grid grid-cols-2 md:grid-cols-3 gap-2 text-[8px] font-bold text-md-on-surface-variant/70 uppercase tracking-tighter">
              <div>Admin: admin@meddelegate.pro / admin123</div>
              <div>Médical: medical@meddelegate.pro / medical123</div>
              <div>Commercial: commercial@meddelegate.pro / comm123</div>
              <div>Médecin: doctor@meddelegate.pro / doc123</div>
           </div>
        </div>

        <p className="mt-6 text-center text-[9px] font-bold text-md-outline/40 uppercase tracking-[0.4em]">
          Système MédDelegate Pro — Accès Sécurisé
        </p>
      </motion.div>
    </div>
  );
}
