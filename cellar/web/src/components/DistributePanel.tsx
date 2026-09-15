import { useEffect, useMemo, useState } from 'react';
import { Download, RotateCcw, Trash2 } from 'lucide-react';
import { api, TAG_STATUSES, type RunSummary, type StatusResponse, type TagStatus, type Wine } from '../api';
import { Help } from './Help';
import { RunStatusBadge, formatRunId, runLabel } from './RunHistory';
import { StatusCounts } from './StatusCounts';
import { WineTable } from './WineTable';

/** Sentinel for "show output/wines.json as it is now" instead of one run's output. */
export const LIVE = 'live';

const SELECTOR_HELP =
  'Which results the table shows. A run shows exactly what that fermentation run produced ' +
  '(its wine set, its tags, its phase logs); wines it never reached are Pending. ' +
  "'Live table' is output/wines.json: the merged result of every run plus your hand edits, and what the export uses. " +
  'A new run switches this to itself automatically.';

export function DistributePanel({
  status,
  liveWines,
  runs,
  resultsRun,
  onResultsRunChange,
  activeRunId,
  winesVersion,
  onSelect,
  showDevColumns,
  onWinesChanged,
  onRunsChanged,
}: {
  status: StatusResponse | null;
  liveWines: Wine[];
  runs: RunSummary[];
  resultsRun: string;
  onResultsRunChange: (r: string) => void;
  activeRunId: string | null;
  /** Bumped whenever the store changes on disk; triggers a run-results refetch. */
  winesVersion: number;
  onSelect: (w: Wine) => void;
  showDevColumns: boolean;
  onWinesChanged: () => void;
  onRunsChanged: () => void;
}) {
  const [runWines, setRunWines] = useState<Wine[]>([]);
  const [runInfo, setRunInfo] = useState<RunSummary | null>(null);
  const [runError, setRunError] = useState<string | null>(null);
  const [resetting, setResetting] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  const isLive = resultsRun === LIVE;

  useEffect(() => {
    if (isLive) return;
    let cancelled = false;
    api
      .getRunResults(resultsRun)
      .then((r) => {
        if (cancelled) return;
        setRunWines(r.wines);
        setRunInfo(r.run);
        setRunError(null);
      })
      .catch((e) => {
        if (cancelled) return;
        setRunError(e instanceof Error ? e.message : 'Failed to load run results');
      });
    return () => {
      cancelled = true;
    };
  }, [resultsRun, isLive, winesVersion]);

  const wines = isLive ? liveWines : runWines;
  const byStatus = useMemo(() => {
    const out: Partial<Record<TagStatus, number>> = {};
    for (const s of TAG_STATUSES) out[s] = 0;
    for (const w of wines) out[w.tag_status] = (out[w.tag_status] ?? 0) + 1;
    return out;
  }, [wines]);

  const humanCount = status?.fermentation.wines_json.by_status?.human ?? 0;
  const resetHuman = async () => {
    if (!humanCount) return;
    if (!confirm(`Reset ${humanCount} human-edited wine(s) to pending so fermentation stops skipping them?`)) {
      return;
    }
    setResetting(true);
    setMsg(null);
    try {
      const { reset } = await api.resetHumanWines();
      setMsg(`Reset ${reset} wine(s) to pending.`);
      onWinesChanged();
    } catch (e) {
      setMsg(e instanceof Error ? e.message : 'Failed to reset human-edited wines');
    } finally {
      setResetting(false);
    }
  };

  const deleteSelectedRun = async () => {
    if (isLive) return;
    if (!confirm(`Delete run ${resultsRun} and all of its logs? This cannot be undone.`)) return;
    setDeleting(true);
    setMsg(null);
    try {
      await api.deleteRun(resultsRun);
      setMsg(`Deleted run ${resultsRun}.`);
      onRunsChanged();
    } catch (e) {
      setMsg(e instanceof Error ? e.message : 'Failed to delete run');
    } finally {
      setDeleting(false);
    }
  };

  const cfg = (runInfo?.config ?? {}) as Record<string, unknown>;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-lg font-semibold text-ink">Distribute</h2>
        <div className="flex items-center gap-2">
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
          <a
            href={api.exportUrl()}
            className="flex items-center gap-1.5 rounded-md bg-wine px-3 py-1.5 text-sm font-medium text-white hover:bg-wine-dark"
            title="Exports the live table (output/wines.json), whichever run is selected above"
          >
            <Download className="h-4 w-4" />
            Export Lightspeed .xlsx
          </a>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-2 rounded-md border border-parchment bg-white px-3 py-2 text-sm">
        <label className="flex items-center gap-1.5">
          <span className="text-xs text-muted">Results from</span>
          <Help text={SELECTOR_HELP} />
        </label>
        <select
          value={resultsRun}
          onChange={(e) => onResultsRunChange(e.target.value)}
          className="rounded-md border border-parchment bg-white px-2 py-1 text-sm focus:border-wine focus:outline-none"
        >
          <option value={LIVE}>Live table (wines.json, {liveWines.length} wines)</option>
          {runs.map((r, i) => (
            <option key={r.run_id} value={r.run_id}>
              {i === 0 ? 'Latest run · ' : ''}
              {runLabel(r)}
              {r.run_id === activeRunId ? ' (running)' : ''}
            </option>
          ))}
        </select>
        {!isLive && runInfo && (
          <>
            <RunStatusBadge status={runInfo.run_id === activeRunId ? 'running' : runInfo.status} />
            <span className="text-xs text-muted">
              {runInfo.tagged_count}/{runInfo.product_count} tagged
              {' · '}started {runInfo.started_at ? new Date(runInfo.started_at).toLocaleString() : formatRunId(runInfo.run_id)}
              {cfg.limit ? ` · limit ${cfg.limit}` : ''}
              {cfg.confidence_threshold != null ? ` · threshold ${cfg.confidence_threshold}` : ''}
              {cfg.producer_gate === false ? ' · producer gate off' : ''}
              {typeof cfg.model === 'string' ? ` · ${cfg.model}` : ''}
            </span>
            {runInfo.run_id !== activeRunId && (
              <button
                type="button"
                onClick={deleteSelectedRun}
                disabled={deleting}
                className="ml-auto flex items-center gap-1 rounded-md border border-red-300 px-2 py-1 text-xs font-medium text-red-700 hover:bg-red-50 disabled:opacity-50"
                title={`Delete run ${runInfo.run_id} and its logs`}
              >
                <Trash2 className="h-3.5 w-3.5" />
                {deleting ? 'Deleting…' : 'Delete this run'}
              </button>
            )}
          </>
        )}
        {!isLive && runError && <span className="text-xs text-red-700">{runError}</span>}
      </div>

      {!isLive && runInfo?.error && (
        <div className="rounded-md border border-red-300 bg-red-50 px-3 py-2 text-xs text-red-800">
          Run failed: {runInfo.error}
        </div>
      )}

      {msg && <div className="text-xs text-ink/70">{msg}</div>}

      <StatusCounts byStatus={byStatus} />

      <WineTable wines={wines} onSelect={onSelect} showDevColumns={showDevColumns} />
    </div>
  );
}
