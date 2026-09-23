import { Bell, Search, RefreshCw } from 'lucide-react';
import { useState, useEffect } from 'react';
import { api } from '../services/api';

export default function TopBar({ onRefresh }) {
  const [now, setNow] = useState(new Date());
  const [health, setHealth] = useState({ status: 'unknown', database: 'unknown' });

  useEffect(() => {
    const t = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(t);
  }, []);

  useEffect(() => {
    const check = async () => {
      try { setHealth(await api.health()); } catch { setHealth({ status: 'degraded', database: 'error' }); }
    };
    check();
    const t = setInterval(check, 15000);
    return () => clearInterval(t);
  }, []);

  const sev = health.status === 'healthy' ? 'text-accent-green'
    : health.status === 'degraded' ? 'text-accent-amber' : 'text-white/40';

  return (
    <header className="sticky top-0 z-10 h-16 bg-base-900/80 backdrop-blur-md border-b border-base-600/30 px-6 flex items-center gap-6">
      <div className="flex items-center gap-2 flex-1 max-w-md">
        <Search size={16} className="text-white/40" />
        <input className="bg-transparent outline-none text-sm text-white/80 placeholder-white/30 w-full"
          placeholder="Search events, tracks, license plates..." />
      </div>
      <div className="hidden md:flex items-center gap-4 text-xs">
        <div className="flex items-center gap-2 font-mono text-white/50">
          <span className={`w-2 h-2 rounded-full ${sev}`} />
          <span className="uppercase tracking-wider">API: {health.status}</span>
          <span className="mx-2 text-white/20">|</span>
          <span className="uppercase tracking-wider">DB: {health.database}</span>
        </div>
      </div>
      <div className="flex items-center gap-3">
        <button onClick={onRefresh} className="btn-secondary !py-1.5 !px-3 text-xs flex items-center gap-1.5">
          <RefreshCw size={14} /> Refresh
        </button>
        <button className="relative p-2 rounded-lg hover:bg-base-700 text-white/60">
          <Bell size={18} />
          <span className="absolute top-1 right-1 w-2 h-2 rounded-full bg-accent-red" />
        </button>
        <div className="text-right leading-tight pl-3 border-l border-base-600/40">
          <p className="text-sm font-mono text-white/80">{now.toLocaleTimeString()}</p>
          <p className="text-[10px] uppercase tracking-wider text-white/40">{now.toLocaleDateString()}</p>
        </div>
      </div>
    </header>
  );
}
