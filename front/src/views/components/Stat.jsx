import { Card } from './Card';

export const Stat = ({ label, value, trend }) => (
  <Card>
    <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">{label}</p>
    <div className="flex items-baseline gap-2 mt-2">
      <h3 className="text-3xl font-black text-slate-900">{value}</h3>
      {trend && <span className="text-xs font-bold text-emerald-500">{trend}</span>}
    </div>
  </Card>
);
