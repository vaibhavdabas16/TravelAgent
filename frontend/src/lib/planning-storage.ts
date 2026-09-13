/**
 * Durable storage for an in-progress planning session.
 *
 * The wizard used to keep everything in React state, so a refresh, an
 * accidental back-navigation, or a crashed tab lost the whole trip. We persist
 * the working set to sessionStorage keyed by the backend session id, so the
 * URL alone is enough to rebuild the wizard.
 */

const PREFIX = 'travel-agent:session:';
const TRIP_PREFIX = 'travel-agent:trip:';

/** Everything the wizard needs to resume a session from a bare URL. */
export interface PlanningData {
  query: string;
  destination: string | null;
  origin?: string | null;
  tripStyle: string;
  travelers?: number;
  budget?: string;
  interests?: string[];
  pace?: string;
  amenities?: string[];
  dates?: string | null;
  sessionId: string | null;
  selectedItems: Record<string, any>;
  pois?: any[];
  recommended_hotels?: any[];
  recommended_flights?: any[];
  local_transport?: Record<string, any>;
  dining?: any[];
  activities?: any[];
  shopping?: any[];
  wellness?: any[];
  /** The backend's one-line summary per step, shown as the agent's note. */
  summaries?: Record<string, string | undefined>;
  [key: string]: any;
}

export function emptyPlanningData(initial?: Partial<PlanningData>): PlanningData {
  return {
    query: initial?.query ?? '',
    destination: initial?.destination ?? null,
    tripStyle: initial?.tripStyle ?? 'balanced',
    selectedItems: {},
    sessionId: null,
    ...initial,
  };
}

function read<T>(key: string): T | null {
  try {
    const raw = sessionStorage.getItem(key);
    return raw ? (JSON.parse(raw) as T) : null;
  } catch {
    // Private browsing, quota, or corrupt JSON — treat as a cold start rather
    // than taking the app down.
    return null;
  }
}

function write(key: string, value: unknown): void {
  try {
    sessionStorage.setItem(key, JSON.stringify(value));
  } catch {
    // Storage full or unavailable: the wizard still works in-memory for this
    // tab, it just will not survive a refresh.
  }
}

export function loadPlanningData(sessionId: string): PlanningData | null {
  return read<PlanningData>(PREFIX + sessionId);
}

export function savePlanningData(sessionId: string, data: PlanningData): void {
  write(PREFIX + sessionId, data);
}

export function clearPlanningData(sessionId: string): void {
  try {
    sessionStorage.removeItem(PREFIX + sessionId);
  } catch {
    /* nothing to clean up */
  }
}

export function loadTrip(sessionId: string): any | null {
  return read<any>(TRIP_PREFIX + sessionId);
}

export function saveTrip(sessionId: string, trip: any): void {
  write(TRIP_PREFIX + sessionId, trip);
}

// --- Saved trips -------------------------------------------------------------
// sessionStorage holds the working copy for this tab. "Save trip" promotes it
// to localStorage so it shows up under My trips in any tab, and survives the
// tab closing.

const LIBRARY_KEY = 'travel-agent:library';

export interface SavedTripSummary {
  id: string;
  destination: string;
  dates: string | null;
  days: number;
  savedAt: string;
}

function readLibrary(): Record<string, any> {
  try {
    const raw = localStorage.getItem(LIBRARY_KEY);
    return raw ? (JSON.parse(raw) as Record<string, any>) : {};
  } catch {
    return {};
  }
}

export function saveTripToLibrary(sessionId: string, trip: any): boolean {
  try {
    const lib = readLibrary();
    lib[sessionId] = { ...trip, savedAt: new Date().toISOString() };
    localStorage.setItem(LIBRARY_KEY, JSON.stringify(lib));
    return true;
  } catch {
    return false;
  }
}

export function removeTripFromLibrary(sessionId: string): void {
  try {
    const lib = readLibrary();
    delete lib[sessionId];
    localStorage.setItem(LIBRARY_KEY, JSON.stringify(lib));
  } catch {
    /* nothing to clean up */
  }
}

export function loadTripFromLibrary(sessionId: string): any | null {
  return readLibrary()[sessionId] ?? null;
}

export function isTripSaved(sessionId: string): boolean {
  return Boolean(readLibrary()[sessionId]);
}

export function listSavedTrips(): SavedTripSummary[] {
  return Object.entries(readLibrary())
    .map(([id, t]) => ({
      id,
      destination: typeof t?.destination === 'string' ? t.destination : 'Trip',
      dates: typeof t?.dates === 'string' ? t.dates : null,
      days: Array.isArray(t?.itinerary) ? t.itinerary.length : 0,
      savedAt: typeof t?.savedAt === 'string' ? t.savedAt : '',
    }))
    .sort((a, b) => (a.savedAt < b.savedAt ? 1 : -1));
}

/**
 * Read every locally saved trip and clear the store.
 *
 * Used once at login to move trips planned as a guest into the account. They
 * are removed locally in the same step: a signed-in user reads their trips
 * from the server, and leaving copies behind is what let one account see
 * another's trips on a shared browser.
 */
export function takeLocalLibrary(): Array<{ sessionId: string; trip: any }> {
  const lib = readLibrary();
  const entries = Object.entries(lib).map(([sessionId, trip]) => ({ sessionId, trip }));
  try {
    localStorage.removeItem(LIBRARY_KEY);
  } catch {
    /* nothing to clean up */
  }
  return entries;
}
