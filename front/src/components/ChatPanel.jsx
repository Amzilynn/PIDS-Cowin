import React, { useState, useRef, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { Bot, Mic, MicOff, Send, Activity, X } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export default function ChatPanel({ onSpeakingState, onVolumeSync, onManifest, avatarSessionId = null, isActive = false }) {
  const [messages, setMessages] = useState([]);
  const [isRecording, setIsRecording] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [sessionError, setSessionError] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [avatarSpeaking, setAvatarSpeaking] = useState(false);

  const scrollRef = useRef(null);
  const timerRef = useRef(null);
  const recognitionRef = useRef(null);
  const sessionInitializedRef = useRef(false);
  const chatFeedRef = useRef(null);

  const audioRef = useRef(null);
  const audioCtxRef = useRef(null);

  const { user } = useAuth();

  // ─── Init Audio ───────────────────────────────────────────────────────────
  useEffect(() => {
    if (!audioRef.current) {
      audioRef.current = new Audio();
      audioRef.current.crossOrigin = 'anonymous';
      audioRef.current.addEventListener('play', () => {
        setAvatarSpeaking(true);
        if (onSpeakingState) onSpeakingState(true);
      });
      audioRef.current.onended = () => {
        setAvatarSpeaking(false);
        if (onSpeakingState) onSpeakingState(false);
        if (onVolumeSync) onVolumeSync(0);
      };
    }
  }, []);

  // ─── Web Speech API ───────────────────────────────────────────────────────
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) return;

    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'fr-FR';

    recognition.onresult = (event) => {
      const t = Array.from(event.results).map(r => r[0].transcript).join('');
      setTranscript(t);
    };

    recognition.onerror = (e) => {
      console.error('STT Error', e);
      setIsRecording(false);
      clearInterval(timerRef.current);
      setRecordingTime(0);
    };

    recognitionRef.current = recognition;
  }, []);

  // ─── Session Init ─────────────────────────────────────────────────────────
  useEffect(() => {
    if (!isActive || sessionInitializedRef.current) return;
    sessionInitializedRef.current = true;

    let currentSessionId = null;

    const initSession = async () => {
      try {
        const queryParams = new URLSearchParams(window.location.search);
        const urlProductId = queryParams.get('productId') || 1;

        const res = await fetch('http://127.0.0.1:8001/api/training/start', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            delegue_id: user?.user_id || 1,
            product_id: parseInt(urlProductId)
          })
        });

        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();

        if (data?.session_id) {
          setSessionId(data.session_id);
          currentSessionId = data.session_id;
          setSessionError(false);
        } else {
          throw new Error('Missing session_id');
        }
      } catch (err) {
        console.error('[ChatPanel] Session init error:', err);
        setSessionError(true);
        sessionInitializedRef.current = false;
      }
    };

    initSession();

    return () => {
      if (currentSessionId) {
        fetch('http://127.0.0.1:8001/api/training/stop', { method: 'POST' }).catch(() => {});
      }
      if (audioCtxRef.current && audioCtxRef.current.state !== 'closed') {
        audioCtxRef.current.close().catch(() => {});
      }
    };
  }, [isActive]);

  // ─── chat_feed SSE → bot text responses in panel ─────────────────────────
  useEffect(() => {
    if (!isActive || !sessionId) return;

    const es = new EventSource('http://127.0.0.1:8001/api/training/chat_feed');
    chatFeedRef.current = es;

    es.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        // Only show bot messages (user msgs already added locally)
        if (msg.role === 'bot' && msg.content) {
          setIsTyping(false);
          setMessages(prev => [...prev, {
            id: Date.now(),
            text: msg.content,
            sender: 'bot',
            time: new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })
          }]);
        }
      } catch (_) {}
    };

    es.onerror = () => { es.close(); };

    return () => { es.close(); };
  }, [isActive, sessionId]);

  // ─── Auto-scroll ──────────────────────────────────────────────────────────
  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [messages, isTyping]);

  // ─── Recording timer ──────────────────────────────────────────────────────
  useEffect(() => {
    if (isRecording) {
      timerRef.current = setInterval(() => setRecordingTime(t => t + 1), 1000);
    } else {
      clearInterval(timerRef.current);
      setRecordingTime(0);
    }
    return () => clearInterval(timerRef.current);
  }, [isRecording]);

  // ─── PTT: Start ───────────────────────────────────────────────────────────
  const handleStartRecording = () => {
    if (!recognitionRef.current || isRecording || avatarSpeaking || isTyping) return;
    setTranscript('');
    try {
      recognitionRef.current.start();
      setIsRecording(true);
    } catch (e) { console.error('Recognition start error:', e); }
  };

  // ─── PTT: Stop + Send immediately ────────────────────────────────────────
  const handleStopAndSend = async () => {
    if (!isRecording) return;

    try { recognitionRef.current.stop(); } catch (e) {}
    setIsRecording(false);

    const textToSend = transcript.trim();
    setTranscript('');

    if (!textToSend || !sessionId) return;

    // Add user bubble immediately
    setMessages(prev => [...prev, {
      id: Date.now(),
      text: textToSend,
      sender: 'user',
      time: new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })
    }]);
    setIsTyping(true);

    // Send to backend — response will arrive via chat_feed SSE
    try {
      await fetch('http://127.0.0.1:8001/api/training/speech_text', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: textToSend, lang: 'fr' })
      });
      // bot response arrives via chat_feed SSE → setIsTyping(false) is called there
    } catch (err) {
      console.error('[ChatPanel] Send error:', err);
      setIsTyping(false);
    }
  };

  const formatTime = (s) => `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`;

  const sessionReady = sessionId && !sessionError;
  const canRecord = sessionReady && !avatarSpeaking && !isTyping;

  return (
    <div className="flex flex-col h-full bg-white rounded-[32px] border border-md-outline/10 overflow-hidden font-sans">

      {/* ── Header ── */}
      <div className="px-6 py-4 border-b border-slate-100 bg-white flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-xl bg-md-primary/10 flex items-center justify-center text-md-primary">
            <Bot size={18} />
          </div>
          <div>
            <p className="text-[10px] font-black uppercase tracking-widest text-md-primary leading-none">Sarah</p>
            <p className="text-[11px] font-semibold text-slate-500 leading-none mt-0.5">
              {!isActive ? 'En attente de démarrage' :
               !sessionReady && !sessionError ? 'Connexion en cours...' :
               sessionError ? 'Erreur de connexion' :
               avatarSpeaking ? 'En train de répondre...' :
               isTyping ? 'Analyse en cours...' :
               isRecording ? 'Enregistrement...' :
               'Prête à vous écouter'}
            </p>
          </div>
        </div>
        <div className={`w-2.5 h-2.5 rounded-full transition-all duration-500 ${
          sessionError ? 'bg-rose-500' :
          sessionReady ? 'bg-emerald-500 animate-pulse shadow-[0_0_8px_#10b981]' :
          'bg-slate-300 animate-pulse'
        }`} />
      </div>

      {/* ── Messages ── */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto p-6 space-y-4 bg-gradient-to-b from-white via-slate-50/30 to-white">

        {messages.length === 0 && !isTyping && (
          <div className="h-full flex flex-col items-center justify-center opacity-20 select-none pointer-events-none">
            <Mic size={40} className="mb-3" />
            <p className="text-[11px] font-black uppercase tracking-widest">
              {isActive ? 'Appuyez pour parler' : 'Session non démarrée'}
            </p>
          </div>
        )}

        {messages.map((msg) => (
          <motion.div
            key={msg.id}
            initial={{ opacity: 0, y: 8, scale: 0.97 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            transition={{ duration: 0.25 }}
            className={`flex flex-col ${msg.sender === 'user' ? 'items-end' : 'items-start'}`}
          >
            <div className={`text-[9px] font-black uppercase tracking-widest mb-1 opacity-40 ${
              msg.sender === 'user' ? 'text-md-primary' : 'text-slate-500'
            }`}>
              {msg.sender === 'user' ? 'Vous' : 'Sarah'} · {msg.time}
            </div>
            <div className={`max-w-[88%] px-5 py-3 rounded-[20px] text-[14px] font-medium leading-relaxed ${
              msg.sender === 'user'
                ? 'bg-md-primary text-white rounded-tr-sm shadow-md shadow-md-primary/15'
                : 'bg-white text-slate-800 border border-slate-100 rounded-tl-sm shadow-sm'
            }`}>
              {msg.text}
            </div>
          </motion.div>
        ))}

        {/* Typing indicator — shown while waiting for SSE response */}
        {isTyping && (
          <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="flex items-start gap-2">
            <div className="flex items-center gap-1 bg-white border border-slate-100 shadow-sm px-4 py-3 rounded-[20px] rounded-tl-sm">
              <Activity size={12} className="text-md-primary animate-pulse mr-1" />
              {[0, 1, 2].map(i => (
                <motion.div
                  key={i}
                  animate={{ scale: [1, 1.4, 1], opacity: [0.4, 1, 0.4] }}
                  transition={{ duration: 0.8, repeat: Infinity, delay: i * 0.2 }}
                  className="w-1.5 h-1.5 bg-slate-300 rounded-full"
                />
              ))}
            </div>
          </motion.div>
        )}
      </div>

      {/* ── PTT Voice Control ── */}
      <div className="p-6 bg-white border-t border-slate-100 flex flex-col items-center gap-4">

        {/* Live transcript preview while recording */}
        <AnimatePresence>
          {isRecording && transcript && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-2xl text-[13px] text-slate-700 font-medium italic text-center leading-relaxed"
            >
              "{transcript}"
            </motion.div>
          )}
        </AnimatePresence>

        {/* PTT Button — 2 states: green (idle) / red pulsing (recording+send) */}
        <AnimatePresence mode="wait">
          {!isRecording ? (
            /* ── GREEN: press to start ── */
            <motion.button
              key="ptt-idle"
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              whileHover={canRecord ? { scale: 1.04 } : {}}
              whileTap={canRecord ? { scale: 0.96 } : {}}
              onClick={handleStartRecording}
              disabled={!canRecord}
              className={`flex items-center gap-3 px-10 py-4 rounded-full font-black text-[12px] uppercase tracking-widest shadow-lg transition-all duration-200 ${
                !canRecord
                  ? 'bg-slate-200 text-slate-400 cursor-not-allowed shadow-none'
                  : 'bg-emerald-500 hover:bg-emerald-400 text-white shadow-emerald-500/30 cursor-pointer'
              }`}
            >
              <Mic size={20} />
              {!isActive ? 'Session non démarrée' :
               !sessionReady ? 'Connexion...' :
               avatarSpeaking ? 'Sarah parle...' :
               isTyping ? 'Analyse en cours...' :
               'Appuyer pour parler'}
            </motion.button>
          ) : (
            /* ── RED: recording — press again to stop AND send ── */
            <motion.button
              key="ptt-recording"
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              whileTap={{ scale: 0.96 }}
              onClick={handleStopAndSend}
              className="relative flex items-center gap-3 px-10 py-4 rounded-full font-black text-[12px] uppercase tracking-widest bg-rose-500 text-white shadow-lg shadow-rose-500/30 cursor-pointer overflow-hidden"
            >
              {/* Pulse ring */}
              <motion.div
                className="absolute inset-0 rounded-full bg-rose-400"
                animate={{ scale: [1, 1.09, 1], opacity: [0.6, 0, 0.6] }}
                transition={{ duration: 1.2, repeat: Infinity }}
              />
              <Send size={18} className="relative z-10" />
              <span className="relative z-10">Envoyer · {formatTime(recordingTime)}</span>
              {/* Waveform bars */}
              <div className="relative z-10 flex items-end gap-0.5 h-4 ml-1">
                {[...Array(5)].map((_, i) => (
                  <motion.div
                    key={i}
                    animate={{ height: [`${20 + i * 10}%`, `${55 + Math.random() * 45}%`, `${20 + i * 10}%`] }}
                    transition={{ duration: 0.4, repeat: Infinity, delay: i * 0.08 }}
                    className="w-0.5 bg-white/70 rounded-full"
                    style={{ minHeight: '3px' }}
                  />
                ))}
              </div>
            </motion.button>
          )}
        </AnimatePresence>

        {/* Error message */}
        {sessionError && isActive && (
          <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }}
            className="text-[10px] font-bold text-rose-500 uppercase tracking-wider">
            ⚠ Impossible de se connecter au serveur DSO1 (port 8001)
          </motion.p>
        )}
      </div>
    </div>
  );
}
