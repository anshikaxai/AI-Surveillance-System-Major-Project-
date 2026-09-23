import { useState } from 'react';
import { Send, Wand2, Check, AlertTriangle, Code, Loader2, Sparkles } from 'lucide-react';
import { api } from '../services/api';

const SUGGESTIONS = [
  'Monitor main gate after 8 PM',
  'Loitering threshold 2 minutes on parking zone',
  'Alert crowd if more than 10 people at entrance',
  'Watch parking during night hours',
  'Disable loitering alerts on lobby during business hours',
];

export default function NLPCommandPanel({ compact = false }) {
  const [command, setCommand] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [cameraId, setCameraId] = useState('cam_001');

  const run = async (mode) => {
    if (!command.trim()) return;
    setLoading(true);
    setResult(null);
    try {
      const r = mode === 'parse'
        ? await api.nlp.parse(command, cameraId)
        : await api.nlp.preview(command, cameraId);
      setResult(r);
    } catch (e) {
      setResult({ error: e.response?.data?.detail || e.message, confidence: 0 });
    } finally {
      setLoading(false);
    }
  };

  const onKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      run('parse');
    }
  };

  return (
    <div className={`card ${compact ? '' : 'animate-slide_in'} overflow-hidden`}>
      <div className="px-5 py-4 border-b border-base-600/40 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-accent-violet to-accent-cyan flex items-center justify-center">
            <Wand2 className="text-white" size={18} />
          </div>
          <div>
            <h3 className="font-semibold text-white">NLP → Rule Engine</h3>
            <p className="text-xs text-white/45 mt-0.5">Describe rules in plain English → auto-apply to ROI config</p>
          </div>
        </div>
        <select value={cameraId} onChange={(e) => setCameraId(e.target.value)}
          className="input !py-1.5 !px-3 text-xs w-auto">
          <option value="cam_001">cam_001 — Main Gate</option>
          <option value="cam_002">cam_002 — Parking</option>
        </select>
      </div>

      <div className="p-5 space-y-4">
        <div className="relative">
          <Sparkles size={16} className="absolute top-3 left-3 text-accent-violet/80" />
          <input
            className="input !pl-10 !pr-28 min-h-[48px]"
            placeholder="e.g. Monitor main gate after 8 PM with loitering at 90 seconds"
            value={command}
            onChange={(e) => setCommand(e.target.value)}
            onKeyDown={onKey}
          />
          <div className="absolute top-1.5 right-1.5 flex items-center gap-1">
            <button onClick={() => run('preview')} disabled={loading || !command}
              className="btn-secondary !py-1.5 !px-3 text-xs flex items-center gap-1">
              <Code size={12} /> Preview
            </button>
            <button onClick={() => run('parse')} disabled={loading || !command}
              className="btn-primary !py-1.5 !px-3 text-xs flex items-center gap-1">
              {loading ? <Loader2 size={12} className="animate-spin" /> : <Send size={12} />}
              Apply
            </button>
          </div>
        </div>

        {!result && !compact && (
          <div className="space-y-2">
            <p className="text-[11px] uppercase tracking-wider text-white/35 font-semibold">Suggestions</p>
            <div className="flex flex-wrap gap-2">
              {SUGGESTIONS.map((s) => (
                <button key={s} onClick={() => setCommand(s)}
                  className="text-xs px-3 py-1.5 rounded-full bg-base-700/70 text-white/70 border border-base-600/50 hover:bg-base-600 hover:text-white transition-colors">
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {result && !result.error && (
          <div className="space-y-3 border border-base-600/40 rounded-xl p-4 bg-base-900/40 animate-slide_in">
            <div className="flex items-center justify-between flex-wrap gap-2">
              <div className="flex items-center gap-2">
                {result.applied
                  ? <span className="chip bg-accent-green/15 text-accent-green border-accent-green/30"><Check size={12} /> Applied</span>
                  : <span className="chip bg-accent-amber/15 text-accent-amber border-accent-amber/30"><AlertTriangle size={12} /> Not applied</span>}
                <span className={`chip ${result.confidence >= 0.7 ? 'severity-low' : result.confidence >= 0.5 ? 'severity-medium' : 'severity-high'}`}>
                  Confidence {(result.confidence * 100).toFixed(0)}%
                </span>
              </div>
              <p className="text-[11px] text-white/50">{result.explanation}</p>
            </div>
            {result.warnings?.length > 0 && (
              <ul className="list-disc list-inside text-[11px] text-accent-amber/80 space-y-0.5">
                {result.warnings.map((w, i) => <li key={i}>{w}</li>)}
              </ul>
            )}
            <div>
              <p className="text-[10px uppercase tracking-wider text-white/35 font-semibold mb-1.5">Generated JSON payload</p>
              <pre className="text-[11px] font-mono text-white/75 bg-base-900 rounded-lg p-3 border border-base-600/40 overflow-x-auto">
{JSON.stringify(result.json_payload, null, 2)}
              </pre>
            </div>
          </div>
        )}
        {result?.error && (
          <div className="severity-critical p-3 rounded-lg text-[12px]">
            Error: {result.error}
          </div>
        )}
      </div>
    </div>
  );
}
