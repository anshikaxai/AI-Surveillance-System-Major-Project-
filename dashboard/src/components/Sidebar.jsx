import { NavLink } from 'react-router-dom';
import { LayoutDashboard, AlertTriangle, MapPin, Settings, Shield, Activity, Cpu } from 'lucide-react';

const NAV = [
  { to: '/', label: 'Command Center', icon: LayoutDashboard },
  { to: '/events', label: 'Events', icon: AlertTriangle },
  { to: '/rois', label: 'ROI Manager', icon: MapPin },
  { to: '/nlp', label: 'NLP Commands', icon: Activity },
  { to: '/cameras', label: 'Cameras', icon: Cpu },
  { to: '/settings', label: 'Config', icon: Settings },
];

export default function Sidebar() {
  return (
    <aside className="w-64 shrink-0 bg-base-800/90 border-r border-base-600/40 h-screen sticky top-0 flex flex-col">
      <div className="px-5 py-6 border-b border-base-600/40">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-accent-green to-accent-cyan flex items-center justify-center text-base-900">
            <Shield className="w-6 h-6" strokeWidth={2.5} />
          </div>
          <div>
            <p className="text-sm text-white/90 font-bold leading-tight">AEGIS</p>
            <p className="text-[10px] text-white/50 uppercase tracking-widest">Edge Surveillance</p>
          </div>
        </div>
      </div>
      <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
        {NAV.map(({ to, label, icon: Icon }) => (
          <NavLink key={to} to={to} end={to === '/'}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all
              ${isActive
                ? 'bg-accent-green/15 text-accent-green border border-accent-green/20 shadow-glow'
                : 'text-white/65 hover:bg-base-700/70 hover:text-white border border-transparent'}`
            }
          >
            <Icon size={18} />
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>
      <div className="p-4 border-t border-base-600/40">
        <div className="card px-3 py-3 bg-base-900/40">
          <div className="flex items-center gap-2">
            <span className="relative inline-block w-2 h-2 rounded-full bg-accent-green animate-pulse_slow" />
            <span className="text-xs font-semibold text-white/80">Pipeline Online</span>
          </div>
          <p className="text-[10px] text-white/40 mt-1 font-mono">v1.0.0 — YOLOv8s</p>
        </div>
      </div>
    </aside>
  );
}
