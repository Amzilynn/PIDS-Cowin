import React, { useState, useEffect } from 'react';
import { 
  Users, 
  TrendingUp, 
  Star, 
  Activity, 
  Search, 
  Download, 
  Calendar, 
  Zap, 
  Stethoscope, 
  Store,
  ChevronRight,
  ArrowRight,
  FileText,
  Clock,
  Filter,
  CheckCircle2,
  ExternalLink,
  ArrowLeft
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8001';

export default function AdminDashboard() {
  const [activeTab, setActiveTab] = useState('delegues'); // 'delegues', 'medecins', 'pharmacies'
  const [delegues, setDelegues] = useState([]);
  const [medecins, setMedecins] = useState([]);
  const [pharmacies, setPharmacies] = useState([]);
  const [selectedDelegue, setSelectedDelegue] = useState(null);
  const [simulations, setSimulations] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

  // 1. Fetch initial data
  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true);
      try {
        const [delRes, medRes, pharRes] = await Promise.all([
          fetch(`${API_BASE}/api/admin/delegues_summary`),
          fetch(`${API_BASE}/api/admin/medecins`),
          fetch(`${API_BASE}/api/admin/pharmaciens`)
        ]);

        if (delRes.ok) setDelegues(await delRes.json());
        if (medRes.ok) setMedecins(await medRes.json());
        if (pharRes.ok) setPharmacies(await pharRes.json());
      } catch (e) {
        console.error("Erreur chargement admin:", e);
      } finally {
        setIsLoading(false);
      }
    };
    fetchData();
  }, []);

  // 2. Fetch simulations for a delegate
  const handleSelectDelegue = async (del) => {
    setSelectedDelegue(del);
    setSimulations([]);
    try {
      const res = await fetch(`${API_BASE}/api/admin/delegue_simulations/${del.id}`);
      if (res.ok) {
        setSimulations(await res.json());
      }
    } catch (e) {
      console.error("Erreur chargement simulations:", e);
    }
  };

  const filteredDelegues = delegues.filter(d => d.nom.toLowerCase().includes(searchQuery.toLowerCase()));
  const filteredMedecins = medecins.filter(m => m.nom.toLowerCase().includes(searchQuery.toLowerCase()) || m.specialite.toLowerCase().includes(searchQuery.toLowerCase()));
  const filteredPharmacies = pharmacies.filter(p => p.nom.toLowerCase().includes(searchQuery.toLowerCase()));

  // ── Rendu de l'historique d'un délégué ──────────────────────────────────────
  if (selectedDelegue) {
    return (
      <div className="space-y-12 animate-fade-in pb-24">
        <button 
          onClick={() => setSelectedDelegue(null)}
          className="flex items-center gap-3 text-[10px] font-black uppercase tracking-[0.3em] text-md-primary hover:gap-5 transition-all"
        >
          <ArrowLeft size={16} /> Retour à la liste
        </button>

        <div className="flex flex-col md:flex-row items-start justify-between gap-10">
          <div className="space-y-4">
             <div className="w-16 h-16 rounded-3xl bg-md-primary flex items-center justify-center text-white text-2xl font-black shadow-xl shadow-md-primary/30">
                {selectedDelegue.nom[0]}
             </div>
             <h1 className="text-5xl font-black text-md-on-background tracking-tighter uppercase leading-none">
                {selectedDelegue.nom}
             </h1>
             <div className="flex items-center gap-3">
                <span className="px-5 py-2 bg-md-primary/10 text-md-primary rounded-full text-[10px] font-black uppercase tracking-widest">{selectedDelegue.role}</span>
                <span className="px-5 py-2 bg-emerald-500/10 text-emerald-600 rounded-full text-[10px] font-black uppercase tracking-widest">Niveau : {selectedDelegue.level}</span>
             </div>
          </div>

          <div className="md-card p-8 bg-md-on-background text-white flex gap-10 shadow-2xl">
             <div className="text-center">
                <p className="text-[10px] font-black uppercase tracking-widest opacity-50 mb-1">Simulations</p>
                <p className="text-3xl font-black">{selectedDelegue.total_sims_completed}</p>
             </div>
             <div className="w-px h-12 bg-white/10 self-center" />
             <div className="text-center">
                <p className="text-[10px] font-black uppercase tracking-widest opacity-50 mb-1">Score Moyen</p>
                <p className="text-3xl font-black text-emerald-400">{Math.round(selectedDelegue.actual_avg_score)}%</p>
             </div>
          </div>
        </div>

        <div className="md-card !p-0 overflow-hidden shadow-2xl border-none bg-white">
           <div className="p-10 border-b border-md-outline/5 flex items-center justify-between">
              <h3 className="text-xl font-black text-md-on-background uppercase tracking-tight">Historique des Sessions</h3>
              <FileText size={24} className="opacity-20" />
           </div>
           
           <div className="overflow-x-auto">
              <table className="w-full text-left">
                 <thead className="bg-md-surface-container text-[10px] font-black text-md-on-surface-variant uppercase tracking-[0.3em]">
                    <tr>
                       <th className="px-10 py-6">Date & Heure</th>
                       <th className="px-10 py-6">Produit Cible</th>
                       <th className="px-10 py-6">Score Final</th>
                       <th className="px-10 py-6 text-right">Rapport</th>
                    </tr>
                 </thead>
                 <tbody className="divide-y divide-md-outline/5">
                    {simulations.length === 0 ? (
                      <tr><td colSpan="4" className="px-10 py-20 text-center text-xs font-bold opacity-40 uppercase tracking-widest">Aucune session enregistrée</td></tr>
                    ) : simulations.map((s) => (
                       <tr key={s.id} className="hover:bg-slate-50 transition-colors">
                          <td className="px-10 py-6 text-sm font-bold text-md-on-background flex items-center gap-3">
                             <Calendar size={14} className="opacity-40" /> {s.date}
                          </td>
                          <td className="px-10 py-6">
                             <span className="text-[10px] font-black text-md-primary uppercase tracking-widest px-4 py-1.5 bg-md-primary/5 rounded-full">
                                {s.product_name}
                             </span>
                          </td>
                          <td className="px-10 py-6 font-black text-md-on-background">{Math.round(s.score)}%</td>
                          <td className="px-10 py-6 text-right">
                             <a 
                               href={`${API_BASE}/reports/${s.report_path}`} 
                               target="_blank" 
                               rel="noreferrer"
                               className="inline-flex items-center gap-2 px-6 py-2.5 bg-emerald-500 text-white rounded-full text-[10px] font-black uppercase tracking-widest shadow-lg shadow-emerald-500/20 hover:scale-105 transition-all"
                             >
                                Voir PDF <ExternalLink size={12} />
                             </a>
                          </td>
                       </tr>
                    ))}
                 </tbody>
              </table>
           </div>
        </div>
      </div>
    );
  }

  // ── Rendu Dashboard Principal ──────────────────────────────────────────────
  return (
    <div className="space-y-12 animate-fade-in pb-24">
      <div className="fixed top-0 right-0 w-[600px] h-[600px] organic-glow bg-md-primary/10 rounded-full -z-10" />
      
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-10">
        <div className="space-y-4">
           <div className="flex items-center gap-4">
               <div className="w-12 h-12 rounded-2xl bg-md-primary flex items-center justify-center text-white shadow-lg">
                  <Zap size={24} fill="currentColor" />
               </div>
               <span className="text-[11px] font-black text-md-primary uppercase tracking-[0.5em] leading-none">Console Administrative Centrale</span>
           </div>
           <h1 className="text-6xl font-black text-md-on-background tracking-tighter leading-[0.9] uppercase">Supervision <br/><span className="text-md-primary italic lowercase">terrain.</span></h1>
           <p className="text-md-on-surface-variant font-bold text-lg max-w-lg mt-4 opacity-70 italic tracking-tight">Analyse globale des performances et suivi du réseau Vital.</p>
        </div>

        <div className="flex flex-col items-end gap-4">
           <div className="bg-white p-2 rounded-2xl border border-md-outline/10 flex gap-1 shadow-sm">
              <button 
                onClick={() => setActiveTab('delegues')}
                className={`px-8 py-3 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all ${activeTab === 'delegues' ? 'bg-md-primary text-white shadow-lg' : 'text-md-outline hover:bg-slate-50'}`}
              >
                Délégués
              </button>
              <button 
                onClick={() => setActiveTab('medecins')}
                className={`px-8 py-3 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all ${activeTab === 'medecins' ? 'bg-md-primary text-white shadow-lg' : 'text-md-outline hover:bg-slate-50'}`}
              >
                Médecins
              </button>
              <button 
                onClick={() => setActiveTab('pharmacies')}
                className={`px-8 py-3 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all ${activeTab === 'pharmacies' ? 'bg-md-primary text-white shadow-lg' : 'text-md-outline hover:bg-slate-50'}`}
              >
                Pharmacies
              </button>
           </div>
           <div className="relative">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-md-outline/40" size={16} />
              <input 
                type="text" 
                placeholder="Rechercher..." 
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                className="pl-12 pr-6 h-12 bg-white rounded-full text-xs font-bold border border-md-outline/10 w-64 shadow-sm focus:w-80 transition-all outline-none" 
              />
           </div>
        </div>
      </div>

      <AnimatePresence mode="wait">
        {isLoading ? (
          <div className="h-96 flex items-center justify-center opacity-30"><Activity size={48} className="animate-pulse" /></div>
        ) : (
          <motion.div 
            key={activeTab}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="md-card !p-0 overflow-hidden bg-white shadow-2xl border-none"
          >
             <table className="w-full text-left">
                <thead className="bg-md-surface-container text-[10px] font-black text-md-on-surface-variant uppercase tracking-[0.3em]">
                   {activeTab === 'delegues' && (
                     <tr>
                        <th className="px-10 py-6">Délégué</th>
                        <th className="px-10 py-6">Role</th>
                        <th className="px-10 py-6">Sessions</th>
                        <th className="px-10 py-6">Moyenne Score</th>
                        <th className="px-10 py-6 text-right">Détails</th>
                     </tr>
                   )}
                   {activeTab === 'medecins' && (
                     <tr>
                        <th className="px-10 py-6">Médecin</th>
                        <th className="px-10 py-6">Spécialité</th>
                        <th className="px-10 py-6">Gouvernorat</th>
                        <th className="px-10 py-6">Contact</th>
                     </tr>
                   )}
                   {activeTab === 'pharmacies' && (
                     <tr>
                        <th className="px-10 py-6">Pharmacie</th>
                        <th className="px-10 py-6">Type</th>
                        <th className="px-10 py-6">Localisation</th>
                        <th className="px-10 py-6">Contact</th>
                     </tr>
                   )}
                </thead>
                <tbody className="divide-y divide-md-outline/5">
                   {activeTab === 'delegues' && filteredDelegues.map(d => (
                     <tr key={d.id} className="hover:bg-slate-50 transition-colors group">
                        <td className="px-10 py-6 flex items-center gap-4">
                           <div className="w-10 h-10 rounded-xl bg-md-primary/10 text-md-primary flex items-center justify-center font-black text-xs">{d.nom[0]}</div>
                           <span className="font-bold text-md-on-background">{d.nom}</span>
                        </td>
                        <td className="px-10 py-6 text-xs font-bold text-md-on-surface-variant uppercase tracking-widest">{d.role}</td>
                        <td className="px-10 py-6 font-black">{d.total_sims_completed}</td>
                        <td className="px-10 py-6">
                           <div className="flex items-center gap-3">
                              <div className="w-16 h-1.5 bg-md-surface-container rounded-full overflow-hidden">
                                 <div className="h-full bg-emerald-500" style={{ width: `${d.actual_avg_score}%` }} />
                              </div>
                              <span className="font-black text-emerald-600">{Math.round(d.actual_avg_score)}%</span>
                           </div>
                        </td>
                        <td className="px-10 py-6 text-right">
                           <button 
                             onClick={() => handleSelectDelegue(d)}
                             className="p-3 bg-md-primary/5 text-md-primary rounded-xl hover:bg-md-primary hover:text-white transition-all shadow-sm"
                           >
                              <ChevronRight size={18} />
                           </button>
                        </td>
                     </tr>
                   ))}

                   {activeTab === 'medecins' && filteredMedecins.map(m => (
                     <tr key={m.id} className="hover:bg-slate-50 transition-colors">
                        <td className="px-10 py-6 flex items-center gap-4">
                           <div className="w-10 h-10 rounded-xl bg-sky-50 text-sky-600 flex items-center justify-center"><Stethoscope size={18} /></div>
                           <span className="font-bold text-md-on-background">{m.nom} {m.prenom}</span>
                        </td>
                        <td className="px-10 py-6 font-black text-xs uppercase tracking-widest text-sky-600">{m.specialite}</td>
                        <td className="px-10 py-6 italic text-sm opacity-60">{m.adresse}</td>
                        <td className="px-10 py-6 font-bold text-sm tracking-tighter">{m.telephone}</td>
                     </tr>
                   ))}

                   {activeTab === 'pharmacies' && filteredPharmacies.map(p => (
                     <tr key={p.id} className="hover:bg-slate-50 transition-colors">
                        <td className="px-10 py-6 flex items-center gap-4">
                           <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center"><Store size={18} /></div>
                           <span className="font-bold text-md-on-background">{p.nom}</span>
                        </td>
                        <td className="px-10 py-6 font-black text-xs uppercase tracking-widest text-emerald-600">{p.type_pharmacie}</td>
                        <td className="px-10 py-6 italic text-sm opacity-60">{p.adresse}, {p.gouvernorat}</td>
                        <td className="px-10 py-6 font-bold text-sm tracking-tighter">{p.telephone}</td>
                     </tr>
                   ))}
                </tbody>
             </table>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
