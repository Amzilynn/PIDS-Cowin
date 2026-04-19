import React, { useState, useEffect } from 'react';
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

const DSO3_API_URL = import.meta.env.VITE_DSO3_API_URL || 'http://127.0.0.1:8000';

function getColorByScore(score) {
  if (score >= 90) return "bg-emerald-500";
  if (score >= 80) return "bg-sky-500";
  if (score >= 70) return "bg-indigo-500";
  if (score >= 60) return "bg-amber-500";
  return "bg-rose-500";
}

export default function ProductRecommendations() {
  const location = useLocation();
  const query = new URLSearchParams(location.search);
  const subRole = query.get('sub') || 'medical';
  const authData = JSON.parse(localStorage.getItem('cw_auth') || '{}');
  const delegateId = query.get('id') || authData.delegate_id || 1;
  const [filter, setFilter] = useState('all');
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchRecommendations = async () => {
      try {
        const res = await fetch(`${DSO3_API_URL}/delegates/${delegateId}/recommended-products/new?limit=10`);
        const data = await res.json();
        if (data.items) {
          const mapped = data.items.map((item, index) => ({
            id: item.product_id || index,
            name: item.product_name,
            range: item.category,
            score: Math.round(item.score * 100),
            reason: item.description || "Aucune description disponible pour ce produit.",
            color: getColorByScore(Math.round(item.score * 100)),
            desc: item.description || "Aucune description disponible pour ce produit."
          }));
          setProducts(mapped);
        }
      } catch (err) {
        console.error("Erreur DSO3 API:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchRecommendations();
  }, [delegateId]);
 
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
               <span className="text-[11px] font-black text-md-primary uppercase tracking-[0.5em] leading-none text-md-primary">Assistant IA de Gamme</span>
            </div>
            <h1 className="text-6xl font-black text-md-on-background tracking-tighter leading-[0.9] uppercase">Gamme <br/><span className="text-md-primary italic lowercase">recommandée.</span></h1>
            <p className="text-md-on-surface-variant font-bold text-xl leading-relaxed max-w-xl mt-4 opacity-70 italic tracking-tight">
               Algorithmes prédictifs basés sur vos performances.
            </p>
         </div>

      </div>

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

    </div>
  );
}
