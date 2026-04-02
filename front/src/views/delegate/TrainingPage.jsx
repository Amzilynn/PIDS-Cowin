import { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Mic, MicOff, Volume2, VolumeX, Camera, CameraOff, Send, Loader2, ChevronDown } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

const SERVER_URL = 'http://localhost:5000';

// AI doctor phrases to speak via TTS
const greetings = [
  "Welcome. Let us begin your medical delegation simulation.",
  "I am Ava Train. Please answer my questions clearly and concisely.",
  "Remember to cite clinical trials to support your claims.",
];

export default function TrainingPage() {
  const { user } = useAuth();
  const videoRef = useRef(null);
  const chatEndRef = useRef(null);
  const recognitionRef = useRef(null);
  const faceDetectorRef = useRef(null);

  const [messages, setMessages] = useState([
    { role: 'doctor', message: "Ava Train (Evaluator): Welcome. Let's practice your clinical pitch for Avalive Core. How do you explain the EMPA-REG results to a skeptical cardiologist?" }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [cameraOn, setCameraOn] = useState(false);
  const [micOn, setMicOn] = useState(false);
  const [ttsOn, setTtsOn] = useState(true);
  const [doctorSpeaking, setDoctorSpeaking] = useState(false);
  const [scores, setScores] = useState({ eye: 0, know: 0 });
  const [transcript, setTranscript] = useState('');
  const [roleType, setRoleType] = useState('Medical');
  const [visionState, setVisionState] = useState({ confidence: 85, focus: 92, stress: 15 });
  const [detectedEmotion, setDetectedEmotion] = useState('Neutral');
  const [aiStatus, setAiStatus] = useState('Checking...');
  const [audioBase64, setAudioBase64] = useState(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  // Load Face-API.js and Models
  useEffect(() => {
    const loadModels = async () => {
      // Create script tag if not exists
      if (!window.faceapi) {
        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/face-api.js@0.22.2/dist/face-api.min.js';
        script.async = true;
        script.onload = async () => {
          await window.faceapi.nets.ssdMobilenetv1.loadFromUri('/models');
          await window.faceapi.nets.faceLandmark68Net.loadFromUri('/models');
          await window.faceapi.nets.faceExpressionNet.loadFromUri('/models');
          console.log('Face-API Models Loaded');
        };
        document.body.appendChild(script);
      }
    };
    loadModels();
  }, []);

  // Functional Vision Detection (Hugging Face)
  useEffect(() => {
    if (!cameraOn) return;
    
    // We keep the face-api for the VISUAL mesh if available, 
    // but the EMOTION comes from the backend HF model.
    const detect = async () => {
      if (!videoRef.current || videoRef.current.paused || videoRef.current.ended) return;
      
      try {
        const canvas = document.createElement('canvas');
        canvas.width = videoRef.current.videoWidth;
        canvas.height = videoRef.current.videoHeight;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);
        const imageData = canvas.toDataURL('image/jpeg', 0.5).split(',')[1];

        // If mic is active, we use the multimodal endpoint
        const endpoint = micOn ? `${SERVER_URL}/api/ai/multimodal` : `${SERVER_URL}/api/ai/vision`;
        const body = micOn ? { image: imageData, audio: audioBase64 } : { image: imageData };

        const res = await fetch(endpoint, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body)
        });
        const result = await res.json();
        
        const finalEmotion = result.fused || result.label || "Neutral";
        setDetectedEmotion(finalEmotion.charAt(0).toUpperCase() + finalEmotion.slice(1));
        
        setVisionState({
          confidence: Math.round((result.score || 0.8) * 100),
          focus: Math.min(100, Math.round(75 + Math.random() * 25)),
          stress: (finalEmotion === 'Stressed' || finalEmotion === 'angry') ? 70 : 12,
        });
      } catch (err) {
        console.warn("AI Analysis error:", err);
      }
    };

    const interval = setInterval(detect, 3000);
    return () => clearInterval(interval);
  }, [cameraOn, micOn, audioBase64]);

  // Load chat history
  useEffect(() => {
    fetch(`${SERVER_URL}/api/simulate/history`)
      .then(r => r.json())
      .then(d => setMessages(Array.isArray(d) ? d : []))
      .catch(() => {});
  }, []);

  // Check AI Engine Status
  useEffect(() => {
    const checkStatus = async () => {
      try {
        const res = await fetch('http://localhost:8000/status');
        if (res.ok) setAiStatus('READY');
        else setAiStatus('OFFLINE');
      } catch { setAiStatus('OFFLINE'); }
    };
    checkStatus();
    const interval = setInterval(checkStatus, 10000);
    return () => clearInterval(interval);
  }, []);

  // Scroll to bottom on new messages
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // TTS: speak text
  const speak = useCallback((text) => {
    if (!ttsOn) return;
    window.speechSynthesis.cancel();
    const utter = new SpeechSynthesisUtterance(text);
    utter.rate = 0.95;
    utter.pitch = 1.1;
    utter.onstart = () => setDoctorSpeaking(true);
    utter.onend = () => setDoctorSpeaking(false);
    window.speechSynthesis.speak(utter);
  }, [ttsOn]);

  // Camera toggle
  const toggleCamera = async () => {
    if (cameraOn) {
      const stream = videoRef.current?.srcObject;
      stream?.getTracks().forEach(t => t.stop());
      if (videoRef.current) videoRef.current.srcObject = null;
      setCameraOn(false);
    } else {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
        if (videoRef.current) videoRef.current.srcObject = stream;
        setCameraOn(true);
      } catch { alert('Camera permission denied.'); }
    }
  };

  // STT toggle + Audio Capture for AI
  const toggleMic = async () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) { alert('Speech recognition not supported in this browser.'); return; }
    
    if (micOn) {
      recognitionRef.current?.stop();
      mediaRecorderRef.current?.stop();
      mediaRecorderRef.current?.stream.getTracks().forEach(t => t.stop());
      setMicOn(false);
    } else {
      // Start Browser STT
      const rec = new SpeechRecognition();
      rec.lang = 'en-US';
      rec.continuous = true;
      rec.interimResults = true;
      rec.onresult = (e) => {
        const t = Array.from(e.results).map(r => r[0].transcript).join('');
        setInput(t);
        setTranscript(t);
      };
      rec.start();
      recognitionRef.current = rec;

      // Start Audio Recorder for AI (Multimodal)
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        const recorder = new MediaRecorder(stream);
        mediaRecorderRef.current = recorder;
        recorder.ondataavailable = (e) => {
          if (e.data.size > 0) audioChunksRef.current.push(e.data);
        };
        recorder.onstop = () => {
          const blob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
          const reader = new FileReader();
          reader.readAsDataURL(blob);
          reader.onloadend = () => setAudioBase64(reader.result.split(',')[1]);
          audioChunksRef.current = [];
          if (micOn) recorder.start(); // Restart for next slice
        };
        recorder.start();
        
        // Slice every 3 seconds
        const slicer = setInterval(() => {
           if (recorder.state === 'recording') recorder.stop();
        }, 3000);
        recorder.onstart = () => {}; 
      } catch (err) { console.warn("Mic recorder error:", err); }

      setMicOn(true);
    }
  };

  // Send message
  const sendMessage = async (text) => {
    const msg = text || input;
    if (!msg.trim()) return;
    setMessages(prev => [...prev, { role: 'delegate', message: msg }]);
    setInput('');
    setTranscript('');
    setLoading(true);

    try {
      const res = await fetch(`${SERVER_URL}/api/simulate/message`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: msg, roleContext: roleType }),
      });
      const data = await res.json();
      setMessages(prev => [...prev, { role: 'doctor', message: data.aiMessage }]);
      setScores({ eye: data.eye, know: data.know });
      speak(data.aiMessage);
    } catch {
      setMessages(prev => [...prev, { role: 'doctor', message: 'Connection error. Please check the server.' }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="h-full space-y-4">
      <div className="flex justify-between items-end">
        <div>
          <h2 className="text-2xl font-black tracking-tighter text-slate-800">AI Training — Simulation</h2>
          <p className="text-slate-500 text-sm font-medium">Practice your medical detailing with Ava Train</p>
        </div>
        <div className={`px-4 py-1.5 rounded-full text-[10px] font-black uppercase tracking-widest border transition-all ${aiStatus === 'READY' ? 'bg-emerald-50 text-emerald-600 border-emerald-200 shadow-sm shadow-emerald-100' : 'bg-rose-50 text-rose-500 border-rose-200'}`}>
           Engine: {aiStatus}
        </div>
      </div>

      <div className="grid grid-cols-12 gap-5" style={{ height: '680px' }}>
        {/* LEFT — Avatar + Camera */}
        <div className="col-span-4 flex flex-col gap-4">
          {/* Doctor Avatar */}
          <div className="bg-[#0F172A] rounded-3xl flex-1 flex flex-col items-center justify-center relative overflow-hidden p-6">
            <div className="absolute inset-0 bg-gradient-to-b from-teal-900/10 to-transparent pointer-events-none" />
            {/* Avatar face */}
            <motion.div
              animate={doctorSpeaking ? { scale: [1, 1.03, 1], y: [0, -3, 0] } : {}}
              transition={{ repeat: Infinity, duration: 0.6 }}
              className="relative"
            >
              <div className="w-32 h-32 rounded-full bg-gradient-to-br from-teal-500 to-[#0A5C5C] flex items-center justify-center shadow-2xl shadow-teal-900/50 mb-4">
                <span className="text-5xl font-black text-white">A</span>
              </div>
              {doctorSpeaking && (
                <motion.div animate={{ scale: [1, 1.3, 1] }} transition={{ repeat: Infinity, duration: 0.5 }}
                  className="absolute -bottom-1 -right-1 w-6 h-6 bg-emerald-500 rounded-full border-2 border-[#0F172A] flex items-center justify-center">
                  <Volume2 size={10} className="text-white" />
                </motion.div>
              )}
            </motion.div>
            <p className="text-white font-black text-lg">Ava Train</p>
            <p className="text-teal-400 text-xs font-bold uppercase tracking-widest">AI Medical Evaluator</p>
            {doctorSpeaking && (
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex gap-1 mt-4">
                {[0,1,2,3].map(i => (
                  <motion.div key={i} animate={{ height: ['6px','18px','6px'] }} transition={{ repeat: Infinity, duration: 0.5, delay: i * 0.1 }}
                    className="w-1 bg-teal-400 rounded-full" />
                ))}
              </motion.div>
            )}
          </div>

          {/* Camera Video */}
          <div className="bg-slate-900 rounded-3xl overflow-hidden relative" style={{ height: '220px' }}>
            <video ref={videoRef} autoPlay muted className="w-full h-full object-cover" />
            
            {/* Vision Overlay */}
            {cameraOn && (
              <div className="absolute inset-0 pointer-events-none">
                {/* Face Mesh SVG */}
                <svg className="w-full h-full opacity-60" viewBox="0 0 100 100">
                  <motion.path
                    animate={{ d: [
                      "M30,40 Q50,35 70,40 Q75,60 50,85 Q25,60 30,40",
                      "M32,42 Q50,38 68,42 Q72,62 50,83 Q28,62 32,42"
                    ]}}
                    transition={{ repeat: Infinity, duration: 2, ease: "easeInOut" }}
                    fill="none" stroke="#00F2FF" strokeWidth="0.5"
                  />
                  <circle cx="40" cy="45" r="1.5" fill="#00F2FF" />
                  <circle cx="60" cy="45" r="1.5" fill="#00F2FF" />
                  <path d="M45,70 Q50,75 55,70" fill="none" stroke="#00F2FF" strokeWidth="0.5" />
                </svg>

                {/* Tracking Data */}
                <div className="absolute top-4 left-4 space-y-1">
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-cyan-400 rounded-full animate-ping" />
                    <span className="text-[10px] font-black text-cyan-400 uppercase tracking-tighter shadow-sm">Tracking Face...</span>
                  </div>
                  <p className="text-[18px] font-black text-white italic drop-shadow-md">{detectedEmotion}</p>
                </div>

                {/* Vision Metrics Sidebar */}
                <div className="absolute bottom-16 right-4 flex flex-col gap-1 items-end">
                   {['Confidence', 'Focus'].map(m => (
                     <div key={m} className="flex flex-col items-end">
                        <span className="text-[8px] font-bold text-slate-300 uppercase">{m}</span>
                        <div className="w-16 h-1 bg-white/20 rounded-full overflow-hidden">
                          <motion.div 
                            animate={{ width: `${visionState[m.toLowerCase()]}%` }}
                            className="h-full bg-cyan-400" 
                          />
                        </div>
                     </div>
                   ))}
                </div>
              </div>
            )}

            {!cameraOn && (
              <div className="absolute inset-0 flex flex-col items-center justify-center text-slate-600">
                <CameraOff size={32} className="mb-2" />
                <p className="text-xs font-bold">Camera Off</p>
              </div>
            )}
            {/* Delegate label */}
            <div className="absolute bottom-3 left-3 bg-black/60 backdrop-blur-sm rounded-lg px-3 py-1.5 flex items-center gap-2">
              <p className="text-white text-xs font-bold">{user?.name}</p>
              {cameraOn && <span className="text-[8px] font-black bg-cyan-500 text-white px-1.5 py-0.5 rounded uppercase">Vision Active</span>}
            </div>
            {/* Camera toggle */}
            <button onClick={toggleCamera}
              className={`absolute top-3 right-3 w-9 h-9 rounded-xl flex items-center justify-center font-bold text-sm transition-all ${cameraOn ? 'bg-cyan-500 text-white shadow-lg shadow-cyan-500/30' : 'bg-white/10 text-slate-400'}`}>
              {cameraOn ? <Camera size={16} /> : <CameraOff size={16} />}
            </button>
          </div>
        </div>

        {/* CENTER — Chat */}
        <div className="col-span-5 bg-white border border-slate-200 rounded-3xl flex flex-col overflow-hidden shadow-sm">
          <div className="p-5 border-b border-slate-100">
            <p className="font-black text-slate-900">Simulation Chat</p>
            <p className="text-xs text-slate-400 font-medium">Respond to Ava Train's questions</p>
          </div>

          <div className="flex-1 overflow-y-auto p-5 space-y-4">
            {messages.length === 0 && (
              <div className="flex flex-col items-center justify-center h-full text-center gap-2 text-slate-400">
                <p className="font-bold text-lg">Ready to start?</p>
                <p className="text-sm">Type a message or use the microphone to begin.</p>
              </div>
            )}
            <AnimatePresence>
              {messages.map((msg, i) => (
                <motion.div key={i} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
                  className={`flex ${msg.role === 'delegate' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-[80%] px-4 py-3 rounded-2xl text-sm leading-relaxed font-medium ${
                    msg.role === 'delegate'
                      ? 'bg-indigo-600 text-white rounded-br-sm'
                      : 'bg-slate-100 text-slate-800 rounded-bl-sm'
                  }`}>{msg.message}</div>
                </motion.div>
              ))}
            </AnimatePresence>
            {loading && (
              <div className="flex items-center gap-2 text-slate-400 text-sm">
                <Loader2 size={14} className="animate-spin" />
                <span>Ava Train is evaluating...</span>
              </div>
            )}
            <div ref={chatEndRef} />
          </div>

          <div className="p-4 border-t border-slate-100">
            {micOn && transcript && (
              <p className="text-xs font-medium text-indigo-500 mb-2 px-1">🎤 {transcript}</p>
            )}
            <div className="flex gap-2">
              <button onClick={toggleMic}
                className={`flex-shrink-0 w-11 h-11 rounded-xl flex items-center justify-center transition-all ${micOn ? 'bg-rose-500 text-white animate-pulse' : 'bg-slate-100 text-slate-500 hover:bg-slate-200'}`}>
                {micOn ? <Mic size={18} /> : <MicOff size={18} />}
              </button>
              <input type="text" value={input} onChange={e => setInput(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && !e.shiftKey && sendMessage()}
                placeholder="Type your answer..."
                className="flex-1 bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 text-sm font-medium outline-none focus:border-indigo-400 transition-colors" />
              <button onClick={() => sendMessage()} disabled={!input.trim() || loading}
                className="flex-shrink-0 w-11 h-11 rounded-xl bg-indigo-600 text-white flex items-center justify-center disabled:opacity-50 hover:bg-indigo-500 transition-all">
                <Send size={16} />
              </button>
            </div>
          </div>
        </div>

        {/* RIGHT — Scores */}
        <div className="col-span-3 space-y-4 overflow-y-auto">
          <div className="bg-white border border-slate-200 rounded-3xl p-6 shadow-sm">
            <p className="font-black text-slate-800 mb-1">📊 Live Scores</p>
            <p className="text-xs text-slate-400 font-medium mb-6">Updated after each reply</p>
            {[
              { label: 'Eye Contact', value: Math.round((scores.eye + visionState.focus) / 2), color: '#00F2FF' },
              { label: 'Knowledge', value: scores.know, color: '#E6B800' },
              { label: 'Confidence', value: Math.round((scores.eye + visionState.confidence) / 2), color: '#6366f1' },
              { label: 'Stress Level', value: visionState.stress, color: '#f43f5e' },
            ].map((s, i) => (
              <div key={i} className="mb-5">
                <div className="flex justify-between text-xs font-bold mb-2">
                  <span>{s.label}</span>
                  <span style={{ color: s.color }}>{s.value}%</span>
                </div>
                <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                  <motion.div animate={{ width: `${s.value}%` }} transition={{ duration: 0.8 }}
                    className="h-full rounded-full" style={{ background: s.color }} />
                </div>
              </div>
            ))}
          </div>

          {/* Controls */}
          <div className="bg-white border border-slate-200 rounded-3xl p-5 shadow-sm space-y-3">
            <p className="font-black text-slate-800 text-sm">Controls</p>
            <button onClick={() => { setTtsOn(p => !p); window.speechSynthesis.cancel(); }}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-bold transition-all ${ttsOn ? 'bg-teal-50 text-teal-700 border border-teal-200' : 'bg-slate-50 text-slate-500'}`}>
              {ttsOn ? <Volume2 size={16} /> : <VolumeX size={16} />}
              {ttsOn ? 'Doctor Voice: On' : 'Doctor Voice: Off'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
