import React, { useState, useRef, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { Send, Mic, MicOff, Bot, FileText, Copy, Download, X, Volume2, VolumeX, MessageSquare, ArrowRight, PlusCircle } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export default function ChatPanel({ persona = 'medical', onSpeakingState, onVolumeSync, onVideoResponse }) {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [isTyping, setIsTyping] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [showHistory, setShowHistory] = useState(false);
  const [copied, setCopied] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [persistentHistory, setPersistentHistory] = useState([]);
  const [viewingSessionId, setViewingSessionId] = useState(null);
  const [sessionError, setSessionError] = useState(false);
  
  const scrollRef = useRef(null);
  const timerRef = useRef(null);
  const recognitionRef = useRef(null);
  const pendingBotMessageRef = useRef(null);
  
  // Audio state refs for Lip-Sync
  const audioRef = useRef(null);
  const audioCtxRef = useRef(null);
  const analyserRef = useRef(null);
  const sourceRef = useRef(null);

  // Sync avatar stream start with text reveal
  useEffect(() => {
    const handleAvatarStart = () => {
      if (pendingBotMessageRef.current) {
        setMessages(prev => [...prev, pendingBotMessageRef.current]);
        setIsTyping(false);
        pendingBotMessageRef.current = null;
      }
    };
    window.addEventListener('avatarStreamStart', handleAvatarStart);
    return () => window.removeEventListener('avatarStreamStart', handleAvatarStart);
  }, []);

  // Initialize Audio element on mount
  useEffect(() => {
    if (!audioRef.current) {
      audioRef.current = new Audio();
      audioRef.current.crossOrigin = "anonymous";
      
      audioRef.current.addEventListener('play', () => {
        if (onSpeakingState) onSpeakingState(true);
        if (onVolumeSync && analyserRef.current) {
           const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount);
           const syncLoop = () => {
             if (audioRef.current.paused || audioRef.current.ended) return;
             analyserRef.current.getByteFrequencyData(dataArray);
             let sum = 0;
             for (let i = 2; i < 20; i++) sum += dataArray[i];
             onVolumeSync(Math.min((sum / 18) / 120, 1.0));
             requestAnimationFrame(syncLoop);
           };
           syncLoop();
        }
      });

      audioRef.current.onended = () => {
        if (onSpeakingState) onSpeakingState(false);
        if (onVolumeSync) onVolumeSync(0);
      };
    }
  }, [onSpeakingState, onVolumeSync]);

  // Synchronise history
  useEffect(() => {
    const saved = localStorage.getItem('dso2_history');
    if (saved) setPersistentHistory(JSON.parse(saved));
  }, []);

  useEffect(() => {
    if (persistentHistory.length > 0) {
      localStorage.setItem('dso2_history', JSON.stringify(persistentHistory));
    }
  }, [persistentHistory]);

  // Auto-save session
  useEffect(() => {
    if (!sessionId || messages.length === 0) return;
    
    setPersistentHistory(prev => {
      const otherSessions = prev.filter(s => s.id !== sessionId);
      const currentSession = {
        id: sessionId,
        persona,
        date: new Date().toLocaleDateString('en-US'),
        time: new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
        messages: messages
      };
      return [currentSession, ...otherSessions].slice(0, 50);
    });
  }, [messages, sessionId, persona]);

  // Initialize session
  useEffect(() => {
    let currentSessionId = null;
    const initSession = async () => {
      try {
        console.log("Starting session with persona:", persona);
        const res = await fetch('http://127.0.0.1:8000/session/start', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ persona })
        });
        
        if (!res.ok) {
          const errorPayload = await res.json().catch(() => ({}));
          throw new Error(`HTTP ${res.status}: ${JSON.stringify(errorPayload)}`);
        }

        const data = await res.json();
        if (data && data.session_id) {
          setSessionId(data.session_id);
          currentSessionId = data.session_id;
        } else {
          throw new Error("Missing session ID.");
        }
      } catch (err) {
        console.error("Session error:", err);
        setSessionError(true);
      }
    };
    initSession();

    return () => {
      if (currentSessionId) {
        fetch(`http://127.0.0.1:8000/session/${currentSessionId}`, { method: 'DELETE' }).catch(console.error);
      }
      if (audioCtxRef.current && audioCtxRef.current.state !== 'closed') {
        audioCtxRef.current.close().catch(() => {});
      }
    };
  }, [persona]);

  // Speech-to-Text configuration
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = 'en-US';

      recognition.onresult = (event) => {
        const transcript = Array.from(event.results)
          .map(result => result[0].transcript)
          .join('');
        setInputValue(transcript);
      };

      recognition.onerror = (e) => {
        console.error("STT Error", e);
        setIsRecording(false);
      };

      recognition.onend = () => {
        setIsRecording(false);
        clearInterval(timerRef.current);
        setRecordingTime(0);
      };

      recognitionRef.current = recognition;
    }
  }, []);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isTyping]);

  const ensureAudioContext = () => {
    try {
      if (!audioCtxRef.current) {
        const AudioContext = window.AudioContext || window.webkitAudioContext;
        audioCtxRef.current = new AudioContext();
        analyserRef.current = audioCtxRef.current.createAnalyser();
        analyserRef.current.fftSize = 256;
        sourceRef.current = audioCtxRef.current.createMediaElementSource(audioRef.current);
        sourceRef.current.connect(analyserRef.current);
        analyserRef.current.connect(audioCtxRef.current.destination);
      }
      if (audioCtxRef.current.state === 'suspended') {
        audioCtxRef.current.resume();
      }
    } catch(e) {
      console.warn("Failed to initialize AudioContext.", e);
    }
  };

  const handleSend = async () => {
    ensureAudioContext();

    if (!inputValue.trim() || !sessionId) return;
    
    if (isRecording) {
      if (recognitionRef.current) recognitionRef.current.stop();
      setIsRecording(false);
      clearInterval(timerRef.current);
      setRecordingTime(0);
    }

    const textToSend = inputValue;
    const newMessage = {
      id: Date.now(),
      text: textToSend,
      sender: 'user',
      time: new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
    };
    
    setMessages(prev => [...prev, newMessage]);
    setInputValue('');
    setIsTyping(true);
    
    try {
      const res = await fetch('http://127.0.0.1:8000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId, message: textToSend })
      });
      const data = await res.json();
      
      const botMessage = {
        id: Date.now() + 1,
        text: data.agent_response,
        sender: 'bot',
        time: new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
      };
      
      if (data.manifest_url) {
        // Avatar is rendering -> Stay in 'typing' state and defer text display
        pendingBotMessageRef.current = botMessage;
      } else {
        // No avatar -> Display instantly and play TTS
        setMessages(prev => [...prev, botMessage]);
        setIsTyping(false);
        playTTS(data.agent_response);
      }
      
      if (onVideoResponse) {
        onVideoResponse(data.video_url, data.manifest_url);
      }
    } catch (err) {
      console.error(err);
      setIsTyping(false);
    }
  };

  const playTTS = (text) => {
    if (isMuted || !audioRef.current) return;
    try {
      const audioUrl = `http://127.0.0.1:5500/tts?text=${encodeURIComponent(text)}&voice=en-US-AvaMultilingualNeural`;
      audioRef.current.src = audioUrl;
      audioRef.current.play().catch(e => console.error("TTS play error", e));
    } catch (err) {
      console.error("TTS request error", err);
    }
  };

  const toggleRecording = () => {
    if (isRecording) {
      if (recognitionRef.current) recognitionRef.current.stop();
      setIsRecording(false);
      clearInterval(timerRef.current);
      setRecordingTime(0);
    } else {
      if (recognitionRef.current) {
        setInputValue("");
        recognitionRef.current.start();
        setIsRecording(true);
        timerRef.current = setInterval(() => {
          setRecordingTime(prev => prev + 1);
        }, 1000);
      } else {
        alert("Speech Recognition is not supported in this browser.");
      }
    }
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const buildTranscript = () => {
    const header = `=== DSO2 Session Transcript ===\nPersona: ${persona}\nDate: ${new Date().toLocaleDateString('en-US', { dateStyle: 'full' })}\n\n`;
    const body = messages.map(m =>
      `[${m.time}] ${m.sender === 'user' ? 'Delegate' : 'Agent'}: ${m.text}`
    ).join('\n');
    return header + body;
  };

  return (
    <div className="flex flex-col h-full bg-white rounded-[32px] border border-md-outline/10 overflow-hidden shadow-[0_8px_32px_-4px_rgba(0,0,0,0.05)] relative font-sans">
      
      {/* Header */}
      <div className="px-8 py-5 border-b border-md-outline/5 bg-white/80 backdrop-blur-xl flex items-center justify-between sticky top-0 z-20">
        <div className="flex items-center gap-3">
           <div className="w-8 h-8 rounded-xl bg-md-primary/10 flex items-center justify-center text-md-primary">
              <Bot size={18} />
           </div>
           <h3 className="text-[11px] font-black text-md-on-background uppercase tracking-[0.3em]">Chat</h3>
        </div>

        <div className="flex items-center gap-3">
           <button
              onClick={async () => {
                try {
                  if (sessionId) {
                    await fetch(`http://127.0.0.1:8000/session/${sessionId}`, { method: 'DELETE' }).catch(() => {});
                  }
                  setMessages([]);
                  setSessionId(null);
                  setSessionError(false);
                  const res = await fetch('http://127.0.0.1:8000/session/start', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ persona })
                  });
                  const data = await res.json();
                  if (data?.session_id) setSessionId(data.session_id);
                } catch (e) { console.error('Error starting new chat:', e); }
              }}
              title="New conversation"
              className="flex items-center gap-2 px-3 py-2 rounded-full bg-white hover:bg-emerald-50 text-emerald-600 border border-emerald-100 hover:border-emerald-300 transition-all duration-300 shadow-sm group"
           >
              <PlusCircle size={14} className="group-hover:scale-110 transition-transform" />
              <span className="text-[10px] font-black uppercase tracking-widest">New</span>
           </button>
 
           <button
              onClick={() => setShowHistory(true)}
              className="flex items-center gap-2.5 px-4 py-2 rounded-full bg-white hover:bg-slate-50 text-md-primary transition-all duration-300 shadow-sm border border-md-outline/10 group overflow-hidden relative"
           >
              <div className="relative z-10 flex items-center gap-2">
                 <FileText size={14} className="group-hover:scale-110 transition-transform" />
                 <span className="text-[10px] font-black uppercase tracking-widest">History</span>
              </div>
              {persistentHistory.filter(s => s.persona === persona).length > 0 && (
                 <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 bg-rose-500 rounded-full animate-pulse" />
              )}
           </button>

           <button
             onClick={() => setIsMuted(!isMuted)}
             className={`w-9 h-9 rounded-full flex items-center justify-center transition-all duration-300 ${
               isMuted 
                 ? 'bg-rose-50 text-rose-500 border border-rose-100 shadow-inner' 
                 : 'bg-white text-md-primary border border-md-outline/10 hover:border-md-primary/20'
             }`}
           >
              {isMuted ? <VolumeX size={16} /> : <Volume2 size={16} />}
           </button>

           <div className="pl-3 border-l border-md-outline/10">
              <button 
                onClick={async () => {
                  if (window.confirm("Permanent Action: Clear this session and local history?")) {
                     setMessages([]);
                     setPersistentHistory(prev => prev.filter(s => s.id !== sessionId));
                     try {
                       await fetch(`http://127.0.0.1:8000/session/${sessionId}/reset`, { method: 'POST' });
                     } catch (e) { console.error("Reset error:", e); }
                  }
                }}
                className="w-9 h-9 rounded-full flex items-center justify-center text-md-outline hover:text-rose-500 hover:bg-rose-50 transition-all"
                title="Delete session"
              >
                <X size={18} />
              </button>
           </div>
        </div>
      </div>

      {/* Messages */}
      <div 
        ref={scrollRef}
        className="flex-1 overflow-y-auto p-8 space-y-8 bg-gradient-to-b from-white via-slate-50/20 to-white"
      >
        {messages.length === 0 && !isTyping && (
          <div className="h-full flex flex-col items-center justify-center pointer-events-none opacity-20">
            <Bot size={48} className="mb-4" />
            <p className="text-[10px] font-black uppercase tracking-widest">Awaiting Link</p>
          </div>
        )}

        {messages.map((msg) => (
          <motion.div
            key={msg.id}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            className={`flex flex-col ${msg.sender === 'user' ? 'items-end' : 'items-start'}`}
          >
            <div className={`flex items-center gap-2 mb-2 px-1 text-[10px] font-black uppercase tracking-tighter opacity-40 ${msg.sender === 'user' ? 'text-md-primary' : 'text-slate-500'}`}>
              <span>{msg.sender === 'user' ? (persona === 'medical' ? 'Doctor' : 'Pharmacist') : 'AI Representative'}</span>
              <span className="w-1 h-1 rounded-full bg-current opacity-20" />
              <span>{msg.time}</span>
            </div>
            <div 
              className={`max-w-[85%] px-6 py-4 rounded-[24px] text-[15px] font-medium leading-relaxed ${
                msg.sender === 'user'
                  ? 'bg-md-primary text-white rounded-tr-none shadow-lg shadow-md-primary/10'
                  : 'bg-white text-md-on-background border border-slate-100 rounded-tl-none shadow-sm'
              }`}
            >
              {msg.text}
            </div>
          </motion.div>
        ))}

        {isTyping && (
           <div className="flex items-center gap-2 pl-2">
              <div className="flex gap-1 bg-slate-50 px-4 py-3 rounded-2xl">
                 <span className="w-1.5 h-1.5 bg-slate-300 rounded-full animate-bounce" />
                 <span className="w-1.5 h-1.5 bg-slate-300 rounded-full animate-bounce delay-100" />
                 <span className="w-1.5 h-1.5 bg-slate-300 rounded-full animate-bounce delay-200" />
              </div>
           </div>
        )}
      </div>

      {/* Input Bar */}
      <div className="p-6 bg-white border-t border-slate-50">
        <div className="max-w-4xl mx-auto">
          <div className="relative bg-slate-50 rounded-[28px] border border-slate-100 shadow-inner group transition-all focus-within:border-md-primary/30 focus-within:bg-white focus-within:shadow-md">
             <textarea
               rows={1}
               value={inputValue}
               onChange={(e) => {
                 setInputValue(e.target.value);
                 e.target.style.height = 'auto';
                 e.target.style.height = Math.min(e.target.scrollHeight, 140) + 'px';
               }}
               onKeyDown={(e) => {
                 if (e.key === 'Enter' && !e.shiftKey) {
                   e.preventDefault();
                   handleSend();
                 }
               }}
               placeholder="Write a message..."
               className="w-full min-h-[56px] max-h-40 bg-transparent px-6 py-4 text-base font-medium focus:outline-none resize-none overflow-y-auto scrollbar-none leading-relaxed placeholder:text-slate-400"
             />

             <AnimatePresence>
                {isRecording && (
                    <motion.div 
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="absolute inset-0 bg-rose-500 rounded-[28px] flex items-center justify-between px-6 text-white"
                    >
                        <div className="flex items-center gap-3">
                            <div className="flex gap-1">
                                {[0,1,2].map(i => <div key={i} className="w-1 h-3 bg-white/50 rounded-full animate-pulse" style={{ animationDelay: `${i*0.1}s` }} />)}
                            </div>
                            <span className="text-[11px] font-black uppercase tracking-widest leading-none">Transcription in progress...</span>
                        </div>
                        <div className="flex items-center gap-4">
                            <span className="font-mono font-bold font-sm opacity-80">{formatTime(recordingTime)}</span>
                            <button onClick={toggleRecording} className="w-8 h-8 rounded-full bg-white/20 hover:bg-white/30 flex items-center justify-center transition-all">
                                <X size={14} />
                            </button>
                        </div>
                    </motion.div>
                )}
             </AnimatePresence>

             <div className="flex items-center justify-between px-4 pb-3">
                <div className="flex items-center gap-2">
                    <button 
                        onClick={toggleRecording}
                        className={`w-10 h-10 rounded-full flex items-center justify-center transition-all ${
                            isRecording ? 'bg-white text-rose-500' : 'bg-white text-slate-500 hover:text-md-primary hover:shadow-sm'
                        }`}
                        title="Voice"
                    >
                        {isRecording ? <MicOff size={18} /> : <Mic size={18} />}
                    </button>
                </div>

                <button 
                    onClick={handleSend}
                    disabled={!inputValue.trim() || (!sessionId && !sessionError)}
                    className={`h-10 px-6 rounded-full shadow-md active:scale-95 transition-all flex items-center gap-2 group/btn ${
                      !sessionId && !sessionError
                        ? 'bg-slate-200 text-slate-400 cursor-not-allowed'
                        : sessionError
                        ? 'bg-rose-500 text-white cursor-pointer hover:bg-rose-600'
                        : 'bg-md-primary text-white hover:bg-md-primary-dark cursor-pointer'
                    }`}
                    title={!sessionId && !sessionError ? "Connecting..." : sessionError ? "Error - Click to Refresh" : "Send"}
                >
                    <span className="text-[10px] font-black uppercase tracking-widest pl-1">
                      {!sessionId && !sessionError ? 'Connecting...' : 'Send'}
                    </span>
                    <Send size={14} className={`${!sessionId && !sessionError ? 'animate-pulse' : 'group-hover:translate-x-0.5'} transition-transform`} />
                </button>
             </div>
          </div>
        </div>
      </div>

      {/* History Modal */}
      {showHistory && createPortal(
        <AnimatePresence mode="wait">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-[9999] bg-slate-900/60 backdrop-blur-md flex items-center justify-center p-4"
          >
            <motion.div 
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 30 }}
              className="w-full max-w-7xl h-[88vh] bg-white rounded-[32px] overflow-hidden flex flex-col shadow-2xl"
            >
               <div className="px-10 py-8 border-b flex items-center justify-between">
                 <div className="flex items-center gap-4">
                    <FileText className="text-md-primary" />
                    <h3 className="font-black uppercase tracking-widest">Session Archives</h3>
                 </div>
                 <button onClick={() => setShowHistory(false)} className="w-10 h-10 rounded-full hover:bg-slate-100 flex items-center justify-center">
                    <X />
                 </button>
               </div>
               <div className="flex-1 flex overflow-hidden">
                  <div className="w-80 border-r overflow-y-auto p-4 space-y-2">
                     {persistentHistory.filter(s => s.persona === persona).map(s => (
                        <button
                           key={s.id}
                           onClick={() => setViewingSessionId(s.id)}
                           className={`w-full text-left p-4 rounded-2xl transition-all ${
                              viewingSessionId === s.id ? 'bg-md-primary text-white' : 'hover:bg-slate-50'
                           }`}
                        >
                           <p className="text-[10px] font-black uppercase mb-1">{s.date} at {s.time}</p>
                           <p className="text-sm font-bold truncate opacity-80">{s.messages[s.messages.length - 1]?.text}</p>
                        </button>
                     ))}
                  </div>
                  <div className="flex-1 overflow-y-auto p-12 space-y-6 bg-slate-50/30">
                     {(() => {
                        const s = persistentHistory.find(h => h.id === (viewingSessionId || sessionId));
                        return s?.messages.map(m => (
                           <div key={m.id} className={`flex flex-col ${m.sender === 'user' ? 'items-end' : 'items-start'}`}>
                              <div className={`max-w-[70%] p-5 rounded-[24px] ${m.sender === 'user' ? 'bg-md-primary text-white rounded-tr-none' : 'bg-white border rounded-tl-none'}`}>
                                 {m.text}
                              </div>
                           </div>
                        ));
                     })()}
                  </div>
               </div>
            </motion.div>
          </motion.div>
        </AnimatePresence>,
        document.body
      )}
    </div>
  );
}
