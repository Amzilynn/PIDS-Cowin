import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  PlusSquare, 
  ChevronLeft, 
  Package, 
  Stethoscope,
  Activity,
  CheckCircle2,
  HelpCircle,
  Award,
  ArrowRight,
  Info,
  ShieldCheck,
  User,
  Zap
} from 'lucide-react';
import Avatar3D from '../../components/Avatar3D';
import CameraPanel from '../../components/CameraPanel';
import ChatPanel from '../../components/ChatPanel';

export default function PractitionerView() {
  const navigate = useNavigate();
  const location = useLocation();
  const query = new URLSearchParams(location.search);
  const sub = query.get('sub') || 'doctor';
  
  const isDoctor = sub === 'doctor';
  const practitionerName = isDoctor ? 'Dr. Anne-Sophie Martin' : 'Pharmacie Valérie Bernard';
  const delegateName = isDoctor ? 'Sarah Khalil (Médical)' : 'Youssef Amari (Commercial)';
  const productTitle = isDoctor ? 'Cardio-Zolpin v4.2' : 'Gamme Hiver Promo 2026';

  return (
    <div className="relative h-screen overflow-hidden bg-md-surface flex flex-col font-sans">
      
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
              <div className={`w-10 h-10 rounded-xl ${isDoctor ? 'bg-sky-500/10 text-sky-600' : 'bg-emerald-500/10 text-emerald-600'} flex items-center justify-center`}>
                 {isDoctor ? <Stethoscope size={20} /> : <Activity size={20} />}
              </div>
              <div>
                 <p className="text-[10px] font-black uppercase tracking-widest text-md-primary leading-none mb-1">Espace de Réception DSO2 Intelligence</p>
                 <h1 className="text-sm font-black text-md-on-background uppercase tracking-tight">{practitionerName}</h1>
              </div>
           </div>
        </div>

        <div className="flex items-center gap-6">
           <div className="flex flex-col items-end">
              <p className="text-[9px] font-black text-md-outline uppercase tracking-widest opacity-60">Status Session</p>
              <div className="flex items-center gap-2 text-emerald-500 font-black text-xs uppercase tracking-widest">
                 <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse shadow-[0_0_8px_#10b981]" /> En Direct
              </div>
           </div>
        </div>
      </div>

      {/* Interface Principal : Unified Side-by-Side Layout */}
      <div className="flex-1 grid grid-cols-1 md:grid-cols-[2fr_1.2fr] gap-8 p-8 min-h-0 relative z-10">
        
        {/* COL 1 : Card Unifiée (Avatar + Caméra côte à côte) */}
        <div className="md-card !p-0 overflow-hidden bg-md-surface-container border-none shadow-2xl flex flex-row divide-x divide-md-outline/5">
           {/* Section Avatar */}
           <div className="flex-1 min-h-0 flex flex-col relative">
              <Avatar3D type="delegate" />
           </div>

           {/* Section Caméra */}
           <div className="flex-1 min-h-0 p-6 flex flex-col relative">
              <CameraPanel label="Flux Praticien" />
           </div>
        </div>

        {/* COL 2 : Chat Panel (Slightly expanded) - Custom Container to prevent modal scaling */}
        <div className="bg-md-surface-container/60 rounded-[32px] overflow-hidden relative flex flex-col shadow-2xl border border-md-outline/5">
           <ChatPanel persona={isDoctor ? 'medical' : 'commercial'} />
        </div>
      </div>

      {/* Signature Background Layer */}
      <div className="absolute bottom-0 right-0 w-[500px] h-[500px] organic-glow bg-amber-500/5 rounded-full pointer-events-none -z-10" />
    </div>
  );
}
