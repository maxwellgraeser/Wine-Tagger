import { useEffect, useState } from 'react';
import { X } from 'lucide-react';
import { api, type GrapeEntry, type RegionEntry, type Wine, type WinePatch } from '../api';

function ChipInput({
  values,
  onChange,
  datalistId,
  options,
  placeholder,
}: {
  values: string[];
  onChange: (values: string[]) => void;
  datalistId: string;
  options: string[];
  placeholder: string;
}) {
  const [draft, setDraft] = useState('');

  const add = () => {
    const v = draft.trim();
    if (v && !values.includes(v)) {
      onChange([...values, v]);
    }
    setDraft('');
  };

  return (
    <div>
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
        list={datalistId}
        value={draft}
        onChange={(e) => setDraft(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ',') {
            e.preventDefault();
            add();
          }
        }}
        onBlur={add}
        placeholder={placeholder}
        className="w-full rounded-md border border-parchment bg-white px-2 py-1 text-sm focus:border-wine focus:outline-none"
      />
      <datalist id={datalistId}>
        {options.map((o) => (
          <option key={o} value={o} />
        ))}
      </datalist>
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
        <input
          list="tag-editor-countries"
          value={country}
          onChange={(e) => setCountry(e.target.value)}
          className="w-full rounded-md border border-parchment bg-white px-2 py-1 text-sm focus:border-wine focus:outline-none"
        />
        <datalist id="tag-editor-countries">
          {countries.map((c) => (
            <option key={c} value={c} />
          ))}
        </datalist>
      </div>

      <div>
        <label className="mb-1 block text-xs font-medium text-muted">Region</label>
        <ChipInput
          values={region}
          onChange={setRegion}
          datalistId="tag-editor-regions"
          options={regions.map((r) => r.name)}
          placeholder="Add region and press Enter"
        />
      </div>

      <div>
        <label className="mb-1 block text-xs font-medium text-muted">Grapes</label>
        <ChipInput
          values={grapes}
          onChange={setGrapes}
          datalistId="tag-editor-grapes"
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
            step="0.01"
            min={0}
            max={1}
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
        {saving ? 'Saving…' : 'Save (marks manual)'}
      </button>
    </div>
  );
}
