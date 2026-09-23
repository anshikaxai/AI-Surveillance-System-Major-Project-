import { useState } from 'react';
import { Cpu, Plus, Save, Wifi, WifiOff, CircleDot } from 'lucide-react';
import { useCameras } from '../hooks/useData';
import { api } from '../services/api';

export default function CamerasPage() {
  const { cameras, loading, refresh } = useCameras();
  const [form, setForm] = useState({ id: '', name: '', location: '', stream_url: '', status: 'offline' });

  const create = async () => {
    if (!form.id || !form.name) return;
    try {
      await api.cameras.create(form);
      setForm({ id: '', name: '', location: '', stream_url: '', status: 'offline' });
      refresh();
    } catch (e) {
      alert(e.response?.data?.detail || e.message);
    }
  };

  const toggle = async (c, target) => {
    try {
      await api.cameras.status(c.id, target);
      refresh();
    } catch (e) {
      alert(e.response?.data?.detail || e.message);
    }
  };

  return (
    <div className="space-y-5 max-w-5xl">
      <div>
        <h1 className="text-2xl font-bold text-white">Camera Inventory</h1>
        <p className="text-sm text-white/50 mt-1">Registered cameras, stream URLs, and operational status.</p>
      </div>
      <div className="card p-5 animate-slide_in">
        <h3 className="font-semibold text-white mb-3 flex items-center gap-2"><Plus size={16} /> Register Camera</h3>
        <div className="grid md:grid-cols-2 gap-3">
          <input className="input" placeholder="ID (e.g. cam_001)"
            value={form.id} onChange={e => setForm({ ...form, id: e.target.value })} />
          <input className="input" placeholder="Name"
            value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} />
          <input className="input md:col-span-2" placeholder="Location"
            value={form.location} onChange={e => setForm({ ...form, location: e.target.value })} />
          <input className="input md:col-span-2" placeholder="Stream URL (RTSP / file path / camera index)"
            value={form.stream_url} onChange={e => setForm({ ...form, stream_url: e.target.value })} />
        </div>
        <div className="mt-3 flex justify-end">
          <button onClick={create} disabled={!form.id || !form.name} className="btn-primary flex items-center gap-1.5">
            <Save size={16} /> Register
          </button>
        </div>
      </div>
      <div className="card overflow-hidden animate-slide_in">
        <table className="w-full text-sm">
          <thead className="bg-base-900/50 text-white/60 uppercase tracking-wider text-[11px]">
            <tr>
              <th className="text-left px-5 py-3">ID</th>
              <th className="text-left px-5 py-3">Name / Location</th>
              <th className="text-left px-5 py-3">Stream</th>
              <th className="text-left px-5 py-3">Status</th>
              <th className="text-right px-5 py-3">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-base-600/30">
            {loading && (
              <tr><td colSpan="5" className="text-center p-8 text-white/40">Loading…</td></tr>
            )}
            {!loading && !cameras?.length && (
              <tr><td colSpan="5" className="text-center p-8 text-white/40">
                <Cpu size={28} className="mx-auto mb-2 opacity-40" />No cameras registered.
              </td></tr>
            )}
            {cameras?.map(c => (
              <tr key={c.id} className="hover:bg-base-700/20">
                <td className="px-5 py-3 font-mono text-white/80">{c.id}</td>
                <td className="px-5 py-3">
                  <p className="text-white font-medium">{c.name}</p>
                  <p className="text-xs text-white/40">{c.location || '—'}</p>
                </td>
                <td className="px-5 py-3 text-xs font-mono text-white/50 truncate max-w-xs">{c.stream_url || '—'}</td>
                <td className="px-5 py-3">
                  {c.status === 'online' ? (
                    <span className="severity-low"><Wifi size={12} /> Online</span>
                  ) : (
                    <span className="severity-info"><WifiOff size={12} /> Offline</span>
                  )}
                </td>
                <td className="px-5 py-3 text-right space-x-1">
                  <button onClick={() => toggle(c, c.status === 'online' ? 'offline' : 'online')}
                    className="btn-secondary !py-1.5 !px-3 text-xs">
                    <CircleDot size={12} className="inline mr-1" />
                    Toggle
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
