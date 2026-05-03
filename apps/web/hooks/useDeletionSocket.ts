import { useEffect, useRef } from 'react';

type DeletionEvent = 'deletion_requested' | 'deletion_approved' | 'deletion_rejected';
type EventHandler = (data: any) => void;

export function useDeletionSocket(onEvent: (type: DeletionEvent, data: any) => void) {
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const ws = new WebSocket(`${protocol}//${window.location.host}/ws`);
    wsRef.current = ws;

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (['deletion_requested', 'deletion_approved', 'deletion_rejected'].includes(msg.type)) {
          onEvent(msg.type as DeletionEvent, msg.payload);
        }
      } catch (err) {
        console.error('WebSocket parse error:', err);
      }
    };

    return () => ws.close();
  }, [onEvent]);

  return wsRef;
}
