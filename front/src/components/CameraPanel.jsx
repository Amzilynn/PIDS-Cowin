import React, { useState, useEffect, useRef } from 'react';
import { Camera, CameraOff, Video, Mic, Shield } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export default function CameraPanel({ label = "Délégué", isActive, onToggle, hideControls = false }) {
  const streamRef = useRef(null);
  const [micLevel, setMicLevel] = useState([0, 0, 0, 0, 0, 0]);

  // Plus de `getUserMedia` ici, on dépend de l'API backend pour la caméra.
  // Lors de l'activation, DSO1 lance `cv2.VideoCapture` et stream le résultat via MJPEG.
  useEffect(() => {
    if (!isActive) {
      setMicLevel([0, 0, 0, 0, 0, 0]);
    }
  }, [isActive]);

  // Simulation de l'animation du micro quand actif
  useEffect(() => {
    let interval;
    if (isActive) {
      interval = setInterval(() => {
        setMicLevel(prev => prev.map(() => Math.random() * 100));
      }, 150);
    } else {
      setMicLevel([0, 0, 0, 0, 0, 0]);
    }
    return () => clearInterval(interval);
  }, [isActive]);

  return (
    <div className="h-full flex flex-col relative overflow-hidden">
      
      {/* Background patterns */}
      <div className="absolute inset-0 opacity-[0.03] pointer-events-none" style={{ backgroundImage: 'radial-gradient(var(--color-md-primary) 1px, transparent 0)', backgroundSize: '24px 24px' }} />
      
      {/* Header Statut */}
      <div className="flex items-center justify-between mb-6 relative z-10 px-2">
         <div className="flex items-center gap-3">
            <div className={`w-3 h-3 rounded-full ${isActive ? 'bg-emerald-500 animate-pulse shadow-[0_0_12px_#10b981]' : 'bg-md-outline/40'}`} />
            <span className="text-[11px] font-black uppercase tracking-widest text-md-on-background">{label}</span>
         </div>
         {isActive && (
            <div className="flex items-center gap-2 bg-emerald-500/10 px-3 py-1 rounded-pill">
               <Shield size={12} className="text-emerald-500" />
               <span className="text-[10px] font-bold text-emerald-500 uppercase tracking-tighter">Sécurisé</span>
            </div>
         )}
      </div>

      {/* Zone Caméra Principal */}
      <div className="flex-1 flex flex-col items-center justify-center relative rounded-[20px] overflow-hidden bg-transparent">
         <AnimatePresence mode="wait">
           {!isActive ? (
             <motion.div 
               key="inactive"
               initial={{ opacity: 0, scale: 0.9 }}
               animate={{ opacity: 1, scale: 1 }}
               exit={{ opacity: 0, scale: 1.1 }}
               className="flex flex-col items-center gap-6 text-md-outline/40"
             >
                <div className="w-24 h-24 rounded-full bg-white/50 border border-dashed border-md-outline/20 flex items-center justify-center shadow-sm">
                   <CameraOff size={40} />
                </div>
                <div className="text-center">
                   <p className="text-sm font-black uppercase tracking-widest text-md-on-background opacity-40">Caméra désactivée</p>
                   <p className="text-[10px] font-bold mt-1 max-w-[200px] leading-relaxed italic">Autorisez l'accès pour commencer la simulation</p>
                </div>
             </motion.div>
           ) : (
             <motion.div 
                key="active"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="w-full h-full flex-1 relative min-h-[400px]"
             >
                {/* Flux vidéo du backend DSO1 (MJPEG Feed) */}
                <img 
                   key={isActive ? "active-feed" : "inactive-feed"}
                   src={isActive ? `http://localhost:8001/api/training/video_feed?t=${Date.now()}` : ""} 
                   alt="Flux DSO1"
                   className="absolute inset-0 w-full h-full object-contain rounded-xl scale-x-[-1] transition-opacity duration-700 bg-black shadow-inner" 
                />
                
                <div className="absolute bottom-6 left-6 flex items-center gap-2">
                   <div className="w-8 h-8 rounded-full bg-black/20 backdrop-blur-md flex items-center justify-center text-emerald-500">
                      <Mic size={14} />
                   </div>
                   <div className="flex items-end gap-1 h-4">
                      {micLevel.map((level, i) => (
                        <motion.div 
                          key={i}
                          animate={{ height: `${level}%` }}
                          className="w-1 bg-emerald-500 rounded-full transition-all duration-150"
                          style={{ minHeight: '2px' }}
                        />
                      ))}
                   </div>
                </div>
             </motion.div>
           )}
         </AnimatePresence>
      </div>

      {/* Contrôles Inférieurs */}
      {!hideControls && (
        <div className="mt-8 flex justify-center relative z-10">
           <button 
             onClick={onToggle}
             className={`btn-pill px-10 transition-all ${
               isActive 
                 ? 'bg-rose-50 text-rose-600 border border-rose-200 hover:bg-rose-100' 
                 : 'btn-primary'
             }`}
           >
              {isActive ? (
                 <>
                    <CameraOff size={18} /> Désactiver
                 </>
              ) : (
                 <>
                    <Camera size={18} /> Activer la caméra
                 </>
              )}
           </button>
        </div>
      )}

      {/* Decorative corners */}
      {/* Removing decorative corners */}
    </div>
  );
}
