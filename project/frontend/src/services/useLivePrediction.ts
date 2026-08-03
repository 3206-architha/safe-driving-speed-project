import { useEffect, useRef, useState, useCallback } from 'react';
import type { LivePrediction } from '../types';
import { API_BASE_URL } from './api';

export function useLivePrediction() {
  const [latest, setLatest] = useState<LivePrediction | null>(null);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttempts = useRef(0);

  const connect = useCallback(() => {
    const wsUrl = API_BASE_URL.replace(/^https:/, 'wss:').replace(/^http:/, 'ws:');
    const ws = new WebSocket(`${wsUrl}/api/ws/predict`);

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
