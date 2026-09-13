import { Check } from 'lucide-react';
import { Photo } from '../shared/Photo';
import { Rating } from '../shared/States';
import { formatDate, formatMinutes, formatMoney } from '../../lib/format';
import type { TripHotel } from '../../lib/trip-model';

interface HotelRowProps {
  hotel: TripHotel;
  selected?: boolean;
  onToggle?: () => void;
  recommended?: boolean;
  /** Expanded layout for the itinerary's Stay tab. */
  detailed?: boolean;
}

/** Only fields the provider returned are rendered. */
export function HotelRow({ hotel, selected, onToggle, recommended, detailed }: HotelRowProps) {
  const perNight = formatMoney(hotel.pricePerNight, hotel.currency);
  const total = formatMoney(hotel.totalPrice, hotel.currency);
  const commute = formatMinutes(hotel.commuteMinutes);
  const stay = hotel.checkIn && hotel.checkOut ? `${formatDate(hotel.checkIn)} – ${formatDate(hotel.checkOut)}` : null;
  const meta = [hotel.address, commute ? `~${commute} to your stops` : null, recommended ? 'Best fit' : null]
    .filter(Boolean)
    .join(' · ');

  const inner = (
    <>
      {onToggle && (
        <span
          className={`flex h-4 w-4 shrink-0 items-center justify-center rounded-full border ${
            selected ? 'border-ink bg-ink text-paper' : 'border-rule-2 bg-paper'
          }`}
          aria-hidden="true"
        >
          {selected && <Check className="h-3 w-3" />}
        </span>
      )}
      <Photo src={hotel.photo} alt="" className={detailed ? 'h-16 w-24' : 'h-10 w-10'} />
      <span className="min-w-0 flex-1">
        <span className="flex items-baseline gap-2">
          <span className="truncate text-[14px] font-medium text-ink">{hotel.name}</span>
          <Rating value={hotel.rating} count={detailed ? hotel.reviewCount : undefined} className="shrink-0" />
        </span>
        {meta && <span className="line-clamp-1 text-[13px] text-muted">{meta}</span>}
        {detailed && (
          <span className="mt-1 block space-y-0.5 text-[12px] text-muted">
            {stay && <span className="block">{stay}</span>}
            {hotel.amenities.length > 0 && <span className="block">{hotel.amenities.slice(0, 6).join(' · ')}</span>}
            {hotel.cancellation && <span className="block text-positive">{hotel.cancellation}</span>}
            {hotel.description && <span className="line-clamp-2 block">{hotel.description}</span>}
          </span>
        )}
      </span>
      {(perNight || total) && (
        <span className="shrink-0 text-right">
          {perNight && (
            <span className="block text-[14px] font-medium text-ink">
              {perNight}
              <span className="text-subtle"> /night</span>
            </span>
          )}
          {total && <span className="block text-[12px] text-subtle">{total} total</span>}
        </span>
      )}
    </>
  );

  if (onToggle) {
    return (
      <button
        type="button"
        role="radio"
        aria-checked={selected}
        onClick={onToggle}
        className={`row row-hover w-full text-left ${selected ? 'row-selected' : ''}`}
      >
        {inner}
      </button>
    );
  }
  return <div className={`row ${detailed ? 'items-start' : ''}`}>{inner}</div>;
}
