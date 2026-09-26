import { Wine as WineIcon, Play, Square } from 'lucide-react';
import type { LlamaStatus } from '../api';
import type { Stage } from '../api';
import { StageTabs } from './StageTabs';

export function TopBar({
  stage,
  onStageChange,
  llama,
  onStartLlama,
  onStopLlama,
  llamaBusy,
  view,
  onViewChange,
}: {
  stage: Stage;
  onStageChange: (s: Stage) => void;
  llama: LlamaStatus | null;
  onStartLlama: () => void;
  onStopLlama: () => void;
  llamaBusy: boolean;
  view: 'simple' | 'developer';
  onViewChange: (v: 'simple' | 'developer') => void;
}) {
  return (
    <header className="sticky top-0 z-20 border-b border-parchment bg-cream/95 backdrop-blur">
      <div className="mx-auto flex max-w-7xl flex-wrap items-center gap-3 px-4 py-3">
        <div className="flex items-center gap-2">
          <WineIcon className="h-6 w-6 text-wine" strokeWidth={2} />
          <span className="text-lg font-bold tracking-tight text-wine">Cellar</span>
        </div>

        <div className="flex-1 min-w-[220px]">
          <StageTabs stage={stage} onStageChange={onStageChange} />
        </div>

        <div className="flex items-center gap-2">
          <div
            className={`flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium ${
              llama?.ok
                ? 'border-green-300 bg-green-100 text-green-800'
                : llama?.running
                  ? 'border-amber-300 bg-amber-100 text-amber-800'
                  : 'border-red-300 bg-red-100 text-red-800'
            }`}
            title={llama?.base_url ?? ''}
          >
            <span
              className={`h-2 w-2 rounded-full ${
                llama?.ok ? 'bg-green-500' : llama?.running ? 'bg-amber-500' : 'bg-red-500'
              }`}
            />
            LLM {llama?.ok ? 'ok' : llama?.running ? 'loading' : 'down'}
          </div>
          {llama?.running ? (
            <button
              type="button"
              onClick={onStopLlama}
              disabled={llamaBusy}
              className="flex items-center gap-1 rounded-full border border-wine px-2.5 py-1 text-xs font-medium text-wine hover:bg-wine hover:text-white disabled:opacity-50"
            >
              <Square className="h-3 w-3" />
              {llamaBusy ? 'Stopping…' : 'Stop model server'}
            </button>
          ) : (
            <button
              type="button"
              onClick={onStartLlama}
              disabled={llamaBusy || !llama}
              className="flex items-center gap-1 rounded-full bg-wine px-2.5 py-1 text-xs font-medium text-white hover:bg-wine-dark disabled:opacity-50"
            >
              <Play className="h-3 w-3" />
              {llamaBusy ? 'Starting…' : 'Start model server'}
            </button>
          )}

          <div className="ml-2 flex rounded-full border border-parchment bg-white p-0.5 text-xs font-medium">
            <button
              type="button"
              onClick={() => onViewChange('simple')}
              className={`rounded-full px-2.5 py-1 ${
                view === 'simple' ? 'bg-wine text-white' : 'text-muted hover:text-ink'
              }`}
            >
              Simple
            </button>
            <button
              type="button"
              onClick={() => onViewChange('developer')}
              className={`rounded-full px-2.5 py-1 ${
                view === 'developer' ? 'bg-wine text-white' : 'text-muted hover:text-ink'
              }`}
            >
              Developer
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}
