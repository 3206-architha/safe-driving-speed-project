import { useEffect, useRef, useState, useCallback } from 'react';
import type { LivePrediction } from '../types';

/**
 * Connects to the backend's /api/ws/predict WebSocket and exposes a
 * `send()` function to push live GPS + speed readings, plus the latest
 * prediction pushed back by the server.
 *
 * Auto-reconnects with backoff if the connection drops — important for
 * a "real-time while driving" use case where network hiccups (tunnels,
 * dead zones) are expected, not exceptional.
 */
export function useLivePrediction() {
  const [latest, setLatest] = useState<LivePrediction | null>(null);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttempts = useRef(0);

  const connect = useCallback(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const ws = new WebSocket(`${protocol}//${host}/api/ws/predict`);

    ws.onopen = () => {
      setConnected(true);
      reconnectAttempts.current = 0;
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data) as LivePrediction;
      setLatest(data);
    };

    ws.onclose = () => {
      setConnected(false);
      // exponential backoff, capped at 10s, so a dropped connection
      // while driving recovers automatically without user action
      const delay = Math.min(1000 * 2 ** reconnectAttempts.current, 10000);
      reconnectAttempts.current += 1;
      setTimeout(connect, delay);
    };

    wsRef.current = ws;
  }, []);

  useEffect(() => {
    connect();
    return () => wsRef.current?.close();
  }, [connect]);

  const send = useCallback((latitude: number, longitude: number, current_speed: number) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ latitude, longitude, current_speed }));
    }
  }, []);

  return { latest, connected, send };
}
