import React, { useState, useEffect, useRef } from 'react';
import { Camera, CameraOff, Video, Shield, User, Zap } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export default function CameraPanelDSO2({ label = "FLUX PRATICIEN" }) {
  const [isActive, setIsActive] = useState(false);
  const videoRef = useRef(null);
  const streamRef = useRef(null);

  useEffect(() => {
    if (isActive) {
      startCamera();
    } else {
      stopCamera();
    }
    return () => stopCamera();
  }, [isActive]);

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        video: { width: 1280, height: 720 }, 
        audio: false 
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
    } catch (err) {
      console.error("Error accessing camera:", err);
      setIsActive(false);
    }
  };

  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
  };

  return (
    <div className={`h-full w-full relative overflow-hidden rounded-[32px] shadow-2xl flex flex-col transition-all duration-700 ${isActive ? 'bg-slate-900' : 'bg-[#fcfdfe]'}`}>
      
      {/* 1. Status Label Overlay */}
      <div className={`absolute top-8 left-8 z-20 flex items-center gap-3 px-4 py-2 rounded-full border backdrop-blur-md transition-all duration-500 ${
        isActive 
          ? 'bg-black/20 border-white/10 text-white/80' 
          : 'bg-white/80 border-slate-100 text-slate-800 shadow-sm'
      }`}>
          <div className={`w-2 h-2 rounded-full transition-all duration-500 ${isActive ? 'bg-emerald-400 animate-pulse shadow-[0_0_8px_#34d399]' : 'bg-slate-300'}`} />
          <span className="text-[10px] font-black uppercase tracking-[0.2em]">
              {label}
          </span>
      </div>

      {/* 2. Main View Area */}
      <div className="flex-1 relative overflow-hidden">
        <AnimatePresence mode="wait">
          {!isActive ? (
            <motion.div 
              key="inactive"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="w-full h-full flex flex-col items-center justify-center p-12"
            >
              {/* Stylish Light Placeholder */}
              <div className="relative mb-8">
                 <motion.div 
                   animate={{ scale: [1, 1.1, 1], opacity: [0.3, 0.5, 0.3] }}
                   transition={{ duration: 4, repeat: Infinity }}
                   className="absolute inset-0 bg-slate-200 blur-2xl rounded-full"
                 />
                 <div className="relative w-28 h-28 rounded-full bg-white border border-slate-100 shadow-xl flex items-center justify-center text-slate-300">
                    <User size={54} strokeWidth={1} />
                 </div>
              </div>
              
              <div className="text-center space-y-2 relative z-10">
                 <p className="text-[14px] font-black uppercase tracking-[0.2em] text-slate-800">Prêt pour la session ?</p>
                 <p className="text-[10px] font-bold text-slate-400 uppercase tracking-[0.3em] leading-relaxed">
                    Cliquez ci-dessous pour démarrer
                 </p>
              </div>

              {/* Decorative elements */}
              <div className="absolute bottom-32 left-1/2 -translate-x-1/2 flex items-center gap-2 opacity-20">
                 <Zap size={14} className="text-slate-400" />
                 <span className="text-[10px] font-black uppercase tracking-widest text-slate-400">Live Connect Ready</span>
              </div>
            </motion.div>
          ) : (
            <motion.div 
              key="active"
              initial={{ opacity: 0, scale: 1.05 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.6 }}
              className="w-full h-full relative"
            >
               <video 
                 ref={videoRef}
                 autoPlay 
                 playsInline 
                 muted
                 className="w-full h-full object-cover scale-x-[-1]" 
               />
              
              {/* Live Overlay */}
              <div className="absolute top-8 right-8">
                 <div className="bg-rose-500 text-white text-[9px] font-black px-3 py-1 rounded-full flex items-center gap-2 uppercase tracking-widest shadow-lg shadow-rose-500/20">
                    <div className="w-1.5 h-1.5 bg-white rounded-full animate-pulse" />
                    Live
                 </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* 3. Bottom Control Button Overlay */}
      <div className={`p-8 absolute bottom-0 left-0 right-0 z-30 flex flex-col gap-4 bg-gradient-to-t transition-all duration-500 ${
        isActive 
          ? 'from-slate-950 via-slate-950/40 to-transparent' 
          : 'from-white via-white/40 to-transparent'
      }`}>
         <button 
           onClick={() => setIsActive(!isActive)}
           className={`w-full h-14 rounded-2xl text-[11px] font-black uppercase tracking-widest flex items-center justify-center gap-3 transition-all shadow-2xl ${
             isActive 
               ? 'bg-white text-slate-900 hover:bg-slate-100' 
               : 'bg-slate-900 text-white hover:bg-slate-800 shadow-slate-900/20'
           }`}
         >
            {isActive ? <CameraOff size={18} /> : <Camera size={18} />}
            {isActive ? "Arrêter la caméra" : "Activer la caméra"}
         </button>
      </div>
    </div>
  );
}
