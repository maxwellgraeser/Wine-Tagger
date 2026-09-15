import { useEffect, useRef, useState } from 'react';
import { X } from 'lucide-react';
import { api, type GrapeEntry, type RegionEntry, type Wine, type WinePatch } from '../api';

const MAX_SUGGESTIONS = 12;

function filterOptions(options: string[], draft: string): string[] {
  const q = draft.trim().toLowerCase();
  const pool = q ? options.filter((o) => o.toLowerCase().includes(q)) : options;
  return pool.slice(0, MAX_SUGGESTIONS);
}

/**
 * Shared dropdown panel used by both the Country input and ChipInput.
 * Renders below its (relatively positioned) parent input.
 */
function SuggestionPanel({
  options,
  highlightedIndex,
  onSelect,
}: {
  options: string[];
  highlightedIndex: number;
  onSelect: (value: string) => void;
}) {
  return (
    <div className="absolute z-20 mt-1 max-h-56 w-full overflow-y-auto rounded-md border border-parchment bg-white text-sm text-ink shadow-lg">
      {options.length === 0 ? (
        <div className="px-2 py-1 text-muted">No matches</div>
      ) : (
        options.map((o, i) => (
          <div
            key={o}
            onMouseDown={(e) => {
              e.preventDefault();
              onSelect(o);
            }}
            className={`cursor-pointer px-2 py-1 hover:bg-wine-light/50 ${
              i === highlightedIndex ? 'bg-wine-light' : ''
            }`}
          >
            {o}
          </div>
        ))
      )}
    </div>
  );
}

/**
 * Hook encapsulating the open/highlight/keyboard-nav state shared by the
 * Country combobox and ChipInput's suggestion dropdown.
 */
function useCombobox(options: string[], draft: string) {
  const [open, setOpen] = useState(false);
  const [highlightedIndex, setHighlightedIndex] = useState(-1);
  const filtered = filterOptions(options, draft);

  // Opens the panel and clears any stale highlight (e.g. from typing or focusing).
  const openWithReset = () => {
    setOpen(true);
    setHighlightedIndex(-1);
  };

  const onKeyDown = (
    e: React.KeyboardEvent<HTMLInputElement>,
    onCommit: (value: string) => void,
  ): boolean => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setOpen(true);
      setHighlightedIndex((i) => (filtered.length === 0 ? -1 : (i + 1) % filtered.length));
      return true;
    }
    if (e.key === 'ArrowUp') {
      e.preventDefault();
      setOpen(true);
      setHighlightedIndex((i) =>
        filtered.length === 0 ? -1 : (i - 1 + filtered.length) % filtered.length,
      );
      return true;
    }
    if (e.key === 'Escape') {
      setOpen(false);
      return true;
    }
    if (e.key === 'Enter') {
      if (open && highlightedIndex >= 0 && highlightedIndex < filtered.length) {
        e.preventDefault();
        onCommit(filtered[highlightedIndex]);
        setOpen(false);
        return true;
      }
    }
    return false;
  };

  return { open, setOpen, openWithReset, highlightedIndex, filtered, onKeyDown };
}

function ChipInput({
  values,
  onChange,
  id,
  options,
  placeholder,
}: {
  values: string[];
  onChange: (values: string[]) => void;
  id?: string;
  options: string[];
  placeholder: string;
}) {
  const [draft, setDraft] = useState('');
  const { open, setOpen, openWithReset, highlightedIndex, filtered, onKeyDown } = useCombobox(options, draft);

  const addValue = (v: string) => {
    const trimmed = v.trim();
    if (trimmed && !values.includes(trimmed)) {
      onChange([...values, trimmed]);
    }
    setDraft('');
  };

  const add = () => addValue(draft);

  return (
    <div className="relative">
      <div className="mb-1 flex flex-wrap gap-1">
        {values.map((v) => (
          <span
            key={v}
            className="flex items-center gap-1 rounded-full bg-wine-light px-2 py-0.5 text-xs text-wine-dark"
          >
            {v}
            <button
              type="button"
              onClick={() => onChange(values.filter((x) => x !== v))}
              className="hover:text-wine"
            >
              <X className="h-3 w-3" />
            </button>
          </span>
        ))}
      </div>
      <input
        id={id}
        value={draft}
        onChange={(e) => {
          setDraft(e.target.value);
          openWithReset();
        }}
        onFocus={openWithReset}
        onKeyDown={(e) => {
          const handled = onKeyDown(e, (value) => addValue(value));
          if (handled) return;
          if (e.key === 'Enter' || e.key === ',') {
            e.preventDefault();
            add();
            setOpen(false);
          }
        }}
        onBlur={() => {
          add();
          setOpen(false);
        }}
        placeholder={placeholder}
        autoComplete="off"
        className="w-full rounded-md border border-parchment bg-white px-2 py-1 text-sm focus:border-wine focus:outline-none"
      />
      {open && (
        <SuggestionPanel
          options={filtered}
          highlightedIndex={highlightedIndex}
          onSelect={(value) => {
            addValue(value);
            setOpen(false);
          }}
        />
      )}
    </div>
  );
}

function CountryCombobox({
  value,
  onChange,
  options,
}: {
  value: string;
  onChange: (value: string) => void;
  options: string[];
}) {
  const { open, setOpen, openWithReset, highlightedIndex, filtered, onKeyDown } = useCombobox(options, value);
  const inputRef = useRef<HTMLInputElement>(null);

  return (
    <div className="relative">
      <input
        ref={inputRef}
        value={value}
        onChange={(e) => {
          onChange(e.target.value);
          openWithReset();
        }}
        onFocus={openWithReset}
        onKeyDown={(e) => {
          const handled = onKeyDown(e, (v) => onChange(v));
          if (handled) return;
          if (e.key === 'Enter') {
            setOpen(false);
          }
        }}
        onBlur={() => setOpen(false)}
        autoComplete="off"
        className="w-full rounded-md border border-parchment bg-white px-2 py-1 text-sm focus:border-wine focus:outline-none"
      />
      {open && (
        <SuggestionPanel
          options={filtered}
          highlightedIndex={highlightedIndex}
          onSelect={(v) => {
            onChange(v);
            setOpen(false);
          }}
        />
      )}
    </div>
  );
}

export function TagEditor({ wine, onSaved }: { wine: Wine; onSaved: (w: Wine) => void }) {
  const [country, setCountry] = useState(wine.country ?? '');
  const [region, setRegion] = useState<string[]>(wine.region ?? []);
  const [grapes, setGrapes] = useState<string[]>(wine.grapes ?? []);
  const [isBlend, setIsBlend] = useState<boolean | null>(wine.is_blend ?? null);
  const [organic, setOrganic] = useState(wine.organic ?? false);
  const [confidence, setConfidence] = useState<number | ''>(wine.confidence ?? '');

  const [countries, setCountries] = useState<string[]>([]);
  const [regions, setRegions] = useState<RegionEntry[]>([]);
  const [grapeOptions, setGrapeOptions] = useState<GrapeEntry[]>([]);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setCountry(wine.country ?? '');
    setRegion(wine.region ?? []);
    setGrapes(wine.grapes ?? []);
    setIsBlend(wine.is_blend ?? null);
    setOrganic(wine.organic ?? false);
    setConfidence(wine.confidence ?? '');
  }, [wine]);

  useEffect(() => {
    api.getCountries().then(setCountries).catch(() => setCountries([]));
    api.getGrapes().then(setGrapeOptions).catch(() => setGrapeOptions([]));
  }, []);

  useEffect(() => {
    api
      .getRegions(country || undefined)
      .then(setRegions)
      .catch(() => setRegions([]));
  }, [country]);

  const save = async () => {
    setSaving(true);
    setError(null);
    try {
      const patch: WinePatch = {
        country: country || null,
        region,
        grapes,
        is_blend: isBlend,
        organic,
        confidence: confidence === '' ? null : Number(confidence),
      };
      const updated = await api.patchWine(wine.id, patch);
      onSaved(updated);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to save');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-4">
      <div>
        <label className="mb-1 block text-xs font-medium text-muted">Country</label>
        <CountryCombobox value={country} onChange={setCountry} options={countries} />
      </div>

      <div>
        <label className="mb-1 block text-xs font-medium text-muted">Region</label>
        <ChipInput
          values={region}
          onChange={setRegion}
          id="tag-editor-regions"
          options={regions.map((r) => r.name)}
          placeholder="Add region and press Enter"
        />
      </div>

      <div>
        <label className="mb-1 block text-xs font-medium text-muted">Grapes</label>
        <ChipInput
          values={grapes}
          onChange={setGrapes}
          id="tag-editor-grapes"
          options={grapeOptions.map((g) => g.name)}
          placeholder="Add grape and press Enter"
        />
      </div>

      <div className="flex flex-wrap items-center gap-4">
        <div>
          <label className="mb-1 block text-xs font-medium text-muted">Is blend</label>
          <select
            value={isBlend === null ? 'unknown' : isBlend ? 'yes' : 'no'}
            onChange={(e) =>
              setIsBlend(e.target.value === 'unknown' ? null : e.target.value === 'yes')
            }
            className="rounded-md border border-parchment bg-white px-2 py-1 text-sm focus:border-wine focus:outline-none"
          >
            <option value="unknown">Unknown</option>
            <option value="yes">Yes</option>
            <option value="no">No</option>
          </select>
        </div>

        <label className="flex items-center gap-1.5 text-sm">
          <input
            type="checkbox"
            checked={organic}
            onChange={(e) => setOrganic(e.target.checked)}
            className="accent-wine"
          />
          Organic
        </label>

        <div>
          <label className="mb-1 block text-xs font-medium text-muted">Confidence</label>
          <input
            type="number"
            step={1}
            min={0}
            max={100}
            value={confidence}
            onChange={(e) => setConfidence(e.target.value === '' ? '' : Number(e.target.value))}
            className="w-24 rounded-md border border-parchment bg-white px-2 py-1 text-sm focus:border-wine focus:outline-none"
          />
        </div>
      </div>

      {wine.tags_raw && (
        <div>
          <label className="mb-1 block text-xs font-medium text-muted">Tags raw (preview)</label>
          <pre className="max-h-32 overflow-auto rounded-md border border-parchment bg-ink/5 p-2 text-xs">
            {wine.tags_raw}
          </pre>
        </div>
      )}

      {error && <div className="rounded-md bg-red-100 px-2 py-1 text-xs text-red-800">{error}</div>}

      <button
        type="button"
        onClick={save}
        disabled={saving}
        className="w-full rounded-md bg-wine px-3 py-2 text-sm font-medium text-white hover:bg-wine-dark disabled:opacity-50"
      >
        {saving ? 'Saving…' : 'Save (marks human)'}
      </button>
    </div>
  );
}
