import { useMemo, useState } from 'react';
import { ArrowRight, Check, Minus, Plus, X } from 'lucide-react';
import {
  AMENITY_OPTIONS,
  TRAVEL_STYLES,
  parseTripQuery,
  toStartRequest,
  type BudgetTier,
  type Pace,
  type ParsedTrip,
} from '../../lib/trip-parser';

interface TripBriefProps {
  query: string;
  onChangeQuery: (q: string) => void;
  onContinue: (request: ReturnType<typeof toStartRequest>, parsed: ParsedTrip) => void;
  busy: boolean;
}

const BUDGETS: { id: BudgetTier; title: string }[] = [
  { id: 'budget', title: 'Budget' },
  { id: 'moderate', title: 'Mid-range' },
  { id: 'luxury', title: 'Luxury' },
];

const PACES: { id: Pace; title: string }[] = [
  { id: 'relaxed', title: 'Relaxed' },
  { id: 'balanced', title: 'Balanced' },
  { id: 'packed', title: 'Packed' },
];

/**
 * "Here's what we understood." Everything the parser pulled from the
 * sentence, as a compact editable form. Fields the sentence answered arrive
 * filled in; nothing is asked twice.
 */
export function TripBrief({ query, onChangeQuery, onContinue, busy }: TripBriefProps) {
  const parsed = useMemo(() => parseTripQuery(query), [query]);
  const [edits, setEdits] = useState<Partial<ParsedTrip>>({});
  const [editingPrompt, setEditingPrompt] = useState(false);
  const [draft, setDraft] = useState(query);

  const trip: ParsedTrip = { ...parsed, ...edits };
  const set = <K extends keyof ParsedTrip>(key: K, value: ParsedTrip[K]) => setEdits((e) => ({ ...e, [key]: value }));

  const toggleStyle = (id: string) => {
    const next = trip.styles.includes(id) ? trip.styles.filter((s) => s !== id) : [...trip.styles, id];
    const interests = Array.from(new Set(next.flatMap((sid) => TRAVEL_STYLES.find((s) => s.id === sid)?.interests ?? [])));
    setEdits((e) => ({ ...e, styles: next, interests }));
  };
  const toggleAmenity = (a: string) =>
    set('amenities', trip.amenities.includes(a) ? trip.amenities.filter((x) => x !== a) : [...trip.amenities, a]);

  const canContinue = Boolean(trip.destination && trip.destination.trim().length > 1);

  const understood = (() => {
    const when =
      trip.startDate && trip.endDate
        ? `${trip.startDate} to ${trip.endDate}`
        : trip.nights
          ? `${trip.nights} nights${trip.month ? ` in ${trip.month}` : ''}`
          : trip.month
            ? `in ${trip.month}`
            : null;
    const bits = [
      trip.destination ?? 'no destination yet',
      when,
      trip.travelers ? `${trip.travelers} ${trip.travelers === 1 ? 'traveler' : 'travelers'}` : null,
      trip.origin ? `flying from ${trip.origin}` : null,
      trip.styles.length ? TRAVEL_STYLES.filter((t) => trip.styles.includes(t.id)).map((t) => t.title.toLowerCase()).join(' + ') : null,
      trip.budget ? `${BUDGETS.find((b) => b.id === trip.budget)?.title.toLowerCase()} budget` : null,
    ].filter(Boolean);
    return bits.join(' · ') + '.';
  })();

  const applyPrompt = () => {
    const q = draft.trim();
    setEditingPrompt(false);
    if (q && q !== query) {
      setEdits({});
      onChangeQuery(q);
    }
  };

  return (
    <div className="mx-auto max-w-2xl">
      {/* The sentence */}
      <div className="rounded-md border border-rule bg-paper px-3 py-3">
        {editingPrompt ? (
          <div>
            <textarea
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              rows={2}
              autoFocus
              className="block w-full resize-none bg-transparent text-[14px] focus:outline-none"
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  applyPrompt();
                }
              }}
            />
            <div className="mt-2 flex gap-1">
              <button className="btn btn-primary" onClick={applyPrompt}>
                Update
              </button>
              <button
                className="btn btn-ghost"
                onClick={() => {
                  setDraft(query);
                  setEditingPrompt(false);
                }}
              >
                Cancel
              </button>
            </div>
          </div>
        ) : (
          <div className="flex items-start justify-between gap-3">
            <p className="text-[14px] text-ink">{query}</p>
            <button className="btn btn-ghost -my-1 -mr-1 shrink-0" onClick={() => setEditingPrompt(true)}>
              Edit
            </button>
          </div>
        )}
      </div>

      <h1 className="lc mt-8 text-[length:var(--text-xl)]">Check the details</h1>
      <p className="mt-1 text-[13px] text-muted">From your sentence: {understood} Fix anything that&rsquo;s off; only the destination is required.</p>

      <div className="mt-6 divide-y divide-rule border-y border-rule">
        <Section label="Where">
          <div className="grid gap-3 sm:grid-cols-2">
            <Field label="Destination" required>
              <input
                className="field"
                aria-label="Destination"
                value={trip.destination ?? ''}
                placeholder="Kyoto, Lisbon, Bali…"
                onChange={(e) => set('destination', e.target.value || null)}
              />
            </Field>
            <Field label="Flying from" hint="Optional, for flights">
              <input
                className="field"
                aria-label="Flying from"
                value={trip.origin ?? ''}
                placeholder="Delhi, London…"
                onChange={(e) => set('origin', e.target.value || null)}
              />
            </Field>
          </div>
        </Section>

        <Section label="When">
          <div className="grid gap-3 sm:grid-cols-3">
            <Field label="From" hint={trip.month && !trip.startDate ? `Sometime in ${trip.month}` : undefined}>
              <input
                type="date"
                className="field"
                aria-label="Start date"
                value={trip.startDate ?? ''}
                onChange={(e) => set('startDate', e.target.value || null)}
              />
            </Field>
            <Field label="To">
              <input
                type="date"
                className="field"
                aria-label="End date"
                min={trip.startDate ?? undefined}
                value={trip.endDate ?? ''}
                onChange={(e) => set('endDate', e.target.value || null)}
              />
            </Field>
            <Field label="Travelers">
              <div className="flex h-8 items-center rounded-sm border border-rule-2 bg-paper">
                <button
                  type="button"
                  aria-label="Fewer travelers"
                  className="flex h-full w-8 items-center justify-center text-muted hover:bg-paper-2 disabled:opacity-40"
                  disabled={(trip.travelers ?? 2) <= 1}
                  onClick={() => set('travelers', Math.max(1, (trip.travelers ?? 2) - 1))}
                >
                  <Minus className="h-3.5 w-3.5" />
                </button>
                <span className="flex-1 text-center text-[13px] font-medium">{trip.travelers ?? 2}</span>
                <button
                  type="button"
                  aria-label="More travelers"
                  className="flex h-full w-8 items-center justify-center text-muted hover:bg-paper-2"
                  onClick={() => set('travelers', Math.min(20, (trip.travelers ?? 2) + 1))}
                >
                  <Plus className="h-3.5 w-3.5" />
                </button>
              </div>
            </Field>
          </div>
        </Section>

        <Section label="Style" hint="Shapes which places we look for.">
          <Chips
            options={TRAVEL_STYLES.map((s) => ({ id: s.id, label: s.title, title: s.description }))}
            selected={trip.styles}
            onToggle={toggleStyle}
          />
        </Section>

        <Section label="Budget">
          <Chips
            options={BUDGETS.map((b) => ({ id: b.id, label: b.title }))}
            selected={[trip.budget ?? 'moderate']}
            onToggle={(id) => set('budget', id as BudgetTier)}
          />
        </Section>

        <Section label="Pace">
          <Chips
            options={PACES.map((p) => ({ id: p.id, label: p.title }))}
            selected={[trip.pace ?? 'balanced']}
            onToggle={(id) => set('pace', id as Pace)}
          />
        </Section>

        <Section label="Stay must-haves">
          <Chips
            options={[
              ...AMENITY_OPTIONS.map((a) => ({ id: a, label: a })),
              ...trip.amenities.filter((a) => !AMENITY_OPTIONS.includes(a)).map((a) => ({ id: a, label: a, removable: true })),
            ]}
            selected={trip.amenities}
            onToggle={toggleAmenity}
          />
        </Section>
      </div>

      <div className="mt-6 flex items-center justify-between gap-4">
        <p className="text-[12px] text-subtle">Next: places worth visiting in {trip.destination || 'your destination'}.</p>
        <button
          type="button"
          disabled={!canContinue || busy}
          onClick={() => onContinue(toStartRequest(trip), trip)}
          className="btn btn-primary btn-lg"
        >
          {busy ? 'Starting…' : 'Continue'}
          {!busy && <ArrowRight className="h-3.5 w-3.5" />}
        </button>
      </div>
    </div>
  );
}

function Section({ label, hint, children }: { label: string; hint?: string; children: React.ReactNode }) {
  return (
    <section className="grid gap-2 py-4 sm:grid-cols-[120px_1fr] sm:gap-6">
      <div>
        <p className="text-[13px] font-medium text-ink">{label}</p>
        {hint && <p className="text-[12px] text-subtle">{hint}</p>}
      </div>
      <div>{children}</div>
    </section>
  );
}

function Field({
  label,
  hint,
  required,
  children,
}: {
  label: string;
  hint?: string;
  required?: boolean;
  children: React.ReactNode;
}) {
  return (
    <div>
      <span className="mb-1 block text-[12px] text-muted">
        {label}
        {required && <span className="text-critical"> *</span>}
      </span>
      {children}
      {hint && <span className="mt-1 block text-[11px] text-subtle">{hint}</span>}
    </div>
  );
}

function Chips({
  options,
  selected,
  onToggle,
}: {
  options: { id: string; label: string; title?: string; removable?: boolean }[];
  selected: string[];
  onToggle: (id: string) => void;
}) {
  return (
    <div className="flex flex-wrap gap-2">
      {options.map((o) => {
        const on = selected.includes(o.id);
        return (
          <button
            key={o.id}
            type="button"
            title={o.title}
            aria-pressed={on}
            onClick={() => onToggle(o.id)}
            className={`chip ${on ? 'chip-selected' : ''}`}
          >
            {on && !o.removable && <Check className="h-3 w-3" />}
            {o.label}
            {o.removable && <X className="h-3 w-3" />}
          </button>
        );
      })}
    </div>
  );
}
