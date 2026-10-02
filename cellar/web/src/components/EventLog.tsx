import { useEffect, useRef } from 'react';
import type { JobEvent } from '../api';

function colorFor(type: string): string {
  if (type === 'error') return 'text-red-600';
  if (type.startsWith('phase_')) return 'font-bold text-wine';
  if (type === 'progress') return 'text-ink';
  if (type === 'done' || type === 'exit') return 'font-semibold text-green-700';
  if (type === 'paused') return 'font-semibold text-amber-700';
  return 'text-muted';
}

// The progress bars show the wine being worked on; one log line per wine
// start would only double the log.
const HIDDEN = new Set(['wine_start']);

export function EventLog({ events: all, height = 'h-64' }: { events: JobEvent[]; height?: string }) {
  const ref = useRef<HTMLDivElement>(null);
  const events = all.filter((e) => !HIDDEN.has(e.type));

  useEffect(() => {
    if (ref.current) {
      ref.current.scrollTop = ref.current.scrollHeight;
    }
  }, [events.length]);

  return (
    <div
      ref={ref}
      className={`${height} overflow-y-auto rounded-md border border-parchment bg-white p-2 font-mono text-xs leading-relaxed`}
    >
      {events.length === 0 && <div className="text-muted">No events yet.</div>}
      {events.map((e, i) => (
        <div key={i} className={colorFor(e.type)}>
          <span className="text-muted">[{e.type}]</span>{' '}
          {e.message ?? summarize(e)}
        </div>
      ))}
    </div>
  );
}

function summarize(e: JobEvent): string {
  const { type, message, ts, ...rest } = e;
  void type;
  void message;
  void ts;
  const keys = Object.keys(rest);
  if (keys.length === 0) return '';
  return keys.map((k) => `${k}=${JSON.stringify(rest[k])}`).join(' ');
}
