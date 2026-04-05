import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, User, ChevronRight, MessageSquare, Clock } from 'lucide-react';

export default function ChatPanel({ 
  messages = [], 
  onSend = () => {}, 
  isTyping = false, 
  title = "Evaluation Stream" 
}) {
  const [input, setInput] = React.useState('');

  const handleSend = (e) => {
    e.preventDefault();
    if (!input.trim()) return;
    onSend(input);
    setInput('');
  };

  return (
    <div className="flex flex-col h-full bg-white rounded-4xl border border-slate-200 shadow-xl overflow-hidden glass-card">
      {/* Header */}
      <div className="px-8 py-6 border-b border-slate-100 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-brand-navy flex items-center justify-center text-white shadow-xl shadow-brand-navy/20">
            <MessageSquare size={18} />
          </div>
          <div>
            <h3 className="text-brand-navy font-extrabold text-sm tracking-tight capitalize">{title}</h3>
            <p className="text-[10px] font-bold text-brand-teal uppercase tracking-widest">Medical Context: ACTIVE</p>
          </div>
        </div>
        
        <div className="flex items-center gap-2 px-3 py-1.5 bg-brand-teal/10 rounded-full">
           <div className="w-1.5 h-1.5 bg-brand-teal rounded-full animate-pulse" />
           <span className="text-[9px] font-black text-brand-teal uppercase tracking-widest">Live Audit</span>
        </div>
      </div>

      {/* Messages list */}
      <div className="flex-1 overflow-y-auto p-8 space-y-6 scrollbar-thin">
        <AnimatePresence initial={false}>
          {messages.map((msg, i) => (
            <motion.div 
              key={i} 
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className={`flex items-end gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}
            >
              <div className={`w-10 h-10 rounded-2xl flex items-center justify-center shadow-md flex-shrink-0 mb-1 transition-all ${msg.role === 'user' ? 'bg-brand-navy text-white' : 'bg-brand-teal text-white'}`}>
                <User size={16} />
              </div>
              
              <div className={`flex flex-col gap-1 max-w-[75%] ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                <div className={`px-5 py-4 rounded-3xl text-sm leading-relaxed font-semibold transition-all shadow-sm ${
                  msg.role === 'user' 
                    ? 'bg-brand-navy text-white rounded-br-sm' 
                    : 'bg-slate-100 text-brand-navy rounded-bl-sm border border-slate-200'
                }`}>
                  {msg.text}
                </div>
                <div className="flex items-center gap-1.5 px-1 opacity-40">
                   <Clock size={10} />
                   <span className="text-[9px] font-black uppercase tracking-widest">{msg.timestamp || 'Just now'}</span>
                </div>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {isTyping && (
          <motion.div 
            initial={{ opacity: 0 }} 
            animate={{ opacity: 1 }} 
            className="flex items-center gap-3 text-brand-teal"
          >
            <div className="w-8 h-8 rounded-xl bg-brand-teal/10 flex items-center justify-center">
              <User size={12} />
            </div>
            <div className="flex gap-1.5 px-1 py-1">
              {[0, 1, 2].map((i) => (
                <motion.div
                  key={i}
                  animate={{ scale: [1, 1.5, 1] }}
                  transition={{ repeat: Infinity, duration: 1, delay: i * 0.2 }}
                  className="w-1.5 h-1.5 bg-brand-teal rounded-full"
                />
              ))}
            </div>
            <span className="text-[10px] font-black uppercase tracking-widest">Representative Typing...</span>
          </motion.div>
        )}
      </div>

      {/* Input area */}
      <div className="p-8 border-t border-slate-100 bg-white">
        <form onSubmit={handleSend} className="relative flex items-center gap-4 group">
          <div className="flex-1 relative">
            <input 
              type="text" 
              placeholder="Enter clinical response..." 
              value={input}
              onChange={(e) => setInput(e.target.value)}
              className="w-full pl-8 pr-16 py-4 bg-slate-50 border border-slate-200 rounded-[28px] text-sm font-bold text-brand-navy outline-none focus:border-brand-teal focus:ring-4 focus:ring-brand-teal/5 shadow-inner transition-all placeholder:text-slate-400"
            />
            <div className="absolute right-4 top-1/2 -translate-y-1/2 flex items-center gap-2">
               <button 
                  type="submit" 
                  disabled={!input.trim()}
                  className="w-10 h-10 bg-brand-navy text-white rounded-2xl flex items-center justify-center hover:bg-slate-800 transition-all disabled:opacity-20 shadow-xl shadow-brand-navy/20 active:scale-90"
               >
                 <ChevronRight size={18} />
               </button>
            </div>
          </div>
          
          <button 
             type="submit" 
             disabled={!input.trim()}
             className="px-6 py-4 bg-brand-teal text-white rounded-3xl font-extrabold text-xs uppercase tracking-widest flex items-center gap-3 shadow-xl shadow-brand-teal/20 hover:scale-105 active:scale-95 transition-all disabled:grayscale disabled:opacity-50"
          >
            <Send size={16} />
            Send Detailing
          </button>
        </form>
      </div>
    </div>
  );
}
