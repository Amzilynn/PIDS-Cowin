import React, { useState, useEffect } from 'react';
import AvatarPlaceholder from '../../components/AvatarPlaceholder';
import CameraPanel from '../../components/CameraPanel';
import ChatPanel from '../../components/ChatPanel';
import { 
  Dna, 
  Settings, 
  Terminal, 
  AlertCircle, 
  CheckCircle2, 
  ChevronRight,
  ChevronLeft,
  X,
  Target
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export default function TrainingRoom() {
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [cameraActive, setCameraActive] = useState(false);
  const [messages, setMessages] = useState([
    { role: 'ai', text: "Hello Sarah. I'm Ava, your evaluator today. Let's begin the Cardiology Simulation. How do you explain the SGLT2i mechanism to a busy specialist?", timestamp: '14:30' }
  ]);
  const [isTyping, setIsTyping] = useState(false);
  const [simulationState, setSimulationState] = useState('initial'); // 'initial', 'active', 'finished'
  const [currentScenario, setCurrentScenario] = useState("SGLT2i Introduction");

  const handleSendMessage = (text) => {
    // Add user message
    const newMsg = { role: 'user', text, timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) };
    setMessages(prev => [...prev, newMsg]);
    
    // Simulate AI thinking and response
    setIsTyping(true);
    setTimeout(() => {
      setIsTyping(false);
      setIsSpeaking(true);
      const aiReply = { 
        role: 'ai', 
        text: "That clinical reasoning is sound. However, the doctor seems skeptical about the DKA risk profile. How would you handle that objection using the latest 2026 data?",
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages(prev => [...prev, aiReply]);
      
      // Stop speaking animation after 4 seconds
      setTimeout(() => setIsSpeaking(false), 4000);
    }, 2000);
  };

  return (
    <div className="h-[calc(100vh-160px)] flex flex-col gap-6 animate-fade-in-up">
      {/* Simulation Top Bar */}
      <div className="flex items-center justify-between p-6 bg-brand-navy rounded-4xl border border-white/10 shadow-2xl overflow-hidden relative">
        {/* Background glow animation */}
        <div className="absolute inset-0 bg-brand-teal/5 animate-pulse" />
        
        <div className="relative z-10 flex items-center gap-6">
           <button className="p-3 bg-white/5 hover:bg-white/10 rounded-2xl border border-white/10 text-white transition-all active:scale-95">
              <ChevronLeft size={20} />
           </button>
           
           <div className="flex flex-col gap-1">
              <div className="flex items-center gap-2">
                 <h1 className="text-xl font-black text-white tracking-tight leading-none uppercase italic">Simulation <span className="text-brand-teal">Room</span></h1>
                 <span className="text-[10px] font-black bg-brand-teal/10 text-brand-teal px-2 py-0.5 rounded border border-brand-teal/20">LIVE UNIT</span>
              </div>
              <p className="text-[10px] font-black text-white/40 uppercase tracking-[0.2em]">{currentScenario} • Medical Sector v4.1</p>
           </div>
        </div>

        <div className="relative z-10 flex items-center gap-8">
           <div className="hidden md:flex items-center gap-8 border-x border-white/10 px-8">
              <div className="flex flex-col gap-0.5">
                 <span className="text-[9px] font-black text-white/40 uppercase tracking-widest">Signal Latency</span>
                 <span className="text-xs font-black text-emerald-400">12ms - EXCELLENT</span>
              </div>
              <div className="flex flex-col gap-0.5">
                 <span className="text-[9px] font-black text-white/40 uppercase tracking-widest">Active Analysis</span>
                 <span className="text-xs font-black text-brand-teal">Computer Vision: ON</span>
              </div>
           </div>
           
           <div className="flex items-center gap-3">
              <button className="flex items-center gap-2 px-6 py-2.5 bg-brand-teal text-white rounded-xl font-black text-[10px] uppercase tracking-widest shadow-xl shadow-brand-teal/20 transition-all hover:scale-105">
                 <X size={14} /> End Session
              </button>
              <button className="p-2.5 bg-white/5 border border-white/10 text-white rounded-xl hover:bg-white/10 transition-all">
                 <Settings size={18} />
              </button>
           </div>
        </div>
      </div>

      {/* Main Workspace Grid */}
      <div className="flex-1 grid grid-cols-12 gap-6 min-h-0">
        {/* Left Sub-Grid: Avatar & Focus Camera */}
        <div className="col-span-8 flex flex-col gap-6">
           {/* Avatar Simulation Section */}
           <div className="flex-1 min-h-0">
              <AvatarPlaceholder 
                 isSpeaking={isSpeaking} 
                 isLoading={simulationState === 'initial'} 
                 status={simulationState === 'active' ? "ANALYTIC FEED LIVE" : "READY TO START"}
                 name="Ava Train (Audit Mode)"
              />
           </div>

           {/* Metrics & Delegate Camera Panel */}
           <div className="h-[240px] grid grid-cols-2 gap-6">
              <CameraPanel 
                isActive={cameraActive} 
                onToggle={() => setCameraActive(!cameraActive)} 
                userName="Medical Rep: Sarah K."
                className="w-full flex-1"
              />
              
              <div className="bg-white rounded-4xl border border-slate-200 p-8 shadow-sm relative overflow-hidden flex flex-col justify-between group h-full">
                 <div className="flex items-center justify-between relative z-10">
                    <div>
                       <h3 className="text-brand-navy font-extrabold text-sm tracking-tight mb-0.5">CV Performance Analytics</h3>
                       <p className="text-[9px] font-black text-brand-teal uppercase tracking-widest">Real-time Vision Scoring</p>
                    </div>
                    <div className="w-10 h-10 rounded-2xl bg-brand-teal/10 flex items-center justify-center text-brand-teal group-hover:scale-110 transition-transform">
                       <Target size={20} />
                    </div>
                 </div>

                 <div className="space-y-4 relative z-10 w-full flex-1 justify-center flex flex-col">
                    {[
                       { label: 'Eye Contact', score: 92, color: 'brand-teal' },
                       { label: 'Pitch Confidence', score: 78, color: 'brand-navy' },
                       { label: 'Objection Handling', score: 64, color: 'blue-500' }
                    ].map((metric, i) => (
                       <div key={i} className="flex flex-col gap-2">
                          <div className="flex justify-between items-end">
                             <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">{metric.label}</span>
                             <span className={`text-xs font-black text-${metric.color}`}>{metric.score}%</span>
                          </div>
                          <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden">
                             <motion.div 
                                initial={{ width: 0 }}
                                animate={{ width: `${metric.score}%` }}
                                transition={{ duration: 1.5, delay: 0.5 }}
                                className={`h-full bg-${metric.color} rounded-full`}
                             />
                          </div>
                       </div>
                    ))}
                 </div>
                 
                 <div className="absolute right-0 bottom-0 p-4 opacity-5 pointer-events-none group-hover:opacity-10 group-hover:scale-150 transition-all">
                    <Dna size={80} />
                 </div>
              </div>
           </div>
        </div>

        {/* Right Sidebar: Chat & Dialogue Logs */}
        <div className="col-span-4 h-full min-h-0">
           <ChatPanel 
              messages={messages} 
              onSend={handleSendMessage} 
              isTyping={isTyping} 
              title="Simulator Interaction"
           />
        </div>
      </div>

      <style jsx>{`
        @keyframes fade-in-up {
          from { opacity: 0; transform: translateY(20px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .animate-fade-in-up {
          animation: fade-in-up 0.8s ease-out forwards;
        }
      `}</style>
    </div>
  );
}

const ShieldCheck = ({ size, className }) => <AlertCircle size={size} className={className} />; // Fallback
const ShieldCheckIcon = ({ size, className }) => <CheckCircle2 size={size} className={className} />; // Fallback
