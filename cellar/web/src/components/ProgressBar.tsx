import type { ReactNode } from 'react';
import type { PhaseState } from '../lib/progress';

const FILL: Record<PhaseState, string> = {
  pending: 'bg-wine/40',
  running: 'bg-wine',
  done: 'bg-wine',
  stopped: 'bg-amber-500',
};

/**
 * One bar: `fraction` (0–1) fills it, `detail` is the text on the right
 * ("5 / 24 (21%) · ~12 min left"), `sub` an optional line underneath (the
 * wine being worked on). A running bar shows a pulsing dot by its label.
 */
export function ProgressBar({
  fraction,
  label,
  detail,
  state = 'running',
  sub,
}: {
  fraction: number;
  label: string;
  detail: string;
  state?: PhaseState;
  sub?: ReactNode;
}) {
  const pct = Math.max(0, Math.min(100, fraction * 100));
  return (
    <div className="w-full">
      <div className="mb-1 flex items-center justify-between gap-2 text-xs text-muted">
        <span className="flex items-center gap-1.5">
          {label}
          {state === 'running' && (
            <span className="h-1.5 w-1.5 rounded-full bg-wine motion-safe:animate-pulse" aria-label="running" />
          )}
        </span>
        <span className="text-right tabular-nums">{detail}</span>
      </div>
      <div
        className="h-2.5 w-full overflow-hidden rounded-full bg-parchment"
        role="progressbar"
        aria-label={label}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={Math.round(pct)}
      >
        <div className={`h-full rounded-full ${FILL[state]} transition-all duration-300`} style={{ width: `${pct}%` }} />
      </div>
      {sub && <div className="mt-1 truncate text-xs text-muted">{sub}</div>}
    </div>
  );
}
