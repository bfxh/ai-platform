import { useEffect, useRef } from 'react';

type SubAgentEvent = 'sub_agent_spawned' | 'sub_agent_completed' | 'sub_agent_failed';
type EventHandler = (data: any) => void;

export function useSubAgentSocket(onEvent: (type: SubAgentEvent, data: any) => void) {
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const ws = new WebSocket(`${protocol}//${window.location.host}/ws`);
    wsRef.current = ws;

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (['sub_agent_spawned', 'sub_agent_completed', 'sub_agent_failed'].includes(msg.type)) {
          onEvent(msg.type as SubAgentEvent, msg.payload);
        }
      } catch (err) {
        console.error('WebSocket parse error:', err);
      }
    };

    ws.onerror = (err) => console.error('WebSocket error:', err);
    ws.onclose = () => console.log('WebSocket closed');

    return () => {
      ws.close();
    };
  }, [onEvent]);

  return wsRef;
}
