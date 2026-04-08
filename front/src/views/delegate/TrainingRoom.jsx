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
  const [isLoading, setIsLoading] = useState(false);
  
  const [delegues, setDelegues] = useState([]);
  const [selectedDelegue, setSelectedDelegue] = useState("");

  useEffect(() => {
    fetch("http://localhost:8001/api/training/delegues")
      .then(res => res.json())
      .then(data => {
        setDelegues(data);
        if (data.length > 0) setSelectedDelegue(data[0].id);
      })
      .catch(console.error);
  }, []);

  const toggleSession = async () => {
    setIsLoading(true);
    let sessionResult = null;
    try {
      if (!isActive) {
        const response = await fetch("http://localhost:8001/api/training/start", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ delegue_id: Number(selectedDelegue) })
        });
        if (response.ok) setIsActive(true);
        else console.error("Failed to start session", await response.text());
      } else {
        const response = await fetch("http://localhost:8001/api/training/stop", {
          method: "POST"
        });
        if (response.ok) {
          sessionResult = await response.json();
          setIsActive(false);
        }
        else console.error("Failed to stop session", await response.text());
      }
    } catch (error) {
      console.error("API error", error);
    }
    setIsLoading(false);
    return sessionResult;
  };

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
                 <p className="text-[10px] font-black uppercase tracking-widest text-md-primary leading-none mb-1">Module Formation</p>
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
           
           {/* Délégué & Start */}
           {!isActive && (
              <select 
                value={selectedDelegue} 
                onChange={(e) => setSelectedDelegue(e.target.value)}
                className="h-12 px-4 rounded-xl border-none bg-md-surface outline-none text-sm font-bold mt-1 shadow-inner text-md-on-surface"
              >
                {delegues.map(d => (
                  <option key={d.id} value={d.id}>{d.nom} - Niveau {d.level}</option>
                ))}
              </select>
           )}

           {!isActive ? (
             <button 
               disabled={isLoading}
               onClick={toggleSession}
               className="btn-primary !h-12 !px-8 !rounded-pill uppercase text-[11px] font-black tracking-widest shadow-xl shadow-md-primary/20 bg-green-600 hover:bg-green-700 disabled:opacity-50"
             >
                {isLoading ? "Démarrage..." : "Démarrer la Session IA"}
             </button>
           ) : (
             <button 
               onClick={async () => {
                  const data = await toggleSession();
                  navigate('/delegate/results', { state: { resultData: data } });
               }}
               className="btn-primary !h-12 !px-8 !rounded-pill uppercase text-[11px] font-black tracking-widest shadow-xl shadow-md-primary/20 bg-red-600 hover:bg-red-700 flex items-center gap-2"
             >
                {isLoading ? "Veuillez patienter..." : "Arrêter et Évaluer"}
             </button>
           )}
        </div>
      </div>

      {/* Théâtre de Simulation Principal (2 Colonnes Alignées) */}
      <div className="flex-1 grid grid-cols-1 md:grid-cols-2 gap-8 p-8 overflow-hidden">
        
        {/* COL 1 : Caméra du Délégué */}
        <div className="md-card !p-0 overflow-hidden bg-md-surface-container-low/30 relative flex flex-col shadow-xl border-none">
           <div className="flex-1 flex flex-col p-4 w-full h-full">
              <CameraPanel label="Flux Délégué" isActive={isActive} onToggle={toggleSession} hideControls={true} />
           </div>
        </div>

        {/* COL 2 : Panneau de Chat Interactif */}
        <div className="md-card !p-0 overflow-hidden bg-md-surface-container/50 relative flex flex-col shadow-xl border-none w-full h-full">
           <ChatPanel />
        </div>

      </div>

      {/* Signature Background Layer */}
      <div className="absolute bottom-0 right-0 w-[400px] h-[400px] organic-glow bg-md-primary/5 rounded-full pointer-events-none -z-10" />
    </div>
  );
}
