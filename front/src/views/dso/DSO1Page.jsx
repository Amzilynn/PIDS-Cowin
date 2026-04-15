import { useState, useRef, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Camera, CameraOff, Mic, MicOff, Send, Loader2, Award, ClipboardCheck, Users, Target } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const commercialPhrases = [
  "How would you handle a pharmacist's objection to Avalife's stock availability?",
  "Pitch the ROI of the new patient loyalty program to a clinic owner.",
];

const medicalPhrases = [
  "Explain the cardiovascular safety profile of SGLT inhibitors based on the EMPA-REG trial.",
  "How do you address a physician's concern about DKA risks in elderly patients?",
];

export default function DSO1Page() {
  const navigate = useNavigate();
  const videoRef = useRef(null);
  const [roleType, setRoleType] = useState('Medical'); // Medical vs Commercial
  const [cameraOn, setCameraOn] = useState(false);
  const [micOn, setMicOn] = useState(false);
  const [speaking, setSpeaking] = useState(false);
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [isRecording, setIsRecording] = useState(false);

  const [scores, setScores] = useState({
    knowledge: 0,
    confidence: 0,
    empathy: 0,
    compliance: 0
  });

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

  const handleSend = async (text) => {
    const msg = text || input;
    if (!msg.trim()) return;
    setMessages(prev => [...prev, { role: 'delegate', text: msg }]);
    setInput('');
    setLoading(true);

    // AI logic simulation
    setTimeout(() => {
      const reply = roleType === 'Medical'
        ? "Excellent clinical depth. Now, how would you transition to the kidney protection data?"
        : "Strong commercial pitch. Remember to emphasize the pharmacist's margin in the next part.";
      setMessages(prev => [...prev, { role: 'evaluator', text: reply }]);
      speak(reply);
      setScores({
        knowledge: Math.min(scores.knowledge + 15, 95),
        confidence: Math.min(scores.confidence + 10, 92),
        empathy: 88,
        compliance: 100
      });
      setLoading(false);
    }, 1200);
  };

  const toggleRecording = async () => {
    const newStatus = !isRecording;
    
    // Appel à l'API backend pour démarrer ou arrêter l'enregistrement
    try {
      await fetch('http://localhost:8001/api/training/speech_control', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: newStatus ? 'start' : 'stop' })
      });
    } catch (err) {
      console.log("Attention: Backend API non joignable (PTT).", err);
    }

    setIsRecording(newStatus);
    if (!newStatus) {
      setLoading(true);
      // Simulation pour l'UI, le vrai backend va envoyer le texte via websockets ou un GET
      // On arrête le loading visuel après un moment pour simuler le STT processing
      setTimeout(() => setLoading(false), 2000);
    }
  };

  return (
    <div className="min-h-screen bg-[#0F172A] text-slate-100 p-8 flex flex-col font-sans">
      <header className="flex justify-between items-center mb-8 border-b border-slate-800 pb-6">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 bg-teal-500 rounded-2xl flex items-center justify-center text-white font-black text-2xl shadow-xl shadow-teal-900/50">D1</div>
          <div>
            <h1 className="text-2xl font-black tracking-tighter uppercase italic">AVA<span className="text-[#E6B800]">LIVE</span> <span className="text-teal-400">TRAINING</span></h1>
            <p className="text-slate-500 text-xs font-bold uppercase tracking-widest px-1">Advanced Evaluation Platform</p>
          </div>
        </div>
        <div className="flex bg-slate-800 p-1.5 rounded-2xl border border-slate-700">
          {['Medical', 'Commercial'].map(r => (
            <button key={r} onClick={() => { setRoleType(r); setMessages([]); }} className={`px-6 py-2.5 rounded-xl font-bold text-sm transition-all ${roleType === r ? 'bg-teal-500 text-white shadow-lg' : 'text-slate-400 hover:text-white'}`}>
              {r} Delegate
            </button>
          ))}
        </div>
        <button onClick={() => navigate('/')} className="text-slate-500 hover:text-white font-bold text-sm transition-colors">Exit DSO1</button>
      </header>

      <div className="grid grid-cols-12 gap-8 flex-1">
        {/* Left: Avatar Placeholder & Camera */}
        <div className="col-span-4 flex flex-col gap-6">
          <div className="bg-slate-800/50 rounded-3xl border border-slate-700 p-8 flex flex-col items-center justify-center relative overflow-hidden flex-1 min-h-[300px]">
            <div className="absolute top-4 left-4 flex gap-2">
              <div className="bg-slate-900/80 px-3 py-1 rounded-full border border-slate-700 text-[10px] font-black uppercase text-teal-400">Ava Train</div>
            </div>
            {/* Avatar Circle */}
            <motion.div
              animate={speaking ? { scale: [1, 1.05, 1], rotate: [0, 2, -2, 0] } : {}}
              transition={{ repeat: Infinity, duration: 0.6 }}
              className="w-32 h-32 rounded-full bg-gradient-to-br from-teal-500 to-teal-800 flex items-center justify-center text-white font-black text-5xl shadow-2xl mb-6 border-4 border-slate-700"
            >
              A
            </motion.div>
            <p className="font-black text-xl mb-1">Ava Audit</p>
            <p className="text-slate-400 text-xs font-bold font-mono px-4 text-center">READY FOR {roleType.toUpperCase()} SECTOR AUDIT</p>
            {speaking && (
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex gap-1.5 mt-6">
                {[0, 1, 2, 3, 4].map(i => (
                  <motion.div key={i} animate={{ height: ['8px', '24px', '8px'] }} transition={{ repeat: Infinity, duration: 0.4, delay: i * 0.1 }} className="w-1.5 bg-teal-400 rounded-full" />
                ))}
              </motion.div>
            )}
          </div>

          <div className="bg-black rounded-3xl overflow-hidden relative h-[240px] border border-slate-800">
            <video ref={videoRef} autoPlay muted className="w-full h-full object-cover opacity-80" />
            {!cameraOn && (
              <div className="absolute inset-0 flex flex-col items-center justify-center text-slate-700">
                <CameraOff size={40} className="mb-2" />
                <p className="text-xs font-black uppercase tracking-widest">Feed Disabled</p>
              </div>
            )}
            <div className="absolute top-4 right-4 flex gap-2">
              <button onClick={toggleCamera} className={`w-10 h-10 rounded-xl flex items-center justify-center transition-all ${cameraOn ? 'bg-teal-500 text-white shadow-lg shadow-teal-900/50' : 'bg-slate-800/80 text-slate-400 border border-slate-700'}`}>
                <Camera size={18} />
              </button>
            </div>
          </div>
        </div>

        {/* Center: Dialogue */}
        <div className="col-span-5 flex flex-col bg-slate-800/30 rounded-3xl border border-slate-800 overflow-hidden shadow-2xl backdrop-blur-sm">
          <div className="p-6 border-b border-slate-700 flex justify-between items-center bg-slate-800/50">
            <div className="flex items-center gap-3">
              <ClipboardCheck size={20} className="text-teal-400" />
              <p className="font-black text-sm uppercase tracking-wider">Evaluation Log</p>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            {messages.length === 0 && (
              <div className="h-full flex flex-col items-center justify-center text-center opacity-40">
                <Award size={48} className="mb-4" />
                <p className="font-black text-lg">Initialize Simulation</p>
                <p className="text-xs font-medium max-w-[200px] mt-2">Start typing your medical pitch or clinical reasoning to begin the evaluation.</p>
              </div>
            )}
            <AnimatePresence>
              {messages.map((m, i) => (
                <motion.div key={i} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className={`flex ${m.role === 'delegate' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-[85%] p-5 rounded-2xl text-sm leading-relaxed font-medium shadow-lg transition-all ${m.role === 'delegate' ? 'bg-teal-600 text-white rounded-br-sm' : 'bg-slate-800 text-slate-100 rounded-bl-sm border border-slate-700'}`}>
                    {m.text}
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
            {loading && (
              <div className="flex items-center gap-3 text-teal-400 text-xs font-black uppercase tracking-widest animate-pulse">
                <Loader2 size={14} className="animate-spin" /> Processing Audit...
              </div>
            )}
          </div>

          <div className="p-6 border-t border-slate-800 bg-slate-900/50">
            <div className="flex gap-4">
              <button 
                onClick={toggleRecording} 
                className={`h-14 px-6 rounded-2xl flex items-center gap-3 transition-all font-black text-sm uppercase tracking-wider shadow-xl ${isRecording ? 'bg-rose-500 text-white animate-pulse shadow-rose-900/40' : 'bg-slate-800 text-slate-300 hover:bg-slate-700 hover:text-white border border-slate-700'}`}
                title={isRecording ? "Arrêter l'enregistrement" : "Parler (Push to Talk)"}
              >
                {isRecording ? <Mic size={20} /> : <MicOff size={20} />}
                {isRecording ? "Recording..." : "Push to Talk"}
              </button>
              <input
                type="text"
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleSend()}
                placeholder="Enter clinical response or push the mic to talk..."
                className="flex-1 bg-slate-900/80 border border-slate-700 rounded-2xl px-6 py-4 text-sm font-bold outline-none focus:border-teal-500 transition-colors placeholder:text-slate-600"
                disabled={isRecording}
              />
              <button onClick={() => !isRecording && handleSend()} disabled={isRecording} className={`w-14 h-14 rounded-2xl flex items-center justify-center transition-all shadow-xl ${isRecording ? 'bg-slate-800 text-slate-600 cursor-not-allowed' : 'bg-teal-500 text-white hover:bg-teal-400 shadow-teal-900/40'}`}>
                <Send size={20} />
              </button>
            </div>
            {isRecording && (
              <p className="text-center text-xs font-bold text-rose-500 mt-3 animate-pulse">🔴 Recording your speech... click mic again to send.</p>
            )}
          </div>
        </div>

        {/* Right: Enriched Evaluation */}
        <div className="col-span-3 space-y-6">
          <div className="bg-slate-800/50 rounded-3xl border border-slate-700 p-8 shadow-xl">
            <h3 className="font-black text-sm uppercase tracking-widest text-teal-400 mb-8 border-b border-slate-700 pb-4">Audit Metrics</h3>
            <div className="space-y-8">
              {[
                { label: 'Knowledge Accuracy', value: scores.knowledge, icon: Target, color: 'teal' },
                { label: 'Pitch Confidence', value: scores.confidence, icon: Award, color: 'emerald' },
                { label: 'Professional Empathy', value: scores.empathy, icon: Users, color: 'indigo' },
                { label: 'Med-Reg Compliance', value: scores.compliance, icon: ClipboardCheck, color: 'rose' }
              ].map((s, i) => (
                <div key={i}>
                  <div className="flex justify-between text-[11px] font-black uppercase mb-3 text-slate-400">
                    <span className="flex items-center gap-2"><s.icon size={12} /> {s.label}</span>
                    <span className="text-slate-100">{s.value}%</span>
                  </div>
                  <div className="h-2 bg-slate-900 rounded-full overflow-hidden border border-slate-700">
                    <motion.div animate={{ width: `${s.value}%` }} transition={{ duration: 0.8 }} className={`h-full rounded-full bg-${s.color}-500`} />
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="p-6 bg-teal-500/10 rounded-3xl border border-teal-500/20">
            <p className="text-teal-400 font-black text-xs uppercase tracking-widest mb-2">Evaluator Verdict</p>
            <p className="text-xs font-medium text-slate-300 leading-relaxed italic">"The delegate demonstrates robust clinical reasoning. Compliance is perfect. Improvement needed in closing speed."</p>
          </div>
        </div>
      </div>
    </div>
  );
}
