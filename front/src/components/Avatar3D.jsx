import React, { useState, useEffect } from 'react';
import { Play, Square, User, ShieldCheck, HeartPulse, Activity, Star } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export default function Avatar3D({ type = 'doctor' }) {
  const [status, setStatus] = useState('En attente'); // En attente, Initialisation, En ligne
  const [isActive, setIsActive] = useState(false);
  const [rating, setRating] = useState(0);
  const [hoverRating, setHoverRating] = useState(0);

  const startSession = () => {
    setStatus('Initialisation...');
    setRating(0); // Reset rating on new start
    setTimeout(() => {
      setStatus('En ligne');
      setIsActive(true);
    }, 1500);
  };

  const endSession = () => {
    setStatus('Discussion terminée');
    setIsActive(false);
  };

  return (
    <div className="h-full w-full flex flex-col items-center justify-between relative overflow-hidden transition-all group p-6">
      
      {/* Background Glows Signature */}
      <div className="absolute top-0 right-0 w-64 h-64 bg-md-primary/10 rounded-full blur-[60px] animate-pulse-slow" />
      <div className="absolute bottom-0 left-0 w-64 h-64 bg-emerald-500/5 rounded-full blur-[60px] animate-pulse-slow delay-1000" />

      {/* Header Statut */}
      <div className="w-full flex items-center justify-between relative z-10">
         <div className="flex items-center gap-3 bg-white/50 backdrop-blur-md px-5 py-2.5 rounded-pill shadow-sm border border-md-outline/5">
            <div className={`w-2.5 h-2.5 rounded-full ${isActive ? 'bg-emerald-500 animate-pulse' : 'bg-md-outline/40'}`} />
            <span className="text-[11px] font-black uppercase tracking-widest text-md-on-background">{status}</span>
         </div>
      </div>

      {/* Zone Avatar Principal */}
      <div className="relative w-full flex flex-col items-center justify-center py-2 cursor-pointer">
         <div className="relative w-full max-w-[200px] h-[200px] flex items-center justify-center">
            {/* Anneau Dégradé Animé Pulsant */}
            <div className="absolute inset-0 border-[3px] border-dashed border-md-primary/20 rounded-full animate-[spin_20s_linear_infinite]" />
            <div className="absolute inset-4 border-[3px] border-md-primary/10 rounded-full animate-[spin_10s_linear_infinite_reverse]" />
         
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
      </div>

      {/* Métriques / IA Status */}
      <div className="w-full space-y-5 relative z-10">
         <div className="flex flex-col items-center gap-3">
            <h3 className="text-xl font-black text-md-on-background tracking-tighter">
               {isActive ? (type === 'doctor' ? 'Dr. Martin (Médecin)' : type === 'delegate' ? 'Sarah Khalil (Déléguée)' : 'Mme Berthier (Pharmacienne)') : 'Avatar en attente'}
            </h3>
            <p className="text-xs font-bold text-md-on-surface-variant opacity-60 text-center uppercase tracking-widest leading-relaxed">
               Analyse par vision par ordinateur <br/> Prête pour évaluation
            </p>
         </div>

         {/* Rating System */}
         {(status === 'Discussion terminée' || rating > 0) && (
            <div className="flex flex-col items-center gap-2 mb-2">
               <span className="text-[10px] font-black uppercase text-md-primary/60 tracking-widest">Évaluer l'agent</span>
               <div className="flex gap-2">
                  {[1, 2, 3, 4, 5].map((star) => (
                     <button
                        key={star}
                        onMouseEnter={() => setHoverRating(star)}
                        onMouseLeave={() => setHoverRating(0)}
                        onClick={() => setRating(star)}
                        className="transition-all duration-300 hover:scale-125 active:scale-95"
                     >
                        <Star 
                           size={20} 
                           fill={(hoverRating || rating) >= star ? '#F59E0B' : 'transparent'} 
                           className={(hoverRating || rating) >= star ? 'text-amber-500 fill-amber-500' : 'text-md-outline/30'}
                        />
                     </button>
                  ))}
               </div>
            </div>
         )}

         <div className="flex justify-center w-full">
            <button 
              onClick={isActive ? endSession : startSession}
              className={`btn-pill w-full !h-11 text-[11px] font-black uppercase tracking-widest transition-all shadow-md flex items-center justify-center gap-3 transform active:scale-[0.98] ${
                isActive 
                  ? 'bg-rose-500 text-white shadow-rose-500/20 hover:bg-rose-600' 
                  : 'btn-primary'
              }`}
            >
               {status === 'Initialisation...' ? (
                  <div className="flex items-center gap-2">
                     <span className="w-2 h-2 rounded-full bg-white animate-bounce" />
                     <span className="w-2 h-2 rounded-full bg-white animate-bounce delay-100" />
                     <span className="w-2 h-2 rounded-full bg-white animate-bounce delay-200" />
                  </div>
               ) : (
                  <>
                     {isActive ? <Square size={14} fill="currentColor" /> : <Play size={14} fill="currentColor" />}
                     {isActive ? 'Terminer la Session' : 'Démarrer'}
                  </>
               )}
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
