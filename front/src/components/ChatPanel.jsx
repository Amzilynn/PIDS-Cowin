import React, { useState, useRef, useEffect } from 'react';
import { Bot, User } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export default function ChatPanel() {
  const [messages, setMessages] = useState([]);
  const scrollRef = useRef(null);

  useEffect(() => {
    // Connexion SSE au backend DSO1
    const eventSource = new EventSource("http://localhost:8001/api/training/chat_feed");
    
    eventSource.onmessage = (event) => {
      if (event.data) {
        try {
          const msg = JSON.parse(event.data);
          setMessages(prev => [...prev, {
            id: Date.now() + Math.random(),
            text: msg.content,
            sender: msg.role === 'user' ? 'user' : 'bot',
            time: new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })
          }]);
        } catch (e) {
          console.error("Invalid SSE message", e);
        }
      }
    };

    eventSource.onerror = (e) => {
      console.log("SSE Connection Error or Closed");
    };

    return () => {
      eventSource.close();
    };
  }, []);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  return (
    <div className="flex flex-col h-full bg-white rounded-[32px] border border-md-outline/10 overflow-hidden shadow-[0_8px_32px_-4px_rgba(0,0,0,0.05)] relative font-sans">
      
      {/* Header */}
      <div className="px-8 py-5 border-b border-md-outline/5 bg-white/80 backdrop-blur-xl flex items-center justify-between sticky top-0 z-20">
        <div className="flex items-center gap-3">
           <div className="w-8 h-8 rounded-xl bg-md-primary/10 flex items-center justify-center text-md-primary">
              <Bot size={18} />
           </div>
           <h3 className="text-[11px] font-black text-md-on-background uppercase tracking-[0.3em]">Transcription en Direct</h3>
        </div>
      </div>

      {/* Messages */}
      <div 
        ref={scrollRef}
        className="flex-1 overflow-y-auto p-8 flex flex-col gap-8 scroll-smooth"
      >
        <AnimatePresence initial={false}>
          {messages.map((msg) => {
            const isUser = msg.sender === 'user';
            return (
              <motion.div
                key={msg.id}
                initial={{ opacity: 0, y: 10, scale: 0.98 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                transition={{ type: "spring", stiffness: 400, damping: 30 }}
                className={`flex flex-col max-w-[85%] ${isUser ? 'self-end items-end' : 'self-start items-start'} relative group`}
              >
                <div className="flex items-center gap-2 mb-2 px-1">
                  {!isUser && (
                     <div className="w-5 h-5 rounded-full bg-md-secondary-container text-md-on-secondary-container flex items-center justify-center">
                        <Bot size={10} />
                     </div>
                  )}
                  <span className="text-[9px] font-black uppercase tracking-widest text-md-outline opacity-60">
                    {isUser ? 'Vous' : 'Avatar'} • {msg.time}
                  </span>
                  {isUser && (
                     <div className="w-5 h-5 rounded-full bg-md-primary text-white flex items-center justify-center">
                        <User size={10} />
                     </div>
                  )}
                </div>
                
                <div 
                  className={`
                    relative px-6 py-4 text-[13px] leading-relaxed font-medium shadow-sm max-w-full break-words
                    ${isUser 
                      ? 'bg-md-primary text-white rounded-[24px] rounded-tr-sm shadow-md-primary/20' 
                      : 'bg-md-surface-container text-md-on-surface rounded-[24px] rounded-tl-sm border border-md-outline/5'
                    }
                  `}
                >
                  {msg.text}
                </div>
              </motion.div>
            );
          })}
        </AnimatePresence>

        {messages.length === 0 && (
          <div className="flex-1 flex flex-col items-center justify-center text-center opacity-40 mt-10">
            <Bot size={48} className="mb-4 text-md-outline" />
            <p className="text-sm font-bold uppercase tracking-widest">En attente de conversation</p>
            <p className="text-[11px] mt-2 italic max-w-[200px]">Démarrez la session IA pour commencer à discuter.</p>
          </div>
        )}
      </div>

    </div>
  );
}
