/**
 * Display helpers. Every function here returns null when the underlying data
 * is missing, so callers can hide the element instead of showing a made-up
 * value.
 */

export function formatMoney(amount: unknown, currency?: string | null): string | null {
  const n = typeof amount === 'string' ? parseFloat(amount) : (amount as number);
  if (typeof n !== 'number' || !isFinite(n) || n <= 0) return null;
  const code = (currency || 'USD').toUpperCase();
  try {
    return new Intl.NumberFormat(undefined, {
      style: 'currency',
      currency: code,
      maximumFractionDigits: n >= 100 ? 0 : 2,
    }).format(n);
  } catch {
    return `${code} ${Math.round(n).toLocaleString()}`;
  }
}

export function formatMinutes(mins: unknown): string | null {
  const n = typeof mins === 'string' ? parseFloat(mins) : (mins as number);
  if (typeof n !== 'number' || !isFinite(n) || n <= 0) return null;
  const h = Math.floor(n / 60);
  const m = Math.round(n % 60);
  if (h === 0) return `${m} min`;
  if (m === 0) return `${h} h`;
  return `${h} h ${m} min`;
}

/** Backend legs say things like "12 mins", "20 mins driving", "unknown". */
export function formatLegDuration(raw: unknown): string | null {
  if (typeof raw !== 'string') return null;
  const m = raw.match(/(\d+)\s*min/i);
  if (!m) return null;
  return formatMinutes(parseInt(m[1], 10));
}

export function formatKm(km: unknown): string | null {
  const n = typeof km === 'string' ? parseFloat(km) : (km as number);
  if (typeof n !== 'number' || !isFinite(n) || n <= 0) return null;
  return n < 1 ? `${Math.round(n * 1000)} m` : `${n.toFixed(1)} km`;
}

export function formatTime(iso: unknown): string | null {
  if (typeof iso !== 'string' || !iso) return null;
  const d = new Date(iso);
  if (isNaN(d.getTime())) {
    // Maybe it is already HH:MM
    return /^\d{1,2}:\d{2}$/.test(iso) ? iso : null;
  }
  return d.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit', hour12: false });
}

export function formatDate(iso: unknown, opts: Intl.DateTimeFormatOptions = { month: 'short', day: 'numeric' }): string | null {
  if (typeof iso !== 'string' || !iso) return null;
  const d = new Date(iso.length === 10 ? iso + 'T00:00:00' : iso);
  if (isNaN(d.getTime())) return null;
  return d.toLocaleDateString(undefined, opts);
}

export function formatDateRange(start: string | null | undefined, end: string | null | undefined): string | null {
  const a = formatDate(start);
  const b = formatDate(end);
  if (a && b) return `${a} – ${b}`;
  return a ?? b ?? null;
}

/** "2026-10-12 to 2026-10-18" | "from 2026-10-12 for 5 nights" | "5 nights, dates flexible" */
export function parseDatesString(dates: unknown): { start: string | null; end: string | null; nights: number | null } {
  if (typeof dates !== 'string') return { start: null, end: null, nights: null };
  const iso = dates.match(/(\d{4}-\d{2}-\d{2})/g) ?? [];
  const nightsMatch = dates.match(/(\d+)\s*nights?/);
  const start = iso[0] ?? null;
  const end = iso[1] ?? null;
  let nights = nightsMatch ? parseInt(nightsMatch[1], 10) : null;
  if (start && end && !nights) {
    nights = Math.round((new Date(end).getTime() - new Date(start).getTime()) / 86400000);
  }
  return { start, end, nights };
}

export function addDaysISO(iso: string, n: number): string {
  const d = new Date(iso + 'T00:00:00');
  d.setDate(d.getDate() + n);
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

export function pluralize(n: number, one: string, many = one + 's'): string {
  return `${n} ${n === 1 ? one : many}`;
}

/** Google Places "types" are snake_case; turn the first useful one into a label. */
const TYPE_LABELS: Record<string, string> = {
  tourist_attraction: 'Attraction',
  point_of_interest: 'Place',
  establishment: 'Place',
  museum: 'Museum',
  park: 'Park',
  restaurant: 'Restaurant',
  cafe: 'Café',
  bar: 'Bar',
  food: 'Food',
  place_of_worship: 'Temple',
  hindu_temple: 'Temple',
  church: 'Church',
  mosque: 'Mosque',
  shopping_mall: 'Shopping',
  store: 'Shop',
  clothing_store: 'Shop',
  spa: 'Spa',
  gym: 'Gym',
  lodging: 'Stay',
  natural_feature: 'Nature',
  zoo: 'Zoo',
  aquarium: 'Aquarium',
  amusement_park: 'Theme park',
  art_gallery: 'Gallery',
  night_club: 'Nightlife',
  movie_theater: 'Cinema',
  stadium: 'Stadium',
  beach: 'Beach',
  landmark: 'Landmark',
  library: 'Library',
  market: 'Market',
};

export function categoryLabel(item: any): string | null {
  const types: string[] = item?.types ?? item?.category ?? item?.categories ?? [];
  if (!Array.isArray(types)) return null;
  const generic = new Set(['point_of_interest', 'establishment']);
  const specific = types.find((t) => TYPE_LABELS[t] && !generic.has(t));
  if (specific) return TYPE_LABELS[specific];
  const any = types.find((t) => TYPE_LABELS[t]);
  if (any) return TYPE_LABELS[any];
  const first = types[0];
  return typeof first === 'string' ? first.replace(/_/g, ' ').replace(/^\w/, (c) => c.toUpperCase()) : null;
}

export function priceLevelLabel(level: unknown): string | null {
  if (typeof level !== 'number') return null;
  if (level === 0) return 'Free';
  return '$'.repeat(Math.min(4, Math.max(1, level)));
}

/**
 * Photo for a POI/hotel. The backend rewrites Google photo references into a
 * proxied /photos/{ref} URL; hotels from Amadeus carry photo_url directly.
 * Returns null when there is none — callers render a neutral placeholder.
 */
export function photoUrl(item: any): string | null {
  if (!item) return null;
  if (typeof item.photo_url === 'string' && item.photo_url) return item.photo_url;
  if (typeof item.image_url === 'string' && item.image_url) return item.image_url;
  if (typeof item.image === 'string' && item.image.startsWith('http')) return item.image;
  const photos = item.photos;
  if (Array.isArray(photos) && photos[0]) {
    const p = photos[0];
    if (typeof p === 'string' && p.startsWith('http')) return p;
    if (typeof p?.url === 'string') return p.url;
  }
  return null;
}

export function coordsOf(item: any): { lat: number; lng: number } | null {
  if (!item) return null;
  const cands = [
    item.location,
    item.geometry?.location,
    { lat: item.lat, lng: item.lng },
    { lat: item.latitude, lng: item.longitude },
  ];
  for (const c of cands) {
    if (c && typeof c.lat === 'number' && typeof c.lng === 'number' && isFinite(c.lat) && isFinite(c.lng)) {
      return { lat: c.lat, lng: c.lng };
    }
  }
  return null;
}

/** Tint class for a place, from its Google-style types. */
export function categoryTone(item: any): 'sight' | 'eat' | 'stay' | 'act' | 'shop' | 'well' | 'fun' | 'other' {
  const types: string[] = Array.isArray(item?.types) ? item.types : Array.isArray(item?.category) ? item.category : [];
  const has = (...keys: string[]) => types.some((t) => keys.some((k) => String(t).includes(k)));
  if (has('lodging', 'hotel', 'hostel')) return 'stay';
  if (has('restaurant', 'cafe', 'food', 'bakery', 'bar', 'market', 'meal')) return 'eat';
  if (has('spa', 'gym', 'onsen', 'bath', 'yoga')) return 'well';
  if (has('store', 'shopping', 'shop', 'mall', 'boutique')) return 'shop';
  if (has('night_club', 'movie', 'theater', 'stadium', 'amusement', 'casino', 'music')) return 'fun';
  if (has('park', 'hiking', 'trail', 'beach', 'natural', 'zoo', 'aquarium', 'tour', 'activity', 'adventure')) return 'act';
  if (has('museum', 'attraction', 'worship', 'temple', 'shrine', 'church', 'landmark', 'monument', 'gallery', 'historic')) return 'sight';
  return 'other';
}
