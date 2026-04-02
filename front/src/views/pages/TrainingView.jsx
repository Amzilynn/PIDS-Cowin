import { useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Play, Brain, Send, Loader2 } from 'lucide-react';
import { Card } from '../components/Card';

export function TrainingView({ simData, chatMessages, chatInput, chatLoading, onSendChat, setChatInput }) {
  const chatEndRef = useRef(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages]);

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      onSendChat(chatInput);
    }
  };

  return (
    <div className="grid grid-cols-2 gap-8" style={{ height: '680px' }}>
      {/* LEFT: Chat Panel */}
      <div className="bg-[#0F172A] rounded-[32px] flex flex-col overflow-hidden">
        {/* Header */}
        <div className="p-6 border-b border-white/10 flex items-center gap-4">
          <div className="w-10 h-10 rounded-full bg-teal-500 flex items-center justify-center font-black text-sm text-white">AI</div>
          <div>
            <p className="font-black text-white text-sm">Dr. Khalil — AI Medical Evaluator</p>
            <div className="flex items-center gap-2 mt-0.5">
              <div className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse" />
              <p className="text-xs text-emerald-400 font-bold">Live Simulation Active</p>
            </div>
          </div>
          <div className="ml-auto">
            <span className="text-[10px] font-black uppercase tracking-widest text-[#E6B800] bg-yellow-900/40 px-3 py-1.5 rounded-full">
              Assessment Mode
            </span>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {(chatMessages || []).length === 0 && (
            <div className="flex flex-col items-center justify-center h-full text-center gap-3">
              <Brain className="text-teal-500" size={40} />
              <p className="text-white font-black text-lg">Start your AI Assessment</p>
              <p className="text-slate-500 text-sm max-w-xs">Type a message below to begin your delegation simulation with Dr. Khalil.</p>
            </div>
          )}
          <AnimatePresence>
            {(chatMessages || []).map((msg, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className={`flex ${msg.role === 'delegate' ? 'justify-end' : 'justify-start'}`}
              >
                <div className={`max-w-[80%] px-5 py-3.5 rounded-2xl text-sm leading-relaxed font-medium ${
                  msg.role === 'delegate'
                    ? 'bg-teal-600 text-white rounded-br-sm'
                    : 'bg-white/10 text-slate-200 rounded-bl-sm border border-white/5'
                }`}>
                  {msg.message}
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
          {chatLoading && (
            <div className="flex justify-start">
              <div className="bg-white/10 border border-white/5 px-5 py-3.5 rounded-2xl rounded-bl-sm flex items-center gap-3">
                <Loader2 className="text-teal-400 animate-spin" size={16} />
                <span className="text-slate-400 text-sm font-medium">Dr. Khalil is evaluating...</span>
              </div>
            </div>
          )}
          <div ref={chatEndRef} />
        </div>

        {/* Input */}
        <div className="p-4 border-t border-white/10">
          <div className="flex gap-3">
            <input
              type="text"
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={chatLoading}
              placeholder="Answer Dr. Khalil's question..."
              className="flex-1 bg-white/5 border border-white/10 text-white placeholder:text-slate-600 rounded-xl px-4 py-3 text-sm font-medium outline-none focus:border-teal-500 transition-colors disabled:opacity-50"
            />
            <button
              onClick={() => onSendChat(chatInput)}
              disabled={chatLoading || !chatInput.trim()}
              className="px-5 py-3 bg-teal-500 hover:bg-teal-400 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-xl font-black transition-all flex items-center gap-2"
            >
              <Send size={16} />
            </button>
          </div>
        </div>
      </div>

      {/* RIGHT: Real-time Coaching */}
      <div className="space-y-5 overflow-y-auto">
        <Card>
          <h3 className="text-lg font-black mb-6">Real-time Coaching Metrics</h3>
          <div className="space-y-6">
            {[
              { label: 'Eye Contact & Confidence', value: simData.eye, color: 'bg-[#0A5C5C]' },
              { label: 'Knowledge Accuracy', value: simData.know, color: 'bg-[#E6B800]' },
              { label: 'Clinical Clarity', value: Math.round((simData.eye + simData.know) / 2), color: 'bg-indigo-500' },
              { label: 'Objection Handling', value: simData.know ? Math.min(simData.know + 3, 100) : 0, color: 'bg-rose-500' },
            ].map((m, i) => (
              <div key={i}>
                <div className="flex justify-between text-xs font-bold uppercase mb-2">
                  <span className="text-slate-600">{m.label}</span>
                  <span className="text-slate-900">{m.value}%</span>
                </div>
                <div className="h-2.5 bg-slate-100 rounded-full overflow-hidden">
                  <motion.div
                    animate={{ width: `${m.value}%` }}
                    transition={{ duration: 0.8, ease: 'easeOut' }}
                    className={`h-full rounded-full ${m.color}`}
                  />
                </div>
              </div>
            ))}
          </div>
          
          {simData.feedback && simData.feedback !== 'Ready to simulate...' && (
            <motion.div
              key={simData.feedback}
              initial={{ opacity: 0, scale: 0.97 }}
              animate={{ opacity: 1, scale: 1 }}
              className="mt-8 p-5 bg-teal-50 rounded-2xl border border-teal-100 text-[#0A5C5C] text-sm font-bold italic leading-relaxed"
            >
              💬 "{simData.feedback}"
            </motion.div>
          )}
        </Card>

        <Card className="bg-gradient-to-br from-[#0F172A] to-slate-800 border-none text-white">
          <p className="text-[10px] font-black uppercase text-slate-500 tracking-widest mb-4">Session Tips</p>
          <ul className="space-y-3 text-sm text-slate-300 font-medium">
            <li className="flex items-start gap-2"><span className="text-teal-400 mt-0.5">▸</span> Always cite trial names (EMPA-REG, DECLARE) when discussing outcomes.</li>
            <li className="flex items-start gap-2"><span className="text-teal-400 mt-0.5">▸</span> Keep answers under 3 sentences — physicians appreciate brevity.</li>
            <li className="flex items-start gap-2"><span className="text-teal-400 mt-0.5">▸</span> Use patient personas (e.g., "an 68-year-old with HFrEF") to ground your answers.</li>
          </ul>
        </Card>
      </div>
    </div>
  );
}
