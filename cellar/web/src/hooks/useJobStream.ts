import { useCallback, useEffect, useRef, useState } from 'react';
import { api, type JobEvent } from '../api';

const EVENT_TYPES = [
  'start',
  'info',
  'log',
  'error',
  'run_plan',
  'phase_start',
  'phase_end',
  'wine_start',
  'progress',
  'paused',
  'done',
  'exit',
];

export interface UseJobStreamResult {
  events: JobEvent[];
  running: boolean;
  connect: (jobId: string) => void;
  disconnect: () => void;
  clear: () => void;
}

/**
 * Subscribes to a job's SSE event stream (`GET /api/jobs/{id}/events`).
 * History is replayed by the server on connect. Closes automatically on
 * an `exit` event. If the connection drops, EventSource reconnects by itself
 * and the server resumes after the last event id it sent; events already
 * received are dropped by id, so nothing is appended twice.
 *
 * `onDone` fires on done / paused / exit; `onEvent` fires for every event
 * (used to refresh the wine table live while the tag phase runs).
 */
export function useJobStream(onDone?: () => void, onEvent?: (e: JobEvent) => void): UseJobStreamResult {
  const [events, setEvents] = useState<JobEvent[]>([]);
  const [running, setRunning] = useState(false);
  const esRef = useRef<EventSource | null>(null);
  const onDoneRef = useRef(onDone);
  onDoneRef.current = onDone;
  const onEventRef = useRef(onEvent);
  onEventRef.current = onEvent;

  const disconnect = useCallback(() => {
    esRef.current?.close();
    esRef.current = null;
    setRunning(false);
  }, []);

  const clear = useCallback(() => setEvents([]), []);

  const connect = useCallback(
    (jobId: string) => {
      esRef.current?.close();
      setEvents([]);
      const es = new EventSource(api.jobEventsUrl(jobId));
      esRef.current = es;
      setRunning(true);
      let lastId = -1;

      const handleMessage = (evt: MessageEvent) => {
        const id = evt.lastEventId === '' ? NaN : Number(evt.lastEventId);
        if (Number.isFinite(id)) {
          if (id <= lastId) return;
          lastId = id;
        }
        try {
          const data = JSON.parse(evt.data) as JobEvent;
          const type = data.type ?? evt.type;
          setEvents((prev) => [...prev, { ...data, type }]);
          onEventRef.current?.({ ...data, type });
          if (type === 'exit') {
            setRunning(false);
            es.close();
            onDoneRef.current?.();
          }
          if (type === 'done' || type === 'paused') {
            onDoneRef.current?.();
          }
        } catch {
          // ignore malformed event payloads
        }
      };

      for (const type of EVENT_TYPES) {
        es.addEventListener(type, handleMessage);
      }
      es.onmessage = handleMessage;
      es.onerror = () => {
        // While CONNECTING, EventSource is retrying on its own and the job
        // may well still be running. Only a CLOSED stream (the server
        // refused the reconnect, e.g. it restarted) ends it.
        if (es.readyState === EventSource.CLOSED) setRunning(false);
      };
    },
    [],
  );

  useEffect(() => () => esRef.current?.close(), []);

  return { events, running, connect, disconnect, clear };
}
