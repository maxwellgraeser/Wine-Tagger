import { useCallback, useEffect, useRef, useState } from 'react';
import { api, type JobEvent } from '../api';

const EVENT_TYPES = [
  'start',
  'info',
  'log',
  'error',
  'phase_start',
  'phase_end',
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
 * an `exit` event.
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

      const handleMessage = (evt: MessageEvent) => {
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
        // EventSource retries automatically; if the job already finished
        // the server will have closed the stream, so just stop showing
        // "running" after a failure.
        setRunning(false);
      };
    },
    [],
  );

  useEffect(() => () => esRef.current?.close(), []);

  return { events, running, connect, disconnect, clear };
}
