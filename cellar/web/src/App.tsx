import { useCallback, useEffect, useRef, useState } from 'react';
import { api, type FermentRunOptions, type Stage, type StatusResponse, type Wine } from './api';
import { TopBar } from './components/TopBar';
import { IngestPanel } from './components/IngestPanel';
import { FermentPanel } from './components/FermentPanel';
import { DistributePanel } from './components/DistributePanel';
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
  const [startingLlama, setStartingLlama] = useState(false);
  const [activeJobId, setActiveJobId] = useState<string | null>(null);

  const attachedRef = useRef(false);

  const jobStream = useJobStream(
    useCallback(() => {
      refreshWines();
      refreshStatus();
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
    } catch (e) {
      showError(e, 'Failed to load wines');
    }
  }, []);

  useEffect(() => {
    refreshWines();
  }, [refreshWines]);

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

  // Poll status: every 5s while a job runs, else every 20s.
  useEffect(() => {
    const interval = jobStream.running ? 5000 : 20000;
    const id = setInterval(refreshStatus, interval);
    return () => clearInterval(id);
  }, [jobStream.running, refreshStatus]);

  const handleViewChange = (v: View) => {
    setView(v);
    saveView(v);
  };

  const startJob = (jobPromise: Promise<{ id: string; [key: string]: unknown }>) => {
    jobPromise
      .then((job) => {
        setActiveJobId(job.id);
        jobStream.connect(job.id);
      })
      .catch((e) => showError(e, 'Failed to start job'));
  };

  const runIngest = () => startJob(api.runIngest());
  const runFerment = (opts: FermentRunOptions) => startJob(api.runFerment(opts));
  const stopJob = () => {
    if (activeJobId) {
      api.stopJob(activeJobId).catch((e) => showError(e, 'Failed to stop job'));
    }
  };

  const startLlama = async () => {
    setStartingLlama(true);
    try {
      await api.startLlama();
      await refreshStatus();
    } catch (e) {
      showError(e, 'Failed to start model server');
    } finally {
      setStartingLlama(false);
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
        onStartLlama={startLlama}
        startingLlama={startingLlama}
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
          <IngestPanel status={status} onRun={runIngest} running={stageIsRunning} simple={isSimple} />
        )}

        {stage === 'fermentation' && (
          <FermentPanel
            status={status}
            onRun={runFerment}
            onStop={stopJob}
            running={stageIsRunning}
            events={jobStream.events}
            simple={isSimple}
          />
        )}

        {stage === 'distribution' && (
          <DistributePanel
            status={status}
            wines={wines}
            onSelect={setSelectedWine}
            showDevColumns={!isSimple}
            onWinesChanged={() => {
              refreshWines();
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
