import React, { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { useLocation } from 'react-router-dom';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, 
  AreaChart, Area, PieChart, Pie, Cell, LineChart, Line, Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis
} from 'recharts';
import { 
  Users, TrendingUp, Star, Activity, Search, Download, Calendar, Zap, 
  Stethoscope, Store, ChevronRight, ArrowRight, FileText, Clock, Filter, 
  CheckCircle2, ArrowLeft, PackageCheck, Award, ShieldCheck, Target, ExternalLink
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8001';

// Mock Data for Analytics
const annualPerformance = [
  { mois: 'Jan', medical: 4000, commercial: 2400 }, { mois: 'Fév', medical: 3000, commercial: 1398 },
  { mois: 'Mar', medical: 2000, commercial: 9800 }, { mois: 'Avr', medical: 2780, commercial: 3908 },
  { mois: 'Mai', medical: 1890, commercial: 4800 }, { mois: 'Juin', medical: 2390, commercial: 3800 },
  { mois: 'Juil', medical: 3490, commercial: 4300 }, { mois: 'Août', medical: 4200, commercial: 5100 },
  { mois: 'Sep', medical: 3800, commercial: 4600 }, { mois: 'Oct', medical: 4500, commercial: 5800 },
  { mois: 'Nov', medical: 4800, commercial: 6200 }, { mois: 'Déc', medical: 5200, commercial: 7000 },
];

const radarData = [
  { item: 'Connaissance Produit', value: 85, full: 100 },
  { item: 'Communication', value: 92, full: 100 },
  { item: 'Argumentation', value: 78, full: 100 },
  { item: 'Gestion Objections', value: 65, full: 100 },
  { item: 'Présentation', value: 88, full: 100 },
];

export default function AdminDashboard({ initialTab = 'synthèse' }) {
  const location = useLocation();
  const path = location.pathname.split('/').pop();
  
  const [activeTab, setActiveTab] = useState(initialTab);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

  // Data States
  const [delegues, setDelegues] = useState([]);
  const [medecins, setMedecins] = useState([]);
  const [pharmacies, setPharmacies] = useState([]);
  const [products, setProducts] = useState([]);
  const [gammes, setGammes] = useState([]);
  
  // Drill-down State
  const [selectedDelegue, setSelectedDelegue] = useState(null);
  const [simulations, setSimulations] = useState([]);

  // DSO3 States
  const [isAddingProduct, setIsAddingProduct] = useState(false);
  const [showRecs, setShowRecs] = useState(false);
  const [newProduct, setNewProduct] = useState({ name: '', gamme_id: '', description: '', category: '', indications: '', compositions: '', usage_advice: '' });
  const [currentRecs, setCurrentRecs] = useState([]);
  const [selectedRecs, setSelectedRecs] = useState([]);
  const [createdProductId, setCreatedProductId] = useState(null);

  // Sync state with URL path
  useEffect(() => {
    if (path === 'dashboard') setActiveTab('synthèse');
    else if (path === 'produits') setActiveTab('produits');
    else if (path === 'stats') setActiveTab('stats');
    else if (path === 'delegues') setActiveTab('délégués');
  }, [path]);

  // 1. Fetch initial data
  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true);
      try {
        const [delRes, medRes, pharRes, prodRes, gammeRes] = await Promise.all([
          fetch(`${API_BASE}/api/admin/delegues_summary`),
          fetch(`${API_BASE}/api/admin/medecins`),
          fetch(`${API_BASE}/api/admin/pharmaciens`),
          fetch(`${API_BASE}/api/admin/training/products`),
          fetch(`${API_BASE}/api/admin/training/gammes`)
        ]);

        if (delRes.ok) setDelegues(await delRes.json());
        if (medRes.ok) setMedecins(await medRes.json());
        if (pharRes.ok) setPharmacies(await pharRes.json());
        if (prodRes.ok) setProducts(await prodRes.json());
        if (gammeRes.ok) setGammes(await gammeRes.json());
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

  // ── Handlers DSO3 ──────────────────────────────────────────────────────────
  const handleAddProduct = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch(`${API_BASE}/api/admin/products/product`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newProduct)
      });
      if (res.ok) {
        const data = await res.json();
        setCreatedProductId(data.product_id);
        setCurrentRecs(data.recommendations);
        setShowRecs(true);
        setIsAddingProduct(false);
        const pRes = await fetch(`${API_BASE}/api/admin/training/products`);
        if (pRes.ok) setProducts(await pRes.json());
      }
    } catch (err) {
      console.error("Erreur ajout produit:", err);
    }
  };

  const handleConfirmRecs = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/admin/products/confirm-recommendations`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          product_id: createdProductId,
          delegate_ids: selectedRecs
        })
      });
      if (res.ok) {
        setShowRecs(false);
        setSelectedRecs([]);
        alert("Affectations enregistrées avec succès !");
      }
    } catch (err) {
      console.error("Erreur confirmation recs:", err);
    }
  };

  // Filtering
  const filteredDelegues = delegues.filter(d => d.nom.toLowerCase().includes(searchQuery.toLowerCase()));
  const filteredMedecins = medecins.filter(m => m.nom?.toLowerCase().includes(searchQuery.toLowerCase()) || m.specialite?.toLowerCase().includes(searchQuery.toLowerCase()));
  const filteredPharmacies = pharmacies.filter(p => p.nom?.toLowerCase().includes(searchQuery.toLowerCase()));
  const filteredProducts = products.filter(p => p.name?.toLowerCase().includes(searchQuery.toLowerCase()));

  // ── Sub-renders ────────────────────────────────────────────────────────────

  const renderAnalytics = () => (
    <div className="space-y-10 animate-fade-in">
       {/* KPI Cards */}
       <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          {[
            { label: 'Délégués Actifs', value: delegues.length, icon: Users, trend: '+12%', color: 'bg-md-primary/10 text-md-primary' },
            { label: 'Score Moyen', value: '86.4%', icon: Star, trend: '+4.2%', color: 'bg-amber-100 text-amber-700' },
            { label: 'Sessions Direct', value: '156', icon: Zap, trend: '-2.1%', color: 'bg-emerald-100 text-emerald-700' },
            { label: 'Produits Vital', value: products.length, icon: PackageCheck, trend: '+5%', color: 'bg-sky-100 text-sky-700' },
          ].map((kpi, i) => (
            <motion.div whileHover={{ y: -5 }} key={i} className="md-card flex flex-col gap-4 relative overflow-hidden">
               <div className="flex items-center justify-between relative z-10">
                  <div className={`w-12 h-12 rounded-2xl ${kpi.color} flex items-center justify-center shadow-sm`}>
                     <kpi.icon size={22} />
                  </div>
                  <div className="text-[10px] font-black text-emerald-500 uppercase">{kpi.trend}</div>
               </div>
               <div className="relative z-10">
                  <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">{kpi.label}</p>
                  <h3 className="text-3xl font-black text-slate-800">{kpi.value}</h3>
               </div>
            </motion.div>
          ))}
       </div>

       {/* Performance Graph */}
       <div className="md-card p-10">
          <h3 className="text-xl font-black text-slate-800 uppercase tracking-tight mb-8">Performance Analytique du Réseau</h3>
          <div className="h-[400px] w-full">
             <ResponsiveContainer width="100%" height="100%">
                <LineChart data={annualPerformance}>
                   <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                   <XAxis dataKey="mois" axisLine={false} tickLine={false} tick={{ fontSize: 11, fontWeight: 900, fill: '#64748b' }} dy={10} />
                   <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 11, fontWeight: 900, fill: '#64748b' }} />
                   <Tooltip contentStyle={{ borderRadius: '24px', border: 'none', boxShadow: '0 10px 40px -10px rgba(0,0,0,0.1)' }} />
                   <Line type="monotone" dataKey="medical" stroke="#52b1a8" strokeWidth={6} dot={{ r: 6, fill: '#52b1a8', strokeWidth: 3, stroke: '#fff' }} />
                   <Line type="monotone" dataKey="commercial" stroke="#0f172a" strokeWidth={6} dot={{ r: 6, fill: '#0f172a', strokeWidth: 3, stroke: '#fff' }} />
                </LineChart>
             </ResponsiveContainer>
          </div>
       </div>
    </div>
  );

  const renderStats = () => (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-10 animate-fade-in">
       <div className="md-card p-10 flex flex-col gap-10">
          <h3 className="text-xl font-black text-slate-800 uppercase tracking-tight">Compétences Globales</h3>
          <div className="h-[400px]">
             <ResponsiveContainer width="100%" height="100%">
               <RadarChart cx="50%" cy="50%" outerRadius="80%" data={radarData}>
                  <PolarGrid stroke="#f1f5f9" />
                  <PolarAngleAxis dataKey="item" tick={{ fontSize: 10, fontWeight: 900, fill: '#0f172a' }} />
                  <Radar name="Moyenne Réseau" dataKey="value" stroke="#52b1a8" fill="#52b1a8" fillOpacity={0.5} strokeWidth={5} />
                  <Tooltip />
               </RadarChart>
             </ResponsiveContainer>
          </div>
       </div>

       <div className="md-card p-10 flex flex-col gap-10">
          <h3 className="text-xl font-black text-slate-800 uppercase tracking-tight">Leaderboard Excellence</h3>
          <div className="space-y-6">
             {delegues.slice(0, 4).sort((a,b) => b.actual_avg_score - a.actual_avg_score).map((d, i) => (
                <div key={i} className="flex items-center justify-between p-4 bg-slate-50 rounded-2xl">
                   <div className="flex items-center gap-4">
                      <div className="w-10 h-10 rounded-xl bg-[#52b1a8] text-white flex items-center justify-center font-black">#{i+1}</div>
                      <span className="font-bold text-slate-800 uppercase text-xs">{d.nom}</span>
                   </div>
                   <span className="font-black text-emerald-600">{Math.round(d.actual_avg_score)}%</span>
                </div>
             ))}
          </div>
       </div>
    </div>
  );

  if (selectedDelegue) {
    return (
      <div className="space-y-12 animate-fade-in pb-24">
        <button onClick={() => setSelectedDelegue(null)} className="flex items-center gap-3 text-[10px] font-black uppercase tracking-[0.3em] text-[#52b1a8] hover:gap-5 transition-all">
          <ArrowLeft size={16} /> Retour à la liste
        </button>
        <div className="flex flex-col md:flex-row items-start justify-between gap-10">
          <div className="space-y-4">
             <div className="w-16 h-16 rounded-3xl bg-[#52b1a8] flex items-center justify-center text-white text-2xl font-black shadow-xl shadow-[#52b1a8]/30">{selectedDelegue.nom[0]}</div>
             <h1 className="text-5xl font-black text-slate-800 tracking-tighter uppercase leading-none">{selectedDelegue.nom}</h1>
             <div className="flex items-center gap-3">
                <span className="px-5 py-2 bg-[#52b1a8]/10 text-[#52b1a8] rounded-full text-[10px] font-black uppercase tracking-widest">{selectedDelegue.role}</span>
                <span className="px-5 py-2 bg-emerald-500/10 text-emerald-600 rounded-full text-[10px] font-black uppercase tracking-widest">Niveau : {selectedDelegue.level}</span>
             </div>
          </div>
          <div className="md-card p-8 bg-slate-900 text-white flex gap-10 shadow-2xl">
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
        <div className="md-card !p-0 overflow-hidden shadow-2xl bg-white">
           <div className="p-10 border-b border-slate-50 flex items-center justify-between">
              <h3 className="text-xl font-black text-slate-800 uppercase tracking-tight">Historique des Sessions</h3>
              <FileText size={24} className="opacity-20" />
           </div>
           <div className="overflow-x-auto">
              <table className="w-full text-left">
                 <thead className="bg-slate-50 text-[10px] font-black text-slate-400 uppercase tracking-[0.3em]">
                    <tr>
                       <th className="px-10 py-6">Date & Heure</th>
                       <th className="px-10 py-6">Produit Cible</th>
                       <th className="px-10 py-6">Score Final</th>
                       <th className="px-10 py-6 text-right">Rapport</th>
                    </tr>
                 </thead>
                 <tbody className="divide-y divide-slate-50">
                    {simulations.length === 0 ? (
                      <tr><td colSpan="4" className="px-10 py-20 text-center text-xs font-bold opacity-40 uppercase tracking-widest">Aucune session enregistrée</td></tr>
                    ) : simulations.map((s) => (
                       <tr key={s.id} className="hover:bg-slate-50 transition-colors">
                          <td className="px-10 py-6 text-sm font-bold text-slate-800 flex items-center gap-3">
                             <Calendar size={14} className="opacity-40" /> {s.date}
                          </td>
                          <td className="px-10 py-6">
                             <span className="text-[10px] font-black text-[#52b1a8] uppercase tracking-widest px-4 py-1.5 bg-[#52b1a8]/5 rounded-full">{s.product_name}</span>
                          </td>
                          <td className="px-10 py-6 font-black text-slate-800">{Math.round(s.score)}%</td>
                          <td className="px-10 py-6 text-right">
                             <a href={`${API_BASE}/reports/${s.report_path}`} target="_blank" rel="noreferrer" className="inline-flex items-center gap-2 px-6 py-2.5 bg-emerald-500 text-white rounded-full text-[10px] font-black uppercase tracking-widest shadow-lg shadow-emerald-500/20 hover:scale-105 transition-all">
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

  return (
    <div className="space-y-12 animate-fade-in pb-24 relative">
      <div className="fixed top-0 right-0 w-[600px] h-[600px] organic-glow bg-[#52b1a8]/5 rounded-full -z-10" />
      
      <div className="flex flex-col lg:flex-row lg:items-end justify-between gap-10">
        <div className="space-y-4">
           <div className="flex items-center gap-4">
               <div className="w-12 h-12 rounded-2xl bg-[#52b1a8] flex items-center justify-center text-white shadow-lg shadow-[#52b1a8]/20">
                  <ShieldCheck size={24} />
               </div>
               <span className="text-[11px] font-black text-[#52b1a8] uppercase tracking-[0.5em] leading-none">Console Administrative</span>
           </div>
           <h1 className="text-6xl font-black text-slate-800 tracking-tighter leading-[0.9] uppercase">Supervision <br/><span className="text-[#52b1a8] italic lowercase">réseau.</span></h1>
        </div>

        <div className="flex flex-col items-end gap-4">
           <div className="bg-white p-2 rounded-2xl border border-slate-100 flex flex-wrap gap-1 shadow-xl">
              {['synthèse', 'stats', 'délégués', 'médecins', 'pharmacies', 'produits'].map(tab => (
                 <button 
                   key={tab}
                   onClick={() => setActiveTab(tab)}
                   className={`px-6 py-3 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all ${activeTab === tab ? 'bg-[#52b1a8] text-white shadow-lg shadow-[#52b1a8]/20' : 'text-slate-400 hover:bg-slate-50'}`}
                 >
                   {tab}
                 </button>
              ))}
           </div>
           <div className="relative">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-300" size={16} />
              <input 
                type="text" 
                placeholder="Rechercher..." 
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                className="pl-12 pr-6 h-12 bg-white rounded-full text-xs font-bold border border-slate-100 w-64 shadow-sm focus:w-80 transition-all outline-none" 
              />
           </div>
        </div>
      </div>

      <AnimatePresence mode="wait">
        {isLoading ? (
          <div className="h-96 flex items-center justify-center opacity-30"><Activity size={48} className="animate-pulse" /></div>
        ) : (
          <motion.div key={activeTab} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }} className="md-card !p-0 overflow-hidden bg-white shadow-2xl">
             {activeTab === 'synthèse' && renderAnalytics()}
             {activeTab === 'stats' && renderStats()}
             
             {(['délégués', 'médecins', 'pharmacies', 'produits'].includes(activeTab)) && (
                <table className="w-full text-left">
                   <thead className="bg-slate-50 text-[10px] font-black text-slate-400 uppercase tracking-[0.3em]">
                      {activeTab === 'délégués' && (
                        <tr>
                           <th className="px-10 py-6">Délégué</th>
                           <th className="px-10 py-6">Role</th>
                           <th className="px-10 py-6">Sessions</th>
                           <th className="px-10 py-6">Score Moyen</th>
                           <th className="px-10 py-6 text-right">Détails</th>
                        </tr>
                      )}
                      {activeTab === 'médecins' && (
                        <tr>
                           <th className="px-10 py-6">Médecin</th>
                           <th className="px-10 py-6">Spécialité</th>
                           <th className="px-10 py-6">Localisation</th>
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
                      {activeTab === 'produits' && (
                        <tr>
                           <th className="px-10 py-6">Produit</th>
                           <th className="px-10 py-6">Gamme</th>
                           <th className="px-10 py-6">Catégorie</th>
                           <th className="px-10 py-6 text-right">
                              <button onClick={() => setIsAddingProduct(true)} className="px-6 py-2 bg-[#52b1a8] text-white rounded-full text-[10px] font-black uppercase tracking-widest shadow-lg shadow-[#52b1a8]/20">+ Nouveau</button>
                           </th>
                        </tr>
                      )}
                   </thead>
                   <tbody className="divide-y divide-slate-50">
                      {activeTab === 'délégués' && filteredDelegues.map(d => (
                        <tr key={d.id} className="hover:bg-slate-50 transition-colors group">
                           <td className="px-10 py-6 flex items-center gap-4">
                              <div className="w-10 h-10 rounded-xl bg-[#52b1a8]/10 text-[#52b1a8] flex items-center justify-center font-black text-xs">{d.nom[0]}</div>
                              <span className="font-bold text-slate-800">{d.nom}</span>
                           </td>
                           <td className="px-10 py-6 text-[10px] font-black text-slate-400 uppercase tracking-widest">{d.role}</td>
                           <td className="px-10 py-6 font-black">{d.total_sims_completed}</td>
                           <td className="px-10 py-6">
                              <div className="flex items-center gap-3">
                                 <div className="w-16 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                                    <div className="h-full bg-emerald-500" style={{ width: `${d.actual_avg_score}%` }} />
                                 </div>
                                 <span className="font-black text-emerald-600">{Math.round(d.actual_avg_score)}%</span>
                              </div>
                           </td>
                           <td className="px-10 py-6 text-right">
                              <button onClick={() => handleSelectDelegue(d)} className="p-3 bg-[#52b1a8]/5 text-[#52b1a8] rounded-xl hover:bg-[#52b1a8] hover:text-white transition-all"><ChevronRight size={18} /></button>
                           </td>
                        </tr>
                      ))}

                      {activeTab === 'médecins' && filteredMedecins.map(m => (
                        <tr key={m.id} className="hover:bg-slate-50 transition-colors">
                           <td className="px-10 py-6 flex items-center gap-4">
                              <div className="w-10 h-10 rounded-xl bg-sky-50 text-sky-600 flex items-center justify-center"><Stethoscope size={18} /></div>
                              <span className="font-bold text-slate-800">{m.nom} {m.prenom}</span>
                           </td>
                           <td className="px-10 py-6 font-black text-[10px] uppercase tracking-widest text-sky-600">{m.specialite}</td>
                           <td className="px-10 py-6 italic text-xs text-slate-400">{m.adresse}</td>
                           <td className="px-10 py-6 font-bold text-xs">{m.telephone}</td>
                        </tr>
                      ))}

                      {activeTab === 'pharmacies' && filteredPharmacies.map(p => (
                        <tr key={p.id} className="hover:bg-slate-50 transition-colors">
                           <td className="px-10 py-6 flex items-center gap-4">
                              <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center"><Store size={18} /></div>
                              <span className="font-bold text-slate-800">{p.nom}</span>
                           </td>
                           <td className="px-10 py-6 font-black text-[10px] uppercase tracking-widest text-emerald-600">{p.type_pharmacie}</td>
                           <td className="px-10 py-6 italic text-xs text-slate-400">{p.adresse}, {p.gouvernorat}</td>
                           <td className="px-10 py-6 font-bold text-xs">{p.telephone}</td>
                        </tr>
                      ))}

                      {activeTab === 'produits' && filteredProducts.map(p => (
                        <tr key={p.id} className="hover:bg-slate-50 transition-colors">
                           <td className="px-10 py-6 flex items-center gap-4">
                              <div className="w-10 h-10 rounded-xl bg-[#52b1a8]/5 text-[#52b1a8] flex items-center justify-center"><PackageCheck size={18} /></div>
                              <span className="font-bold text-slate-800">{p.name}</span>
                           </td>
                           <td className="px-10 py-6 text-[10px] font-black text-slate-400 uppercase tracking-widest">Gamme #{p.gamme_id}</td>
                           <td className="px-10 py-6 font-black text-[10px] uppercase tracking-widest text-[#52b1a8]">{p.category || "N/A"}</td>
                           <td className="px-10 py-6 text-right opacity-40 italic text-[10px]">ID: {p.id}</td>
                        </tr>
                      ))}
                   </tbody>
                </table>
             )}
          </motion.div>
        )}
      </AnimatePresence>

      {/* DSO3 Modals */}
      {isAddingProduct && typeof document !== 'undefined' && createPortal(
        <div className="fixed inset-0 z-[1000] flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4 overflow-y-auto">
          <div className="bg-white rounded-[40px] p-10 w-full max-w-xl shadow-2xl relative my-auto">
             <h2 className="text-3xl font-black uppercase tracking-tighter mb-8">Nouveau Produit</h2>
             <div className="space-y-6 max-h-[60vh] overflow-y-auto pr-2 scrollbar-hide">
                <input placeholder="Nom du produit" className="w-full p-5 bg-slate-50 rounded-2xl outline-none focus:ring-2 ring-[#52b1a8]/20 transition-all font-bold" value={newProduct.name} onChange={e => setNewProduct({...newProduct, name: e.target.value})} />
                <select className="w-full p-5 bg-slate-50 rounded-2xl outline-none font-bold" value={newProduct.gamme_id} onChange={e => setNewProduct({...newProduct, gamme_id: e.target.value})}>
                   <option value="">Choisir une gamme...</option>
                   {gammes.map(g => <option key={g.id} value={g.id}>{g.name}</option>)}
                </select>
                <input placeholder="Catégorie" className="w-full p-5 bg-slate-50 rounded-2xl outline-none font-bold" value={newProduct.category} onChange={e => setNewProduct({...newProduct, category: e.target.value})} />
                <textarea placeholder="Indications" className="w-full p-5 bg-slate-50 rounded-2xl outline-none font-bold min-h-[100px]" value={newProduct.indications} onChange={e => setNewProduct({...newProduct, indications: e.target.value})} />
                <textarea placeholder="Composition" className="w-full p-5 bg-slate-50 rounded-2xl outline-none font-bold min-h-[100px]" value={newProduct.compositions} onChange={e => setNewProduct({...newProduct, compositions: e.target.value})} />
                <textarea placeholder="Conseils d'utilisation" className="w-full p-5 bg-slate-50 rounded-2xl outline-none font-bold min-h-[100px]" value={newProduct.usage_advice} onChange={e => setNewProduct({...newProduct, usage_advice: e.target.value})} />
             </div>
             <div className="flex gap-4 mt-10">
                <button onClick={() => setIsAddingProduct(false)} className="flex-1 p-5 rounded-2xl font-black uppercase tracking-widest text-[10px] bg-slate-100 text-slate-500">Annuler</button>
                <button onClick={handleAddProduct} className="flex-[2] p-5 rounded-2xl font-black uppercase tracking-widest text-[10px] bg-[#52b1a8] text-white shadow-xl shadow-[#52b1a8]/20">Ajouter & Recommander</button>
             </div>
          </div>
        </div>
      , document.body)}

      {showRecs && typeof document !== 'undefined' && createPortal(
        <div className="fixed inset-0 z-[1100] flex items-center justify-center bg-slate-900/80 backdrop-blur-xl p-4">
          <div className="bg-white rounded-[48px] p-12 w-full max-w-4xl shadow-2xl space-y-10 max-h-[90vh] overflow-y-auto scrollbar-hide">
             <div className="space-y-2">
                <span className="text-[10px] font-black text-[#52b1a8] uppercase tracking-[0.5em]">Intelligence DSO3</span>
                <h2 className="text-4xl font-black uppercase tracking-tighter">Profils Recommandés</h2>
                <p className="text-slate-400 font-bold opacity-60">Délégués experts sélectionnés pour <span className="text-[#52b1a8] uppercase">{newProduct.name}</span>.</p>
             </div>
             <div className="grid grid-cols-1 gap-4">
                {currentRecs.map(rec => (
                   <div key={rec.delegate_id} onClick={() => selectedRecs.includes(rec.delegate_id) ? setSelectedRecs(selectedRecs.filter(id => id !== rec.delegate_id)) : setSelectedRecs([...selectedRecs, rec.delegate_id])} className={`p-8 rounded-[32px] border-2 transition-all cursor-pointer flex items-center justify-between ${selectedRecs.includes(rec.delegate_id) ? 'border-[#52b1a8] bg-[#52b1a8]/5' : 'border-slate-50 hover:border-[#52b1a8]/30'}`}>
                      <div className="flex items-center gap-6">
                         <div className={`w-14 h-14 rounded-[22px] flex items-center justify-center font-black text-white ${selectedRecs.includes(rec.delegate_id) ? 'bg-[#52b1a8]' : 'bg-slate-200'}`}>{rec.delegate_name[0]}</div>
                         <div>
                            <p className="font-black text-xl uppercase tracking-tighter">{rec.delegate_name}</p>
                            <p className="text-[10px] font-bold text-[#52b1a8] uppercase tracking-widest">Expertise: {rec.expertise}</p>
                         </div>
                      </div>
                      <div className="text-right">
                         <p className="text-[10px] font-black uppercase opacity-30 mb-1">Score Moyen</p>
                         <p className="text-3xl font-black text-emerald-500">{rec.score}%</p>
                      </div>
                   </div>
                ))}
             </div>
             <div className="flex gap-4 pt-6">
                <button onClick={() => setShowRecs(false)} className="flex-1 h-16 rounded-3xl font-black uppercase tracking-widest text-[10px] bg-slate-100">Plus tard</button>
                <button onClick={handleConfirmRecs} disabled={selectedRecs.length === 0} className="flex-[2] h-16 rounded-3xl font-black uppercase tracking-widest text-[10px] bg-[#52b1a8] text-white shadow-xl shadow-[#52b1a8]/20">Affecter {selectedRecs.length} profil(s)</button>
             </div>
          </div>
        </div>
      , document.body)}
    </div>
  );
}
