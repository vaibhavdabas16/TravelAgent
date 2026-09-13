/**
 * Normalises the combined planning + itinerary payload into what the trip
 * screens render. Nothing in here invents data: if the backend did not send
 * a field, the view model carries null and the UI hides that element.
 */
import { addDaysISO, coordsOf, parseDatesString, formatLegDuration, formatKm, photoUrl, categoryLabel } from './format';

export type StopKind = 'stay' | 'eat' | 'poi' | 'act' | 'shop' | 'well' | 'fun' | 'night' | 'other';

export interface TripStop {
  id: string;
  index: number; // 1-based within the day
  name: string;
  kind: StopKind;
  category: string | null;
  address: string | null;
  description: string | null;
  reason: string | null; // why the AI recommended it
  rating: number | null;
  reviewCount: number | null;
  priceLevel: number | null;
  website: string | null;
  photo: string | null;
  coords: { lat: number; lng: number } | null;
  time: string | null; // only when the backend scheduled it
  durationMinutes: number | null;
  openingHours: string[] | null;
}

export interface TripLeg {
  from: string;
  to: string;
  mode: 'walk' | 'transit' | 'taxi' | 'unknown';
  modeLabel: string;
  duration: string | null;
  distance: string | null;
  distanceKm: number | null;
}

export interface TripDay {
  day: number;
  title: string | null;
  date: string | null; // YYYY-MM-DD
  stops: TripStop[];
  legs: TripLeg[]; // legs[i] goes from stops[i] to stops[i+1]
  insights: string[]; // derived from real leg data only
  totalTravelMinutes: number | null;
  totalDistanceKm: number | null;
}

export interface TripHotel {
  id: string;
  name: string;
  photo: string | null;
  rating: number | null;
  reviewCount: number | null;
  pricePerNight: number | null;
  totalPrice: number | null;
  currency: string | null;
  address: string | null;
  description: string | null;
  amenities: string[];
  commuteMinutes: number | null;
  checkIn: string | null;
  checkOut: string | null;
  coords: { lat: number; lng: number } | null;
  cancellation: string | null;
  score: number | null;
}

export interface TripFlight {
  id: string;
  airline: string | null;
  flightNumber: string | null;
  origin: string | null;
  destination: string | null;
  departure: string | null;
  arrival: string | null;
  durationMinutes: number | null;
  stops: number | null;
  layovers: string[];
  price: number | null;
  currency: string | null;
  cabin: string | null;
  baggage: string | null;
  co2Kg: number | null;
}

export interface LocalTransport {
  recommendedMode: string | null;
  modes: { mode: string; avgMinutes: number }[];
  estimatedDailyCost: number | null;
  analysis: string | null;
}

export interface TripModel {
  id: string | null;
  destination: string;
  origin: string | null;
  startDate: string | null;
  endDate: string | null;
  nights: number | null;
  travelers: number | null;
  budget: string | null;
  tripStyle: string | null;
  interests: string[];
  days: TripDay[];
  hotels: TripHotel[];
  flights: TripFlight[];
  localTransport: LocalTransport | null;
  generatedAt: string | null;
  allCoords: { lat: number; lng: number }[];
}

function str(v: unknown): string | null {
  return typeof v === 'string' && v.trim() ? v.trim() : null;
}
function numOrNull(v: unknown): number | null {
  const n = typeof v === 'string' ? parseFloat(v) : (v as number);
  return typeof n === 'number' && isFinite(n) ? n : null;
}

function kindOf(stop: any): StopKind {
  const t = String(stop?.type ?? '').toLowerCase();
  const sid = String(stop?.simple_id ?? '');
  const prefix = sid.split('_')[0];
  const map: Record<string, StopKind> = {
    pois: 'poi', poi: 'poi', dining: 'eat', eat: 'eat', shopping: 'shop', shop: 'shop',
    activities: 'act', act: 'act', wellness: 'well', well: 'well', entertainment: 'fun',
    fun: 'fun', nightlife: 'night', night: 'night', accommodation: 'stay', stay: 'stay',
  };
  return map[t] ?? map[prefix] ?? 'other';
}

function legMode(raw: unknown): { mode: TripLeg['mode']; label: string } {
  const m = String(raw ?? '').toLowerCase();
  if (m.includes('walk')) return { mode: 'walk', label: 'walk' };
  if (m.includes('transit') || m.includes('metro') || m.includes('train') || m.includes('bus')) return { mode: 'transit', label: 'transit or taxi' };
  if (m.includes('taxi') || m.includes('ride') || m.includes('driv') || m.includes('car')) return { mode: 'taxi', label: 'taxi' };
  return { mode: 'unknown', label: 'travel' };
}

function minutesFromLeg(raw: unknown): number | null {
  if (typeof raw !== 'string') return null;
  const m = raw.match(/(\d+)\s*min/i);
  return m ? parseInt(m[1], 10) : null;
}

function toStop(raw: any, index: number, dayIndex: number): TripStop {
  const hours = raw?.opening_hours?.weekday_text;
  return {
    id: str(raw?.place_id) ?? str(raw?.provider_id) ?? str(raw?.simple_id) ?? `stop-${dayIndex}-${index}`,
    index: index + 1,
    name: str(raw?.name) ?? 'Unnamed stop',
    kind: kindOf(raw),
    category: categoryLabel(raw),
    address: str(raw?.formatted_address) ?? str(raw?.address) ?? str(raw?.vicinity),
    description: str(raw?.editorial_summary?.overview) ?? str(raw?.editorial_summary) ?? str(raw?.description?.text) ?? str(raw?.description),
    reason: str(raw?.why_recommended) ?? str(raw?.recommendation_reason),
    rating: numOrNull(raw?.rating),
    reviewCount: numOrNull(raw?.user_ratings_total) ?? numOrNull(raw?.review_count),
    priceLevel: typeof raw?.price_level === 'number' ? raw.price_level : null,
    website: str(raw?.website),
    photo: photoUrl(raw),
    coords: coordsOf(raw),
    time: str(raw?.time) ?? str(raw?.start_time),
    durationMinutes: numOrNull(raw?.visit_duration_minutes),
    openingHours: Array.isArray(hours) && hours.length ? hours : null,
  };
}

function dayInsights(stops: TripStop[], legs: TripLeg[]): string[] {
  const out: string[] = [];
  if (stops.length < 2) return out;
  const known = legs.filter((l) => l.distanceKm !== null);
  if (known.length === 0) return out;

  const totalKm = known.reduce((s, l) => s + (l.distanceKm ?? 0), 0);
  const walks = known.filter((l) => l.mode === 'walk').length;
  const maxKm = Math.max(...known.map((l) => l.distanceKm ?? 0));

  if (walks === known.length) out.push('Every stop today is within walking distance of the last.');
  else if (walks >= Math.ceil(known.length / 2)) out.push(`${walks} of ${known.length} legs are walkable — the rest need a short ride.`);

  if (maxKm <= 3 && known.length >= 2) out.push(`Stops are grouped within about ${Math.max(1, Math.round(totalKm))} km to keep backtracking down.`);
  else if (maxKm > 10) out.push(`One leg is ${maxKm.toFixed(0)} km — the longest ride of the day. Plan it around traffic.`);

  return out.slice(0, 2);
}

export function buildTripModel(raw: any): TripModel | null {
  if (!raw) return null;

  const destination =
    str(raw.destination) ?? str(raw.destination?.name) ?? str(raw.constraints?.destination) ?? str(raw.query) ?? 'Your trip';

  // Dates: the planning string is our own format; the agent echoes it back.
  const { start, end, nights } = parseDatesString(raw.dates ?? raw.constraints?.dates);
  const startDate = start ?? str(raw.startDate);
  const endDate = end ?? str(raw.endDate) ?? (startDate && nights ? addDaysISO(startDate, nights) : null);

  const rawDays: any[] = Array.isArray(raw.itinerary) ? raw.itinerary : [];
  const days: TripDay[] = rawDays.map((d, di) => {
    const stops = (Array.isArray(d.stops) ? d.stops : []).map((s: any, i: number) => toStop(s, i, di));
    const legs: TripLeg[] = (Array.isArray(d.transport_legs) ? d.transport_legs : []).map((l: any) => {
      const { mode, label } = legMode(l?.mode);
      const km = numOrNull(l?.distance_km);
      return {
        from: str(l?.from) ?? '',
        to: str(l?.to) ?? '',
        mode,
        modeLabel: label,
        duration: formatLegDuration(l?.duration),
        distance: formatKm(km),
        distanceKm: km,
      };
    });
    const dayNumber = typeof d.day === 'number' ? d.day : di + 1;
    const mins = legs.map((l) => minutesFromLeg(rawLegDuration(d, l))).filter((m): m is number => m !== null);
    const kms = legs.map((l) => l.distanceKm).filter((k): k is number => k !== null);
    return {
      day: dayNumber,
      title: str(d.title),
      date: startDate ? addDaysISO(startDate, dayNumber - 1) : null,
      stops,
      legs,
      insights: dayInsights(stops, legs),
      totalTravelMinutes: mins.length ? mins.reduce((a, b) => a + b, 0) : null,
      totalDistanceKm: kms.length ? kms.reduce((a, b) => a + b, 0) : null,
    };
  });

  // Hotels: only the ones the user picked, matched against the search results.
  const selectedHotelIds: string[] = raw.selectedItems?.accommodations ?? [];
  const hotelPool: any[] = raw.recommended_hotels ?? raw.hotels ?? [];
  const hotels: TripHotel[] = hotelPool
    .filter((h) => {
      const ids = [h?.hotel_id, h?.id, h?.provider_id].filter(Boolean).map(String);
      return selectedHotelIds.length === 0 ? false : ids.some((id) => selectedHotelIds.map(String).includes(id));
    })
    .map((h) => ({
      id: String(h.hotel_id ?? h.id ?? h.provider_id),
      name: str(h.name) ?? 'Hotel',
      photo: photoUrl(h),
      rating: numOrNull(h.rating),
      reviewCount: numOrNull(h.review_count),
      pricePerNight: numOrNull(h.price_per_night),
      totalPrice: numOrNull(h.total_price),
      currency: str(h.currency),
      address: str(h.address) ?? str(h.address?.cityName),
      description: str(h.description?.text) ?? str(h.description),
      amenities: Array.isArray(h.amenities) ? h.amenities.filter((a: unknown) => typeof a === 'string') : [],
      commuteMinutes: numOrNull(h.avg_commute_time_minutes),
      checkIn: str(h.check_in),
      checkOut: str(h.check_out),
      coords: coordsOf(h),
      cancellation: str(h.cancellation_policy),
      score: numOrNull(h.ai_score),
    }));

  const selectedFlightIds: string[] = (raw.selectedItems?.transportation ?? []).map(String);
  const flightPool: any[] = raw.recommended_flights ?? [];
  const flights: TripFlight[] = flightPool
    .filter((f) => {
      const ids = [f?.offer_id, f?.id, f?.provider_id].filter(Boolean).map(String);
      return ids.some((id) => selectedFlightIds.includes(id));
    })
    .map((f) => ({
      id: String(f.offer_id ?? f.id ?? f.provider_id),
      airline: str(f.airline),
      flightNumber: str(f.flight_number),
      origin: str(f.origin),
      destination: str(f.destination),
      departure: str(f.departure_datetime) ?? str(f.departure_at),
      arrival: str(f.arrival_datetime) ?? str(f.arrival_at),
      durationMinutes: numOrNull(f.duration_minutes),
      stops: typeof f.stops === 'number' ? f.stops : null,
      layovers: Array.isArray(f.layover_airports) ? f.layover_airports : [],
      price: numOrNull(f.price),
      currency: str(f.currency),
      cabin: str(f.cabin_class),
      baggage: str(f.baggage_allowance),
      co2Kg: numOrNull(f.co2_emissions_kg),
    }));

  const lt = raw.local_transport;
  const localTransport: LocalTransport | null =
    lt && typeof lt === 'object' && (lt.mode_comparison || lt.recommended_mode)
      ? {
          recommendedMode: str(lt.recommended_mode),
          modes: Object.entries(lt.mode_comparison ?? {})
            .map(([mode, v]: [string, any]) => ({ mode, avgMinutes: numOrNull(v?.avg_time_minutes) ?? -1 }))
            .filter((m) => m.avgMinutes >= 0),
          estimatedDailyCost: numOrNull(lt.estimated_daily_cost),
          analysis: str(lt.analysis),
        }
      : null;

  const allCoords = [
    ...days.flatMap((d) => d.stops.map((s) => s.coords)),
    ...hotels.map((h) => h.coords),
  ].filter((c): c is { lat: number; lng: number } => !!c);

  return {
    id: str(raw.trip_id) ?? str(raw.sessionId),
    destination,
    origin: str(raw.origin),
    startDate,
    endDate,
    nights: nights ?? (days.length ? days.length - 1 : null),
    travelers: numOrNull(raw.travelers),
    budget: str(raw.budget),
    tripStyle: str(raw.tripStyle),
    interests: Array.isArray(raw.interests) ? raw.interests : [],
    days,
    hotels,
    flights,
    localTransport,
    generatedAt: str(raw.generated_at),
    allCoords,
  };
}

/** Find the raw duration string for a leg so we can sum minutes. */
function rawLegDuration(day: any, leg: TripLeg): unknown {
  const match = (day.transport_legs ?? []).find((l: any) => l?.from === leg.from && l?.to === leg.to);
  return match?.duration;
}

export const STOP_KIND_LABEL: Record<StopKind, string> = {
  stay: 'Stay',
  eat: 'Food',
  poi: 'Sight',
  act: 'Activity',
  shop: 'Shopping',
  well: 'Wellness',
  fun: 'Entertainment',
  night: 'Nightlife',
  other: 'Stop',
};
