import { useMemo, useState } from 'react';
import type { Wine } from '../api';
import { Badge, PhaseDot, StatusBadge } from './Badge';

type SortKey = 'name' | 'category' | 'brand' | 'country' | 'confidence' | 'tag_status';

export function WineTable({
  wines,
  onSelect,
  showDevColumns,
}: {
  wines: Wine[];
  onSelect: (w: Wine) => void;
  showDevColumns: boolean;
}) {
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [sortKey, setSortKey] = useState<SortKey>('name');
  const [sortDir, setSortDir] = useState<1 | -1>(1);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    let rows = wines;
    if (statusFilter !== 'all') {
      rows = rows.filter((w) => w.tag_status === statusFilter);
    }
    if (q) {
      rows = rows.filter((w) => {
        const hay = [
          w.name,
          w.category,
          w.brand,
          w.country,
          ...(w.region ?? []),
          ...(w.grapes ?? []),
        ]
          .filter(Boolean)
          .join(' ')
          .toLowerCase();
        return hay.includes(q);
      });
    }
    const sorted = [...rows].sort((a, b) => {
      const av = a[sortKey];
      const bv = b[sortKey];
      if (av == null && bv == null) return 0;
      if (av == null) return 1;
      if (bv == null) return -1;
      if (typeof av === 'number' && typeof bv === 'number') return (av - bv) * sortDir;
      return String(av).localeCompare(String(bv)) * sortDir;
    });
    return sorted;
  }, [wines, search, statusFilter, sortKey, sortDir]);

  const toggleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortDir((d) => (d === 1 ? -1 : 1));
    } else {
      setSortKey(key);
      setSortDir(1);
    }
  };

  const headerCell = (key: SortKey, label: string) => (
    <th
      className="cursor-pointer select-none px-3 py-2 text-left font-semibold text-muted hover:text-ink"
      onClick={() => toggleSort(key)}
    >
      {label} {sortKey === key ? (sortDir === 1 ? '▲' : '▼') : ''}
    </th>
  );

  return (
    <div>
      <div className="mb-3 flex flex-wrap items-center gap-2">
        <input
          type="text"
          placeholder="Search name, brand, country, region, grape…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="min-w-[220px] flex-1 rounded-md border border-parchment bg-white px-3 py-1.5 text-sm focus:border-wine focus:outline-none"
        />
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="rounded-md border border-parchment bg-white px-2 py-1.5 text-sm focus:border-wine focus:outline-none"
        >
          <option value="all">All statuses</option>
          <option value="auto">Auto</option>
          <option value="needs_review">Needs review</option>
          <option value="manual">Manual</option>
          <option value="pending">Pending</option>
        </select>
        <span className="text-xs text-muted">{filtered.length} wines</span>
      </div>

      <div className="overflow-x-auto rounded-md border border-parchment bg-white">
        <table className="w-full min-w-[720px] text-sm">
          <thead className="border-b border-parchment bg-parchment/40">
            <tr>
              {headerCell('name', 'Name')}
              {headerCell('category', 'Category')}
              {showDevColumns && headerCell('brand', 'Brand')}
              {headerCell('country', 'Country')}
              <th className="px-3 py-2 text-left font-semibold text-muted">Region</th>
              <th className="px-3 py-2 text-left font-semibold text-muted">Grapes</th>
              {headerCell('confidence', 'Confidence')}
              {headerCell('tag_status', 'Status')}
              {showDevColumns && <th className="px-3 py-2 text-left font-semibold text-muted">Phases</th>}
            </tr>
          </thead>
          <tbody>
            {filtered.map((w) => (
              <tr
                key={w.id}
                onClick={() => onSelect(w)}
                className="cursor-pointer border-b border-parchment/70 last:border-0 hover:bg-wine-light/30"
              >
                <td className="px-3 py-2 font-medium text-ink">{w.name}</td>
                <td className="px-3 py-2 text-muted">{w.category ?? '—'}</td>
                {showDevColumns && <td className="px-3 py-2 text-muted">{w.brand ?? '—'}</td>}
                <td className="px-3 py-2 text-muted">{w.country ?? '—'}</td>
                <td className="px-3 py-2">
                  <div className="flex flex-wrap gap-1">
                    {(w.region ?? []).length > 0
                      ? w.region.map((r) => (
                          <Badge key={r} tone="neutral">
                            {r}
                          </Badge>
                        ))
                      : <span className="text-muted">—</span>}
                  </div>
                </td>
                <td className="px-3 py-2">
                  <div className="flex flex-wrap gap-1">
                    {(w.grapes ?? []).length > 0
                      ? w.grapes.map((g) => (
                          <Badge key={g} tone="wine">
                            {g}
                          </Badge>
                        ))
                      : <span className="text-muted">—</span>}
                  </div>
                </td>
                <td className="px-3 py-2 text-muted">
                  {w.confidence != null ? w.confidence.toFixed(2) : '—'}
                </td>
                <td className="px-3 py-2">
                  <StatusBadge status={w.tag_status} />
                </td>
                {showDevColumns && (
                  <td className="px-3 py-2">
                    <div className="flex gap-1">
                      <PhaseDot label="search" value={w.phase_status?.search} />
                      <PhaseDot label="score" value={w.phase_status?.score} />
                      <PhaseDot label="tag" value={w.phase_status?.tag} />
                    </div>
                  </td>
                )}
              </tr>
            ))}
            {filtered.length === 0 && (
              <tr>
                <td colSpan={showDevColumns ? 9 : 7} className="px-3 py-6 text-center text-muted">
                  No wines match.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
