import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';
import type { JobEvent } from '../api';
import {
  computeRunProgress,
  formatClock,
  formatDuration,
  hasRunStart,
  overallEta,
  overallFraction,
  phaseEta,
} from './progress';

// Fixtures are real logs/<run>/events.jsonl excerpts (written before run_plan
// and wine_start existed), trimmed to the fields the bars read.
const fixture = (name: string): JobEvent[] =>
  readFileSync(new URL(`./__fixtures__/${name}`, import.meta.url), 'utf8')
    .split('\n')
    .filter(Boolean)
    .map((l) => JSON.parse(l) as JobEvent);

const bars = (events: JobEvent[], live = true) => {
  const { phases } = computeRunProgress(events, { live });
  return Object.fromEntries(Object.entries(phases).map(([k, p]) => [k, `${p.state} ${p.done}/${p.total}`]));
};

/** A run in today's event format: run_plan, wine_start, skipped flags. */
function newFormatRun(opts: { resume?: string; cursor?: number; stopAfter?: string | null } = {}) {
  const { resume = 'search', cursor = 0, stopAfter = null } = opts;
  const total = 4;
  const ev: JobEvent[] = [];
  let ts = 1000;
  const push = (e: JobEvent) => ev.push({ ts, run_id: 'r1', ...e });
  push({ type: 'info', phase: resume, total, cursor });
  const phases = ['search', 'score', 'tag'];
  const start = phases.indexOf(resume);
  push({
    type: 'run_plan', total, resume_phase: resume, cursor, stop_after: stopAfter,
    phases: Object.fromEntries(phases.map((p, i) => [p, i < start ? { state: 'done', done: total } : { state: 'pending', done: i === start ? cursor : 0 }])),
  });
  return { ev, push, tick: (s: number) => (ts += s), total };
}

describe('the bug as reported (Oct 1, run 20261001-115700)', () => {
  const events = fixture('oct01-start-of-score.jsonl');

  it('gives every bar its real total from the first event', () => {
    // Event 0 is the run's opening info; before the fix score and tag read 0 / 1.
    expect(bars(events.slice(0, 1))).toEqual({
      search: 'pending 0/24', score: 'pending 0/24', tag: 'pending 0/24',
    });
  });

  it('counts wines done from 1, matching the log line', () => {
    // Events 0–2: phase_start, then `[search 1/24] Annabella…` (index 0).
    expect(bars(events.slice(0, 3)).search).toBe('running 1/24');
    // Events 0–7: six wines done (`[search 6/24]`); the old bar said 5.
    expect(bars(events.slice(0, 8)).search).toBe('running 6/24');
  });

  it('shows score and tag waiting at 0 / 24 while search runs, and search done once it ends', () => {
    expect(bars(events)).toEqual({ search: 'done 24/24', score: 'running 0/24', tag: 'pending 0/24' });
  });

  it('times wines and estimates the rest once three are done', () => {
    const p2 = computeRunProgress(events.slice(0, 4)).phases.search; // two wines done
    expect(p2.secPerWine).toBeNull();
    const p = computeRunProgress(events.slice(0, 8)).phases.search; // six done
    expect(p.secPerWine).toBeGreaterThan(5);
    expect(p.secPerWine).toBeLessThan(15);
    // At the moment the 6th finished, 18 wines remain at that rate.
    const last = Number(events[7].ts);
    expect(phaseEta(p, last)).toBeCloseTo(18 * p.secPerWine!, 5);
  });
});

describe('re-runs and stops (real logs)', () => {
  it('re-run from tag: search and score are done, and Stop leaves tag stopped, not running', () => {
    const events = fixture('sep15c-rerun-tag-interrupted.jsonl');
    expect(bars(events.slice(0, 4))).toEqual({ search: 'done 24/24', score: 'done 24/24', tag: 'running 2/24' });
    expect(bars(events)).toEqual({ search: 'done 24/24', score: 'done 24/24', tag: 'stopped 2/24' });
  });

  it('a second invocation in the same log starts from its own plan', () => {
    const events = fixture('sep15b-two-invocations.jsonl');
    const second = events.findIndex((e, i) => i > 0 && e.type === 'info' && e.total === 24);
    expect(bars(events.slice(0, second + 2))).toEqual({
      search: 'done 24/24', score: 'running 0/24', tag: 'pending 0/24',
    });
    expect(bars(events)).toEqual({ search: 'done 24/24', score: 'done 24/24', tag: 'done 24/24' });
  });

  it('never goes backwards when the server replays the history a second time', () => {
    const events = fixture('oct01-start-of-score.jsonl');
    const doubled = [...events, ...events.slice(0, 10)];
    expect(bars(doubled).search).toBe('done 24/24');
  });
});

describe('today’s event format', () => {
  it('names the wine being worked on and when it started', () => {
    const r = newFormatRun();
    r.push({ type: 'phase_start', phase: 'search', total: r.total });
    r.push({ type: 'wine_start', phase: 'search', index: 0, total: r.total, name: 'Aster' });
    const p = computeRunProgress(r.ev).phases.search;
    expect(p.current).toEqual({ index: 0, name: 'Aster', since: 1000 });
    r.tick(20);
    r.push({ type: 'progress', phase: 'search', index: 0, total: r.total });
    expect(computeRunProgress(r.ev).phases.search.current).toEqual({ index: 1, name: null, since: 1020 });
  });

  it('a resumed phase starts at its cursor, not 0, and never dips on phase_start', () => {
    const r = newFormatRun({ resume: 'score', cursor: 2 });
    expect(bars(r.ev)).toEqual({ search: 'done 4/4', score: 'pending 2/4', tag: 'pending 0/4' });
    r.push({ type: 'phase_start', phase: 'score', total: r.total });
    expect(bars(r.ev).score).toBe('running 2/4');
    r.push({ type: 'wine_start', phase: 'score', index: 2, total: r.total, name: 'Cloudline' });
    r.push({ type: 'progress', phase: 'score', index: 2, total: r.total });
    expect(bars(r.ev).score).toBe('running 3/4');
  });

  it('leaves human skips out of the rate', () => {
    const r = newFormatRun();
    r.push({ type: 'phase_start', phase: 'tag', total: r.total });
    for (let i = 0; i < 4; i++) {
      if (i === 1) {
        r.push({ type: 'progress', phase: 'tag', index: i, total: r.total, skipped: true });
        continue;
      }
      r.push({ type: 'wine_start', phase: 'tag', index: i, total: r.total, name: `w${i}` });
      r.tick(30);
      r.push({ type: 'progress', phase: 'tag', index: i, total: r.total });
    }
    expect(computeRunProgress(r.ev).phases.tag.secPerWine).toBe(30);
  });

  it('exit or a closed stream clears "running"', () => {
    const r = newFormatRun();
    r.push({ type: 'phase_start', phase: 'search', total: r.total });
    r.push({ type: 'progress', phase: 'search', index: 0, total: r.total });
    expect(bars(r.ev, false).search).toBe('stopped 1/4');
    r.push({ type: 'exit', exit_code: -9 });
    expect(bars(r.ev).search).toBe('stopped 1/4');
  });

  it('a phase past the pause point is not part of this invocation', () => {
    const r = newFormatRun({ stopAfter: 'search' });
    const { phases } = computeRunProgress(r.ev);
    expect([phases.search.inRun, phases.score.inRun, phases.tag.inRun]).toEqual([true, false, false]);
  });
});

describe('the overall bar', () => {
  it('weights phases by time and never falls as a phase starts', () => {
    const events = fixture('oct01-start-of-score.jsonl');
    const fractions = events.map((_, i) => overallFraction(computeRunProgress(events.slice(0, i + 1))));
    for (let i = 1; i < fractions.length; i++) expect(fractions[i]).toBeGreaterThanOrEqual(fractions[i - 1]);
    // Search alone is about a sixth of a run's time, not a third.
    expect(fractions.at(-1)).toBeCloseTo(17 / 107, 5);
  });

  it('estimates the time left: the running phase’s own rate, then typical times', () => {
    const events = fixture('oct01-start-of-score.jsonl').slice(0, 8);
    const r = computeRunProgress(events);
    const now = Number(events[7].ts);
    expect(overallEta(r, now)).toBeCloseTo(phaseEta(r.phases.search, now)! + 24 * 60 + 24 * 30, 5);
    expect(overallEta(computeRunProgress(fixture('sep15b-two-invocations.jsonl')), now)).toBeNull();
  });
});

describe('helpers', () => {
  it('hasRunStart ignores an ingest job’s events', () => {
    expect(hasRunStart([{ type: 'info', message: 'Reading x.csv' }, { type: 'progress', index: 500, total: 900 }])).toBe(false);
    expect(hasRunStart(fixture('oct01-start-of-score.jsonl').slice(0, 1))).toBe(true);
  });

  it('formats durations and clocks', () => {
    expect(formatDuration(45)).toBe('45 s');
    expect(formatDuration(12 * 60 + 10)).toBe('12 min');
    expect(formatDuration(65 * 60)).toBe('1 h 05 min');
    expect(formatClock(42)).toBe('0:42');
    expect(formatClock(725)).toBe('12:05');
  });
});
