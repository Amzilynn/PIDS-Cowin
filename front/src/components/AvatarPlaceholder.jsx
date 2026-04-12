import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Camera, Mic, Volume2, ShieldCheck, Activity } from 'lucide-react';

export default function AvatarPlaceholder({ 
  isSpeaking = false, 
  isLoading = false, 
  status = "REPRESENTATIVE READY",
  name = "Ava Assistant"
}) {
  return (
    <div className="relative w-full h-[480px] bg-brand-navy rounded-4xl overflow-hidden shadow-2xl flex flex-col items-center justify-center p-8 group border border-white/10">
      {/* Background Pulse Pattern */}
      <div className="absolute inset-0 opacity-10 pointer-events-none">
        <svg width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
              <path d="M 40 0 L 0 0 0 40" fill="none" stroke="white" strokeWidth="0.5"/>
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#grid)" />
        </svg>
      </div>

      {/* Main Silhouette Skeleton */}
      <motion.div 
        animate={isSpeaking ? { 
          scale: [1, 1.02, 1],
          transition: { repeat: Infinity, duration: 1.5, ease: "easeInOut" }
        } : {}}
        className="relative z-10 w-48 h-48 mb-8"
      >
        {/* Silhouette Glow */}
        <div className="absolute inset-0 bg-brand-teal/20 blur-3xl rounded-full" />
        
        {/* Silhouette Vector (Based on Logo style) */}
        <svg viewBox="0 0 200 200" className="w-full h-full drop-shadow-[0_0_30px_rgba(78,140,138,0.4)]">
          <path
            d="M100 30 C 130 30 155 55 155 85 C 155 105 145 125 130 145 C 120 160 110 170 100 170 C 90 170 80 160 70 145 C 55 125 45 105 45 85 C 45 55 70 30 100 30 Z"
            fill="white"
            fillOpacity="0.05"
            stroke="white"
            strokeWidth="1.5"
            strokeDasharray="4 4"
          />
          
          {/* Heartbeat/ECG Pulse Line inside the head */}
          <motion.path
            d="M60 85 L 85 85 L 92 65 L 108 105 L 115 85 L 140 85"
            stroke="#4E8C8A"
            strokeWidth="3"
            strokeLinecap="round"
            strokeLinejoin="round"
            fill="none"
            initial={{ pathLength: 0, opacity: 0 }}
            animate={{ 
              pathLength: isSpeaking ? 1 : 0.6,
              opacity: isSpeaking ? 1 : 0.4,
              scaleY: isSpeaking ? [1, 1.4, 1] : 1
            }}
            transition={{ 
              pathLength: { duration: 1.5, repeat: Infinity, ease: "linear" },
              scaleY: { duration: 0.2, repeat: Infinity, ease: "easeInOut" }
            }}
          />
        </svg>
      </motion.div>

      {/* Text Info */}
      <div className="relative z-10 text-center">
        <AnimatePresence mode="wait">
          {isLoading ? (
            <motion.div 
              key="loading"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="flex flex-col items-center gap-2"
            >
              <div className="flex gap-1">
                {[0, 1, 2].map((i) => (
                  <motion.div
                    key={i}
                    animate={{ scale: [1, 1.5, 1] }}
                    transition={{ repeat: Infinity, duration: 1, delay: i * 0.2 }}
                    className="w-2 h-2 bg-brand-teal rounded-full"
                  />
                ))}
              </div>
              <p className="text-white/60 font-bold text-xs uppercase tracking-[0.3em]">Avatar Loading...</p>
            </motion.div>
          ) : (
            <motion.div
              key="info"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="space-y-1"
            >
              <h3 className="text-white font-extrabold text-2xl tracking-tight">{name}</h3>
              <div className="flex items-center justify-center gap-2 text-brand-teal">
                <ShieldCheck size={14} />
                <span className="text-[10px] font-black uppercase tracking-widest">{status}</span>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Floating Controls Overlay (Visible on Hover/Focus) */}
      <div className="absolute bottom-8 left-1/2 -translate-x-1/2 flex items-center gap-4 group-hover:translate-y-0 translate-y-4 opacity-0 group-hover:opacity-100 transition-all duration-300">
        <button className="p-4 bg-white/5 hover:bg-white/10 rounded-2xl border border-white/10 text-white/40 hover:text-white transition-colors">
          <Camera size={20} />
        </button>
        <button className={`p-5 rounded-3xl border transition-all ${isSpeaking ? 'bg-brand-teal border-brand-teal text-white shadow-[0_0_20px_rgba(78,140,138,0.4)]' : 'bg-white/10 border-white/20 text-white'}`}>
          <Volume2 size={24} />
        </button>
        <button className="p-4 bg-white/5 hover:bg-white/10 rounded-2xl border border-white/10 text-white/40 hover:text-white transition-colors">
          <Mic size={20} />
        </button>
      </div>

      {/* Live Indicator */}
      <div className="absolute top-8 right-8 flex items-center gap-2 px-3 py-1 bg-white/5 rounded-full border border-white/10 backdrop-blur-md">
        <Activity size={12} className="text-brand-teal" />
        <span className="text-[9px] font-black text-white/60 tracking-widest uppercase">Live Process</span>
      </div>
    </div>
  );
}
