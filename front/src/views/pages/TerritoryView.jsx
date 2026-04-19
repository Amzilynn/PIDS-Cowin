import { MapContainer, TileLayer, Marker } from 'react-leaflet';
import { Zap } from 'lucide-react';
import { Card } from '../components/Card';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Fix Leaflet's broken default icon URLs when bundled with Vite
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

export function TerritoryView({ selectedRegion, regionsData, onRegionSelect }) {
  return (
    <div className="grid grid-cols-12 gap-6" style={{ height: '650px' }}>
      <Card className="col-span-8 p-3 overflow-hidden">
        <MapContainer center={[33.8869, 9.5375]} zoom={6} style={{ height: '100%', width: '100%' }} className="rounded-[20px]">
          <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
          {(regionsData || []).map((reg) => (
            <Marker
              key={reg.id}
              position={[parseFloat(reg.lat), parseFloat(reg.lng)]}
              eventHandlers={{ click: () => onRegionSelect({
                name: reg.name, perf: reg.perf, reps: reg.reps, strategy: reg.strategy
              }) }}
            />
          ))}
        </MapContainer>
      </Card>
      <div className="col-span-4 space-y-6">
        <Card>
          <h3 className="text-xl font-black mb-4">Insight: {selectedRegion.name}</h3>
          <div className="space-y-6">
            <div>
              <p className="text-[10px] font-bold text-slate-400 uppercase">Efficiency</p>
              <p className="text-4xl font-black text-[#0A5C5C]">{selectedRegion.perf}%</p>
            </div>
            <div className="p-5 bg-slate-50 rounded-2xl border border-slate-100">
              <p className="text-[10px] font-bold text-[#E6B800] uppercase mb-2 italic flex items-center gap-2">
                <Zap size={12} fill="currentColor" /> AI Strategy Recommendation
              </p>
              <p className="text-sm leading-relaxed text-slate-600 font-medium">
                {selectedRegion.strategy}
              </p>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}
