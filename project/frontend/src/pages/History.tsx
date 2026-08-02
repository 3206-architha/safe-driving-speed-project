import { useEffect, useState } from 'react';
import { predictionApi } from '../services/api';
import type { Prediction } from '../types';
import RiskBadge from '../components/RiskBadge';

export default function History() {
  const [predictions, setPredictions] = useState<Prediction[]>([]);
  const [filter, setFilter] = useState<string>('');
  const [loading, setLoading] = useState(true);

  const load = () => {
    setLoading(true);
    predictionApi
      .history({ risk_level: filter || undefined, limit: 50 })
      .then((res) => setPredictions(res.data))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filter]);

  const exportCsv = () => {
    const headers = ['Date', 'Speed (km/h)', 'Risk', 'Confidence', 'Road', 'Traffic'];
    const rows = predictions.map((p) => [
      new Date(p.created_at).toLocaleString(),
      p.recommended_speed,
      p.risk_level,
      p.confidence_score,
      p.road_condition ?? '',
      p.traffic_density ?? '',
    ]);
    const csv = [headers, ...rows].map((r) => r.join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'prediction_history.csv';
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6">
      <div className="flex items-center justify-between mb-6 flex-wrap gap-3">
        <h1 className="text-xl font-semibold">Prediction History</h1>
        <div className="flex items-center gap-3">
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-sm"
          >
            <option value="">All risk levels</option>
            <option value="Low">Low</option>
            <option value="Medium">Medium</option>
            <option value="High">High</option>
          </select>
          <button
            onClick={exportCsv}
            className="bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-lg px-3 py-1.5 text-sm"
          >
            Export CSV
          </button>
        </div>
      </div>

      <div className="bg-slate-900/80 border border-slate-800 rounded-xl overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-900 text-slate-400 text-xs uppercase">
            <tr>
              <th className="text-left px-4 py-3">Date</th>
              <th className="text-left px-4 py-3">Speed</th>
              <th className="text-left px-4 py-3">Risk</th>
              <th className="text-left px-4 py-3">Confidence</th>
              <th className="text-left px-4 py-3">Road</th>
              <th className="text-left px-4 py-3">Traffic</th>
            </tr>
          </thead>
          <tbody>
            {loading && (
              <tr><td colSpan={6} className="text-center text-slate-500 py-8">Loading...</td></tr>
            )}
            {!loading && predictions.length === 0 && (
              <tr><td colSpan={6} className="text-center text-slate-500 py-8">No predictions yet</td></tr>
            )}
            {predictions.map((p) => (
              <tr key={p.id} className="border-t border-slate-800 hover:bg-slate-800/40">
                <td className="px-4 py-3">{new Date(p.created_at).toLocaleString()}</td>
                <td className="px-4 py-3 font-medium">{p.recommended_speed} km/h</td>
                <td className="px-4 py-3"><RiskBadge level={p.risk_level} /></td>
                <td className="px-4 py-3">{(p.confidence_score * 100).toFixed(0)}%</td>
                <td className="px-4 py-3 capitalize">{p.road_condition ?? '-'}</td>
                <td className="px-4 py-3 capitalize">{p.traffic_density ?? '-'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
