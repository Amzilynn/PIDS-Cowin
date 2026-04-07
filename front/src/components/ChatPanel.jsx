import React, { useState, useRef, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { Send, Mic, MicOff, Bot, FileText, Copy, Download, X, Volume2, VolumeX } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export default function ChatPanel({ persona = 'medical' }) {
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

  // Synchronisation de l'historique persistent
  useEffect(() => {
    const saved = localStorage.getItem('dso2_history');
    if (saved) setPersistentHistory(JSON.parse(saved));
  }, []);

  useEffect(() => {
    if (persistentHistory.length > 0) {
      localStorage.setItem('dso2_history', JSON.stringify(persistentHistory));
    }
  }, [persistentHistory]);

  // Sauvegarde auto de la session active dans l'historique persistent
  useEffect(() => {
    if (!sessionId || messages.length === 0) return;
    
    setPersistentHistory(prev => {
      const otherSessions = prev.filter(s => s.id !== sessionId);
      const currentSession = {
        id: sessionId,
        persona,
        date: new Date().toLocaleDateString('fr-FR'),
        time: new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' }),
        messages: messages
      };
      return [currentSession, ...otherSessions].slice(0, 50); // Garde les 50 derniers
    });
  }, [messages, sessionId, persona]);

  // Initialisation de la session backend
  useEffect(() => {
    let currentSessionId = null;
    const initSession = async () => {
      try {
        console.log("Démarrage de la session avec le persona:", persona);
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
          console.log("Session initialisée avec succès:", data.session_id);
        } else {
          throw new Error("ID de session manquant dans la réponse du serveur.");
        }
      } catch (err) {
        console.error("Erreur critique de session:", err);
        setSessionError(true);
      }
    };
    initSession();

    return () => {
      // Cleanup de session
      if (currentSessionId) {
        fetch(`http://127.0.0.1:8000/session/${currentSessionId}`, { method: 'DELETE' }).catch(console.error);
      }
    };
  }, [persona]);

  // Configuration Speech-to-Text
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = 'fr-FR';

      recognition.onresult = (event) => {
        const transcript = Array.from(event.results)
          .map(result => result[0].transcript)
          .join('');
        setInputValue(transcript);
      };

      recognition.onerror = (e) => {
        console.error("Erreur STT", e);
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

  const handleSend = async () => {
    if (!inputValue.trim() || !sessionId) return;
    
    // Si on envoie pendant qu'on enregistre, on coupe le micro proprement.
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
      time: new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })
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
        time: new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })
      };
      setMessages(prev => [...prev, botMessage]);
      
      playTTS(data.agent_response);
    } catch (err) {
      console.error(err);
    } finally {
      setIsTyping(false);
    }
  };

  const playTTS = (text) => {
    if (isMuted) return;
    try {
      const audioUrl = `http://127.0.0.1:5500/tts?text=${encodeURIComponent(text)}&voice=fr-FR-DeniseNeural`;
      const audio = new Audio(audioUrl);
      audio.play().catch(e => console.error("TTS play error", e));
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
        alert("Speech Recognition non supporté par ce navigateur.");
      }
    }
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const buildTranscript = () => {
    const header = `=== Transcript de Session DSO2 ===\nPersona: ${persona}\nDate: ${new Date().toLocaleDateString('fr-FR', { dateStyle: 'full' })}\n\n`;
    const body = messages.map(m =>
      `[${m.time}] ${m.sender === 'user' ? 'Délégué' : 'Agent'}: ${m.text}`
    ).join('\n');
    return header + body;
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(buildTranscript()).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  const handleDownload = () => {
    const blob = new Blob([buildTranscript()], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `transcript_dso2_${new Date().toISOString().slice(0,10)}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="flex flex-col h-full bg-white rounded-[32px] border border-md-outline/10 overflow-hidden shadow-[0_8px_32px_-4px_rgba(0,0,0,0.05)] relative font-sans">
      
      {/* Refined Header - Glassmorphism & Modern Alignments */}
      <div className="px-8 py-5 border-b border-md-outline/5 bg-white/80 backdrop-blur-xl flex items-center justify-between sticky top-0 z-20">
        <div className="flex items-center gap-3">
           <div className="w-8 h-8 rounded-xl bg-md-primary/10 flex items-center justify-center text-md-primary">
              <Bot size={18} />
           </div>
           <h3 className="text-[11px] font-black text-md-on-background uppercase tracking-[0.3em]">Chat</h3>
        </div>

        <div className="flex items-center gap-3">
           {/* Historique Button */}
           <button
              onClick={() => setShowHistory(true)}
              className="flex items-center gap-2.5 px-4 py-2 rounded-full bg-white hover:bg-slate-50 text-md-primary transition-all duration-300 shadow-sm border border-md-outline/10 group overflow-hidden relative"
           >
              <div className="relative z-10 flex items-center gap-2">
                 <FileText size={14} className="group-hover:scale-110 transition-transform" />
                 <span className="text-[10px] font-black uppercase tracking-widest">Historique</span>
              </div>
              {persistentHistory.filter(s => s.persona === persona).length > 0 && (
                 <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 bg-rose-500 rounded-full animate-pulse" />
              )}
           </button>

           {/* Sound Toggle */}
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

           {/* Reset Utility */}
           <div className="pl-3 border-l border-md-outline/10">
              <button 
                onClick={async () => {
                  if (window.confirm("Action Irréversible: Effacer TOUTE la session en cours et son historique local ?")) {
                     setMessages([]);
                     setPersistentHistory(prev => prev.filter(s => s.id !== sessionId));
                     try {
                       await fetch(`http://127.0.0.1:8000/session/${sessionId}/reset`, { method: 'POST' });
                     } catch (e) { console.error("Erreur reset:", e); }
                  }
                }}
                className="w-9 h-9 rounded-full flex items-center justify-center text-md-outline hover:text-rose-500 hover:bg-rose-50 transition-all"
                title="Supprimer la session"
              >
                <X size={18} />
              </button>
           </div>
        </div>
      </div>

      {/* Messages Viewport - Gradient Background & Subtle Details */}
      <div 
        ref={scrollRef}
        className="flex-1 overflow-y-auto p-8 space-y-8 scrollbar-thin scrollbar-thumb-md-primary/10 bg-gradient-to-b from-white via-slate-50/20 to-white"
      >
        {messages.length === 0 && !isTyping && (
          <div className="h-full flex flex-col items-center justify-center pointer-events-none">
            <div className="relative mb-6">
                <div className="w-20 h-20 rounded-full bg-slate-50 flex items-center justify-center">
                    <Bot size={40} className="text-slate-300" />
                </div>
                <div className="absolute inset-0 border-2 border-dashed border-slate-200 rounded-full animate-[spin_20s_linear_infinite]" />
            </div>
            <p className="text-[11px] font-black text-slate-400 uppercase tracking-[0.25em] text-center">En attente d'interaction</p>
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
              <span>{msg.sender === 'user' ? 'Délégué' : 'Agent VITAL'}</span>
              <span className="w-1 h-1 rounded-full bg-current opacity-20" />
              <span>{msg.time}</span>
            </div>
            <div 
              className={`max-w-[85%] px-6 py-4 rounded-[24px] text-[15px] font-medium leading-relaxed leading-snug ${
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

      {/* Unified Modern Input Bar */}
      <div className="p-6 bg-white border-t border-slate-50">
        <div className="max-w-4xl mx-auto">
          <div className="relative bg-slate-50 rounded-[28px] border border-slate-100 shadow-inner group transition-all focus-within:border-md-primary/30 focus-within:bg-white focus-within:shadow-md">
             {/* Textarea Area */}
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
               placeholder="Écrivez un message..."
               className="w-full min-h-[56px] max-h-40 bg-transparent px-6 py-4 text-base font-medium focus:outline-none resize-none overflow-y-auto scrollbar-none leading-relaxed placeholder:text-slate-400"
             />

             {/* Recording Overlay */}
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
                            <span className="text-[11px] font-black uppercase tracking-widest leading-none">Transcription en cours...</span>
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

             {/* Action Toolbar Inside Input */}
             <div className="flex items-center justify-between px-4 pb-3">
                <div className="flex items-center gap-2">
                    <button 
                        onClick={toggleRecording}
                        className={`w-10 h-10 rounded-full flex items-center justify-center transition-all ${
                            isRecording ? 'bg-white text-rose-500' : 'bg-white text-slate-500 hover:text-md-primary hover:shadow-sm'
                        }`}
                        title="Vocal"
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
                    title={!sessionId && !sessionError ? "Connexion au serveur..." : sessionError ? "Erreur de connexion - Cliquez pour réessayer (F5)" : "Envoyer"}
                >
                    <span className="text-[10px] font-black uppercase tracking-widest pl-1">
                      {!sessionId && !sessionError ? 'Connexion...' : 'Envoyer'}
                    </span>
                    <Send size={14} className={`${!sessionId && !sessionError ? 'animate-pulse' : 'group-hover:translate-x-0.5'} transition-transform`} />
                </button>
             </div>
          </div>
        </div>
      </div>

      {/* History Modal : Moved to Portal to escape layout constraints */}
      {showHistory && createPortal(
        <AnimatePresence mode="wait">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-[9999] bg-slate-900/60 backdrop-blur-md flex items-center justify-center p-4 md:p-8"
          >
            <motion.div 
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 30 }}
              transition={{ type: 'spring', damping: 25, stiffness: 300 }}
              className="w-full max-w-7xl h-[88vh] bg-white rounded-[32px] shadow-2xl flex flex-col overflow-hidden relative border border-white/20"
            >
               {/* Modal Header */}
               <div className="px-10 py-8 flex items-center justify-between bg-white border-b border-md-outline/5">
                 <div className="flex items-center gap-5">
                    <div className="w-12 h-12 rounded-2xl bg-md-primary/10 flex items-center justify-center text-md-primary shadow-inner">
                       <FileText size={24} />
                    </div>
                    <div>
                       <h3 className="text-lg font-black text-md-on-background uppercase tracking-[0.2em]">Archives de Sessions</h3>
                       <p className="text-[10px] font-bold text-md-outline uppercase tracking-widest opacity-60">ID Session Active: {sessionId?.slice(0, 8)}</p>
                    </div>
                 </div>
                 <button 
                   onClick={() => setShowHistory(false)} 
                   className="w-12 h-12 rounded-full hover:bg-rose-50 hover:text-rose-600 flex items-center justify-center text-md-outline transition-all duration-300 transform hover:rotate-90 shadow-sm"
                 >
                   <X size={24} />
                 </button>
               </div>

               {/* Master-Detail View */}
               <div className="flex-1 flex overflow-hidden">
                  <div className="w-[360px] border-r border-md-outline/5 bg-md-surface-container-low/30 overflow-y-auto p-6 flex flex-col gap-4">
                     <h4 className="text-[11px] font-black uppercase text-md-outline/60 tracking-[0.2em] px-2">Répertoire DSO</h4>
                     {persistentHistory.filter(s => s.persona === persona).length === 0 && (
                        <div className="text-center py-10 opacity-30">
                           <FileText size={32} className="mx-auto mb-3" />
                           <p className="text-[10px] font-bold uppercase tracking-widest">Aucune Session {persona}</p>
                        </div>
                     )}
                     {persistentHistory.filter(s => s.persona === persona).map(s => (
                        <button
                           key={s.id}
                           onClick={() => setViewingSessionId(s.id)}
                           className={`w-full text-left p-5 rounded-2xl transition-all duration-300 border ${
                              (viewingSessionId || sessionId) === s.id 
                                 ? 'bg-md-primary text-white shadow-xl border-md-primary scale-[1.02] z-10' 
                                 : 'bg-white text-md-on-background border-md-outline/5 hover:border-md-primary/30'
                           }`}
                        >
                           <div className="flex justify-between items-start mb-2">
                              <span className={`text-[10px] font-black uppercase tracking-widest ${ (viewingSessionId || sessionId) === s.id ? 'text-white' : 'text-md-primary'}`}>
                                 {s.persona === 'medical' ? 'Dossier Médical' : 'Suivi Commercial'}
                              </span>
                              <span className="text-[9px] opacity-60 font-bold">{s.time}</span>
                           </div>
                           <p className="text-[12px] font-bold truncate leading-tight mb-3">{s.messages[s.messages.length - 1]?.text || 'Session vide'}</p>
                           <div className="flex items-center justify-between pt-3 border-t border-current/10">
                              <span className="text-[9px] font-black uppercase opacity-60">{s.date}</span>
                              <span className="text-[9px] font-medium opacity-50">{s.messages.length} msgs</span>
                           </div>
                        </button>
                     ))}
                  </div>

                  <div className="flex-1 flex flex-col bg-slate-50/30 overflow-hidden">
                     <div className="flex-1 overflow-y-auto p-12 space-y-8 scrollbar-thin scrollbar-thumb-md-primary/10">
                       {(() => {
                         const session = persistentHistory.find(s => s.id === (viewingSessionId || sessionId));
                         if (!session) return (
                           <div className="h-full flex flex-col items-center justify-center opacity-20 grayscale">
                             <FileText size={48} className="mb-4" />
                             <p className="text-xs font-black uppercase tracking-widest">Sélectionnez une session</p>
                           </div>
                         );

                         return session.messages.map(msg => (
                           <div key={msg.id} className={`flex flex-col ${msg.sender === 'user' ? 'items-end' : 'items-start'}`}>
                             <div className="flex items-center gap-2 mb-2 px-1">
                               <span className="text-[10px] font-black uppercase text-md-primary/60">{msg.sender === 'user' ? 'Délégué' : 'L\'Agent'}</span>
                               <span className="text-[10px] font-medium text-md-outline opacity-40">{msg.time}</span>
                             </div>
                             <div className={`max-w-[75%] px-8 py-5 rounded-[32px] text-[16px] font-medium leading-relaxed ${
                               msg.sender === 'user'
                                 ? 'bg-md-primary text-white rounded-tr-none shadow-md'
                                 : 'bg-white shadow-sm border border-md-outline/10 text-md-on-background rounded-tl-none'
                             }`}>{msg.text}</div>
                           </div>
                         ));
                       })()}
                     </div>
                  </div>
               </div>

               {/* Modal Footer Actions */}
               <div className="p-8 bg-md-surface-container-low border-t border-md-outline/10 flex gap-4 backdrop-blur-md">
                 <button 
                   onClick={() => {
                     const s = persistentHistory.find(h => h.id === (viewingSessionId || sessionId));
                     if (!s) return;
                     const transcript = `=== Transcript Session DSO2 ===\n${s.persona} | ${s.date} ${s.time}\n\n` + s.messages.map(m => `[${m.time}] ${m.sender}: ${m.text}`).join('\n');
                     navigator.clipboard.writeText(transcript).then(() => {
                       setCopied(true);
                       setTimeout(() => setCopied(false), 2000);
                     });
                   }} 
                   className={`btn-pill flex-1 !h-14 text-[11px] font-black uppercase tracking-wider transition-all duration-500 relative overflow-hidden ${
                     copied ? 'bg-emerald-500 text-white' : 'bg-white text-md-primary border border-md-outline/10 hover:border-md-primary hover:shadow-lg'
                   }`}
                 >
                    {copied ? 'Copié !' : 'Copier'}
                 </button>
                 <button 
                   onClick={() => {
                     const s = persistentHistory.find(h => h.id === (viewingSessionId || sessionId));
                     if (!s) return;
                     const transcript = `=== Transcript Session DSO2 ===\n${s.persona} | ${s.date} ${s.time}\n\n` + s.messages.map(m => `[${m.time}] ${m.sender}: ${m.text}`).join('\n');
                     const blob = new Blob([transcript], { type: 'text/plain;charset=utf-8' });
                     const url = URL.createObjectURL(blob);
                     const a = document.createElement('a');
                     a.href = url;
                     a.download = `dso2_archive_${s.id.slice(0,8)}.txt`;
                     a.click();
                   }} 
                   disabled={persistentHistory.length === 0}
                   className="btn-pill flex-1 !h-14 text-[11px] font-black uppercase tracking-wider btn-primary shadow-2xl transition-all duration-300"
                 >
                   <Download size={16} className="mr-2" /> Télécharger
                 </button>
                 <button 
                   onClick={() => {
                      if (window.confirm("Action Irréversible: Effacer tout l'historique ?")) {
                         localStorage.removeItem('dso2_history');
                         setPersistentHistory([]);
                         setViewingSessionId(null);
                      }
                   }}
                   className="w-14 h-14 rounded-full border-2 border-md-outline/10 flex items-center justify-center text-md-outline hover:bg-rose-50 hover:text-rose-500 transition-all shadow-sm"
                 >
                    <X size={24} />
                 </button>
               </div>
            </motion.div>
          </motion.div>
        </AnimatePresence>,
        document.body
      )}
    </div>
  );
}
