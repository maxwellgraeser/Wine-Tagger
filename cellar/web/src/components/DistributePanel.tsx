import { Download } from 'lucide-react';
import { api, type StatusResponse, type Wine } from '../api';
import { WineTable } from './WineTable';

export function DistributePanel({
  status,
  wines,
  onSelect,
  showDevColumns,
}: {
  status: StatusResponse | null;
  wines: Wine[];
  onSelect: (w: Wine) => void;
  showDevColumns: boolean;
}) {
  const byStatus = status?.fermentation.wines_json.by_status;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-lg font-semibold text-ink">Distribute</h2>
        <a
          href={api.exportUrl()}
          className="flex items-center gap-1.5 rounded-md bg-wine px-3 py-1.5 text-sm font-medium text-white hover:bg-wine-dark"
        >
          <Download className="h-4 w-4" />
          Export Lightspeed .xlsx
        </a>
      </div>

      {byStatus && (
        <div className="flex flex-wrap gap-2 text-xs">
          <span className="rounded-full bg-green-100 px-2 py-0.5 text-green-800">auto: {byStatus.auto}</span>
          <span className="rounded-full bg-amber-100 px-2 py-0.5 text-amber-800">
            needs_review: {byStatus.needs_review}
          </span>
          <span className="rounded-full bg-blue-100 px-2 py-0.5 text-blue-800">manual: {byStatus.manual}</span>
          <span className="rounded-full bg-gray-100 px-2 py-0.5 text-gray-700">pending: {byStatus.pending}</span>
        </div>
      )}

      <WineTable wines={wines} onSelect={onSelect} showDevColumns={showDevColumns} />
    </div>
  );
}
