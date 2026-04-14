import React, { useState } from 'react';
import { 
  MapContainer, 
  TileLayer, 
  Marker, 
  Popup, 
  Polyline,
  ZoomControl
} from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { 
  Navigation, 
  TrendingUp, 
  Clock, 
  Activity, 
  PlusCircle, 
  MoreVertical, 
  MapPin, 
  ChevronRight,
  ArrowRight,
  AlertCircle,
  Calendar,
  Zap,
  Map as MapIcon,
  Navigation2
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

// Correction des icônes Leaflet par défaut
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

const initialVisits = [
  { id: 1, name: "Dr. Henri Martin", type: "Cardiologue", address: "Avenue Monge, Paris", time: "09:00", priority: "Haute", coords: [48.8415, 2.3500] },
  { id: 2, name: "Pharmacie Bastille", type: "Officine", address: "Place de la Bastille, Paris", time: "11:30", priority: "Moyenne", coords: [48.8530, 2.3690] },
  { id: 3, name: "Dr. Lucie Moreau", type: "Médecin Généraliste", address: "Rue des Écoles, Paris", time: "14:15", priority: "Basse", coords: [48.8480, 2.3480] },
  { id: 4, name: "Clinique du Louvre", type: "Spécialité Ophtalmo", address: "Quai du Louvre, Paris", time: "16:45", priority: "Haute", coords: [48.8580, 2.3380] },
];

export default function VisitPlanner() {
  const [visits, setVisits] = useState(initialVisits);
  const [optimizing, setOptimizing] = useState(false);
  const [showToast, setShowToast] = useState(false);

  const handleOptimize = () => {
    setOptimizing(true);
    // Simulation visuelle de calcul d'itinéraire (BO4 logic)
    setTimeout(() => {
      const optimized = [...visits].sort((a, b) => a.time.localeCompare(b.time));
      setVisits(optimized);
      setOptimizing(false);
      setShowToast(true);
      setTimeout(() => setShowToast(false), 3500);
    }, 2500);
  };

  return (
    <div className="flex flex-col lg:flex-row gap-8 animate-fade-in relative z-10 pb-10 min-h-[800px]">
      
      {/* Background Glows Signature */}
      <div className="fixed top-20 right-10 w-[500px] h-[500px] organic-glow bg-md-primary/10 rounded-full pointer-events-none -z-10" />

      {/* COLONNE GAUCHE: Carte Interactive RÉELLE (60%) */}
      <div className="lg:flex-[0.65] min-h-[700px] flex flex-col bg-white rounded-[48px] p-6 relative overflow-hidden group shadow-2xl border border-md-outline/10">
        <div className="flex-1 w-full relative rounded-[36px] overflow-hidden z-0">
          <MapContainer 
            center={[48.8500, 2.3500]} 
            zoom={14} 
            className="absolute inset-0 w-full h-full grayscale hover:grayscale-0 transition-all duration-700"
            zoomControl={false}
          >
          <TileLayer
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            attribution='&copy; Avalive Intelligence'
          />
          <ZoomControl position="bottomright" />
          
          {visits.map(v => (
            <Marker key={v.id} position={v.coords}>
              <Popup className="md-popup">
                <div className="p-6 font-sans space-y-4 min-w-[200px]">
                   <div className="flex items-center gap-3">
                       <div className={`w-3 h-3 rounded-full shadow-lg ${v.priority === 'Haute' ? 'bg-rose-500 shadow-rose-500/30' : v.priority === 'Moyenne' ? 'bg-amber-500 shadow-amber-500/30' : 'bg-emerald-500 shadow-emerald-500/30'}`} />
                       <span className="text-[10px] font-black uppercase text-md-primary tracking-[0.2em]">{v.priority} Priorité</span>
                   </div>
                   <h4 className="text-lg font-black text-md-on-background tracking-tighter leading-none uppercase">{v.name}</h4>
                   <p className="text-xs font-bold text-md-on-surface-variant opacity-60 uppercase tracking-widest">{v.type}</p>
                   <div className="pt-3 border-t border-md-outline/10 text-[10px] font-black text-md-on-background italic uppercase opacity-40">Visite prévue : {v.time}</div>
                   <button className="w-full btn-primary !h-10 !text-[10px]">Voir Détails</button>
                </div>
              </Popup>
            </Marker>
          ))}

          {/* Route Optimisée (Polyline) */}
          <Polyline 
             positions={visits.map(v => v.coords)} 
             color="var(--color-md-primary)" 
             weight={8} 
             dashArray="15, 20"
             opacity={0.6}
             lineCap="round"
             className="animate-pulse"
          />
        </MapContainer>
        </div>

        {/* Contrôles flottants sur la carte */}
        <div className="absolute top-12 left-12 z-[1000] flex flex-col gap-6">
           <button 
             onClick={handleOptimize}
             disabled={optimizing}
             className="btn-primary !h-16 !px-12 shadow-2xl shadow-md-primary/40 relative overflow-hidden group !rounded-[24px] !text-sm active:scale-95"
           >
              {optimizing ? (
                <div className="flex items-center gap-4">
                   <Activity className="animate-spin" size={24} />
                   <span className="text-[11px] font-black uppercase tracking-[0.3em]">IA en action...</span>
                </div>
              ) : (
                <div className="flex items-center gap-4">
                   <Navigation2 size={24} className="group-hover:rotate-45 transition-transform duration-500" />
                   <span className="text-[11px] font-black uppercase tracking-[0.3em]">Optimiser l'Itinéraire</span>
                </div>
              )}
              {!optimizing && <div className="absolute inset-0 shimmer-anim opacity-15 pointer-events-none" />}
           </button>

           <div className="p-8 bg-white/70 backdrop-blur-3xl rounded-[36px] border border-white/50 shadow-2xl flex flex-col gap-4">
               <p className="text-[10px] font-black text-md-on-background uppercase tracking-[0.4em] mb-2 opacity-50">Priorités du Secteur</p>
               <div className="flex items-center gap-4 group">
                  <div className="w-3.5 h-3.5 rounded-full bg-rose-500 shadow-[0_0_12px_#f43f5e] animate-pulse" />
                  <span className="text-[11px] font-black text-md-on-surface-variant uppercase tracking-widest tracking-tighter">Urgent (Priorité Haute)</span>
               </div>
               <div className="flex items-center gap-4 group">
                  <div className="w-3.5 h-3.5 rounded-full bg-amber-500 shadow-[0_0_12px_#f59e0b]" />
                  <span className="text-[11px] font-black text-md-on-surface-variant uppercase tracking-widest tracking-tighter">Récurrent</span>
               </div>
               <div className="flex items-center gap-4 group">
                  <div className="w-3.5 h-3.5 rounded-full bg-md-primary shadow-[0_0_12px_var(--color-md-primary)]" />
                  <span className="text-[11px] font-black text-md-on-surface-variant uppercase tracking-widest tracking-tighter">Prospection</span>
               </div>
           </div>
        </div>

        <AnimatePresence>
           {showToast && (
             <motion.div 
               initial={{ opacity: 0, y: 100 }}
               animate={{ opacity: 1, y: 0 }}
               exit={{ opacity: 0, y: 100 }}
               className="absolute bottom-12 left-1/2 -translate-x-1/2 z-[1000] px-12 py-6 bg-emerald-500 text-white rounded-pill font-black text-[12px] uppercase tracking-[0.4em] shadow-2xl flex items-center gap-6 border-4 border-white/20 backdrop-blur-md"
             >
                <Zap size={24} fill="currentColor" /> Tournée optimisée en temps réel !
             </motion.div>
           )}
        </AnimatePresence>
      </div>

      {/* COLONNE DROITE: Liste & Planning (35%) */}
      <div className="lg:flex-[0.35] flex flex-col gap-8 h-full min-w-[400px]">
         
         <div className="md-card !p-0 flex flex-col h-full bg-md-surface-container shadow-2xl border-none relative overflow-hidden">
            <div className="p-10 border-b border-md-outline/5 bg-md-surface-container-low/50 relative">
               <div className="absolute top-0 right-0 w-32 h-32 bg-md-primary/5 rounded-full blur-2xl" />
               <div className="flex items-center justify-between relative z-10">
                  <div className="space-y-1">
                     <div className="flex items-center gap-3">
                        <MapIcon size={18} className="text-md-primary" />
                        <h3 className="text-[10px] font-black uppercase text-md-primary tracking-[0.4em]">Planning Terrain</h3>
                     </div>
                     <h4 className="text-3xl font-black text-md-on-background tracking-tighter leading-none uppercase">Tournée du Jour.</h4>
                  </div>
                  <button className="w-14 h-14 bg-md-primary text-white rounded-[20px] flex items-center justify-center shadow-xl active:scale-95 transition-all shadow-md-primary/30">
                     <PlusCircle size={28} />
                  </button>
               </div>
            </div>

            {/* Liste */}
            <div className="p-10 space-y-6 relative z-10">
               {visits.map((v, i) => (
                  <motion.div 
                    layout
                    key={v.id} 
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="p-8 bg-white rounded-[32px] border border-md-outline/5 hover:border-md-primary/30 hover:shadow-2xl transition-all cursor-pointer group flex items-start gap-6 relative overflow-hidden"
                  >
                     <div className="absolute top-0 right-0 w-24 h-24 bg-md-primary/5 rounded-full blur-2xl -translate-y-1/2 translate-x-1/2 opacity-0 group-hover:opacity-100 transition-opacity" />
                     
                     <div className="flex flex-col items-center gap-3">
                        <div className="text-lg font-black text-md-primary font-mono">{v.time}</div>
                        <div className="flex-1 w-1 bg-md-outline/10 group-last:hidden rounded-full" />
                     </div>
                     
                     <div className="flex-1 space-y-3">
                        <div className="flex justify-between items-start">
                           <div className="space-y-1">
                              <h5 className="text-xl font-black text-md-on-background tracking-tighter uppercase leading-none">{v.name}</h5>
                              <p className="text-[10px] font-black text-md-on-surface-variant uppercase tracking-widest opacity-60 leading-none">{v.type}</p>
                           </div>
                           <div className={`px-5 py-2 rounded-pill text-[9px] font-black uppercase tracking-widest shadow-sm ${
                              v.priority === 'Haute' ? 'bg-rose-500 text-white shadow-rose-500/20' : v.priority === 'Moyenne' ? 'bg-amber-500 text-white shadow-amber-500/20' : 'bg-md-primary text-white shadow-md-primary/20'
                           }`}>
                              {v.priority}
                           </div>
                        </div>
                        <div className="flex items-center gap-3 text-xs font-bold text-md-on-surface-variant opacity-60 uppercase italic tracking-tighter">
                           <MapPin size={16} className="text-md-primary" /> {v.address}
                        </div>
                        <div className="flex items-center gap-5 pt-5 opacity-0 group-hover:opacity-100 transition-all border-t border-md-outline/5">
                           <button className="text-[10px] font-black uppercase tracking-widest text-md-primary underline underline-offset-8 decoration-4 decoration-md-primary/20 hover:decoration-md-primary">Détails</button>
                           <button className="text-[10px] font-black uppercase tracking-widest text-rose-500">Modifier</button>
                        </div>
                     </div>
                  </motion.div>
               ))}
            </div>

            {/* Statistiques Matrix */}
            <div className="p-10 border-t border-md-outline/10 bg-md-surface-container-low/50 grid grid-cols-2 gap-6 relative z-10">
               <div className="p-6 bg-md-primary/5 rounded-[28px] border border-md-primary/10 flex flex-col gap-1 transition-transform hover:scale-105">
                   <p className="text-[9px] font-black uppercase text-md-primary tracking-[0.3em]">Optimisation IA</p>
                   <p className="text-3xl font-black text-md-on-background tracking-tighter">94.8%</p>
               </div>
               <div className="p-6 bg-amber-500/5 rounded-[28px] border border-amber-500/10 flex flex-col gap-1 transition-transform hover:scale-105">
                   <p className="text-[9px] font-black uppercase text-amber-600 tracking-[0.3em]">Distance Totale</p>
                   <p className="text-3xl font-black text-md-on-background tracking-tighter">12.4 km</p>
               </div>
               <div className="col-span-2">
                  <button className="w-full btn-primary !h-16 uppercase !tracking-[0.4em] !text-[12px] font-black rounded-pill shadow-2xl relative overflow-hidden group">
                     <span className="relative z-10 flex items-center justify-center gap-4">Lancer la Navigation <ArrowRight size={20} className="group-hover:translate-x-2 transition-transform" /></span>
                     <div className="absolute inset-0 shimmer-anim opacity-20 pointer-events-none" />
                  </button>
               </div>
            </div>
         </div>
      </div>

      <style>{`
        .md-popup .leaflet-popup-content-wrapper {
           border-radius: 36px;
           padding: 0;
           box-shadow: 0 30px 60px rgba(0,0,0,0.15);
           border: 1px solid rgba(0,0,0,0.05);
           background-color: rgba(255,255,255,0.95);
           backdrop-filter: blur(10px);
        }
        .md-popup .leaflet-popup-content {
           margin: 0;
           padding: 0;
        }
        .leaflet-container {
           font-family: inherit !important;
        }
      `}</style>
    </div>
  );
}
