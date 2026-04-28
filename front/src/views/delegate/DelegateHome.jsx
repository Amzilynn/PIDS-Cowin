import React, { useState, useEffect } from 'react';
import { 
  BrainCircuit, 
  PackageCheck, 
  Map as MapIcon,
  TrendingUp,
  Award,
  Calendar,
  ArrowRight,
  ChevronRight,
  Zap,
  Target,
  User,
  Mail,
  Star,
  Activity,
  Smile,
  ShieldCheck,
  ZapOff,
  Database
} from 'lucide-react';
import { motion } from 'framer-motion';
import { AreaChart, Area, ResponsiveContainer, XAxis, Tooltip, CartesianGrid, YAxis } from 'recharts';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8001';

const METRICS = [
  { id: 'score', label: 'Global', icon: TrendingUp, color: 'var(--color-md-primary)' },
  { id: 'confidence', label: 'Confiance', icon: ShieldCheck, color: '#10b981' }, // Emerald
  { id: 'engagement', label: 'Engagement', icon: Zap, color: '#f59e0b' },   // Amber
  { id: 'product_knowledge', label: 'NLP / Produit', icon: Database, color: '#6366f1' }, // Indigo
];

export default function DelegateHome({ subRole = 'medical' }) {
  const navigate = useNavigate();
  const location = useLocation();
  const { user } = useAuth();

  const isMedical = subRole === 'medical';
  const roleTitle = isMedical ? 'Délégué Médical' : 'Délégué Commercial';

  // Infos et Historique
  const [delegueInfo, setDelegueInfo] = useState(null);
  const [historyData, setHistoryData] = useState([]);
  const [selectedMetric, setSelectedMetric] = useState('score');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        // 1. Charger les infos délégués pour le score global et niveau
        const delRes = await fetch(`${API_BASE}/api/training/delegues`);
        if (!delRes.ok) return;
        const delegues = await delRes.json();

        const displayName = user?.display_name || '';
        const found = delegues.find(d => d.nom.toLowerCase().includes(displayName.split(' ')[0].toLowerCase()));
        
        if (found) {
          setDelegueInfo(found);
          
          // 2. Charger l'historique réel
          const histRes = await fetch(`${API_BASE}/api/training/history/${found.id}`);
          if (histRes.ok) {
            const data = await histRes.json();
            // Assurer qu'on a au moins quelques points pour le rendu initial
            setHistoryData(data.length > 0 ? data : [
              { date: 'Initial', score: 0, confidence: 0, engagement: 0, product_knowledge: 0 }
            ]);
          }
        }
      } catch (e) {
        console.warn('Erreur chargement données dashboard:', e);
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, [user]);

  const navigateTo = (path) => {
    navigate(`${path}?role=delegate&sub=${subRole}`);
  };

  const displayName = user?.display_name || 'Délégué';
  const firstName = displayName.split(' ')[0];
  const score = delegueInfo?.score ?? '—';
  const level = delegueInfo?.level ?? '—';

  // ── Page Profil ──────────────────────────────────────────────────────────────
  if (location.pathname.includes('profil')) {
    return (
      <div className="space-y-12 animate-fade-in pb-20 relative">
        <h1 className="text-6xl font-black uppercase text-md-on-background tracking-tighter">Mon Profil</h1>
        <div className="md-card max-w-3xl p-10 bg-white shadow-xl mt-8 border-none">
          <div className="flex items-center gap-6 mb-10">
            <div className="w-20 h-20 rounded-3xl bg-md-primary flex items-center justify-center text-white text-3xl font-black shadow-xl shadow-md-primary/30">
              {firstName[0]?.toUpperCase() || 'D'}
            </div>
            <div>
              <h2 className="text-2xl font-black text-md-on-background">{displayName}</h2>
              <p className="text-sm font-bold text-md-primary uppercase tracking-widest">{roleTitle}</p>
              <div className="flex items-center gap-2 mt-2">
                <Star size={14} className="text-amber-500 fill-amber-500" />
                <span className="text-xs font-bold text-md-outline">{level}</span>
                <span className="text-xs text-md-outline">•</span>
                <Activity size={14} className="text-emerald-500" />
                <span className="text-xs font-bold text-emerald-600">Score : {score}/100</span>
              </div>
            </div>
          </div>

          <h3 className="text-[11px] font-black uppercase tracking-[0.2em] opacity-60 mb-6">Informations du compte</h3>
          <div className="space-y-5">
            <div className="flex items-center gap-4 p-4 bg-md-surface-container rounded-2xl">
              <User size={18} className="text-md-primary flex-shrink-0" />
              <div>
                <p className="text-[10px] font-black uppercase tracking-widest opacity-50 mb-0.5">Nom complet</p>
                <p className="font-bold text-md-on-background">{displayName}</p>
              </div>
            </div>
            <div className="flex items-center gap-4 p-4 bg-md-surface-container rounded-2xl">
              <Mail size={18} className="text-md-primary flex-shrink-0" />
              <div>
                <p className="text-[10px] font-black uppercase tracking-widest opacity-50 mb-0.5">Email</p>
                <p className="font-bold text-md-on-background">{user?.email || '—'}</p>
              </div>
            </div>
            <div className="flex items-center gap-4 p-4 bg-md-surface-container rounded-2xl">
              <Award size={18} className="text-amber-500 flex-shrink-0" />
              <div>
                <p className="text-[10px] font-black uppercase tracking-widest opacity-50 mb-0.5">Niveau actuel</p>
                <p className="font-bold text-md-on-background">{level}</p>
              </div>
            </div>
            <div className="flex items-center gap-4 p-4 bg-md-surface-container rounded-2xl">
              <Activity size={18} className="text-emerald-500 flex-shrink-0" />
              <div>
                <p className="text-[10px] font-black uppercase tracking-widest opacity-50 mb-0.5">Score global</p>
                <p className="font-bold text-emerald-600">{score} / 100</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const activeMetric = METRICS.find(m => m.id === selectedMetric) || METRICS[0];

  // ── Page d'accueil ─────────────────────────────────────────────────────────
  return (
    <div className="space-y-12 animate-fade-in pb-20 relative">
      <div className="fixed top-0 right-0 w-[600px] h-[600px] organic-glow bg-md-primary/10 rounded-full -z-10" />
      
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-10 relative z-10">
        <div className="space-y-4">
           <div className="flex items-center gap-4">
               <div className="w-12 h-12 rounded-2xl bg-md-secondary-container flex items-center justify-center text-md-primary shadow-lg shadow-md-primary/10 transition-transform hover:rotate-12">
                  <Zap size={24} fill="currentColor" />
               </div>
               <span className="text-[11px] font-black text-md-primary uppercase tracking-[0.5em] leading-none">Unité de Performance Active</span>
           </div>
           <h1 className="text-6xl font-black text-md-on-background tracking-tighter leading-[0.9] uppercase">
             Bonjour, <br/>
             <span className={`${isMedical ? 'text-md-primary' : 'text-emerald-500'} italic lowercase`}>
               {firstName}.
             </span>
           </h1>
           <p className="text-md-on-surface-variant font-bold text-xl leading-relaxed max-w-lg mt-4 opacity-70 italic tracking-tight">
             Prêt pour votre session d'excellence en tant que <span className={`font-black not-italic ${isMedical ? 'text-md-on-background' : 'text-emerald-600'}`}>{roleTitle}</span> ?
           </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 relative z-10">
         {[
           { title: 'Formation', desc: 'Simulateur cognitif & flux IA', cta: 'Lancer Simulation', icon: BrainCircuit, color: 'bg-md-primary/10 text-md-primary', path: '/delegate/training' },
           { title: 'Produits', desc: 'Analyse des gammes prioritaires', cta: 'Recommandations', icon: PackageCheck, color: 'bg-emerald-500/10 text-emerald-600', path: '/delegate/produits' },
           { title: 'Visites', desc: 'Planification optimale IA', cta: 'Ma Tournée', icon: MapIcon, color: 'bg-md-on-background/5 text-md-on-background', path: '/delegate/planner' },
         ].map((card, i) => (
            <motion.div whileHover={{ y: -12, scale: 1.02 }} key={i} onClick={() => navigateTo(card.path)} className="md-card flex flex-col items-start gap-10 group bg-white border-none shadow-xl hover:shadow-2xl cursor-pointer p-10 overflow-hidden relative">
               <div className="absolute top-0 right-0 w-32 h-32 bg-md-primary/5 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2 group-hover:scale-150 transition-transform duration-700" />
               <div className={`w-16 h-16 rounded-[24px] ${card.color} flex items-center justify-center shadow-inner relative z-10`}>
                  <card.icon size={30} strokeWidth={2.5} />
               </div>
               <div className="flex-1 relative z-10">
                   <h4 className="text-2xl font-black text-md-on-background tracking-tighter uppercase leading-none">{card.title}</h4>
                   <p className="text-xs font-bold text-md-on-surface-variant opacity-60 mt-3 uppercase tracking-widest">{card.desc}</p>
               </div>
               <button className="relative z-10 w-full btn-tonal !h-14 group flex items-center justify-between px-8 border border-md-outline/10 shadow-sm transition-all !rounded-2xl">
                  <span className="text-[11px] font-black uppercase tracking-[0.2em]">{card.cta}</span>
                  <ChevronRight size={18} className="group-hover:translate-x-2 transition-transform" />
               </button>
            </motion.div>
         ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 relative z-10">
         <div className="lg:col-span-8 md-card p-10 flex flex-col gap-8 bg-white border-none shadow-xl">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
               <div className="space-y-1">
                  <h3 className="text-2xl font-black text-md-on-background tracking-tighter uppercase">Analyse de Progression</h3>
                  <p className="text-xs font-bold text-md-on-surface-variant opacity-60 uppercase tracking-widest italic">Historique réel par simulation</p>
               </div>
               
               {/* Metrics Tabs */}
               <div className="flex items-center p-1.5 bg-md-surface-container rounded-2xl border border-md-outline/5 self-start">
                  {METRICS.map(m => (
                    <button
                      key={m.id}
                      onClick={() => setSelectedMetric(m.id)}
                      className={`px-4 py-2 rounded-xl flex items-center gap-2 transition-all duration-300 ${selectedMetric === m.id ? 'bg-white shadow-md text-md-on-background' : 'text-md-on-surface-variant opacity-50 hover:opacity-100'}`}
                    >
                      <m.icon size={14} style={{ color: selectedMetric === m.id ? m.color : 'inherit' }} />
                      <span className="text-[10px] font-black uppercase tracking-wider">{m.label}</span>
                    </button>
                  ))}
               </div>
            </div>
            
            <div className="h-[350px] w-full mt-4">
               {isLoading ? (
                 <div className="w-full h-full flex items-center justify-center opacity-30"><Activity size={40} className="animate-pulse" /></div>
               ) : (
                 <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={historyData}>
                       <defs>
                          <linearGradient id="colorMetric" x1="0" y1="0" x2="0" y2="1">
                             <stop offset="5%" stopColor={activeMetric.color} stopOpacity={0.3}/>
                             <stop offset="95%" stopColor={activeMetric.color} stopOpacity={0}/>
                          </linearGradient>
                       </defs>
                       <XAxis 
                          dataKey="date" 
                          axisLine={false} 
                          tickLine={false} 
                          tick={{ fontSize: 10, fontWeight: 900, fill: 'var(--color-md-outline)' }}
                          dy={15}
                       />
                       <Tooltip 
                          contentStyle={{ borderRadius: '24px', border: 'none', boxShadow: '0 20px 50px -10px rgba(0,0,0,0.1)', padding: '20px', backgroundColor: 'rgba(255,255,255,0.95)', backdropFilter: 'blur(10px)' }}
                          itemStyle={{ fontWeight: 900, fontSize: '13px', textTransform: 'uppercase' }}
                          cursor={{ stroke: activeMetric.color, strokeWidth: 1, strokeDasharray: '4 4' }}
                       />
                       <Area 
                          type="monotone" 
                          dataKey={selectedMetric} 
                          name={activeMetric.label}
                          stroke={activeMetric.color} 
                          strokeWidth={6} 
                          fillOpacity={1} 
                          fill="url(#colorMetric)" 
                          animationDuration={1500}
                       />
                    </AreaChart>
                 </ResponsiveContainer>
               )}
            </div>
         </div>

         <div className="lg:col-span-4 flex flex-col gap-8">
            <div className="bg-md-on-background text-white p-12 rounded-[48px] flex-1 flex flex-col justify-between shadow-2xl relative overflow-hidden group border border-white/5">
               <div className="absolute top-0 right-0 w-64 h-64 organic-glow bg-md-primary/20 blur-[100px] -z-10 group-hover:scale-150 transition-all duration-1000" />
               <div className="relative z-10">
                  <div className="flex items-center gap-4 mb-10">
                     <div className="w-14 h-14 bg-md-primary rounded-2xl flex items-center justify-center text-white text-xl font-black shadow-xl shadow-md-primary/30">
                       {firstName[0]?.toUpperCase() || 'D'}
                     </div>
                     <div>
                       <h4 className="text-[11px] font-black uppercase tracking-[0.4em] opacity-50">Mon Profil</h4>
                       <p className="font-black text-white text-sm mt-0.5">{displayName}</p>
                     </div>
                  </div>
                  <div className="space-y-4">
                    <div className="p-4 bg-white/5 rounded-2xl border border-white/5 flex items-center gap-4">
                       <Award size={20} className="text-amber-400" />
                       <div>
                          <p className="text-[9px] font-black uppercase tracking-widest text-white/40">Niveau</p>
                          <p className="font-black text-sm">{level}</p>
                       </div>
                    </div>
                    <div className="p-4 bg-white/5 rounded-2xl border border-white/5 flex items-center gap-4">
                       <Activity size={20} className="text-emerald-400" />
                       <div>
                          <p className="text-[9px] font-black uppercase tracking-widest text-white/40">Score Global</p>
                          <p className="font-black text-sm text-emerald-400">{score} / 100</p>
                       </div>
                    </div>
                    <div className="p-4 bg-white/5 rounded-2xl border border-white/5 flex items-center gap-4">
                       <Mail size={20} className="text-indigo-400" />
                       <div>
                          <p className="text-[9px] font-black uppercase tracking-widest text-white/40">Email</p>
                          <p className="font-bold text-xs opacity-70 truncate max-w-[150px]">{user?.email || '—'}</p>
                       </div>
                    </div>
                  </div>
               </div>
               <button onClick={() => navigateTo('/delegate/training')} className="relative z-10 w-full py-6 bg-white/5 hover:bg-md-primary hover:text-white rounded-3xl border border-white/10 transition-all duration-500 font-black text-[12px] uppercase tracking-[0.3em] mt-10 group shadow-lg">
                  Lancer Simulation <ArrowRight size={20} className="inline ml-4 group-hover:translate-x-3 transition-transform" />
               </button>
            </div>
         </div>
      </div>
    </div>
  );
}
