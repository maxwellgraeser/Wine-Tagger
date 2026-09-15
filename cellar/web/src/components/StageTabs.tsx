import type { Stage } from '../api';

const STAGES: { key: Stage; label: string }[] = [
  { key: 'ingestion', label: 'Ingest' },
  { key: 'fermentation', label: 'Ferment' },
  { key: 'distribution', label: 'Distribute' },
];

export function StageTabs({
  stage,
  onStageChange,
}: {
  stage: Stage;
  onStageChange: (s: Stage) => void;
}) {
  return (
    <nav className="flex items-center justify-center gap-1 text-sm font-medium">
      {STAGES.map((s, i) => (
        <div key={s.key} className="flex items-center gap-1">
          <button
            type="button"
            onClick={() => onStageChange(s.key)}
            className={`rounded-full px-3 py-1.5 transition-colors ${
              stage === s.key
                ? 'bg-wine text-white shadow-sm'
                : 'text-muted hover:bg-parchment hover:text-ink'
            }`}
          >
            {s.label}
          </button>
          {i < STAGES.length - 1 && <span className="text-parchment">&rarr;</span>}
        </div>
      ))}
    </nav>
  );
}
