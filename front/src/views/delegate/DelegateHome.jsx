import React from 'react';
import { 
  Play, 
  Map as MapIcon, 
  Box, 
  TrendingUp, 
  Calendar, 
  ChevronRight, 
  Star,
  Clock,
  ArrowRight
} from 'lucide-react';
import { motion } from 'framer-motion';

const recommendedProducts = [
  { id: 1, name: "Cardia-Max Pro", category: "Cardiology", focus: "HFpEF", score: 92 },
  { id: 2, name: "Gluco-Shield Elite", category: "Endocrine", focus: "T2D Management", score: 85 },
  { id: 3, name: "Renal-Active v2", category: "Nephrology", focus: "CKD Stage 3", score: 78 }
];

const stats = [
  { label: 'Overall Readiness', value: '84%', icon: Star, color: 'text-amber-500 bg-amber-50' },
  { label: 'Simulations Done', value: '12/15', icon: Play, color: 'text-brand-teal bg-brand-teal/5' },
  { label: 'Map Efficiency', value: '76.8%', icon: MapIcon, color: 'text-blue-500 bg-blue-50' },
  { label: 'Next Scheduled', value: '14:30', icon: Clock, color: 'text-brand-navy bg-brand-navy/5' },
];

export default function DelegateHome({ user = { name: "Sarah" } }) {
  return (
    <div className="space-y-8 animate-fade-in-up">
      {/* Welcome Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div>
           <div className="flex items-center gap-2 mb-2">
              <span className="text-[10px] font-black bg-brand-teal text-white px-3 py-1 rounded-full uppercase tracking-widest">Medical Sector</span>
              <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Zone: North District</span>
           </div>
           <h1 className="text-4xl font-black text-brand-navy tracking-tighter">Welcome Back, <span className="text-brand-teal">{user.name}</span>.</h1>
           <p className="text-slate-500 font-semibold mt-1">Ready for your daily training and territory optimization?</p>
        </div>
        
        <div className="flex items-center gap-4">
           <button className="px-8 py-4 bg-brand-navy text-white rounded-2xl font-black text-xs uppercase tracking-[0.2em] shadow-2xl shadow-brand-navy/20 flex items-center gap-3 hover:scale-105 transition-all">
              Launch Simulator <Play size={16} fill="currentColor" />
           </button>
        </div>
      </div>

      {/* Stats Summary Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
        {stats.map((s, i) => (
          <motion.div 
            key={i}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
            className="p-6 bg-white rounded-4xl border border-slate-200 shadow-sm"
          >
             <div className={`w-10 h-10 rounded-2xl ${s.color} flex items-center justify-center mb-4`}>
                <s.icon size={18} />
             </div>
             <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">{s.label}</p>
             <h3 className="text-2xl font-black text-brand-navy tracking-tight">{s.value}</h3>
          </motion.div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* BO4: Visit Strategy Map Preview */}
        <div className="lg:col-span-2 space-y-6">
           <div className="flex items-center justify-between">
              <h2 className="text-xl font-extrabold text-brand-navy tracking-tight">Daily Visit Strategy <span className="text-brand-teal">(BO4)</span></h2>
              <button className="text-[10px] font-black text-brand-teal uppercase tracking-widest flex items-center gap-2 hover:underline">
                 Optimize Map <ArrowRight size={12} />
              </button>
           </div>
           
           <div className="relative h-[360px] bg-slate-100 rounded-[48px] border-4 border-white shadow-2xl overflow-hidden group">
              {/* This would be the Leaflet map in a real implementation */}
              <div className="absolute inset-0 bg-[#f9fafb] flex items-center justify-center">
                 <div className="w-full h-full opacity-40 bg-[url('https://maps.googleapis.com/maps/api/staticmap?center=40.7128,-74.0060&zoom=13&size=800x400&sensor=false')] bg-cover bg-center grayscale" />
                 <div className="absolute inset-0 bg-brand-navy/5" />
                 
                 {/* Map Overlays: Destinations */}
                 {[
                    { t: '15%', l: '30%', n: 'Dr. Ross' },
                    { t: '45%', l: '60%', n: 'Clinic Med-X' },
                    { t: '70%', l: '20%', n: 'Apex Pharma' }
                 ].map((p, i) => (
                    <motion.div 
                       key={i}
                       style={{ top: p.t, left: p.l }}
                       initial={{ scale: 0 }}
                       animate={{ scale: 1 }}
                       transition={{ delay: 0.5 + (i * 0.2) }}
                       className="absolute flex flex-col items-center gap-2"
                    >
                       <div className="w-4 h-4 bg-brand-teal rounded-full border-4 border-white shadow-lg ring-4 ring-brand-teal/20" />
                       <div className="px-3 py-1 bg-white rounded-lg shadow-xl text-[9px] font-black text-brand-navy uppercase tracking-tight opacity-0 group-hover:opacity-100 transition-opacity">
                          {p.n}
                       </div>
                    </motion.div>
                 ))}
                 
                 {/* Route Line Simulation */}
                 <svg className="absolute inset-0 w-full h-full pointer-events-none opacity-20">
                    <motion.path 
                       d="M200,100 L350,200 L150,300" 
                       stroke="#4E8C8A" 
                       strokeWidth="4" 
                       strokeDasharray="10 5" 
                       fill="none"
                       initial={{ pathLength: 0 }}
                       animate={{ pathLength: 1 }}
                       transition={{ duration: 2, repeat: Infinity }}
                    />
                 </svg>
              </div>
              
              {/* Itinerary Overlay Card */}
              <div className="absolute bottom-6 left-6 right-6 p-6 glass-card rounded-4xl flex items-center justify-between">
                 <div className="flex items-center gap-4">
                    <div className="w-12 h-12 rounded-2xl bg-brand-navy flex flex-col items-center justify-center text-white">
                       <span className="text-[10px] font-black uppercase text-brand-teal leading-none mb-0.5">MAR</span>
                       <span className="text-xl font-black leading-none">05</span>
                    </div>
                    <div>
                       <p className="text-brand-navy font-extrabold text-sm tracking-tight">Optimal Routing Ready</p>
                       <p className="text-slate-500 font-bold text-xs">3 Visits • Est. Duration 4h 20m</p>
                    </div>
                 </div>
                 <button className="p-4 bg-brand-navy text-white rounded-2xl shadow-xl shadow-brand-navy/20 active:scale-95 transition-all">
                    <MapIcon size={20} />
                 </button>
              </div>
           </div>
        </div>

        {/* BO3: Smart Product Recommender */}
        <div className="space-y-6">
           <div className="flex items-center justify-between">
              <h2 className="text-xl font-extrabold text-brand-navy tracking-tight">AI Recommender <span className="text-brand-teal">(BO3)</span></h2>
           </div>
           
           <div className="space-y-4">
              {recommendedProducts.map((p, i) => (
                 <motion.div 
                    key={i}
                    whileHover={{ x: 6 }}
                    className="p-6 bg-white rounded-4xl border border-slate-200 shadow-sm flex flex-col gap-4 group"
                 >
                    <div className="flex items-start justify-between">
                       <div className="w-12 h-12 rounded-2xl bg-slate-50 flex items-center justify-center text-brand-teal group-hover:bg-brand-teal group-hover:text-white transition-all">
                          <Box size={20} />
                       </div>
                       <div className="text-right">
                          <p className="text-[9px] font-black text-slate-400 uppercase tracking-widest">Priority Index</p>
                          <p className="text-sm font-black text-brand-navy">{p.score}%</p>
                       </div>
                    </div>
                    
                    <div>
                       <h4 className="text-lg font-black text-brand-navy tracking-tight">{p.name}</h4>
                       <p className="text-[10px] font-bold text-brand-teal uppercase tracking-widest">{p.category} • {p.focus}</p>
                    </div>
                    
                    <button className="mt-2 w-full py-3 border-2 border-slate-100 rounded-2xl text-[10px] font-black uppercase tracking-widest text-slate-400 group-hover:border-brand-teal group-hover:text-brand-teal transition-all">
                       Review Detailing Assets
                    </button>
                 </motion.div>
              ))}
              
              <div className="p-8 bg-brand-gradient rounded-4xl text-white text-center flex flex-col items-center gap-4 shadow-xl">
                 <div className="w-12 h-12 rounded-full border-2 border-brand-teal/40 flex items-center justify-center">
                    <TrendingUp size={20} className="text-brand-teal" />
                 </div>
                 <p className="text-xs font-bold leading-relaxed">Your detailing score on <span className="text-brand-teal font-black">SGLT2 inhibitors</span> is increasing. Recommending advanced cardio modules.</p>
                 <button className="w-full py-3 bg-brand-teal text-white rounded-2xl font-black text-[10px] uppercase tracking-widest hover:bg-brand-aqua transition-colors">
                    Start Learning Path
                 </button>
              </div>
           </div>
        </div>
      </div>

      <style jsx>{`
        .glass-card {
          background: rgba(255, 255, 255, 0.7);
          backdrop-filter: blur(16px);
          border: 1px solid rgba(255, 255, 255, 0.2);
        }
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
