import { useState, useRef, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Package, Mic, MicOff, Volume2, ChevronLeft, ChevronRight, Globe, Pill, ShieldCheck, Camera, CameraOff, Send, Loader2, TrendingUp, ShieldAlert } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const productSlides = [
  { 
    id: 'intro', 
    title: 'Avalife Core™ Portfolio', 
    medical: 'Leading SGLT2i with multi-organ protection (Heart, Kidney, Metabolic).',
    commercial: 'Market leader in SGLT2 category with 64% share and 12% YoY growth.',
    icon: Globe,
    stats: {
      Medical: [{ label: 'CV Death Reduc.', val: '38%' }, { label: 'HF Hosp. Reduc.', val: '35%' }],
      Commercial: [{ label: 'Market Share', val: '64%' }, { label: 'Growth', val: '+12%' }]
    }
  },
  { 
    id: 'trials', 
    title: 'Clinical Excellence', 
    medical: 'EMPA-REG OUTCOME results demonstrate robust safety in CV-risk patients.',
    commercial: 'Superior formulary positioning and Tier 1 access for $0 copay.',
    icon: ShieldCheck,
    stats: {
      Medical: [{ label: 'A1c Reduction', val: '0.8%' }, { label: 'Weight Loss', val: '2.5kg' }],
      Commercial: [{ label: 'Payer Access', val: '92%' }, { label: 'Retail Stock', val: '98%' }]
    }
  },
  { 
    id: 'dosing', 
    title: 'Precision Dosing', 
    medical: 'Once-daily 10mg tablet. High adherence due to simple regimen.',
    commercial: 'Available in 30-day and 90-day packs for maximized sell-out.',
    icon: Pill,
    stats: {
      Medical: [{ label: 'Adherence', val: '94%' }, { label: 'Compliance', val: '96%' }],
      Commercial: [{ label: 'Patient Reach', val: '1.2M' }, { label: 'Scripts/Day', val: '4.5k' }]
    }
  }
];

export default function DSO2Page() {
  const navigate = useNavigate();
  const videoRef = useRef(null);
  const [slideIdx, setSlideIdx] = useState(0);
  const [roleType, setRoleType] = useState('Medical'); // Medical vs Commercial
  const [cameraOn, setCameraOn] = useState(false);
  const [micOn, setMicOn] = useState(false);
  const [speaking, setSpeaking] = useState(false);
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState([{ role: 'agent', text: "Hello. I am Ava Business. Would you like to review the product deck for Avalive Core?" }]);
  const recognitionRef = useRef(null);

  const speak = useCallback((text) => {
    window.speechSynthesis.cancel();
    const utter = new SpeechSynthesisUtterance(text);
    utter.onstart = () => setSpeaking(true);
    utter.onend = () => setSpeaking(false);
    window.speechSynthesis.speak(utter);
  }, []);

  const toggleCamera = async () => {
    if (cameraOn) {
      const stream = videoRef.current?.srcObject;
      stream?.getTracks().forEach(t => t.stop());
      setCameraOn(false);
    } else {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
        if (videoRef.current) videoRef.current.srcObject = stream;
        setCameraOn(true);
      } catch { alert('Camera permission denied.'); }
    }
  };

  const handleUserMessage = (text) => {
    const msg = text || input;
    if (!msg.trim()) return;
    setMessages(prev => [...prev, { role: 'doctor', text: msg }]);
    setInput('');
    setMicOn(false);
    
    setTimeout(() => {
      const reply = roleType === 'Medical' 
        ? `The clinical data for ${productSlides[slideIdx].title} is quite definitive. Would you like to see the safety protocol?`
        : `Commercially, ${productSlides[slideIdx].title} is outperforming the category average by 2.5x. Let's look at the ROI.`;
      setMessages(prev => [...prev, { role: 'agent', text: reply }]);
      speak(reply);
    }, 1000);
  };

  const toggleMic = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) return;
    if (micOn) { recognitionRef.current?.stop(); setMicOn(false); }
    else {
      const rec = new SpeechRecognition();
      rec.onresult = (e) => handleUserMessage(e.results[0][0].transcript);
      rec.start();
      recognitionRef.current = rec;
      setMicOn(true);
    }
  };

  const slide = productSlides[slideIdx];

  return (
    <div className="min-h-screen bg-[#F0F2F5] text-slate-900 p-8 flex flex-col font-sans overflow-hidden">
      <header className="flex justify-between items-center mb-8 border-b border-slate-200 pb-6">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 bg-indigo-600 rounded-2xl flex items-center justify-center text-white font-black text-2xl shadow-xl shadow-indigo-900/20">D2</div>
          <div>
            <h1 className="text-2xl font-black tracking-tighter uppercase italic">AVA<span className="text-[#E6B800]">LIVE</span> <span className="text-indigo-600">PRODUCT DEMO</span></h1>
            <p className="text-slate-400 text-[10px] font-black uppercase tracking-widest font-mono px-1">Interactive Detailing — Ava Business vs {roleType}</p>
          </div>
        </div>
        <div className="flex bg-white/50 p-1.5 rounded-2xl border border-slate-200 shadow-sm backdrop-blur-md">
           {['Medical', 'Commercial'].map(r => (
             <button key={r} onClick={() => setRoleType(r)} className={`px-6 py-2 rounded-xl font-black text-[10px] uppercase tracking-widest transition-all ${roleType === r ? 'bg-indigo-600 text-white shadow-lg' : 'text-slate-400 hover:text-slate-600'}`}>
                {r} Sector
             </button>
           ))}
        </div>
        <button onClick={() => navigate('/')} className="text-slate-400 hover:text-slate-600 font-bold text-sm transition-colors">Exit DSO2</button>
      </header>

      <div className="grid grid-cols-12 gap-8 flex-1">
        {/* Left: Avatar & Camera Feed (Legacy consistency) */}
        <div className="col-span-3 flex flex-col gap-6">
          <div className="bg-[#0F172A] rounded-[48px] p-10 flex flex-col items-center justify-center relative overflow-hidden flex-1 min-h-[300px] shadow-2xl border-2 border-white/5">
            <div className="absolute inset-0 bg-gradient-to-b from-indigo-500/10 to-transparent pointer-events-none" />
            <motion.div 
               animate={speaking ? { scale: [1, 1.05, 1], y: [0, -4, 0] } : {}}
               transition={{ repeat: Infinity, duration: 0.5 }}
               className="w-32 h-32 rounded-full bg-gradient-to-br from-indigo-400 to-indigo-700 flex items-center justify-center text-white font-black text-5xl shadow-2xl mb-8 relative border-4 border-white/10"
            >
              A
              {speaking && (
                <div className="absolute -bottom-2 -right-1 w-12 h-12 bg-emerald-500 rounded-full border-4 border-[#0F172A] flex items-center justify-center">
                  <Volume2 size={24} className="text-white" />
                </div>
              )}
            </motion.div>
            <p className="text-white font-black text-2xl tracking-tight leading-none mb-2">Ava Business</p>
            <div className="px-4 py-1.5 bg-indigo-500/20 rounded-full border border-indigo-500/30">
               <p className="text-indigo-400 text-[10px] font-black uppercase tracking-widest">Scientific Specialist</p>
            </div>
          </div>

          <div className="bg-[#0F172A] rounded-[48px] overflow-hidden relative h-[250px] shadow-xl border-4 border-white group">
            <video ref={videoRef} autoPlay muted className="w-full h-full object-cover opacity-60 group-hover:opacity-100 transition-opacity" />
            {!cameraOn && (
              <div className="absolute inset-0 flex flex-col items-center justify-center text-white/30">
                <CameraOff size={40} className="mb-3" />
                <p className="text-[10px] font-black uppercase tracking-[0.2em]">Clinic Feed Off</p>
              </div>
            )}
            <button onClick={toggleCamera} className={`absolute top-6 right-6 w-12 h-12 rounded-2xl flex items-center justify-center transition-all bg-white shadow-xl ${cameraOn ? 'text-indigo-600' : 'text-slate-400'}`}>
              <Camera size={20} />
            </button>
            <div className="absolute bottom-6 left-6 flex items-center gap-2">
               <div className="w-2 h-2 bg-rose-500 rounded-full animate-pulse" />
               <p className="text-[9px] font-black text-white/60 uppercase tracking-widest">Live Integration</p>
            </div>
          </div>
        </div>

        {/* Center: Interactive Slide Deck */}
        <div className="col-span-6 flex flex-col gap-6">
          <div className="bg-white rounded-[64px] shadow-2xl shadow-slate-200 border border-slate-100 overflow-hidden flex-1 flex flex-col">
            <div className="p-12 flex-1 flex flex-col justify-center">
               <AnimatePresence mode="wait">
                 <motion.div key={slideIdx + roleType} initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="flex-1 flex flex-col">
                   <div className="w-16 h-16 bg-indigo-50 text-indigo-600 rounded-3xl flex items-center justify-center mb-10 shadow-sm">
                     <slide.icon size={32} />
                   </div>
                   <h2 className="text-5xl font-black text-slate-900 mb-6 tracking-tighter leading-tight">{slide.title}</h2>
                   <p className="text-2xl text-slate-500 font-medium leading-relaxed mb-12">
                     {roleType === 'Medical' ? slide.medical : slide.commercial}
                   </p>
                   
                   <div className="grid grid-cols-2 gap-6">
                      {slide.stats[roleType].map((s, i) => (
                        <div key={i} className="bg-slate-50 border border-slate-100 rounded-[32px] p-8 group hover:bg-indigo-600 transition-colors">
                           <div className="flex items-center gap-3 mb-2">
                             {roleType === 'Medical' ? <ShieldAlert size={16} className="text-indigo-400 group-hover:text-white/60" /> : <TrendingUp size={16} className="text-indigo-400 group-hover:text-white/60" />}
                             <p className="text-[11px] font-black uppercase text-slate-400 tracking-widest group-hover:text-white/60">{s.label}</p>
                           </div>
                           <p className="text-5xl font-black text-indigo-600 tracking-tighter group-hover:text-white">{s.val}</p>
                        </div>
                      ))}
                   </div>
                 </motion.div>
               </AnimatePresence>
            </div>
            
            <div className="p-10 border-t border-slate-50 bg-slate-50/30 flex justify-between items-center px-12">
               <div className="flex gap-2">
                 {productSlides.map((_, i) => (
                   <div key={i} className={`h-2 rounded-full transition-all duration-300 ${i === slideIdx ? 'w-12 bg-indigo-600' : 'w-4 bg-slate-200'}`} />
                 ))}
               </div>
               <div className="flex gap-4">
                 <button onClick={() => setSlideIdx(p => Math.max(0, p-1))} className="w-14 h-14 bg-white rounded-2xl border border-slate-200 flex items-center justify-center text-slate-400 hover:text-indigo-600 transition-all hover:shadow-xl">
                    <ChevronLeft size={24} />
                 </button>
                 <button onClick={() => setSlideIdx(p => Math.min(productSlides.length -1, p+1))} className="px-10 h-14 bg-indigo-600 text-white rounded-[24px] shadow-2xl font-black text-xs uppercase tracking-widest flex items-center gap-3 hover:scale-105 transition-transform">
                    Next Insight <ChevronRight size={20} />
                 </button>
               </div>
            </div>
          </div>

          {/* Discussion Input */}
          <div className="bg-white rounded-[32px] border border-slate-200 p-5 shadow-2xl shadow-slate-200 flex gap-5 items-center backdrop-blur-xl border-white/40">
             <button onClick={toggleMic} className={`w-16 h-16 rounded-2xl flex items-center justify-center transition-all shadow-xl ${micOn ? 'bg-indigo-500 text-white animate-pulse' : 'bg-slate-50 text-slate-400 border border-slate-100'}`}>
               {micOn ? <Mic size={28} /> : <MicOff size={28} />}
             </button>
             <input 
               type="text" 
               value={input}
               onChange={e => setInput(e.target.value)}
               onKeyDown={e => e.key === 'Enter' && handleUserMessage()}
               placeholder={`Ask about ${roleType === 'Medical' ? 'clinical efficacy' : 'commercial ROI'}...`}
               className="flex-1 bg-transparent text-lg font-bold outline-none placeholder:text-slate-300 px-4"
             />
             <button onClick={() => handleUserMessage()} className="w-14 h-14 bg-indigo-600 text-white rounded-2xl flex items-center justify-center shadow-2xl shadow-indigo-900/40 hover:bg-indigo-700 transition-colors">
               <Send size={24} />
             </button>
          </div>
        </div>

        {/* Right: Interaction Workspace */}
        <div className="col-span-3 flex flex-col gap-8">
           <div className="bg-white rounded-[48px] border border-slate-200 shadow-xl flex flex-col flex-1 overflow-hidden transition-all hover:shadow-2xl">
              <div className="p-8 border-b border-slate-50 bg-slate-50/50 flex flex-col gap-1">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-indigo-600 rounded-full" />
                  <p className="font-black text-[11px] uppercase tracking-widest text-slate-900 leading-none">Insight Log</p>
                </div>
                <p className="text-[10px] font-bold text-slate-400 uppercase">Synchronized with AI Engine</p>
              </div>
              <div className="flex-1 overflow-y-auto p-8 space-y-6">
                 {messages.map((m, i) => (
                   <div key={i} className={`flex ${m.role === 'doctor' ? 'justify-end' : 'justify-start'}`}>
                     <div className={`max-w-[95%] p-5 rounded-3xl text-[12px] leading-relaxed font-bold shadow-sm border ${m.role === 'doctor' ? 'bg-indigo-600 text-white border-indigo-400 rounded-br-none' : 'bg-slate-50 text-slate-800 border-slate-100 rounded-bl-none'}`}>
                       {m.text}
                     </div>
                   </div>
                 ))}
                 {speaking && (
                   <div className="flex items-center gap-3 text-indigo-500 text-[10px] font-black uppercase tracking-widest animate-bounce mt-4">
                     <Loader2 size={12} className="animate-spin" /> Analyzing response...
                   </div>
                 )}
              </div>
           </div>
           
           <div className="grid grid-cols-1 gap-4">
             <div className="p-8 bg-indigo-600 rounded-[40px] text-white shadow-2xl shadow-indigo-900/30 flex flex-col gap-2 relative overflow-hidden group">
                <div className="absolute -right-4 -bottom-4 w-24 h-24 bg-white/10 rounded-full blur-2xl group-hover:scale-150 transition-transform" />
                <p className="text-[10px] font-black uppercase tracking-[0.2em] opacity-60">Success Score</p>
                <div className="flex items-end gap-3">
                   <p className="text-5xl font-black tracking-tighter leading-none text-white">98.2</p>
                   <p className="text-xs font-black text-indigo-200 mb-1 leading-none uppercase">/ 100</p>
                </div>
             </div>
             
             <button className="h-20 bg-white border border-slate-200 rounded-[32px] shadow-lg flex items-center justify-center gap-4 group hover:border-indigo-600 transition-all">
                <div className="w-10 h-10 bg-indigo-50 text-indigo-600 rounded-xl flex items-center justify-center group-hover:bg-indigo-600 group-hover:text-white transition-all">
                   <Package size={20} />
                </div>
                <p className="font-black text-xs uppercase tracking-widest text-slate-800">Request Clinical Samples</p>
             </button>
           </div>
        </div>
      </div>
    </div>
  );
}
