import React, { useState, useEffect, useCallback } from 'react';
import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
  Polyline,
  ZoomControl,
  Circle
} from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import {
  Navigation,
  TrendingUp,
  Clock,
  Activity,
  PlusCircle,
  MoreVertical,
  MapPin,
  ChevronRight,
  ArrowRight,
  AlertCircle,
  Calendar,
  Zap,
  Map as MapIcon,
  Navigation2,
  CheckCircle2,
  XCircle,
  CircleDot,
  Loader2,
  Phone,
  Monitor,
  Route,
  Timer,
  Target,
  RefreshCw,
  CloudRain,
  Wind,
  Sun,
  CloudLightning,
  AlertTriangle
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

// ─── Leaflet Icon Fix ───────────────────────────────────────────
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

// ─── Custom Marker Icons by Status ─────────────────────────────
const createIcon = (color, glow) => L.divIcon({
  className: 'custom-marker',
  html: `<div style="
    width: 18px; height: 18px;
    background: ${color};
    border: 3px solid white;
    border-radius: 50%;
    box-shadow: 0 0 12px ${glow}, 0 2px 8px rgba(0,0,0,0.3);
  "></div>`,
  iconSize: [18, 18],
  iconAnchor: [9, 9],
});

const ICONS = {
  planifiee: createIcon('#3b82f6', 'rgba(59,130,246,0.5)'),
  effectuee: createIcon('#10b981', 'rgba(16,185,129,0.5)'),
  annulee: createIcon('#ef4444', 'rgba(239,68,68,0.5)'),
  default: createIcon('#94a3b8', 'rgba(148,163,184,0.3)'),
  delegate: createIcon('#8b5cf6', 'rgba(139,92,246,0.6)'),
};

const API_BASE = 'http://localhost:8000/api/tournee';

// ─── Weather Condition Icon ────────────────────────────────────
const WeatherIcon = ({ condition, size = 20 }) => {
  switch (condition) {
    case 'bad':
      return <CloudLightning size={size} className="text-rose-500" />;
    case 'moderate':
      return <CloudRain size={size} className="text-amber-500" />;
    case 'good':
      return <Sun size={size} className="text-emerald-500" />;
    default:
      return <Sun size={size} className="text-gray-400" />;
  }
};

export default function VisitPlanner() {
  const [schedule, setSchedule] = useState(null);
  const [stats, setStats] = useState(null);
  const [delegateInfo, setDelegateInfo] = useState(null);
  const [optimizing, setOptimizing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [showToast, setShowToast] = useState(false);
  const [toastMessage, setToastMessage] = useState('');
  const [error, setError] = useState(null);

  // Default delegate ID (hardcoded for now)
  const delegueId = 1;

  // Read subRole from query to determine the delegate type
  const searchParams = new URLSearchParams(window.location.search);
  const subRole = searchParams.get('sub') || 'medical';
  const targetType = subRole === 'commercial' ? 'pharmacies' : 'medecins';

  // ─── Fetch Today's Schedule ─────────────────────────────────
  const fetchSchedule = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await fetch(`${API_BASE}/${delegueId}/today?max_visits=8&target=${targetType}`);
      if (!res.ok) throw new Error(`API error: ${res.status}`);
      const data = await res.json();
      setSchedule(data);
    } catch (err) {
      console.error('Failed to fetch schedule:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [delegueId]);

  // ─── Fetch Stats ────────────────────────────────────────────
  const fetchStats = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/stats/${delegueId}`);
      if (res.ok) {
        setStats(await res.json());
      }
    } catch (err) {
      console.error('Failed to fetch stats:', err);
    }
  }, [delegueId]);

  // ─── Fetch Delegate Info ────────────────────────────────────
  const fetchDelegateInfo = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/delegues`);
      if (res.ok) {
        const delegues = await res.json();
        const d = delegues.find(x => x.id === delegueId);
        if (d) setDelegateInfo(d);
      }
    } catch (err) {
      console.error('Failed to fetch delegate:', err);
    }
  }, [delegueId]);

  useEffect(() => {
    fetchSchedule();
    fetchStats();
    fetchDelegateInfo();
  }, [fetchSchedule, fetchStats, fetchDelegateInfo]);

  // ─── Optimize Route ─────────────────────────────────────────
  const handleOptimize = async () => {
    setOptimizing(true);
    try {
      const res = await fetch(`${API_BASE}/${delegueId}/optimize?max_visits=8&target=${targetType}`);
      if (!res.ok) throw new Error(`Optimize error: ${res.status}`);
      const data = await res.json();
      setSchedule(data);
      setToastMessage('Tournee optimisee avec TomTom Traffic + Meteo !');
      setShowToast(true);
      setTimeout(() => setShowToast(false), 3500);
    } catch (err) {
      console.error('Optimization failed:', err);
      setToastMessage('Erreur lors de l\'optimisation');
      setShowToast(true);
      setTimeout(() => setShowToast(false), 3500);
    } finally {
      setOptimizing(false);
    }
  };

  // ─── Update Visit Status ────────────────────────────────────
  const updateVisitStatus = async (visiteId, newStatut) => {
    try {
      const res = await fetch(`${API_BASE}/visite/${visiteId}/statut`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ statut: newStatut }),
      });
      if (res.ok) {
        // Update local state
        setSchedule(prev => {
          if (!prev) return prev;
          return {
            ...prev,
            blocks: prev.blocks.map(b =>
              b.medecin_id === visiteId ? { ...b, statut: newStatut } : b
            )
          };
        });
        setToastMessage(`Visite marquee comme ${newStatut}`);
        setShowToast(true);
        setTimeout(() => setShowToast(false), 2500);
        fetchStats(); // Refresh stats
      }
    } catch (err) {
      console.error('Status update failed:', err);
    }
  };

  // ─── Extract visits from schedule blocks ────────────────────
  const visitBlocks = schedule?.blocks?.filter(b => b.type === 'visite') || [];
  const weather = schedule?.weather || null;
  const mapCenter = delegateInfo
    ? [delegateInfo.latitude, delegateInfo.longitude]
    : visitBlocks.length > 0
      ? [visitBlocks[0].latitude, visitBlocks[0].longitude]
      : [36.8190, 10.1658]; // Default: Tunis

  // Route polyline coordinates  
  const routeCoords = visitBlocks
    .filter(v => v.latitude && v.longitude)
    .map(v => [v.latitude, v.longitude]);

  // ─── Status Badge Component ─────────────────────────────────
  const StatusBadge = ({ statut }) => {
    const styles = {
      planifiee: { bg: 'bg-blue-500', text: 'Planifie', icon: CircleDot },
      effectuee: { bg: 'bg-emerald-500', text: 'Effectue', icon: CheckCircle2 },
      annulee: { bg: 'bg-rose-500', text: 'Annule', icon: XCircle },
      reportee: { bg: 'bg-amber-500', text: 'Reporte', icon: Clock },
    };
    const s = styles[statut] || styles.planifiee;
    const Icon = s.icon;
    return (
      <div className={`${s.bg} text-white px-4 py-1.5 rounded-pill text-[9px] font-black uppercase tracking-widest shadow-sm flex items-center gap-1.5`}>
        <Icon size={10} /> {s.text}
      </div>
    );
  };



  // ─── Visit Type Badge ───────────────────────────────────────
  const VisitTypeBadge = ({ type, weatherOverride, weatherReason }) => (
    <div className={`flex items-center gap-1.5 text-[9px] font-black uppercase tracking-wider ${type === 'physique' ? 'text-violet-600' : 'text-sky-600'
      }`}>
      {type === 'physique' ? <Phone size={10} /> : <Monitor size={10} />}
      {type === 'physique' ? 'Physique' : 'En ligne'}
      {weatherOverride && (
        <span className="flex items-center gap-0.5 text-amber-500 ml-1" title={weatherReason || "Modifié par la météo"}>
          <CloudRain size={9} />
        </span>
      )}
    </div>
  );

  // ─── Weather Widget Component ────────────────────────────────
  const WeatherWidget = ({ weather }) => {
    if (!weather) return null;

    const conditionStyles = {
      bad: { bg: 'bg-rose-500/10', border: 'border-rose-500/20', text: 'text-rose-700' },
      moderate: { bg: 'bg-amber-500/10', border: 'border-amber-500/20', text: 'text-amber-700' },
      good: { bg: 'bg-emerald-500/10', border: 'border-emerald-500/20', text: 'text-emerald-700' },
      unknown: { bg: 'bg-gray-500/10', border: 'border-gray-500/20', text: 'text-gray-700' },
    };
    const style = conditionStyles[weather.condition] || conditionStyles.unknown;

    return (
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className={`p-5 ${style.bg} backdrop-blur-3xl rounded-[24px] border ${style.border} shadow-xl flex flex-col gap-3 min-w-[200px]`}
      >
        <div className="flex items-center gap-3">
          <WeatherIcon condition={weather.condition} size={24} />
          <div>
            <p className="text-[10px] font-black uppercase tracking-[0.3em] opacity-60">Meteo en direct</p>
            <p className={`text-sm font-black ${style.text} leading-tight`}>
              {weather.condition === 'bad' ? 'Defavorable' :
                weather.condition === 'moderate' ? 'Incertaine' :
                  weather.condition === 'good' ? 'Favorable' : 'Inconnue'}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-4 text-[10px] font-bold opacity-70">
          <span className="flex items-center gap-1">
            <CloudRain size={11} /> {weather.rain_mm} mm
          </span>
          <span className="flex items-center gap-1">
            <Wind size={11} /> {weather.wind_kmh} km/h
          </span>
        </div>
      </motion.div>
    );
  };

  // ─── Loading State ──────────────────────────────────────────
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[700px]">
        <div className="flex flex-col items-center gap-6">
          <Loader2 size={48} className="animate-spin text-md-primary" />
          <p className="text-sm font-black uppercase tracking-[0.3em] text-md-on-surface-variant opacity-60">
            Chargement de la tournee...
          </p>
          <p className="text-[10px] font-bold text-md-on-surface-variant opacity-40">
            Connexion TomTom Traffic + Open-Meteo
          </p>
        </div>
      </div>
    );
  }

  // ─── Error State ────────────────────────────────────────────
  if (error && !schedule) {
    return (
      <div className="flex items-center justify-center min-h-[700px]">
        <div className="flex flex-col items-center gap-6 p-12 bg-white rounded-[36px] shadow-xl max-w-md text-center">
          <AlertCircle size={48} className="text-rose-500" />
          <h3 className="text-xl font-black text-md-on-background">Erreur de connexion</h3>
          <p className="text-sm text-md-on-surface-variant">{error}</p>
          <p className="text-xs text-md-on-surface-variant opacity-60">
            Verifiez que le serveur FastAPI tourne sur le port 8000
          </p>
          <button onClick={fetchSchedule} className="btn-primary !h-12 !px-8 !text-xs">
            <RefreshCw size={16} /> Reessayer
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col lg:flex-row gap-8 animate-fade-in relative z-10 pb-10 min-h-[800px]">

      {/* Background Glows */}
      <div className="fixed top-20 right-10 w-[500px] h-[500px] organic-glow bg-md-primary/10 rounded-full pointer-events-none -z-10" />



      {/* LEFT: Interactive Map (60%) */}
      <div className="lg:flex-[0.65] min-h-[700px] flex flex-col bg-white rounded-[48px] p-6 relative overflow-hidden group shadow-2xl border border-md-outline/10">
        <div className="flex-1 w-full relative rounded-[36px] overflow-hidden z-0">
          <MapContainer
            center={mapCenter}
            zoom={13}
            className="absolute inset-0 w-full h-full"
            zoomControl={false}
          >
            <TileLayer
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              attribution='&copy; Avalive Intelligence'
            />
            <ZoomControl position="bottomright" />

            {/* Delegate starting position */}
            {delegateInfo && (
              <Marker position={[delegateInfo.latitude, delegateInfo.longitude]} icon={ICONS.delegate}>
                <Popup className="md-popup">
                  <div className="p-6 font-sans space-y-3 min-w-[200px]">
                    <p className="text-[10px] font-black uppercase text-violet-600 tracking-[0.2em]">Point de Depart</p>
                    <h4 className="text-lg font-black text-md-on-background tracking-tighter leading-none uppercase">
                      {delegateInfo.prenom} {delegateInfo.nom}
                    </h4>
                    <p className="text-xs font-bold text-md-on-surface-variant opacity-60">{delegateInfo.ville} — {delegateInfo.zone}</p>
                  </div>
                </Popup>
              </Marker>
            )}

            {/* Visit markers */}
            {visitBlocks.map((v, i) => (
              <Marker
                key={`visit-${i}`}
                position={[v.latitude, v.longitude]}
                icon={ICONS[v.statut] || ICONS.planifiee}
              >
                <Popup className="md-popup">
                  <div className="p-6 font-sans space-y-4 min-w-[220px]">
                    <div className="flex items-center justify-end">
                      <VisitTypeBadge type={v.visit_type} weatherOverride={v.weather_override} weatherReason={v.weather_reason} />
                    </div>
                    <h4 className="text-lg font-black text-md-on-background tracking-tighter leading-none uppercase">{v.medecin_nom}</h4>
                    <p className="text-xs font-bold text-md-on-surface-variant opacity-60 uppercase tracking-widest">{v.specialite}</p>
                    <div className="flex items-center gap-4 text-[10px] font-bold text-md-on-surface-variant opacity-50">
                      <span>{v.start} - {v.end}</span>
                      <span>{v.duration_min} min</span>
                    </div>
                    {/* Real-time travel info */}
                    {v.travel_distance_km > 0 && (
                      <div className="flex items-center gap-3 text-[10px] font-bold text-md-primary bg-md-primary/5 px-3 py-2 rounded-xl">
                        <Navigation2 size={11} />
                        {v.travel_distance_km} km • {v.travel_time_min ? `${v.travel_time_min} min` : ''}
                        {v.travel_source === 'tomtom' && (
                          <span className="text-emerald-500 font-black">(TomTom)</span>
                        )}
                      </div>
                    )}

                  </div>
                </Popup>
              </Marker>
            ))}

            {/* Optimized Route Line */}
            {routeCoords.length > 1 && (
              <Polyline
                positions={routeCoords}
                color="var(--color-md-primary)"
                weight={6}
                dashArray="12, 16"
                opacity={0.7}
                lineCap="round"
              />
            )}
          </MapContainer>
        </div>

        {/* Floating Controls */}
        <div className="absolute top-12 left-12 z-[1000] flex flex-col gap-6">
          <button
            onClick={handleOptimize}
            disabled={optimizing}
            className="btn-primary !h-16 !px-12 shadow-2xl shadow-md-primary/40 relative overflow-hidden group !rounded-[24px] !text-sm active:scale-95"
          >
            {optimizing ? (
              <div className="flex items-center gap-4">
                <Loader2 className="animate-spin" size={24} />
                <span className="text-[11px] font-black uppercase tracking-[0.3em]">TomTom + Meteo...</span>
              </div>
            ) : (
              <div className="flex items-center gap-4">
                <Navigation2 size={24} className="group-hover:rotate-45 transition-transform duration-500" />
                <span className="text-[11px] font-black uppercase tracking-[0.3em]">Optimiser l'Itineraire</span>
              </div>
            )}
            {!optimizing && <div className="absolute inset-0 shimmer-anim opacity-15 pointer-events-none" />}
          </button>

          {/* Weather Widget — live conditions */}
          <WeatherWidget weather={weather} />

        </div>

        {/* Toast Notification */}
        <AnimatePresence>
          {showToast && (
            <motion.div
              initial={{ opacity: 0, y: 100 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 100 }}
              className="absolute bottom-12 left-1/2 -translate-x-1/2 z-[1000] px-12 py-6 bg-emerald-500 text-white rounded-pill font-black text-[12px] uppercase tracking-[0.4em] shadow-2xl flex items-center gap-6 border-4 border-white/20 backdrop-blur-md"
            >
              <Zap size={24} fill="currentColor" /> {toastMessage}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* RIGHT: Schedule Panel (35%) */}
      <div className="lg:flex-[0.35] flex flex-col gap-8 h-full min-w-[400px]">

        <div className="md-card !p-0 flex flex-col h-full bg-md-surface-container shadow-2xl border-none relative overflow-hidden">
          <div className="p-10 border-b border-md-outline/5 bg-md-surface-container-low/50 relative">
            <div className="absolute top-0 right-0 w-32 h-32 bg-md-primary/5 rounded-full blur-2xl" />
            <div className="flex items-center justify-between relative z-10">
              <div className="space-y-1">
                <div className="flex items-center gap-3">
                  <MapIcon size={18} className="text-md-primary" />
                  <h3 className="text-[10px] font-black uppercase text-md-primary tracking-[0.4em]">Planning Terrain</h3>
                </div>
                <h4 className="text-3xl font-black text-md-on-background tracking-tighter leading-none uppercase">Tournee du Jour.</h4>
                {schedule && (
                  <p className="text-[10px] font-bold text-md-on-surface-variant opacity-50 mt-2">
                    {schedule.date} &bull; {schedule.visits_scheduled} visites
                    {weather && weather.condition !== 'unknown' && (
                      <span className="ml-2 inline-flex items-center gap-1">
                        &bull; <WeatherIcon condition={weather.condition} size={11} />
                        {weather.condition === 'good' ? 'Beau temps' :
                          weather.condition === 'moderate' ? 'Meteo variable' :
                            weather.condition === 'bad' ? 'Mauvais temps' : ''}
                      </span>
                    )}
                  </p>
                )}
              </div>
              <button
                onClick={fetchSchedule}
                className="w-14 h-14 bg-md-primary text-white rounded-[20px] flex items-center justify-center shadow-xl active:scale-95 transition-all shadow-md-primary/30"
              >
                <RefreshCw size={24} />
              </button>
            </div>
          </div>

          {/* Visit List */}
          <div className="p-8 space-y-5 relative z-10 overflow-y-auto flex-1 max-h-[500px]">
            {visitBlocks.length === 0 && (
              <div className="text-center py-12 opacity-50">
                <Route size={48} className="mx-auto mb-4 text-md-primary" />
                <p className="text-sm font-bold text-md-on-surface-variant">Aucune visite planifiee</p>
              </div>
            )}
            {visitBlocks.map((v, i) => (
              <motion.div
                layout
                key={`card-${i}`}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.08 }}
                className={`p-6 bg-white rounded-[28px] border hover:shadow-xl transition-all cursor-pointer group flex items-start gap-5 relative overflow-hidden ${v.statut === 'effectuee' ? 'border-emerald-200 bg-emerald-50/30' :
                    v.statut === 'annulee' ? 'border-rose-200 bg-rose-50/30 opacity-60' :
                      v.weather_override ? 'border-amber-200 bg-amber-50/20' :
                        'border-md-outline/5 hover:border-md-primary/30'
                  }`}
              >
                <div className="absolute top-0 right-0 w-20 h-20 bg-md-primary/5 rounded-full blur-2xl -translate-y-1/2 translate-x-1/2 opacity-0 group-hover:opacity-100 transition-opacity" />

                <div className="flex flex-col items-center gap-2 min-w-[50px]">
                  <div className="text-base font-black text-md-primary font-mono">{v.start}</div>
                  <div className="text-[9px] font-bold text-md-on-surface-variant opacity-40">{v.duration_min}min</div>
                </div>

                <div className="flex-1 space-y-2.5">
                  <div className="flex justify-between items-start gap-2">
                    <div className="space-y-1 flex-1 min-w-0">
                      <h5 className="text-base font-black text-md-on-background tracking-tighter uppercase leading-none truncate">{v.medecin_nom}</h5>
                      <p className="text-[9px] font-black text-md-on-surface-variant uppercase tracking-widest opacity-60 leading-none">{v.specialite}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <VisitTypeBadge type={v.visit_type} weatherOverride={v.weather_override} weatherReason={v.weather_reason} />
                    {v.travel_distance_km > 0 && (
                      <span className="text-[9px] font-bold text-md-on-surface-variant opacity-40 flex items-center gap-1">
                        <Navigation2 size={9} />
                        {v.travel_distance_km} km
                        {v.travel_time_min != null && ` • ${v.travel_time_min} min`}
                        {v.travel_source === 'tomtom' && (
                          <span className="text-emerald-500 ml-0.5">(trafic reel)</span>
                        )}
                      </span>
                    )}
                  </div>
                  {/* Weather override warning */}
                  {v.weather_override && (
                    <div className="flex items-center gap-1.5 text-[9px] font-black text-amber-600 bg-amber-500/10 px-2.5 py-1.5 rounded-lg w-fit">
                      <CloudRain size={10} />
                      {v.weather_reason || 'Basculee en ligne (meteo)'}
                    </div>
                  )}

                </div>
              </motion.div>
            ))}
          </div>

          {/* Stats Panel */}
          <div className="p-8 border-t border-md-outline/10 bg-md-surface-container-low/50 grid grid-cols-3 gap-4 relative z-10">
            <div className="p-5 bg-amber-500/5 rounded-[24px] border border-amber-500/10 flex flex-col gap-1 transition-transform hover:scale-105">
              <p className="text-[8px] font-black uppercase text-amber-600 tracking-[0.3em]">Distance Totale</p>
              <p className="text-2xl font-black text-md-on-background tracking-tighter">
                {schedule?.total_distance_km?.toFixed(1) || 0} km
              </p>
            </div>
            <div className="p-5 bg-violet-500/5 rounded-[24px] border border-violet-500/10 flex flex-col gap-1 transition-transform hover:scale-105">
              <p className="text-[8px] font-black uppercase text-violet-600 tracking-[0.3em]">Temps Trajet</p>
              <p className="text-2xl font-black text-md-on-background tracking-tighter">
                {schedule?.total_travel_min?.toFixed(0) || 0} min
              </p>
            </div>
            <div className="p-5 bg-emerald-500/5 rounded-[24px] border border-emerald-500/10 flex flex-col gap-1 transition-transform hover:scale-105">
              <p className="text-[8px] font-black uppercase text-emerald-600 tracking-[0.3em]">
                {stats ? 'Taux Realisation' : 'Visites'}
              </p>
              <p className="text-2xl font-black text-md-on-background tracking-tighter">
                {stats ? `${stats.taux_realisation}%` : `${schedule?.visits_scheduled || 0}`}
              </p>
            </div>

          </div>
        </div>
      </div>

      <style jsx>{`
        .md-popup .leaflet-popup-content-wrapper {
           border-radius: 28px;
           padding: 0;
           box-shadow: 0 30px 60px rgba(0,0,0,0.15);
           border: 1px solid rgba(0,0,0,0.05);
           background-color: rgba(255,255,255,0.95);
           backdrop-filter: blur(10px);
        }
        .md-popup .leaflet-popup-content {
           margin: 0;
           padding: 0;
        }
        .leaflet-container {
           font-family: inherit !important;
        }
      `}
      </style>
    </div>
  );
}
