import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { PackageSearch, ArrowRight, Activity, Pill, Dna, Hexagon, Component } from 'lucide-react';

export default function ProductSelection() {
  const navigate = useNavigate();
  const [products, setProducts] = useState([]);
  const [delegues, setDelegues] = useState([]);
  const [selectedProductId, setSelectedProductId] = useState(null);
  const [selectedDelegueId, setSelectedDelegueId] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [isLoading, setIsLoading] = useState(true);

  // Random icons for products lacking specific metadata
  const productIcons = [Pill, Activity, Dna, Hexagon, Component];

  useEffect(() => {
    // Simulation du temps de chargement pour effet visuel
    Promise.all([
      fetch("http://localhost:8001/api/training/products").then(res => res.json()),
      fetch("http://localhost:8001/api/training/delegues").then(res => res.json())
    ]).then(([prodData, delData]) => {
      setProducts(prodData);
      setDelegues(delData);
      if (delData.length > 0) setSelectedDelegueId(delData[0].id);
      setIsLoading(false);
    }).catch(err => {
      console.error(err);
      setIsLoading(false);
    });
  }, []);

  const filteredProducts = products.filter(p => p.name.toLowerCase().includes(searchQuery.toLowerCase()));

  const handleStart = () => {
    if (selectedProductId && selectedDelegueId) {
      navigate('/delegate/training/session', { 
        state: { 
          productId: selectedProductId, 
          delegueId: selectedDelegueId 
        } 
      });
    }
  };

  return (
    <div className="relative min-h-[calc(100vh-100px)] p-8 animate-fade-in flex flex-col font-sans">
      
      {/* Decors de fond */}
      <div className="fixed top-20 right-0 w-[500px] h-[500px] bg-md-primary/5 blur-[100px] rounded-full pointer-events-none -z-10" />
      <div className="fixed bottom-0 left-10 w-[600px] h-[600px] bg-indigo-500/5 blur-[120px] rounded-full pointer-events-none -z-10" />

      {/* Header */}
      <div className="flex flex-col md:flex-row items-start md:items-end justify-between gap-6 mb-12">
        <div className="space-y-4">
          <div className="w-14 h-14 rounded-2xl bg-md-primary/10 text-md-primary flex items-center justify-center shadow-lg shadow-md-primary/5">
            <PackageSearch size={28} />
          </div>
          <div>
            <h1 className="text-4xl font-black text-md-on-background tracking-tighter uppercase leading-none">
              Choix du <span className="text-md-primary italic lowercase">produit.</span>
            </h1>
            <p className="text-sm font-bold text-md-on-surface-variant opacity-60 uppercase tracking-widest mt-2 ml-1">
              Configuration de la simulation IA
            </p>
          </div>
        </div>
        
        {/* Menu Délégué Temporaire (Avant auth DB) */}
        <div className="flex items-center gap-4 bg-white p-3 rounded-2xl shadow-xl shadow-black/5 border border-md-outline/5 relative overflow-hidden group">
          <div className="absolute inset-0 bg-md-primary/[0.02] pointer-events-none group-hover:bg-md-primary/[0.05] transition-colors" />
          <div className="relative z-10 flex flex-col">
             <span className="text-[9px] font-black uppercase tracking-widest text-md-primary mb-1 ml-2">Profil Temporaire</span>
             <select 
               value={selectedDelegueId}
               onChange={e => setSelectedDelegueId(e.target.value)}
               className="h-10 px-4 bg-md-surface-container rounded-xl text-xs font-bold outline-none border-none cursor-pointer"
             >
               {delegues.map(d => (
                 <option key={d.id} value={d.id}>{d.nom} ({d.level})</option>
               ))}
             </select>
          </div>
        </div>
      </div>

      {/* Barre de Recherche */}
      <div className="mb-8 max-w-xl relative">
         <input 
           type="text" 
           placeholder="Rechercher un produit Vital..."
           value={searchQuery}
           onChange={(e) => setSearchQuery(e.target.value)}
           className="w-full h-14 pl-6 pr-12 rounded-full border border-md-outline/20 bg-white/50 backdrop-blur-md shadow-inner focus:outline-none focus:ring-2 focus:ring-md-primary/50 focus:border-md-primary text-sm font-bold text-md-on-background placeholder:font-medium placeholder:uppercase placeholder:tracking-widest placeholder:text-[11px]"
         />
      </div>

      {/* Grille des Produits */}
      {isLoading ? (
        <div className="flex-1 flex items-center justify-center">
          <div className="w-12 h-12 rounded-full border-4 border-md-primary border-t-transparent animate-spin" />
        </div>
      ) : (
        <div className="flex-1 grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 2xl:grid-cols-5 gap-6 content-start pb-24">
          <AnimatePresence>
            {filteredProducts.map((p, i) => {
              const isSelected = selectedProductId === p.id;
              const Icon = productIcons[p.id % productIcons.length];
              
              return (
                <motion.div
                  key={p.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, scale: 0.9 }}
                  transition={{ delay: i * 0.05 }}
                  onClick={() => setSelectedProductId(p.id)}
                  className={`
                    cursor-pointer rounded-[24px] p-6 flex flex-col gap-4 relative overflow-hidden transition-all duration-300
                    ${isSelected 
                      ? 'bg-md-primary text-white shadow-2xl shadow-md-primary/30 scale-105 border-none' 
                      : 'bg-white text-md-on-background hover:bg-white/80 hover:shadow-xl border border-md-outline/10 shadow-sm hover:-translate-y-1'
                    }
                  `}
                >
                  {isSelected && (
                    <div className="absolute top-0 right-0 w-32 h-32 bg-white/20 blur-3xl rounded-full -translate-y-1/2 translate-x-1/2" />
                  )}
                  
                  <div className={`w-12 h-12 rounded-2xl flex items-center justify-center relative z-10 transition-colors ${isSelected ? 'bg-white/20' : 'bg-md-surface-container-high'}`}>
                     <Icon size={22} className={isSelected ? 'text-white' : 'text-md-primary'} />
                  </div>
                  
                  <div className="relative z-10 mt-2">
                    <h3 className="text-base font-black uppercase tracking-tight leading-none mb-2">{p.name}</h3>
                    <p className={`text-[10px] font-bold uppercase tracking-widest ${isSelected ? 'text-white/70' : 'text-md-outline/60'}`}>
                      ID de la Base: #{p.id}
                    </p>
                  </div>
                </motion.div>
              );
            })}
          </AnimatePresence>
          
          {filteredProducts.length === 0 && (
            <div className="col-span-full py-20 text-center opacity-50">
              <p className="text-sm font-black uppercase tracking-widest mb-2">Aucun produit trouvé</p>
              <p className="text-xs font-medium">Vérifiez l'orthographe de votre recherche.</p>
            </div>
          )}
        </div>
      )}

      {/* Floating Action Bar */}
      <AnimatePresence>
        {selectedProductId && (
          <motion.div 
            initial={{ opacity: 0, y: 50, scale: 0.9 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 50, scale: 0.9 }}
            className="fixed bottom-10 left-1/2 -translate-x-1/2 z-50 pointer-events-none"
          >
             <div className="pointer-events-auto bg-md-on-background p-3 pl-8 rounded-full shadow-2xl shadow-black/30 flex items-center gap-8 border border-white/10 backdrop-blur-3xl">
                <div className="flex flex-col">
                   <span className="text-[9px] font-bold text-white/50 uppercase tracking-widest leading-none mb-1">Cible Sélectionnée</span>
                   <span className="text-sm font-black text-white uppercase tracking-wider">{products.find(p => p.id === selectedProductId)?.name}</span>
                </div>
                <button 
                  onClick={handleStart}
                  className="h-12 px-8 bg-md-primary rounded-full text-white font-black text-[11px] uppercase tracking-widest flex items-center gap-3 hover:bg-md-primary/90 hover:scale-105 active:scale-95 transition-all shadow-lg shadow-md-primary/40"
                >
                   Continuer <ArrowRight size={16} />
                </button>
             </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
