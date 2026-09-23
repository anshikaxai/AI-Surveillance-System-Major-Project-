import NLPCommandPanel from '../components/NLPCommandPanel';

export default function NLPPage() {
  return (
    <div className="space-y-5 max-w-5xl">
      <div>
        <h1 className="text-2xl font-bold text-white">NLP → Configuration</h1>
        <p className="text-sm text-white/50 mt-1">
          Natural-language command panel parses operator instructions into structured JSON payloads
          that update the rule engine's ROI configuration via the backend API.
        </p>
      </div>
      <NLPCommandPanel />
      <div className="card p-5 animate-slide_in">
        <h3 className="font-semibold text-white mb-2">How the Parser Works</h3>
        <ol className="list-decimal list-inside text-sm text-white/65 space-y-1.5">
          <li><span className="text-white/80 font-medium">ROI recognition:</span> matches zones by name (main gate, parking, entrance, etc.)</li>
          <li><span className="text-white/80 font-medium">Feature detection:</span> keywords like <code className="text-accent-cyan">loiter</code>, <code className="text-accent-cyan">crowd</code>, <code className="text-accent-cyan">monitor</code> identify the intent</li>
          <li><span className="text-white/80 font-medium">Threshold extraction:</span> numbers with units (seconds, minutes, persons) become thresholds</li>
          <li><span className="text-white/80 font-medium">Time expressions:</span> "after 8 PM", "between 9 and 17", "night" → active_hours [start, end]</li>
          <li><span className="text-white/80 font-medium">Confidence gating:</span> confidence ≥ 0.45 auto-applies; otherwise returns a preview with warnings</li>
        </ol>
      </div>
    </div>
  );
}
