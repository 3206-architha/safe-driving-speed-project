import { useEffect, useState } from 'react';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS, CategoryScale, LinearScale, PointElement,
  LineElement, Title, Tooltip, Legend,
} from 'chart.js';
import { useAuth } from '../context/AuthContext';
import { useLivePrediction } from '../services/useLivePrediction';
import { predictionApi, analyticsApi } from '../services/api';
import RiskBadge from '../components/RiskBadge';
import StatCard from '../components/StatCard';
import ScenarioTester from '../components/ScenarioTester';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend);

export default function Dashboard() {
  const { user, logout } = useAuth();
  const { latest, connected, send } = useLivePrediction();
  const [currentSpeed, setCurrentSpeed] = useState(50);
  const [coords, setCoords] = useState<{ lat: number; lng: number } | null>(null);
  const [trend, setTrend] = useState<{ day: string; avg_speed: number }[]>([]);
  const [geoError, setGeoError] = useState('');

  // Get browser GPS location once, then stream it over the WebSocket every 5s
  useEffect(() => {
    if (!navigator.geolocation) {
      setGeoError('Geolocation not supported by this browser');
      return;
    }
    const watchId = navigator.geolocation.watchPosition(
      (pos) => setCoords({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
      () => setGeoError('Location permission denied — using default location'),
      { enableHighAccuracy: true }
    );
    return () => navigator.geolocation.clearWatch(watchId);
  }, []);

  useEffect(() => {
    if (!connected) return;
    const fallback = { lat: 17.385, lng: 78.4867 }; // Hyderabad, used if GPS unavailable
    const interval = setInterval(() => {
      const point = coords ?? fallback;
      send(point.lat, point.lng, currentSpeed);
    }, 5000);
    return () => clearInterval(interval);
  }, [connected, coords, currentSpeed, send]);

  useEffect(() => {
    analyticsApi.trends().then((res) => setTrend(res.data)).catch(() => {});
  }, []);

  const handleManualPredict = async () => {
    const point = coords ?? { lat: 17.385, lng: 78.4867 };
    await predictionApi.predict({
      latitude: point.lat,
      longitude: point.lng,
      current_speed: currentSpeed,
    });
    analyticsApi.trends().then((res) => setTrend(res.data)).catch(() => {});
  };

  const chartData = {
    labels: trend.map((t) => t.day),
    datasets: [
      {
        label: 'Avg recommended speed (km/h)',
        data: trend.map((t) => t.avg_speed),
        borderColor: '#3b82f6',
        backgroundColor: 'rgba(59,130,246,0.15)',
        tension: 0.3,
        fill: true,
      },
    ],
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6">
      <header className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold">Safe Driving Dashboard</h1>
          <p className="text-slate-400 text-sm">
            {user?.name ? `Hi ${user.name}` : ''} · {connected ? (
              <span className="text-green-400">● Live connection active</span>
            ) : (
              <span className="text-amber-400">● Reconnecting...</span>
            )}
          </p>
        </div>
        <button
          onClick={logout}
          className="text-sm text-slate-400 hover:text-slate-100 border border-slate-800 rounded-lg px-3 py-1.5"
        >
          Sign out
        </button>
      </header>

      {geoError && (
        <p className="text-amber-400 text-xs mb-4">{geoError}</p>
      )}

      {/* Live recommendation hero card */}
      <div className="bg-gradient-to-br from-blue-900/40 to-slate-900 border border-slate-800 rounded-2xl p-6 mb-6">
        <div className="flex items-start justify-between flex-wrap gap-4">
          <div>
            <p className="text-slate-400 text-sm mb-1">Recommended Safe Speed</p>
            <p className="text-5xl font-bold">
              {latest ? latest.recommended_speed : '--'}
              <span className="text-lg text-slate-400 ml-2">km/h</span>
            </p>
          </div>
          <div className="text-right">
            {latest && <RiskBadge level={latest.risk_level} size="lg" />}
            {latest && (
              <p className="text-slate-400 text-xs mt-2">
                Confidence: {(latest.confidence_score * 100).toFixed(0)}%
              </p>
            )}
          </div>
        </div>

        <div className="mt-4 flex items-center gap-3">
          <label className="text-sm text-slate-400">Your current speed:</label>
          <input
            type="number"
            value={currentSpeed}
            onChange={(e) => setCurrentSpeed(Number(e.target.value))}
            className="w-24 bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-sm"
          />
          <span className="text-sm text-slate-400">km/h</span>
          <button
            onClick={handleManualPredict}
            className="ml-auto bg-blue-600 hover:bg-blue-500 transition rounded-lg px-4 py-1.5 text-sm font-medium"
          >
            Save this prediction
          </button>
        </div>
      </div>

      {/* XAI explanation panel */}
      {latest?.explanation && (
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 mb-6">
          <h3 className="text-sm font-medium text-slate-300 mb-2">Why this speed?</h3>
          <pre className="text-sm text-slate-400 whitespace-pre-wrap font-sans">{latest.explanation}</pre>
        </div>
      )}

      {/* Stat grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <StatCard label="Connection" value={connected ? 'Live' : 'Reconnecting'} icon="📡" />
        <StatCard label="Current Speed" value={currentSpeed} unit="km/h" icon="🚗" />
        <StatCard
          label="Location"
          value={coords ? `${coords.lat.toFixed(2)}, ${coords.lng.toFixed(2)}` : 'Pending'}
          icon="📍"
        />
        <StatCard label="Risk Level" value={latest?.risk_level ?? '--'} icon="⚠️" />
      </div>

      <div className="mb-6">
        <ScenarioTester />
      </div>

      {/* Trend chart */}

      {/* Trend chart */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5">
        <h3 className="text-sm font-medium text-slate-300 mb-4">Speed Recommendation Trend</h3>
        {trend.length > 0 ? (
          <Line data={chartData} options={{ responsive: true, plugins: { legend: { display: false } } }} />
        ) : (
          <p className="text-slate-500 text-sm">No prediction history yet — save a prediction to see trends.</p>
        )}
      </div>
    </div>
  );
}
