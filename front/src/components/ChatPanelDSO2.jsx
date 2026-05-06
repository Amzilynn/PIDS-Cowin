import React, { useState, useRef, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { Bot, Mic, MicOff, Send, Activity, X, History, Plus, Sparkles } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

// Consistent DSO2 Teal Color Palette
const DSO2_COLORS = {
  primary: '#52b1a8',
  primaryLight: '#eef8f7',
  textDark: '#0f172a',
  textMuted: '#64748b',
  bgLight: '#fcfdfe'
};

export default function ChatPanelDSO2({ onSpeakingState, onVolumeSync, onManifest, isActive = true }) {
  const [showHistory, setShowHistory] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [messages, setMessages] = useState([]);
  const [historySessions, setHistorySessions] = useState(() => {
     const saved = localStorage.getItem('dso2_history');
     return saved ? JSON.parse(saved) : [];
  });

  // Save history to localStorage
  useEffect(() => {
     localStorage.setItem('dso2_history', JSON.stringify(historySessions));
  }, [historySessions]);

  const [isRecording, setIsRecording] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);

  const scrollRef = useRef(null);
  const timerRef = useRef(null);
  const recognitionRef = useRef(null);
  const [sessionId, setSessionId] = useState(null);
  const sessionInitializedRef = useRef(false);
  const { user } = useAuth();

  // ─── Session Init DSO2 (Port 8000) ────────────────────────────────────────
  useEffect(() => {
    if (!isActive || sessionInitializedRef.current) return;
    sessionInitializedRef.current = true;

    const initSession = async () => {
      try {
        const res = await fetch('http://127.0.0.1:8000/session/start', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            persona: "commercial", 
            session_id: `dso2_${Date.now()}`
          })
        });

        if (res.ok) {
          const data = await res.json();
          setSessionId(data.session_id);
          console.log("[DSO2] Session started:", data.session_id);
        }
      } catch (err) {
        console.error('[DSO2] Session init error:', err);
        sessionInitializedRef.current = false;
      }
    };

    initSession();
  }, [isActive]);

  // ─── Web Speech API (STT) ────────────────────────────────────────────────
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
    };

    recognitionRef.current = recognition;
  }, []);

  // ─── Recording Timer ─────────────────────────────────────────────────────
  useEffect(() => {
    if (isRecording) {
      timerRef.current = setInterval(() => setRecordingTime(t => t + 1), 1000);
    } else {
      clearInterval(timerRef.current);
      setRecordingTime(0);
    }
    return () => clearInterval(timerRef.current);
  }, [isRecording]);

  // ─── Auto-scroll ──────────────────────────────────────────────────────────
  useEffect(() => {
    if (scrollRef.current) {
      const { scrollHeight, clientHeight } = scrollRef.current;
      scrollRef.current.scrollTo({ top: scrollHeight - clientHeight, behavior: 'smooth' });
    }
  }, [messages, isTyping, transcript]);

  const handleSend = async (forcedText = null) => {
    const textToSend = forcedText || transcript.trim();
    if (!textToSend) return;

    setTranscript(''); 
    setMessages(prev => [...prev, {
      id: Date.now(),
      text: textToSend,
      sender: 'user',
      time: new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })
    }]);
    setIsTyping(true);

    try {
      const response = await fetch('http://127.0.0.1:8000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          session_id: sessionId || "dso2_test_session", 
          message: textToSend 
        })
      });
      
      const data = await response.json();
      setIsTyping(false);
      
      if (data.agent_response) {
         setMessages(prev => [...prev, {
            id: Date.now() + 1,
            text: data.agent_response,
            sender: 'bot',
            time: new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })
         }]);
      }
    } catch (err) {
      console.error('[DSO2 Chat] Error:', err);
      setTimeout(() => {
        setIsTyping(false);
        setMessages(prev => [...prev, {
          id: Date.now() + 1,
          text: "Je comprends votre demande. Permettez-moi de vous présenter nos solutions adaptées.",
          sender: 'bot',
          time: new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })
        }]);
      }, 1000);
    }
  };

  const toggleRecording = () => {
    if (!recognitionRef.current) return;
    if (isRecording) {
      recognitionRef.current.stop();
      setIsRecording(false);
      if (transcript.trim()) handleSend();
    } else {
      setTranscript('');
      recognitionRef.current.start();
      setIsRecording(true);
    }
  };

  return (
    <div className="flex flex-col h-full bg-white rounded-[40px] border border-slate-100/50 overflow-hidden font-sans shadow-[0_20px_50px_-20px_rgba(0,0,0,0.05)] relative">

      {/* ── Header Clean ── */}
      <div className="px-10 py-7 border-b border-slate-50 bg-white/80 backdrop-blur-xl flex items-center justify-between z-20">
        <h3 className="text-[12px] font-black uppercase tracking-[0.4em] text-slate-800 leading-none">Chat</h3>
        
        <div className="flex items-center gap-3">
           <button 
             onClick={() => {
                if (messages.length === 0) { setShowHistory(false); return; }
                setIsSaving(true);
                setTimeout(() => {
                   const firstMsg = messages.find(m => m.sender === 'user')?.text || "Nouvelle Session";
                   const newSession = {
                      id: Date.now(),
                      text: firstMsg.length > 30 ? firstMsg.substring(0, 30) + '...' : firstMsg,
                      time: new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' }),
                      data: [...messages]
                   };
                   setHistorySessions(prev => [newSession, ...prev]);
                   setMessages([]);
                   setShowHistory(false);
                   setIsSaving(false);
                }, 800);
             }}
             className={`flex items-center gap-2 px-5 py-2.5 rounded-2xl text-[10px] font-black uppercase tracking-widest transition-all ${
               !showHistory 
                 ? 'bg-[#52b1a8] text-white shadow-lg shadow-[#52b1a8]/20' 
                 : 'bg-slate-50 text-slate-500 hover:bg-slate-100'
             }`}
           >
             <Plus size={14} strokeWidth={3} /> New
           </button>
           <button 
             onClick={() => setShowHistory(true)}
             className={`flex items-center gap-2 px-5 py-2.5 rounded-2xl text-[10px] font-black uppercase tracking-widest transition-all ${
               showHistory 
                 ? 'bg-[#52b1a8] text-white shadow-lg shadow-[#52b1a8]/20' 
                 : 'bg-slate-50 text-slate-500 hover:bg-slate-100'
             }`}
           >
             <History size={14} strokeWidth={3} /> History
           </button>
        </div>
      </div>

      {/* ── Messages Feed ── */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto px-10 py-8 space-y-8 bg-[#fcfdfe]/50 scroll-smooth">
        {showHistory ? (
          <div className="space-y-4 relative z-10 animate-in fade-in slide-in-from-bottom-4 duration-500">
             <p className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] mb-6">Archives</p>
             {historySessions.length === 0 ? (
                <div className="py-20 text-center flex flex-col items-center gap-4 opacity-30">
                   <Sparkles size={40} strokeWidth={1} />
                   <p className="text-[11px] font-bold uppercase tracking-[0.3em]">Aucun historique</p>
                </div>
             ) : (
                historySessions.map((session) => (
                   <button 
                     key={session.id}
                     onClick={() => {
                        setMessages([...session.data]);
                        setShowHistory(false);
                     }}
                     className="w-full p-7 rounded-[32px] bg-white border border-slate-100 hover:border-[#52b1a8]/30 hover:shadow-2xl hover:shadow-[#52b1a8]/5 transition-all text-left group relative"
                   >
                      <div className="flex justify-between items-center mb-3">
                         <span className="text-[12px] font-black text-slate-800 uppercase tracking-tight group-hover:text-[#52b1a8] transition-colors">{session.text}</span>
                         <span className="text-[9px] font-bold text-slate-300 uppercase tracking-widest">{session.time}</span>
                      </div>
                      <p className="text-[12px] text-slate-400 font-medium line-clamp-1 italic">Reprendre l'échange...</p>
                   </button>
                ))
             )}
          </div>
        ) : (
          <AnimatePresence initial={false}>
            {messages.length === 0 && (
              <motion.div 
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="h-full flex flex-col items-center justify-center text-center p-12 opacity-10"
              >
                 <Bot size={60} strokeWidth={0.5} />
                 <p className="mt-6 text-[11px] font-black uppercase tracking-[0.4em]">Sarah est prête</p>
              </motion.div>
            )}
            {messages.map((msg) => (
              <motion.div 
                key={msg.id}
                initial={{ opacity: 0, y: 10, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                className={`flex flex-col ${msg.sender === 'user' ? 'items-end' : 'items-start'}`}
              >
                <div className={`max-w-[85%] px-7 py-5 rounded-[28px] text-[14px] font-medium leading-relaxed shadow-sm ${
                  msg.sender === 'user'
                    ? `text-white rounded-tr-lg shadow-lg shadow-[#52b1a8]/20`
                    : 'bg-white text-slate-800 rounded-tl-lg border border-slate-100'
                }`} style={{ background: msg.sender === 'user' ? `linear-gradient(135deg, ${DSO2_COLORS.primary}, #459b93)` : undefined }}>
                  {msg.text}
                </div>
                <span className="text-[9px] font-black text-slate-300 uppercase tracking-[0.2em] mt-3 px-2">
                   {msg.sender === 'user' ? 'Moi' : 'Sarah Khalil'} · {msg.time}
                </span>
              </motion.div>
            ))}
          </AnimatePresence>
        )}

        {isTyping && (
           <div className="flex items-center gap-2 bg-white border border-slate-100 px-6 py-4 rounded-full w-fit shadow-sm">
              <div className="w-1.5 h-1.5 bg-[#52b1a8] rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
              <div className="w-1.5 h-1.5 bg-[#52b1a8] rounded-full animate-bounce" style={{ animationDelay: '200ms' }} />
              <div className="w-1.5 h-1.5 bg-[#52b1a8] rounded-full animate-bounce" style={{ animationDelay: '400ms' }} />
           </div>
        )}
      </div>

      {/* ── Input Redesigned ── */}
      <div className="px-10 py-9 bg-white flex items-end gap-5 relative z-20">
         
         <button 
           onClick={toggleRecording}
           className={`w-14 h-14 rounded-2xl flex items-center justify-center transition-all shadow-xl hover:scale-105 active:scale-95 ${
             isRecording 
               ? 'bg-rose-500 text-white animate-pulse shadow-rose-500/30' 
               : 'bg-slate-50 text-slate-400 hover:bg-slate-100 hover:text-slate-600'
           }`}
         >
            {isRecording ? <MicOff size={22} /> : <Mic size={22} />}
         </button>

         <div className="flex-1 relative">
            <textarea 
              placeholder="Votre message..."
              value={transcript}
              onChange={(e) => setTranscript(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              rows={1}
              className="w-full min-h-[56px] max-h-40 bg-slate-50 border-none rounded-[24px] px-8 py-4 text-[14px] font-medium placeholder:text-slate-300 focus:bg-white focus:shadow-[0_0_0_2px_rgba(82,177,168,0.1)] outline-none transition-all resize-none overflow-y-auto"
            />
         </div>

         <button 
           onClick={() => handleSend()}
           className="w-14 h-14 text-white rounded-2xl flex items-center justify-center shadow-2xl hover:scale-110 active:scale-90 transition-all group overflow-hidden relative"
           style={{ background: `linear-gradient(135deg, ${DSO2_COLORS.primary}, #459b93)` }}
         >
            <div className="absolute inset-0 bg-white/20 translate-y-12 group-hover:translate-y-0 transition-transform duration-500" />
            <Send size={22} className="relative z-10" />
         </button>
      </div>

      {/* ── Saving Overlay ── */}
      <AnimatePresence>
         {isSaving && (
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="absolute inset-0 z-[100] bg-white/90 backdrop-blur-md flex flex-col items-center justify-center"
            >
               <div className="relative mb-8">
                  <div className="w-16 h-16 border-4 border-slate-100 rounded-full" />
                  <div className="absolute inset-0 w-16 h-16 border-4 border-[#52b1a8] border-t-transparent rounded-full animate-spin" />
               </div>
               <h4 className="text-[14px] font-black uppercase tracking-[0.3em] text-slate-800 mb-2">Archivage</h4>
            </motion.div>
         )}
      </AnimatePresence>
    </div>
  );
}
