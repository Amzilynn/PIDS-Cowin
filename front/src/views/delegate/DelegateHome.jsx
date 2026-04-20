import React, { useMemo, useEffect } from 'react';
import { 
  BrainCircuit, 
  PlusSquare, 
  PackageCheck, 
  Map as MapIcon,
  TrendingUp,
  Award,
  Calendar,
  MessageSquare,
  ArrowRight,
  ChevronRight,
  Activity,
  Star,
  Zap,
  Target
} from 'lucide-react';
import { motion } from 'framer-motion';
import { AreaChart, Area, ResponsiveContainer, XAxis, Tooltip } from 'recharts';
import { useNavigate, useLocation } from 'react-router-dom';

const performanceData = [
  { day: 'Lun', score: 72 }, { day: 'Mar', score: 85 }, { day: 'Mer', score: 78 },
  { day: 'Jeu', score: 91 }, { day: 'Ven', score: 88 }, { day: 'Sam', score: 94 },
  { day: 'Dim', score: 90 },
];

export default function DelegateHome({ subRole = 'medical' }) {
  const navigate = useNavigate();
  const location = useLocation();
  const isMedical = subRole === 'medical';
  const roleTitle = isMedical ? 'Délégué Médical' : 'Délégué Commercial';
  const presentedTo = isMedical ? 'médecin' : 'pharmacien';

   const authPayload = useMemo(() => {
      try {
         return JSON.parse(localStorage.getItem('cw_auth') || '{}');
      } catch {
         return {};
      }
   }, []);
   const newRecommendations = Array.isArray(authPayload?.new_recommendations)
      ? authPayload.new_recommendations
      : [];

  useEffect(() => {
    if (newRecommendations.length > 0) {
      try {
        const currentAuth = JSON.parse(localStorage.getItem('cw_auth') || '{}');
        if (currentAuth.new_recommendations) {
          delete currentAuth.new_recommendations;
          currentAuth.new_recommendations_count = 0;
          localStorage.setItem('cw_auth', JSON.stringify(currentAuth));
        }
      } catch (e) {}
    }
  }, [newRecommendations]);

  const navigateTo = (path) => {
    navigate(`${path}?role=delegate&sub=${subRole}`);
  };

  if (location.pathname.includes('profil')) {
    return (
      <div className="space-y-12 animate-fade-in pb-20 relative">
         <h1 className="text-6xl font-black uppercase text-md-on-background tracking-tighter">Éditer le Profil</h1>
         <div className="md-card max-w-3xl p-10 bg-white shadow-xl mt-8 border-none">
            <h2 className="text-xl font-black uppercase tracking-tight mb-8">Informations Personnelles</h2>
            <div className="space-y-6">
                <div>
                   <label className="block text-[11px] font-black uppercase tracking-[0.2em] opacity-60 mb-3">Nom Complet</label>
                   <input type="text" className="w-full bg-md-surface-container border border-md-outline/10 p-4 rounded-2xl font-bold" defaultValue={isMedical ? 'Sarah Khalil' : 'Marc Dupont'} />
                </div>
                <div>
                   <label className="block text-[11px] font-black uppercase tracking-[0.2em] opacity-60 mb-3">Rôle</label>
                   <input type="text" className="w-full bg-md-surface-container border border-md-outline/10 p-4 rounded-2xl font-bold opacity-60 text-md-on-surface-variant" disabled defaultValue={roleTitle} />
                </div>
                <div>
                   <label className="block text-[11px] font-black uppercase tracking-[0.2em] opacity-60 mb-3">Email</label>
                   <input type="email" className="w-full bg-md-surface-container border border-md-outline/10 p-4 rounded-2xl font-bold" defaultValue={`${isMedical ? 'sarah' : 'marc'}@meddelegate.pro`} />
                </div>
                <button className="btn-primary !h-14 uppercase tracking-[0.2em] text-[11px] font-black mt-8 w-full md:w-auto px-8 !rounded-xl shadow-xl">Enregistrer les modifications</button>
            </div>
         </div>
      </div>
    );
  }

  return (
    <div className="space-y-12 animate-fade-in pb-20 relative">
      {/* Background Organic Glow */}
      <div className="fixed top-0 right-0 w-[600px] h-[600px] organic-glow bg-md-primary/10 rounded-full -z-10" />
      
      {/* Personalized Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-10 relative z-10">
        <div className="space-y-4">
           <div className="flex items-center gap-4">
               <div className="w-12 h-12 rounded-2xl bg-md-secondary-container flex items-center justify-center text-md-primary shadow-lg shadow-md-primary/10 transition-transform hover:rotate-12">
                  <Zap size={24} fill="currentColor" />
               </div>
               <span className="text-[11px] font-black text-md-primary uppercase tracking-[0.5em] leading-none">Unité de Performance Active</span>
           </div>
           <h1 className="text-6xl font-black text-md-on-background tracking-tighter leading-[0.9] uppercase">Bonjour, <br/><span className={`${isMedical ? 'text-md-primary' : 'text-emerald-500'} italic lowercase`}>{isMedical ? 'Sarah' : 'Marc'}.</span></h1>
           <p className="text-md-on-surface-variant font-bold text-xl leading-relaxed max-w-lg mt-4 opacity-70 italic tracking-tight">
             Prêts pour votre session d'excellence aujourd'hui en tant que <span className={`font-black not-italic ${isMedical ? 'text-md-on-background' : 'text-emerald-600'}`}>{roleTitle}</span> ?
           </p>
        </div>
      </div>

         {newRecommendations.length > 0 ? (
            <div className="rounded-3xl border border-amber-300 bg-amber-50 px-6 py-5 shadow-sm relative z-10">
               <p className="text-[11px] font-black uppercase tracking-widest text-amber-700 mb-2">Nouveaux produits recommandés</p>
               <p className="text-sm font-bold text-amber-800 mb-3">
                  {newRecommendations.length} nouvelle(s) recommandation(s) pour votre profil.
               </p>
               <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  {newRecommendations.map((item, index) => (
                     <div key={`${item.recommendation_id}-${index}`} className="rounded-2xl bg-white border border-amber-200 px-4 py-3">
                        <p className="text-xs font-black text-md-on-background uppercase">{item.product_name}</p>
                        <p className="text-[10px] font-bold text-md-on-surface-variant mt-1">Score: {(item.score * 100).toFixed(1)}%</p>
                     </div>
                  ))}
               </div>
            </div>
         ) : null}

      {/* Main Action Grid (4 Cards - BO1 to BO4) */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 relative z-10">
         {[
           { 
             title: 'Formation', 
             desc: 'Simulateur cognitif & flux conversationnel IA', 
             cta: 'Lancer Simulation', 
             icon: BrainCircuit, 
             color: 'bg-md-primary/10 text-md-primary',
             path: '/delegate/training'
           },
           { 
             title: `Présentation`, 
             desc: `Pitching clinique haute-fidélité au ${presentedTo}`, 
             cta: 'Commencer Session', 
             icon: PlusSquare, 
             color: 'bg-indigo-500/10 text-indigo-600',
             path: '/delegate/presentation'
           },
           { 
             title: 'Produits', 
             desc: 'Analyse prédictive des gammes prioritaires', 
             cta: 'Recommandations', 
             icon: PackageCheck, 
             color: 'bg-emerald-500/10 text-emerald-600',
             path: '/delegate/produits'
           },
           { 
             title: 'Visites', 
             desc: 'Planification optimale & itinéraire IA', 
             cta: 'Ma Tournée', 
             icon: MapIcon, 
             color: 'bg-md-on-background/5 text-md-on-background',
             path: '/delegate/planner'
           },
         ].filter(c => c.title !== 'Présentation').map((card, i) => (
            <motion.div 
               whileHover={{ y: -12, scale: 1.02 }}
               key={i} 
               onClick={() => navigateTo(card.path)}
               className="md-card flex flex-col items-start gap-10 group bg-white border-none shadow-xl hover:shadow-2xl cursor-pointer p-10 overflow-hidden relative"
            >
               <div className="absolute top-0 right-0 w-32 h-32 bg-md-primary/5 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2 group-hover:scale-150 transition-transform duration-700" />
               
               <div className={`w-16 h-16 rounded-[24px] ${card.color} flex items-center justify-center shadow-inner group-hover:shadow-md transition-all duration-500 relative z-10`}>
                  <card.icon size={30} strokeWidth={2.5} />
               </div>
               <div className="flex-1 relative z-10">
                   <h4 className="text-2xl font-black text-md-on-background tracking-tighter uppercase leading-none">{card.title}</h4>
                   <p className="text-xs font-bold text-md-on-surface-variant opacity-60 mt-3 leading-relaxed uppercase tracking-widest">{card.desc}</p>
               </div>
               <button className="relative z-10 w-full btn-tonal !h-14 group flex items-center justify-between px-8 border border-md-outline/10 shadow-sm hover:shadow-md transition-all !rounded-2xl">
                  <span className="text-[11px] font-black uppercase tracking-[0.2em]">{card.cta}</span>
                  <ChevronRight size={18} className="group-hover:translate-x-2 transition-transform" />
               </button>
            </motion.div>
         ))}
      </div>

      {/* Metrics & Activity Summary */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 relative z-10">
         
         {/* Performance AreaChart */}
         <div className="lg:col-span-8 md-card p-12 flex flex-col gap-10 bg-white border-none shadow-xl">
            <div className="flex items-center justify-between">
               <div className="space-y-1">
                  <h3 className="text-2xl font-black text-md-on-background tracking-tighter uppercase">Courbe de Performance</h3>
                  <p className="text-xs font-bold text-md-on-surface-variant opacity-60 uppercase tracking-widest italic leading-none">Progression analytique sur les 7 derniers jours</p>
               </div>
               <div className="flex items-center gap-3 px-6 py-3 bg-emerald-500/10 border border-emerald-500/20 rounded-full shadow-sm">
                  <TrendingUp size={20} className="text-emerald-500" />
                  <span className="text-xs font-black text-emerald-500 uppercase tracking-widest leading-none">+18.4%</span>
               </div>
            </div>
            
            <div className="h-[300px] w-full mt-4">
               <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={performanceData}>
                     <defs>
                        <linearGradient id="colorScoreHome" x1="0" y1="0" x2="0" y2="1">
                           <stop offset="5%" stopColor="var(--color-md-primary)" stopOpacity={0.4}/>
                           <stop offset="95%" stopColor="var(--color-md-primary)" stopOpacity={0}/>
                        </linearGradient>
                     </defs>
                     <XAxis dataKey="day" hide />
                     <Tooltip 
                        contentStyle={{ borderRadius: '28px', border: 'none', boxShadow: '0 20px 50px -10px rgba(0,0,0,0.1)', padding: '24px', backgroundColor: 'rgba(255,255,255,0.9)', backdropFilter: 'blur(10px)' }}
                        itemStyle={{ fontWeight: 900, color: 'var(--color-md-primary)', textTransform: 'uppercase', fontSize: '14px' }}
                     />
                     <Area 
                        type="monotone" 
                        dataKey="score" 
                        stroke="var(--color-md-primary)" 
                        strokeWidth={8} 
                        fillOpacity={1} 
                        fill="url(#colorScoreHome)" 
                        animationDuration={2000}
                     />
                  </AreaChart>
               </ResponsiveContainer>
            </div>
         </div>

         {/* Prochaine Étape / Focus */}
         <div className="lg:col-span-4 flex flex-col gap-8">
            <div className="bg-md-on-background text-white p-12 rounded-[48px] flex-1 flex flex-col justify-between shadow-2xl relative overflow-hidden group border border-white/5">
               <div className="absolute top-0 right-0 w-64 h-64 organic-glow bg-md-primary/20 blur-[100px] -z-10 group-hover:scale-150 transition-all duration-1000" />
               
               <div className="relative z-10">
                  <div className="flex items-center gap-4 mb-10">
                     <div className="w-12 h-12 bg-md-primary rounded-2xl flex items-center justify-center text-white shadow-xl shadow-md-primary/30">
                        <Calendar size={24} />
                     </div>
                     <h4 className="text-[11px] font-black uppercase tracking-[0.4em] opacity-50">Focus Terrain</h4>
                  </div>
                  <h3 className="text-4xl font-black tracking-tighter leading-[1] mb-4 uppercase">Visite Critique au <br /><span className="text-md-primary italic lowercase">Dr. Jean-Pierre.</span></h3>
                  <div className="flex items-center gap-3 text-xs font-bold opacity-40 uppercase tracking-[0.2em] italic">
                     <Target size={16} /> Paris 16e — 14:30 Aujourd'hui
                  </div>
               </div>
               
               <button 
                 onClick={() => navigateTo('/delegate/planner')}
                 className="relative z-10 w-full py-6 bg-white/5 hover:bg-md-primary hover:text-white rounded-3xl border border-white/10 transition-all duration-500 font-black text-[12px] uppercase tracking-[0.3em] mt-10 group shadow-lg"
               >
                  Préparer la Tournée
                  <ArrowRight size={20} className="inline ml-4 group-hover:translate-x-3 transition-transform" />
               </button>
            </div>
         </div>
      </div>
    </div>
  );
}
