import { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Mic, MicOff, Volume2, VolumeX, ChevronRight, User, Package, MessageSquare, Sparkles, X, Send, Loader2 } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useNavigate } from 'react-router-dom';

const delegates = [
  { id: 'ava', name: 'Ava Doctor (Cardio)', specialty: 'Cardiology Specialist', color: 'from-emerald-400 to-emerald-600' },
  { id: 'youssef', name: 'Youssef (Metabolic)', specialty: 'Metabolic Specialist', color: 'from-indigo-400 to-indigo-600' },
  { id: 'leila', name: 'Leila Amari', specialty: 'Pharma Expert', color: 'from-teal-400 to-teal-600' },
];

const products = [
  { name: 'Avalife Core', detail: 'SGLT2 Inhibitor for T2D & CV protection.', trial: 'EMPA-REG OUTCOME' },
  { name: 'Avalife Renal', detail: 'Advanced protection for Chronic Kidney Disease.', trial: 'EMPA-KIDNEY' },
];

export default function DoctorGuestPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [step, setStep] = useState('select-delegate');
  const [selectedDelegate, setSelectedDelegate] = useState(null);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [roleType, setRoleType] = useState('Medical');
  
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState([]);
  const [micOn, setMicOn] = useState(false);
  const [speaking, setSpeaking] = useState(false);
  const recognitionRef = useRef(null);

  // Ava Assistant State
  const [showAva, setShowAva] = useState(false);
  const [avaChat, setAvaChat] = useState([{ role: 'ava', text: "Hello Dr. Welcome to Avalive. I am your assistant Ava. How can I help you today?" }]);
  const [avaInput, setAvaInput] = useState('');

  const speak = useCallback((text) => {
    window.speechSynthesis.cancel();
    const utter = new SpeechSynthesisUtterance(text);
    utter.onstart = () => setSpeaking(true);
    utter.onend = () => setSpeaking(false);
    window.speechSynthesis.speak(utter);
  }, []);

  const startPresentation = (product) => {
    setSelectedProduct(product);
    setStep('presentation');
    const intro = `Hello Dr. ${user?.name || 'Guest'}. I am your Ava Doctor. Today I wanted to present ${product.name}, which showed significant results in the ${product.trial} trial. How can I help you with more details?`;
    setMessages([{ role: 'delegate', text: intro }]);
    speak(intro);
  };

  const handleUserMessage = (text) => {
    if (!text.trim()) return;
    setMessages(prev => [...prev, { role: 'doctor', text }]);
    setInput('');
    setMicOn(false);
    
    setTimeout(() => {
      const reply = `That is a great point regarding ${selectedProduct.name}. The clinical data from ${selectedProduct.trial} suggests a robust safety profile. Would you like to see the dosing guidelines?`;
      setMessages(prev => [...prev, { role: 'delegate', text: reply }]);
      speak(reply);
    }, 1000);
  };

  const toggleMic = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) return;
    if (micOn) {
      recognitionRef.current?.stop();
      setMicOn(false);
    } else {
      const rec = new SpeechRecognition();
      rec.lang = 'en-US';
      rec.onresult = (e) => handleUserMessage(e.results[0][0].transcript);
      rec.start();
      recognitionRef.current = rec;
      setMicOn(true);
    }
  };

  const handleAvaChat = () => {
    if (!avaInput.trim()) return;
    setAvaChat(prev => [...prev, { role: 'doctor', text: avaInput }]);
    const query = avaInput.toLowerCase();
    setAvaInput('');
    
    setTimeout(() => {
      let reply = "I'm looking into the clinical database for you. Generally, Avalife Core therapy is well tolerated across elderly populations.";
      if (query.includes('trial')) reply = "The EMPA-REG OUTCOME trial demonstrated a 38% relative risk reduction in CV death.";
      if (query.includes('side effect')) reply = "Common side effects include urinary tract infections and mycotic genital infections. Safety first!";
      
      setAvaChat(prev => [...prev, { role: 'samar', text: reply }]);
    }, 800);
  };

  return (
    <div className="min-h-screen bg-[#F8FAFC] flex flex-col p-8 font-sans overflow-hidden">
      {/* Header */}
      <header className="flex justify-between items-center mb-8 bg-white/50 backdrop-blur-md p-4 rounded-3xl border border-white shadow-sm">
        <div className="flex items-center gap-3">
          <div className="w-14 h-14 bg-[#0A5C5C] rounded-2xl flex items-center justify-center text-white font-black text-2xl shadow-xl shadow-teal-900/50">A</div>
          <h1 className="text-4xl font-black tracking-tighter text-slate-900 uppercase italic">AVA<span className="text-[#E6B800]">LIVE</span></h1>
        </div>
        <div className="flex items-center gap-6">
          <button onClick={() => setShowAva(true)} className="flex items-center gap-2 px-6 py-2.5 bg-gradient-to-r from-amber-400 to-amber-600 text-white rounded-full font-black text-xs uppercase tracking-widest shadow-lg shadow-amber-900/20 hover:scale-105 transition-transform">
             <Sparkles size={14} /> Ask Ava
          </button>
          <button onClick={() => { logout(); navigate('/'); }} className="text-slate-400 font-bold text-sm hover:text-rose-600 transition-colors">Exit Session</button>
        </div>
      </header>

      <div className="max-w-6xl mx-auto w-full flex-1 flex flex-col items-center justify-center">
        <AnimatePresence mode="wait">
          {step === 'select-delegate' && (
            <motion.div key="step1" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }} className="text-center w-full">
              <h2 className="text-4xl font-black text-slate-900 mb-4 tracking-tighter">Welcome, Doctor</h2>
              <p className="text-slate-500 font-medium mb-12 text-lg">Select a Medical Delegate to start your product briefing</p>
              <div className="grid grid-cols-3 gap-8 max-w-4xl mx-auto">
                {delegates.map((d) => (
                  <motion.button
                    key={d.id}
                    whileHover={{ y: -10, scale: 1.02 }}
                    onClick={() => { setSelectedDelegate(d); setStep('select-product'); }}
                    className="bg-white p-10 rounded-[40px] shadow-xl shadow-slate-200 border border-slate-100 flex flex-col items-center group relative overflow-hidden"
                  >
                    <div className={`absolute top-0 inset-x-0 h-2 bg-gradient-to-r ${d.color}`} />
                    <div className={`w-24 h-24 rounded-full bg-gradient-to-br ${d.color} flex items-center justify-center text-white font-black text-4xl mb-6 shadow-2xl group-hover:rotate-6 transition-transform`}>
                      {d.name[0]}
                    </div>
                    <p className="font-black text-2xl text-slate-900 mb-1">{d.name}</p>
                    <p className="text-slate-400 text-[10px] font-black uppercase tracking-widest mb-8">{d.specialty}</p>
                    <div className="px-8 py-3 bg-slate-50 rounded-2xl text-slate-500 group-hover:bg-rose-600 group-hover:text-white font-black text-xs uppercase tracking-wider transition-all">Start Briefing</div>
                  </motion.button>
                ))}
              </div>
            </motion.div>
          )}

          {step === 'select-product' && (
            <motion.div key="step2" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }} className="text-center w-full">
              <div className="flex flex-col items-center mb-12">
                <button onClick={() => setStep('select-delegate')} className="text-rose-600 font-black text-xs uppercase tracking-widest mb-4 hover:underline">← Change Delegate</button>
                <h2 className="text-4xl font-black text-slate-900 tracking-tighter">What would you like to review?</h2>
                <p className="text-slate-500 font-medium mt-2 text-lg">Discussing with <span className="text-rose-600 font-black">{selectedDelegate.name}</span></p>
              </div>
              <div className="grid grid-cols-2 gap-8 max-w-4xl mx-auto">
                {products.map((p) => (
                  <motion.button
                    key={p.name}
                    whileHover={{ scale: 1.02, y: -4 }}
                    onClick={() => startPresentation(p)}
                    className="bg-white p-10 rounded-[40px] shadow-xl shadow-slate-200 border border-slate-100 text-left flex flex-col group relative overflow-hidden"
                  >
                    <div className="w-16 h-16 rounded-3xl bg-rose-50 text-rose-600 flex items-center justify-center mb-8 group-hover:bg-rose-600 group-hover:text-white transition-colors">
                      <Package size={32} />
                    </div>
                    <p className="font-black text-3xl text-slate-900 mb-3 tracking-tighter">{p.name}</p>
                    <p className="text-slate-500 font-medium text-lg mb-8 leading-relaxed">{p.detail}</p>
                    <div className="mt-auto flex items-center gap-2 text-rose-600 font-black text-xs uppercase tracking-widest group-hover:translate-x-2 transition-transform">
                      Initiate Detailing <ChevronRight size={14} />
                    </div>
                  </motion.button>
                ))}
              </div>
            </motion.div>
          )}

          {step === 'presentation' && (
            <motion.div key="step3" initial={{ opacity: 0, scale: 0.98 }} animate={{ opacity: 1, scale: 1 }} className="flex gap-8 w-full max-w-6xl h-[600px]">
              {/* Left: Avatar Video Mode */}
              <div className="w-2/5 flex flex-col gap-6">
                <div className="bg-[#0F172A] rounded-[48px] flex-1 flex flex-col items-center justify-center p-12 relative overflow-hidden shadow-2xl border-4 border-white">
                   <div className="absolute inset-0 bg-gradient-to-b from-rose-900/10 to-transparent pointer-events-none" />
                   <motion.div 
                     animate={speaking ? { scale: [1, 1.05, 1], rotate: [0, 1, -1, 0] } : {}}
                     transition={{ repeat: Infinity, duration: 0.5 }}
                     className={`w-48 h-48 rounded-full bg-gradient-to-br ${selectedDelegate.color} flex items-center justify-center text-white font-black text-7xl shadow-2xl relative border-8 border-white/10`}
                   >
                     {selectedDelegate.name[0]}
                     {speaking && (
                        <div className="absolute -bottom-4 -right-2 w-14 h-14 bg-rose-500 rounded-full border-8 border-[#0F172A] flex items-center justify-center">
                           <Volume2 size={24} className="text-white" />
                        </div>
                     )}
                   </motion.div>
                   <div className="text-center mt-12">
                     <p className="text-white font-black text-3xl tracking-tight">{selectedDelegate.name}</p>
                     <p className="text-rose-400 text-[10px] font-black uppercase tracking-[0.2em] mt-2">Your Scientific Delegate</p>
                   </div>
                </div>
              </div>

              {/* Right: Interaction Workspace */}
              <div className="flex-1 flex flex-col bg-white border border-slate-200 rounded-[48px] overflow-hidden shadow-2xl shadow-slate-200">
                <div className="p-8 border-b border-slate-100 flex justify-between items-center bg-slate-50/50">
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 rounded-full bg-rose-100 flex items-center justify-center">
                      <MessageSquare className="text-rose-600" size={20} />
                    </div>
                    <div>
                      <p className="font-black text-slate-900 uppercase text-xs tracking-widest">Detailing Flow</p>
                      <p className="text-[10px] font-bold text-slate-400 uppercase">{selectedProduct.name} Spotlight</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 px-4 py-1.5 bg-emerald-50 rounded-full">
                    <div className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse" />
                    <span className="text-[10px] font-black text-emerald-600 uppercase tracking-widest">Active Discussion</span>
                  </div>
                </div>

                <div className="flex-1 overflow-y-auto p-10 space-y-6">
                  {messages.map((m, i) => (
                    <motion.div key={i} initial={{ opacity: 0, x: m.role === 'doctor' ? 20 : -20 }} animate={{ opacity: 1, x: 0 }} className={`flex ${m.role === 'doctor' ? 'justify-end' : 'justify-start'}`}>
                      <div className={`max-w-[85%] p-5 rounded-3xl text-[13px] leading-relaxed font-bold shadow-sm ${m.role === 'doctor' ? 'bg-rose-600 text-white rounded-br-none' : 'bg-slate-100 text-slate-800 rounded-bl-none border border-slate-200'}`}>
                        {m.text}
                      </div>
                    </motion.div>
                  ))}
                  {speaking && (
                    <div className="flex items-center gap-2 text-rose-500 text-[10px] font-black uppercase tracking-widest animate-pulse px-2">
                       <Loader2 size={12} className="animate-spin" /> Representative is speaking...
                    </div>
                  )}
                </div>

                <div className="p-8 border-t border-slate-100 bg-slate-50/50 flex gap-4">
                  <button onClick={toggleMic} className={`w-16 h-16 rounded-[24px] flex items-center justify-center transition-all shadow-xl ${micOn ? 'bg-rose-500 text-white animate-pulse' : 'bg-white text-slate-400 hover:text-rose-600 border border-slate-200 hover:shadow-lg'}`}>
                    {micOn ? <Mic size={28} /> : <MicOff size={28} />}
                  </button>
                  <div className="flex-1 relative">
                    <input 
                      type="text" 
                      placeholder={micOn ? "Listening to your request..." : "Type your question to the representative..."}
                      value={input}
                      onChange={e => setInput(e.target.value)}
                      onKeyDown={e => e.key === 'Enter' && handleUserMessage(input)}
                      className="w-full h-16 pl-8 pr-16 bg-white border border-slate-200 rounded-[24px] text-sm font-bold outline-none focus:border-rose-400 shadow-xl transition-all"
                    />
                    <button onClick={() => handleUserMessage(input)} className="absolute right-3 top-3 w-10 h-10 bg-rose-600 text-white rounded-xl flex items-center justify-center hover:bg-rose-700 transition-colors shadow-lg shadow-rose-900/20">
                      <ChevronRight size={22} />
                    </button>
                  </div>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Ava Overlay */}
      <AnimatePresence>
        {showAva && (
          <motion.div 
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-[100] flex items-center justify-center p-8"
          >
            <motion.div 
              initial={{ scale: 0.9, y: 20 }} animate={{ scale: 1, y: 0 }} exit={{ scale: 0.9, y: 20 }}
              className="bg-white w-full max-w-2xl h-[600px] rounded-[48px] shadow-[0_32px_128px_-32px_rgba(0,0,0,0.4)] flex flex-col overflow-hidden relative"
            >
              <div className="p-8 bg-gradient-to-r from-amber-500 to-amber-700 flex justify-between items-center text-white">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-white/20 rounded-2xl flex items-center justify-center"><Sparkles size={24} /></div>
                  <div>
                    <p className="font-black text-xl leading-tight">Ava Assistant</p>
                    <p className="text-amber-100/60 text-[10px] font-black uppercase tracking-widest mt-0.5">Clinical Knowledge Engine</p>
                  </div>
                </div>
                <button onClick={() => setShowAva(false)} className="w-10 h-10 bg-white/10 rounded-xl flex items-center justify-center hover:bg-white/20 transition-colors"><X size={20} /></button>
              </div>

              <div className="flex-1 overflow-y-auto p-8 space-y-6 bg-slate-50">
                {avaChat.map((m, i) => (
                  <div key={i} className={`flex ${m.role === 'doctor' ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-[85%] p-5 rounded-3xl text-[13px] leading-relaxed font-bold shadow-sm ${m.role === 'doctor' ? 'bg-amber-600 text-white rounded-br-none' : 'bg-white text-slate-800 rounded-bl-none border border-slate-100'}`}>
                      {m.text}
                    </div>
                  </div>
                ))}
              </div>

              <div className="p-8 bg-white border-t border-slate-100 flex gap-4">
                <input 
                  type="text" 
                  value={avaInput}
                  onChange={e => setAvaInput(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && handleAvaChat()}
                  placeholder="Ask Ava for clinical data, dosages..."
                  className="flex-1 bg-slate-50 border border-slate-200 rounded-2xl px-6 py-4 text-sm font-bold outline-none focus:border-amber-400 transition-colors"
                />
                <button onClick={handleAvaChat} className="w-14 h-14 bg-amber-600 text-white rounded-2xl flex items-center justify-center shadow-lg shadow-amber-900/20 hover:bg-amber-700 transition-colors">
                  <Send size={24} />
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
