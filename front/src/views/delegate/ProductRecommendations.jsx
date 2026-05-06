import React, { useState, useEffect } from 'react';
import { 
  PackageCheck, 
  ChevronRight, 
  Loader2,
  AlertCircle
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '../../context/AuthContext';

// We need two different ports for the different DSO services
const API_DSO3 = 'http://localhost:8003'; // Expertise & Recommendations
const API_DSO1 = 'http://localhost:8001'; // Training & Product Details

export default function ProductRecommendations() {
  const { user } = useAuth();
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [detailsLoading, setDetailsLoading] = useState(false);
  const [detailsError, setDetailsError] = useState(null);
  const [isDetailsOpen, setIsDetailsOpen] = useState(false);

  useEffect(() => {
    if (!user?.user_id) return;

    const fetchRecommendations = async () => {
      try {
        setLoading(true);
        // Call DSO3 (8003) for personalized recommendations
        const response = await fetch(`${API_DSO3}/api/delegate/${user.user_id}`);
        if (!response.ok) throw new Error('Erreur lors du chargement des recommandations');
        
        const data = await response.json();
        setRecommendations(data);
      } catch (err) {
        console.error(err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchRecommendations();
  }, [user]);

  const openProductDetails = async (productId) => {
    setIsDetailsOpen(true);
    setDetailsLoading(true);
    setDetailsError(null);
    try {
      // Call DSO1 (8001) for specific product sheet details
      const response = await fetch(`${API_DSO1}/api/training/products/${productId}`);
      if (!response.ok) throw new Error('Erreur lors du chargement du produit');
      const data = await response.json();
      setSelectedProduct(data);
    } catch (err) {
      setDetailsError(err.message);
      setSelectedProduct(null);
    } finally {
      setDetailsLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="h-full flex flex-col items-center justify-center space-y-4">
        <Loader2 className="w-12 h-12 text-md-primary animate-spin" />
        <p className="text-md-on-surface-variant font-bold animate-pulse uppercase tracking-widest">Analyse de vos scores en cours...</p>
      </div>
    );
  }

  return (
    <div className="space-y-12 animate-fade-in pb-20 relative z-10">
      
      {/* Background Graphic Signature */}
      <div className="fixed top-0 right-0 w-[600px] h-[600px] organic-glow bg-md-primary/5 rounded-full pointer-events-none -z-10" />

      {/* Header Info */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-10">
         <div className="space-y-4 flex-1">
            <div className="flex items-center gap-4">
               <div className="w-12 h-12 rounded-2xl bg-md-secondary-container text-md-primary flex items-center justify-center shadow-lg shadow-md-primary/10">
                  <PackageCheck size={26} strokeWidth={2.5} />
               </div>
               <span className="text-[11px] font-black text-md-primary uppercase tracking-[0.5em] leading-none">IA de Recommandation</span>
            </div>
            <h1 className="text-6xl font-black text-md-on-background tracking-tighter leading-[0.9] uppercase">Produits <br/><span className="text-md-primary italic lowercase">suggérés.</span></h1>
            <p className="text-md-on-surface-variant font-bold text-xl leading-relaxed max-w-xl mt-4 opacity-70 italic tracking-tight">
               Basé sur vos performances réelles lors des dernières simulations.
            </p>
         </div>
      </div>

      {error && (
        <div className="bg-rose-50 border border-rose-200 p-6 rounded-3xl flex items-center gap-4 text-rose-600">
          <AlertCircle />
          <p className="font-bold">{error}</p>
        </div>
      )}

      {!loading && recommendations.length === 0 && !error && (
        <div className="bg-md-surface-container p-12 rounded-[40px] text-center space-y-4 border-2 border-dashed border-md-outline/20">
          <PackageCheck size={48} className="mx-auto text-md-outline opacity-20" />
          <p className="text-xl font-bold text-md-on-surface-variant">Aucune recommandation pour le moment.</p>
          <p className="text-sm opacity-60">Réalisez des simulations pour que l'IA puisse analyser vos points forts.</p>
        </div>
      )}

      {/* Grille de Produits */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-10 relative z-10 pb-12">
         <AnimatePresence mode="popLayout">
            {recommendations.map((p, i) => (
               <motion.div 
                 layout
                 key={p.recommendation_id} 
                 initial={{ opacity: 0, scale: 0.9 }}
                 animate={{ opacity: 1, scale: 1 }}
                 transition={{ delay: i * 0.05 }}
                 className="md-card p-10 flex flex-col gap-10 group bg-white border-none shadow-xl hover:shadow-2xl transition-all duration-500 relative overflow-hidden"
               >
                  <div className="absolute top-0 right-0 w-32 h-32 bg-md-primary/5 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2 group-hover:scale-150 transition-transform duration-700" />
                  
                  <div className="flex items-center justify-between relative z-10">
                     <div className={`w-14 h-14 rounded-[20px] bg-md-primary text-white flex items-center justify-center shadow-inner group-hover:rotate-12 transition-transform`}>
                        <PackageCheck size={28} strokeWidth={2} />
                     </div>
                     <div className="text-right">
                        <p className="text-[10px] font-black text-md-on-surface-variant uppercase tracking-widest opacity-40 mb-1 leading-none">Score Match</p>
                        <p className="text-3xl font-black text-md-primary tracking-tighter">{p.score}%</p>
                     </div>
                  </div>
                  
                  <div className="flex-1 space-y-3 relative z-10">
                     <h4 className="text-2xl font-black text-md-on-background tracking-tighter leading-none uppercase">{p.product_name}</h4>
                     <p className="text-[11px] font-black text-md-primary uppercase tracking-[0.3em] underline underline-offset-4 decoration-md-primary/20">Gamme: {p.gamme_name || 'Sans Gamme'}</p>
                     <p className="text-[10px] font-black text-md-on-surface-variant uppercase tracking-[0.3em] opacity-60">Catégorie: {p.category || 'N/A'}</p>
                     <p className="text-xs font-bold text-md-on-surface-variant opacity-60 leading-relaxed italic mt-6 border-l-4 border-md-primary/20 pl-4">
                       {p.description || "Aucune description disponible."}
                     </p>
                  </div>

                  <button
                    onClick={() => openProductDetails(p.product_id)}
                    className="relative z-10 w-full btn-tonal !h-14 !rounded-2xl group flex items-center justify-between px-8 font-black uppercase text-[11px] tracking-widest"
                  >
                     <span>Fiche Produit</span>
                     <ChevronRight size={18} className="group-hover:translate-x-2 transition-transform" />
                  </button>
               </motion.div>
            ))}
         </AnimatePresence>
      </div>

      {isDetailsOpen && (
        <div className="fixed inset-0 z-[1000] flex items-center justify-center bg-black/70 p-6">
          <div className="bg-white rounded-[32px] p-8 w-full max-w-2xl shadow-2xl max-h-[85vh] overflow-y-auto relative">
            <button 
              onClick={() => { setIsDetailsOpen(false); setSelectedProduct(null); }}
              className="absolute top-6 right-6 text-slate-400 hover:text-slate-600 transition-colors"
            >
              <AlertCircle size={24} className="rotate-45" />
            </button>

            {detailsLoading && (
              <div className="h-40 flex items-center justify-center">
                <Loader2 className="w-10 h-10 text-md-primary animate-spin" />
              </div>
            )}
            {detailsError && (
              <div className="bg-rose-50 border border-rose-200 p-4 rounded-2xl text-rose-600 font-bold">
                {detailsError}
              </div>
            )}
            {!detailsLoading && !detailsError && selectedProduct && (
              <div className="space-y-6">
                <div>
                  <p className="text-[10px] font-black uppercase tracking-[0.3em] text-md-primary">Fiche Produit</p>
                  <h3 className="text-3xl font-black text-md-on-background uppercase tracking-tighter">{selectedProduct.name}</h3>
                  <div className="flex gap-4 mt-2">
                    <p className="text-xs font-bold text-md-on-surface-variant uppercase tracking-widest opacity-60">Gamme: {selectedProduct.gamme_name || 'Sans Gamme'}</p>
                    <p className="text-xs font-bold text-md-on-surface-variant uppercase tracking-widest opacity-60">Catégorie: {selectedProduct.category || 'N/A'}</p>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-8 pt-6 border-t border-slate-100">
                  <div className="space-y-6">
                    <div>
                      <p className="text-[10px] font-black uppercase tracking-widest opacity-40 mb-2">Description</p>
                      <p className="text-sm font-bold text-md-on-surface-variant leading-relaxed">{selectedProduct.description || 'Aucune description disponible.'}</p>
                    </div>
                    <div>
                      <p className="text-[10px] font-black uppercase tracking-widest opacity-40 mb-2">Indications</p>
                      <p className="text-sm font-bold text-md-on-surface-variant leading-relaxed">{selectedProduct.indications || 'Non renseigné.'}</p>
                    </div>
                  </div>
                  <div className="space-y-6">
                    <div>
                      <p className="text-[10px] font-black uppercase tracking-widest opacity-40 mb-2">Composition</p>
                      <p className="text-sm font-bold text-md-on-surface-variant leading-relaxed">{selectedProduct.compositions || 'Non renseigné.'}</p>
                    </div>
                    <div>
                      <p className="text-[10px] font-black uppercase tracking-widest opacity-40 mb-2">Conseils d'utilisation</p>
                      <p className="text-sm font-bold text-md-on-surface-variant leading-relaxed">{selectedProduct.usage_advice || 'Non renseigné.'}</p>
                    </div>
                  </div>
                </div>
              </div>
            )}

            <div className="flex justify-end mt-12">
              <button
                onClick={() => { setIsDetailsOpen(false); setSelectedProduct(null); }}
                className="px-10 h-12 rounded-xl bg-md-primary text-white font-black uppercase text-[10px] tracking-widest shadow-lg shadow-md-primary/20 hover:scale-105 transition-transform"
              >
                Fermer la fiche
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
