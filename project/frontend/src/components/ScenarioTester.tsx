import { useState } from 'react';
import api from '../services/api';
import RiskBadge from './RiskBadge';

interface ScenarioResult {
  recommended_speed: number;
  risk_level: 'Low' | 'Medium' | 'High';
  confidence_score: number;
  explanation: string;
}

const PRESETS: Record<string, {
  label: string;
  icon: string;
  road_condition: string;
  rainfall: number;
  visibility: number;
  traffic_density: string;
  wind_speed: number;
  temperature: number;
  humidity: number;
}> = {
  clear: {
    label: 'Clear & Dry', icon: '☀️',
    road_condition: 'dry', rainfall: 0, visibility: 10,
    traffic_density: 'low', wind_speed: 10, temperature: 25, humidity: 50,
  },
  rain: {
    label: 'Heavy Rain', icon: '🌧️',
    road_condition: 'wet', rainfall: 15, visibility: 2,
    traffic_density: 'high', wind_speed: 25, temperature: 22, humidity: 90,
  },
  fog: {
    label: 'Fog', icon: '🌫️',
    road_condition: 'wet', rainfall: 0, visibility: 0.5,
    traffic_density: 'medium', wind_speed: 5, temperature: 15, humidity: 95,
  },
  ice: {
    label: 'Ice / Snow', icon: '❄️',
    road_condition: 'ice', rainfall: 2, visibility: 4,
    traffic_density: 'medium', wind_speed: 20, temperature: -2, humidity: 80,
  },
};

export default function ScenarioTester() {
  const [selected, setSelected] = useState<string>('clear');
  const [result, setResult] = useState<ScenarioResult | null>(null);
  const [loading, setLoading] = useState(false);

  const runScenario = async (key: string) => {
    setSelected(key);
    setLoading(true);
    try {
      const preset = PRESETS[key];
      const { data } = await api.post<ScenarioResult>('/predict/scenario', {
        road_condition: preset.road_condition,
        rainfall: preset.rainfall,
        visibility: preset.visibility,
        traffic_density: preset.traffic_density,
        wind_speed: preset.wind_speed,
        temperature: preset.temperature,
        humidity: preset.humidity,
        current_speed: 50,
      });
      setResult(data);
    } catch {
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5">
      <h3 className="text-sm font-medium text-slate-300 mb-1">Test Different Conditions</h3>
      <p className="text-slate-500 text-xs mb-4">
        See how the recommendation changes across weather scenarios — the model responds
        to road, visibility, and traffic conditions, not to your driving speed.
      </p>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mb-4">
        {Object.entries(PRESETS).map(([key, preset]) => (
          <button
            key={key}
            onClick={() => runScenario(key)}
            className={`rounded-lg px-3 py-2.5 text-sm border transition ${
              selected === key
                ? 'bg-blue-600 border-blue-500 text-white'
                : 'bg-slate-800 border-slate-700 text-slate-300 hover:border-slate-600'
            }`}
          >
            <span className="mr-1.5">{preset.icon}</span>
            {preset.label}
          </button>
        ))}
      </div>

      {loading && <p className="text-slate-500 text-sm">Calculating...</p>}

      {!loading && result && (
        <div className="bg-slate-800/60 rounded-lg p-4 flex items-start justify-between gap-4 flex-wrap">
          <div>
            <p className="text-slate-400 text-xs mb-1">Recommended Speed</p>
            <p className="text-3xl font-bold">
              {result.recommended_speed} <span className="text-sm text-slate-400">km/h</span>
            </p>
          </div>
          <div className="text-right">
            <RiskBadge level={result.risk_level} size="lg" />
            <p className="text-slate-400 text-xs mt-2">
              Confidence: {(result.confidence_score * 100).toFixed(0)}%
            </p>
          </div>
        </div>
      )}
    </div>
  );
}