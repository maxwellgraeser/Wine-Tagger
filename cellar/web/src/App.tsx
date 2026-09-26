import { useCallback, useEffect, useRef, useState } from 'react';
import { api, type FermentRunOptions, type RunSummary, type Stage, type StatusResponse, type Wine } from './api';
import { TopBar } from './components/TopBar';
import { IngestPanel } from './components/IngestPanel';
import { FermentPanel } from './components/FermentPanel';
import { DistributePanel, LIVE } from './components/DistributePanel';
import { WineDrawer } from './components/WineDrawer';
import { useJobStream } from './hooks/useJobStream';

type View = 'simple' | 'developer';

function loadView(): View {
  try {
    const v = localStorage.getItem('cellar:view');
    if (v === 'simple' || v === 'developer') return v;
  } catch {
    // ignore storage errors
  }
  return 'developer';
}

function saveView(v: View) {
  try {
    localStorage.setItem('cellar:view', v);
  } catch {
    // ignore storage errors
  }
}

export default function App() {
  const [stage, setStage] = useState<Stage>('fermentation');
  const [view, setView] = useState<View>(loadView);
  const [status, setStatus] = useState<StatusResponse | null>(null);
  const [wines, setWines] = useState<Wine[]>([]);
  const [selectedWine, setSelectedWine] = useState<Wine | null>(null);
  const [banner, setBanner] = useState<string | null>(null);
  const [llamaBusy, setLlamaBusy] = useState(false);
  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const [runs, setRuns] = useState<RunSummary[]>([]);
  // Which results Distribute shows: LIVE (wines.json) or a run id. Starts
  // unset so the first runs load can pick the latest run.
  const [resultsRun, setResultsRun] = useState<string | null>(null);
  // Bumped every time wines.json is re-read so a run view refetches too.
  const [winesVersion, setWinesVersion] = useState(0);

  const attachedRef = useRef(false);
  // Live table updates: fermentation checkpoints wines.json after every
  // wine, so on each progress event we re-read it — throttled so a fast
  // phase can't flood the API.
  const lastWineRefreshRef = useRef(0);

  const jobStream = useJobStream(
    useCallback(() => {
      refreshWines();
      refreshStatus();
      refreshRuns();
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []),
    useCallback((e) => {
      if (e.type !== 'progress' && e.type !== 'phase_end') return;
      const now = Date.now();
      if (e.type === 'progress' && now - lastWineRefreshRef.current < 2000) return;
      lastWineRefreshRef.current = now;
      refreshWines();
      if (e.type === 'phase_end') {
        refreshStatus();
        refreshRuns();
      }
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []),
  );

  const showError = (e: unknown, fallback: string) => {
    setBanner(e instanceof Error ? e.message : fallback);
  };

  const refreshStatus = useCallback(async () => {
    try {
      const s = await api.getStatus();
      setStatus(s);
      return s;
    } catch (e) {
      showError(e, 'Failed to load status');
      return null;
    }
  }, []);

  const refreshWines = useCallback(async () => {
    try {
      const w = await api.getWines();
      setWines(w.wines ?? []);
      setWinesVersion((v) => v + 1);
    } catch (e) {
      showError(e, 'Failed to load wines');
    }
  }, []);

  const refreshRuns = useCallback(async () => {
    try {
      setRuns(await api.getRuns());
    } catch (e) {
      showError(e, 'Failed to load runs');
    }
  }, []);

  useEffect(() => {
    refreshWines();
    refreshRuns();
  }, [refreshWines, refreshRuns]);

  // The run the current job writes to (from its first event carrying run_id,
  // or the server's summary after a reload).
  const streamRunId = jobStream.events.find((e) => typeof e.run_id === 'string')?.run_id as string | undefined;
  const activeRunId = jobStream.running ? (streamRunId ?? status?.active_job?.run_id ?? null) : null;

  // Distribute defaults to the latest run, follows a new run as soon as it
  // has an id, and falls back if the selected run was deleted.
  useEffect(() => {
    if (activeRunId && resultsRun !== activeRunId) {
      setResultsRun(activeRunId);
      return;
    }
    if (resultsRun === null) {
      if (runs.length) setResultsRun(runs[0].run_id);
      return;
    }
    if (resultsRun !== LIVE && runs.length && !runs.some((r) => r.run_id === resultsRun)) {
      setResultsRun(runs[0].run_id);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeRunId, runs]);

  // Initial status load + attach to an active job if one exists.
  useEffect(() => {
    refreshStatus().then((s) => {
      if (s?.active_job?.running && !attachedRef.current) {
        attachedRef.current = true;
        setActiveJobId(s.active_job.id);
        jobStream.connect(s.active_job.id);
      }
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Poll status: every 2s while the model server is loading, 5s while a job runs, else every 20s.
  const llamaLoading = !!status?.llama.running && !status.llama.ok;
  useEffect(() => {
    const interval = llamaLoading ? 2000 : jobStream.running ? 5000 : 20000;
    const id = setInterval(refreshStatus, interval);
    return () => clearInterval(id);
  }, [llamaLoading, jobStream.running, refreshStatus]);

  const handleViewChange = (v: View) => {
    setView(v);
    saveView(v);
  };

  const startJob = (jobPromise: Promise<{ id: string; [key: string]: unknown }>) => {
    jobPromise
      .then((job) => {
        setActiveJobId(job.id);
        jobStream.connect(job.id);
        setTimeout(refreshRuns, 1500);
      })
      .catch((e) => showError(e, 'Failed to start job'));
  };

  const runIngest = (input: string) => startJob(api.runIngest(input));
  const runFerment = (opts: FermentRunOptions) => startJob(api.runFerment(opts));
  const stopJob = () => {
    if (activeJobId) {
      api.stopJob(activeJobId).catch((e) => showError(e, 'Failed to stop job'));
    }
  };

  const toggleLlama = async (action: 'start' | 'stop') => {
    setLlamaBusy(true);
    try {
      await (action === 'start' ? api.startLlama() : api.stopLlama());
      await refreshStatus();
    } catch (e) {
      showError(e, `Failed to ${action} model server`);
    } finally {
      setLlamaBusy(false);
    }
  };

  const onWineUpdated = (w: Wine) => {
    setWines((prev) => prev.map((x) => (x.id === w.id ? w : x)));
    setSelectedWine(w);
  };

  const isSimple = view === 'simple';
  const stageIsRunning = jobStream.running;

  return (
    <div className="min-h-screen bg-cream">
      <TopBar
        stage={stage}
        onStageChange={setStage}
        llama={status?.llama ?? null}
        onStartLlama={() => toggleLlama('start')}
        onStopLlama={() => toggleLlama('stop')}
        llamaBusy={llamaBusy}
        view={view}
        onViewChange={handleViewChange}
      />

      {banner && (
        <div className="mx-auto mt-2 flex max-w-7xl items-center justify-between gap-2 rounded-md bg-red-100 px-4 py-2 text-sm text-red-800">
          <span>{banner}</span>
          <button type="button" onClick={() => setBanner(null)} className="font-medium hover:underline">
            Dismiss
          </button>
        </div>
      )}

      <main className="mx-auto max-w-7xl px-4 py-6">
        {stage === 'ingestion' && (
          <IngestPanel
            status={status}
            onRun={runIngest}
            running={stageIsRunning}
            events={jobStream.events}
            onChanged={refreshStatus}
            simple={isSimple}
          />
        )}

        {stage === 'fermentation' && (
          <FermentPanel
            status={status}
            onRun={runFerment}
            onStop={stopJob}
            running={stageIsRunning}
            events={jobStream.events}
            simple={isSimple}
            onWinesChanged={() => {
              refreshWines();
              refreshStatus();
            }}
            onSettingsChanged={refreshStatus}
            runs={runs}
            activeRunId={activeRunId}
            onRunsChanged={() => {
              refreshRuns();
              refreshStatus();
            }}
          />
        )}

        {stage === 'distribution' && (
          <DistributePanel
            status={status}
            liveWines={wines}
            runs={runs}
            resultsRun={resultsRun ?? LIVE}
            onResultsRunChange={setResultsRun}
            activeRunId={activeRunId}
            winesVersion={winesVersion}
            onSelect={setSelectedWine}
            showDevColumns={!isSimple}
            onWinesChanged={() => {
              refreshWines();
              refreshStatus();
            }}
            onRunsChanged={() => {
              refreshRuns();
              refreshStatus();
            }}
          />
        )}
      </main>

      {selectedWine && (
        <WineDrawer
          wine={selectedWine}
          showDev={!isSimple}
          onClose={() => setSelectedWine(null)}
          onWineUpdated={onWineUpdated}
        />
      )}
    </div>
  );
}
