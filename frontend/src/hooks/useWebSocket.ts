import { useEffect, useState, useCallback, useRef } from 'react';
import { ProgressUpdate } from '../types/conversion';

// Reconnection configuration
const MAX_RECONNECT_ATTEMPTS = 5;
const INITIAL_RECONNECT_DELAY = 1000; // 1 second
const MAX_RECONNECT_DELAY = 30000; // 30 seconds

export const useWebSocket = (sessionId: string | null) => {
  const [progress, setProgress] = useState<ProgressUpdate | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [reconnectAttempt, setReconnectAttempt] = useState(0);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const shouldReconnectRef = useRef(true);

  // Calculate exponential backoff delay
  const getReconnectDelay = useCallback((attempt: number) => {
    const delay = Math.min(
      INITIAL_RECONNECT_DELAY * Math.pow(2, attempt),
      MAX_RECONNECT_DELAY
    );
    // Add jitter (±20%) to prevent thundering herd
    const jitter = delay * 0.2 * (Math.random() - 0.5);
    return Math.round(delay + jitter);
  }, []);

  const clearReconnectTimeout = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
  }, []);

  const connect = useCallback(() => {
    if (!sessionId) return;

    // Clear any pending reconnect
    clearReconnectTimeout();

    // Close existing connection if any
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/progress/${sessionId}`;

    try {
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        setIsConnected(true);
        setReconnectAttempt(0); // Reset retry counter on successful connection
        if (import.meta.env.DEV) {
          console.log('WebSocket connected');
        }
      };

      ws.onmessage = (event) => {
        try {
          const data: ProgressUpdate = JSON.parse(event.data);
          setProgress(data);

          // Don't reconnect if conversion is complete or failed
          if (data.status === 'completed' || data.status === 'failed') {
            shouldReconnectRef.current = false;
          }
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

      ws.onclose = (event) => {
        setIsConnected(false);
        wsRef.current = null;

        if (import.meta.env.DEV) {
          console.log(`WebSocket disconnected (code: ${event.code}, reason: ${event.reason || 'none'})`);
        }

        // Attempt reconnection if:
        // - We should reconnect (conversion not complete)
        // - We haven't exceeded max attempts
        // - The close wasn't intentional (code 1000 = normal closure)
        if (
          shouldReconnectRef.current &&
          reconnectAttempt < MAX_RECONNECT_ATTEMPTS &&
          event.code !== 1000
        ) {
          const delay = getReconnectDelay(reconnectAttempt);
          if (import.meta.env.DEV) {
            console.log(`Attempting reconnect in ${delay}ms (attempt ${reconnectAttempt + 1}/${MAX_RECONNECT_ATTEMPTS})`);
          }

          reconnectTimeoutRef.current = setTimeout(() => {
            setReconnectAttempt(prev => prev + 1);
            connect();
          }, delay);
        }
      };

      wsRef.current = ws;
    } catch (error) {
      if (import.meta.env.DEV) {
        console.error('Failed to create WebSocket:', error);
      }
    }
  }, [sessionId, reconnectAttempt, getReconnectDelay, clearReconnectTimeout]);

  const disconnect = useCallback(() => {
    shouldReconnectRef.current = false;
    clearReconnectTimeout();

    if (wsRef.current) {
      wsRef.current.close(1000, 'Client disconnect'); // Normal closure
      wsRef.current = null;
      setIsConnected(false);
    }
  }, [clearReconnectTimeout]);

  // Manual reconnect function exposed to consumers
  const reconnect = useCallback(() => {
    shouldReconnectRef.current = true;
    setReconnectAttempt(0);
    connect();
  }, [connect]);

  useEffect(() => {
    // Reset state when sessionId changes
    setProgress(null);
    setReconnectAttempt(0);
    shouldReconnectRef.current = true;

    if (sessionId) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [sessionId, connect, disconnect]);

  return {
    progress,
    isConnected,
    reconnectAttempt,
    maxReconnectAttempts: MAX_RECONNECT_ATTEMPTS,
    reconnect,
  };
};
