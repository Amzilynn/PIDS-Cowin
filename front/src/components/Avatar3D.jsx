import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Play, Square, Activity, Wifi } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const AVATAR_API_SERVICE = 'http://localhost:8011';

export default function Avatar3D({ type = 'doctor', manifestUrl }) {
  const [avatarState, setAvatarState] = useState('standby');
  const [isActive, setIsActive] = useState(false);
  const [chunkCount, setChunkCount] = useState(0);
  const [totalFrames, setTotalFrames] = useState(0);
  const [isMuted, setIsMuted] = useState(true);

  const videoRef = useRef(null);
  const pollRef = useRef(null);
  const mediaSourceRef = useRef(null);
  const sourceBufferRef = useRef(null);
  const chunkQueueRef = useRef([]);
  const lastManifestRef = useRef(null);

  const theme = {
    doctor:     { color: '#4E8C8A', light: '#0D9488', name: 'Dr. Martin (Médecin)'         },
    pharmacist: { color: '#10B981', light: '#059669', name: 'Mme Berthier (Pharmacienne)'  },
    delegate:   { color: '#1E3A8A', light: '#3B82F6', name: 'Sarah Khalil (Déléguée)'      },
  }[type] || { color: '#4E8C8A', light: '#0D9488', name: 'VITAL Agent' };

  // Stable state ref for callbacks
  const stateRef = useRef(avatarState);
  useEffect(() => { stateRef.current = avatarState; }, [avatarState]);

  const flushQueue = useCallback(() => {
    const sb = sourceBufferRef.current;
    const ms = mediaSourceRef.current;
    const queue = chunkQueueRef.current;
    const video = videoRef.current;
    const currState = stateRef.current;

    if (!sb || !ms || ms.readyState !== 'open' || sb.updating || queue.length === 0) return;
    
    try {
        const buf = queue.shift();
        sb.appendBuffer(buf);
        if (currState === 'waiting' || currState === 'standby') {
            setAvatarState('streaming');
            setIsActive(true);
            if (video && video.paused) {
                video.play().catch(() => {});
            }
        }
    } catch (e) {
        console.warn('[Avatar3D MSE] append error:', e);
    }
  }, []); // Truly stable

  const stopAvatarStream = useCallback(() => {
    if (pollRef.current) {
        clearInterval(pollRef.current);
        pollRef.current = null;
    }
    if (sourceBufferRef.current) {
        try { sourceBufferRef.current.removeEventListener('updateend', flushQueue); } catch (e) {}
        sourceBufferRef.current = null;
    }
    if (mediaSourceRef.current && mediaSourceRef.current.readyState === 'open') {
        try { mediaSourceRef.current.endOfStream(); } catch(e) {}
    }
    mediaSourceRef.current = null;
    chunkQueueRef.current = [];
  }, [flushQueue]);

  const startAvatarStream = useCallback(async (mUrl) => {
    if (!mUrl || mUrl === lastManifestRef.current) return;
    lastManifestRef.current = mUrl;
    
    const video = videoRef.current;
    if (!video) return;

    console.log("[Avatar3D] Starting stream:", mUrl);
    stopAvatarStream();
    setAvatarState('waiting');
    setChunkCount(0);
    setTotalFrames(0);

    const API_BASE = 'http://localhost:8011';
    const absManifest = mUrl.startsWith('http') ? mUrl : `${API_BASE}${mUrl}`;
    let seenChunks = 0;
    const pollStart = Date.now();

    const ms = new MediaSource();
    mediaSourceRef.current = ms;
    video.src = URL.createObjectURL(ms);

    ms.addEventListener('sourceopen', () => {
        try {
            if (ms.readyState !== 'open') return;
            const sb = ms.addSourceBuffer('video/mp4; codecs="avc1.42E01E"');
            sb.mode = 'sequence';
            sourceBufferRef.current = sb;
            sb.addEventListener('updateend', flushQueue);
            console.log("[Avatar3D MSE] Ready");
        } catch (e) {
            console.error('[Avatar3D MSE] init failed:', e);
        }
    }, { once: true });

    pollRef.current = setInterval(async () => {
        if (Date.now() - pollStart > 300000) { 
            stopAvatarStream();
            return;
        }

        try {
            const res = await fetch(`${absManifest}?t=${Date.now()}`);
            if (!res.ok) return;
            const manifest = await res.json();
            
            if (manifest.total_frames) setTotalFrames(manifest.total_frames);
            
            const allChunks = manifest.chunks || [];
            const newChunks = allChunks.slice(seenChunks);
            
            if (newChunks.length > 0) {
                console.log(`[Avatar3D Poll] Found ${newChunks.length} chunks`);
                for (const chunk of newChunks) {
                    const cUrl = chunk.url.startsWith('http') ? chunk.url : `${API_BASE}${chunk.url}`;
                    const cRes = await fetch(cUrl);
                    if (!cRes.ok) continue;
                    const buf = await cRes.arrayBuffer();
                    chunkQueueRef.current.push(buf);
                    setChunkCount(prev => prev + 1);
                    seenChunks++;
                }
            }
            
            if (chunkQueueRef.current.length > 0) flushQueue();

            if (manifest.done || manifest.status === 'complete') {
                if (seenChunks >= allChunks.length && chunkQueueRef.current.length === 0) {
                    clearInterval(pollRef.current);
                    pollRef.current = null;
                    setAvatarState('idle');
                }
            }
        } catch (e) { console.warn('[Avatar3D Poll] error:', e.message); }
    }, 1000);

  }, [stopAvatarStream, flushQueue]);

  useEffect(() => {
    if (manifestUrl) startAvatarStream(manifestUrl);
    return () => stopAvatarStream();
  }, [manifestUrl, startAvatarStream, stopAvatarStream]);

  const progressPct = totalFrames > 0 ? Math.min(Math.round((chunkCount * 4 / totalFrames) * 100), 99) : 0;

  return (
    <div className="h-full w-full flex flex-col items-center justify-between relative overflow-hidden p-6 bg-brand-navy/50 rounded-4xl border border-white/10 shadow-2xl backdrop-blur-3xl transition-all group">
      <div className="absolute -top-24 -right-24 w-80 h-80 opacity-20 rounded-full blur-[100px]" style={{ backgroundColor: theme.color }} />
      <div className="w-full flex items-center justify-between relative z-10">
        <div className="flex items-center gap-3 bg-white/5 backdrop-blur-xl px-5 py-2.5 rounded-full border border-white/10">
          <div className={`w-2.5 h-2.5 rounded-full ${isActive ? 'animate-pulse' : ''}`}
               style={{ backgroundColor: avatarState === 'streaming' ? theme.color : '#3B82F6' }} />
          <span className="text-[10px] font-black uppercase tracking-[0.2em] text-white">
            {avatarState === 'waiting' ? 'Generating...' : 'Neural Link Active'}
          </span>
        </div>
        {avatarState === 'waiting' && (
           <div className="flex items-center gap-2 text-white/40">
              <Activity size={14} className="animate-pulse" style={{ color: theme.color }} />
              <span className="text-[9px] font-black uppercase tracking-widest">Rendering {progressPct}%</span>
           </div>
        )}
      </div>

      <div className="relative w-full flex-1 flex flex-col items-center justify-center min-h-[350px] mt-4 mb-4">
        <AnimatePresence mode="wait">
          {avatarState !== 'streaming' && chunkCount === 0 && (
            <motion.div key="idle" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="relative w-full h-full flex items-center justify-center">
              <div className="w-64 h-64 rounded-full border-2 border-white/10 overflow-hidden relative">
                <img src="/avalive.jpg" alt="Avatar" className="w-full h-full object-cover transform scale-110" />
                <div className="absolute inset-0 bg-gradient-to-t from-brand-navy/60 to-transparent" />
              </div>
              {avatarState === 'waiting' && (
                <div className="absolute -bottom-4 bg-brand-navy border border-brand-teal/30 px-6 py-2.5 rounded-full flex items-center gap-3">
                   <div className="flex gap-1">
                      <div className="w-1.5 h-1.5 bg-brand-teal rounded-full animate-bounce" />
                      <div className="w-1.5 h-1.5 bg-brand-teal rounded-full animate-bounce delay-100" />
                      <div className="w-1.5 h-1.5 bg-brand-teal rounded-full animate-bounce delay-200" />
                   </div>
                   <span className="text-[10px] font-black tracking-widest text-brand-teal uppercase">Neural Link Syncing...</span>
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>

        <video
          ref={videoRef}
          autoPlay
          playsInline
          muted={isMuted}
          className="absolute inset-0 h-full w-full object-cover transform scale-110 rounded-full shadow-2xl border border-white/10"
          style={{ opacity: (avatarState === 'streaming' || chunkCount > 0) ? 1 : 0, zIndex: 30, pointerEvents: 'none' }}
        />

        {avatarState === 'streaming' && isMuted && (
          <button onClick={() => setIsMuted(false)} className="absolute z-50 bg-white/10 backdrop-blur-3xl border border-white/20 p-6 rounded-full">
            <Wifi size={32} className="text-white animate-pulse" />
            <span className="text-[10px] font-black uppercase tracking-[0.2em] text-white">Unmute</span>
          </button>
        )}
      </div>

      <div className="w-full space-y-6 relative z-10 px-4">
        <div className="flex flex-col items-center gap-2">
          <h3 className="text-xl font-black text-white tracking-tighter italic uppercase">{theme.name}</h3>
          <div className="h-1 w-10 rounded-full opacity-40" style={{ backgroundColor: theme.color }} />
        </div>
        <button onClick={() => setIsActive(!isActive)} className="w-full h-14 rounded-2xl bg-white text-brand-navy text-[11px] font-black uppercase tracking-[0.25em] flex items-center justify-center gap-4 border border-white">
          {isActive ? <Square size={16} fill="currentColor" /> : <Play size={16} fill="currentColor" />}
          {isActive ? 'Disconnect' : 'Establish Link'}
        </button>
      </div>
    </div>
  );
}
