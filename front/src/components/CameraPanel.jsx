import React from 'react';
import { Camera, CameraOff, Video } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export default function CameraPanel({ 
  isActive = false, 
  onToggle = () => {}, 
  userName = "Medical Delegate",
  className = ""
}) {
  return (
    <div className={`relative bg-brand-slate rounded-3xl overflow-hidden border-2 transition-all duration-500 ${isActive ? 'border-brand-teal ring-4 ring-brand-teal/20' : 'border-white/10'} ${className}`}>
      {/* Black screen placeholder */}
      <div className="absolute inset-0 bg-black flex items-center justify-center">
        {!isActive ? (
          <div className="flex flex-col items-center gap-4 text-white/20">
            <CameraOff size={48} strokeWidth={1.5} />
            <p className="text-[10px] font-black uppercase tracking-[0.3em]">Camera Disabled</p>
          </div>
        ) : (
          <div className="w-full h-full bg-slate-900 flex items-center justify-center relative overflow-hidden">
             {/* Simulated video scanning overlay */}
             <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent pointer-events-none" />
             <div className="absolute top-0 left-0 w-full h-1 bg-brand-teal/40 blur-sm animate-[scan_3s_linear_infinite]" />
             
             {/* Silhouette for Delegate Placeholder */}
             <div className="w-24 h-24 rounded-full bg-white/5 border border-white/10 flex items-center justify-center">
                <Video size={40} className="text-white/20" />
             </div>
          </div>
        )}
      </div>

      {/* Overlay Status */}
      <div className="absolute top-4 left-4 flex items-center gap-2 group">
        <div className={`w-2 h-2 rounded-full transition-all duration-500 ${isActive ? 'bg-emerald-500 shadow-[0_0_10px_#10b981]' : 'bg-rose-500 shadow-[0_0_10px_#f43f5e]'}`} />
        <span className="text-[10px] font-black text-white bg-black/40 blur-border backdrop-blur-md px-3 py-1.5 rounded-full uppercase tracking-widest border border-white/10">
          Feed: {isActive ? 'Live' : 'Offline'}
        </span>
      </div>

      {/* Control Button */}
      <button 
        onClick={onToggle}
        className={`absolute top-4 right-4 p-3 rounded-2xl border backdrop-blur-md transition-all active:scale-90 ${isActive ? 'bg-brand-teal text-white border-brand-teal' : 'bg-white/5 text-white border-white/10 dark-hover hover:bg-white/10'}`}
      >
        {isActive ? <Camera size={18} /> : <CameraOff size={18} />}
      </button>

      {/* Delegate Info */}
      <div className="absolute bottom-4 left-4 right-4 flex items-center justify-between">
        <div className="px-4 py-2 bg-black/40 backdrop-blur-md rounded-2xl border border-white/10">
           <p className="text-white font-extrabold text-[11px] uppercase tracking-tight">{userName}</p>
        </div>
        
        {isActive && (
           <div className="flex items-center gap-1 text-emerald-400 font-black text-[9px] uppercase tracking-widest animate-pulse">
              <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full" /> Connected
           </div>
        )}
      </div>

      <style jsx>{`
        @keyframes scan {
          0% { top: 0; }
          100% { top: 100%; }
        }
      `}</style>
    </div>
  );
}
