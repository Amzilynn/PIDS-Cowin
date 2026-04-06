import React, { useState, useRef, useEffect } from 'react';
import { Send, Mic, MicOff, User, Bot, Volume2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export default function ChatPanel({ persona = 'medical' }) {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [isTyping, setIsTyping] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  
  const scrollRef = useRef(null);
  const timerRef = useRef(null);
  const recognitionRef = useRef(null);

  // Initialisation de la session backend
  useEffect(() => {
    let currentSessionId = null;
    const initSession = async () => {
      try {
        const res = await fetch('http://127.0.0.1:8000/session/start', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ persona })
        });
        const data = await res.json();
        setSessionId(data.session_id);
        currentSessionId = data.session_id;
      } catch (err) {
        console.error("Erreur de session:", err);
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

  return (
    <div className="flex flex-col h-full bg-md-surface-container rounded-[28px] border border-md-outline/10 overflow-hidden shadow-lg">
      {/* En-tête du Chat */}
      <div className="px-6 py-4 border-b border-md-outline/10 bg-white/50 backdrop-blur-md flex items-center justify-between">
        <h3 className="text-sm font-black text-md-on-background uppercase tracking-widest">Conversation en cours</h3>
        <div className="flex items-center gap-4">
           {sessionId && (
             <button 
               onClick={async () => {
                 try {
                   await fetch(`http://127.0.0.1:8000/session/${sessionId}/reset`, { method: 'POST' });
                   setMessages([]);
                 } catch (e) {
                   console.error("Erreur reset:", e);
                 }
               }}
               className="text-[10px] font-bold text-md-primary/60 hover:text-rose-500 uppercase tracking-widest transition-colors"
             >
               Effacer
             </button>
           )}
           <div className="flex flex-row items-center gap-2">
             <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
             <span className="text-[10px] font-bold text-emerald-500 uppercase tracking-widest">Direct</span>
           </div>
        </div>
      </div>

      {/* Zone des Messages (Démarrage VIDE) */}
      <div 
        ref={scrollRef}
        className="flex-1 overflow-y-auto p-6 space-y-6 scrollbar-thin scrollbar-thumb-md-primary/10"
      >
        <AnimatePresence>
          {messages.length === 0 && !isTyping && (
            <motion.div 
               initial={{ opacity: 0 }}
               animate={{ opacity: 1 }}
               className="h-full flex flex-col items-center justify-center text-center opacity-30 grayscale"
            >
               <div className="w-16 h-16 rounded-full bg-md-primary/10 flex items-center justify-center mb-4">
                  <Bot size={32} className="text-md-primary" />
               </div>
               <p className="text-xs font-bold uppercase tracking-widest text-md-on-background">Aucun message pour le moment</p>
               <p className="text-[10px] mt-1">Commencez la discussion ou utilisez le micro.</p>
            </motion.div>
          )}

          {messages.map((msg) => (
            <motion.div
              initial={{ opacity: 0, y: 10, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              key={msg.id}
              className={`flex flex-col ${msg.sender === 'user' ? 'items-end' : 'items-start'}`}
            >
              <div className="flex items-center gap-2 mb-1 px-2">
                 <span className="text-[9px] font-black uppercase text-md-outline tracking-tighter">{msg.sender === 'user' ? 'Délégué' : 'Avatar'}</span>
                 <span className="text-[9px] font-medium text-md-outline opacity-60">{msg.time}</span>
              </div>
              <div className={`max-w-[85%] px-5 py-3.5 rounded-[20px] text-sm font-medium shadow-sm ${
                msg.sender === 'user' 
                  ? 'bg-md-primary text-white rounded-tr-none' 
                  : 'bg-white text-md-on-background rounded-tl-none border border-md-outline/5'
              }`}>
                {msg.text}
              </div>
            </motion.div>
          ))}
          
          {isTyping && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex flex-col items-start">
               <div className="bg-white px-5 py-3 rounded-[20px] rounded-tl-none border border-md-outline/5 flex gap-1 items-center h-10 shadow-sm">
                  {[0, 1, 2].map(i => (
                    <motion.div 
                      key={i}
                      animate={{ y: [0, -5, 0] }}
                      transition={{ repeat: Infinity, duration: 0.6, delay: i * 0.2 }}
                      className="w-1.5 h-1.5 bg-md-primary rounded-full"
                    />
                  ))}
               </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Zone de Saisie */}
      <div className="p-6 bg-white/80 backdrop-blur-md border-t border-md-outline/10 space-y-4">
        {/* Barre d'Input */}
        <div className="relative group">
           <input
             type="text"
             value={inputValue}
             onChange={(e) => setInputValue(e.target.value)}
             onKeyPress={(e) => e.key === 'Enter' && handleSend()}
             placeholder="Votre message..."
             className="w-full h-14 bg-md-surface-container-low border-b-2 border-md-outline/20 px-6 rounded-t-[16px] text-base font-medium focus:outline-none focus:border-md-primary transition-all group-hover:bg-md-surface-container"
           />
           {isRecording && (
              <div className="absolute inset-0 bg-rose-500 rounded-t-[16px] flex items-center justify-between px-6 text-white animate-pulse">
                 <div className="flex items-center gap-3">
                    <div className="w-3 h-3 bg-white rounded-full animate-ping" />
                    <span className="text-sm font-black uppercase tracking-widest">Enregistrement en cours...</span>
                 </div>
                 <span className="font-mono font-bold">{formatTime(recordingTime)}</span>
              </div>
           )}
        </div>

        {/* Contrôles */}
        <div className="flex items-center justify-between">
           <button 
             onClick={toggleRecording}
             className={`w-12 h-12 rounded-full flex items-center justify-center transition-all active:scale-95 shadow-md ${
               isRecording ? 'bg-rose-500 text-white animate-bounce' : 'bg-md-surface-container-low text-md-primary hover:bg-md-primary/10'
             }`}
           >
              {isRecording ? <MicOff size={22} /> : <Mic size={22} />}
           </button>

           <button 
             onClick={handleSend}
             disabled={!inputValue.trim()}
             className="btn-primary flex-1 ml-4 !h-12 !rounded-pill uppercase text-[11px] font-black tracking-widest disabled:opacity-50 disabled:grayscale transition-all"
           >
              Envoyer <Send size={18} />
           </button>
        </div>
      </div>
    </div>
  );
}
