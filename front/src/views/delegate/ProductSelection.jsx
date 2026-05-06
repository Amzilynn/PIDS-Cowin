import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { motion, AnimatePresence } from 'framer-motion';
import { PackageSearch, ArrowRight, Activity, Pill, Dna, Hexagon, Component, ChevronLeft, ChevronRight, BrainCircuit, ShieldCheck } from 'lucide-react';

export default function ProductSelection() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [products, setProducts] = useState([]);
  const [selectedProductId, setSelectedProductId] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [gammes, setGammes] = useState([]);
  const [selectedGammeId, setSelectedGammeId] = useState("all");
  const [isLoading, setIsLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 12;

  // Random icons for products lacking specific metadata
  const productIcons = [Pill, Activity, Dna, Hexagon, Component];

  useEffect(() => {
    // Simulation du temps de chargement pour effet visuel
    Promise.all([
      fetch("http://localhost:8001/api/training/products").then(res => res.json()),
      fetch("http://localhost:8001/api/training/gammes").then(res => res.json())
    ]).then(([prodData, gammeData]) => {
      setProducts(prodData);
      setGammes(gammeData);
      setIsLoading(false);
    }).catch(err => {
      console.error(err);
      setIsLoading(false);
    });
  }, []);

  const filteredProducts = products.filter(p => {
    const matchesSearch = p.name.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesGamme = selectedGammeId === "all" || p.gamme_id === parseInt(selectedGammeId);
    return matchesSearch && matchesGamme;
  });

  // Réinitialiser la page à 1 si la recherche ou le filtre change
  useEffect(() => {
    setCurrentPage(1);
  }, [searchQuery, selectedGammeId]);

  const totalPages = Math.ceil(filteredProducts.length / itemsPerPage);
  const paginatedProducts = filteredProducts.slice((currentPage - 1) * itemsPerPage, currentPage * itemsPerPage);

  const handleStart = () => {
    if (selectedProductId) {
      navigate(`/delegate/training/session?sub=${user?.sub_role}&productId=${selectedProductId}`);
    }
  };

  return (
    <div className="relative min-h-screen p-8 animate-fade-in flex flex-col font-sans overflow-y-auto">
      
      {/* Decors de fond */}
      <div className="fixed top-20 right-0 w-[500px] h-[500px] bg-md-primary/5 blur-[100px] rounded-full pointer-events-none -z-10" />
      <div className="fixed bottom-0 left-10 w-[600px] h-[600px] bg-indigo-500/5 blur-[120px] rounded-full pointer-events-none -z-10" />

      {/* Header with Step Indicator */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6 mb-12">
        <div className="space-y-4">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 rounded-2xl bg-md-primary/10 text-md-primary flex items-center justify-center shadow-lg shadow-md-primary/5">
              <PackageSearch size={28} />
            </div>
            <div>
              <div className="flex items-center gap-2 mb-1">
                <span className="px-2 py-0.5 rounded-full bg-md-primary text-white text-[9px] font-black uppercase tracking-widest">Étape 01</span>
                <span className="text-[10px] font-black text-md-outline uppercase tracking-widest opacity-40">Configuration</span>
              </div>
              <h1 className="text-4xl font-black text-md-on-background tracking-tighter uppercase leading-none">
                Cible de <span className="text-md-primary italic lowercase">formation.</span>
              </h1>
            </div>
          </div>
        </div>
        
        {/* Connection Status */}
        <div className="flex items-center gap-4 bg-white/50 backdrop-blur-md p-2 pl-4 pr-2 rounded-2xl border border-md-outline/5">
           <div className="flex flex-col items-end">
              <span className="text-[9px] font-black uppercase tracking-widest text-md-primary opacity-60">Délégué {user?.sub_role}</span>
              <span className="text-xs font-bold text-md-on-background">{user?.display_name}</span>
           </div>
           <div className="w-10 h-10 rounded-xl bg-md-primary text-white flex items-center justify-center font-black text-sm shadow-lg shadow-md-primary/20">
             {user?.display_name?.[0] || 'D'}
           </div>
        </div>
      </div>

      {/* Main Selection Area */}
      <div className="bg-white/40 backdrop-blur-3xl rounded-[40px] border border-white/20 p-8 shadow-2xl relative overflow-hidden">
        <div className="absolute top-0 right-0 p-8 opacity-[0.03] pointer-events-none">
          <BrainCircuit size={200} />
        </div>

        {/* Search & Categories */}
        <div className="flex flex-col lg:flex-row gap-8 mb-12 relative z-10">
          <div className="flex-1 space-y-4">
            <span className="text-[10px] font-black uppercase tracking-[0.2em] text-md-primary ml-1">Recherche</span>
            <div className="relative group">
               <input 
                 type="text" 
                 placeholder="Quel produit souhaitez-vous présenter ?"
                 value={searchQuery}
                 onChange={(e) => setSearchQuery(e.target.value)}
                 className="w-full h-16 pl-8 pr-12 rounded-3xl border border-md-outline/10 bg-white/80 shadow-sm transition-all focus:ring-4 focus:ring-md-primary/10 focus:border-md-primary text-lg font-bold"
               />
               <div className="absolute right-6 top-1/2 -translate-y-1/2 text-md-outline/30 group-focus-within:text-md-primary transition-colors">
                 <PackageSearch size={24} />
               </div>
            </div>
          </div>

          <div className="space-y-4">
            <span className="text-[10px] font-black uppercase tracking-[0.2em] text-md-primary ml-1">Spécialité / Gamme</span>
            <div className="flex flex-wrap gap-2">
               <button 
                 onClick={() => setSelectedGammeId("all")}
                 className={`px-6 h-16 rounded-3xl text-[11px] font-black uppercase tracking-widest transition-all ${selectedGammeId === "all" ? 'bg-md-on-background text-white shadow-xl' : 'bg-white border border-md-outline/10 text-md-on-background hover:bg-slate-50'}`}
               >
                 Toutes les gammes
               </button>
               {gammes.map(g => (
                 <button 
                   key={g.id}
                   onClick={() => setSelectedGammeId(g.id.toString())}
                   className={`px-6 h-16 rounded-3xl text-[11px] font-black uppercase tracking-widest transition-all ${selectedGammeId === g.id.toString() ? 'bg-md-on-background text-white shadow-xl' : 'bg-white border border-md-outline/10 text-md-on-background hover:bg-slate-50'}`}
                 >
                   {g.name}
                 </button>
               ))}
            </div>
          </div>
        </div>

        {/* Product Grid */}
        {isLoading ? (
          <div className="py-40 flex flex-col items-center justify-center gap-4">
            <div className="w-16 h-16 rounded-full border-4 border-md-primary border-t-transparent animate-spin" />
            <span className="text-[10px] font-black uppercase tracking-[0.3em] text-md-primary animate-pulse">Synchronisation Catalogue...</span>
          </div>
        ) : (
          <div className="space-y-12">
            <div className="grid grid-cols-1 md:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5 gap-6 content-start min-h-[400px]">
              <AnimatePresence mode="popLayout">
                {paginatedProducts.map((p, i) => {
                  const isSelected = selectedProductId === p.id;
                  const Icon = productIcons[p.id % productIcons.length];
                  
                  return (
                    <motion.div
                      key={p.id}
                      layout
                      initial={{ opacity: 0, scale: 0.9 }}
                      animate={{ opacity: 1, scale: 1 }}
                      exit={{ opacity: 0, scale: 0.9 }}
                      transition={{ delay: i * 0.03 }}
                      onClick={() => setSelectedProductId(p.id)}
                      className={`
                        cursor-pointer rounded-[32px] p-8 flex flex-col gap-6 relative overflow-hidden transition-all duration-500
                        ${isSelected 
                          ? 'bg-md-primary text-white shadow-2xl shadow-md-primary/40 scale-105 border-none z-10' 
                          : 'bg-white/50 text-md-on-background hover:bg-white hover:shadow-xl border border-md-outline/10'
                        }
                      `}
                    >
                      <div className={`w-14 h-14 rounded-[20px] flex items-center justify-center relative z-10 transition-colors ${isSelected ? 'bg-white/20' : 'bg-md-primary/5 text-md-primary'}`}>
                         <Icon size={24} />
                      </div>
                      
                      <div className="relative z-10">
                        <h3 className="text-xl font-black uppercase tracking-tight leading-tight mb-2">{p.name}</h3>
                        <div className="flex items-center gap-2">
                           <div className={`w-1.5 h-1.5 rounded-full ${isSelected ? 'bg-white/40' : 'bg-md-primary/20'}`} />
                           <p className={`text-[10px] font-bold uppercase tracking-widest ${isSelected ? 'text-white/60' : 'text-md-outline/60'}`}>
                             {p.gamme_name}
                           </p>
                        </div>
                      </div>

                      {isSelected && (
                        <motion.div 
                          initial={{ opacity: 0, x: -10 }}
                          animate={{ opacity: 1, x: 0 }}
                          className="absolute bottom-6 right-6"
                        >
                          <ShieldCheck size={24} className="text-white/30" />
                        </motion.div>
                      )}
                    </motion.div>
                  );
                })}
              </AnimatePresence>
            </div>

            {/* Bottom Controls */}
            <div className="flex flex-col md:flex-row items-center justify-between gap-8 pt-8 border-t border-md-outline/5">
              {totalPages > 1 ? (
                <div className="flex items-center gap-3">
                  <button 
                    onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                    disabled={currentPage === 1}
                    className="w-12 h-12 rounded-2xl flex items-center justify-center bg-white border border-md-outline/10 hover:bg-md-primary hover:text-white disabled:opacity-20 transition-all"
                  >
                    <ChevronLeft size={20} />
                  </button>
                  <span className="text-xs font-black uppercase tracking-[0.2em] px-4">
                    {currentPage} <span className="opacity-30">/</span> {totalPages}
                  </span>
                  <button 
                    onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                    disabled={currentPage === totalPages}
                    className="w-12 h-12 rounded-2xl flex items-center justify-center bg-white border border-md-outline/10 hover:bg-md-primary hover:text-white disabled:opacity-20 transition-all"
                  >
                    <ChevronRight size={20} />
                  </button>
                </div>
              ) : <div />}

              <AnimatePresence>
                {selectedProductId && (
                  <motion.button 
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: 20 }}
                    onClick={handleStart}
                    className="h-20 px-12 bg-md-on-background text-white rounded-[24px] flex items-center gap-6 group hover:scale-[1.02] active:scale-95 transition-all shadow-2xl shadow-black/20"
                  >
                    <div className="flex flex-col items-start">
                      <span className="text-[10px] font-bold text-white/40 uppercase tracking-widest leading-none mb-1">Prêt pour la simulation</span>
                      <span className="text-xl font-black uppercase tracking-tight">Démarrer la session</span>
                    </div>
                    <div className="w-12 h-12 rounded-xl bg-md-primary flex items-center justify-center group-hover:translate-x-2 transition-transform">
                      <ArrowRight size={24} />
                    </div>
                  </motion.button>
                )}
              </AnimatePresence>
            </div>
          </div>
        )}
    </div>
  </div>
  );
}
