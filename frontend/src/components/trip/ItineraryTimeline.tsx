import { useEffect, useRef, useState } from 'react';
import { ExternalLink } from 'lucide-react';
import { Photo } from '../shared/Photo';
import { Rating } from '../shared/States';
import { Note } from '../shared/Agent';
import { formatMinutes, priceLevelLabel } from '../../lib/format';
import { STOP_KIND_LABEL, type StopKind, type TripDay, type TripLeg, type TripStop } from '../../lib/trip-model';

const TONE: Record<StopKind, string> = { stay: 'stay', eat: 'eat', poi: 'sight', act: 'act', shop: 'shop', well: 'well', fun: 'fun', night: 'fun', other: 'other' };

interface ItineraryTimelineProps {
  day: TripDay;
  activeStopId: string | null;
  onSelectStop: (id: string | null) => void;
  removedIds: Set<string>;
  onRemove: (id: string) => void;
  onRestore: (id: string) => void;
}

/**
 * One list for the day. Stops are rows; travel legs are thin rows between
 * them. A stop with no scheduled time shows its sequence number — never an
 * invented clock time.
 */
export function ItineraryTimeline({ day, activeStopId, onSelectStop, removedIds, onRemove, onRestore }: ItineraryTimelineProps) {
  if (!day.stops.length) {
    return (
      <div className="rounded-md border border-dashed border-rule-2 px-4 py-8 text-center">
        <p className="text-[14px] font-medium text-ink">No route for this day.</p>
        <p className="mt-1 text-[13px] text-muted">Go back and choose a few more places, or remove one that is far from the rest.</p>
      </div>
    );
  }

  return (
    <ol className="list">
      {day.stops.map((stop, i) => {
        const leg = i < day.stops.length - 1 ? day.legs[i] ?? null : null;
        return (
          <li key={stop.id} className="!border-t-0">
            <StopItem
              stop={stop}
              active={stop.id === activeStopId}
              removed={removedIds.has(stop.id)}
              onSelect={() => onSelectStop(stop.id === activeStopId ? null : stop.id)}
              onRemove={() => onRemove(stop.id)}
              onRestore={() => onRestore(stop.id)}
              first={i === 0}
            />
            {leg && <TravelSegment leg={leg} />}
          </li>
        );
      })}
    </ol>
  );
}

function StopItem({
  stop,
  active,
  removed,
  onSelect,
  onRemove,
  onRestore,
  first,
}: {
  stop: TripStop;
  active: boolean;
  removed: boolean;
  onSelect: () => void;
  onRemove: () => void;
  onRestore: () => void;
  first: boolean;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const [showHours, setShowHours] = useState(false);

  useEffect(() => {
    if (active) ref.current?.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
  }, [active]);

  const kind = STOP_KIND_LABEL[stop.kind] !== 'Stop' ? STOP_KIND_LABEL[stop.kind] : null;
  const category = stop.category && !['Attraction', 'Place', 'Stay'].includes(stop.category) ? stop.category : null;
  const tag = category ?? kind;
  const meta = [stop.time, priceLevelLabel(stop.priceLevel), formatMinutes(stop.durationMinutes), stop.address]
    .filter(Boolean)
    .join(' · ');

  return (
    <div ref={ref} className={`${first ? '' : 'border-t border-rule'} ${active ? 'bg-accent-soft' : ''} ${removed ? 'opacity-50' : ''}`}>
      <button type="button" onClick={onSelect} aria-expanded={active} className="row row-hover w-full text-left">
        <span
          className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-[11px] font-semibold ${
            active ? 'bg-accent text-paper' : 'bg-ink text-paper'
          }`}
        >
          {stop.index}
        </span>
        <span className="min-w-0 flex-1">
          <span className="flex items-center gap-2">
            <span className={`truncate text-[14px] font-medium ${removed ? 'text-muted line-through' : 'text-ink'}`}>{stop.name}</span>
            {tag && <span className={`cat cat-${TONE[stop.kind]}`}>{tag}</span>}
          </span>
          {meta && <span className="line-clamp-1 text-[13px] text-muted">{meta}</span>}
        </span>
        <Rating value={stop.rating} className="shrink-0" />
        {stop.photo && <Photo src={stop.photo} alt="" />}
      </button>

      {active && (
        <div className="px-3 pb-3 pl-11 text-[13px]">
          {stop.description && <p className="text-ink">{stop.description}</p>}
          {stop.reason && (
            <Note lead="Why this stop" className="mt-2">
              {stop.reason}
            </Note>
          )}
          {showHours && stop.openingHours && (
            <ul className="mt-2 text-[12px] text-muted">
              {stop.openingHours.map((h) => (
                <li key={h}>{h}</li>
              ))}
            </ul>
          )}
          <div className="mt-3 flex flex-wrap items-center gap-1">
            {stop.website && (
              <a href={stop.website} target="_blank" rel="noreferrer" className="btn btn-secondary no-underline">
                Website
                <ExternalLink className="h-3 w-3" />
              </a>
            )}
            {stop.openingHours && (
              <button type="button" onClick={() => setShowHours((v) => !v)} className="btn btn-secondary" aria-expanded={showHours}>
                {showHours ? 'Hide hours' : 'Opening hours'}
              </button>
            )}
            {removed ? (
              <button type="button" onClick={onRestore} className="btn btn-ghost ml-auto">
                Put back
              </button>
            ) : (
              <button type="button" onClick={onRemove} className="btn btn-ghost ml-auto">
                Remove from day
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function TravelSegment({ leg }: { leg: TripLeg }) {
  const parts = [leg.duration, leg.modeLabel, leg.distance].filter(Boolean);
  if (!parts.length) return null;
  return (
    <div className="flex items-center gap-3 border-t border-rule bg-paper px-3 py-2 text-[12px] text-subtle" aria-label={`Travel: ${parts.join(', ')}`}>
      <span className="flex w-5 justify-center" aria-hidden="true">
        <span className="h-3 w-px bg-rule-2" />
      </span>
      <span>
        {leg.duration && <span className="font-medium text-muted">{leg.duration} </span>}
        {leg.modeLabel}
        {leg.distance && <span> · {leg.distance}</span>}
      </span>
    </div>
  );
}
