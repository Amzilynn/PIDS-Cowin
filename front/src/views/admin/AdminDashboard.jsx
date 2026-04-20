import React, { useState, useEffect } from 'react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, 
  AreaChart, Area, PieChart, Pie, Cell, LineChart, Line, Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis
} from 'recharts';
import { 
  Users, 
  TrendingUp, 
  Target, 
  Award, 
  Search, 
  Filter, 
  MoreHorizontal,
  ChevronRight,
  Download,
  Calendar,
  Zap,
  Map as MapIcon,
  PackageCheck,
  Star,
  Activity,
  AlertCircle,
  Clock,
  ArrowUpRight,
  ArrowDownRight,
  ShieldCheck,
  LayoutDashboard,
  BarChart3,
  Settings,
  User,
  Edit,
  Trash2
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useLocation, useNavigate } from 'react-router-dom';
import { MapContainer, TileLayer, Marker, Popup, Polyline } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

// Correction des icônes Leaflet par défaut
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

// Mock Data
const annualPerformance = [
  { mois: 'Jan', medical: 4000, commercial: 2400 }, { mois: 'Fév', medical: 3000, commercial: 1398 },
  { mois: 'Mar', medical: 2000, commercial: 9800 }, { mois: 'Avr', medical: 2780, commercial: 3908 },
  { mois: 'Mai', medical: 1890, commercial: 4800 }, { mois: 'Juin', medical: 2390, commercial: 3800 },
  { mois: 'Juil', medical: 3490, commercial: 4300 }, { mois: 'Août', medical: 4200, commercial: 5100 },
  { mois: 'Sep', medical: 3800, commercial: 4600 }, { mois: 'Oct', medical: 4500, commercial: 5800 },
  { mois: 'Nov', medical: 4800, commercial: 6200 }, { mois: 'Déc', medical: 5200, commercial: 7000 },
];

// Les donnees des delegues seront recuperees dynamiquement

const radarData = [
  { item: 'Connaissance Produit', value: 85, full: 100 },
  { item: 'Communication', value: 92, full: 100 },
  { item: 'Argumentation', value: 78, full: 100 },
  { item: 'Gestion Objections', value: 65, full: 100 },
  { item: 'Présentation', value: 88, full: 100 },
];

const visits = [
  { id: 1, praticien: "Dr. Martin", spé: "Cardiologue", heure: "09:00", pos: [48.8566, 2.3522], prio: "Haute" },
  { id: 2, praticien: "Pharmacie Elite", spé: "Officine", heure: "11:30", pos: [48.8600, 2.3400], prio: "Moyenne" },
  { id: 3, praticien: "Clinique Atlas", spé: "Généraliste", heure: "14:15", pos: [48.8700, 2.3600], prio: "Basse" },
];

const DSO3_API_URL = import.meta.env.VITE_DSO3_API_URL || 'http://127.0.0.1:8000';

export default function AdminDashboard() {
  const location = useLocation();
  const navigate = useNavigate();
  const path = location.pathname.split('/').pop();
  
  // Synchronisation auto de l'onglet avec l'URL
  const activeTab = ['stats', 'delegues'].includes(path) ? path : 'generale';

  const [optimizing, setOptimizing] = useState(false);
   const [delegateForm, setDelegateForm] = useState({ name: '', expertise: '', interests: '', specification: '', user_email: '', user_password: '' });
   const [productForm, setProductForm] = useState({ name: '', category: '', description: '' });
   const [adminLoading, setAdminLoading] = useState({ delegate: false, product: false });
   const [adminError, setAdminError] = useState('');
   const [adminSuccess, setAdminSuccess] = useState('');
   const [productRecommendations, setProductRecommendations] = useState([]);
   const [delegatesList, setDelegatesList] = useState([]);

   const fetchDelegates = async () => {
      try {
         const res = await fetch(`${DSO3_API_URL}/delegates/`);
         const data = await res.json();
         setDelegatesList(data.map(d => ({
            id: d.id,
            nom: d.name,
            role: d.specification || 'Médical',
            score: Math.floor(Math.random() * 20 + 80),
            eval: Math.floor(Math.random() * 30 + 10),
            statut: 'Actif'
         })));
      } catch (e) {
         console.error("Erreur récupération délégués", e);
      }
   };

   useEffect(() => {
      fetchDelegates();
   }, []);

   const deleteDelegate = async (id) => {
      if (!window.confirm("Voulez-vous vraiment supprimer cet utilisateur ?")) return;
      try {
         const res = await fetch(`${DSO3_API_URL}/delegates/${id}`, { method: 'DELETE' });
         if (res.ok) {
            setDelegatesList(prev => prev.filter(d => d.id !== id));
            setAdminSuccess('Utilisateur supprimé avec succès.');
         } else {
            const err = await res.json().catch(() => ({}));
            setAdminError(err.detail || "Erreur lors de la suppression.");
         }
      } catch (e) {
         setAdminError('Erreur de connexion serveur.');
      }
   };

   const handleDelegateInput = (event) => {
      const { name, value } = event.target;
      setDelegateForm((previous) => ({ ...previous, [name]: value }));
   };

   const handleProductInput = (event) => {
      const { name, value } = event.target;
      setProductForm((previous) => ({ ...previous, [name]: value }));
   };

   const submitDelegate = async (event) => {
      event.preventDefault();
      setAdminError('');
      setAdminSuccess('');
      setAdminLoading((previous) => ({ ...previous, delegate: true }));

      try {
         const response = await fetch(`${DSO3_API_URL}/delegates/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(delegateForm),
         });

         if (!response.ok) {
            const payload = await response.json().catch(() => ({}));
            throw new Error(payload?.detail || 'Erreur création délégué.');
         }

         setAdminSuccess('Délégué créé avec succès.');
         setDelegateForm({ name: '', expertise: '', interests: '', specification: '', user_email: '', user_password: '' });
         fetchDelegates();
      } catch (error) {
         setAdminError(error.message || 'Erreur inconnue.');
      } finally {
         setAdminLoading((previous) => ({ ...previous, delegate: false }));
      }
   };

   const submitProduct = async (event) => {
      event.preventDefault();
      setAdminError('');
      setAdminSuccess('');
      setAdminLoading((previous) => ({ ...previous, product: true }));

      try {
         const response = await fetch(`${DSO3_API_URL}/products/product`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(productForm),
         });

         if (!response.ok) {
            const payload = await response.json().catch(() => ({}));
            throw new Error(payload?.detail || 'Erreur création produit.');
         }

         const payload = await response.json();
         setProductRecommendations(payload.recommendations || []);
         setAdminSuccess('Produit créé et matching généré.');
         setProductForm({ name: '', category: '', description: '' });
      } catch (error) {
         setAdminError(error.message || 'Erreur inconnue.');
      } finally {
         setAdminLoading((previous) => ({ ...previous, product: false }));
      }
   };

  const renderGenerale = () => (
    <div className="space-y-10 animate-fade-in">
       {/* KPI Cards Row */}
       <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          {[
            { label: 'Délégués Actifs', value: '1 284', icon: Users, trend: '+12%', color: 'bg-md-primary/10 text-md-primary' },
            { label: 'Score Moyen', value: '86.4%', icon: Star, trend: '+4.2%', color: 'bg-amber-100 text-amber-700' },
            { label: 'Sessions Direct', value: '156', icon: Zap, trend: '-2.1%', color: 'bg-md-secondary-container text-md-on-secondary-container' },
            { label: 'Visites Planifiées', value: '432', icon: MapIcon, trend: '+18.5%', color: 'bg-sky-100 text-sky-700' },
          ].map((kpi, i) => (
            <motion.div 
               whileHover={{ y: -8 }}
               key={i} 
               className="md-card flex flex-col gap-4 relative overflow-hidden"
            >
               <div className="flex items-center justify-between relative z-10">
                  <div className={`w-12 h-12 rounded-2xl ${kpi.color} flex items-center justify-center shadow-sm`}>
                     <kpi.icon size={22} />
                  </div>
                  <div className={`flex items-center gap-1 text-[11px] font-black uppercase ${kpi.trend.startsWith('+') ? 'text-emerald-500' : 'text-rose-500'}`}>
                     {kpi.trend.startsWith('+') ? <ArrowUpRight size={14} /> : <ArrowDownRight size={14} />} {kpi.trend}
                  </div>
               </div>
               <div className="relative z-10">
                  <p className="text-[10px] font-black text-md-on-surface-variant uppercase tracking-[0.2em] opacity-60 mb-1">{kpi.label}</p>
                  <h3 className="text-3xl font-black text-md-on-background tracking-tighter">{kpi.value}</h3>
               </div>
               <div className="absolute -right-4 -bottom-4 w-24 h-24 opacity-5 pointer-events-none grayscale">
                  <kpi.icon size={96} />
               </div>
            </motion.div>
          ))}
       </div>

       {/* Performance Graph */}
       <div className="md-card p-10 flex flex-col gap-8">
          <div className="flex items-center justify-between">
             <div className="space-y-1">
                <h3 className="text-xl font-black text-md-on-background tracking-tight uppercase">Performance Analytique du Réseau</h3>
                <p className="text-xs font-bold text-md-on-surface-variant opacity-60">Engagement comparatif Médical vs Commercial — 12 derniers mois</p>
             </div>
             <div className="flex gap-6">
                <div className="flex items-center gap-3">
                   <div className="w-3 h-3 rounded-full bg-md-primary shadow-[0_0_8px_var(--color-md-primary)]" />
                   <span className="text-[10px] font-black uppercase tracking-widest text-md-on-surface-variant">Délégués Médicaux</span>
                </div>
                <div className="flex items-center gap-3">
                   <div className="w-3 h-3 rounded-full bg-md-on-background" />
                   <span className="text-[10px] font-black uppercase tracking-widest text-md-on-surface-variant">Commerciaux</span>
                </div>
             </div>
          </div>
          
          <div className="h-[400px] w-full mt-4">
             <ResponsiveContainer width="100%" height="100%">
                <LineChart data={annualPerformance}>
                   <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--color-md-outline)" strokeOpacity={0.1} />
                   <XAxis dataKey="mois" axisLine={false} tickLine={false} tick={{ fontSize: 11, fontWeight: 900, fill: 'var(--color-md-on-surface-variant)' }} dy={10} />
                   <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 11, fontWeight: 900, fill: 'var(--color-md-on-surface-variant)' }} />
                   <Tooltip 
                      contentStyle={{ borderRadius: '24px', border: 'none', boxShadow: '0 10px 40px -10px rgba(0,0,0,0.1)', padding: '20px', backgroundColor: 'rgba(255,255,255,0.9)', backdropFilter: 'blur(10px)' }}
                      itemStyle={{ fontWeight: 900, fontSize: '13px', textTransform: 'uppercase' }}
                   />
                   <Line type="monotone" dataKey="medical" stroke="var(--color-md-primary)" strokeWidth={6} dot={{ r: 6, fill: 'var(--color-md-primary)', strokeWidth: 3, stroke: '#FFFFFF' }} activeDot={{ r: 10, strokeWidth: 0 }} />
                   <Line type="monotone" dataKey="commercial" stroke="var(--color-md-on-background)" strokeWidth={6} dot={{ r: 6, fill: 'var(--color-md-on-background)', strokeWidth: 3, stroke: '#FFFFFF' }} activeDot={{ r: 10, strokeWidth: 0 }} />
                </LineChart>
             </ResponsiveContainer>
          </div>
       </div>

    </div>
  );

  const renderDelegates = () => (
    <div className="animate-fade-in space-y-10">
       <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <form onSubmit={submitDelegate} className="md-card space-y-4">
             <h3 className="text-xl font-black text-md-on-background uppercase">Ajouter un délégué</h3>
             <input
               name="name"
               value={delegateForm.name}
               onChange={handleDelegateInput}
               required
               placeholder="Nom du délégué"
               className="w-full h-12 bg-white rounded-xl border border-md-outline/20 px-4 text-sm font-semibold"
             />
             <input
               name="expertise"
               value={delegateForm.expertise}
               onChange={handleDelegateInput}
               required
               placeholder="Expertise (ex: cardiologie, diabète)"
               className="w-full h-12 bg-white rounded-xl border border-md-outline/20 px-4 text-sm font-semibold"
             />
             <input
               name="interests"
               value={delegateForm.interests}
               onChange={handleDelegateInput}
               required
               placeholder="Intérêts (ex: prévention, innovation)"
               className="w-full h-12 bg-white rounded-xl border border-md-outline/20 px-4 text-sm font-semibold"
             />
             <select
               name="specification"
               value={delegateForm.specification}
               onChange={handleDelegateInput}
               required
               className="w-full h-12 bg-white rounded-xl border border-md-outline/20 px-4 text-sm font-semibold text-md-on-surface-variant focus:text-md-on-background appearance-none"
             >
               <option value="" disabled>Spécialité (Médical/Commercial)</option>
               <option value="Médical">Médical</option>
               <option value="Commercial">Commercial</option>
             </select>
                   <input
                      name="user_email"
                      type="email"
                      value={delegateForm.user_email}
                      onChange={handleDelegateInput}
                      required
                      placeholder="E-mail du compte utilisateur"
                      className="w-full h-12 bg-white rounded-xl border border-md-outline/20 px-4 text-sm font-semibold"
                   />
                   <input
                      name="user_password"
                      type="password"
                      value={delegateForm.user_password}
                      onChange={handleDelegateInput}
                      required
                      placeholder="Mot de passe du compte"
                      className="w-full h-12 bg-white rounded-xl border border-md-outline/20 px-4 text-sm font-semibold"
                   />
             <button disabled={adminLoading.delegate} className="btn-primary !h-11 !text-[10px] uppercase tracking-widest">
               {adminLoading.delegate ? 'Création...' : 'Créer Délégué'}
             </button>
          </form>

          <form onSubmit={submitProduct} className="md-card space-y-4">
             <h3 className="text-xl font-black text-md-on-background uppercase">Ajouter un produit</h3>
             <input
               name="name"
               value={productForm.name}
               onChange={handleProductInput}
               required
               placeholder="Nom produit"
               className="w-full h-12 bg-white rounded-xl border border-md-outline/20 px-4 text-sm font-semibold"
             />
             <input
               name="category"
               value={productForm.category}
               onChange={handleProductInput}
               required
               placeholder="Catégorie"
               className="w-full h-12 bg-white rounded-xl border border-md-outline/20 px-4 text-sm font-semibold"
             />
             <textarea
               name="description"
               value={productForm.description}
               onChange={handleProductInput}
               required
               rows={3}
               placeholder="Description produit"
               className="w-full bg-white rounded-xl border border-md-outline/20 px-4 py-3 text-sm font-semibold resize-none"
             />
             <button disabled={adminLoading.product} className="btn-primary !h-11 !text-[10px] uppercase tracking-widest">
               {adminLoading.product ? 'Matching...' : 'Créer Produit + Matching'}
             </button>
          </form>
       </div>

       {adminError ? (
          <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-rose-700 font-bold">
             {adminError}
          </div>
       ) : null}

       {adminSuccess ? (
          <div className="rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-emerald-700 font-bold">
             {adminSuccess}
          </div>
       ) : null}

       {productRecommendations.length > 0 ? (
          <div className="md-card">
             <h3 className="text-lg font-black uppercase text-md-on-background mb-4">Résultat matching produit</h3>
             <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {productRecommendations.map((recommendation, index) => (
                   <div key={`${recommendation.delegate_id}-${index}`} className="p-4 bg-white rounded-2xl border border-md-outline/10">
                      <p className="text-[10px] font-black uppercase tracking-widest text-md-primary">Rang {index + 1}</p>
                      <p className="text-lg font-black text-md-on-background">{recommendation.delegate_name}</p>
                      <p className="text-xs font-bold text-md-on-surface-variant">ID: {recommendation.delegate_id}</p>
                      <p className="text-2xl font-black text-md-on-background mt-2">{(recommendation.score * 100).toFixed(1)}%</p>
                   </div>
                ))}
             </div>
          </div>
       ) : null}

       <div className="md-card">
          <h2 className="text-3xl font-black text-md-on-background uppercase mb-2">Registre Complet du Réseau</h2>
          <p className="text-md-on-surface-variant/60 font-bold italic mb-6">Accès direct au suivi individuel et aux performances par territoire.</p>
       </div>
       {/* Delegates Registry Table */}
       <div className="md-card !p-0 overflow-hidden">
          <div className="p-10 border-b border-md-outline/5 flex items-center justify-between bg-md-surface-container-low/30 backdrop-blur-md">
             <h3 className="text-xl font-black text-md-on-background tracking-tight uppercase">Registre des Délégués Actifs</h3>
             <div className="flex gap-4">
                <div className="relative group">
                   <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-md-outline/40 group-focus-within:text-md-primary transition-colors" size={16} />
                   <input type="text" placeholder="Rechercher un délégué..." className="pl-12 pr-6 h-12 bg-white rounded-pill text-xs font-bold outline-none focus:ring-4 focus:ring-md-primary/10 border border-md-outline/10 w-72 transition-all shadow-sm" />
                </div>
                <button className="btn-tonal !px-6 !h-12 text-[11px] font-black uppercase tracking-widest">
                   <Filter size={18} /> Filtrer
                </button>
             </div>
          </div>
          
          <div className="overflow-x-auto">
             <table className="w-full text-left">
                <thead className="bg-md-surface-container text-[10px] font-black text-md-on-surface-variant uppercase tracking-[0.3em]">
                   <tr>
                      <th className="px-10 py-6">Nom Complet</th>
                      <th className="px-10 py-6">Division</th>
                      <th className="px-10 py-6">Score Global</th>
                      <th className="px-10 py-6">Sessions</th>
                      <th className="px-10 py-6">Statut</th>
                      <th className="px-10 py-6 text-right">Actions</th>
                   </tr>
                </thead>
                <tbody className="divide-y divide-md-outline/5">
                   {delegatesList.map((d) => (
                      <tr key={d.id} className="group hover:bg-white transition-colors">
                         <td className="px-10 py-6">
                            <div className="flex items-center gap-4">
                               <div className="w-10 h-10 rounded-pill bg-md-primary/10 text-md-primary flex items-center justify-center font-black text-xs border border-md-primary/10">
                                  {d.nom.charAt(4)}
                               </div>
                               <span className="text-sm font-black text-md-on-background">{d.nom}</span>
                            </div>
                         </td>
                         <td className="px-10 py-6">
                            <span className={`text-[10px] font-black uppercase px-4 py-1.5 rounded-pill ${d.role === 'Médical' ? 'bg-sky-50 text-sky-700' : 'bg-emerald-50 text-emerald-700'}`}>
                               {d.role}
                            </span>
                         </td>
                         <td className="px-10 py-6 text-sm font-black text-md-on-background">{d.score}%</td>
                         <td className="px-10 py-6 text-sm font-bold text-md-on-surface-variant opacity-60">{d.eval} eval.</td>
                         <td className="px-10 py-6">
                            <div className="flex items-center gap-2 text-emerald-500 font-black text-[10px] uppercase tracking-widest">
                               <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse shadow-[0_0_8px_#10b981]" /> {d.statut}
                            </div>
                         </td>
                         <td className="px-10 py-6 text-right">
                            <div className="flex items-center justify-end gap-3 transition-opacity">
                               <button className="p-3 bg-sky-50 text-sky-600 rounded-2xl hover:bg-sky-500 hover:text-white transition-all shadow-sm">
                                  <Edit size={16} />
                               </button>
                               <button onClick={() => deleteDelegate(d.id)} className="p-3 bg-rose-50 text-rose-600 rounded-2xl hover:bg-rose-500 hover:text-white transition-all shadow-sm">
                                  <Trash2 size={16} />
                               </button>
                            </div>
                         </td>
                      </tr>
                   ))}
                </tbody>
             </table>
          </div>

          <div className="p-10 flex items-center justify-between border-t border-md-outline/5 bg-md-surface-container-low/30 backdrop-blur-md">
             <p className="text-[10px] font-black text-md-on-surface-variant uppercase tracking-widest opacity-60">1-4 sur 1 284 membres du réseau</p>
             <div className="flex gap-3">
                <button className="btn-tonal !px-6 !py-2.5 !text-[10px] !font-black uppercase tracking-widest border border-md-outline/10 shadow-sm">Précédent</button>
                <button className="btn-tonal !px-6 !py-2.5 !text-[10px] !font-black uppercase tracking-widest border border-md-outline/10 shadow-sm">Suivant</button>
             </div>
          </div>
       </div>
    </div>
  );

  const renderPerformances = () => (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-10 animate-fade-in">
       <div className="md-card p-10 flex flex-col gap-10">
          <div className="space-y-1">
              <h3 className="text-xl font-black text-md-on-background tracking-tight uppercase">Compétences Globales du Réseau</h3>
              <p className="text-xs font-bold text-md-on-surface-variant opacity-60 italic">Analyse radar des 5 piliers métriques de l'Optimiseur Stratégique de Visite</p>
          </div>
          <div className="h-[400px]">
             <ResponsiveContainer width="100%" height="100%">
               <RadarChart cx="50%" cy="50%" outerRadius="80%" data={radarData}>
                  <PolarGrid stroke="var(--color-md-outline)" strokeOpacity={0.1} />
                  <PolarAngleAxis dataKey="item" tick={{ fontSize: 10, fontWeight: 900, fill: 'var(--color-md-on-background)', textTransform: 'uppercase' }} />
                  <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} axisLine={false} />
                  <Radar name="Moyenne Réseau" dataKey="value" stroke="var(--color-md-primary)" fill="var(--color-md-primary)" fillOpacity={0.5} strokeWidth={5} />
                  <Tooltip contentStyle={{ borderRadius: '24px', textTransform: 'uppercase', fontBlack: '900' }} />
               </RadarChart>
             </ResponsiveContainer>
          </div>
       </div>

       <div className="md-card p-10 flex flex-col gap-10">
          <div className="space-y-1">
              <h3 className="text-xl font-black text-md-on-background tracking-tight uppercase">Comparaison par Module Métier</h3>
              <p className="text-xs font-bold text-md-on-surface-variant opacity-60 italic">Scores moyens par module (Training, Presentation, Produit)</p>
          </div>
          <div className="h-[400px]">
             <ResponsiveContainer width="100%" height="100%">
                <BarChart data={[
                   { module: 'Training Simulator', medical: 85, commercial: 70 },
                   { module: 'Presentation Simulator', medical: 62, commercial: 92 },
                   { module: 'Product Recommender', medical: 90, commercial: 85 }
                ]}>
                   <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--color-md-outline)" strokeOpacity={0.1} />
                   <XAxis dataKey="module" axisLine={false} tickLine={false} tick={{ fontSize: 10, fontWeight: 900, fill: 'var(--color-md-on-background)' }} />
                   <YAxis hide />
                   <Tooltip cursor={{ fill: 'transparent' }} contentStyle={{ borderRadius: '24px', textTransform: 'uppercase' }} />
                   <Bar dataKey="medical" fill="var(--color-md-primary)" radius={[20, 20, 0, 0]} name="Médical" />
                   <Bar dataKey="commercial" fill="var(--color-md-on-background)" radius={[20, 20, 0, 0]} name="Commercial" />
                </BarChart>
             </ResponsiveContainer>
          </div>
       </div>
       
       <div className="md:col-span-2 md-card p-10">
          <h3 className="text-xl font-black text-md-on-background tracking-tight mb-10 flex items-center gap-4 uppercase">
             Leaderboard de l'Excellence <span className="p-2 bg-amber-500/10 rounded-xl text-amber-500 shadow-sm"><Award size={24} /></span>
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
             {[...delegatesList].sort((a,b) => b.score - a.score).map((d, i) => (
                <div key={i} className="p-8 bg-md-surface-container-low rounded-[48px] flex flex-col items-center gap-6 text-center group transition-all hover:bg-white hover:shadow-2xl hover:scale-105 border border-md-outline/5">
                    <div className="relative">
                       <div className="w-24 h-24 rounded-full bg-md-primary/10 flex items-center justify-center text-md-primary font-black text-2xl border-4 border-white shadow-xl">
                          {d.nom.charAt(4)}
                       </div>
                       <div className="absolute -bottom-2 -right-2 w-10 h-10 rounded-full bg-md-on-background border-4 border-white flex items-center justify-center text-white font-black text-xs shadow-lg">
                          #{i+1}
                       </div>
                    </div>
                    <div className="space-y-1">
                       <p className="text-base font-black text-md-on-background uppercase">{d.nom}</p>
                       <p className="text-[11px] font-black text-md-primary uppercase tracking-[0.2em]">{d.score}% Score Global</p>
                    </div>
                    <div className="w-full h-1.5 bg-md-primary/10 rounded-full overflow-hidden">
                       <motion.div initial={{ width: 0 }} animate={{ width: `${d.score}%` }} className="h-full bg-md-primary rounded-full shadow-lg shadow-md-primary/20" />
                    </div>
                </div>
             ))}
          </div>
       </div>
    </div>
  );


  return (
    <div className="space-y-12 animate-fade-in-up pb-24 relative">
      {/* Glow Décoratif Central */}
      <div className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-md-primary/5 blur-[120px] rounded-full pointer-events-none -z-10" />
      
      {/* Header Central avec Logo Intégré */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-10 relative z-10">
        <div className="space-y-4">
           <div className="flex items-center gap-4 mb-2">
               <div className="w-10 h-10 rounded-2xl bg-md-primary flex items-center justify-center text-white shadow-lg shadow-md-primary/30">
                  <ShieldCheck size={24} />
               </div>
               <h2 className="text-[11px] font-black text-md-primary uppercase tracking-[0.5em] leading-none">Console de Supervision Centrale</h2>
           </div>
           <h1 className="text-6xl font-black text-md-on-background tracking-tighter leading-[0.9] uppercase">Tableau de <br/><span className="text-md-primary italic lowercase">bord digital.</span></h1>
           <p className="text-md-on-surface-variant/60 font-bold text-lg italic tracking-tight">Analyse temps réel de l'intelligence terrain et des scores globaux.</p>
        </div>
        
        <div className="flex items-center gap-6 p-4 bg-white/60 backdrop-blur-3xl rounded-[32px] border border-white shadow-2xl">
           <div className="w-12 h-12 bg-md-primary/10 rounded-[18px] flex items-center justify-center text-md-primary">
              <Calendar size={24} />
           </div>
           <div className="pr-6">
              <p className="text-[10px] font-black text-md-primary uppercase tracking-widest opacity-60 mb-0.5">Session Administrative</p>
              <span className="text-sm font-black text-md-on-background uppercase tracking-tighter">
                 {new Date().toLocaleDateString('fr-FR', { day: '2-digit', month: 'long', year: 'numeric' }).toUpperCase()}
              </span>
           </div>
        </div>
      </div>


      {/* Rendu des Onglets avec Animation */}
      <div className="relative z-10 w-full min-h-[600px]">
         <AnimatePresence mode="wait">
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, y: 30, scale: 0.98 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -30, scale: 0.98 }}
              transition={{ duration: 0.6, ease: [0.2, 0, 0, 1] }}
            >
               {activeTab === 'generale' && renderGenerale()}
               {activeTab === 'stats' && renderPerformances()}
               {activeTab === 'delegues' && renderDelegates()}
            </motion.div>
         </AnimatePresence>
      </div>
    </div>
  );
}
