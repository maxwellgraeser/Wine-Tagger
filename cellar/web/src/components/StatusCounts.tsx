import { TAG_STATUSES, TAG_STATUS_LABEL, type TagStatus } from '../api';
import { TAG_STATUS_STYLES, TAG_STATUS_TITLE } from './Badge';

/** The four tag-status counters shown on the Ferment and Distribute panels. */
export function StatusCounts({ byStatus }: { byStatus: Partial<Record<TagStatus, number>> }) {
  return (
    <div className="flex flex-wrap gap-2 text-xs">
      {TAG_STATUSES.map((s) => (
        <span
          key={s}
          title={TAG_STATUS_TITLE[s]}
          className={`rounded-full border px-2 py-0.5 ${TAG_STATUS_STYLES[s]}`}
        >
          {TAG_STATUS_LABEL[s]}: {byStatus[s] ?? 0}
        </span>
      ))}
    </div>
  );
}
