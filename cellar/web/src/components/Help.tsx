import { CircleHelp } from 'lucide-react';

/** A small "?" icon whose native tooltip explains a control. */
export function Help({ text, className = '' }: { text: string; className?: string }) {
  return (
    <span title={text} aria-label={text} className={`inline-flex cursor-help text-muted hover:text-ink ${className}`}>
      <CircleHelp className="h-3.5 w-3.5" />
    </span>
  );
}

/** Tooltip text for the Ferment runtime options. Kept in one place so the
 *  labels, the simple view, and the docs say the same thing. */
export const FERMENT_HELP = {
  force:
    'Ignore the saved resume cursor and start a brand-new run from the search phase. ' +
    'Without it, a run that was stopped or interrupted picks up where it left off (as long as the wine set is the same).',
  limit:
    'Process only the first N wines of combined.csv (blank or 0 = all). Handy for a quick test run. ' +
    'A saved resume cursor only applies to a run over the same wine set, so changing the limit starts a fresh run.',
  threshold:
    "Minimum tagger confidence (0-100) for a wine to be tagged 'Model' instead of 'Needs review'. " +
    'Saved to settings.json when you leave the field, and used by console runs too.',
  model:
    'Model name sent with every request to llama-server. The list is what the server currently reports as loaded; ' +
    'it serves one model at a time, so pick the one it has loaded (start it from the top bar if it is down).',
  producerGate:
    "Producer gate: before scoring, every web snippet that doesn't mention any significant word from the wine's name or brand " +
    "is dropped (dropped_reason = producer_absent) so text about a different producer never reaches the tagger. " +
    "If every snippet is dropped the wine gets no web context and lands in 'Needs review'. " +
    'Disabling the gate is a debugging aid: all snippets are scored and can be pasted into web_context.',
  pause:
    'Stop after each phase (search, score) so you can inspect the logs and the wine table before continuing. ' +
    "A 'Continue' button appears when a run is paused.",
  rerun:
    "Start again at the chosen phase reusing an earlier run's logs: score re-reads that run's search snippets, " +
    "tag re-reads its scorer output. The run keeps its id and its later-phase logs are overwritten. " +
    'Useful after changing the scorer, tagger, or threshold without searching the web again.',
};
