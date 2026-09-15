export function ProgressBar({
  value,
  total,
  label,
}: {
  value: number;
  total: number;
  label?: string;
}) {
  const pct = total > 0 ? Math.min(100, Math.round((value / total) * 100)) : 0;
  return (
    <div className="w-full">
      {label && (
        <div className="mb-1 flex items-center justify-between text-xs text-muted">
          <span>{label}</span>
          <span>
            {value} / {total} ({pct}%)
          </span>
        </div>
      )}
      <div className="h-2.5 w-full overflow-hidden rounded-full bg-parchment">
        <div
          className="h-full rounded-full bg-wine transition-all duration-300"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}
