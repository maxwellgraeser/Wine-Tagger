import { useRef, useState } from 'react';
import { CircleHelp } from 'lucide-react';

const TIP_WIDTH = 288;

/** A small "?" icon that shows a rendered tooltip explaining a control on hover
 *  or keyboard focus. (Native `title` tooltips are slow and unreliable in some
 *  webviews, so the text is drawn by us.) Positioned `fixed` so panels with
 *  overflow don't clip it. */
export function Help({ text, className = '' }: { text: string; className?: string }) {
  const ref = useRef<HTMLSpanElement>(null);
  const [pos, setPos] = useState<{ left: number; top: number; above: boolean } | null>(null);

  const show = () => {
    const r = ref.current?.getBoundingClientRect();
    if (!r) return;
    const left = Math.min(Math.max(8, r.left + r.width / 2 - TIP_WIDTH / 2), window.innerWidth - TIP_WIDTH - 8);
    const above = r.bottom + 160 > window.innerHeight;
    setPos({ left, top: above ? r.top - 6 : r.bottom + 6, above });
  };
  const hide = () => setPos(null);

  return (
    <span
      ref={ref}
      tabIndex={0}
      role="img"
      aria-label={text}
      onMouseEnter={show}
      onMouseLeave={hide}
      onFocus={show}
      onBlur={hide}
      // The icon often sits inside a <label>; don't let a click toggle its control.
      onClick={(e) => e.preventDefault()}
      className={`inline-flex cursor-help text-muted hover:text-ink focus:text-ink focus:outline-none ${className}`}
    >
      <CircleHelp className="h-3.5 w-3.5" />
      {pos && (
        <span
          role="tooltip"
          style={{
            position: 'fixed',
            left: pos.left,
            top: pos.top,
            width: TIP_WIDTH,
            transform: pos.above ? 'translateY(-100%)' : undefined,
          }}
          className="pointer-events-none z-50 rounded-md bg-ink px-2.5 py-1.5 text-left text-xs font-normal leading-snug text-cream normal-case shadow-lg"
        >
          {text}
        </span>
      )}
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
