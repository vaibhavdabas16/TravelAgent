import { Check } from 'lucide-react';
import { formatDate, formatMinutes, formatMoney, formatTime } from '../../lib/format';
import type { TripFlight } from '../../lib/trip-model';

interface FlightRowProps {
  flight: TripFlight;
  selected?: boolean;
  onToggle?: () => void;
  recommended?: boolean;
}

/** DEL 08:40 → KIX 20:15 · 12 Oct · 7 h 35 min · 1 stop via HND · ANA NH828 · $520 */
export function FlightRow({ flight, selected, onToggle, recommended }: FlightRowProps) {
  const dep = formatTime(flight.departure);
  const arr = formatTime(flight.arrival);
  const date = formatDate(flight.departure);
  const duration = formatMinutes(flight.durationMinutes);
  const price = formatMoney(flight.price, flight.currency);
  const stops =
    flight.stops === null ? null : flight.stops === 0 ? 'Direct' : `${flight.stops} stop${flight.stops === 1 ? '' : 's'}`;
  const via = flight.layovers.length ? `via ${flight.layovers.join(', ')}` : null;
  const carrier = flight.airline && flight.flightNumber ? `${flight.airline} ${flight.flightNumber}` : flight.airline;
  const meta = [date, duration, stops && via ? `${stops} ${via}` : stops, carrier, flight.cabin, recommended ? 'Best value' : null]
    .filter(Boolean)
    .join(' · ');

  const inner = (
    <>
      {onToggle && (
        <span
          className={`flex h-4 w-4 shrink-0 items-center justify-center rounded-[3px] border ${
            selected ? 'border-ink bg-ink text-paper' : 'border-rule-2 bg-paper'
          }`}
          aria-hidden="true"
        >
          {selected && <Check className="h-3 w-3" />}
        </span>
      )}
      <span className="min-w-0 flex-1">
        <span className="flex items-baseline gap-2 text-[14px] text-ink">
          <span className="font-medium">{flight.origin ?? '—'}</span>
          {dep && <span className="text-muted">{dep}</span>}
          <span className="text-subtle">→</span>
          <span className="font-medium">{flight.destination ?? '—'}</span>
          {arr && <span className="text-muted">{arr}</span>}
        </span>
        {meta && <span className="line-clamp-1 text-[13px] text-muted">{meta}</span>}
      </span>
      {price && <span className="shrink-0 text-[14px] font-medium text-ink">{price}</span>}
    </>
  );

  if (onToggle) {
    return (
      <button
        type="button"
        role="checkbox"
        aria-checked={selected}
        onClick={onToggle}
        className={`row row-hover w-full text-left ${selected ? 'row-selected' : ''}`}
      >
        {inner}
      </button>
    );
  }
  return <div className="row">{inner}</div>;
}
