import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, Loader2, Sparkles, Mic, MicOff, Volume2, VolumeX } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

const SERVER_URL = 'http://localhost:5000';

const AVA_OPENING = "Hi! I'm Ava, your AI medical assistant. I can help you prepare for physician visits, summarize product data, or answer clinical questions. How can I help you today? 😊";

const localResponses = [
  { keywords: ['product', 'ava', 'live'], reply: "The Avalive Core is an SGLT2 inhibitor for T2D and cardiovascular risk. It's best known for its 35% reduction in heart failure cases. We currently hold a 64% market share in the cardio segment." },
  { keywords: ['visit', 'prepare', 'doctor'], reply: "I suggest opening your next visit with the EMPA-REG trial data. Don't forget to address DKA risks and mention renal protection. It usually builds strong trust with specialists." },
  { keywords: ['side effect', 'adverse', 'risk'], reply: "When talking about safety, keep in mind: UTI risk is around +10%, and DKA is extremely rare (<0.1%). It's always a good practice to mention eGFR monitoring." },
  { keywords: ['help', 'what can you do'], reply: "I'm here to help with your product summaries, visit scripts, clinical trial lookups, or objection handling. Just ask!" },
  { keywords: ['hello', 'hi', 'hey'], reply: "Hello! It's great to see you. How's your territory looking today? Anything I can help you prepare for?" },
];

function getAvaResponse(msg, context) {
  const lower = msg.toLowerCase();
  
  // Adaptive awareness
  let prefix = "";
  if (context.length > 0) {
    const lastTopic = context[context.length - 1];
    if (!lower.includes(lastTopic)) {
      prefix = `Expanding on our discussion about ${lastTopic}, `;
    }
  }

  const found = localResponses.find(r => r.keywords.some(k => lower.includes(k)));
  const baseReply = found ? found.reply : "That's an interesting point. Based on the 2026 clinical landscape, Avalive remains a leader in evidence-based therapy. Shall I look up specific guidelines for you?";
  
  return prefix + baseReply;
}

export default function AssistantPage() {
  const { user } = useAuth();
  const userName = user?.display_name?.split(' ')[0] || "there";
  const [messages, setMessages] = useState([
    { role: 'assistant', text: `Hello ${userName}! I am Ava, your personal Medical Intelligence Assistant. How can I help you today with your territory or clinical data?` }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [micOn, setMicOn] = useState(false);
  const [ttsOn, setTtsOn] = useState(true);
  const [learnedContext, setLearnedContext] = useState([]);
  const chatEndRef = useRef(null);
  const recognitionRef = useRef(null);

  useEffect(() => { chatEndRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages]);

  // Load persistent context
  useEffect(() => {
    fetch(`${SERVER_URL}/api/simulate/context`)
      .then(r => r.json())
      .then(d => { if (Array.isArray(d)) setLearnedContext(d); })
      .catch(() => {});
  }, []);

  const speak = (text) => {
    if (!ttsOn) return;
    window.speechSynthesis.cancel();
    const utter = new SpeechSynthesisUtterance(text);
    utter.rate = 1.0;
    utter.pitch = 1.1;
    window.speechSynthesis.speak(utter);
  };

  const toggleMic = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) { alert('Speech recognition not supported in this browser.'); return; }
    
    if (micOn) {
      recognitionRef.current?.stop();
      setMicOn(false);
    } else {
      const rec = new SpeechRecognition();
      rec.lang = 'en-US';
      rec.continuous = false;
      rec.onresult = (e) => {
        const transcript = e.results[0][0].transcript;
        setInput(transcript);
        setMicOn(false);
      };
      rec.start();
      recognitionRef.current = rec;
      setMicOn(true);
    }
  };

  const handleSend = async (text) => {
    const msg = text || input;
    if (!msg.trim()) return;
    setMessages(prev => [...prev, { role: 'user', text: msg }]);
    setInput('');
    setLoading(true);

    // Update learned context
    const topics = ['sfax', 'tunis', 'stock', 'side effect', 'visit', 'product', 'cardio', 'guidelines'];
    const matchedTopic = topics.find(t => msg.toLowerCase().includes(t));
    if (matchedTopic && !learnedContext.includes(matchedTopic)) {
      setLearnedContext(prev => [...prev, matchedTopic]);
      fetch(`${SERVER_URL}/api/simulate/context`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topic: matchedTopic }),
      }).catch(() => {});
    }

    // Simulated Ava logic
    setTimeout(() => {
      const reply = getAvaResponse(msg, learnedContext);
      setMessages(prev => [...prev, { role: 'assistant', text: reply }]);
      speak(reply);
      setLoading(false);
    }, 1000);
  };

  return (
    <div className="flex flex-col h-full space-y-4">
      <div>
        <h2 className="text-2xl font-black tracking-tighter text-slate-800 flex items-center gap-3">
          <Sparkles className="text-[#E6B800]" size={26} />
          Ava — AI Assistant
        </h2>
        <p className="text-slate-500 text-sm font-medium mt-1">Your personal medical delegation intelligence assistant</p>
      </div>

      {/* Chat Container */}
      <div className="flex-1 bg-white border border-slate-200 rounded-3xl overflow-hidden flex flex-col shadow-sm" style={{ minHeight: '540px' }}>
        {/* Header */}
        <div className="p-5 bg-gradient-to-r from-[#0F172A] to-slate-800 flex items-center gap-4">
          <div className="relative">
            <div className="w-12 h-12 rounded-full bg-gradient-to-br from-[#E6B800] to-amber-600 flex items-center justify-center font-black text-xl text-white shadow-xl">A</div>
            <div className="absolute bottom-0 right-0 w-3.5 h-3.5 bg-emerald-500 rounded-full border-2 border-slate-900" />
          </div>
          <div>
            <p className="font-black text-white">Ava</p>
            <p className="text-xs text-emerald-400 font-bold">AI Medical Delegate Assistant • Online</p>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4 bg-slate-50/50">
          <AnimatePresence>
            {messages.map((msg, i) => (
              <motion.div key={i} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} items-end gap-3`}>
                {msg.role === 'assistant' && (
                  <div className="w-8 h-8 rounded-full bg-gradient-to-br from-[#E6B800] to-amber-600 flex items-center justify-center font-black text-xs text-white flex-shrink-0">A</div>
                )}
                <div className={`max-w-[75%] px-5 py-3.5 rounded-2xl text-sm leading-relaxed font-medium shadow-sm ${
                  msg.role === 'user'
                    ? 'bg-indigo-600 text-white rounded-br-sm'
                    : 'bg-white text-slate-700 rounded-bl-sm border border-slate-200'
                }`}>
                  {msg.text}
                </div>
                {msg.role === 'user' && (
                  <div className="w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center font-black text-xs text-indigo-600 flex-shrink-0">
                    {user?.display_name?.[0] || 'U'}
                  </div>
                )}
              </motion.div>
            ))}
          </AnimatePresence>
          {loading && (
            <div className="flex items-end gap-3">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-[#E6B800] to-amber-600 flex items-center justify-center font-black text-xs text-white flex-shrink-0">A</div>
              <div className="bg-white border border-slate-200 rounded-2xl rounded-bl-sm px-5 py-3.5 flex items-center gap-2">
                <Loader2 size={14} className="animate-spin text-amber-500" />
                <span className="text-sm text-slate-500 font-medium">Ava is thinking...</span>
              </div>
            </div>
          )}
          <div ref={chatEndRef} />
        </div>

        {/* Input */}
        <div className="p-5 border-t border-slate-100 bg-white">
          {learnedContext.length > 0 && (
            <div className="flex gap-2 mb-3 overflow-x-auto pb-1 no-scrollbar">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest self-center mr-2">Adaptive Focus:</span>
              {learnedContext.map((topic, i) => (
                <span key={i} className="px-3 py-1 bg-amber-50 text-amber-700 rounded-full text-[10px] font-black uppercase border border-amber-100">
                  {topic}
                </span>
              ))}
            </div>
          )}
          <div className="flex gap-3">
            <button 
              onClick={toggleMic}
              className={`flex-shrink-0 w-12 h-12 rounded-xl flex items-center justify-center transition-all ${micOn ? 'bg-rose-500 text-white animate-pulse shadow-lg shadow-rose-200' : 'bg-slate-100 text-slate-500 hover:bg-slate-200'}`}
            >
              {micOn ? <MicOff size={20} /> : <Mic size={20} />}
            </button>
            <input
              type="text"
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleSend()}
              placeholder={micOn ? "Listening..." : "Ask Ava about products, visits, or clinical data..."}
              className="flex-1 bg-slate-50 border border-slate-200 rounded-xl px-5 py-3 text-sm font-medium outline-none focus:border-amber-400 transition-colors"
            />
            <button onClick={() => setTtsOn(!ttsOn)} className={`flex-shrink-0 w-12 h-12 rounded-xl flex items-center justify-center transition-all ${ttsOn ? 'bg-teal-50 text-teal-600' : 'bg-slate-100 text-slate-400'}`}>
              {ttsOn ? <Volume2 size={20} /> : <VolumeX size={20} />}
            </button>
            <button onClick={() => handleSend()} disabled={!input.trim() || loading}
              className="flex-shrink-0 px-6 py-3 bg-gradient-to-r from-[#E6B800] to-amber-500 text-white rounded-xl font-black text-sm disabled:opacity-50 hover:opacity-90 transition-all flex items-center gap-2">
              <Send size={18} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
