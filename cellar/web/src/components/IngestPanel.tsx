import { useCallback, useEffect, useMemo, useRef, useState, type DragEvent } from 'react';
import { CheckCircle2, ChevronDown, ChevronRight, FileSpreadsheet, FlaskConical, Trash2, UploadCloud } from 'lucide-react';
import {
  api,
  EXCLUDED_BY,
  EXCLUDED_BY_LABEL,
  type ExcludedBy,
  type IngestFilters,
  type IngestInput,
  type IngestSummary,
  type IngestionRowsResponse,
  type JobEvent,
  type StatusResponse,
} from '../api';
import { EventLog } from './EventLog';
import { Help } from './Help';

function fmtBytes(n: number | null | undefined): string {
  if (n == null) return '—';
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(0)} KB`;
  return `${(n / (1024 * 1024)).toFixed(1)} MB`;
}

function fmtDate(iso: string | null | undefined): string {
  if (!iso) return '—';
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? iso : d.toLocaleString();
}

function fmtNum(n: number | null | undefined): string {
  return n == null ? '—' : n.toLocaleString();
}

const HELP = {
  upload:
    'Export Products from Lightspeed as a CSV and drop it here. The header row is checked on upload, so the ' +
    'wrong file (an inventory report, an .xlsx) is rejected with a reason. Uploads are kept in ingestion/uploads/ ' +
    'until you delete them.',
  test:
    'The 24 wines used to develop the pipeline (with sales stats). Handy for a quick fermentation test run; ' +
    'they always pass the filters.',
  filters:
    'Filter 1 keeps rows whose category is whitelisted (Red, White, Rose, Sparkling, Orange/Amber) and excludes any ' +
    'other category (Beer, Accessories, Dessert…). Uncategorized rows — the wines added since the POS switch — then ' +
    'pass through filter 2 (vendor blacklist) and filter 3 (name / keyword exclusions). Rules live in ' +
    'ingestion/filters.toml.',
  uncategorized:
    'Wines with no Lightspeed category that passed every filter. Fermentation infers a category for these ' +
    '(Red / White / Rose / Sparkling) alongside the other tags.',
  excluded: 'Every excluded row is written to ingestion/output/excluded.csv with the filter and the reason.',
};

// ---------------------------------------------------------------------------

export function IngestPanel({
  status,
  onRun,
  running,
  events,
  onChanged,
  simple,
}: {
  status: StatusResponse | null;
  onRun: (input: string) => void;
  running: boolean;
  events: JobEvent[];
  onChanged: () => void;
  simple?: boolean;
}) {
  const uploads = useMemo(() => status?.ingestion.uploads ?? [], [status?.ingestion.uploads]);
  const summary = status?.ingestion.summary ?? null;
  const csv = status?.ingestion.csv;

  const [chosen, setSelected] = useState<string | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploading, setUploading] = useState<string | null>(null);
  const [justUploaded, setJustUploaded] = useState<string | null>(null);
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  // The chosen input if it still exists, else the newest upload, else the test set.
  const selected =
    chosen && uploads.some((u) => u.name === chosen)
      ? chosen
      : (uploads.find((u) => u.kind === 'upload') ?? uploads[0])?.name ?? null;

  // Only the ingest job's events belong here (the stream is shared with Ferment).
  const ingestEvents = useMemo(() => (events[0]?.stage === 'ingest' ? events : []), [events]);
  const ingestRunning = running && ingestEvents.length > 0;

  const upload = useCallback(
    async (file: File) => {
      setUploadError(null);
      setJustUploaded(null);
      if (!file.name.toLowerCase().endsWith('.csv')) {
        setUploadError(`${file.name}: only .csv product exports are accepted (export Products from Lightspeed as CSV).`);
        return;
      }
      setUploading(file.name);
      try {
        const stored = await api.uploadIngestFile(file);
        setSelected(stored.name);
        setJustUploaded(stored.name);
        onChanged();
      } catch (e) {
        setUploadError(e instanceof Error ? e.message : 'Upload failed');
      } finally {
        setUploading(null);
      }
    },
    [onChanged],
  );

  const onDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file) void upload(file);
  };

  const remove = async (name: string) => {
    try {
      await api.deleteIngestUpload(name);
      if (selected === name) setSelected(null);
      onChanged();
    } catch (e) {
      setUploadError(e instanceof Error ? e.message : 'Delete failed');
    }
  };

  const selectedInput = uploads.find((u) => u.name === selected) ?? null;
  const runLabel = selectedInput
    ? `Run ingestion on ${selectedInput.kind === 'test' ? 'the test set' : selectedInput.name}`
    : 'Run ingestion';

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <h2 className="text-lg font-semibold text-ink">Ingest</h2>
          <p className="text-sm text-muted">
            Upload the Lightspeed product export, run the filters, and hand the wines to Ferment.
          </p>
        </div>
      </div>

      {/* --- Step 1: upload ------------------------------------------------ */}
      <section className="rounded-md border border-parchment bg-white p-4">
        <h3 className="mb-3 flex items-center gap-1.5 text-sm font-semibold text-ink">
          <span className="flex h-5 w-5 items-center justify-center rounded-full bg-wine text-[11px] text-white">1</span>
          Upload the product export
          <Help text={HELP.upload} />
        </h3>

        <div
          role="button"
          tabIndex={0}
          aria-label="Upload a product export CSV"
          onClick={() => inputRef.current?.click()}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault();
              inputRef.current?.click();
            }
          }}
          onDragOver={(e) => {
            e.preventDefault();
            if (!dragging) setDragging(true);
          }}
          onDragEnter={(e) => {
            e.preventDefault();
            setDragging(true);
          }}
          onDragLeave={(e) => {
            if (e.currentTarget.contains(e.relatedTarget as Node)) return;
            setDragging(false);
          }}
          onDrop={onDrop}
          data-testid="dropzone"
          className={`flex cursor-pointer flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed px-4 py-8 text-center transition-colors ${
            dragging ? 'border-wine bg-wine-light' : 'border-parchment bg-cream hover:border-wine/60 hover:bg-wine-light/40'
          }`}
        >
          <UploadCloud className={`h-8 w-8 ${dragging ? 'text-wine' : 'text-muted'}`} />
          {uploading ? (
            <div className="text-sm font-medium text-ink">Uploading {uploading}…</div>
          ) : (
            <>
              <div className="text-sm font-medium text-ink">
                {dragging ? 'Drop to upload' : 'Drag & drop the product export here'}
              </div>
              <div className="text-xs text-muted">
                or <span className="font-medium text-wine underline">browse</span> for the file — Lightspeed → Products →
                Export → CSV
              </div>
            </>
          )}
          <input
            ref={inputRef}
            type="file"
            accept=".csv,text/csv"
            className="hidden"
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) void upload(f);
              e.target.value = '';
            }}
          />
        </div>

        {uploadError && (
          <div className="mt-2 rounded-md bg-red-100 px-3 py-2 text-sm text-red-800">{uploadError}</div>
        )}
        {justUploaded && !uploadError && (
          <div className="mt-2 flex items-center gap-1.5 rounded-md bg-green-50 px-3 py-2 text-sm text-green-800">
            <CheckCircle2 className="h-4 w-4" /> {justUploaded} uploaded and selected — run ingestion below.
          </div>
        )}

        {/* Available inputs */}
        <div className="mt-4">
          <div className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-muted">Choose the input</div>
          {uploads.length === 0 && <div className="text-sm text-muted">Nothing uploaded yet.</div>}
          <ul className="divide-y divide-parchment/70 rounded-md border border-parchment">
            {uploads.map((u) => (
              <InputRow
                key={u.name}
                input={u}
                selected={u.name === selected}
                onSelect={() => setSelected(u.name)}
                onDelete={u.kind === 'upload' ? () => void remove(u.name) : undefined}
                disabled={running}
              />
            ))}
          </ul>
        </div>
      </section>

      {/* --- Step 2: run --------------------------------------------------- */}
      <section className="rounded-md border border-parchment bg-white p-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h3 className="flex items-center gap-1.5 text-sm font-semibold text-ink">
            <span className="flex h-5 w-5 items-center justify-center rounded-full bg-wine text-[11px] text-white">2</span>
            Run the filters
            <Help text={HELP.filters} />
          </h3>
          <button
            type="button"
            onClick={() => selected && onRun(selected)}
            disabled={running || !selected}
            className="rounded-md bg-wine px-3 py-1.5 text-sm font-medium text-white hover:bg-wine-dark disabled:opacity-50"
          >
            {ingestRunning ? 'Running…' : runLabel}
          </button>
        </div>
        <p className="mt-1 text-sm text-muted">
          Whitelisted categories are kept as-is. Uncategorized rows are checked against the vendor blacklist and the
          keyword list; what passes is kept as an uncategorized wine.
        </p>
        {(ingestRunning || ingestEvents.length > 0) && (
          <div className="mt-3">
            <EventLog events={ingestEvents} height="h-36" />
          </div>
        )}
      </section>

      {/* --- Step 3: results ----------------------------------------------- */}
      <section className="rounded-md border border-parchment bg-white p-4">
        <h3 className="mb-3 flex items-center gap-1.5 text-sm font-semibold text-ink">
          <span className="flex h-5 w-5 items-center justify-center rounded-full bg-wine text-[11px] text-white">3</span>
          Result
        </h3>
        {summary ? (
          <SummaryView summary={summary} />
        ) : (
          <div className="text-sm text-muted">
            {csv?.exists
              ? `combined.csv exists (${fmtNum(csv.row_count)} rows) but has no summary — run ingestion to see the filter results.`
              : 'Not run yet.'}
          </div>
        )}
      </section>

      {/* Keyed on the run so the loaded rows and filters reset after each ingestion. */}
      {summary && <ExcludedRows key={summary.generated_at} summary={summary} />}

      {!simple && (
        <>
          <FiltersView />
          <CsvPreview csv={csv} version={summary?.generated_at ?? csv?.mtime ?? null} />
        </>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------

function InputRow({
  input,
  selected,
  onSelect,
  onDelete,
  disabled,
}: {
  input: IngestInput;
  selected: boolean;
  onSelect: () => void;
  onDelete?: () => void;
  disabled: boolean;
}) {
  const isTest = input.kind === 'test';
  return (
    <li
      className={`flex items-center gap-3 px-3 py-2 text-sm ${selected ? 'bg-wine-light/50' : 'hover:bg-cream'}`}
      data-testid={`input-${input.name}`}
    >
      <label className="flex min-w-0 flex-1 cursor-pointer items-center gap-3">
        <input
          type="radio"
          name="ingest-input"
          checked={selected}
          onChange={onSelect}
          disabled={disabled}
          className="accent-wine"
        />
        {isTest ? (
          <FlaskConical className="h-4 w-4 shrink-0 text-muted" />
        ) : (
          <FileSpreadsheet className="h-4 w-4 shrink-0 text-muted" />
        )}
        <span className="min-w-0 flex-1">
          <span className="flex items-center gap-1.5 truncate font-medium text-ink">
            {input.label ?? input.name}
            {isTest && <Help text={HELP.test} />}
          </span>
          <span className="block text-xs text-muted">
            {fmtNum(input.rows)} rows · {fmtBytes(input.size)}
            {!isTest && ` · uploaded ${fmtDate(input.mtime)}`}
          </span>
        </span>
      </label>
      {onDelete && (
        <button
          type="button"
          onClick={onDelete}
          disabled={disabled}
          title="Delete this upload"
          aria-label={`Delete ${input.name}`}
          className="rounded p-1 text-muted hover:bg-red-50 hover:text-red-700 disabled:opacity-40"
        >
          <Trash2 className="h-4 w-4" />
        </button>
      )}
    </li>
  );
}

// ---------------------------------------------------------------------------

function Tile({ label, value, sub, tone = 'neutral' }: { label: string; value: string; sub?: string; tone?: 'neutral' | 'good' | 'bad' }) {
  const tones = {
    neutral: 'border-parchment bg-cream',
    good: 'border-green-200 bg-green-50',
    bad: 'border-amber-200 bg-amber-50',
  };
  return (
    <div className={`rounded-md border px-3 py-2 ${tones[tone]}`}>
      <div className="text-xs font-medium uppercase tracking-wide text-muted">{label}</div>
      <div className="text-2xl font-semibold text-ink">{value}</div>
      {sub && <div className="text-xs text-muted">{sub}</div>}
    </div>
  );
}

function SummaryView({ summary }: { summary: IngestSummary }) {
  const { input, kept, excluded } = summary;
  const uncatIn = input.rows - input.invalid_rows - excluded.by.category - kept.by_category; // rows reaching filter 2
  const afterVendor = uncatIn - excluded.by.vendor;
  const afterKeyword = afterVendor - excluded.by.name - excluded.by.keyword;

  return (
    <div className="space-y-4">
      <div className="text-xs text-muted">
        {input.name} · {fmtNum(input.rows)} rows · ingested {fmtDate(summary.generated_at)}
        {input.invalid_rows > 0 && ` · ${input.invalid_rows} rows with an invalid id skipped`}
      </div>

      <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
        <Tile label="Input rows" value={fmtNum(input.rows)} />
        <Tile label="Wines kept" value={fmtNum(kept.total)} sub="→ combined.csv" tone="good" />
        <Tile label="Green-lit by category" value={fmtNum(kept.by_category)} sub="already categorized" tone="good" />
        <Tile label="Uncategorized kept" value={fmtNum(kept.uncategorized)} sub="Ferment will categorize" tone="good" />
      </div>

      {/* Pipeline */}
      <div>
        <div className="mb-1.5 flex items-center gap-1 text-xs font-semibold uppercase tracking-wide text-muted">
          How the rows were decided <Help text={HELP.filters} />
        </div>
        <ol className="grid gap-2 sm:grid-cols-4">
          <Step
            n={1}
            title="Category"
            keep={`${fmtNum(kept.by_category)} kept`}
            drop={`${fmtNum(excluded.by.category)} excluded`}
            note={`${fmtNum(uncatIn)} uncategorized go on`}
          />
          <Step n={2} title="Vendor blacklist" keep={`${fmtNum(afterVendor)} go on`} drop={`${fmtNum(excluded.by.vendor)} excluded`} />
          <Step
            n={3}
            title="Name & keywords"
            keep={`${fmtNum(afterKeyword)} kept`}
            drop={`${fmtNum(excluded.by.name + excluded.by.keyword)} excluded`}
          />
          <li className="flex flex-col justify-center rounded-md border border-green-200 bg-green-50 px-3 py-2 text-sm">
            <div className="font-semibold text-green-900">{fmtNum(kept.total)} wines</div>
            <div className="text-xs text-green-800">
              {fmtNum(kept.by_category)} categorized + {fmtNum(kept.uncategorized)} uncategorized
            </div>
          </li>
        </ol>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <div>
          <div className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-muted">Kept, by category</div>
          <div className="flex flex-wrap gap-1.5">
            {Object.entries(kept.categories).map(([c, n]) => (
              <Chip key={c} tone="good">
                {c} <b>{fmtNum(n)}</b>
              </Chip>
            ))}
            <Chip tone="neutral">
              <span className="flex items-center gap-1">
                Uncategorized <b>{fmtNum(kept.uncategorized)}</b> <Help text={HELP.uncategorized} />
              </span>
            </Chip>
          </div>
        </div>
        <div>
          <div className="mb-1.5 flex items-center gap-1 text-xs font-semibold uppercase tracking-wide text-muted">
            Excluded {fmtNum(excluded.total)} <Help text={HELP.excluded} />
          </div>
          <div className="space-y-1.5">
            {EXCLUDED_BY.map((by) => (
              <BreakdownRow key={by} by={by} count={excluded.by[by]} values={excluded.breakdown[by]} />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function Step({ n, title, keep, drop, note }: { n: number; title: string; keep: string; drop: string; note?: string }) {
  return (
    <li className="rounded-md border border-parchment bg-cream px-3 py-2 text-sm">
      <div className="font-semibold text-ink">
        <span className="text-muted">{n}.</span> {title}
      </div>
      <div className="text-xs text-green-800">{keep}</div>
      <div className="text-xs text-amber-800">{drop}</div>
      {note && <div className="text-xs text-muted">{note}</div>}
    </li>
  );
}

function Chip({ children, tone }: { children: React.ReactNode; tone: 'good' | 'bad' | 'neutral' }) {
  const tones = {
    good: 'border-green-200 bg-green-50 text-green-900',
    bad: 'border-amber-200 bg-amber-50 text-amber-900',
    neutral: 'border-parchment bg-parchment text-ink',
  };
  return <span className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs ${tones[tone]}`}>{children}</span>;
}

function BreakdownRow({ by, count, values }: { by: ExcludedBy; count: number; values: Record<string, number> }) {
  const [open, setOpen] = useState(false);
  const entries = Object.entries(values ?? {});
  return (
    <div className="rounded-md border border-parchment">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        disabled={entries.length === 0}
        className="flex w-full items-center justify-between px-2.5 py-1.5 text-left text-sm disabled:cursor-default"
      >
        <span className="flex items-center gap-1.5 text-ink">
          {entries.length > 0 ? (
            open ? <ChevronDown className="h-3.5 w-3.5 text-muted" /> : <ChevronRight className="h-3.5 w-3.5 text-muted" />
          ) : (
            <span className="inline-block w-3.5" />
          )}
          {EXCLUDED_BY_LABEL[by]}
        </span>
        <span className="font-semibold text-amber-900">{fmtNum(count)}</span>
      </button>
      {open && (
        <div className="flex flex-wrap gap-1.5 border-t border-parchment/70 px-2.5 py-2">
          {entries.map(([v, n]) => (
            <Chip key={v} tone="bad">
              {v} <b>{fmtNum(n)}</b>
            </Chip>
          ))}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------

const PAGE = 200;

function ExcludedRows({ summary }: { summary: IngestSummary }) {
  const [open, setOpen] = useState(false);
  const [data, setData] = useState<IngestionRowsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [by, setBy] = useState<ExcludedBy | 'all'>('all');
  const [q, setQ] = useState('');
  const [shown, setShown] = useState(PAGE);

  useEffect(() => {
    if (!open || data) return;
    api
      .getIngestionExcluded()
      .then(setData)
      .catch((e) => setError(e instanceof Error ? e.message : 'Failed to load excluded rows'));
  }, [open, data]);

  const rows = useMemo(() => {
    if (!data) return [];
    const needle = q.trim().toLowerCase();
    return data.rows.filter(
      (r) =>
        (by === 'all' || r.excluded_by === by) &&
        (!needle ||
          String(r.name ?? '').toLowerCase().includes(needle) ||
          String(r.supplier_name ?? '').toLowerCase().includes(needle) ||
          String(r.excluded_reason ?? '').toLowerCase().includes(needle)),
    );
  }, [data, by, q]);

  const changeBy = (v: ExcludedBy | 'all') => {
    setBy(v);
    setShown(PAGE);
  };
  const changeQ = (v: string) => {
    setQ(v);
    setShown(PAGE);
  };

  return (
    <section className="rounded-md border border-parchment bg-white p-4">
      <button type="button" onClick={() => setOpen((v) => !v)} className="flex w-full items-center gap-1.5 text-left">
        {open ? <ChevronDown className="h-4 w-4 text-muted" /> : <ChevronRight className="h-4 w-4 text-muted" />}
        <h3 className="text-sm font-semibold text-ink">Excluded rows ({fmtNum(summary.excluded.total)})</h3>
        <span className="text-xs text-muted">— check nothing was filtered out by mistake</span>
      </button>
      {open && (
        <div className="mt-3 space-y-2">
          <div className="flex flex-wrap items-center gap-2 text-sm">
            <select
              value={by}
              onChange={(e) => changeBy(e.target.value as ExcludedBy | 'all')}
              className="rounded-md border border-parchment bg-white px-2 py-1 text-sm"
            >
              <option value="all">All filters</option>
              {EXCLUDED_BY.map((b) => (
                <option key={b} value={b}>
                  {EXCLUDED_BY_LABEL[b]} ({fmtNum(summary.excluded.by[b])})
                </option>
              ))}
            </select>
            <input
              value={q}
              onChange={(e) => changeQ(e.target.value)}
              placeholder="Search name, supplier, reason…"
              className="min-w-56 flex-1 rounded-md border border-parchment bg-white px-2 py-1 text-sm"
            />
            <span className="text-xs text-muted">
              {data ? `${fmtNum(rows.length)} of ${fmtNum(data.total)}` : 'Loading…'}
            </span>
          </div>
          {error && <div className="text-sm text-red-700">{error}</div>}
          {data && (
            <div className="max-h-96 overflow-auto rounded-md border border-parchment">
              <table className="w-full text-xs">
                <thead className="sticky top-0 bg-parchment">
                  <tr>
                    <th className="px-2 py-1 text-left font-semibold text-muted">Name</th>
                    <th className="px-2 py-1 text-left font-semibold text-muted">Category</th>
                    <th className="px-2 py-1 text-left font-semibold text-muted">Supplier</th>
                    <th className="px-2 py-1 text-left font-semibold text-muted">Filter</th>
                    <th className="px-2 py-1 text-left font-semibold text-muted">Reason</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.slice(0, shown).map((r, i) => (
                    <tr key={String(r.id ?? i)} className="border-t border-parchment/60">
                      <td className="whitespace-nowrap px-2 py-1 font-medium text-ink">{String(r.name ?? '')}</td>
                      <td className="whitespace-nowrap px-2 py-1 text-ink">{String(r.product_category ?? '') || '—'}</td>
                      <td className="whitespace-nowrap px-2 py-1 text-ink">{String(r.supplier_name ?? '') || '—'}</td>
                      <td className="whitespace-nowrap px-2 py-1 text-ink">
                        {EXCLUDED_BY_LABEL[r.excluded_by as ExcludedBy] ?? String(r.excluded_by ?? '')}
                      </td>
                      <td className="px-2 py-1 text-muted">{String(r.excluded_reason ?? '')}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {rows.length > shown && (
                <button
                  type="button"
                  onClick={() => setShown((s) => s + PAGE)}
                  className="w-full border-t border-parchment px-2 py-1.5 text-xs font-medium text-wine hover:bg-cream"
                >
                  Show {Math.min(PAGE, rows.length - shown)} more
                </button>
              )}
            </div>
          )}
        </div>
      )}
    </section>
  );
}

// ---------------------------------------------------------------------------

function FiltersView() {
  const [open, setOpen] = useState(false);
  const [filters, setFilters] = useState<IngestFilters | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!open || filters) return;
    api
      .getIngestionFilters()
      .then(setFilters)
      .catch((e) => setError(e instanceof Error ? e.message : 'Failed to load filters'));
  }, [open, filters]);

  return (
    <section className="rounded-md border border-parchment bg-white p-4">
      <button type="button" onClick={() => setOpen((v) => !v)} className="flex w-full items-center gap-1.5 text-left">
        {open ? <ChevronDown className="h-4 w-4 text-muted" /> : <ChevronRight className="h-4 w-4 text-muted" />}
        <h3 className="text-sm font-semibold text-ink">Filter rules</h3>
        <span className="text-xs text-muted">— edit ingestion/filters.toml, then run again</span>
      </button>
      {open && (
        <div className="mt-3 space-y-3 text-sm">
          {error && <div className="text-red-700">{error}</div>}
          {filters && (
            <>
              <div className="text-xs text-muted">{filters.path}</div>
              <Rule title="1 · Category whitelist (kept as-is; any other category is excluded)" items={filters.categories.whitelist} tone="good" />
              <Rule title="2 · Vendor blacklist (uncategorized rows only; matches the supplier's leading words)" items={filters.vendors.blacklist} tone="bad" />
              <Rule title="3a · Exact names excluded" items={filters.names.exclude} tone="bad" />
              {Object.entries(filters.keywords).map(([group, terms]) => (
                <Rule key={group} title={`3b · Keywords — ${group} (whole-word match)`} items={terms} tone="bad" />
              ))}
            </>
          )}
        </div>
      )}
    </section>
  );
}

function Rule({ title, items, tone }: { title: string; items: string[]; tone: 'good' | 'bad' }) {
  return (
    <div>
      <div className="mb-1 text-xs font-semibold text-ink">{title}</div>
      <div className="flex flex-wrap gap-1">
        {items.length === 0 && <span className="text-xs text-muted">none</span>}
        {items.map((i) => (
          <Chip key={i} tone={tone}>
            {i}
          </Chip>
        ))}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------

function CsvPreview({ csv, version }: { csv: StatusResponse['ingestion']['csv'] | undefined; version: string | null }) {
  const [rows, setRows] = useState<IngestionRowsResponse | null>(null);
  const [expanded, setExpanded] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!csv?.exists) return;
    api
      .getIngestionRows(10)
      .then(setRows)
      .catch((e) => setError(e instanceof Error ? e.message : 'Failed to load rows'));
  }, [csv?.exists, version]);

  const cols = rows ? (expanded ? rows.columns : rows.columns.slice(0, 8)) : [];

  return (
    <section className="rounded-md border border-parchment bg-white p-4">
      <div className="mb-2 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-ink">combined.csv preview</h3>
        {rows && (
          <button type="button" onClick={() => setExpanded((v) => !v)} className="text-xs font-medium text-wine hover:underline">
            {expanded ? 'Fewer columns' : 'All columns'}
          </button>
        )}
      </div>
      {csv?.exists ? (
        <div className="mb-2 text-xs text-muted">
          {csv.path} — {fmtNum(csv.row_count)} rows — updated {fmtDate(csv.mtime)}
        </div>
      ) : (
        <div className="text-sm text-muted">Not generated yet.</div>
      )}
      {error && <div className="text-sm text-red-700">{error}</div>}
      {rows && rows.rows.length > 0 && (
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-parchment">
                {cols.map((c) => (
                  <th key={c} className="whitespace-nowrap px-2 py-1 text-left font-semibold text-muted">
                    {c}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.rows.map((r, i) => (
                <tr key={i} className="border-b border-parchment/60 last:border-0">
                  {cols.map((c) => (
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
    </section>
  );
}
