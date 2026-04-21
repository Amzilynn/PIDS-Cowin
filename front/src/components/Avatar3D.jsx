import React, { useState, useEffect, useRef } from 'react';
import { Play, Square, Activity, Cpu } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const AVATAR_SERVICE = 'http://127.0.0.1:8001';

export default function Avatar3D({ type = 'doctor', manifestUrl }) {
  const [avatarState, setAvatarState] = useState('standby');
  // standby | waiting | streaming | idle
  const [isActive, setIsActive]     = useState(false);
  const [chunkCount, setChunkCount] = useState(0);
  const [totalFrames, setTotalFrames] = useState(0);

  const videoRef   = useRef(null);
  const audioRef   = useRef(null);
  const pollRef    = useRef(null);

  const theme = {
    doctor:     { color: '#4E8C8A', light: '#0D9488', name: 'Dr. Martin (Médecin)'         },
    pharmacist: { color: '#10B981', light: '#059669', name: 'Mme Berthier (Pharmacienne)'  },
    delegate:   { color: '#1E3A8A', light: '#3B82F6', name: 'Sarah Khalil (Déléguée)'      },
  }[type] || { color: '#4E8C8A', light: '#0D9488', name: 'VITAL Agent' };

  // ── Status label ───────────────────────────────────────────────────────
  const statusLabel = {
    standby:   'Neural Standby',
    waiting:   'Generating Twin...',
    streaming: 'En ligne',
    idle:      'En ligne',
  }[avatarState] ?? 'En ligne';

  // ══════════════════════════════════════════════════════════════════════
  //  Progressive Streaming Engine
  //  When a new manifestUrl arrives, poll the manifest until chunks appear,
  //  then play them sequentially with seamless hand-off.
  // ══════════════════════════════════════════════════════════════════════
  useEffect(() => {
    console.log('[Avatar3D] manifestUrl changed:', manifestUrl);
    if (!manifestUrl) return;

    // Reset state for the new response
    console.log('[Avatar3D] Setting state to WAITING');
    setAvatarState('waiting');
    setChunkCount(0);

    // Mutable state owned by this effect closure (avoids stale-closure issues)
    let knownChunks  = [];
    let chunkPlayIdx = 0;
    let isDone       = false;
    let isPlaying    = false;

    const video = videoRef.current;
    if (!video) return;

    // Build the absolute manifest URL
    const absManifest = manifestUrl.startsWith('http')
      ? manifestUrl
      : `${AVATAR_SERVICE}${manifestUrl}`;

    // Absolute URL helper
    const getAbs = (url) => url.startsWith('http') ? url : `${AVATAR_SERVICE}${url}`;

    // ── Play the next available chunk ─────────────────────────────────
    const playNext = () => {
      if (chunkPlayIdx >= knownChunks.length) {
        // Buffer underrun — wait for more chunks
        isPlaying = false;
        if (isDone) {
          // All chunks played, return to standby portrait
          video.src = '';
          if (audioRef.current) audioRef.current.src = '';
          setAvatarState('standby');
        }
        return;
      }

      const chunk = knownChunks[chunkPlayIdx++];
      video.src = getAbs(chunk.url);
      video.load();
      video.play().catch(() => {});
      isPlaying = true;

      // Start MASTER audio only on the very first chunk
      if (chunkPlayIdx === 1 && audioRef.current && audioRef.current.src) {
        audioRef.current.play().catch(() => {});
      }
    };

    // ── On chunk ended → immediately play next ─────────────────────────
    const onEnded = () => { playNext(); };
    video.addEventListener('ended', onEnded);

    // ── Manifest polling (every 2.5 s) ─────────────────────────────────
    pollRef.current = setInterval(async () => {
      try {
        const res      = await fetch(absManifest);
        const manifest = await res.json();

        // 1. Prepare Audio Master track
        if (manifest.audio_url && (!audioRef.current.src || audioRef.current.src === window.location.href)) {
           audioRef.current.src = getAbs(manifest.audio_url);
           audioRef.current.load();
        }

        // 2. Detect newly published chunks
        if (manifest.chunks && manifest.chunks.length > knownChunks.length) {
          const added = manifest.chunks.slice(knownChunks.length);
          knownChunks = [...knownChunks, ...added];
          setChunkCount(knownChunks.length);

          // First chunk just arrived — switch to streaming mode and play
          if (!isPlaying && chunkPlayIdx === 0) {
            setAvatarState('streaming');
            setIsActive(true);
            window.dispatchEvent(new CustomEvent('avatarStreamStart'));
            playNext();
          } else if (!isPlaying) {
            // Buffer recovered after underrun
            playNext();
          }
        }

        if (manifest.total_frames) setTotalFrames(manifest.total_frames);

        if (manifest.done) {
          isDone = true;
          // Failsafe: if it finishes but no chunks fired the event, fire it now to unblock chat
          window.dispatchEvent(new CustomEvent('avatarStreamStart'));
          clearInterval(pollRef.current);
        }
      } catch (_) {
        // Service not yet ready — silently retry
      }
    }, 2500);

    return () => {
      clearInterval(pollRef.current);
      video.removeEventListener('ended', onEnded);
      video.src = '';
    };
  }, [manifestUrl]);

  // ── Manual session controls ────────────────────────────────────────────
  const startSession = () => {
    setAvatarState('standby');
    setIsActive(true);
  };
  const endSession = () => {
    setAvatarState('standby');
    setIsActive(false);
    if (videoRef.current) videoRef.current.src = '';
  };

  // ── Progress percentage ────────────────────────────────────────────────
  const framesPerChunk = 25;
  const progressPct = totalFrames > 0
    ? Math.min(Math.round((chunkCount * framesPerChunk / totalFrames) * 100), 99)
    : 0;

  return (
    <div className="h-full w-full flex flex-col items-center justify-between relative overflow-hidden p-6 bg-brand-navy/50 rounded-4xl border border-white/10 shadow-2xl backdrop-blur-3xl transition-all group">

      {/* Background Glows */}
      <div className="absolute -top-24 -right-24 w-80 h-80 opacity-20 rounded-full blur-[100px] animate-pulse-slow"
           style={{ backgroundColor: theme.color }} />
      <div className="absolute -bottom-24 -left-24 w-80 h-80 opacity-10 rounded-full blur-[100px] animate-pulse-slow delay-1000"
           style={{ backgroundColor: theme.light }} />

      {/* Status Bar */}
      <div className="w-full flex items-center justify-between relative z-10">
        <div className="flex items-center gap-3 bg-white/5 backdrop-blur-xl px-5 py-2.5 rounded-full border border-white/10 shadow-lg">
          <div
            className={`w-2.5 h-2.5 rounded-full transition-all duration-500 ${isActive ? 'animate-pulse' : ''}`}
            style={{
              backgroundColor: avatarState === 'streaming'
                ? theme.color
                : avatarState === 'waiting'
                ? '#3B82F6'
                : 'rgba(255,255,255,0.2)',
              boxShadow: isActive ? `0 0 10px ${theme.color}` : 'none',
            }}
          />
          <span className="text-[10px] font-black uppercase tracking-[0.2em] text-white/80">
            {statusLabel}
          </span>
        </div>

        {/* Neural Link indicator */}
        <div className={`flex items-center gap-2 text-white/40 transition-all duration-500 ${isActive ? 'opacity-100' : 'opacity-0'}`}>
          <Activity size={14} className="animate-pulse" style={{ color: theme.color }} />
          <span className="text-[9px] font-black uppercase tracking-widest leading-none">Neural Link Active</span>
        </div>
      </div>

      {/* ── Main Avatar Area ───────────────────────────────────────────── */}
      <div className="relative w-full flex-1 flex flex-col items-center justify-center min-h-[350px] mt-4 mb-4">
        <AnimatePresence mode="wait">

          {/* Waiting — Avatar Thinking State */}
          {avatarState === 'waiting' && (
            <motion.div
              key="waiting"
              initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              className="relative group/avatar w-full h-full flex items-center justify-center z-20"
            >
              <div className="w-64 h-64 rounded-full border-2 border-brand-teal flex items-center justify-center bg-white/5 backdrop-blur-3xl overflow-hidden shadow-[0_0_50px_rgba(20,184,166,0.15)] relative">
                
                {/* Active "Thinking" Breathing Animation Layer */}
                <motion.div 
                  className="absolute inset-0 z-0 opacity-40 bg-brand-teal"
                  animate={{ scale: [1, 1.1, 1], opacity: [0.2, 0.4, 0.2] }}
                  transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut" }}
                />

                <img
                  src="/avalive.jpg"
                  alt="Sarah Khalil Processing"
                  className="w-full h-full object-cover transform scale-110 relative z-10"
                />
              </div>

              {/* Minimal Thinking Badge */}
              <div className="absolute -bottom-4 bg-brand-navy border border-brand-teal/30 px-6 py-2.5 rounded-full shadow-2xl flex items-center gap-3">
                <div className="flex gap-1">
                   <div className="w-1.5 h-1.5 bg-brand-teal rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                   <div className="w-1.5 h-1.5 bg-brand-teal rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                   <div className="w-1.5 h-1.5 bg-brand-teal rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
                <span className="text-[10px] font-black tracking-widest text-brand-teal uppercase">Thinking...</span>
              </div>
            </motion.div>
          )}

          {/* Streaming — hidden video element, shown via CSS */}
          {/* NOTE: the <video> element is ALWAYS mounted (below) so we never
              lose the event listener. We just toggle visibility here. */}

          {/* Standby — portrait with idle animations */}
          {(avatarState === 'standby' || avatarState === 'idle') && (
            <motion.div
              key="standby"
              initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              className="relative group/avatar w-full h-full flex items-center justify-center"
            >
              <div className="w-64 h-64 rounded-full border-2 border-white/10 flex items-center justify-center bg-white/5 backdrop-blur-3xl overflow-hidden shadow-[0_0_50px_rgba(255,255,255,0.05)] relative">
                
                {/* Breathing Animation Layer */}
                <motion.div 
                  className="absolute inset-0 z-0 opacity-20"
                  animate={{ scale: [1, 1.05, 1], opacity: [0.1, 0.3, 0.1] }}
                  transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
                  style={{ backgroundColor: theme.color }}
                />

                <motion.img
                  src="/avalive.jpg"
                  alt="Sarah Khalil"
                  className="w-full h-full object-cover transform scale-110"
                  animate={{ scale: [1.1, 1.12, 1.1] }}
                  transition={{ duration: 8, repeat: Infinity, ease: "easeInOut" }}
                />

                {/* Subtle Blink Overlay */}
                <motion.div 
                  className="absolute inset-0 bg-brand-navy opacity-0 pointer-events-none"
                  animate={{ opacity: [0, 0, 0.8, 0, 0] }}
                  transition={{ 
                    duration: 0.15, 
                    repeat: Infinity, 
                    repeatDelay: 5,
                    times: [0, 0.4, 0.5, 0.6, 1] 
                  }}
                />

                <div className="absolute inset-0 bg-gradient-to-t from-brand-navy/60 via-transparent to-transparent opacity-60" />
              </div>

              {/* Glowing Pulse Ring */}
              <motion.div 
                className="absolute w-72 h-72 rounded-full border border-white/5" 
                animate={{ scale: [1, 1.1, 1], opacity: [0.1, 0.5, 0.1] }}
                transition={{ duration: 3, repeat: Infinity }}
              />

              <div className="absolute inset-0 flex items-end justify-center pb-12 opacity-0 group-hover/avatar:opacity-100 transition-all duration-700">
                <div className="bg-white/10 backdrop-blur-md px-4 py-1.5 rounded-full border border-white/20">
                  <span className="text-[9px] font-black text-white uppercase tracking-[0.3em]">Neural Standby</span>
                </div>
              </div>
            </motion.div>
          )}

        </AnimatePresence>

        {/* ── Always-mounted video element ──────────────────────────────
            Visibility is controlled via CSS so the event listener persists.
        ─────────────────────────────────────────────────────────────── */}
        <motion.video
          ref={videoRef}
          playsInline
          muted={true}
          className="absolute inset-0 h-full w-full object-contain rounded-3xl shadow-2xl border border-white/10"
          style={{
            // Show ONLY when actively streaming; otherwise transparent/hidden
            opacity:   avatarState === 'streaming' ? 1 : 0,
            pointerEvents: avatarState === 'streaming' ? 'auto' : 'none',
            transition: 'opacity 0.4s ease',
          }}
          animate={{ opacity: avatarState === 'streaming' ? 1 : 0 }}
          transition={{ duration: 0.4 }}
        />

        {/* Hidden Master Audio Sync Track */}
        <audio ref={audioRef} className="hidden" />
      </div>

      {/* ── Footer: Name + Connect Button ─────────────────────────────────── */}
      <div className="w-full space-y-6 relative z-10 px-4">
        <div className="flex flex-col items-center gap-2">
          <h3 className="text-xl font-black text-white tracking-tighter leading-none italic uppercase">
            {theme.name}
          </h3>
          <div className="h-1 w-10 rounded-full opacity-40" style={{ backgroundColor: theme.color }} />
        </div>

        <button
          onClick={isActive ? endSession : startSession}
          className={`w-full h-14 rounded-2xl text-[11px] font-black uppercase tracking-[0.25em] transition-all shadow-2xl flex items-center justify-center gap-4 transform active:scale-[0.98] border ${
            isActive
              ? 'bg-rose-500/10 text-rose-500 border-rose-500/20 hover:bg-rose-500/20'
              : 'bg-white text-brand-navy border-white hover:scale-[1.02]'
          }`}
        >
          {isActive ? <Square size={16} fill="currentColor" /> : <Play size={16} fill="currentColor" />}
          {isActive ? 'Disconnect' : 'Establish Link'}
        </button>
      </div>
    </div>
  );
}
