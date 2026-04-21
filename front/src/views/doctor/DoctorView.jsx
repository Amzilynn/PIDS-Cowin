import React, { useState } from 'react';
import Avatar3D from '../../components/Avatar3D';
import CameraPanel from '../../components/CameraPanel';
import ChatPanel from '../../components/ChatPanel';
import { 
  Stethoscope, 
  Settings, 
  MoreHorizontal, 
  AlertCircle, 
  CheckCircle2, 
  MessageSquare,
  Sparkles,
  LogOut,
  ChevronRight,
  Package,
  Award
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export default function DoctorView() {
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [speechPulse, setSpeechPulse] = useState(0);
  const [cameraActive, setCameraActive] = useState(false);
  const [currentManifestUrl, setCurrentManifestUrl] = useState(null);

  const handleVideoUrl = (url, manifest) => {
    setCurrentManifestUrl(manifest);
  };

  return (
    <div className="h-[calc(100vh-160px)] flex flex-col gap-6 animate-fade-in-up">
      {/* Presentation Top Bar */}
      <div className="flex items-center justify-between p-6 bg-brand-navy rounded-[40px] border border-white/10 shadow-2xl relative overflow-hidden">
        {/* Decorative elements */}
        <div className="absolute inset-0 bg-brand-teal/5 animate-pulse" />
        
        <div className="relative z-10 flex items-center gap-6">
           <div className="w-12 h-12 bg-white/5 border border-white/10 rounded-2xl flex items-center justify-center text-brand-teal shadow-xl">
              <Stethoscope size={24} />
           </div>
           
           <div className="flex flex-col gap-1">
              <div className="flex items-center gap-2">
                 <h1 className="text-xl font-black text-white tracking-tight leading-none uppercase italic">Presentation <span className="text-brand-teal">Receiver</span></h1>
                 <span className="text-[10px] font-black bg-brand-teal/10 text-brand-teal px-2 py-0.5 rounded border border-brand-teal/20 uppercase tracking-widest">Guest: Dr. Khalil</span>
              </div>
              <p className="text-[10px] font-black text-white/40 uppercase tracking-[0.2em]">Product Detailing • Cardia-Max Pro • Cardiology Unit</p>
           </div>
        </div>

        <div className="relative z-10 flex items-center gap-4">
           <div className="hidden lg:flex items-center gap-8 border-x border-white/10 px-8">
              <div className="flex items-center gap-3">
                 <div className="w-2 h-2 bg-brand-teal rounded-full animate-ping" />
                 <span className="text-xs font-black text-white tracking-widest">REPRESENTATIVE IS ACTIVE</span>
              </div>
           </div>
           
           <div className="flex items-center gap-3">
              <button className="flex items-center gap-2 px-6 py-2.5 bg-brand-navy text-white rounded-xl font-black text-[10px] uppercase tracking-widest shadow-xl shadow-brand-navy/20 border border-white/10 transition-all hover:bg-white/5">
                 <LogOut size={14} /> Exit Receiver
              </button>
           </div>
        </div>
      </div>

      {/* Main Workspace Grid */}
      <div className="flex-1 grid grid-cols-12 gap-6 min-h-0">
        {/* Left Sub-Grid: Representative Avatar & Info */}
        <div className="col-span-12 lg:col-span-8 flex flex-col gap-6">
           {/* Rep Avatar Section */}
           <div className="flex-1 min-h-0 relative">
              <Avatar3D 
                 isSpeaking={isSpeaking} 
                 speechPulse={speechPulse}
                 type="doctor"
                 status="SCIENTIFIC DETAILING ACTIVE"
                 name="Delegate: Sarah K."
                 manifestUrl={currentManifestUrl}
              />
              
              {/* Product Info Inset */}
              <div className="absolute top-8 left-8 p-4 bg-brand-navy/40 backdrop-blur-xl rounded-3xl border border-white/10 flex items-center gap-4 z-20">
                 <div className="w-10 h-10 rounded-2xl bg-brand-teal flex items-center justify-center text-white shadow-xl shadow-brand-teal/20">
                    <Package size={20} />
                 </div>
                 <div>
                    <p className="text-[9px] font-black text-brand-teal uppercase tracking-widest mb-0.5 leading-none">Focus Product</p>
                    <p className="text-sm font-black text-white leading-none">Cardia-Max Pro v3</p>
                 </div>
              </div>
           </div>

           {/* Feedback & Doctor Camera Section */}
           <div className="h-[200px] grid grid-cols-2 gap-6">
              <CameraPanel 
                isActive={cameraActive} 
                onToggle={() => setCameraActive(!cameraActive)} 
                userName="Doctor Receiver: Dr. Khalil"
                className="w-full h-full"
              />
              
              <div className="p-8 bg-white rounded-4xl border border-slate-200 shadow-sm flex flex-col justify-between group overflow-hidden relative">
                 <div className="relative z-10 flex items-center justify-between">
                    <div>
                        <h3 className="text-brand-navy font-extrabold text-sm tracking-tight mb-0.5 leading-none">Clinical Feedback</h3>
                        <p className="text-[9px] font-black text-brand-teal uppercase tracking-widest">Rate Interest Level</p>
                    </div>
                    <div className="w-10 h-10 rounded-2xl bg-slate-50 flex items-center justify-center text-slate-400 group-hover:text-brand-teal transition-all">
                       <Award size={20} />
                    </div>
                 </div>

                 <div className="relative z-10 flex gap-2 w-full mt-4">
                    {[1, 2, 3, 4, 5].map((s) => (
                       <button key={s} className="flex-1 py-4.5 bg-slate-50 border-2 border-slate-100 rounded-2xl text-slate-300 hover:border-brand-teal hover:text-brand-teal hover:bg-white transition-all text-sm font-black">
                         {s}
                       </button>
                    ))}
                 </div>
                 
                 <div className="relative z-10 mt-auto">
                    <button className="w-full py-3 bg-brand-navy text-white rounded-2xl font-black text-[10px] uppercase tracking-widest shadow-xl shadow-brand-navy/20 hover:scale-105 transition-all">
                       Submit Clinical Interest
                    </button>
                 </div>
                 
                 <div className="absolute right-0 bottom-0 p-8 opacity-5 grayscale pointer-events-none group-hover:scale-110 transition-transform">
                    <Sparkles size={120} />
                 </div>
              </div>
           </div>
        </div>

        {/* Right Sidebar: Chat Interaction */}
        <div className="col-span-12 lg:col-span-4 h-full min-h-0">
           <ChatPanel 
              persona="medical"
              onSpeakingState={setIsSpeaking}
              onVolumeSync={setSpeechPulse} 
              onVideoResponse={handleVideoUrl}
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
