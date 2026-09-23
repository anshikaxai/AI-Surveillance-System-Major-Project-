import { MapPin, Plus, Trash2, Save, Clock, Users, Calendar } from 'lucide-react';
import { useState } from 'react';
import { useROIs, useCameras } from '../hooks/useData';

export default function ROIManager() {
  const [cameraId, setCameraId] = useState('cam_001');
  const { cameras } = useCameras();
  const { rois, loading, refresh, save, remove } = useROIs(cameraId);
  const [editing, setEditing] = useState(null);

  const blank = () => ({
    camera_id: cameraId,
    name: 'New ROI',
    polygon: [[200, 100], [500, 100], [500, 400], [200, 400]],
    loitering_threshold_sec: 30,
    crowd_threshold: 5,
    color: '#10B981',
    active_hours: null,
    enabled: true,
  });

  const updateField = (key, value) => setEditing(prev => ({ ...prev, [key]: value }));

  const startEdit = (r) => {
    const src = r || blank();
    setEditing({
      ...src,
      polygon: (src.polygon || []).map(p => [Number(p[0]), Number(p[1])]),
      active_hours: src.active_hours ? [Number(src.active_hours[0]), Number(src.active_hours[1])] : null,
    });
  };

  const commit = async () => {
    try {
      const payload = {
        ...editing,
        loitering_threshold_sec: Number(editing.loitering_threshold_sec),
        crowd_threshold: Number(editing.crowd_threshold),
      };
      await save(payload, editing.id);
      setEditing(null);
      refresh();
    } catch (e) {
      alert(e.response?.data?.detail || e.message);
    }
  };

  const polyToText = (p) => (p || []).map(pt => `${pt[0]},${pt[1]}`).join(' ');
  const textToPoly = (s) => s
    .split(/[\s;]+/)
    .filter(Boolean)
    .map(pair => pair.split(',').map(Number))
    .filter(p => p.length === 2 && p.every(n => !Number.isNaN(n)));

  return (
    <div className="space-y-5">
      <div className="card p-5 animate-slide_in">
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div>
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <MapPin size={20} className="text-accent-green" /> Regions of Interest (ROI) Manager
            </h2>
            <p className="text-sm text-white/50 mt-1">Configure spatial rules that feed the Event Intelligence Layer.</p>
          </div>
          <div className="flex items-center gap-3">
            <select className="input !py-2 !px-3 text-sm w-auto"
              value={cameraId}
              onChange={(e) => { setCameraId(e.target.value); setEditing(null); }}>
              {(cameras?.length ? cameras : [{ id: 'cam_001', name: 'Main Gate Camera' }]).map(c => (
                <option key={c.id} value={c.id}>{c.id} — {c.name}</option>
              ))}
            </select>
            <button onClick={() => startEdit(null)} className="btn-primary flex items-center gap-1.5">
              <Plus size={16} /> New ROI
            </button>
          </div>
        </div>
      </div>

      <div className="grid lg:grid-cols-3 gap-5">
        <div className="lg:col-span-2 space-y-4">
          {loading && <p className="text-white/40 text-sm">Loading ROIs…</p>}
          {!loading && !rois?.length && (
            <div className="card p-10 text-center text-white/40">
              <MapPin size={36} className="mx-auto mb-2 opacity-50" />
              <p>No ROIs configured. Click
                <button className="text-accent-green underline-offset-2 underline mx-1"
                  onClick={() => startEdit(null)}>Create</button>the first one.
              </p>
            </div>
          )}
          {rois?.map(r => (
            <div key={r.id} className="card p-5 animate-slide_in">
              <div className="flex items-start justify-between gap-3 flex-wrap">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg flex items-center justify-center shrink-0"
                    style={{ background: r.color + '30', border: `1px solid ${r.color}` }}>
                    <MapPin size={18} style={{ color: r.color }} />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <h4 className="font-semibold text-white">{r.name}</h4>
                      <span className={r.enabled ? 'severity-low' : 'severity-info'}>
                        {r.enabled ? 'ACTIVE' : 'DISABLED'}
                      </span>
                    </div>
                    <p className="text-[11px] text-white/45 font-mono">{r.camera_id} · polygon: {(r.polygon || []).length} vertices</p>
                  </div>
                </div>
                <div className="flex items-center gap-1">
                  <button className="btn-secondary !py-1.5 !px-3 text-xs"
                    onClick={() => startEdit(r)}>
                    <Save size={12} className="inline mr-1" /> Edit
                  </button>
                  <button className="btn-danger !py-1.5 !px-3 text-xs"
                    onClick={async () => { if (confirm('Delete ROI?')) { await remove(r.id); refresh(); } }}>
                    <Trash2 size={12} className="inline mr-1" /> Delete
                  </button>
                </div>
              </div>

              <div className="mt-4 grid grid-cols-3 gap-3 text-xs">
                <div className="bg-base-900/40 rounded-lg p-3 border border-base-600/30 flex items-center gap-2">
                  <Clock size={14} className="text-accent-amber" />
                  <div>
                    <p className="text-white/40 uppercase tracking-wider text-[10px]">Loiter</p>
                    <p className="text-white font-semibold">{r.loitering_threshold_sec}s threshold</p>
                  </div>
                </div>
                <div className="bg-base-900/40 rounded-lg p-3 border border-base-600/30 flex items-center gap-2">
                  <Users size={14} className="text-accent-cyan" />
                  <div>
                    <p className="text-white/40 uppercase tracking-wider text-[10px]">Crowd</p>
                    <p className="text-white font-semibold">{r.crowd_threshold} people</p>
                  </div>
                </div>
                <div className="bg-base-900/40 rounded-lg p-3 border border-base-600/30 flex items-center gap-2">
                  <Calendar size={14} className="text-accent-violet" />
                  <div>
                    <p className="text-white/40 uppercase tracking-wider text-[10px]">Active Hours</p>
                    <p className="text-white font-semibold">
                      {r.active_hours ? `${String(r.active_hours[0]).padStart(2, '0')}:00 – ${String(r.active_hours[1]).padStart(2, '0')}:00` : 'Always'}
                    </p>
                  </div>
                </div>
              </div>

              <div className="mt-3">
                <svg viewBox="0 0 1000 600" className="w-full h-32 bg-base-900/60 rounded-lg border border-base-600/30">
                  <polygon
                    points={(r.polygon || []).map(p => `${(Number(p[0]) || 0) * 1.15},${(Number(p[1]) || 0) * 1.1}`).join(' ')}
                    fill={r.color + '33'}
                    stroke={r.color}
                    strokeWidth={3}
                  />
                  <text x="10" y="20" fontSize="10" fill="#94a3b8" fontFamily="monospace">Preview (scaled)</text>
                </svg>
              </div>
            </div>
          ))}
        </div>

        <div>
          {editing ? (
            <div className="card p-5 animate-slide_in sticky top-24 space-y-4">
              <h3 className="font-semibold text-white text-base">
                {editing.id ? `Editing: ${editing.name}` : 'New ROI'}
              </h3>
              <div>
                <label className="text-[11px] uppercase tracking-wider text-white/40 mb-1 block">Name</label>
                <input className="input" value={editing.name} onChange={e => updateField('name', e.target.value)} />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-[11px] uppercase tracking-wider text-white/40 mb-1 block">Loiter (s)</label>
                  <input type="number" className="input" value={editing.loitering_threshold_sec}
                    onChange={e => updateField('loitering_threshold_sec', e.target.value)} />
                </div>
                <div>
                  <label className="text-[11px] uppercase tracking-wider text-white/40 mb-1 block">Crowd count</label>
                  <input type="number" className="input" value={editing.crowd_threshold}
                    onChange={e => updateField('crowd_threshold', e.target.value)} />
                </div>
              </div>
              <div>
                <label className="text-[11px] uppercase tracking-wider text-white/40 mb-1 block">Polygon (x,y pairs, space separated)</label>
                <input className="input font-mono text-xs" value={polyToText(editing.polygon)}
                  onChange={e => updateField('polygon', textToPoly(e.target.value))} />
                <p className="text-[10px] text-white/30 mt-1">e.g. 200,100 500,100 500,400 200,400</p>
              </div>
              <div>
                <label className="text-[11px] uppercase tracking-wider text-white/40 mb-1 block">Active hours (start – end, 24h format)</label>
                <div className="grid grid-cols-2 gap-2">
                  <input type="number" min="0" max="23" className="input" value={editing.active_hours?.[0] ?? ''}
                    placeholder="0"
                    onChange={e => updateField('active_hours', [Number(e.target.value || 0), editing.active_hours?.[1] ?? 23])} />
                  <input type="number" min="0" max="23" className="input" value={editing.active_hours?.[1] ?? ''}
                    placeholder="23"
                    onChange={e => updateField('active_hours', [editing.active_hours?.[0] ?? 0, Number(e.target.value || 23)])} />
                </div>
                <button onClick={() => updateField('active_hours', null)} className="text-[11px] text-white/40 hover:text-white/70 mt-1">
                  Clear (always active)
                </button>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-[11px] uppercase tracking-wider text-white/40 mb-1 block">Color</label>
                  <input type="color" className="input h-10 w-full p-1 cursor-pointer rounded-lg"
                    value={editing.color || '#10B981'}
                    onChange={e => updateField('color', e.target.value)} />
                </div>
                <div>
                  <label className="text-[11px] uppercase tracking-wider text-white/40 mb-1 block">Enabled</label>
                  <select className="input !py-2" value={String(editing.enabled)}
                    onChange={e => updateField('enabled', e.target.value === 'true')}>
                    <option value="true">Yes</option>
                    <option value="false">No</option>
                  </select>
                </div>
              </div>
              <div className="flex gap-2 pt-2">
                <button onClick={() => setEditing(null)} className="btn-secondary flex-1">Cancel</button>
                <button onClick={commit} className="btn-primary flex-1 flex items-center justify-center gap-1.5">
                  <Save size={16} /> Save
                </button>
              </div>
            </div>
          ) : (
            <div className="card p-6 text-white/50 text-sm">
              <h4 className="font-semibold text-white/80 mb-2">Editing panel</h4>
              <p>Select an ROI or create a new one to configure loitering thresholds, crowd limits, active hours, and polygon vertices.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
