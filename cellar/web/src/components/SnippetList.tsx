import type { ScoredSnippet, Snippet } from '../api';

export function SnippetList({ snippets }: { snippets: Snippet[] }) {
  if (!snippets || snippets.length === 0) {
    return <div className="text-sm text-muted">No snippets.</div>;
  }
  return (
    <div className="space-y-2">
      {snippets.map((s, i) => (
        <div key={i} className="rounded-md border border-parchment bg-white p-2 text-sm">
          <div className="flex items-center justify-between text-xs text-muted">
            <span className="font-medium text-ink">{s.domain ?? s.source ?? 'unknown source'}</span>
            {s.url && (
              <a href={s.url} target="_blank" rel="noreferrer" className="text-wine hover:underline">
                link
              </a>
            )}
          </div>
          <p className="mt-1 whitespace-pre-wrap text-ink">{s.body ?? ''}</p>
        </div>
      ))}
    </div>
  );
}

export function ScoredSnippetList({ snippets }: { snippets: ScoredSnippet[] }) {
  if (!snippets || snippets.length === 0) {
    return <div className="text-sm text-muted">No scored snippets.</div>;
  }
  return (
    <div className="space-y-2">
      {snippets.map((s, i) => (
        <div
          key={i}
          className={`rounded-md border p-2 text-sm ${
            s.dropped_reason ? 'border-red-200 bg-red-50' : 'border-parchment bg-white'
          }`}
        >
          <div className="flex flex-wrap items-center justify-between gap-1 text-xs text-muted">
            <span className="font-medium text-ink">{s.domain ?? s.source ?? 'unknown source'}</span>
            <div className="flex items-center gap-2">
              <span className="rounded-full bg-wine-light px-2 py-0.5 font-medium text-wine-dark">
                score {s.match_score ?? 'n/a'}
              </span>
              {s.dropped_reason && (
                <span className="rounded-full bg-red-100 px-2 py-0.5 font-medium text-red-700">
                  dropped: {s.dropped_reason}
                </span>
              )}
            </div>
          </div>
          <p className="mt-1 whitespace-pre-wrap text-ink">{s.body ?? ''}</p>
        </div>
      ))}
    </div>
  );
}
