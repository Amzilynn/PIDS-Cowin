import React, { useState, useEffect, useRef, useMemo } from 'react';
import { Play, Square, Activity, Star, HeartPulse, ShieldCheck } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { io } from 'socket.io-client';

const AVATAR_SOCKET_URL = 'http://127.0.0.1:8027';

export default function Avatar3D({ type = 'delegate', isActive = false }) {
  const [avatarState, setAvatarState] = useState('standby');
  const [liveFrame, setLiveFrame] = useState(null);
  const [rating, setRating] = useState(0);
  const [hoverRating, setHoverRating] = useState(0);

  const socketRef = useRef(null);

  const theme = useMemo(() => ({
    doctor:     { color: '#4E8C8A', light: '#0D9488', name: 'Dr. Martin (Médecin)'         },
    pharmacist: { color: '#10B981', light: '#059669', name: 'Mme Berthier (Pharmacienne)'  },
    delegate:   { color: '#1E3A8A', light: '#3B82F6', name: 'Sarah Khalil (Déléguée)'      },
  }[type] || { color: '#4E8C8A', light: '#0D9488', name: 'VITAL Assistant' }), [type]);

  // 1. WebSocket Initialization (Kept from Sync-Version)
  useEffect(() => {
    if (isActive) {
      console.log("[Avatar3D] Establishing Neural Link...");
      const socket = io(AVATAR_SOCKET_URL);
      socketRef.current = socket;

      socket.on('connect', () => {
        setAvatarState('idle');
      });

      socket.on('avatar_frame', (data) => {
        setLiveFrame(`data:image/jpeg;base64,${data.frame}`);
        setAvatarState('streaming');
      });

      socket.on('avatar_audio', (data) => {
        const audio = new Audio(`data:audio/mpeg;base64,${data.audio}`);
        
        // Ground-truth sync: Tell the server the EXACT moment audio starts
        audio.onplaying = () => {
          socket.emit('audio_started', {});
          console.log("[Avatar3D] Sync signal sent: audio_started");
        };

        audio.play().catch(e => console.error("Audio play failed:", e));
      });

      socket.on('disconnect', () => {
        setAvatarState('standby');
        setLiveFrame(null);
      });

      return () => socket.disconnect();
    } else {
      setAvatarState('standby');
      setLiveFrame(null);
    }
  }, [isActive]);



  return (
    <div className="h-full w-full relative overflow-hidden bg-brand-navy rounded-[40px] border border-white/10 shadow-2xl backdrop-blur-3xl group">
      
      {/* Cinematic Background Glows (From Intelligence Branch) */}
      <div className="absolute -top-24 -right-24 w-80 h-80 opacity-20 rounded-full blur-[100px] animate-pulse-slow" 
           style={{ backgroundColor: theme.color }} />
      <div className="absolute -bottom-24 -left-24 w-80 h-80 opacity-10 rounded-full blur-[100px] animate-pulse-slow delay-1000" 
           style={{ backgroundColor: theme.light }} />

      {/* 1. THE FULL-SCREEN AVATAR BASE */}
      <div className="absolute inset-0 z-0">
        <AnimatePresence mode="wait">
          {(!isActive || !liveFrame) && (
            <motion.div 
              key="idle" 
              initial={{ opacity: 0 }} 
              animate={{ opacity: 1 }} 
              exit={{ opacity: 0 }} 
              className="w-full h-full"
            >
              <img src="/sarah_source_neutral.jpg" alt="Avatar" className="w-full h-full object-cover" />
              <div className="absolute inset-0 bg-gradient-to-t from-brand-navy via-transparent to-brand-navy/30" />
            </motion.div>
          )}
        </AnimatePresence>

        {liveFrame && (
          <img
            src={liveFrame}
            alt="Live Avatar"
            className="absolute inset-0 w-full h-full object-cover z-10"
            style={{ objectPosition: 'center top' }}
          />
        )}
      </div>

      {/* 2. TOP OVERLAY: Neural Status (Hybrid Version) */}
      <div className="absolute top-8 left-8 right-8 z-20 flex justify-between items-start pointer-events-none">
        <div className="flex items-center gap-3 bg-white/5 backdrop-blur-xl px-5 py-2.5 rounded-full border border-white/10 shadow-lg pointer-events-auto">
            <div className={`w-2.5 h-2.5 rounded-full transition-all duration-500 ${isActive ? 'shadow-[0_0_10px]' : ''}`} 
                 style={{ backgroundColor: isActive ? theme.color : 'rgba(255,255,255,0.2)', boxShadow: isActive ? `0 0 10px ${theme.color}` : 'none' }} />
            <span className="text-[10px] font-black uppercase tracking-[0.2em] text-white/80">
                {isActive ? (avatarState === 'streaming' ? 'Neural Link Active' : 'Initialisation...') : 'Standby'}
            </span>
        </div>
        
        {isActive && (
          <div className="flex items-center gap-2 text-white/40 animate-pulse">
            <Activity size={14} style={{ color: theme.color }} />
            <span className="text-[9px] font-black uppercase tracking-widest leading-none">Biolink Active</span>
          </div>
        )}
      </div>

      {/* 3. BOTTOM OVERLAY: Identity & Rating System */}
      <div className="absolute bottom-0 left-0 right-0 z-30 p-8 pt-20 bg-gradient-to-t from-brand-navy via-brand-navy/60 to-transparent">
        <div className="flex flex-col items-center gap-6">
          
          <div className="flex flex-col items-center gap-2">
             <h3 className="text-2xl font-black text-white tracking-tighter italic uppercase leading-none">
                {theme.name}
             </h3>
             <div className="h-1 w-12 rounded-full opacity-40" style={{ backgroundColor: theme.color }} />
          </div>

          {/* Rating System (From Intelligence Branch) */}
          <AnimatePresence>
            {!isActive && rating > 0 && (
              <motion.div 
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex flex-col items-center gap-2 mb-2 p-3 bg-white/5 rounded-2xl border border-white/10"
              >
                <div className="flex gap-2">
                  {[1, 2, 3, 4, 5].map((star) => (
                    <Star 
                      key={star}
                      size={14} 
                      fill={rating >= star ? '#F59E0B' : 'transparent'} 
                      className={rating >= star ? 'text-amber-500' : 'text-white/10'}
                    />
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Connection status label (read-only — controlled by TrainingRoom) */}
          <div className={`w-full h-10 rounded-2xl text-[10px] font-black uppercase tracking-[0.2em] flex items-center justify-center gap-3 border ${
              isActive
                ? 'bg-white/5 text-white/60 border-white/10'
                : 'bg-white/5 text-white/30 border-white/5'
          }`}>
            {isActive
              ? <><Activity size={12} className="animate-pulse" style={{ color: theme.color }} /> Neural Link Active</>
              : <><Play size={12} className="opacity-40" /> En attente de session</>}
          </div>
        </div>
      </div>

      {/* Decorative Scanline Effect when Active */}
      {isActive && (
        <div className="absolute inset-0 pointer-events-none opacity-[0.03] z-40 bg-[linear-gradient(rgba(18,16,16,0)_50%,rgba(0,0,0,0.25)_50%),linear-gradient(90deg,rgba(255,0,0,0.06),rgba(0,255,0,0.02),rgba(0,0,255,0.06))] bg-[length:100%_2px,3px_100%]" />
      )}
    </div>
  );
}

