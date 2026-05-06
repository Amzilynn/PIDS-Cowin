import React, { useState } from 'react';
import { 
  LayoutDashboard, 
  BrainCircuit, 
  Map as MapIcon, 
  BarChart3, 
  LogOut, 
  User,
  Settings,
  ShieldCheck,
  ChevronRight,
  Menu,
  X,
  PlusSquare,
  PackageCheck,
  Stethoscope,
  Store
} from 'lucide-react';
import { NavLink, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import Logo from './Logo';

export default function Sidebar({ role = 'delegate', subRole = 'medical' }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [isOpen, setIsOpen] = useState(true);

  // Normalisation des rôles pour l'affichage
  const isDelegate = role === 'delegate';
  const isMedicalDelegate = isDelegate && subRole === 'medical';
  const isCommercialDelegate = isDelegate && subRole === 'commercial';
  
  const isPractitioner = role === 'practitioner';
  const isDoctor = isPractitioner && (subRole === 'doctor' || subRole === 'medical');
  const isPharmacist = isPractitioner && (subRole === 'pharmacist' || subRole === 'commercial');

  const menuItems = {
    admin: [
      { to: '/admin/dashboard', icon: LayoutDashboard, label: 'Vue Générale' },
      { to: '/admin/produits', icon: PackageCheck, label: 'Gestion Produits' },
      { to: '/admin/stats', icon: BarChart3, label: 'Statistiques' },
      { to: '/admin/delegues', icon: User, label: 'Délégués' },
    ],
      delegate: [
        { to: '/delegate/home', icon: LayoutDashboard, label: 'Accueil' },
        { to: '/delegate/training', icon: BrainCircuit, label: 'Formation' },
        { to: '/delegate/produits', icon: PackageCheck, label: 'Mes Produits' },
        { to: '/delegate/planner', icon: MapIcon, label: 'Ma Tournée' },
        { to: '/delegate/profil', icon: User, label: 'Mon Profil' },
      ],
      practitioner: [
        { to: '/practitioner/presentations', icon: PlusSquare, label: 'Salle de Présentation' },
      ]
  };

  const activeMenu = menuItems[role] || menuItems.delegate;

  const getRoleLabel = () => {
    if (role === 'admin') return 'Administrateur';
    if (isMedicalDelegate) return 'Délégué Médical';
    if (isCommercialDelegate) return 'Délégué Commercial';
    if (isDoctor) return 'Médecin';
    if (isPharmacist) return 'Pharmacien';
    return 'Utilisateur';
  };

  return (
    <>
      {/* Bouton Toggle Mobile */}
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className="lg:hidden fixed top-6 left-6 z-[60] w-12 h-12 bg-md-primary rounded-2xl flex items-center justify-center text-white shadow-xl active:scale-95 transition-all"
      >
        {isOpen ? <X size={24} /> : <Menu size={24} />}
      </button>

      <aside className={`fixed inset-y-0 left-0 z-50 bg-md-surface-container border-r border-md-outline/10 h-screen transition-all duration-500 ease-[cubic-bezier(0.2,0,0,1)] ${isOpen ? 'w-80 translate-x-0' : 'w-0 -translate-x-full lg:w-20 lg:translate-x-0 overflow-hidden'} flex flex-col p-8 overflow-y-auto`}>
        
        {/* Glow Décoratif */}
        <div className="absolute top-0 left-0 w-64 h-64 organic-glow bg-md-primary/5 -translate-x-1/2 -translate-y-1/2" />
        
        {/* Section Logo */}
        <div className="relative z-10 mb-4 flex items-center justify-center">
           <Logo showText={isOpen} className={`${isOpen ? 'h-40 lg:h-48 drop-shadow-lg w-full px-4' : 'h-12 w-12 object-contain opacity-0 lg:opacity-100'} transition-all`} />
        </div>

        {/* Menu de Navigation */}
        <nav className="relative z-10 flex-1 space-y-3">
           {activeMenu.map((item) => (
              <NavLink
                 key={item.to}
                 to={`${item.to}?role=${role}&sub=${subRole}`}
                 className={({ isActive }) => 
                    `flex items-center justify-between px-6 py-4 rounded-pill font-bold transition-all duration-300 group ${
                       isActive 
                          ? 'bg-md-primary text-white shadow-lg shadow-md-primary/25 translate-x-1' 
                          : 'text-md-on-surface-variant hover:bg-md-primary/10 hover:text-md-primary hover:translate-x-1'
                    } ${!isOpen && 'lg:justify-center lg:px-0 lg:w-12 lg:h-12'}`
                 }
              >
                 {({ isActive }) => (
                    <>
                       <div className="flex items-center gap-4">
                          <item.icon size={20} strokeWidth={isActive ? 2.5 : 2} className="transition-transform duration-500 group-hover:scale-110" />
                          <span className={`text-[13px] uppercase tracking-widest leading-none ${!isOpen && 'hidden'}`}>{item.label}</span>
                       </div>
                       {isOpen && <ChevronRight size={14} className={`opacity-0 transition-opacity duration-500 group-hover:opacity-100 ${isActive ? 'opacity-100' : ''}`} />}
                    </>
                 )}
              </NavLink>
           ))}
        </nav>

        {/* Section Inférieure : Utilisateur & Déconnexion */}
        <div className="relative z-10 mt-10 space-y-6">
           {/* Badge d'Identification */}
           {isOpen && (
             <div className="p-5 bg-md-secondary-container/30 rounded-[28px] border border-md-secondary-container/50 flex flex-col gap-1 shadow-inner group overflow-hidden relative">
                <div className="absolute top-0 right-0 w-16 h-16 bg-md-primary/5 rounded-full blur-xl -translate-y-1/2 translate-x-1/2" />
                <p className="text-[10px] font-black text-md-on-surface-variant uppercase tracking-widest opacity-60 relative z-10">
                   {user?.display_name || 'Rôle Actif'}
                </p>
                <div className="flex items-center gap-2 relative z-10">
                   <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                   <p className="text-sm font-black text-md-primary truncate uppercase tracking-tighter">
                      {getRoleLabel()}
                   </p>
                </div>
             </div>
           )}

           <div className={`flex items-center gap-3 ${!isOpen && 'lg:flex-col lg:items-center'}`}>
              <button 
                onClick={logout}
                className={`flex-1 btn-pill bg-white/50 border border-md-outline/10 text-rose-500 hover:bg-rose-50 hover:border-rose-200 shadow-sm ${!isOpen && 'lg:w-12 lg:h-12 !p-0 !rounded-2xl'}`}
              >
                 <LogOut size={20} className="transition-transform group-hover:rotate-12" /> 
                 <span className={`${!isOpen && 'hidden'} text-[11px] font-black uppercase tracking-widest`}>Déconnexion</span>
              </button>
           </div>
        </div>
      </aside>

      {/* Overlay Mobile */}
      {isOpen && (
        <div 
          onClick={() => setIsOpen(false)}
          className="lg:hidden fixed inset-0 z-40 bg-black/20 backdrop-blur-sm"
        />
      )}
    </>
  );
}
