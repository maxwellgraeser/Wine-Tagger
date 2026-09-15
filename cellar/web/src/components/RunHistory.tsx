import { useState } from 'react';
import { Trash2 } from 'lucide-react';
import { api, PHASES, type RunSummary } from '../api';

export const RUN_STATUS_STYLES: Record<string, string> = {
  done: 'bg-green-100 text-green-800 border-green-300',
  running: 'bg-blue-100 text-blue-800 border-blue-300',
  paused: 'bg-amber-100 text-amber-800 border-amber-300',
  interrupted: 'bg-gray-100 text-gray-700 border-gray-300',
  failed: 'bg-red-100 text-red-800 border-red-300',
};

export function RunStatusBadge({ status }: { status: string | null | undefined }) {
  const s = status ?? 'unknown';
  return (
    <span className={`inline-flex rounded-full border px-2 py-0.5 text-xs font-medium ${RUN_STATUS_STYLES[s] ?? RUN_STATUS_STYLES.interrupted}`}>
      {s}
    </span>
  );
}

/** "20260915-164254" -> "2026-09-15 16:42:54" (run ids are local timestamps). */
export function formatRunId(id: string): string {
  const m = /^(\d{4})(\d{2})(\d{2})-(\d{2})(\d{2})(\d{2})$/.exec(id);
  return m ? `${m[1]}-${m[2]}-${m[3]} ${m[4]}:${m[5]}:${m[6]}` : id;
}

export function runLabel(r: RunSummary): string {
  const phase = r.status === 'done' ? 'done' : r.status === 'paused' ? `paused after ${r.paused_after}` : r.status;
  return `${formatRunId(r.run_id)} · ${r.product_count} wines · ${phase}`;
}

/**
 * Every fermentation run on disk (logs/<run_id>/) with per-run and bulk
 * delete. `activeRunId` is the run the current job writes to; the server
 * refuses to delete it and the UI hides the button.
 */
export function RunHistory({
  runs,
  activeRunId,
  onChanged,
}: {
  runs: RunSummary[];
  activeRunId: string | null;
  onChanged: () => void;
}) {
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  const report = (res: { deleted: string[]; skipped: string[] }) => {
    const parts = [`Deleted ${res.deleted.length} run${res.deleted.length === 1 ? '' : 's'}.`];
    if (res.skipped.length) parts.push(`Skipped ${res.skipped.join(', ')} (in use by the running job).`);
    setMsg(parts.join(' '));
    onChanged();
  };

  const run = async (fn: () => Promise<{ deleted: string[]; skipped: string[] }>) => {
    setBusy(true);
    setMsg(null);
    try {
      report(await fn());
    } catch (e) {
      setMsg(e instanceof Error ? e.message : 'Delete failed');
    } finally {
      setBusy(false);
    }
  };

  const deleteOne = (id: string) => {
    if (!confirm(`Delete run ${id} and all of its logs? This cannot be undone.`)) return;
    run(() => api.deleteRun(id));
  };
  const deleteAllButLatest = (n: number) => {
    const doomed = runs.slice(n);
    if (!doomed.length) return;
    if (!confirm(`Delete ${doomed.length} run(s) older than the latest ${n}? This cannot be undone.`)) return;
    run(() => api.deleteRuns({ keep_latest: n }));
  };
  const deleteAll = () => {
    if (!runs.length) return;
    if (!confirm(`Delete all ${runs.length} run(s) and their logs? This cannot be undone.`)) return;
    run(() => api.deleteRuns({ all: true }));
  };

  return (
    <div className="rounded-md border border-parchment bg-white p-3">
      <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
        <h3 className="text-sm font-semibold text-ink">
          Run history <span className="font-normal text-muted">({runs.length})</span>
        </h3>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => deleteAllButLatest(5)}
            disabled={busy || runs.length <= 5}
            className="rounded-md border border-parchment px-2.5 py-1 text-xs font-medium text-ink hover:bg-parchment/60 disabled:cursor-not-allowed disabled:opacity-50"
            title="Keep the 5 newest runs, delete the rest"
          >
            Delete all but latest 5
          </button>
          <button
            type="button"
            onClick={deleteAll}
            disabled={busy || runs.length === 0}
            className="rounded-md border border-red-300 px-2.5 py-1 text-xs font-medium text-red-700 hover:bg-red-50 disabled:cursor-not-allowed disabled:opacity-50"
            title="Delete every run folder under logs/"
          >
            Delete all
          </button>
        </div>
      </div>
      {msg && <div className="mb-2 text-xs text-ink/70">{msg}</div>}
      {runs.length === 0 ? (
        <div className="text-sm text-muted">No runs yet.</div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[640px] text-xs">
            <thead className="border-b border-parchment text-left text-muted">
              <tr>
                <th className="px-2 py-1 font-semibold">Run</th>
                <th className="px-2 py-1 font-semibold">Status</th>
                <th className="px-2 py-1 font-semibold">Wines</th>
                <th className="px-2 py-1 font-semibold">Tagged</th>
                <th className="px-2 py-1 font-semibold">Phases</th>
                <th className="px-2 py-1 font-semibold">Config</th>
                <th className="px-2 py-1" />
              </tr>
            </thead>
            <tbody>
              {runs.map((r) => {
                const cfg = (r.config ?? {}) as Record<string, unknown>;
                const isActive = r.run_id === activeRunId;
                return (
                  <tr key={r.run_id} className="border-b border-parchment/70 last:border-0">
                    <td className="px-2 py-1 font-mono text-ink" title={r.run_id}>
                      {formatRunId(r.run_id)}
                      {isActive && <span className="ml-1 text-blue-700">(running)</span>}
                    </td>
                    <td className="px-2 py-1">
                      <RunStatusBadge status={r.status} />
                    </td>
                    <td className="px-2 py-1 text-muted">{r.product_count}</td>
                    <td className="px-2 py-1 text-muted">{r.tagged_count}</td>
                    <td className="px-2 py-1 text-muted">
                      {PHASES.map((p) => `${p}: ${r.phases[p]?.status ?? '—'}`).join(' · ')}
                    </td>
                    <td className="px-2 py-1 text-muted">
                      {cfg.limit ? `limit ${cfg.limit} · ` : ''}
                      thr {String(cfg.confidence_threshold ?? '—')}
                      {cfg.producer_gate === false ? ' · gate off' : ''}
                    </td>
                    <td className="px-2 py-1 text-right">
                      {!isActive && (
                        <button
                          type="button"
                          onClick={() => deleteOne(r.run_id)}
                          disabled={busy}
                          className="rounded p-1 text-muted hover:bg-red-50 hover:text-red-700 disabled:opacity-50"
                          title={`Delete run ${r.run_id}`}
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </button>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
