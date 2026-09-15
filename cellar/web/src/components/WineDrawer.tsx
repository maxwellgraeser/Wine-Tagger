import { useEffect, useState } from 'react';
import { X } from 'lucide-react';
import { api, type Wine, type WineDetailResponse } from '../api';
import { StatusBadge } from './Badge';
import { TagEditor } from './TagEditor';
import { SnippetList, ScoredSnippetList, contextSources } from './SnippetList';
import { TranscriptView } from './TranscriptView';
import { JsonView } from './JsonView';

type DevTab = 'snippets' | 'scores' | 'transcript' | 'final';

export function WineDrawer({
  wine,
  showDev,
  onClose,
  onWineUpdated,
}: {
  wine: Wine;
  showDev: boolean;
  onClose: () => void;
  onWineUpdated: (w: Wine) => void;
}) {
  const [detail, setDetail] = useState<WineDetailResponse | null>(null);
  const [selectedRun, setSelectedRun] = useState<string | undefined>(wine.run_id ?? undefined);
  const [devTab, setDevTab] = useState<DevTab>('snippets');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onClose]);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    api
      .getWine(wine.id, selectedRun)
      .then((d) => {
        if (!cancelled) {
          setDetail(d);
          if (!selectedRun && d.logs?.run_id) setSelectedRun(d.logs.run_id);
        }
      })
      .catch((e) => !cancelled && setError(e instanceof Error ? e.message : 'Failed to load'))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [wine.id, selectedRun]);

  const sales = wine.sales;

  return (
    <div className="fixed inset-0 z-30 flex justify-end bg-ink/30" onClick={onClose}>
      <div
        className="h-full w-full max-w-xl overflow-y-auto bg-cream shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="sticky top-0 z-10 flex items-center justify-between border-b border-parchment bg-cream px-4 py-3">
          <div>
            <h2 className="text-base font-semibold text-ink">{wine.name}</h2>
            <div className="mt-0.5 flex items-center gap-2 text-xs text-muted">
              <StatusBadge status={wine.tag_status} />
              <span>{wine.category ?? '—'}</span>
            </div>
          </div>
          <button type="button" onClick={onClose} className="rounded-full p-1 hover:bg-parchment">
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="space-y-6 p-4">
          <section>
            <h3 className="mb-2 text-sm font-semibold text-ink">Tags</h3>
            <TagEditor wine={wine} onSaved={onWineUpdated} />
          </section>

          <section>
            <h3 className="mb-2 text-sm font-semibold text-ink">Sales stats</h3>
            <div className="grid grid-cols-2 gap-2 text-sm sm:grid-cols-3">
              <Stat label="Items sold" value={sales?.items_sold} />
              <Stat label="Margin %" value={sales?.margin_pct} />
              <Stat label="Sale count" value={sales?.sale_count} />
              <Stat label="Customers" value={sales?.customer_count} />
              <Stat label="Avg sale value" value={sales?.avg_sale_value} />
            </div>
          </section>

          {showDev && (
            <section>
              <div className="mb-2 flex items-center justify-between">
                <h3 className="text-sm font-semibold text-ink">Developer detail</h3>
                {detail && detail.runs.length > 0 && (
                  <select
                    value={selectedRun ?? ''}
                    onChange={(e) => setSelectedRun(e.target.value || undefined)}
                    className="rounded-md border border-parchment bg-white px-2 py-1 text-xs"
                  >
                    {detail.runs.map((r) => (
                      <option key={r} value={r}>
                        {r}
                      </option>
                    ))}
                  </select>
                )}
              </div>

              {loading && <div className="text-sm text-muted">Loading…</div>}
              {error && <div className="rounded-md bg-red-100 px-2 py-1 text-xs text-red-800">{error}</div>}

              {detail && (
                <>
                  <div className="mb-3 flex gap-1 rounded-full border border-parchment bg-white p-0.5 text-xs font-medium">
                    {(['snippets', 'scores', 'transcript', 'final'] as DevTab[]).map((t) => (
                      <button
                        key={t}
                        type="button"
                        onClick={() => setDevTab(t)}
                        className={`flex-1 rounded-full px-2 py-1 capitalize ${
                          devTab === t ? 'bg-wine text-white' : 'text-muted hover:text-ink'
                        }`}
                      >
                        {t}
                      </button>
                    ))}
                  </div>

                  {devTab === 'snippets' && (
                    detail.logs.search ? (
                      <>
                        <div className="mb-2 text-xs text-muted">
                          raw_snippet_count: {detail.logs.search.raw_snippet_count}
                        </div>
                        {detail.logs.search.errors && detail.logs.search.errors.length > 0 && (
                          <div className="mb-2 rounded-md border border-amber-300 bg-amber-50 p-2 text-xs text-amber-900">
                            <div className="font-semibold">
                              {detail.logs.search.errors.length} search quer{detail.logs.search.errors.length === 1 ? 'y' : 'ies'} failed
                              (rate limit / timeout), so this wine may have fewer snippets than it should:
                            </div>
                            <ul className="mt-1 list-disc pl-4">
                              {detail.logs.search.errors.map((e, i) => (
                                <li key={i}>
                                  <span className="font-medium">{e.source}</span>: {e.error}
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                        <SnippetList snippets={detail.logs.search.snippets} />
                        <JsonView data={detail.logs.search} label="search log JSON" />
                      </>
                    ) : (
                      <NoLog phase="search" runId={detail.logs.run_id} />
                    )
                  )}

                  {devTab === 'scores' && (
                    detail.logs.scorer ? (
                      <>
                        <div className="mb-2 flex flex-wrap gap-3 text-xs text-muted">
                          <span>input_count: {detail.logs.scorer.input_count}</span>
                          <span>producer_gate_dropped: {detail.logs.scorer.producer_gate_dropped}</span>
                          <span>web_context_built: {String(detail.logs.scorer.web_context_built)}</span>
                          <span>
                            sent to LLM:{' '}
                            {detail.logs.scorer.context_count ??
                              contextSources(detail.logs.scorer.web_context).size}
                          </span>
                        </div>
                        {detail.logs.scorer.llm?.error && (
                          <div className="mb-2 rounded-md border border-red-300 bg-red-50 p-2 text-xs text-red-800">
                            Scoring LLM reply could not be used ({detail.logs.scorer.llm.error}, after{' '}
                            {detail.logs.scorer.llm.attempts} attempt
                            {detail.logs.scorer.llm.attempts === 1 ? '' : 's'}) — every snippet scored 0.
                          </div>
                        )}
                        <div className="mb-2 text-xs text-muted">
                          Sorted by score, highest first. Green rows were pasted into web_context and
                          are what the tagger LLM saw.
                        </div>
                        <ScoredSnippetList
                          snippets={detail.logs.scorer.scored_snippets}
                          webContext={detail.logs.scorer.web_context}
                        />
                        {detail.logs.scorer.web_context && (
                          <div className="mt-3">
                            <h4 className="mb-1 text-xs font-semibold text-muted">web_context</h4>
                            <pre className="max-h-56 overflow-auto rounded-md border border-parchment bg-white p-2 text-xs whitespace-pre-wrap">
                              {detail.logs.scorer.web_context}
                            </pre>
                          </div>
                        )}
                        <JsonView data={detail.logs.scorer} label="scorer log JSON" />
                      </>
                    ) : (
                      <NoLog phase="score" runId={detail.logs.run_id} />
                    )
                  )}

                  {devTab === 'transcript' && (
                    detail.logs.tagger ? (
                      <>
                        <div className="mb-2 flex flex-wrap gap-3 text-xs text-muted">
                          <span>had_web_context: {String(detail.logs.tagger.had_web_context)}</span>
                          <span>submit_attempts: {detail.logs.tagger.submit_attempts}</span>
                          <span>success: {String(detail.logs.tagger.success)}</span>
                        </div>
                        <TranscriptView transcript={detail.logs.tagger.transcript} />
                        <JsonView data={detail.logs.tagger} label="tagger log JSON" />
                      </>
                    ) : (
                      <NoLog phase="tag" runId={detail.logs.run_id} />
                    )
                  )}

                  {devTab === 'final' && (
                    detail.logs.final ? (
                      <>
                        <div className="space-y-1 text-sm">
                          <div>tag_status: <StatusBadge status={detail.logs.final.tag_status} /></div>
                          <div>organic: {String(detail.logs.final.organic)}</div>
                        </div>
                        {detail.logs.final.normalized && (
                          <JsonView data={detail.logs.final.normalized} label="normalized block" />
                        )}
                        <JsonView data={detail.logs.final} label="final log JSON" />
                      </>
                    ) : (
                      <NoLog phase="final" runId={detail.logs.run_id} />
                    )
                  )}
                </>
              )}
            </section>
          )}
        </div>
      </div>
    </div>
  );
}

function NoLog({ phase, runId }: { phase: string; runId: string }) {
  return (
    <div className="text-sm text-muted">
      No {phase} log for this phase in run {runId}.
    </div>
  );
}

function Stat({ label, value }: { label: string; value: number | null | undefined }) {
  return (
    <div className="rounded-md border border-parchment bg-white px-2 py-1.5">
      <div className="text-xs text-muted">{label}</div>
      <div className="font-medium text-ink">{value != null ? value : '—'}</div>
    </div>
  );
}
