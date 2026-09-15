// Typed API client for the Cellar backend. Backend lives at the same origin
// under /api (proxied to http://localhost:8000 in dev via vite.config.ts).

export type Stage = 'ingestion' | 'fermentation' | 'distribution' | string;

export interface InputFile {
  name: string;
  exists: boolean;
  mtime: string | null;
  size: number | null;
}

export interface CsvInfo {
  exists: boolean;
  path: string | null;
  mtime: string | null;
  row_count: number | null;
}

export interface LlamaStatus {
  ok: boolean;
  base_url: string;
  models: string[];
}

export interface RunState {
  run_id: string;
  phase: string;
  cursor: number | null;
}

export interface WinesJsonStatus {
  exists: boolean;
  count: number;
  by_status: {
    auto: number;
    needs_review: number;
    manual: number;
    pending: number;
  };
}

export interface FermentationStatus {
  wines_json: WinesJsonStatus;
  last_run_id: string | null;
  run_state: RunState | null;
  runs: string[];
}

export interface JobSummary {
  id: string;
  stage: Stage;
  running: boolean;
  run_id?: string | null;
  [key: string]: unknown;
}

export interface ActiveJob {
  id: string;
  stage: Stage;
  running: boolean;
  run_id: string | null;
}

export interface StatusResponse {
  now: string;
  defaults: {
    api_url: string;
    model: string;
    confidence_threshold: number;
  };
  llama: LlamaStatus;
  ingestion: {
    inputs: InputFile[];
    csv: CsvInfo;
  };
  fermentation: FermentationStatus;
  active_job: ActiveJob | null;
  jobs: JobSummary[];
}

export interface IngestionRowsResponse {
  path: string;
  columns: string[];
  rows: Record<string, unknown>[];
}

export interface SalesStats {
  items_sold: number | null;
  margin_pct: number | null;
  sale_count: number | null;
  customer_count: number | null;
  avg_sale_value: number | null;
}

export type PhaseStatusValue =
  | 'ok'
  | 'empty'
  | 'no_context'
  | 'skipped'
  | 'no_submit'
  | 'null'
  | null;

export interface PhaseStatus {
  search: PhaseStatusValue;
  score: PhaseStatusValue;
  tag: PhaseStatusValue;
}

export type TagStatus = 'pending' | 'auto' | 'needs_review' | 'manual';

export interface Wine {
  id: number | string;
  name: string;
  sku: string | null;
  category: string | null;
  supply_price: number | null;
  retail_price: number | null;
  supplier: string | null;
  brand: string | null;
  country: string | null;
  region: string[];
  grapes: string[];
  is_blend: boolean | null;
  organic: boolean;
  confidence: number | null;
  web_context: string | null;
  tags_raw: string | null;
  tag_status: TagStatus;
  sales: SalesStats;
  run_id: string | null;
  phase_status: PhaseStatus;
  updated_at: string | null;
}

export interface WinesResponse {
  generated_at: string | null;
  last_run_id: string | null;
  wines: Wine[];
}

export interface Snippet {
  source: string | null;
  domain: string | null;
  body: string | null;
  url: string | null;
}

export interface ScoredSnippet extends Snippet {
  match_score: number | null;
  dropped_reason: string | null;
}

export interface TranscriptToolCall {
  id: string;
  function: {
    name: string;
    arguments: string;
  };
}

export interface TranscriptMessage {
  role: 'system' | 'user' | 'assistant' | 'tool';
  content: string | null;
  tool_calls?: TranscriptToolCall[];
  tool_call_id?: string;
  name?: string;
}

export interface SearchLog {
  run_id: string;
  snippets: Snippet[];
  raw_snippet_count: number;
}

export interface ScorerLog {
  input_count: number;
  producer_gate_dropped: number;
  scored_snippets: ScoredSnippet[];
  web_context_built: boolean;
  web_context: string | null;
}

export interface TaggerLog {
  had_web_context: boolean;
  submit_attempts: number;
  success: boolean;
  transcript: TranscriptMessage[];
}

export interface NormalizedTags {
  country: string | null;
  region: string[];
  grapes: string[];
  is_blend: boolean | null;
  organic: boolean;
  confidence: number | null;
}

export interface FinalLog {
  tag_status: TagStatus;
  organic: boolean;
  normalized: NormalizedTags | null;
  tags_raw: string | null;
}

export interface WineLogs {
  run_id: string;
  search: SearchLog | null;
  scorer: ScorerLog | null;
  tagger: TaggerLog | null;
  final: FinalLog | null;
}

export interface WineDetailResponse {
  wine: Wine;
  logs: WineLogs;
  runs: string[];
}

export interface WinePatch {
  country?: string | null;
  region?: string[];
  grapes?: string[];
  is_blend?: boolean | null;
  organic?: boolean;
  confidence?: number | null;
  tag_status?: TagStatus;
}

export interface RunPhaseSummary {
  status: string;
  counts?: Record<string, number>;
}

export interface RunSummary {
  run_id: string;
  started_at: string | null;
  ended_at: string | null;
  status: string;
  product_count: number | null;
  phases: {
    search?: RunPhaseSummary;
    score?: RunPhaseSummary;
    tag?: RunPhaseSummary;
  };
  config: Record<string, unknown>;
}

export interface RunDetailResponse {
  run: RunSummary;
  files: unknown;
}

export interface RunEventsResponse {
  events: JobEvent[];
}

export interface RegionEntry {
  name: string;
  country: string;
  classification: string | null;
}

export interface GrapeEntry {
  name: string;
  color: string | null;
}

export interface JobEvent {
  type: string;
  message?: string;
  ts?: string;
  [key: string]: unknown;
}

export interface JobDetailResponse extends JobSummary {
  events: JobEvent[];
}

export interface FermentRunOptions {
  force?: boolean;
  limit?: number;
  confidence_threshold?: number;
  model?: string;
  api_url?: string;
  no_producer_gate?: boolean;
  phase?: 'search' | 'score' | 'tag';
  run_id?: string;
}

const BASE = '/api';

class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: init?.body ? { 'Content-Type': 'application/json' } : undefined,
    ...init,
  });
  if (!res.ok) {
    let message = `${res.status} ${res.statusText}`;
    try {
      const body = await res.json();
      if (body?.detail) message = body.detail;
      else if (body?.message) message = body.message;
    } catch {
      // ignore body parse failure
    }
    throw new ApiError(res.status, message);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export const api = {
  getStatus: () => request<StatusResponse>('/status'),

  runIngest: () => request<JobSummary>('/ingest/run', { method: 'POST' }),

  runFerment: (opts: FermentRunOptions) =>
    request<JobSummary>('/ferment/run', {
      method: 'POST',
      body: JSON.stringify(opts),
    }),

  startLlama: () => request<{ started: boolean; [key: string]: unknown }>('/llama/start', { method: 'POST' }),
  getLlamaLog: (lines = 60) => request<{ lines: string[] }>(`/llama/log?lines=${lines}`),

  getJobs: () => request<JobSummary[]>('/jobs'),
  getJob: (id: string) => request<JobDetailResponse>(`/jobs/${id}`),
  stopJob: (id: string) => request<void>(`/jobs/${id}/stop`, { method: 'POST' }),
  jobEventsUrl: (id: string) => `${BASE}/jobs/${id}/events`,

  getIngestionRows: () => request<IngestionRowsResponse>('/ingestion/rows'),

  getWines: () => request<WinesResponse>('/wines'),
  getWine: (id: number | string, runId?: string) =>
    request<WineDetailResponse>(`/wines/${id}${runId ? `?run_id=${encodeURIComponent(runId)}` : ''}`),
  patchWine: (id: number | string, patch: WinePatch) =>
    request<Wine>(`/wines/${id}`, { method: 'PATCH', body: JSON.stringify(patch) }),
  resetManualWines: () => request<{ reset: number }>('/wines/reset-manual', { method: 'POST' }),

  getRuns: () => request<RunSummary[]>('/runs'),
  getRun: (runId: string) => request<RunDetailResponse>(`/runs/${encodeURIComponent(runId)}`),
  getRunEvents: (runId: string, limit?: number) =>
    request<RunEventsResponse>(`/runs/${encodeURIComponent(runId)}/events${limit ? `?limit=${limit}` : ''}`),

  getCountries: () => request<string[]>('/library/countries'),
  getRegions: (country?: string) =>
    request<RegionEntry[]>(`/library/regions${country ? `?country=${encodeURIComponent(country)}` : ''}`),
  getGrapes: () => request<GrapeEntry[]>('/library/grapes'),

  exportUrl: (statuses?: string[]) =>
    `${BASE}/export.xlsx${statuses && statuses.length ? `?status=${statuses.join(',')}` : ''}`,
};

export { ApiError };
