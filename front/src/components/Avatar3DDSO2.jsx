import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { io } from 'socket.io-client';

const AVATAR_SOCKET_URL = 'http://127.0.0.1:8027';

export default function Avatar3DDSO2({ isActive = false, onDisconnect, onConnect }) {
  const [avatarState, setAvatarState] = useState('standby');
  const [liveFrame, setLiveFrame] = useState(null);
  const socketRef = useRef(null);

  useEffect(() => {
    if (isActive) {
      const socket = io(AVATAR_SOCKET_URL);
      socketRef.current = socket;
      socket.on('connect', () => setAvatarState('idle'));
      socket.on('avatar_frame', (data) => {
        setLiveFrame(`data:image/jpeg;base64,${data.frame}`);
        setAvatarState('streaming');
      });
      socket.on('avatar_audio', (data) => {
        const audio = new Audio(`data:audio/mpeg;base64,${data.audio}`);
        audio.onplaying = () => socket.emit('audio_started', {});
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
    <div className="h-full w-full relative overflow-hidden bg-slate-900 rounded-[32px] shadow-2xl flex flex-col">
      
      {/* Neural Status Indicator */}
      <div className="absolute top-8 left-8 z-20 flex items-center gap-3 bg-black/20 backdrop-blur-md px-4 py-2 rounded-full border border-white/10">
          <div className={`w-2 h-2 rounded-full ${isActive ? 'bg-indigo-400 animate-pulse shadow-[0_0_8px_#818cf8]' : 'bg-white/20'}`} />
          <span className="text-[10px] font-black uppercase tracking-[0.2em] text-white/80">
              {isActive ? 'LIVE CONNECTION' : 'STANDBY'}
          </span>
      </div>

      {/* Avatar Image Feed */}
      <div className="flex-1 relative">
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
              <div className="absolute inset-0 bg-gradient-to-t from-slate-900 via-transparent to-transparent" />
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

      {/* Bottom Identity & Control DSO2 Style */}
      <div className="p-8 absolute bottom-0 left-0 right-0 z-30 flex flex-col gap-6 bg-gradient-to-t from-slate-950 via-slate-950/40 to-transparent">
         {!isActive ? (
            <button 
              onClick={onConnect}
              className="w-full h-14 bg-white text-slate-900 rounded-xl text-[11px] font-black uppercase tracking-widest flex items-center justify-center gap-3 hover:bg-slate-50 transition-all shadow-xl"
            >
               <div className="w-2 h-2 bg-indigo-600 rounded-full animate-pulse" />
               Establish Connection
            </button>
         ) : (
            <>
               <div className="space-y-1">
                  <h3 className="text-2xl font-black text-white tracking-tighter italic uppercase leading-none">
                     SARAH KHALIL <span className="text-white/40 font-bold not-italic text-lg">(DÉLÉGUÉE)</span>
                  </h3>
               </div>

               <button 
                 onClick={onDisconnect}
                 className="w-full h-12 bg-white text-slate-900 rounded-xl text-[11px] font-black uppercase tracking-widest flex items-center justify-center gap-3 hover:bg-slate-100 transition-all shadow-xl"
               >
                  <div className="w-2 h-2 bg-slate-900" />
                  Disconnect Session
               </button>
            </>
         )}
      </div>
    </div>
  );
}
