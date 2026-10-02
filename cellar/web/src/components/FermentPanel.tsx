import { useEffect, useMemo, useRef, useState } from 'react';
import { Pause, Play, RotateCcw } from 'lucide-react';
import {
  api,
  PHASES,
  type FermentRunOptions,
  type JobEvent,
  type Phase,
  type RunSummary,
  type StatusResponse,
} from '../api';
import {
  computeRunProgress,
  formatClock,
  formatDuration,
  hasRunStart,
  overallEta,
  overallFraction,
  phaseEta,
  type PhaseProgress,
  type PhaseState,
  type RunProgress,
} from '../lib/progress';
import { EventLog } from './EventLog';
import { FERMENT_HELP, Help } from './Help';
import { RunHistory, runLabel } from './RunHistory';
import { ProgressBar } from './ProgressBar';
import { StatusCounts } from './StatusCounts';

const nextPhase = (p: Phase): Phase | null => PHASES[PHASES.indexOf(p) + 1] ?? null;

/** The clock in epoch seconds, ticking every second while `active`. */
function useNow(active: boolean): number {
  const [now, setNow] = useState(() => Date.now() / 1000);
  useEffect(() => {
    if (!active) return;
    const tick = () => setNow(Date.now() / 1000);
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, [active]);
  return now;
}

function phaseDetail(p: PhaseProgress, now: number): string {
  if (!p.total) return 'waiting';
  const count = `${p.done} / ${p.total}`;
  switch (p.state) {
    case 'pending':
      return `${count} · ${p.inRun ? 'waiting' : 'after the pause'}`;
    case 'done':
      return `${count} · done`;
    case 'stopped':
      return `${count} · stopped`;
    case 'running': {
      const eta = phaseEta(p, now);
      const pct = Math.round((p.done / p.total) * 100);
      return `${count} (${pct}%)${eta !== null ? ` · ~${formatDuration(eta)} left` : ''}`;
    }
  }
}

function PhaseBars({ progress, now }: { progress: RunProgress; now: number }) {
  return (
    <>
      {PHASES.map((ph) => {
        const p = progress.phases[ph];
        const cur = p.state === 'running' ? p.current : null;
        return (
          <ProgressBar
            key={ph}
            label={ph}
            state={p.state}
            fraction={p.total ? p.done / p.total : 0}
            detail={phaseDetail(p, now)}
            sub={
              cur && (
                <>
                  Now: <span className="text-ink">{cur.name ?? `wine ${cur.index + 1}`}</span> ·{' '}
                  <span className="tabular-nums">{formatClock(now - cur.since)}</span>
                </>
              )
            }
          />
        );
      })}
    </>
  );
}

function OverallBar({ progress, now }: { progress: RunProgress; now: number }) {
  const states = PHASES.map((p) => progress.phases[p].state);
  const state: PhaseState = states.includes('running')
    ? 'running'
    : states.includes('stopped')
      ? 'stopped'
      : states.every((s) => s === 'done')
        ? 'done'
        : 'pending';
  const fraction = overallFraction(progress);
  const eta = overallEta(progress, now);
  return (
    <ProgressBar
      label="Overall progress"
      state={state}
      fraction={fraction}
      detail={`${Math.floor(fraction * 100)}%${eta !== null ? ` · ~${formatDuration(eta)} left` : ''}`}
    />
  );
}

/** The pause point of the current stream (if the last event is `paused`). */
function pausedFromEvents(events: JobEvent[]): { runId: string; after: Phase; next: Phase } | null {
  for (let i = events.length - 1; i >= 0; i--) {
    const e = events[i];
    if (e.type === 'paused' && typeof e.run_id === 'string' && typeof e.phase === 'string') {
      const after = e.phase as Phase;
      const next = (e.next_phase as Phase | undefined) ?? nextPhase(after);
      return next ? { runId: e.run_id, after, next } : null;
    }
    if (e.type === 'done' || e.type === 'error') return null;
  }
  return null;
}

export function FermentPanel({
  status,
  onRun,
  onStop,
  running,
  events,
  simple,
  onWinesChanged,
  onSettingsChanged,
  runs = [],
  activeRunId = null,
  onRunsChanged,
}: {
  status: StatusResponse | null;
  onRun: (opts: FermentRunOptions) => void;
  onStop: () => void;
  running: boolean;
  events: JobEvent[];
  simple?: boolean;
  onWinesChanged?: () => void;
  onSettingsChanged?: () => void;
  runs?: RunSummary[];
  activeRunId?: string | null;
  onRunsChanged?: () => void;
}) {
  const defaults = status?.defaults;
  const [force, setForce] = useState(false);
  const [limit, setLimit] = useState<number | ''>('');
  const [noProducerGate, setNoProducerGate] = useState(false);
  const [pauseBetweenPhases, setPauseBetweenPhases] = useState(() => {
    try {
      return localStorage.getItem('cellar:pausePhases') === '1';
    } catch {
      return false;
    }
  });

  // --- Model: a dropdown of what the running llama-server reports -------
  const serverModels = status?.llama.models;
  const defaultModel = defaults?.model;
  const modelOptions = useMemo(() => {
    const opts = [...(serverModels ?? [])];
    if (defaultModel && !opts.includes(defaultModel)) opts.push(defaultModel);
    return opts;
  }, [serverModels, defaultModel]);
  // '' means "whatever the server has loaded" (first reported model).
  const [modelChoice, setModelChoice] = useState('');
  const model = modelChoice || serverModels?.[0] || '';

  // --- Confidence threshold: persisted in settings.json ------------------
  const savedThreshold = status?.settings?.confidence_threshold;
  const [threshold, setThreshold] = useState<number | ''>('');
  const [thresholdSaved, setThresholdSaved] = useState<string | null>(null);
  const seededRef = useRef(false);
  useEffect(() => {
    if (!seededRef.current && savedThreshold != null) {
      seededRef.current = true;
      setThreshold(savedThreshold);
    }
  }, [savedThreshold]);
  const saveThreshold = async (v: number | '') => {
    if (v === '' || Number.isNaN(v)) return;
    const n = Math.max(0, Math.min(100, Math.round(Number(v))));
    setThreshold(n);
    if (n === savedThreshold) return;
    try {
      await api.patchSettings({ confidence_threshold: n });
      setThresholdSaved(`Saved ${n} to settings.json`);
      onSettingsChanged?.();
    } catch (e) {
      setThresholdSaved(e instanceof Error ? e.message : 'Failed to save threshold');
    }
  };

  const [rerunRunId, setRerunRunId] = useState('');
  const [rerunPhase, setRerunPhase] = useState<Phase>('search');

  const [resetting, setResetting] = useState(false);
  const [resetMsg, setResetMsg] = useState<string | null>(null);

  // The bars follow the live job's events. With no fermentation run in them
  // (after a reload once the job ended, or after an ingest job), they show
  // the last fermentation run, read back from its events.jsonl.
  const liveHasRun = useMemo(() => hasRunStart(events), [events]);
  const lastRunId =
    status?.jobs.find((j) => j.stage === 'ferment' && typeof j.run_id === 'string')?.run_id ??
    runs[0]?.run_id ??
    null;
  const [lastRun, setLastRun] = useState<{ runId: string; events: JobEvent[] } | null>(null);
  useEffect(() => {
    if (running || liveHasRun || !lastRunId || lastRun?.runId === lastRunId) return;
    let cancelled = false;
    api
      .getRunEvents(lastRunId, 100000)
      .then((r) => !cancelled && setLastRun({ runId: lastRunId, events: r.events }))
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, [running, liveHasRun, lastRunId, lastRun?.runId]);
  const progress = useMemo(
    () =>
      running || liveHasRun
        ? computeRunProgress(events, { live: running })
        : computeRunProgress(lastRun?.events ?? [], { live: false }),
    [running, liveHasRun, events, lastRun],
  );
  const now = useNow(PHASES.some((p) => progress.phases[p].state === 'running'));
  const runState = status?.fermentation.run_state ?? null;
  const byStatus = status?.fermentation.wines_json.by_status;

  // A paused run to continue: from the live stream first, else from the
  // server's persisted run state (survives a page reload).
  const paused = useMemo(() => {
    if (running) return null;
    const live = pausedFromEvents(events);
    if (live) return live;
    const f = status?.fermentation;
    if (f?.last_run_status === 'paused' && f.paused_after && f.last_run_id) {
      const next = nextPhase(f.paused_after);
      return next ? { runId: f.last_run_id, after: f.paused_after, next } : null;
    }
    return null;
  }, [running, events, status?.fermentation]);

  const togglePause = (v: boolean) => {
    setPauseBetweenPhases(v);
    try {
      localStorage.setItem('cellar:pausePhases', v ? '1' : '0');
    } catch {
      // ignore
    }
  };

  const run = () => {
    const opts: FermentRunOptions = {};
    if (force) opts.force = true;
    if (limit !== '') opts.limit = limit;
    if (threshold !== '') opts.confidence_threshold = threshold;
    if (model) opts.model = model;
    if (noProducerGate) opts.no_producer_gate = true;
    if (pauseBetweenPhases) opts.stop_after = 'search';
    onRun(opts);
  };

  const continueRun = () => {
    if (!paused) return;
    const opts: FermentRunOptions = { run_id: paused.runId, phase: paused.next };
    if (threshold !== '') opts.confidence_threshold = threshold;
    if (model) opts.model = model;
    if (noProducerGate) opts.no_producer_gate = true;
    if (pauseBetweenPhases && paused.next !== 'tag') opts.stop_after = paused.next;
    onRun(opts);
  };

  const rerun = () => {
    if (!rerunRunId) return;
    const opts: FermentRunOptions = { run_id: rerunRunId, phase: rerunPhase };
    if (threshold !== '') opts.confidence_threshold = threshold;
    if (model) opts.model = model;
    if (pauseBetweenPhases && rerunPhase !== 'tag') opts.stop_after = rerunPhase;
    onRun(opts);
  };

  const humanCount = byStatus?.human ?? 0;
  const resetHuman = async () => {
    if (!humanCount) return;
    if (!confirm(`Reset ${humanCount} human-edited wine(s) to pending so fermentation stops skipping them?`)) {
      return;
    }
    setResetting(true);
    setResetMsg(null);
    try {
      const { reset } = await api.resetHumanWines();
      setResetMsg(`Reset ${reset} wine(s) to pending.`);
      onWinesChanged?.();
    } catch (e) {
      setResetMsg(e instanceof Error ? e.message : 'Failed to reset human-edited wines');
    } finally {
      setResetting(false);
    }
  };

  const continueButton = paused && (
    <button
      type="button"
      onClick={continueRun}
      disabled={running}
      className="flex items-center gap-1.5 rounded-md bg-wine px-3 py-1.5 text-sm font-medium text-white hover:bg-wine-dark disabled:opacity-50"
      title={`Run ${paused.runId} is paused after ${paused.after}. Continue with the ${paused.next} phase over its logs.`}
    >
      <Play className="h-4 w-4" />
      Continue → {paused.next}
    </button>
  );

  const resetButton = (
    <button
      type="button"
      onClick={resetHuman}
      disabled={resetting || !humanCount}
      className="flex items-center gap-1.5 rounded-md border border-wine px-3 py-1.5 text-sm font-medium text-wine hover:bg-wine-light disabled:cursor-not-allowed disabled:opacity-50"
      title="Reset every human-edited wine to pending so the next fermentation run doesn't skip it"
    >
      <RotateCcw className="h-4 w-4" />
      {resetting ? 'Resetting…' : 'Reset human tags'}
    </button>
  );

  const pausedBanner = paused && (
    <div className="flex flex-wrap items-center gap-2 rounded-md border border-amber-300 bg-amber-50 px-3 py-2 text-sm text-amber-900">
      <Pause className="h-4 w-4" />
      <span>
        Run <span className="font-mono">{paused.runId}</span> is paused after the{' '}
        <span className="font-semibold">{paused.after}</span> phase. Inspect the results in Distribute,
        then continue with <span className="font-semibold">{paused.next}</span>.
      </span>
    </div>
  );

  if (simple) {
    return (
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-ink">Run pipeline</h2>
          <div className="flex gap-2">
            {continueButton}
            <button
              type="button"
              onClick={run}
              disabled={running}
              className="rounded-md bg-wine px-3 py-1.5 text-sm font-medium text-white hover:bg-wine-dark disabled:opacity-50"
            >
              {running ? 'Running…' : 'Run pipeline'}
            </button>
            {running && (
              <button
                type="button"
                onClick={onStop}
                className="rounded-md border border-wine px-3 py-1.5 text-sm font-medium text-wine hover:bg-wine-light"
              >
                Stop
              </button>
            )}
            {resetButton}
          </div>
        </div>
        {pausedBanner}
        <div className="space-y-2 rounded-md border border-parchment bg-white p-3">
          <OverallBar progress={progress} now={now} />
          <PhaseBars progress={progress} now={now} />
        </div>
        {byStatus && <StatusCounts byStatus={byStatus} />}
        {resetMsg && <div className="text-xs text-ink/70">{resetMsg}</div>}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-lg font-semibold text-ink">Ferment</h2>
        <div className="flex gap-2">
          {continueButton}
          <button
            type="button"
            onClick={run}
            disabled={running}
            className="rounded-md bg-wine px-3 py-1.5 text-sm font-medium text-white hover:bg-wine-dark disabled:opacity-50"
          >
            {running ? 'Running…' : paused ? 'Start new run' : 'Run fermentation'}
          </button>
          {running && (
            <button
              type="button"
              onClick={onStop}
              className="rounded-md border border-wine px-3 py-1.5 text-sm font-medium text-wine hover:bg-wine-light"
            >
              Stop
            </button>
          )}
          {resetButton}
        </div>
      </div>
      {pausedBanner}
      {resetMsg && <div className="text-xs text-ink/70">{resetMsg}</div>}
      {byStatus && <StatusCounts byStatus={byStatus} />}

      <div className="grid grid-cols-2 gap-3 rounded-md border border-parchment bg-white p-3 sm:grid-cols-3">
        <label className="flex items-center gap-1.5 text-sm">
          <input type="checkbox" checked={force} onChange={(e) => setForce(e.target.checked)} className="accent-wine" />
          Force fresh run
          <Help text={FERMENT_HELP.force} />
        </label>
        <label className="text-sm">
          <span className="mb-1 flex items-center gap-1 text-xs text-muted">
            Limit <Help text={FERMENT_HELP.limit} />
          </span>
          <input
            type="number"
            value={limit}
            onChange={(e) => setLimit(e.target.value === '' ? '' : Number(e.target.value))}
            className="w-full rounded-md border border-parchment px-2 py-1 text-sm focus:border-wine focus:outline-none"
          />
        </label>
        <label className="text-sm">
          <span className="mb-1 flex items-center gap-1 text-xs text-muted">
            Confidence threshold
            {savedThreshold != null && <span>(saved: {savedThreshold})</span>}
            <Help text={FERMENT_HELP.threshold} />
          </span>
          <input
            type="number"
            min={0}
            max={100}
            step={1}
            value={threshold}
            onChange={(e) => setThreshold(e.target.value === '' ? '' : Number(e.target.value))}
            onBlur={(e) => saveThreshold(e.target.value === '' ? '' : Number(e.target.value))}
            onKeyDown={(e) => {
              if (e.key === 'Enter') (e.target as HTMLInputElement).blur();
            }}
           
            className="w-full rounded-md border border-parchment px-2 py-1 text-sm focus:border-wine focus:outline-none"
          />
          {thresholdSaved && <span className="mt-0.5 block text-[11px] text-muted">{thresholdSaved}</span>}
        </label>
        <label className="text-sm sm:col-span-2">
          <span className="mb-1 flex items-center gap-1 text-xs text-muted">
            Model {status?.llama.ok ? '(loaded on llama-server)' : '(llama-server is down)'}
            <Help text={FERMENT_HELP.model} />
          </span>
          <select
            value={model}
            onChange={(e) => setModelChoice(e.target.value)}
            disabled={modelOptions.length === 0}
            className="w-full rounded-md border border-parchment bg-white px-2 py-1 text-sm focus:border-wine focus:outline-none disabled:opacity-60"
          >
            {modelOptions.length === 0 && <option value="">— start the model server —</option>}
            {modelOptions.map((m) => (
              <option key={m} value={m}>
                {m}
                {defaultModel === m && !(serverModels ?? []).includes(m) ? ' (default, not loaded)' : ''}
              </option>
            ))}
          </select>
        </label>
        <label className="flex items-center gap-1.5 text-sm">
          <input
            type="checkbox"
            checked={noProducerGate}
            onChange={(e) => setNoProducerGate(e.target.checked)}
            className="accent-wine"
          />
          Disable producer gate
          <Help text={FERMENT_HELP.producerGate} />
        </label>
        <label className="flex items-center gap-1.5 text-sm sm:col-span-3">
          <input
            type="checkbox"
            checked={pauseBetweenPhases}
            onChange={(e) => togglePause(e.target.checked)}
            className="accent-wine"
          />
          Pause after each phase
          <span className="text-xs text-muted">(search → pause → score → pause → tag)</span>
          <Help text={FERMENT_HELP.pause} />
        </label>
      </div>

      <div className="rounded-md border border-parchment bg-white p-3">
        <h3 className="mb-2 flex items-center gap-1 text-sm font-semibold text-ink">
          Re-run from phase <Help text={FERMENT_HELP.rerun} />
        </h3>
        <div className="flex flex-wrap items-center gap-2">
          <select
            value={rerunRunId}
            onChange={(e) => setRerunRunId(e.target.value)}
            className="rounded-md border border-parchment bg-white px-2 py-1 text-sm focus:border-wine focus:outline-none"
          >
            <option value="">Select run…</option>
            {runs.map((r) => (
              <option key={r.run_id} value={r.run_id}>
                {runLabel(r)}
              </option>
            ))}
          </select>
          <select
            value={rerunPhase}
            onChange={(e) => setRerunPhase(e.target.value as Phase)}
            className="rounded-md border border-parchment bg-white px-2 py-1 text-sm focus:border-wine focus:outline-none"
          >
            {PHASES.map((p) => (
              <option key={p} value={p}>
                {p}
              </option>
            ))}
          </select>
          <button
            type="button"
            onClick={rerun}
            disabled={running || !rerunRunId}
            className="rounded-md border border-wine px-3 py-1.5 text-sm font-medium text-wine hover:bg-wine-light disabled:opacity-50"
          >
            Re-run
          </button>
        </div>
        {runState && (
          <div className="mt-2 text-xs text-muted">
            Resume cursor: run {runState.run_id}, phase {runState.phase}, cursor {runState.cursor ?? 'n/a'}
          </div>
        )}
      </div>

      <div className="space-y-2 rounded-md border border-parchment bg-white p-3">
        <h3 className="text-sm font-semibold text-ink">Phase progress</h3>
        <PhaseBars progress={progress} now={now} />
      </div>

      <div>
        <h3 className="mb-2 text-sm font-semibold text-ink">Event log</h3>
        <EventLog events={events} />
      </div>

      <RunHistory runs={runs} activeRunId={activeRunId} onChanged={() => onRunsChanged?.()} />
    </div>
  );
}
