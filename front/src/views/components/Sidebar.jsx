import { menuItems } from '../../models/mockData';

export function Sidebar({ activeTab, onTabChange }) {
  return (
    <nav className="w-72 bg-white border-r border-slate-200 p-6 flex flex-col z-50">
      <div className="flex items-center gap-3 mb-12 px-2">
        <div className="w-10 h-10 bg-[#0A5C5C] rounded-xl flex items-center justify-center text-white font-black text-xl">A</div>
        <h1 className="text-xl font-black tracking-tighter uppercase italic">AVA<span className="text-[#E6B800]">LIVE</span></h1>
      </div>

      <div className="space-y-2">
        {menuItems.map((item) => (
          <button
            key={item.id}
            onClick={() => onTabChange(item.id)}
            className={`w-full flex items-center gap-4 px-4 py-3.5 rounded-xl font-bold text-sm transition-all duration-300 ${
              activeTab === item.id 
              ? 'bg-[#0A5C5C] text-white shadow-xl shadow-teal-900/20' 
              : 'text-slate-500 hover:bg-slate-50 hover:text-[#0A5C5C]'
            }`}
          >
            <item.icon size={20} />
            {item.id}
          </button>
        ))}
      </div>

      <div className="mt-auto p-4 bg-slate-50 rounded-2xl border border-slate-100">
        <p className="text-[10px] font-bold text-slate-400 uppercase mb-2">System Status</p>
        <div className="flex items-center gap-2 text-xs font-bold text-emerald-600">
          <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse" />
          Core Logic Online
        </div>
      </div>
    </nav>
  );
}
