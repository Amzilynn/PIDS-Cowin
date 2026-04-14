import React, { useMemo, useState } from 'react';
import { PackageCheck } from 'lucide-react';
import { useLocation } from 'react-router-dom';

const DSO3_API_URL = import.meta.env.VITE_DSO3_API_URL || 'http://127.0.0.1:8000';

export default function ProductRecommendations() {
   const location = useLocation();
   const query = new URLSearchParams(location.search);
   const subRole = query.get('sub') || 'medical';

   const [formData, setFormData] = useState({
      name: '',
      category: '',
      description: '',
   });
   const [loading, setLoading] = useState(false);
   const [error, setError] = useState('');
   const [result, setResult] = useState(null);

   const hasRecommendations = useMemo(
      () => Boolean(result && Array.isArray(result.recommendations) && result.recommendations.length > 0),
      [result],
   );

   const handleChange = (event) => {
      const { name, value } = event.target;
      setFormData((previous) => ({ ...previous, [name]: value }));
   };

   const handleSubmit = async (event) => {
      event.preventDefault();
      setError('');
      setResult(null);
      setLoading(true);

      try {
         const response = await fetch(`${DSO3_API_URL}/products/product`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData),
         });

         if (!response.ok) {
            const payload = await response.json().catch(() => ({}));
            throw new Error(payload?.detail || 'Impossible de générer les recommandations.');
         }

         const payload = await response.json();
         setResult(payload);
      } catch (submitError) {
         setError(submitError.message || 'Erreur inconnue lors du matching.');
      } finally {
         setLoading(false);
      }
   };

   return (
      <div className="space-y-8 animate-fade-in pb-20">
         <div className="space-y-4">
            <div className="flex items-center gap-3">
               <div className="w-11 h-11 rounded-2xl bg-md-secondary-container text-md-primary flex items-center justify-center">
                  <PackageCheck size={24} />
               </div>
               <span className="text-[11px] font-black text-md-primary uppercase tracking-[0.35em]">DSO3 Matching</span>
            </div>
            <h1 className="text-4xl font-black text-md-on-background tracking-tight">Recommandation produit</h1>
            <p className="text-md-on-surface-variant font-semibold">
               Crée un produit puis récupère les meilleurs délégués (profil {subRole}).
            </p>
         </div>

         <form onSubmit={handleSubmit} className="bg-white rounded-2xl border border-slate-200 p-6 grid gap-4 md:grid-cols-3">
            <div className="space-y-2">
               <label className="text-xs font-bold uppercase tracking-wider text-slate-500">Nom produit</label>
               <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleChange}
                  required
                  className="w-full rounded-xl border border-slate-300 px-4 py-3 outline-none focus:ring-2 focus:ring-indigo-500"
                  placeholder="Cardio Protect X10"
               />
            </div>
            <div className="space-y-2">
               <label className="text-xs font-bold uppercase tracking-wider text-slate-500">Catégorie</label>
               <input
                  type="text"
                  name="category"
                  value={formData.category}
                  onChange={handleChange}
                  required
                  className="w-full rounded-xl border border-slate-300 px-4 py-3 outline-none focus:ring-2 focus:ring-indigo-500"
                  placeholder="Cardiologie"
               />
            </div>
            <div className="space-y-2 md:col-span-3">
               <label className="text-xs font-bold uppercase tracking-wider text-slate-500">Description</label>
               <textarea
                  name="description"
                  value={formData.description}
                  onChange={handleChange}
                  required
                  rows={4}
                  className="w-full rounded-xl border border-slate-300 px-4 py-3 outline-none focus:ring-2 focus:ring-indigo-500 resize-none"
                  placeholder="Description clinique et bénéfices du produit"
               />
            </div>

            <div className="md:col-span-3 flex items-center gap-3">
               <button
                  type="submit"
                  disabled={loading}
                  className="px-6 py-3 rounded-xl bg-indigo-600 text-white font-bold disabled:opacity-60"
               >
                  {loading ? 'Matching en cours...' : 'Générer le matching'}
               </button>
               <span className="text-xs text-slate-500">API: {DSO3_API_URL}</span>
            </div>
         </form>

         {error ? (
            <div className="rounded-xl border border-rose-300 bg-rose-50 text-rose-700 px-4 py-3 font-semibold">
               {error}
            </div>
         ) : null}

         {result ? (
            <div className="space-y-4">
               <div className="rounded-2xl bg-white border border-slate-200 p-5">
                  <p className="text-sm font-bold text-slate-500 uppercase tracking-wider">Produit créé</p>
                  <p className="text-2xl font-black text-slate-900">{formData.name}</p>
                  <p className="text-sm text-slate-600">ID: {result.product_id}</p>
               </div>

               {hasRecommendations ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                     {result.recommendations.map((recommendation, index) => (
                        <div key={`${recommendation.delegate_id}-${index}`} className="rounded-2xl bg-white border border-slate-200 p-5">
                           <p className="text-xs font-black text-indigo-600 uppercase tracking-wider">Rang {index + 1}</p>
                           <h3 className="text-xl font-black text-slate-900 mt-1">{recommendation.delegate_name}</h3>
                           <p className="text-sm text-slate-500 mt-2">ID délégué: {recommendation.delegate_id}</p>
                           <p className="text-3xl font-black text-slate-900 mt-3">{(recommendation.score * 100).toFixed(1)}%</p>
                           <p className="text-xs text-slate-500 uppercase tracking-wider">Cosine similarity</p>
                        </div>
                     ))}
                  </div>
               ) : (
                  <div className="rounded-xl border border-amber-300 bg-amber-50 text-amber-700 px-4 py-3 font-semibold">
                     Aucun match au-dessus du seuil (0.35). Ajoute plus de délégués ou ajuste la description.
                  </div>
               )}
            </div>
         ) : null}
      </div>
   );
}
