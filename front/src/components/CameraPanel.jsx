import React, { useState, useEffect } from 'react';
import { Camera, CameraOff, Mic, Shield, Video } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export default function CameraPanel({ label = "Délégué", autoStart = false }) {
  const [isActive, setIsActive] = useState(false);
  const [micLevel, setMicLevel] = useState([0, 0, 0, 0, 0, 0]);

  // Auto-start camera when prop changes to true
  useEffect(() => {
    if (autoStart) {
      setIsActive(true);
    } else {
      setIsActive(false);
    }
  }, [autoStart]);

  // Mic animation when active
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
      
      {/* Header */}
      <div className="flex items-center justify-between mb-4 relative z-10 px-1">
        <div className="flex items-center gap-3">
          <div className={`w-2.5 h-2.5 rounded-full transition-all duration-500 ${isActive ? 'bg-emerald-500 animate-pulse shadow-[0_0_10px_#10b981]' : 'bg-slate-300'}`} />
          <span className="text-[11px] font-black uppercase tracking-widest text-md-on-background">{label}</span>
        </div>
        {isActive && (
          <div className="flex items-center gap-1.5 bg-emerald-500/10 px-2.5 py-1 rounded-full">
            <Shield size={10} className="text-emerald-500" />
            <span className="text-[9px] font-bold text-emerald-500 uppercase tracking-tighter">Live</span>
          </div>
        )}
      </div>

      {/* Camera View */}
      <div className="flex-1 flex flex-col items-center justify-center relative rounded-[20px] overflow-hidden bg-slate-950/5">
        <AnimatePresence mode="wait">
          {!isActive ? (
            <motion.div 
              key="inactive"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 1.05 }}
              className="flex flex-col items-center gap-4 text-md-outline/40"
            >
              <div className="w-20 h-20 rounded-full bg-white/60 border border-dashed border-md-outline/20 flex items-center justify-center">
                <Video size={32} className="opacity-40" />
              </div>
              <p className="text-[11px] font-black uppercase tracking-widest opacity-40">En attente...</p>
            </motion.div>
          ) : (
            <motion.div 
              key="active"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.6 }}
              className="w-full h-full relative"
            >
              {/* IMPORTANT: Use the backend's video feed to prevent locking the Windows hardware camera! */}
              <img 
                src={`http://127.0.0.1:8001/api/training/video_feed?t=${Date.now()}`} 
                alt="Flux OpenCV"
                className="w-full h-full object-cover" 
                onError={(e) => { console.error('Erreur de chargement du flux vidéo OpenCV'); }}
              />
              
              {/* Mic indicator overlay */}
              <div className="absolute bottom-4 left-4 flex items-center gap-1.5 bg-black/30 backdrop-blur-sm px-3 py-1.5 rounded-full">
                <Mic size={12} className="text-emerald-400" />
                <div className="flex items-end gap-0.5 h-3">
                  {micLevel.map((level, i) => (
                    <motion.div 
                      key={i}
                      animate={{ height: `${Math.max(level * 0.12, 2)}px` }}
                      className="w-0.5 bg-emerald-400 rounded-full"
                      style={{ minHeight: '2px', maxHeight: '12px' }}
                    />
                  ))}
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
