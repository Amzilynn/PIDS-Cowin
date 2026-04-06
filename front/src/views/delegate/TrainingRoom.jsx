import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  ChevronLeft, 
  BrainCircuit, 
  Clock, 
  ShieldCheck, 
  Award,
  Activity,
  Zap
} from 'lucide-react';
import Avatar3D from '../../components/Avatar3D';
import CameraPanel from '../../components/CameraPanel';
import ChatPanel from '../../components/ChatPanel';

export default function TrainingRoom() {
  const navigate = useNavigate();
  const location = useLocation();
  const query = new URLSearchParams(location.search);
  const subRole = query.get('sub') || 'medical';
  const isMedical = subRole === 'medical';
  
  const [sessionTime, setSessionTime] = useState(0);
  const [isActive, setIsActive] = useState(false);

  useEffect(() => {
    let interval;
    if (isActive) {
      interval = setInterval(() => setSessionTime(prev => prev + 1), 1000);
    }
    return () => clearInterval(interval);
  }, [isActive]);

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="relative min-h-full bg-md-surface flex flex-col font-sans">
      
      {/* Barre d'Outils Supérieure Contextuelle */}
      <div className="h-20 border-b border-md-outline/10 bg-white/40 backdrop-blur-3xl flex items-center justify-between px-8 relative z-50">
        <div className="flex items-center gap-6">
           <button 
             onClick={() => navigate(-1)}
             className="w-10 h-10 rounded-xl bg-white shadow-xl flex items-center justify-center text-md-primary hover:scale-110 active:scale-90 transition-all border border-md-outline/5"
           >
              <ChevronLeft size={20} />
           </button>
           
           <div className="flex items-center gap-4">
              <div className="w-10 h-10 rounded-xl bg-md-primary/10 text-md-primary flex items-center justify-center">
                 <BrainCircuit size={20} />
              </div>
              <div>
                 <p className="text-[10px] font-black uppercase tracking-widest text-md-primary leading-none mb-1">Module Simulator BO1</p>
                 <h1 className="text-sm font-black text-md-on-background uppercase tracking-tight">Salle de Formation {isMedical ? 'Médicale' : 'Commerciale'}</h1>
              </div>
           </div>
        </div>

        <div className="flex items-center gap-8">
           {/* Chronomètre Session */}
           <div className="flex flex-col items-end">
              <p className="text-[9px] font-black text-md-outline uppercase tracking-widest opacity-60">Durée Session</p>
              <div className="flex items-center gap-2 text-md-on-background font-mono font-bold text-xl">
                 <Clock size={18} className="text-md-primary" />
                 {formatTime(sessionTime)}
              </div>
           </div>
           
           <button 
             onClick={() => navigate('/delegate/results')}
             className="btn-primary !h-12 !px-8 !rounded-pill uppercase text-[11px] font-black tracking-widest shadow-xl shadow-md-primary/20"
           >
              Évaluer la Session
           </button>
        </div>
      </div>

      {/* Théâtre de Simulation Principal (3 Colonnes) */}
      <div className="flex-1 flex overflow-hidden">
        
        {/* COL 1 : Avatar de Formation (40%) */}
        <div className="flex-[0.4] p-8 relative flex flex-col">
           <div className="absolute inset-0 bg-md-primary/[0.03] -z-10" />
           <Avatar3D type={isMedical ? 'doctor' : 'pharmacist'} />
           
           {/* Overlay Analytics */}
           <div className="mt-8 grid grid-cols-2 gap-6">
              <div className="md-card !p-5 bg-white/60 backdrop-blur-md border-none flex flex-col gap-3">
                 <div className="flex items-center justify-between">
                    <span className="text-[9px] font-black uppercase text-md-outline tracking-widest leading-none">Réactivité IA</span>
                    <Zap size={14} className="text-amber-500" />
                 </div>
                 <div className="h-1.5 bg-md-surface-container-low rounded-full overflow-hidden">
                    <motion.div initial={{ width: 0 }} animate={{ width: '85%' }} className="h-full bg-amber-500" />
                 </div>
              </div>
              <div className="md-card !p-5 bg-white/60 backdrop-blur-md border-none flex flex-col gap-3">
                 <div className="flex items-center justify-between">
                    <span className="text-[9px] font-black uppercase text-md-outline tracking-widest leading-none">Score DSO1</span>
                    <Award size={14} className="text-md-primary" />
                 </div>
                 <div className="h-1.5 bg-md-surface-container-low rounded-full overflow-hidden">
                    <motion.div initial={{ width: 0 }} animate={{ width: '92%' }} className="h-full bg-md-primary" />
                 </div>
              </div>
           </div>
        </div>

        {/* COL 2 : Caméra du Délégué (30%) */}
        <div className="flex-[0.3] p-8 border-x border-md-outline/10 bg-md-surface-container-low/30 relative flex flex-col">
           <div className="flex-1">
              <CameraPanel label="Délégué" />
           </div>
           
           <div className="mt-8 p-6 bg-md-on-background text-white rounded-[28px] shadow-2xl relative overflow-hidden group">
              <div className="absolute top-0 right-0 w-32 h-32 bg-md-primary/20 blur-2xl -z-10" />
              <div className="flex items-center gap-3 mb-4">
                 <ShieldCheck size={16} className="text-md-primary" />
                 <h4 className="text-[10px] font-black uppercase tracking-widest opacity-60">Analyse de Posture</h4>
              </div>
              <p className="text-xs font-bold leading-relaxed opacity-80 uppercase tracking-tighter italic">
                 "Maintenez un contact visuel direct avec l'avatar pour optimiser votre score de communication."
              </p>
           </div>
        </div>

        {/* COL 3 : Panneau de Chat Interactif (30%) */}
        <div className="flex-[0.3] p-8 h-full bg-md-surface-container/50">
           <ChatPanel />
        </div>

      </div>

      {/* Signature Background Layer */}
      <div className="absolute bottom-0 right-0 w-[400px] h-[400px] organic-glow bg-md-primary/5 rounded-full pointer-events-none -z-10" />
    </div>
  );
}
