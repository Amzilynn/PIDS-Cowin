import React, { useState } from 'react';
import { 
  PackageCheck, 
  Search, 
  Filter, 
  ArrowUpRight, 
  ChevronRight, 
  Target, 
  Activity, 
  Zap,
  Info,
  Download,
  Star,
  Award,
  Box,
  TrendingUp,
  ShieldCheck,
  LayoutGrid
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useLocation } from 'react-router-dom';

const products = [
  { id: 1, name: "Cardio-Protect X10", range: "Cardiologie", score: 98, reason: "Adéquation totale profil DSO1", color: "bg-emerald-500", desc: "Inhibiteur SGLT2 de nouvelle génération avec protection rénale étendue." },
  { id: 2, name: "Gluco-Smart 500", range: "Diabétologie", score: 85, reason: "Module de perfectionnement requis", color: "bg-amber-500", desc: "Traitement oral pour le diabète de type 2, focalisé sur la stabilité glycémique." },
  { id: 3, name: "Nephro-Guard v2", range: "Néphrologie", score: 92, reason: "Opportunité de secteur identifiée", color: "bg-sky-500", desc: "Solution injectable pour la gestion de l'insuffisance rénale terminale." },
  { id: 4, name: "Onco-Lift 200", range: "Oncologie", score: 76, reason: "Priorité stratégique Q2 2026", color: "bg-rose-500", desc: "Thérapie ciblée pour les adénocarcinomes métastatiques." },
  { id: 5, name: "Neuro-Sync Alpha", range: "Neurologie", score: 81, reason: "Nouveauté de gamme 2026", color: "bg-indigo-500", desc: "Traitement adjuvant pour les syndromes neuro-dégénératifs précoces." },
];

export default function ProductRecommendations() {
  const location = useLocation();
  const query = new URLSearchParams(location.search);
  const subRole = query.get('sub') || 'medical';
  const [filter, setFilter] = useState('all');
  
  const filteredProducts = filter === 'all' 
    ? products 
    : products.filter(p => p.range.toLowerCase().includes(filter));

  return (
    <div className="space-y-12 animate-fade-in pb-20 relative z-10">
      
      {/* Background Graphic Signature */}
      <div className="fixed top-0 right-0 w-[600px] h-[600px] organic-glow bg-md-primary/5 rounded-full pointer-events-none -z-10" />
      <div className="fixed bottom-0 left-0 w-[800px] h-[800px] organic-glow bg-md-tertiary/5 rounded-full pointer-events-none -z-10" />

      {/* Header Info - Impact Visuel MD3 */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-10">
         <div className="space-y-4 flex-1">
            <div className="flex items-center gap-4">
               <div className="w-12 h-12 rounded-2xl bg-md-secondary-container text-md-primary flex items-center justify-center shadow-lg shadow-md-primary/10 transition-transform hover:rotate-12">
                  <PackageCheck size={26} strokeWidth={2.5} />
               </div>
               <span className="text-[11px] font-black text-md-primary uppercase tracking-[0.5em] leading-none text-md-primary">Assistant IA de Gamme (BO3)</span>
            </div>
            <h1 className="text-6xl font-black text-md-on-background tracking-tighter leading-[0.9] uppercase">Gamme <br/><span className="text-md-primary italic lowercase">recommandée.</span></h1>
            <p className="text-md-on-surface-variant font-bold text-xl leading-relaxed max-w-xl mt-4 opacity-70 italic tracking-tight">
               Algorithmes prédictifs basés sur vos scores DSO en tant que <span className="text-md-on-background font-black not-italic px-4 py-1.5 bg-white rounded-full shadow-sm">délégué {subRole}</span>.
            </p>
         </div>

      </div>

      {/* Recommandation Vedette (Carte Horizontale Impactante) */}
      <motion.div 
         initial={{ opacity: 0, y: 30 }}
         animate={{ opacity: 1, y: 0 }}
         transition={{ duration: 0.8, ease: [0.2, 0, 0, 1] }}
         className="md-card p-12 bg-md-on-background text-white flex flex-col md:flex-row items-center gap-12 relative overflow-hidden group shadow-2xl border border-white/5"
      >
         {/* Background Decoration */}
         <div className="absolute top-0 right-0 w-[500px] h-[500px] organic-glow bg-md-primary/20 blur-[120px] -z-10 translate-x-1/4 -translate-y-1/4 group-hover:scale-150 transition-transform duration-1000" />
         
         <div className="relative z-10 w-56 h-56 rounded-[56px] bg-white/5 flex items-center justify-center border-4 border-white/10 group-hover:scale-110 transition-all duration-700 shadow-2xl overflow-hidden">
            <div className="absolute inset-0 bg-md-primary/10 blur-xl animate-pulse" />
            <PackageCheck size={100} strokeWidth={1} className="text-md-primary group-hover:rotate-12 transition-all relative z-10" />
         </div>

         <div className="flex-1 relative z-10 text-center md:text-left space-y-6">
            <div className="flex flex-col md:flex-row md:items-center gap-4">
               <div className="px-6 py-2.5 bg-md-primary text-white rounded-pill text-[10px] font-black uppercase tracking-[0.3em] w-fit mx-auto md:mx-0 shadow-lg shadow-md-primary/30">Opportunité Alpha #1</div>
               <div className="px-6 py-2.5 bg-white/5 rounded-pill text-[10px] font-black uppercase tracking-[0.3em] w-fit mx-auto md:mx-0 border border-white/10 italic">IA Predictive May 2026</div>
            </div>
            <h2 className="text-5xl font-black tracking-tighter leading-none uppercase italic text-md-primary">Cardio-Protect X10</h2>
            <p className="text-base font-bold opacity-50 max-w-xl leading-relaxed uppercase tracking-tighter italic">
               "Le produit le plus pertinent pour votre secteur actuel. Les données d'étude clinique DSO-v42 montrent une corrélation directe avec votre zone géographique de visite."
            </p>
            <div className="flex flex-wrap items-center justify-center md:justify-start gap-12 pt-6 border-t border-white/10">
                <div className="flex flex-col">
                   <span className="text-5xl font-black text-md-primary tracking-tighter">98<span className="text-2xl font-bold opacity-40">%</span></span>
                   <span className="text-[10px] font-black uppercase opacity-40 tracking-widest mt-2">Score Adéquation</span>
                </div>
                <div className="h-14 w-px bg-white/10 hidden md:block" />
                <div className="flex flex-col">
                   <span className="text-5xl font-black text-md-primary tracking-tighter">DSO<span className="text-2xl font-bold opacity-40">1</span></span>
                   <span className="text-[10px] font-black uppercase opacity-40 tracking-widest mt-2">Niveau Requis</span>
                </div>
                <button className="flex-1 md:flex-none btn-primary !h-16 !px-12 !bg-white !text-md-on-background !shadow-2xl hover:!bg-md-primary hover:!text-white transition-all group !rounded-3xl">
                   <span className="relative z-10 flex items-center gap-4 font-black uppercase tracking-[0.3em] text-[12px]">Lancer le Detailing <ArrowUpRight size={22} className="group-hover:translate-x-1 group-hover:-translate-y-1 transition-transform" /></span>
                </button>
            </div>
         </div>
      </motion.div>

      {/* Grille de Produits Secondaires */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-10 relative z-10 pb-12">
         <AnimatePresence mode="popLayout">
            {filteredProducts.map((p, i) => (
               <motion.div 
                 layout
                 key={p.id} 
                 initial={{ opacity: 0, scale: 0.9 }}
                 animate={{ opacity: 1, scale: 1 }}
                 transition={{ delay: i * 0.05 }}
                 className="md-card p-10 flex flex-col gap-10 group bg-white border-none shadow-xl hover:shadow-2xl transition-all duration-500 relative overflow-hidden"
               >
                  <div className="absolute top-0 right-0 w-32 h-32 bg-md-primary/5 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2 group-hover:scale-150 transition-transform duration-700" />
                  
                  <div className="flex items-center justify-between relative z-10">
                     <div className={`w-14 h-14 rounded-[20px] ${p.color} text-white flex items-center justify-center shadow-inner group-hover:shadow-lg transition-all duration-500 group-hover:rotate-12`}>
                        <PackageCheck size={28} strokeWidth={2} />
                     </div>
                     <div className="text-right">
                        <p className="text-[10px] font-black text-md-on-surface-variant uppercase tracking-widest opacity-40 mb-1 leading-none uppercase">Indice IA</p>
                        <p className="text-3xl font-black text-md-on-background tracking-tighter">{p.score}%</p>
                     </div>
                  </div>
                  
                  <div className="flex-1 space-y-3 relative z-10">
                     <h4 className="text-2xl font-black text-md-on-background tracking-tighter leading-none uppercase">{p.name}</h4>
                     <p className="text-[11px] font-black text-md-primary uppercase tracking-[0.3em] underline underline-offset-4 decoration-md-primary/20">{p.range}</p>
                     <p className="text-xs font-bold text-md-on-surface-variant opacity-60 leading-relaxed italic mt-6 uppercase tracking-widest border-l-4 border-md-primary/20 pl-4">
                       "{p.reason}"
                     </p>
                  </div>

                  <button className="relative z-10 w-full btn-tonal !h-14 !rounded-2xl group flex items-center justify-between px-8 border border-md-outline/10 hover:border-md-primary/30 transition-all font-black uppercase text-[11px] tracking-widest">
                     <span>Détails Techniques</span>
                     <ChevronRight size={18} className="group-hover:translate-x-2 transition-transform" />
                  </button>
               </motion.div>
            ))}
         </AnimatePresence>
      </div>

      {/* Profil Insights - IA & Big Data Section */}
      <div className="md-card overflow-hidden bg-md-surface-container p-0 border-none shadow-2xl relative">
          <div className="grid grid-cols-1 lg:grid-cols-12">
             <div className="lg:col-span-4 p-14 bg-md-primary text-white flex flex-col gap-10 relative overflow-hidden">
                <div className="absolute inset-0 organic-glow bg-white/10 blur-[120px] pointer-events-none" />
                <div className="relative z-10 w-20 h-20 rounded-[28px] bg-white/20 flex items-center justify-center shadow-2xl border border-white/20">
                   <Target size={40} className="text-white animate-pulse" />
                </div>
                <div className="relative z-10 space-y-6">
                   <h3 className="text-4xl font-black tracking-tighter leading-none uppercase italic">Processus de <br/>Recommandation IA.</h3>
                   <p className="text-base font-bold opacity-50 leading-relaxed uppercase tracking-tighter">
                      Nos algorithmes croisent 48 points de données incluant vos scores simulator (BO1), vos performances terrain (BO4) et les objectifs stratégiques globaux.
                   </p>
                </div>
                <button className="relative z-10 btn-pill w-full h-16 bg-white text-md-on-background mt-8 !text-[12px] font-black uppercase tracking-[0.4em] shadow-2xl transition-all group active:scale-95">
                   <span className="flex items-center justify-center gap-4">Actualiser le Profil <Activity size={20} className="group-hover:rotate-12 transition-transform" /></span>
                </button>
             </div>
             
             <div className="lg:col-span-8 p-14 bg-white/40 backdrop-blur-3xl flex items-center relative">
                <div className="absolute bottom-0 right-0 w-64 h-64 bg-md-primary/5 blur-[80px] -z-10" />
                <div className="grid grid-cols-1 md:grid-cols-2 gap-16 w-full">
                   <div className="space-y-6 group cursor-default">
                      <div className="flex items-center gap-5">
                         <div className="w-14 h-14 rounded-2xl bg-md-primary/10 text-md-primary flex items-center justify-center shadow-inner group-hover:scale-110 transition-transform duration-500">
                            <Star size={26} strokeWidth={2.5} />
                         </div>
                         <h4 className="text-lg font-black text-md-on-background uppercase tracking-tight">Rang DSO Élite</h4>
                      </div>
                      <p className="text-sm font-bold text-md-on-surface-variant opacity-60 leading-relaxed uppercase tracking-widest italic border-l-4 border-md-primary/10 pl-6">
                         Votre score de 94% sur le module Cardio influence dynamiquement les recommandations de haute-technicité médicale.
                      </p>
                   </div>
                   <div className="space-y-6 group cursor-default">
                      <div className="flex items-center gap-5">
                         <div className="w-14 h-14 rounded-2xl bg-indigo-500/10 text-indigo-600 flex items-center justify-center shadow-inner group-hover:scale-110 transition-transform duration-500">
                            <TrendingUp size={26} strokeWidth={2.5} />
                         </div>
                         <h4 className="text-lg font-black text-md-on-background uppercase tracking-tight">Potentiel Secteur</h4>
                      </div>
                      <p className="text-sm font-bold text-md-on-surface-variant opacity-60 leading-relaxed uppercase tracking-widest italic border-l-4 border-indigo-500/10 pl-6">
                         La densité de praticiens cibles dans votre zone actuelle (BO4) priorise les produits de spécialité à fort impact clinique.
                      </p>
                   </div>
                </div>
             </div>
          </div>
      </div>
    </div>
  );
}
