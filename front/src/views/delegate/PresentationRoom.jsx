import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  ChevronLeft, 
  PlusSquare, 
  Package, 
  CheckCircle2, 
  Clock, 
  ArrowRight,
  ShieldCheck,
  Star,
  Activity
} from 'lucide-react';
import Avatar3D from '../../components/Avatar3D';
import CameraPanel from '../../components/CameraPanel';
import ChatPanel from '../../components/ChatPanel';

export default function PresentationRoom() {
  const navigate = useNavigate();
  const location = useLocation();
  const query = new URLSearchParams(location.search);
  const subRole = query.get('sub') || 'medical';
  const isMedical = subRole === 'medical';
  
  const practitionerName = isMedical ? 'Dr. Anne-Sophie Martin' : 'Mme Valérie Bernard (Pharmacienne)';
  const productTitle = isMedical ? 'Cardio-Zolpin v4.2' : 'Gamme Hiver Promo 2026';
  
  const [sessionTime, setSessionTime] = useState(0);
  const [isActive, setIsActive] = useState(false);
  const [manifestUrl, setManifestUrl] = useState(null);

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
    <div className="relative h-screen bg-md-surface flex flex-col font-sans overflow-hidden">
      
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
              <div className="w-10 h-10 rounded-xl bg-indigo-500/10 text-indigo-600 flex items-center justify-center">
                 <PlusSquare size={20} />
              </div>
              <div>
                 <p className="text-[10px] font-black uppercase tracking-widest text-indigo-600 leading-none mb-1">Module Pitching BO2</p>
                 <h1 className="text-sm font-black text-md-on-background uppercase tracking-tight">Présentation : {practitionerName}</h1>
              </div>
           </div>
        </div>

        <div className="flex items-center gap-8">
           <div className="flex flex-col items-end">
              <p className="text-[9px] font-black text-md-outline uppercase tracking-widest opacity-60">Durée Session</p>
              <div className="flex items-center gap-2 text-md-on-background font-mono font-bold text-xl">
                 <Clock size={16} className="text-md-primary" />
                 {formatTime(sessionTime)}
              </div>
           </div>
           
           <button 
             onClick={() => navigate('/delegate/results')}
             className="btn-primary !h-12 !px-8 !rounded-pill uppercase text-[11px] font-black tracking-widest shadow-xl shadow-md-primary/20"
           >
              Évaluer la Présentation
           </button>
        </div>
      </div>

      {/* Théâtre de Simulation Principal (3 Colonnes) */}
      <div className="flex-1 flex overflow-hidden">
        
        {/* COL 1 : Avatar du Praticien (40%) */}
        <div className="flex-[0.4] p-8 relative flex flex-col">
           <div className="absolute inset-0 bg-indigo-500/[0.03] -z-10" />
           <Avatar3D 
              type={isMedical ? 'doctor' : 'pharmacist'} 
              manifestUrl={manifestUrl}
            />
           
           {/* Feedback temps réel */}
           <div className="mt-8 grid grid-cols-3 gap-4">
              {[
                { label: 'Empathie', icon: Activity, color: 'text-rose-500', val: 88 },
                { label: 'Posture', icon: Activity, color: 'text-md-primary', val: 92 },
                { label: 'Confiance', icon: Star, color: 'text-amber-500', val: 76 },
              ].map((m, i) => (
                <div key={i} className="md-card !p-5 bg-white/60 backdrop-blur-md border-none flex flex-col gap-3">
                   <div className="flex items-center justify-between">
                      <span className="text-[8px] font-black uppercase text-md-outline tracking-widest leading-none">{m.label}</span>
                      <m.icon size={12} className={m.color} />
                   </div>
                   <div className="h-1 bg-md-surface-container-low rounded-full overflow-hidden">
                      <motion.div initial={{ width: 0 }} animate={{ width: `${m.val}%` }} className={`h-full ${m.color.replace('text', 'bg')}`} />
                   </div>
                </div>
              ))}
           </div>
        </div>

        {/* COL 2 : Caméra du Délégué (30%) */}
        <div className="flex-[0.3] p-8 border-x border-md-outline/10 bg-md-surface-container-low/30 relative flex flex-col">
           <div className="flex-1">
              <CameraPanel label="Délégué" />
           </div>
           
           {/* Suggestion IA */}
           <div className="mt-8 p-6 bg-md-on-background text-white rounded-[28px] shadow-2xl relative overflow-hidden group">
              <div className="absolute top-0 right-0 w-32 h-32 bg-md-primary/20 blur-2xl -z-10" />
              <div className="flex items-center gap-3 mb-4">
                 <ShieldCheck size={16} className="text-md-primary" />
                 <h4 className="text-[10px] font-black uppercase tracking-widest opacity-60">Intelligence Pitching v2</h4>
              </div>
              <p className="text-xs font-bold leading-relaxed opacity-80 uppercase tracking-tighter italic">
                 "Le praticien semble hésitant sur le prix. Préparez votre argumentaire sur le retour sur investissement."
              </p>
           </div>
        </div>

        {/* COL 3 : Panneau Produit & Chat (30%) */}
        <div className="flex-[0.3] p-8 h-full bg-md-surface-container/50 flex flex-col gap-6 overflow-hidden">
           {/* Fiche Produit Compacte */}
           <div className="md-card p-6 bg-white/80 backdrop-blur-md border border-md-primary/10 shadow-xl flex flex-col gap-4 group">
              <div className="flex items-center justify-between">
                 <div className="w-12 h-12 rounded-xl bg-md-primary/10 text-md-primary flex items-center justify-center group-hover:scale-110 transition-transform">
                    <Package size={24} />
                 </div>
                 <div className="text-right">
                    <p className="text-[9px] font-black text-md-primary uppercase tracking-widest opacity-60 mb-0.5">Produit Focus</p>
                    <h4 className="text-base font-black text-md-on-background uppercase">{productTitle}</h4>
                 </div>
              </div>
              <div className="space-y-2">
                 <div className="flex items-center gap-3 text-[10px] font-black text-md-on-surface-variant uppercase tracking-widest italic leading-none">
                    <CheckCircle2 size={12} className="text-emerald-500" /> Évidence Clinique Validée
                 </div>
                 <div className="flex items-center gap-3 text-[10px] font-black text-md-on-surface-variant uppercase tracking-widest italic leading-none">
                    <CheckCircle2 size={12} className="text-emerald-500" /> Gamme Prioritaire DSO1
                 </div>
              </div>
           </div>

           {/* Chat Panel - Prend le reste de la hauteur */}
           <div className="flex-1 min-h-0">
              <ChatPanel onManifest={setManifestUrl} />
           </div>
        </div>

      </div>

      {/* Signature Background Layer */}
      <div className="absolute bottom-0 right-1/2 w-[600px] h-[600px] organic-glow bg-indigo-500/5 rounded-full pointer-events-none -z-10" />
    </div>
  );
}

// Composants internes pour compatibilité
function HeartPulse({ size, className }) {
  return <Activity size={size} className={className} />;
}
