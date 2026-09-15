import { useEffect, useState } from 'react';
import { api, type IngestionRowsResponse, type StatusResponse } from '../api';

export function IngestPanel({
  status,
  onRun,
  running,
  simple,
}: {
  status: StatusResponse | null;
  onRun: () => void;
  running: boolean;
  simple?: boolean;
}) {
  const [rows, setRows] = useState<IngestionRowsResponse | null>(null);
  const [expanded, setExpanded] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (simple) return;
    api
      .getIngestionRows()
      .then(setRows)
      .catch((e) => setError(e instanceof Error ? e.message : 'Failed to load rows'));
  }, [simple, status?.ingestion.csv.mtime]);

  const csv = status?.ingestion.csv;
  const inputs = status?.ingestion.inputs ?? [];

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-lg font-semibold text-ink">Ingest</h2>
        <button
          type="button"
          onClick={onRun}
          disabled={running}
          className="rounded-md bg-wine px-3 py-1.5 text-sm font-medium text-white hover:bg-wine-dark disabled:opacity-50"
        >
          {running ? 'Running…' : 'Run ingestion'}
        </button>
      </div>

      {!simple && (
        <>
          <div className="rounded-md border border-parchment bg-white p-3">
            <h3 className="mb-2 text-sm font-semibold text-ink">Input files</h3>
            {inputs.length === 0 && <div className="text-sm text-muted">No input files found.</div>}
            <table className="w-full text-sm">
              <tbody>
                {inputs.map((f) => (
                  <tr key={f.name} className="border-b border-parchment/60 last:border-0">
                    <td className="py-1 pr-3 font-medium text-ink">{f.name}</td>
                    <td className="py-1 pr-3 text-muted">{f.exists ? 'present' : 'missing'}</td>
                    <td className="py-1 pr-3 text-muted">{f.mtime ?? '—'}</td>
                    <td className="py-1 text-muted">{f.size != null ? `${f.size} bytes` : '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="rounded-md border border-parchment bg-white p-3">
            <h3 className="mb-2 text-sm font-semibold text-ink">Combined CSV</h3>
            {csv?.exists ? (
              <div className="text-sm text-muted">
                {csv.path} — {csv.row_count} rows — updated {csv.mtime}
              </div>
            ) : (
              <div className="text-sm text-muted">Not generated yet.</div>
            )}
          </div>

          <div className="rounded-md border border-parchment bg-white p-3">
            <div className="mb-2 flex items-center justify-between">
              <h3 className="text-sm font-semibold text-ink">CSV preview</h3>
              {rows && (
                <button
                  type="button"
                  onClick={() => setExpanded((v) => !v)}
                  className="text-xs font-medium text-wine hover:underline"
                >
                  {expanded ? 'Fewer columns' : 'All columns'}
                </button>
              )}
            </div>
            {error && <div className="text-sm text-red-700">{error}</div>}
            {rows && (
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b border-parchment">
                      {(expanded ? rows.columns : rows.columns.slice(0, 10)).map((c) => (
                        <th key={c} className="whitespace-nowrap px-2 py-1 text-left font-semibold text-muted">
                          {c}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {rows.rows.slice(0, 10).map((r, i) => (
                      <tr key={i} className="border-b border-parchment/60 last:border-0">
                        {(expanded ? rows.columns : rows.columns.slice(0, 10)).map((c) => (
                          <td key={c} className="whitespace-nowrap px-2 py-1 text-ink">
                            {String(r[c] ?? '')}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
