import { useMemo, useState } from 'react';
import type { FermentRunOptions, JobEvent, StatusResponse } from '../api';
import { EventLog } from './EventLog';
import { ProgressBar } from './ProgressBar';

const PHASES = ['search', 'score', 'tag'] as const;
type Phase = (typeof PHASES)[number];

function computePhaseProgress(events: JobEvent[]): Record<Phase, { index: number; total: number; active: boolean }> {
  const result: Record<Phase, { index: number; total: number; active: boolean }> = {
    search: { index: 0, total: 0, active: false },
    score: { index: 0, total: 0, active: false },
    tag: { index: 0, total: 0, active: false },
  };
  for (const e of events) {
    const phase = e.phase as Phase | undefined;
    if (!phase || !(phase in result)) continue;
    if (e.type === 'phase_start') {
      result[phase].active = true;
      result[phase].total = Number(e.total ?? result[phase].total);
      result[phase].index = 0;
    } else if (e.type === 'progress') {
      result[phase].index = Number(e.index ?? result[phase].index);
      result[phase].total = Number(e.total ?? result[phase].total);
      result[phase].active = true;
    } else if (e.type === 'phase_end') {
      result[phase].active = false;
      if (result[phase].total) result[phase].index = result[phase].total;
    }
  }
  return result;
}

export function FermentPanel({
  status,
  onRun,
  onStop,
  running,
  events,
  simple,
}: {
  status: StatusResponse | null;
  onRun: (opts: FermentRunOptions) => void;
  onStop: () => void;
  running: boolean;
  events: JobEvent[];
  simple?: boolean;
}) {
  const defaults = status?.defaults;
  const [force, setForce] = useState(false);
  const [limit, setLimit] = useState<number | ''>('');
  const [confidenceThreshold, setConfidenceThreshold] = useState<number | ''>('');
  const [model, setModel] = useState('');
  const [noProducerGate, setNoProducerGate] = useState(false);

  const [rerunRunId, setRerunRunId] = useState('');
  const [rerunPhase, setRerunPhase] = useState<Phase>('search');

  const phaseProgress = useMemo(() => computePhaseProgress(events), [events]);
  const runState = status?.fermentation.run_state ?? null;
  const runs = status?.fermentation.runs ?? [];
  const byStatus = status?.fermentation.wines_json.by_status;

  const run = () => {
    const opts: FermentRunOptions = {};
    if (force) opts.force = true;
    if (limit !== '') opts.limit = limit;
    if (confidenceThreshold !== '') opts.confidence_threshold = confidenceThreshold;
    if (model) opts.model = model;
    if (noProducerGate) opts.no_producer_gate = true;
    onRun(opts);
  };

  const rerun = () => {
    if (!rerunRunId) return;
    onRun({ run_id: rerunRunId, phase: rerunPhase });
  };

  if (simple) {
    const totalIndex = PHASES.reduce((s, p) => s + phaseProgress[p].index, 0);
    const totalTotal = PHASES.reduce((s, p) => s + phaseProgress[p].total, 0);
    return (
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-ink">Run pipeline</h2>
          <div className="flex gap-2">
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
          </div>
        </div>
        <ProgressBar value={totalIndex} total={totalTotal || 1} label="Overall progress" />
        {byStatus && (
          <div className="flex flex-wrap gap-2 text-xs text-muted">
            <span>auto: {byStatus.auto}</span>
            <span>needs_review: {byStatus.needs_review}</span>
            <span>manual: {byStatus.manual}</span>
            <span>pending: {byStatus.pending}</span>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-lg font-semibold text-ink">Ferment</h2>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={run}
            disabled={running}
            className="rounded-md bg-wine px-3 py-1.5 text-sm font-medium text-white hover:bg-wine-dark disabled:opacity-50"
          >
            {running ? 'Running…' : 'Run fermentation'}
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
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 rounded-md border border-parchment bg-white p-3 sm:grid-cols-3">
        <label className="flex items-center gap-1.5 text-sm">
          <input type="checkbox" checked={force} onChange={(e) => setForce(e.target.checked)} className="accent-wine" />
          Force
        </label>
        <label className="text-sm">
          <span className="mb-1 block text-xs text-muted">Limit</span>
          <input
            type="number"
            value={limit}
            onChange={(e) => setLimit(e.target.value === '' ? '' : Number(e.target.value))}
            className="w-full rounded-md border border-parchment px-2 py-1 text-sm focus:border-wine focus:outline-none"
          />
        </label>
        <label className="text-sm">
          <span className="mb-1 block text-xs text-muted">
            Confidence threshold {defaults ? `(default ${defaults.confidence_threshold})` : ''}
          </span>
          <input
            type="number"
            step="0.01"
            value={confidenceThreshold}
            onChange={(e) => setConfidenceThreshold(e.target.value === '' ? '' : Number(e.target.value))}
            className="w-full rounded-md border border-parchment px-2 py-1 text-sm focus:border-wine focus:outline-none"
          />
        </label>
        <label className="text-sm sm:col-span-2">
          <span className="mb-1 block text-xs text-muted">Model {defaults ? `(default ${defaults.model})` : ''}</span>
          <input
            type="text"
            value={model}
            onChange={(e) => setModel(e.target.value)}
            className="w-full rounded-md border border-parchment px-2 py-1 text-sm focus:border-wine focus:outline-none"
          />
        </label>
        <label className="flex items-center gap-1.5 text-sm">
          <input
            type="checkbox"
            checked={noProducerGate}
            onChange={(e) => setNoProducerGate(e.target.checked)}
            className="accent-wine"
          />
          Disable producer gate
        </label>
      </div>

      <div className="rounded-md border border-parchment bg-white p-3">
        <h3 className="mb-2 text-sm font-semibold text-ink">Re-run from phase</h3>
        <div className="flex flex-wrap items-center gap-2">
          <select
            value={rerunRunId}
            onChange={(e) => setRerunRunId(e.target.value)}
            className="rounded-md border border-parchment px-2 py-1 text-sm focus:border-wine focus:outline-none"
          >
            <option value="">Select run…</option>
            {runs.map((r) => (
              <option key={r} value={r}>
                {r}
              </option>
            ))}
          </select>
          <select
            value={rerunPhase}
            onChange={(e) => setRerunPhase(e.target.value as Phase)}
            className="rounded-md border border-parchment px-2 py-1 text-sm focus:border-wine focus:outline-none"
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
        {PHASES.map((p) => (
          <ProgressBar
            key={p}
            value={phaseProgress[p].index}
            total={phaseProgress[p].total || 1}
            label={`${p}${phaseProgress[p].active ? ' (running)' : ''}`}
          />
        ))}
      </div>

      <div>
        <h3 className="mb-2 text-sm font-semibold text-ink">Event log</h3>
        <EventLog events={events} />
      </div>
    </div>
  );
}
