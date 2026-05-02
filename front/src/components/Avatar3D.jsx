import React, { useState, useEffect, useRef } from 'react';
import { Play, Square, Activity, Wifi } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { io } from 'socket.io-client';

const AVATAR_SOCKET_URL = 'http://localhost:8027';

export default function Avatar3D({ type = 'delegate' }) {
  const [avatarState, setAvatarState] = useState('standby');
  const [isActive, setIsActive] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [liveFrame, setLiveFrame] = useState(null);

  const socketRef = useRef(null);
  const audioContextRef = useRef(null);

  const theme = {
    doctor:     { color: '#4E8C8A', light: '#0D9488', name: 'Dr. Martin (Médecin)'         },
    pharmacist: { color: '#10B981', light: '#059669', name: 'Mme Berthier (Pharmacienne)'  },
    delegate:   { color: '#1E3A8A', light: '#3B82F6', name: 'Sarah Khalil (Déléguée)'      },
  }[type] || { color: '#4E8C8A', light: '#0D9488', name: 'VITAL Agent' };

  // 1. WebSocket Initialization
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
        console.log("[Avatar3D] Audio received");
        const audio = new Audio(`data:audio/mpeg;base64,${data.audio}`);
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

  const toggleLink = () => {
    setIsActive(!isActive);
  };

  return (
    <div className="h-full w-full relative overflow-hidden bg-brand-navy rounded-[40px] border border-white/10 shadow-[0_8px_64px_-12px_rgba(0,0,0,0.6)] group">
      
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

      {/* 2. TOP OVERLAY: Neural Status */}
      <div className="absolute top-8 left-8 right-8 z-20 flex justify-between items-start pointer-events-none">
        <div className="flex items-center gap-3 bg-brand-navy/40 backdrop-blur-md px-5 py-2.5 rounded-full border border-white/10 pointer-events-auto">
          <div className={`w-2 h-2 rounded-full ${isActive ? 'animate-pulse' : ''}`}
               style={{ backgroundColor: avatarState === 'streaming' ? theme.color : '#3B82F6' }} />
          <span className="text-[10px] font-black uppercase tracking-[0.2em] text-white">
            {isActive ? (avatarState === 'streaming' ? 'Live Connection' : 'Syncing...') : 'Offline'}
          </span>
        </div>
        
        {isActive && avatarState === 'idle' && (
          <motion.div 
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="bg-brand-teal/20 backdrop-blur-md border border-brand-teal/40 px-5 py-2.5 rounded-full flex items-center gap-3"
          >
             <div className="flex gap-1">
                <div className="w-1 h-1 bg-brand-teal rounded-full animate-bounce [animation-delay:-0.3s]" />
                <div className="w-1 h-1 bg-brand-teal rounded-full animate-bounce [animation-delay:-0.15s]" />
                <div className="w-1 h-1 bg-brand-teal rounded-full animate-bounce" />
             </div>
             <span className="text-[9px] font-black tracking-widest text-brand-teal uppercase">Listening</span>
          </motion.div>
        )}
      </div>

      {/* 3. BOTTOM OVERLAY: Identity & Controls */}
      <div className="absolute bottom-0 left-0 right-0 z-30 p-8 pt-20 bg-gradient-to-t from-brand-navy via-brand-navy/60 to-transparent">
        <div className="flex flex-col gap-6">
          <div className="space-y-1">
            <h3 className="text-3xl font-black text-white tracking-tighter italic uppercase leading-none">
              {theme.name}
            </h3>
            <div className="h-1 w-16 rounded-full" style={{ backgroundColor: theme.color }} />
          </div>

          <button 
            onClick={toggleLink} 
            className="w-full h-16 rounded-3xl bg-white text-brand-navy text-[12px] font-black uppercase tracking-[0.3em] flex items-center justify-center gap-4 border-2 border-white hover:bg-transparent hover:text-white transition-all duration-500 group/btn overflow-hidden relative shadow-2xl"
          >
            <div className="absolute inset-0 bg-brand-navy translate-y-full group-hover/btn:translate-y-0 transition-transform duration-500" />
            <div className="relative z-10 flex items-center gap-3">
              {isActive ? <Square size={16} fill="currentColor" /> : <Play size={16} fill="currentColor" />}
              {isActive ? 'Disconnect Session' : 'Establish Link'}
            </div>
          </button>
        </div>
      </div>

      {/* Decorative Scanline Effect when Active */}
      {isActive && (
        <div className="absolute inset-0 pointer-events-none opacity-[0.03] z-40 bg-[linear-gradient(rgba(18,16,16,0)_50%,rgba(0,0,0,0.25)_50%),linear-gradient(90deg,rgba(255,0,0,0.06),rgba(0,255,0,0.02),rgba(0,0,255,0.06))] bg-[length:100%_2px,3px_100%]" />
      )}
    </div>
  );
}
