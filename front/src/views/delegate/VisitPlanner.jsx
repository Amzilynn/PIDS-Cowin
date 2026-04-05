import React, { useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { 
  Calendar, 
  Map as MapIcon, 
  Clock, 
  Navigation, 
  Search, 
  Filter, 
  CheckCircle2, 
  MoreHorizontal,
  ChevronRight,
  TrendingUp,
  Hospital
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

// Mock visit data
const visits = [
  { id: 1, name: "Dr. Sarah Khalil", position: [36.8065, 10.1815], time: "09:00", type: "Cardio", status: "Completed", address: "Central Square Hospital" },
  { id: 2, name: "Tunis Med Clinic", position: [36.8200, 10.1700], time: "11:30", type: "Pharma", status: "Optimal", address: "North District Med-Park" },
  { id: 3, name: "Clinique La Marsa", position: [36.8850, 10.3300], time: "14:15", type: "General", status: "Priority", address: "Coastal Road, La Marsa" },
  { id: 4, name: "Pharmacy Elite", position: [36.8400, 10.2000], time: "16:45", type: "Retail", status: "Scheduled", address: "Olympic City center" },
];

const polylineRoute = visits.map(v => v.position);

export default function VisitPlanner() {
  const [selectedVisit, setSelectedVisit] = useState(visits[1]);

  return (
    <div className="flex flex-col h-[calc(100vh-160px)] gap-6 animate-fade-in-up">
      {/* Header Info */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div>
           <div className="flex items-center gap-2 mb-2">
              <span className="text-[10px] font-black bg-brand-teal text-white px-3 py-1 rounded-full uppercase tracking-widest">BO4 Unit</span>
              <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Territory Optimization: Active</span>
           </div>
           <h1 className="text-4xl font-black text-brand-navy tracking-tighter">Visit Strategy <span className="text-brand-teal">Optimizer</span>.</h1>
           <p className="text-slate-500 font-semibold mt-1">Smart routing & territory prioritization based on delegate profile.</p>
        </div>
        
        <div className="flex items-center gap-3">
           <button className="flex items-center gap-2 px-6 py-2.5 bg-brand-navy text-white rounded-xl font-bold text-xs uppercase tracking-widest shadow-xl shadow-brand-navy/20 hover:scale-105 transition-all">
              <TrendingUp size={14} /> Calculate ROI Path
           </button>
           <button className="p-2.5 bg-white border border-slate-200 rounded-xl text-slate-400 hover:text-brand-navy transition-all">
              <Calendar size={18} />
           </button>
        </div>
      </div>

      <div className="flex-1 grid grid-cols-12 gap-6 min-h-0">
        {/* Left: Schedule & Search */}
        <div className="col-span-12 lg:col-span-4 flex flex-col gap-6 overflow-hidden">
           <div className="p-8 bg-white rounded-4xl border border-slate-200 shadow-sm flex flex-col gap-6 h-full overflow-hidden">
              <div className="flex items-center justify-between">
                 <h3 className="text-lg font-extrabold text-brand-navy tracking-tight">Daily Itinerary</h3>
                 <span className="text-[9px] font-black text-brand-teal uppercase tracking-widest bg-brand-teal/5 px-2 py-1 rounded border border-brand-teal/10">March 05, 2026</span>
              </div>

              <div className="relative">
                 <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" size={16} />
                 <input type="text" placeholder="Search facilities..." className="w-full pl-12 pr-6 py-3 bg-slate-50 border border-slate-100 rounded-2xl text-xs font-bold outline-none focus:border-brand-teal transition-all" />
              </div>

              <div className="flex-1 overflow-y-auto space-y-3 scrollbar-none pr-1">
                 {visits.map((v) => (
                    <button 
                       key={v.id}
                       onClick={() => setSelectedVisit(v)}
                       className={`w-full p-5 rounded-3xl border-2 transition-all text-left flex items-start justify-between group ${
                          selectedVisit.id === v.id 
                             ? 'bg-brand-navy border-brand-navy shadow-xl shadow-brand-navy/20' 
                             : 'bg-white border-transparent hover:border-slate-200 hover:bg-slate-50'
                       }`}
                    >
                       <div className="flex items-start gap-3">
                          <div className={`w-10 h-10 rounded-2xl flex items-center justify-center transition-colors ${
                             selectedVisit.id === v.id ? 'bg-brand-teal text-white' : 'bg-slate-50 text-slate-400 group-hover:bg-white'
                          }`}>
                            <Hospital size={18} />
                          </div>
                          <div>
                             <p className={`text-sm font-extrabold tracking-tight ${selectedVisit.id === v.id ? 'text-white' : 'text-brand-navy'}`}>{v.name}</p>
                             <p className={`text-[10px] font-bold ${selectedVisit.id === v.id ? 'text-white/40' : 'text-slate-400 uppercase tracking-widest'}`}>{v.address}</p>
                          </div>
                       </div>
                       
                       <div className="flex flex-col items-end gap-1">
                          <span className={`text-[10px] font-black uppercase tracking-widest ${selectedVisit.id === v.id ? 'text-brand-teal' : 'text-slate-400'}`}>{v.time}</span>
                          <div className={`px-2 py-0.5 rounded text-[8px] font-black uppercase transition-colors ${
                             v.status === 'Completed' ? 'bg-emerald-500/10 text-emerald-500' : 
                             v.status === 'Optimal' ? 'bg-brand-teal/10 text-brand-teal' : 
                             v.status === 'Priority' ? 'bg-rose-500/10 text-rose-500' : 'bg-slate-100 text-slate-400'
                          }`}>
                             {v.status}
                          </div>
                       </div>
                    </button>
                 ))}
              </div>
              
              <button className="w-full py-4 bg-brand-teal text-white rounded-2xl font-black text-[10px] uppercase tracking-widest shadow-xl shadow-brand-teal/20 active:scale-95 transition-all">
                 <Navigation size={14} className="inline-block mr-2" /> Start Optimal Path
              </button>
           </div>
        </div>

        {/* Right: Leaflet Interactive Map */}
        <div className="col-span-12 lg:col-span-8 bg-slate-100 rounded-[48px] border-4 border-white shadow-2xl relative overflow-hidden group">
           <MapContainer center={[36.8065, 10.1815]} zoom={12} scrollWheelZoom={false} className="w-full h-full z-10 transition-all duration-700">
             <TileLayer
               url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
               attribution='&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors'
             />
             {visits.map((v) => (
                <Marker key={v.id} position={v.position}>
                  <Popup>
                    <div className="p-1">
                       <p className="font-extrabold text-brand-navy mb-0.5">{v.name}</p>
                       <p className="text-[10px] font-black text-brand-teal uppercase tracking-widest">{v.address}</p>
                    </div>
                  </Popup>
                </Marker>
             ))}
             <Polyline positions={polylineRoute} color="#4E8C8A" weight={4} dashArray="10, 10" opacity={0.6} />
           </MapContainer>
           
           {/* Map UI Overlays */}
           <div className="absolute top-8 left-8 right-8 z-20 flex justify-between pointer-events-none">
              <div className="flex flex-col gap-2 pointer-events-auto">
                 <div className="px-4 py-2 bg-white/70 backdrop-blur-md rounded-2xl border border-white/20 shadow-xl inline-flex items-center gap-3">
                    <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse" />
                    <span className="text-[10px] font-black text-brand-navy uppercase tracking-widest">Delegate Active Trace</span>
                 </div>
              </div>
              
              <div className="flex items-center gap-2 pointer-events-auto">
                 <button className="p-4 bg-white/70 backdrop-blur-md rounded-2xl border border-white/20 shadow-xl text-brand-navy hover:bg-white transition-all">
                    <MapIcon size={18} />
                 </button>
                 <button className="p-4 bg-white/70 backdrop-blur-md rounded-2xl border border-white/20 shadow-xl text-brand-navy hover:bg-white transition-all">
                    <Filter size={18} />
                 </button>
              </div>
           </div>
           
           <div className="absolute bottom-8 left-1/2 -translate-x-1/2 z-20 w-full px-8 pointer-events-none">
              <motion.div 
                 initial={{ y: 20, opacity: 0 }}
                 animate={{ y: 0, opacity: 1 }}
                 className="p-8 bg-brand-navy/90 backdrop-blur-xl border border-white/10 rounded-[32px] shadow-2xl flex items-center justify-between text-white pointer-events-auto"
              >
                 <div className="flex items-center gap-6">
                    <div className="w-16 h-16 rounded-3xl bg-white/5 border border-white/10 flex items-center justify-center text-brand-teal">
                       <Navigation size={28} />
                    </div>
                    <div>
                       <p className="text-xl font-black tracking-tight leading-none mb-1 text-brand-teal">Current Route Ready.</p>
                       <p className="text-[10px] font-black text-white/40 uppercase tracking-[0.2em]">Next Facility: {selectedVisit.name}</p>
                    </div>
                 </div>
                 
                 <div className="flex items-center gap-3">
                    <div className="text-right sr-only md:not-sr-only">
                       <p className="text-[10px] font-black uppercase tracking-widest text-white/40">Transit Est.</p>
                       <p className="text-lg font-black leading-none">14 min</p>
                    </div>
                    <button className="px-8 py-4 bg-white text-brand-navy rounded-2xl font-black text-[10px] uppercase tracking-widest hover:scale-105 active:scale-95 transition-all shadow-xl shadow-white/10">
                       Open in Navigation
                    </button>
                 </div>
              </motion.div>
           </div>
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
