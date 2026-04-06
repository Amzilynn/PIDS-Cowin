import React, { useState, useEffect } from 'react';
import { Play, Square, User, ShieldCheck, HeartPulse, Activity } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export default function Avatar3D({ type = 'doctor' }) {
  const [status, setStatus] = useState('En attente'); // En attente, Initialisation, En ligne
  const [isActive, setIsActive] = useState(false);

  const startSession = () => {
    setStatus('Initialisation...');
    setTimeout(() => {
      setStatus('En ligne');
      setIsActive(true);
    }, 1500);
  };

  const endSession = () => {
    setStatus('En attente');
    setIsActive(false);
  };

  return (
    <div className="h-full md-card flex flex-col items-center justify-between relative overflow-hidden bg-md-surface-container shadow-xl border border-md-primary/10 transition-all group">
      
      {/* Background Glows Signature */}
      <div className="absolute top-0 right-0 w-64 h-64 bg-md-primary/10 rounded-full blur-[60px] animate-pulse-slow" />
      <div className="absolute bottom-0 left-0 w-64 h-64 bg-emerald-500/5 rounded-full blur-[60px] animate-pulse-slow delay-1000" />

      {/* Header Statut */}
      <div className="w-full flex items-center justify-between px-2 relative z-10">
         <div className="flex items-center gap-3">
            <div className={`w-2 h-2 rounded-full ${isActive ? 'bg-emerald-500 animate-pulse' : 'bg-md-outline/30'}`} />
            <span className="text-[11px] font-black uppercase tracking-widest text-md-on-background">{status}</span>
         </div>
         <div className="flex items-center gap-3 invisible">
         </div>
      </div>

      {/* Zone Avatar Principal */}
      <div className="relative w-full aspect-square max-w-[320px] flex items-center justify-center p-10 cursor-pointer">
         {/* Anneau Dégradé Animé Pulsant */}
         <div className="absolute inset-0 border-2 border-dashed border-md-primary/20 rounded-full animate-[spin_20s_linear_infinite]" />
         <div className="absolute inset-4 border-2 border-md-primary/10 rounded-full animate-[spin_10s_linear_infinite_reverse]" />
         
         <div className="avatar-ring" />
         <div className="avatar-ring-pulse" />
         
         {/* Silhouette SVG */}
         <div className="relative z-10 w-full h-full flex items-center justify-center bg-white/20 backdrop-blur-sm rounded-full shadow-2xl border border-white/50 overflow-hidden shimmer-anim transition-transform hover:scale-110">
            <svg 
              viewBox="0 0 200 200" 
              className="w-4/5 h-4/5 transition-all duration-500"
              style={{ filter: isActive ? 'drop-shadow(0 0 10px rgba(72,169,166,0.3))' : 'grayscale(0.5)' }}
            >
               {/* Humanoid Silhouette */}
               <path 
                 d="M100 45 C 80 45 65 60 65 80 C 65 100 80 115 100 115 C 120 115 135 100 135 80 C 135 60 120 45 100 45 M60 180 C 60 140 140 140 140 180" 
                 fill={isActive ? 'var(--color-md-primary)' : 'var(--color-md-on-background)'} 
                 className="transition-colors duration-1000"
                 fillOpacity={isActive ? 0.9 : 0.4}
               />
               
               {/* Context Item (Stethoscope or Cross) */}
               {type === 'doctor' ? (
                 <path d="M85 105 Q 100 135 115 105" stroke="white" strokeWidth="3" fill="none" strokeLinecap="round" />
               ) : (
                 <path d="M90 70 L 110 70 M 100 60 L 100 80" stroke="white" strokeWidth="4" />
               )}
            </svg>
            
            {/* Animating Waveform on high status */}
            {isActive && (
              <motion.div 
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="absolute bottom-10 left-0 right-0 h-10 px-10 flex items-center justify-center"
              >
                 <Activity size={40} strokeWidth={1} className="text-md-primary opacity-40 animate-pulse" />
              </motion.div>
            )}
         </div>
      </div>

      {/* Métriques / IA Status */}
      <div className="w-full space-y-6 relative z-10">
         <div className="flex flex-col items-center gap-3">
            <h3 className="text-xl font-black text-md-on-background tracking-tighter">
               {isActive ? (type === 'doctor' ? 'Dr. Martin (Médecin)' : 'Mme Berthier (Pharmacienne)') : 'Avatar en attente'}
            </h3>
            <p className="text-xs font-bold text-md-on-surface-variant opacity-60 text-center uppercase tracking-widest leading-relaxed">
               Analyse par vision par ordinateur <br/> Prête pour évaluation DSO2
            </p>
         </div>

         <div className="flex justify-center gap-4">
            <button 
              onClick={startSession}
              disabled={isActive}
              className={`btn-pill px-8 !h-14 font-black transition-all ${isActive ? 'bg-emerald-500/10 text-emerald-500 border border-emerald-500/20' : 'btn-primary'}`}
            >
               <Play size={20} fill="currentColor" /> {isActive ? 'Connecté' : 'Démarrer'}
            </button>
            <button 
              onClick={endSession}
              disabled={!isActive}
              className="btn-pill px-8 !h-14 border-2 border-md-outline/10 text-md-on-surface-variant font-black hover:bg-rose-50 hover:text-rose-600 active:scale-95 disabled:opacity-30 disabled:grayscale transition-all"
            >
               <Square size={18} fill="currentColor" /> Terminer
            </button>
         </div>
      </div>

      {/* Decorative details */}
      <div className="absolute top-2 w-10 h-1 bg-md-outline/10 rounded-full" />
    </div>
  );
}

function BadgeDSO({ rating = "DSO1" }) {
  return (
    <motion.div 
      initial={{ scale: 0 }}
      animate={{ scale: 1 }}
      className="flex items-center gap-2 px-4 py-2 bg-md-tertiary rounded-pill text-white shadow-lg active:scale-95 cursor-default group"
    >
       <HeartPulse size={14} className="group-hover:animate-bounce" />
       <span className="text-[11px] font-black uppercase tracking-tighter">{rating}</span>
    </motion.div>
  );
}
