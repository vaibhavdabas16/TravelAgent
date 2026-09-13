/**
 * Turns a free-text trip request into the structured fields the planning API
 * needs. Runs entirely in the browser so the "here's what I understood" step
 * is instant; everything it extracts is shown back to the user as editable
 * fields before anything is sent, so a wrong guess costs one click.
 *
 * The output shape mirrors PlanningStartRequest on the backend. Budget must be
 * one of "budget" | "moderate" | "luxury" — anything else falls back to
 * moderate server-side, which is what the old "Mid-range" label silently did.
 */

export type BudgetTier = 'budget' | 'moderate' | 'luxury';
export type Pace = 'relaxed' | 'balanced' | 'packed';

export interface ParsedTrip {
  query: string;
  destination: string | null;
  origin: string | null;
  startDate: string | null; // YYYY-MM-DD
  endDate: string | null; // YYYY-MM-DD
  nights: number | null;
  /** "October" when only a month was given — no day is invented. */
  month: string | null;
  travelers: number | null;
  budget: BudgetTier | null;
  interests: string[];
  pace: Pace | null;
  styles: string[]; // ids from TRAVEL_STYLES
  amenities: string[];
}

export interface TravelStyle {
  id: string;
  title: string;
  description: string;
  interests: string[];
  keywords: string[];
}

/** Image-led selection tiles. Interests feed the backend's discovery prompt. */
export const TRAVEL_STYLES: TravelStyle[] = [
  {
    id: 'slow',
    title: 'Slow & scenic',
    description: 'Fewer stops, longer lunches, time to wander.',
    interests: ['Scenic views', 'Relaxation'],
    keywords: ['slow', 'scenic', 'relax', 'relaxed', 'laid-back', 'laid back', 'chill', 'unwind', 'leisurely'],
  },
  {
    id: 'food',
    title: 'Food & culture',
    description: 'Markets, neighbourhood restaurants, old quarters.',
    interests: ['Food', 'Culture', 'History'],
    keywords: ['food', 'eat', 'eating', 'cuisine', 'restaurant', 'culinary', 'culture', 'cultural', 'history', 'historic', 'temple', 'temples', 'museum', 'museums', 'heritage', 'art'],
  },
  {
    id: 'adventure',
    title: 'Adventure',
    description: 'Trails, water, heights. Days that earn the dinner.',
    interests: ['Adventure', 'Outdoors', 'Nature'],
    keywords: ['adventure', 'hike', 'hiking', 'trek', 'trekking', 'outdoor', 'outdoors', 'nature', 'surf', 'dive', 'diving', 'climb', 'kayak', 'wildlife', 'safari'],
  },
  {
    id: 'nightlife',
    title: 'Nightlife',
    description: 'Late dinners, bars worth the queue, live music.',
    interests: ['Nightlife', 'Music', 'Bars'],
    keywords: ['nightlife', 'night life', 'bars', 'clubs', 'clubbing', 'party', 'music', 'concert', 'drinks', 'cocktail'],
  },
  {
    id: 'luxury',
    title: 'Luxury',
    description: 'The good hotel, the tasting menu, a driver on call.',
    interests: ['Fine dining', 'Luxury', 'Spa'],
    keywords: ['luxury', 'luxurious', 'five star', '5 star', '5-star', 'upscale', 'premium', 'high-end', 'high end'],
  },
  {
    id: 'hidden',
    title: 'Hidden gems',
    description: 'Skip the queue. Local favourites, side streets.',
    interests: ['Local experiences', 'Off the beaten path'],
    keywords: ['hidden', 'local', 'locals', 'off the beaten', 'authentic', 'offbeat', 'quiet', 'lesser known', 'lesser-known', 'non-touristy'],
  },
  {
    id: 'family',
    title: 'Family',
    description: 'Short walks, early dinners, something for everyone.',
    interests: ['Family friendly', 'Parks', 'Kid-friendly'],
    keywords: ['family', 'kids', 'kid', 'children', 'child', 'toddler', 'parents', 'grandparents'],
  },
  {
    id: 'photo',
    title: 'Photography',
    description: 'Golden hour, viewpoints, streets with character.',
    interests: ['Photography', 'Scenic views', 'Architecture'],
    keywords: ['photo', 'photos', 'photography', 'photograph', 'instagram', 'viewpoint', 'viewpoints', 'architecture', 'sunrise', 'sunset'],
  },
];

export const AMENITY_OPTIONS = [
  'Free Wi-Fi',
  'Breakfast included',
  'Pool',
  'Gym',
  'Spa',
  'Parking',
  'Airport shuttle',
  'Kitchen',
  'Pet friendly',
  'Air conditioning',
];

const MONTHS = [
  'january', 'february', 'march', 'april', 'may', 'june',
  'july', 'august', 'september', 'october', 'november', 'december',
];

const WORD_NUMBERS: Record<string, number> = {
  one: 1, two: 2, three: 3, four: 4, five: 5, six: 6, seven: 7, eight: 8, nine: 9, ten: 10,
  eleven: 11, twelve: 12, fourteen: 14, a: 1, an: 1,
};

function toISO(d: Date): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

function addDays(iso: string, n: number): string {
  const d = new Date(iso + 'T00:00:00');
  d.setDate(d.getDate() + n);
  return toISO(d);
}

function num(token: string | undefined): number | null {
  if (!token) return null;
  const t = token.toLowerCase();
  if (/^\d+$/.test(t)) return parseInt(t, 10);
  return WORD_NUMBERS[t] ?? null;
}

function monthIndex(name: string): number {
  const n = name.toLowerCase().slice(0, 3);
  return MONTHS.findIndex((m) => m.startsWith(n));
}

/** Next occurrence of a month/day; assumes the trip is in the future. */
function upcoming(month: number, day: number, explicitYear?: number): string {
  const today = new Date();
  let year = explicitYear ?? today.getFullYear();
  let d = new Date(year, month, day);
  if (!explicitYear && d < today) d = new Date(year + 1, month, day);
  return toISO(d);
}

function titleCase(s: string): string {
  return s
    .trim()
    .split(/\s+/)
    .map((w) => (w.length > 2 ? w[0].toUpperCase() + w.slice(1) : w.toUpperCase() === w ? w : w))
    .join(' ');
}

/** Strip trailing prepositions and filler from a captured place name. */
function cleanPlace(raw: string): string | null {
  let s = raw
    .replace(/[.,;!?]+$/g, '')
    .replace(/\b(next|this|in|on|for|with|during|around|and|between|from|under|at)\b.*$/i, '')
    .trim();
  s = s.replace(/^(the)\s+/i, '');
  if (!s || s.length < 2 || s.length > 40) return null;
  if (/^\d/.test(s)) return null;
  return titleCase(s);
}

export function parseTripQuery(query: string): ParsedTrip {
  const text = query.trim();
  const lower = text.toLowerCase();

  const out: ParsedTrip = {
    query: text,
    destination: null,
    origin: null,
    startDate: null,
    endDate: null,
    nights: null,
    month: null,
    travelers: null,
    budget: null,
    interests: [],
    pace: null,
    styles: [],
    amenities: [],
  };

  // --- Duration: "6 days", "a week", "two weeks", "5 nights", "long weekend"
  const dur = lower.match(/\b(\d+|a|an|one|two|three|four|five|six|seven|eight|nine|ten|twelve|fourteen)[\s-]*(day|days|night|nights|week|weeks|weekend)\b/);
  if (dur) {
    const n = num(dur[1]) ?? 1;
    const unit = dur[2];
    if (unit.startsWith('week') && unit !== 'weekend') out.nights = n * 7;
    else if (unit === 'weekend') out.nights = lower.includes('long weekend') ? 3 : 2;
    else if (unit.startsWith('night')) out.nights = n;
    else out.nights = Math.max(1, n - 1);
  } else if (/\bweekend\b/.test(lower)) {
    out.nights = 2;
  }

  // --- Explicit date ranges: "Oct 12-18", "12-18 October", "October 12 to 18", "from 3 to 9 March 2026"
  const mdRange = lower.match(/\b(jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\.?\s+(\d{1,2})(?:st|nd|rd|th)?\s*(?:-|–|to|until|till|through)\s*(?:(jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\.?\s+)?(\d{1,2})(?:st|nd|rd|th)?(?:,?\s*(\d{4}))?/);
  const dmRange = lower.match(/\b(\d{1,2})(?:st|nd|rd|th)?\s*(?:-|–|to|until|till|through)\s*(\d{1,2})(?:st|nd|rd|th)?\s+(?:of\s+)?(jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*(?:,?\s*(\d{4}))?/);
  if (mdRange) {
    const m1 = monthIndex(mdRange[1]);
    const m2 = mdRange[3] ? monthIndex(mdRange[3]) : m1;
    const year = mdRange[5] ? parseInt(mdRange[5], 10) : undefined;
    out.startDate = upcoming(m1, parseInt(mdRange[2], 10), year);
    const startYear = parseInt(out.startDate.slice(0, 4), 10);
    out.endDate = upcoming(m2, parseInt(mdRange[4], 10), year ?? startYear);
    if (out.endDate < out.startDate) out.endDate = upcoming(m2, parseInt(mdRange[4], 10), startYear + 1);
  } else if (dmRange) {
    const m = monthIndex(dmRange[3]);
    const year = dmRange[4] ? parseInt(dmRange[4], 10) : undefined;
    out.startDate = upcoming(m, parseInt(dmRange[1], 10), year);
    const startYear = parseInt(out.startDate.slice(0, 4), 10);
    out.endDate = upcoming(m, parseInt(dmRange[2], 10), year ?? startYear);
  } else {
    // Single anchored date: "on October 12", "12th October", "from 3 March"
    const md = lower.match(/\b(jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\.?\s+(\d{1,2})(?:st|nd|rd|th)?\b(?:,?\s*(\d{4}))?/);
    const dm = lower.match(/\b(\d{1,2})(?:st|nd|rd|th)?\s+(?:of\s+)?(jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\b(?:,?\s*(\d{4}))?/);
    const monthOnly = lower.match(/\b(?:in|during|for|this|next)\s+(january|february|march|april|may|june|july|august|september|october|november|december)\b/);
    if (md) {
      out.startDate = upcoming(monthIndex(md[1]), parseInt(md[2], 10), md[3] ? parseInt(md[3], 10) : undefined);
    } else if (dm) {
      out.startDate = upcoming(monthIndex(dm[2]), parseInt(dm[1], 10), dm[3] ? parseInt(dm[3], 10) : undefined);
    } else if (monthOnly) {
      // A month with no day: leave the dates empty rather than invent a day.
      out.month = monthOnly[1][0].toUpperCase() + monthOnly[1].slice(1);
    }
    if (out.startDate && out.nights) out.endDate = addDays(out.startDate, out.nights);
  }
  if (out.startDate && out.endDate && !out.nights) {
    const a = new Date(out.startDate + 'T00:00:00').getTime();
    const b = new Date(out.endDate + 'T00:00:00').getTime();
    out.nights = Math.max(1, Math.round((b - a) / 86400000));
  }

  // --- Travelers
  const trav = lower.match(/\b(\d+|two|three|four|five|six|seven|eight)\s*(?:people|persons|person|travellers|travelers|adults|friends|of us|pax|guests)\b/);
  if (trav) out.travelers = num(trav[1]);
  else if (/\b(solo|alone|by myself|just me|myself)\b/.test(lower)) out.travelers = 1;
  else if (/\b(couple|honeymoon|my (?:wife|husband|partner|girlfriend|boyfriend)|the two of us|romantic|anniversary)\b/.test(lower)) out.travelers = 2;
  else if (/\bfamily of (\d+)\b/.test(lower)) out.travelers = parseInt(lower.match(/\bfamily of (\d+)\b/)![1], 10);
  else if (/\bfamily\b/.test(lower)) out.travelers = 4;

  // --- Budget tier
  if (/\b(luxury|luxurious|five[- ]star|5[- ]star|splurge|no budget|money is no object|high[- ]end|premium)\b/.test(lower)) out.budget = 'luxury';
  else if (/\b(cheap|budget|backpack|backpacking|shoestring|affordable|hostel|hostels|low[- ]cost|frugal|tight budget)\b/.test(lower)) out.budget = 'budget';
  else if (/\b(mid[- ]range|moderate|comfortable|reasonable)\b/.test(lower)) out.budget = 'moderate';

  // A hotel cap like "under ₹15,000 per night" is passed through as an amenity-style note
  const cap = text.match(/(?:under|below|less than|max(?:imum)?|up to)\s*([₹$€£]\s?[\d,]+(?:\.\d+)?\s*k?|[\d,]+\s*k?\s*(?:inr|usd|eur|gbp|rupees|dollars|euros|pounds))\s*(?:\/|per|a|each)?\s*(night|day|person|head)?/i);
  if (cap) {
    const note = `Max ${cap[1].replace(/\s+/g, '')}${cap[2] ? ` per ${cap[2]}` : ' total'}`;
    out.amenities.push(note);
    if (!out.budget && cap[2] && /night|day/.test(cap[2])) {
      const raw = parseFloat(cap[1].replace(/[^\d.]/g, ''));
      const isK = /k\b/i.test(cap[1]);
      const val = isK ? raw * 1000 : raw;
      const inr = /₹|inr|rupee/i.test(cap[1]);
      if (inr) out.budget = val <= 4000 ? 'budget' : val >= 18000 ? 'luxury' : 'moderate';
      else out.budget = val <= 60 ? 'budget' : val >= 250 ? 'luxury' : 'moderate';
    }
  }

  // --- Pace
  if (/\b(slow|relaxed|relaxing|laid[- ]back|leisurely|chill|easy[- ]going|unhurried)\b/.test(lower)) out.pace = 'relaxed';
  else if (/\b(packed|see everything|as much as possible|fast[- ]paced|jam[- ]packed|busy|non[- ]stop|action[- ]packed)\b/.test(lower)) out.pace = 'packed';

  // --- Styles / interests
  for (const style of TRAVEL_STYLES) {
    if (style.keywords.some((k) => new RegExp(`\\b${k.replace(/[-/\\^$*+?.()|[\]{}]/g, '\\$&')}\\b`).test(lower))) {
      out.styles.push(style.id);
    }
  }
  out.interests = Array.from(new Set(out.styles.flatMap((id) => TRAVEL_STYLES.find((s) => s.id === id)!.interests)));
  if (out.styles.includes('slow') && !out.pace) out.pace = 'relaxed';
  if (out.styles.includes('luxury') && !out.budget) out.budget = 'luxury';

  // --- Amenities
  for (const a of AMENITY_OPTIONS) {
    const key = a.toLowerCase().replace(/ included| friendly/g, '');
    if (lower.includes(key) || (a === 'Free Wi-Fi' && /\bwi-?fi\b/.test(lower))) out.amenities.push(a);
  }
  if (/\bbreakfast\b/.test(lower) && !out.amenities.includes('Breakfast included')) out.amenities.push('Breakfast included');
  out.amenities = Array.from(new Set(out.amenities));

  // --- Origin: "from Delhi", "flying from Mumbai", "starting in London"
  const origin = text.match(/\b(?:flying|fly|depart(?:ing)?|leaving|starting|start)\s+(?:from|in|out of)\s+([A-Z][\w.'-]*(?:\s+[A-Z][\w.'-]*){0,2})/) ||
    text.match(/\bfrom\s+([A-Z][\w.'-]*(?:\s+[A-Z][\w.'-]*){0,2})/);
  if (origin) out.origin = cleanPlace(origin[1]);

  // --- Destination: "in Japan", "to Kyoto", "trip to New York", "visit Lisbon", "Bali trip"
  const destPatterns = [
    /\b([A-Z][\w.'-]*(?:\s+[A-Z][\w.'-]*){0,2})\s+(?:trip|holiday|vacation|getaway|honeymoon|escape|break|itinerary)\b/,
    /\b(?:trip|holiday|vacation|getaway|honeymoon|escape|break|week|weekend|days?|nights?)\s+(?:to|in|around|through|across)\s+([A-Z][\w.'-]*(?:\s+(?:[A-Z][\w.'-]*|de|del|la|of))*)/,
    /\b(?:go|going|travel|travelling|traveling|visit|visiting|explore|exploring|fly|flying|head|heading)\s+(?:to|around)\s+([A-Z][\w.'-]*(?:\s+(?:[A-Z][\w.'-]*|de|del|la|of))*)/,
    /\b(?:in|to|around)\s+([A-Z][\w.'-]*(?:\s+(?:[A-Z][\w.'-]*|de|del|la|of))*)/,
    /^([A-Z][\w.'-]*(?:\s+[A-Z][\w.'-]*)*)\b/,
  ];
  for (const p of destPatterns) {
    const m = text.match(p);
    if (!m) continue;
    const candidate = cleanPlace(m[1]);
    if (!candidate) continue;
    if (out.origin && candidate.toLowerCase() === out.origin.toLowerCase()) continue;
    // Skip month names and style words that happen to be capitalised.
    if (monthIndex(candidate) !== -1 && candidate.length <= 9) continue;
    if (/^(I|We|My|Our|Plan|Please|Trip|Luxury|Budget|Family)$/i.test(candidate)) continue;
    out.destination = candidate;
    break;
  }

  return out;
}

/** Fields as PlanningStartRequest wants them. */
export function toStartRequest(p: ParsedTrip, styleOverride?: string) {
  const dates =
    p.startDate && p.endDate
      ? `${p.startDate} to ${p.endDate}`
      : p.startDate
        ? `from ${p.startDate}${p.nights ? ` for ${p.nights} nights` : ''}`
        : p.nights
          ? `${p.nights} nights${p.month ? ` in ${p.month}` : ''}, dates flexible`
          : p.month
            ? `${p.month}, dates flexible`
            : null;

  const pace = p.pace ?? 'balanced';
  const tripStyle =
    styleOverride ?? (pace === 'relaxed' ? 'laid-back' : pace === 'packed' ? 'adventurous' : 'balanced');

  return {
    query: p.query,
    destination: p.destination ?? '',
    origin: p.origin,
    travelers: p.travelers ?? 2,
    budget: p.budget ?? 'moderate',
    interests: p.interests,
    pace: pace === 'relaxed' ? 'Slow & relaxed' : pace === 'packed' ? 'Action-packed' : 'Balanced',
    amenities: p.amenities,
    dates,
    tripStyle,
  };
}
