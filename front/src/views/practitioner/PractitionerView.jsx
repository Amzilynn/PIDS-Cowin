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
              <div className={`w-10 h-10 rounded-xl ${isDoctor ? 'bg-sky-500/10 text-sky-600' : 'bg-emerald-500/10 text-emerald-600'} flex items-center justify-center`}>
                 {isDoctor ? <Stethoscope size={20} /> : <Activity size={20} />}
              </div>
              <div>
                 <p className="text-[10px] font-black uppercase tracking-widest opacity-40 leading-none mb-1">Espace de Réception Professionnelle</p>
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
           
           <button 
             className="btn-primary !h-12 !px-8 !rounded-pill uppercase text-[11px] font-black tracking-widest shadow-xl shadow-md-primary/20"
           >
              Évaluer la présentation
           </button>
        </div>
      </div>

      {/* Interface de Réception Principal (3 Colonnes) */}
      <div className="flex-1 flex overflow-hidden">
        
        {/* COL 1 : Avatar du Délégué (40%) */}
        <div className="flex-[0.4] p-8 relative flex flex-col">
           <div className="absolute inset-0 bg-md-primary/[0.03] -z-10" />
           {/* On utilise Avatar3D pour simuler le délégué du point de vue du praticien */}
           <Avatar3D type="delegate" />
           
           <div className="mt-8 p-8 bg-white/60 backdrop-blur-md rounded-[32px] border border-md-outline/5 shadow-xl flex items-center justify-between">
              <div>
                 <p className="text-[10px] font-black text-md-on-background uppercase tracking-widest opacity-40 leading-none mb-2 underline underline-offset-4 decoration-md-primary">Identité Interlocuteur</p>
                 <h3 className="text-2xl font-black text-md-on-background tracking-tighter uppercase leading-none">{delegateName.split('(')[0]}</h3>
                 <p className="text-[11px] font-black text-md-primary uppercase mt-1 tracking-widest">{delegateName.split('(')[1].replace(')', '')}</p>
              </div>
              <div className="w-16 h-16 rounded-[48px] bg-md-primary/10 text-md-primary flex items-center justify-center shadow-lg border border-md-primary/10">
                 <ShieldCheck size={32} />
              </div>
           </div>
        </div>

        {/* COL 2 : Caméra du Praticien (30%) */}
        <div className="flex-[0.3] p-8 border-x border-md-outline/10 bg-md-surface-container-low/30 relative flex flex-col">
           <div className="flex-1">
              <CameraPanel label="Praticien" />
           </div>
           
           <div className="mt-8 p-10 bg-md-on-background text-white rounded-[36px] shadow-2xl relative overflow-hidden group">
              <div className="absolute top-0 right-0 w-32 h-32 bg-md-primary/20 blur-2xl -z-10" />
              <div className="flex items-center gap-4 mb-6">
                 <Info size={18} className="text-md-primary animate-pulse" />
                 <h4 className="text-[10px] font-black uppercase tracking-widest opacity-60">Mémo Praticien</h4>
              </div>
              <p className="text-sm font-bold leading-relaxed opacity-80 uppercase tracking-tighter italic">
                 "Ce délégué a un rang DSO Élite. Ses recommandations sont prioritaires pour votre établissement."
              </p>
           </div>
        </div>

        {/* COL 3 : Fiche Produit & Feedback (30%) */}
        <div className="flex-[0.3] p-8 h-full bg-md-surface-container/50 flex flex-col gap-6 overflow-hidden">
           
           {/* Fiche Produit Interactive */}
           <div className="md-card p-10 bg-md-on-background text-white flex flex-col gap-8 relative overflow-hidden group shadow-2xl border border-white/5">
              <div className="absolute top-0 right-0 w-48 h-48 bg-md-primary/20 blur-[80px] -z-10 group-hover:scale-150 transition-all duration-1000" />
              <div className="flex items-center justify-between relative z-10">
                 <div className="w-14 h-14 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center group-hover:scale-110 transition-transform shadow-2xl">
                    <Package size={28} className="text-md-primary" />
                 </div>
                 <div className="text-right">
                    <p className="text-[10px] font-black uppercase tracking-widest opacity-40 mb-1">Documentation Active</p>
                    <h4 className="text-2xl font-black tracking-tighter italic leading-none text-md-primary uppercase">{productTitle}</h4>
                 </div>
              </div>
              
              <div className="relative z-10 space-y-4">
                 <div className="flex items-center gap-4 text-xs font-black uppercase tracking-widest opacity-60">
                    <CheckCircle2 size={16} className="text-emerald-500" /> Indication : Traitement 1ère Intention
                 </div>
                 <button className="w-full h-14 bg-white/5 hover:bg-md-primary hover:text-white rounded-2xl border border-white/10 transition-all font-black text-[10px] uppercase tracking-widest mt-4 group shadow-lg">
                    Télécharger la fiche technique (PDF)
                    <Zap size={14} className="inline ml-3 group-hover:fill-current" />
                 </button>
              </div>
           </div>

           {/* Feedback temps réel / Chat */}
           <div className="flex-1 min-h-0">
              <ChatPanel />
           </div>

           {/* Actions Finales */}
           <div className="grid grid-cols-2 gap-4">
              <button className="btn-tonal !h-14 font-black uppercase text-[10px] tracking-widest !rounded-2xl border border-md-outline/10">
                 <HelpCircle size={18} className="mr-2" /> Question
              </button>
              <button className="btn-tonal !h-14 font-black uppercase text-[10px] tracking-widest !rounded-2xl border border-md-outline/10">
                 <Award size={18} className="mr-2" /> Valider
              </button>
           </div>
        </div>

      </div>

      {/* Signature Background Layer */}
      <div className="absolute bottom-0 right-0 w-[500px] h-[500px] organic-glow bg-amber-500/5 rounded-full pointer-events-none -z-10" />
    </div>
  );
}
