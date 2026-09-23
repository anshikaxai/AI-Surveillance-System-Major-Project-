import { useState, useEffect } from 'react';
import { Save, Settings as SettingsIcon } from 'lucide-react';
import { api } from '../services/api';

export default function SettingsPage() {
  const [cameraId, setCameraId] = useState('cam_001');
  const [jsonText, setJsonText] = useState('{  }');
  const [msg, setMsg] = useState('');

  useEffect(() => {
    (async () => {
      try {
        const r = await api.config.get(cameraId);
        setJsonText(JSON.stringify(r.config || {}, null, 2));
      } catch {}
    })();
  }, [cameraId]);

  const save = async () => {
    try {
      const cfg = JSON.parse(jsonText);
      const r = await api.config.upsert({ camera_id: cameraId, config: cfg, updated_by: 'operator@university' });
      setMsg(`Saved at ${new Date(r.updated_at * 1000).toLocaleTimeString()} by ${r.updated_by}`);
    } catch (e) {
      setMsg('Error: ' + (e.response?.data?.detail || e.message));
    }
  };

  return (
    <div className="space-y-5 max-w-4xl">
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <SettingsIcon size={22} className="text-accent-cyan" /> Pipeline Config
        </h1>
        <p className="text-sm text-white/50 mt-1">
          Low-level per-camera pipeline configuration. Stored in PostgreSQL as JSONB and merged at edge-node boot.
        </p>
      </div>

      <div className="card p-5 animate-slide_in space-y-4">
        <div>
          <label className="text-[11px] uppercase tracking-wider text-white/40 mb-1 block">Camera</label>
          <select className="input" value={cameraId} onChange={e => setCameraId(e.target.value)}>
            <option value="cam_001">cam_001 — Main Gate</option>
            <option value="cam_002">cam_002 — Parking</option>
          </select>
        </div>
        <div>
          <label className="text-[11px] uppercase tracking-wider text-white/40 mb-1 block">config (JSON)</label>
          <textarea
            className="input font-mono text-xs h-96"
            spellCheck={false}
            value={jsonText}
            onChange={e => setJsonText(e.target.value)}
          />
        </div>
        {msg && <p className={`text-xs ${msg.startsWith('Error') ? 'text-accent-red' : 'text-accent-green'}`}>{msg}</p>}
        <div className="flex justify-end gap-2">
          <button onClick={save} className="btn-primary flex items-center gap-1.5"><Save size={16} /> Persist to DB</button>
        </div>
      </div>

      <div className="card p-5 animate-slide_in">
        <h3 className="font-semibold text-white mb-2">Suggested schema (copy-paste)</h3>
        <pre className="text-[11px] font-mono text-white/70 bg-base-900 rounded-lg p-4 overflow-x-auto">
{JSON.stringify({
  detection_model: "yolov8s.pt",
  detection_confidence: 0.45,
  frame_skip: 0,
  track_buffer: 30,
  behaviour_enabled: true,
  walking_speed_px_s: 80,
  running_speed_px_s: 200,
  alpr_enabled: true,
  alpr_ocr_interval_frames: 30,
  occupancy_enabled: true,
  occupancy_interval_frames: 60,
  event_cooldown_sec: 15,
  api_base_url: "http://localhost:8000"
}, null, 2)}
        </pre>
      </div>
    </div>
  );
}
