import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { motion, AnimatePresence } from 'framer-motion';
import { PackageSearch, ArrowRight, Activity, Pill, Dna, Hexagon, Component, ChevronLeft, ChevronRight } from 'lucide-react';

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
    if (selectedProductId && user?.user_id) {
      navigate('/delegate/training/session', { 
        state: { 
          productId: selectedProductId, 
          delegueId: user.user_id 
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
        
        {/* Profil connecté affiché discrètement */}
        <div className="flex items-center gap-3 bg-white p-3 px-5 rounded-2xl shadow-sm border border-md-outline/5 relative overflow-hidden">
          <div className="w-8 h-8 rounded-xl bg-md-primary/10 flex items-center justify-center text-md-primary font-black text-xs">
            {user?.display_name?.[0] || 'D'}
          </div>
          <div className="flex flex-col">
             <span className="text-[9px] font-black uppercase tracking-widest text-md-primary opacity-60">Connecté en tant que</span>
             <span className="text-xs font-bold text-md-on-background">{user?.display_name}</span>
          </div>
        </div>
      </div>

      {/* Barre de Recherche et Filtre par Gamme */}
      <div className="mb-10 flex flex-col gap-6">
        <div className="max-w-xl relative">
           <input 
             type="text" 
             placeholder="Rechercher un produit Vital..."
             value={searchQuery}
             onChange={(e) => setSearchQuery(e.target.value)}
             className="w-full h-14 pl-6 pr-12 rounded-full border border-md-outline/20 bg-white/50 backdrop-blur-md shadow-inner focus:outline-none focus:ring-2 focus:ring-md-primary/50 focus:border-md-primary text-sm font-bold text-md-on-background placeholder:font-medium placeholder:uppercase placeholder:tracking-widest placeholder:text-[11px]"
           />
        </div>

        <div className="flex flex-wrap items-center gap-3">
           <span className="text-[10px] font-black uppercase tracking-[0.2em] text-md-outline/60 mr-2">Filtrer par Gamme :</span>
           <button 
             onClick={() => setSelectedGammeId("all")}
             className={`px-6 py-2.5 rounded-full text-[10px] font-black uppercase tracking-widest transition-all ${selectedGammeId === "all" ? 'bg-md-primary text-white shadow-lg shadow-md-primary/20' : 'bg-white border border-md-outline/10 text-md-on-background hover:bg-slate-50'}`}
           >
             Toutes
           </button>
           {gammes.map(g => (
             <button 
               key={g.id}
               onClick={() => setSelectedGammeId(g.id.toString())}
               className={`px-6 py-2.5 rounded-full text-[10px] font-black uppercase tracking-widest transition-all ${selectedGammeId === g.id.toString() ? 'bg-md-primary text-white shadow-lg shadow-md-primary/20' : 'bg-white border border-md-outline/10 text-md-on-background hover:bg-slate-50'}`}
             >
               {g.name}
             </button>
           ))}
        </div>
      </div>

      {/* Grille des Produits */}
      {isLoading ? (
        <div className="flex-1 flex items-center justify-center">
          <div className="w-12 h-12 rounded-full border-4 border-md-primary border-t-transparent animate-spin" />
        </div>
      ) : (
        <div className="flex flex-col flex-1 pb-32">
          <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 2xl:grid-cols-5 gap-6 content-start flex-1">
            <AnimatePresence mode="popLayout">
              {paginatedProducts.map((p, i) => {
                const isSelected = selectedProductId === p.id;
                const Icon = productIcons[p.id % productIcons.length];
                
                return (
                  <motion.div
                    key={p.id}
                    layout
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, scale: 0.9 }}
                    transition={{ delay: i * 0.05 }}
                    onClick={() => setSelectedProductId(p.id)}
                    className={`
                      cursor-pointer rounded-[24px] p-6 flex flex-col gap-4 relative overflow-hidden transition-all duration-300
                      ${isSelected 
                        ? 'bg-md-primary text-white shadow-2xl shadow-md-primary/30 scale-105 border-none z-10' 
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
                        Gamme: {p.gamme_name}
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

          {/* Contrôles de pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-6 mt-12 bg-white/50 backdrop-blur-md self-center p-2 rounded-full border border-md-outline/10 shadow-lg">
              <button 
                onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                disabled={currentPage === 1}
                className="w-12 h-12 rounded-full flex items-center justify-center bg-white border border-md-outline/10 text-md-on-background shadow-sm hover:bg-md-primary/10 hover:text-md-primary disabled:opacity-30 disabled:cursor-not-allowed transition-all"
              >
                <ChevronLeft size={20} />
              </button>
              
              <div className="flex items-center gap-2 px-4">
                <span className="text-xs font-black uppercase tracking-widest text-md-on-background">Page <span className="text-md-primary">{currentPage}</span> / {totalPages}</span>
              </div>

              <button 
                onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                disabled={currentPage === totalPages}
                className="w-12 h-12 rounded-full flex items-center justify-center bg-white border border-md-outline/10 text-md-on-background shadow-sm hover:bg-md-primary/10 hover:text-md-primary disabled:opacity-30 disabled:cursor-not-allowed transition-all"
              >
                <ChevronRight size={20} />
              </button>
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
