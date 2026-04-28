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
  const [isEvaluating, setIsEvaluating] = useState(false);
  
  // Extraire les ID depuis the routing state
  const delegueId = location.state?.delegueId;
  const productId = location.state?.productId;

  useEffect(() => {
    // Rediriger vers la sélection si la page est chargée sans les props
    if (!delegueId || !productId) {
      navigate('/delegate/training');
    }
  }, [delegueId, productId, navigate]);

  const toggleSession = async () => {
    setIsLoading(true);
    let sessionResult = null;
    try {
      if (!isActive) {
        const response = await fetch("http://localhost:8001/api/training/start", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ 
            delegue_id: Number(delegueId),
            product_id: Number(productId)
          })
        });
        if (response.ok) setIsActive(true);
        else console.error("Failed to start session", await response.text());
      } else {
        setIsActive(false);
        setIsLoading(false);
        setIsEvaluating(true); // Afficher l'overlay pendant l'évaluation IA
        const response = await fetch("http://localhost:8001/api/training/stop", {
          method: "POST"
        });
        setIsEvaluating(false);
        if (response.ok) {
          sessionResult = await response.json();
        } else {
          console.error("Failed to stop session", await response.text());
        }
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
    <div className="relative h-screen bg-md-surface flex flex-col font-sans overflow-hidden">

      {/* Overlay Évaluation IA en cours */}
      {isEvaluating && (
        <div className="fixed inset-0 z-[999] bg-black/80 backdrop-blur-xl flex flex-col items-center justify-center gap-8">
          <div className="flex flex-col items-center gap-6 text-center">
            <div className="relative w-24 h-24">
              <div className="absolute inset-0 rounded-full border-4 border-white/10"/>
              <div className="absolute inset-0 rounded-full border-4 border-t-indigo-400 animate-spin"/>
              <div className="absolute inset-0 flex items-center justify-center text-3xl">🧠</div>
            </div>
            <h2 className="text-2xl font-black text-white tracking-tight">Analyse IA en cours...</h2>
            <p className="text-white/60 text-sm font-medium max-w-sm">
              Le moteur de fact-checking analyse vos allégations produit. Cette opération peut prendre <strong className="text-white">20 à 40 secondes</strong>.
            </p>
            <div className="flex gap-1.5 mt-2">
              {[0,1,2,3,4].map(i => (
                <div key={i} className="w-2 h-2 rounded-full bg-indigo-400 animate-bounce" style={{animationDelay: `${i*0.1}s`}}/>
              ))}
            </div>
          </div>
        </div>
      )}
      
      {/* Barre d'Outils Supérieure Contextuelle */}
      <div className="h-20 border-b border-md-outline/10 bg-white/40 backdrop-blur-3xl flex items-center justify-between px-8 relative z-50">
        <div className="flex items-center gap-6">
           <button 
             onClick={() => navigate('/delegate/training')}
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

            {!isActive ? (
              <button 
                disabled={isLoading}
                onClick={toggleSession}
                className="btn-primary !h-12 !px-8 !rounded-pill uppercase text-[11px] font-black tracking-widest shadow-xl shadow-md-primary/20 bg-green-600 hover:bg-green-700 disabled:opacity-50"
              >
                 {isLoading ? "Démarrage..." : "Démarrer la Session IA"}
              </button>
            ) : (
              <div className="flex items-center gap-3">
                <button 
                  onClick={async () => {
                     setIsLoading(true);
                     try {
                        await fetch("http://localhost:8001/api/training/cancel", { method: "POST" });
                        setIsActive(false);
                        navigate('/delegate/training');
                     } catch (err) {
                        console.error(err);
                     }
                     setIsLoading(false);
                  }}
                  className="!h-12 !px-6 !rounded-pill uppercase text-[10px] font-black tracking-widest text-md-outline bg-white border border-md-outline/20 hover:bg-slate-50 transition-all"
                >
                  Annuler
                </button>
                <button 
                  onClick={async () => {
                     const data = await toggleSession();
                     navigate('/delegate/results', { state: { resultData: data } });
                  }}
                  disabled={isLoading || isEvaluating}
                  className="btn-primary !h-12 !px-8 !rounded-pill uppercase text-[11px] font-black tracking-widest shadow-xl shadow-md-primary/20 bg-red-600 hover:bg-red-700 flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                   Arrêter et Évaluer
                </button>
              </div>
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
           <ChatPanel isActive={isActive} />
        </div>

      </div>

      {/* Signature Background Layer */}
      <div className="absolute bottom-0 right-0 w-[400px] h-[400px] organic-glow bg-md-primary/5 rounded-full pointer-events-none -z-10" />
    </div>
  );
}
