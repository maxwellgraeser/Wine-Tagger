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

/**
 * Which snippets were pasted into web_context (and so seen by the tagger).
 * Newer scorer logs carry `in_context`; for older ones we recover it from
 * the `[source | match=N]` headers inside web_context.
 */
export function contextSources(webContext: string | null | undefined): Set<string> {
  const out = new Set<string>();
  if (!webContext) return out;
  for (const m of webContext.matchAll(/^\[(.+?) \| match=\d+\]$/gm)) out.add(m[1]);
  return out;
}

export function ScoredSnippetList({
  snippets,
  webContext,
}: {
  snippets: ScoredSnippet[];
  webContext?: string | null;
}) {
  if (!snippets || snippets.length === 0) {
    return <div className="text-sm text-muted">No scored snippets.</div>;
  }
  const fromContext = contextSources(webContext);
  const rows = snippets
    .map((s, i) => ({
      s,
      i,
      inContext: s.in_context ?? (s.source != null && fromContext.has(s.source)),
    }))
    // Highest score first; ties keep the original (search-plan) order.
    .sort((a, b) => (b.s.match_score ?? -1) - (a.s.match_score ?? -1) || a.i - b.i);
  return (
    <div className="space-y-2">
      {rows.map(({ s, i, inContext }) => (
        <div
          key={i}
          className={`rounded-md border p-2 text-sm ${
            s.dropped_reason
              ? 'border-red-200 bg-red-50'
              : inContext
                ? 'border-green-300 bg-green-50'
                : 'border-parchment bg-white'
          }`}
        >
          <div className="flex flex-wrap items-center justify-between gap-1 text-xs text-muted">
            <span className="font-medium text-ink">
              {s.source ?? s.domain ?? 'unknown source'}
              {s.domain && s.source && s.domain !== '*' && (
                <span className="ml-1 font-normal text-muted">({s.domain})</span>
              )}
            </span>
            <div className="flex items-center gap-2">
              <span className="rounded-full bg-wine-light px-2 py-0.5 font-medium text-wine-dark">
                score {s.match_score ?? 'n/a'}
              </span>
              {inContext && (
                <span
                  className="rounded-full bg-green-100 px-2 py-0.5 font-medium text-green-800"
                  title="This snippet was in web_context, the text the tagger LLM was given"
                >
                  sent to LLM
                </span>
              )}
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
