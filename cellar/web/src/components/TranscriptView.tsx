import type { TranscriptMessage } from '../api';
import { JsonView } from './JsonView';

const ROLE_STYLES: Record<string, string> = {
  system: 'border-gray-300 bg-gray-50',
  user: 'border-blue-200 bg-blue-50',
  assistant: 'border-wine-light bg-wine-light/40',
  tool: 'border-amber-200 bg-amber-50',
};

function tryParseJson(text: string | null | undefined): unknown | null {
  if (!text) return null;
  try {
    return JSON.parse(text);
  } catch {
    return null;
  }
}

export function TranscriptView({ transcript }: { transcript: TranscriptMessage[] }) {
  if (!transcript || transcript.length === 0) {
    return <div className="text-sm text-muted">No transcript.</div>;
  }
  return (
    <div className="space-y-3">
      {transcript.map((m, i) => {
        const toolResult = m.role === 'tool' ? tryParseJson(m.content) : null;
        return (
          <div key={i} className={`rounded-md border p-2 text-sm ${ROLE_STYLES[m.role] ?? 'border-parchment bg-white'}`}>
            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-muted">
              <span>{m.role}</span>
              {m.name && <span className="normal-case text-ink">({m.name})</span>}
            </div>

            {m.content && !toolResult && (
              <p className="mt-1 whitespace-pre-wrap text-ink">{m.content}</p>
            )}

            {toolResult != null && (
              <pre className="mt-1 max-h-72 overflow-auto rounded bg-ink/5 p-2 text-xs">
                {JSON.stringify(toolResult, null, 2)}
              </pre>
            )}

            {m.tool_calls && m.tool_calls.length > 0 && (
              <div className="mt-2 space-y-1">
                {m.tool_calls.map((tc) => {
                  const args = tryParseJson(tc.function.arguments) ?? tc.function.arguments;
                  return (
                    <div key={tc.id} className="rounded border border-amber-300 bg-white p-1.5">
                      <div className="text-xs font-medium text-amber-800">
                        tool_call: {tc.function.name}
                      </div>
                      <pre className="mt-1 max-h-48 overflow-auto text-xs">
                        {typeof args === 'string' ? args : JSON.stringify(args, null, 2)}
                      </pre>
                    </div>
                  );
                })}
              </div>
            )}

            <JsonView data={m} label="message JSON" />
          </div>
        );
      })}
    </div>
  );
}
