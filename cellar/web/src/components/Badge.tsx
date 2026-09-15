import type { ReactNode } from 'react';
import { TAG_STATUS_LABEL, type TagStatus } from '../api';

export const TAG_STATUS_STYLES: Record<string, string> = {
  model: 'bg-green-100 text-green-800 border-green-300',
  needs_review: 'bg-amber-100 text-amber-800 border-amber-300',
  human: 'bg-blue-100 text-blue-800 border-blue-300',
  pending: 'bg-gray-100 text-gray-600 border-gray-300',
};

export const TAG_STATUS_TITLE: Record<string, string> = {
  model: 'Tagged by the LLM and cleared the confidence threshold',
  needs_review: 'The LLM could not tag this confidently (or at all)',
  human: 'Tags saved by a person in Cellar; fermentation never overwrites it',
  pending: 'Not tagged yet',
};

export function StatusBadge({ status }: { status: string }) {
  const style = TAG_STATUS_STYLES[status] ?? TAG_STATUS_STYLES.pending;
  const label = TAG_STATUS_LABEL[status as TagStatus] ?? status.replace('_', ' ');
  return (
    <span
      title={TAG_STATUS_TITLE[status]}
      className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium ${style}`}
    >
      {label}
    </span>
  );
}

export function Badge({
  children,
  tone = 'neutral',
}: {
  children: ReactNode;
  tone?: 'neutral' | 'wine' | 'muted';
}) {
  const tones: Record<string, string> = {
    neutral: 'bg-parchment text-ink border-parchment',
    wine: 'bg-wine-light text-wine-dark border-wine-light',
    muted: 'bg-gray-100 text-muted border-gray-200',
  };
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium ${tones[tone]}`}
    >
      {children}
    </span>
  );
}

const PHASE_STYLES: Record<string, string> = {
  ok: 'bg-green-500',
  empty: 'bg-gray-300',
  no_context: 'bg-amber-400',
  skipped: 'bg-gray-300',
  no_submit: 'bg-red-400',
  null: 'bg-gray-200',
};

export function PhaseDot({ label, value }: { label: string; value: string | null | undefined }) {
  const key = value ?? 'null';
  const color = PHASE_STYLES[key] ?? 'bg-gray-200';
  return (
    <span
      title={`${label}: ${value ?? 'null'}`}
      className={`inline-block h-2.5 w-2.5 rounded-full ${color}`}
    />
  );
}
