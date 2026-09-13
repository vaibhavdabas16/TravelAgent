import { Check } from 'lucide-react';
import { Photo } from '../shared/Photo';
import { Rating } from '../shared/States';
import { categoryLabel, categoryTone, photoUrl, priceLevelLabel } from '../../lib/format';

export interface PlaceRowData {
  id: string;
  name: string;
  photo: string | null;
  category: string | null;
  rating: number | null;
  reviewCount: number | null;
  priceLevel: string | null;
  address: string | null;
  reason: string | null;
  description: string | null;
  tone: ReturnType<typeof categoryTone>;
}

/** Normalise a POI-shaped record from any of the search endpoints. */
export function toPlaceRow(raw: any): PlaceRowData | null {
  const id = raw?.place_id ?? raw?.id ?? raw?.provider_id;
  if (!id || !raw?.name) return null;
  const rating = typeof raw.rating === 'number' ? raw.rating : parseFloat(raw.rating);
  return {
    id: String(id),
    name: String(raw.name),
    photo: photoUrl(raw),
    category: categoryLabel(raw),
    rating: isFinite(rating) ? rating : null,
    reviewCount: typeof raw.user_ratings_total === 'number' ? raw.user_ratings_total : null,
    priceLevel: priceLevelLabel(raw.price_level),
    address: typeof raw.formatted_address === 'string' ? raw.formatted_address : null,
    tone: categoryTone(raw),
    reason: typeof raw.why_recommended === 'string' ? raw.why_recommended : typeof raw.recommendation_reason === 'string' ? raw.recommendation_reason : null,
    description:
      typeof raw.editorial_summary?.overview === 'string'
        ? raw.editorial_summary.overview
        : typeof raw.editorial_summary === 'string'
          ? raw.editorial_summary
          : null,
  };
}

interface PlaceRowProps {
  place: PlaceRowData;
  selected: boolean;
  recommended?: boolean;
  onToggle: () => void;
}

/** One line per place. Checkbox, thumbnail, name + meta, rating. */
export function PlaceRow({ place, selected, recommended, onToggle }: PlaceRowProps) {
  const meta = [place.priceLevel, place.address].filter(Boolean).join(' · ');
  const blurb = place.description ?? place.reason;
  return (
    <button
      type="button"
      role="checkbox"
      aria-checked={selected}
      onClick={onToggle}
      className={`row row-hover w-full text-left ${selected ? 'row-selected' : ''}`}
    >
      <span
        className={`flex h-4 w-4 shrink-0 items-center justify-center rounded-[3px] border ${
          selected ? 'border-ink bg-ink text-paper' : 'border-rule-2 bg-paper'
        }`}
        aria-hidden="true"
      >
        {selected && <Check className="h-3 w-3" />}
      </span>
      <Photo src={place.photo} alt="" />
      <span className="min-w-0 flex-1">
        <span className="flex items-center gap-2">
          <span className="truncate text-[14px] font-medium text-ink">{place.name}</span>
          {place.category && <span className={`cat cat-${place.tone}`}>{place.category}</span>}
          {recommended && <span className="mono text-accent">top pick</span>}
        </span>
        <span className="line-clamp-1 text-[13px] text-muted">{blurb ?? meta}</span>
      </span>
      <Rating value={place.rating} count={place.reviewCount} className="shrink-0" />
    </button>
  );
}
