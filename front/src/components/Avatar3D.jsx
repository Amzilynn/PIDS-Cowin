import React, { useState, Suspense, useEffect, useMemo } from 'react';
import { Play, Square, User, ShieldCheck, HeartPulse, Activity, Star } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { Canvas } from '@react-three/fiber';
import { OrbitControls } from '@react-three/drei';
import AvatarModel from './AvatarModel';

export default function Avatar3D({ type = 'doctor', isSpeaking = false, speechPulse = 0 }) {
  const [status, setStatus] = useState('En attente'); // En attente, Initialisation, En ligne
  const [isActive, setIsActive] = useState(false);
  const [rating, setRating] = useState(0);
  const [hoverRating, setHoverRating] = useState(0);

  // Memoize stable values to prevent infinite re-renders
  const theme = useMemo(() => ({
    doctor: { color: "#4E8C8A", light: "#0D9488", name: "Dr. Martin (Médecin)" },
    pharmacist: { color: "#10B981", light: "#059669", name: "Mme Berthier (Pharmacienne)" },
    delegate: { color: "#1E3A8A", light: "#3B82F6", name: "Sarah Khalil (Déléguée)" }
  }[type] || { color: "#4E8C8A", light: "#0D9488", name: "Ava Assistant" }), [type]);

  // Sync internal isActive with parent status if needed
  useEffect(() => {
    if (isSpeaking) {
      setIsActive(true);
      setStatus('En ligne');
    }
  }, [isSpeaking]);

  const startSession = () => {
    setStatus('Initialisation...');
    setRating(0); 
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
    <div className="h-full w-full flex flex-col items-center justify-between relative overflow-hidden transition-all group p-6 bg-brand-navy/50 rounded-4xl border border-white/10 shadow-2xl backdrop-blur-3xl">
      
      {/* Cinematic Background Glows */}
      <div className="absolute -top-24 -right-24 w-80 h-80 opacity-20 rounded-full blur-[100px] animate-pulse-slow" 
           style={{ backgroundColor: theme.color }} />
      <div className="absolute -bottom-24 -left-24 w-80 h-80 opacity-10 rounded-full blur-[100px] animate-pulse-slow delay-1000" 
           style={{ backgroundColor: theme.light }} />

      {/* Header Statut */}
      <div className="w-full flex items-center justify-between relative z-10">
         <div className="flex items-center gap-3 bg-white/5 backdrop-blur-xl px-5 py-2.5 rounded-full border border-white/10 shadow-lg">
            <div className={`w-2.5 h-2.5 rounded-full transition-all duration-500 ${isActive ? 'shadow-[0_0_10px]' : ''}`} 
                 style={{ backgroundColor: isActive ? theme.color : 'rgba(255,255,255,0.2)', boxShadow: isActive ? `0 0 10px ${theme.color}` : 'none' }} />
            <span className="text-[10px] font-black uppercase tracking-[0.2em] text-white/80">{status}</span>
         </div>
         {/* Always rendered to prevent layout shift; visibility controlled via opacity */}
         <div className={`flex items-center gap-2 text-white/40 transition-all duration-500 ${isActive ? 'opacity-100' : 'opacity-0 pointer-events-none'}`}>
            <Activity size={14} className="animate-pulse" style={{ color: theme.color }} />
            <span className="text-[9px] font-black uppercase tracking-widest leading-none">Biolink Active</span>
         </div>
      </div>

      {/* Main 3D Canvas Area */}
      <div className="relative w-full flex-1 flex flex-col items-center justify-center cursor-pointer min-h-[350px]">
         <Suspense fallback={
           <div className="flex flex-col items-center gap-4">
              <div className="w-20 h-20 border-[6px] border-white/5 border-t-white/40 rounded-full animate-spin" />
              <p className="text-[10px] font-black text-white/40 uppercase tracking-widest">Loading Neural Mesh...</p>
           </div>
         }>
           <Canvas 
             camera={{ position: [0, 0, 1.8], fov: 30 }}
             dpr={[1, 2]}
             shadows
           >
             {/* The MetaHuman Avatar — upper body framing */}
             <AvatarModel 
               isSpeaking={isSpeaking || (isActive && status === 'En ligne')} 
               speechPulse={speechPulse}
             />

             <OrbitControls 
               enableZoom={false} 
               enablePan={false} 
               makeDefault
               minPolarAngle={Math.PI / 3}
               maxPolarAngle={Math.PI / 2.2}
               minAzimuthAngle={-Math.PI / 6}
               maxAzimuthAngle={Math.PI / 6}
             />
           </Canvas>
         </Suspense>

       </div>

      {/* Metrics / Info Panel */}
      <div className="w-full space-y-6 relative z-10 px-4">
          <div className="flex flex-col items-center gap-3">
             <h3 className="text-2xl font-black text-white tracking-tighter leading-none italic uppercase">
                {theme.name}
             </h3>
             <div className="h-1 w-12 rounded-full opacity-40" style={{ backgroundColor: theme.color }} />
          </div>

         {/* Rating System Overlay - wrapped in AnimatePresence to prevent layout push */}
         <AnimatePresence>
         {(status === 'Discussion terminée' || rating > 0) && (
            <motion.div 
               key="rating-panel"
               initial={{ opacity: 0, y: 20, height: 0 }}
               animate={{ opacity: 1, y: 0, height: 'auto' }}
               exit={{ opacity: 0, y: 10, height: 0 }}
               transition={{ duration: 0.3 }}
               className="flex flex-col items-center gap-2 mb-2 p-4 bg-white/5 rounded-3xl border border-white/10 overflow-hidden"
            >
               <span className="text-[9px] font-black uppercase text-white/40 tracking-[0.3em]">Session Feedback</span>
               <div className="flex gap-3">
                  {[1, 2, 3, 4, 5].map((star) => (
                     <button
                        key={star}
                        onMouseEnter={() => setHoverRating(star)}
                        onMouseLeave={() => setHoverRating(0)}
                        onClick={() => setRating(star)}
                        className="transition-all duration-300 hover:scale-125"
                     >
                        <Star 
                           size={20} 
                           fill={(hoverRating || rating) >= star ? '#F59E0B' : 'transparent'} 
                           className={(hoverRating || rating) >= star ? 'text-amber-500 fill-amber-500 drop-shadow-[0_0_8px_rgba(245,158,11,0.5)]' : 'text-white/10'}
                        />
                     </button>
                  ))}
               </div>
            </motion.div>
         )}
         </AnimatePresence>

         <div className="flex justify-center w-full">
            <button 
              onClick={isActive ? endSession : startSession}
              className={`w-full h-14 rounded-2xl text-[11px] font-black uppercase tracking-[0.25em] transition-all shadow-2xl flex items-center justify-center gap-4 transform active:scale-[0.98] border ${
                isActive 
                  ? 'bg-rose-500/10 text-rose-500 border-rose-500/20 hover:bg-rose-500/20' 
                  : 'bg-white text-brand-navy border-white hover:scale-[1.02] shadow-white/10'
              }`}
            >
               {status === 'Initialisation...' ? (
                  <div className="flex items-center gap-2">
                     <span className="w-2 h-2 rounded-full bg-brand-navy animate-bounce" />
                     <span className="w-2 h-2 rounded-full bg-brand-navy animate-bounce delay-100" />
                     <span className="w-2 h-2 rounded-full bg-brand-navy animate-bounce delay-200" />
                  </div>
               ) : (
                  <>
                     {isActive ? <Square size={16} fill="currentColor" /> : <Play size={16} fill="currentColor" />}
                     {isActive ? 'Terminate Connection' : 'Establish Neural Link'}
                  </>
               )}
            </button>
         </div>
      </div>

    </div>
  );
}
