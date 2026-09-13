/**
 * Saved trips, wherever they happen to live.
 *
 * A signed-in user's trips belong to the account, so they survive a new
 * browser and stay invisible to anyone else signing in on this one. Guests
 * have nowhere to put them but localStorage, which is the old behaviour kept
 * as a fallback rather than the default.
 *
 * Pages call these instead of touching either store directly, so the split
 * lives in one place.
 */
import { api } from '../services/api';
import {
  isTripSaved as isTripSavedLocally,
  listSavedTrips as listLocalTrips,
  loadTripFromLibrary,
  removeTripFromLibrary,
  saveTripToLibrary,
  takeLocalLibrary,
  type SavedTripSummary,
} from './planning-storage';

export type { SavedTripSummary };

export async function listTrips(signedIn: boolean): Promise<SavedTripSummary[]> {
  if (!signedIn) return listLocalTrips();
  const rows = await api.listSavedTrips();
  return rows.map((r) => ({
    id: r.id,
    destination: r.destination ?? 'Trip',
    dates: r.dates,
    days: r.days ?? 0,
    savedAt: r.saved_at ?? '',
  }));
}

/** Returns false when the trip could not be kept, so the caller can say so. */
export async function saveTrip(signedIn: boolean, sessionId: string, trip: any): Promise<boolean> {
  if (!signedIn) return saveTripToLibrary(sessionId, trip);
  try {
    await api.saveTrip(sessionId, trip);
    return true;
  } catch {
    return false;
  }
}

export async function removeTrip(signedIn: boolean, sessionId: string): Promise<void> {
  if (!signedIn) {
    removeTripFromLibrary(sessionId);
    return;
  }
  await api.deleteSavedTrip(sessionId);
}

export async function loadTrip(signedIn: boolean, sessionId: string): Promise<any | null> {
  if (!signedIn) return loadTripFromLibrary(sessionId);
  return api.getSavedTrip(sessionId);
}

export async function isSaved(signedIn: boolean, sessionId: string): Promise<boolean> {
  if (!signedIn) return isTripSavedLocally(sessionId);
  return (await api.getSavedTrip(sessionId)) !== null;
}

/**
 * Move trips saved as a guest into the account, once, at login.
 *
 * Best effort: a trip that fails to upload is dropped rather than retried, so
 * a flaky network cannot block signing in. Returns how many moved, so the
 * caller can tell the user something happened.
 */
export async function migrateLocalTripsToAccount(): Promise<number> {
  const pending = takeLocalLibrary();
  if (pending.length === 0) return 0;

  let moved = 0;
  for (const { sessionId, trip } of pending) {
    try {
      await api.saveTrip(sessionId, trip);
      moved += 1;
    } catch {
      /* keep going; one bad trip should not strand the rest */
    }
  }
  return moved;
}
