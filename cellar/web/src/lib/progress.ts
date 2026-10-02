// The Ferment progress bars as a pure function of a run's event stream.
//
// One fermentation invocation emits, in order:
//   info (run start) · run_plan · per phase: phase_start, then per wine
//   wine_start + progress (a human-edited wine: progress with skipped=true
//   only) · phase_end · then paused | done, or error on Stop / failure.
// The cellar server adds `exit` when the process ends. Logs written before
// run_plan existed are read from the opening info event instead.
import { PHASES, type JobEvent, type Phase } from '../api';

/**
 * Typical seconds per wine on this machine (journal/2026-10-01-BUG-FIXES.md
 * §1.4: means over the Sep 15 – Oct 1 runs). They weight the overall bar by
 * time rather than equal thirds, and stand in for a phase's rate until it has
 * timed a few wines itself.
 */
export const TYPICAL_SECONDS_PER_WINE: Record<Phase, number> = { search: 17, score: 60, tag: 30 };

/** A phase's own rate (and so its ETA) is shown only once it has timed this many wines. */
export const MIN_WINES_FOR_ETA = 3;

export type PhaseState = 'pending' | 'running' | 'done' | 'stopped';

export interface PhaseProgress {
  state: PhaseState;
  /** Wines finished, counting from 1 (a resumed phase starts at its cursor). */
  done: number;
  total: number;
  /** The wine being worked on: its name once `wine_start` names it, and when it started (epoch s). */
  current: { index: number; name: string | null; since: number } | null;
  /** Mean seconds per wine this run, once MIN_WINES_FOR_ETA wines were timed (skips excluded). */
  secPerWine: number | null;
  /** False for a phase after the pause point: this invocation will not reach it. */
  inRun: boolean;
}

export interface RunProgress {
  phases: Record<Phase, PhaseProgress>;
  /** True once the stream holds a fermentation run start (run_plan or its opening info). */
  started: boolean;
}

interface Acc extends PhaseProgress {
  timedSecs: number;
  timedWines: number;
}

const isPhase = (v: unknown): v is Phase => typeof v === 'string' && (PHASES as string[]).includes(v);
const num = (v: unknown): number | null => (typeof v === 'number' && Number.isFinite(v) ? v : null);

function fresh(): Record<Phase, Acc> {
  const make = (): Acc => ({
    state: 'pending', done: 0, total: 0, current: null, secPerWine: null, inRun: true,
    timedSecs: 0, timedWines: 0,
  });
  return { search: make(), score: make(), tag: make() };
}

/** Baseline for a new invocation: earlier phases done, the resume phase at its cursor. */
function plan(total: number, resume: Phase, cursor: number, stopAfter: Phase | null): Record<Phase, Acc> {
  const out = fresh();
  const start = PHASES.indexOf(resume);
  const stop = stopAfter && PHASES.indexOf(stopAfter) >= start ? PHASES.indexOf(stopAfter) : PHASES.length - 1;
  PHASES.forEach((p, i) => {
    out[p].total = total;
    if (i < start) {
      out[p].state = 'done';
      out[p].done = total;
    } else if (i === start) {
      out[p].done = Math.min(cursor, total);
    }
    out[p].inRun = i <= stop;
  });
  return out;
}

/**
 * Fold a job's events into the three bars. `live` is false when the stream is
 * over (a finished job, or a run's log read back after a reload): a phase
 * still "running" then has no process behind it and is shown as stopped.
 */
export function computeRunProgress(events: JobEvent[], { live = true }: { live?: boolean } = {}): RunProgress {
  let acc = fresh();
  let started = false;
  // An event replayed by a reconnecting stream is the same object again, with
  // the same timestamp; folding it twice could restart the run part-way.
  const seen = new Set<string>();

  for (const e of events) {
    const ts = num(e.ts);
    const phase = isPhase(e.phase) ? e.phase : null;
    if (ts !== null) {
      const key = `${e.type}|${ts}|${String(e.phase)}|${String(e.index)}`;
      if (seen.has(key)) continue;
      seen.add(key);
    }

    if (e.type === 'run_plan') {
      const total = num(e.total) ?? 0;
      const resume = isPhase(e.resume_phase) ? e.resume_phase : 'search';
      acc = plan(total, resume, num(e.cursor) ?? 0, isPhase(e.stop_after) ? e.stop_after : null);
      started = true;
      continue;
    }
    // The opening info of a run (`Run <id>: N wines, starting at phase P`).
    // It comes right before run_plan in new logs and is all that older logs have.
    if (e.type === 'info' && phase && num(e.total) !== null && typeof e.run_id === 'string') {
      acc = plan(num(e.total)!, phase, num(e.cursor) ?? 0, null);
      started = true;
      continue;
    }

    if (e.type === 'error' || e.type === 'exit') {
      for (const p of PHASES) {
        if (acc[p].state === 'running') {
          acc[p].state = 'stopped';
          acc[p].current = null;
        }
      }
      continue;
    }

    if (!phase) continue;
    const p = acc[phase];
    // A finished phase never reopens within one invocation, so a replayed
    // event for it cannot pull the bar back.
    if (p.state === 'done') continue;

    if (e.type === 'phase_start') {
      p.state = 'running';
      p.total = num(e.total) ?? p.total;
      if (ts !== null) p.current = { index: p.done, name: null, since: ts };
    } else if (e.type === 'wine_start') {
      p.state = 'running';
      p.total = num(e.total) ?? p.total;
      const index = num(e.index) ?? p.done;
      if (ts !== null) p.current = { index, name: typeof e.name === 'string' ? e.name : null, since: ts };
    } else if (e.type === 'progress') {
      const index = num(e.index);
      if (index === null) continue;
      p.state = 'running';
      p.total = num(e.total) ?? p.total;
      // `index` is 0-based and sent after the wine finished.
      if (index + 1 > p.done) {
        if (!e.skipped && ts !== null && p.current && p.current.index <= index) {
          p.timedSecs += Math.max(0, ts - p.current.since);
          p.timedWines += 1;
        }
        p.done = index + 1;
      }
      p.current = p.done < p.total && ts !== null ? { index: p.done, name: null, since: ts } : null;
    } else if (e.type === 'phase_end') {
      p.state = 'done';
      p.done = Math.max(p.done, p.total);
      p.current = null;
    }
  }

  const phases = {} as Record<Phase, PhaseProgress>;
  for (const p of PHASES) {
    const { timedSecs, timedWines, ...rest } = acc[p];
    const stale = !live && rest.state === 'running';
    phases[p] = {
      ...rest,
      state: stale ? 'stopped' : rest.state,
      current: stale ? null : rest.current,
      secPerWine: timedWines >= MIN_WINES_FOR_ETA ? timedSecs / timedWines : null,
    };
  }
  return { phases, started };
}

/** True when the events hold a fermentation run (not, say, an ingest job). */
export const hasRunStart = (events: JobEvent[]): boolean => computeRunProgress(events).started;

/** Seconds left in a running phase at `now` (epoch s), from its own rate; null until it has one. */
export function phaseEta(p: PhaseProgress, now: number): number | null {
  if (p.state !== 'running' || p.secPerWine === null) return null;
  const elapsed = p.current ? Math.max(0, now - p.current.since) : 0;
  return Math.max(0, (p.total - p.done) * p.secPerWine - elapsed);
}

/** The run's overall completion, 0–1, each phase weighted by its typical time. Never falls as phases start. */
export function overallFraction(r: RunProgress): number {
  let weight = 0;
  let done = 0;
  for (const p of PHASES) {
    const w = TYPICAL_SECONDS_PER_WINE[p];
    weight += w;
    const ph = r.phases[p];
    if (ph.total > 0) done += w * Math.min(1, ph.done / ph.total);
  }
  return weight ? done / weight : 0;
}

/**
 * Seconds until this invocation ends (or pauses): the running phase's own ETA,
 * plus typical times for the phases still to come. Null when nothing runs.
 */
export function overallEta(r: RunProgress, now: number): number | null {
  if (!PHASES.some((p) => r.phases[p].state === 'running')) return null;
  let secs = 0;
  for (const p of PHASES) {
    const ph = r.phases[p];
    if (!ph.inRun || ph.state === 'done' || ph.state === 'stopped') continue;
    const eta = ph.state === 'running' ? phaseEta(ph, now) : null;
    secs += eta ?? Math.max(0, ph.total - ph.done) * TYPICAL_SECONDS_PER_WINE[p];
  }
  return secs;
}

/** "45 s", "12 min", "1 h 05 min". */
export function formatDuration(secs: number): string {
  const s = Math.max(0, Math.round(secs));
  if (s < 60) return `${s} s`;
  const m = Math.round(s / 60);
  if (m < 60) return `${m} min`;
  return `${Math.floor(m / 60)} h ${String(m % 60).padStart(2, '0')} min`;
}

/** A running clock: "0:42", "12:05". */
export function formatClock(secs: number): string {
  const s = Math.max(0, Math.floor(secs));
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`;
}
