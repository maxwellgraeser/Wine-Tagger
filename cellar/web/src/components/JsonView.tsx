import { useState } from 'react';

export function JsonView({ data, label = 'Raw JSON' }: { data: unknown; label?: string }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="mt-2">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="text-xs font-medium text-wine hover:underline"
      >
        {open ? 'Hide' : 'Show'} {label}
      </button>
      {open && (
        <pre className="mt-1 max-h-96 overflow-auto rounded-md border border-parchment bg-ink/5 p-2 text-xs">
          {JSON.stringify(data, null, 2)}
        </pre>
      )}
    </div>
  );
}
