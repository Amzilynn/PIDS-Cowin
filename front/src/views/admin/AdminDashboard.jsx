import React, { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
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
  ArrowLeft,
  PackageCheck
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8001';

export default function AdminDashboard({ initialTab = 'delegues' }) {
  const [activeTab, setActiveTab] = useState(initialTab); // 'delegues', 'medecins', 'pharmacies', 'produits'
  const [delegues, setDelegues] = useState([]);
  const [medecins, setMedecins] = useState([]);
  const [pharmacies, setPharmacies] = useState([]);
  const [products, setProducts] = useState([]);
  const [gammes, setGammes] = useState([]);
  
  const [selectedDelegue, setSelectedDelegue] = useState(null);
  const [simulations, setSimulations] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

  // DSO3 States
  const [isAddingProduct, setIsAddingProduct] = useState(false);
  const [showRecs, setShowRecs] = useState(false);
    const [newProduct, setNewProduct] = useState({ name: '', gamme_id: '', description: '', category: '', indications: '', compositions: '', usage_advice: '' });
  const [currentRecs, setCurrentRecs] = useState([]);
  const [selectedRecs, setSelectedRecs] = useState([]);
  const [createdProductId, setCreatedProductId] = useState(null);

  // 1. Fetch initial data
  useEffect(() => {
    setActiveTab(initialTab);
  }, [initialTab]);

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

  const filteredDelegues = delegues.filter(d => d.nom.toLowerCase().includes(searchQuery.toLowerCase()));
  const filteredMedecins = medecins.filter(m => m.nom.toLowerCase().includes(searchQuery.toLowerCase()) || m.specialite.toLowerCase().includes(searchQuery.toLowerCase()));
  const filteredPharmacies = pharmacies.filter(p => p.nom.toLowerCase().includes(searchQuery.toLowerCase()));
  const filteredProducts = products.filter(p => p.name.toLowerCase().includes(searchQuery.toLowerCase()));

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
        // Refresh products list
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
              <button 
                onClick={() => setActiveTab('produits')}
                className={`px-8 py-3 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all ${activeTab === 'produits' ? 'bg-md-primary text-white shadow-lg' : 'text-md-outline hover:bg-slate-50'}`}
              >
                Produits
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
                   {activeTab === 'produits' && (
                     <tr>
                        <th className="px-10 py-6">Produit</th>
                        <th className="px-10 py-6">Gamme</th>
                        <th className="px-10 py-6">Catégorie</th>
                        <th className="px-10 py-6 text-right">
                           <button 
                             onClick={() => setIsAddingProduct(true)}
                             className="px-6 py-2 bg-md-primary text-white rounded-full text-[10px] font-black uppercase tracking-widest"
                           >
                             + Nouveau Produit
                           </button>
                        </th>
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

                   {activeTab === 'produits' && filteredProducts.map(p => (
                     <tr key={p.id} className="hover:bg-slate-50 transition-colors">
                        <td className="px-10 py-6 flex items-center gap-4">
                           <div className="w-10 h-10 rounded-xl bg-md-primary/5 text-md-primary flex items-center justify-center"><PackageCheck size={18} /></div>
                           <span className="font-bold text-md-on-background">{p.name}</span>
                        </td>
                        <td className="px-10 py-6 text-xs font-bold uppercase tracking-widest opacity-60">Gamme #{p.gamme_id}</td>
                        <td className="px-10 py-6 font-black text-xs uppercase tracking-widest text-md-primary">{p.category || "N/A"}</td>
                        <td className="px-10 py-6 text-right opacity-40 italic text-[10px]">ID: {p.id}</td>
                     </tr>
                   ))}
                </tbody>
             </table>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Modal Ajout Produit - Version Fixée */}
      {isAddingProduct && typeof document !== 'undefined' && createPortal(
        <div className="fixed inset-0 z-[100000] flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 overflow-y-auto" style={{ pointerEvents: 'auto' }}>
          <div className="bg-white rounded-[32px] p-10 w-full max-w-xl shadow-2xl relative my-auto" style={{ color: '#000' }}>
            <h2 className="text-2xl font-bold mb-6 text-slate-900">Nouveau Produit</h2>
            
            <div className="space-y-4 max-h-[70vh] overflow-y-auto pr-2">
              <div>
                <label className="block text-[10px] font-bold uppercase opacity-50 mb-1">Nom du produit</label>
                <input 
                  type="text" 
                  value={newProduct.name} 
                  onChange={e => setNewProduct({...newProduct, name: e.target.value})}
                  className="w-full p-4 bg-slate-100 rounded-xl border-none outline-none focus:ring-2 ring-md-primary"
                  placeholder="Ex: CardioPlus"
                />
              </div>
              
              <div>
                <label className="block text-[10px] font-bold uppercase opacity-50 mb-1">Gamme</label>
                <select 
                  value={newProduct.gamme_id} 
                  onChange={e => setNewProduct({...newProduct, gamme_id: e.target.value})}
                  className="w-full p-4 bg-slate-100 rounded-xl border-none outline-none"
                >
                  <option value="">Choisir une gamme...</option>
                  {gammes && gammes.map(g => (
                    <option key={g.id} value={g.id}>{g.name}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-[10px] font-bold uppercase opacity-50 mb-1">Catégorie</label>
                <input 
                  type="text" 
                  value={newProduct.category} 
                  onChange={e => setNewProduct({...newProduct, category: e.target.value})}
                  className="w-full p-4 bg-slate-100 rounded-xl border-none outline-none"
                />
              </div>

              <div>
                <label className="block text-[10px] font-bold uppercase opacity-50 mb-1">Indications</label>
                <textarea 
                  value={newProduct.indications} 
                  onChange={e => setNewProduct({...newProduct, indications: e.target.value})}
                  className="w-full p-4 bg-slate-100 rounded-xl border-none outline-none focus:ring-2 ring-md-primary"
                  placeholder="Ex: Douleurs modérées..."
                />
              </div>

              <div>
                <label className="block text-[10px] font-bold uppercase opacity-50 mb-1">Composition</label>
                <textarea 
                  value={newProduct.compositions} 
                  onChange={e => setNewProduct({...newProduct, compositions: e.target.value})}
                  className="w-full p-4 bg-slate-100 rounded-xl border-none outline-none focus:ring-2 ring-md-primary"
                  placeholder="Ex: Paracétamol 500mg..."
                />
              </div>

              <div>
                <label className="block text-[10px] font-bold uppercase opacity-50 mb-1">Conseils d'utilisation</label>
                <textarea 
                  value={newProduct.usage_advice} 
                  onChange={e => setNewProduct({...newProduct, usage_advice: e.target.value})}
                  className="w-full p-4 bg-slate-100 rounded-xl border-none outline-none focus:ring-2 ring-md-primary"
                  placeholder="Ex: 1 comprimé toutes les 6 heures..."
                />
              </div>
            </div>

            <div className="flex gap-3 mt-8">
              <button 
                onClick={() => setIsAddingProduct(false)}
                className="flex-1 p-4 rounded-xl font-bold bg-slate-100 text-slate-600"
              >
                Annuler
              </button>
              <button 
                onClick={handleAddProduct}
                className="flex-[2] p-4 rounded-xl font-bold bg-md-primary text-white shadow-lg"
              >
                Ajouter et Recommander
              </button>
            </div>
          </div>
        </div>
      , document.body)}

      {/* Modal Recommandations IA */}
      {showRecs && typeof document !== 'undefined' && createPortal(
        <div className="fixed inset-0 z-[110] flex items-center justify-center p-4 md:p-6" style={{ backgroundColor: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(10px)' }}>
          <div className="bg-white rounded-[40px] p-8 md:p-12 w-full max-w-4xl shadow-2xl space-y-10 relative z-[1100] max-h-[90vh] overflow-y-auto">
            <div className="space-y-2">
              <span className="text-[10px] font-black text-md-primary uppercase tracking-[0.4em]">Analyse IA DSO3</span>
              <h2 className="text-4xl font-black uppercase tracking-tighter">Délégués Recommandés</h2>
              <p className="text-md-on-surface-variant font-bold opacity-60">Voici les profils les plus adaptés pour le produit <span className="text-md-primary uppercase">{newProduct.name}</span> selon leur expertise et leurs scores.</p>
            </div>

            <div className="grid grid-cols-1 gap-4">
              {!currentRecs || currentRecs.length === 0 ? (
                <div className="p-10 text-center border-2 border-dashed rounded-3xl opacity-40 font-bold uppercase tracking-widest">Aucun délégué expert trouvé pour cette gamme</div>
              ) : currentRecs.map(rec => (
                <div 
                  key={rec.delegate_id} 
                  onClick={() => {
                    if (selectedRecs.includes(rec.delegate_id)) {
                      setSelectedRecs(selectedRecs.filter(id => id !== rec.delegate_id));
                    } else {
                      setSelectedRecs([...selectedRecs, rec.delegate_id]);
                    }
                  }}
                  className={`p-6 rounded-3xl border-2 transition-all cursor-pointer flex items-center justify-between ${selectedRecs.includes(rec.delegate_id) ? 'border-md-primary bg-md-primary/5 shadow-md' : 'border-md-outline/10 hover:border-md-primary/30'}`}
                >
                  <div className="flex items-center gap-6">
                    <div className={`w-12 h-12 rounded-2xl flex items-center justify-center font-black text-white ${selectedRecs.includes(rec.delegate_id) ? 'bg-md-primary' : 'bg-slate-300'}`}>
                      {rec.delegate_name ? rec.delegate_name[0] : '?'}
                    </div>
                    <div>
                      <p className="font-black text-lg uppercase tracking-tight">{rec.delegate_name}</p>
                      <p className="text-[10px] font-bold text-md-primary uppercase tracking-widest">Expertise: {rec.expertise}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-[10px] font-black uppercase opacity-40">Score Moyen</p>
                    <p className="text-2xl font-black text-emerald-500">{rec.score}%</p>
                  </div>
                </div>
              ))}
            </div>

            <div className="flex gap-4 pt-6">
              <button onClick={() => setShowRecs(false)} className="flex-1 h-16 rounded-3xl font-black uppercase tracking-widest text-[11px] bg-slate-100 hover:bg-slate-200 transition-colors">Plus tard</button>
              <button 
                onClick={handleConfirmRecs}
                disabled={!selectedRecs || selectedRecs.length === 0}
                className="flex-[2] h-16 rounded-3xl font-black uppercase tracking-widest text-[11px] bg-md-primary text-white shadow-xl shadow-md-primary/25 disabled:opacity-50 disabled:grayscale hover:opacity-90 transition-all"
              >
                Affecter {selectedRecs?.length || 0} Délégué(s)
              </button>
            </div>
          </div>
        </div>
      , document.body)}
    </div>
  );
}
