import { useEffect, useState, useCallback, useRef } from 'react';
import { ProgressUpdate } from '../types/conversion';

export const useWebSocket = (sessionId: string | null) => {
  const [progress, setProgress] = useState<ProgressUpdate | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  const connect = useCallback(() => {
    if (!sessionId) return;

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/progress/${sessionId}`;

    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      setIsConnected(true);
      if (import.meta.env.DEV) {
        console.log('WebSocket connected');
      }
    };

    ws.onmessage = (event) => {
      try {
        const data: ProgressUpdate = JSON.parse(event.data);
        setProgress(data);
      } catch (error) {
        if (import.meta.env.DEV) {
          console.error('Error parsing WebSocket message:', error);
        }
      }
    };

    ws.onerror = (error) => {
      if (import.meta.env.DEV) {
        console.error('WebSocket error:', error);
      }
    };

    ws.onclose = () => {
      setIsConnected(false);
      if (import.meta.env.DEV) {
        console.log('WebSocket disconnected');
      }
    };

    wsRef.current = ws;
  }, [sessionId]);

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
      setIsConnected(false);
    }
  }, []);

  useEffect(() => {
    // Reset progress when sessionId changes to avoid stale data
    setProgress(null);

    if (sessionId) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [sessionId, connect, disconnect]);

  return { progress, isConnected };
};
