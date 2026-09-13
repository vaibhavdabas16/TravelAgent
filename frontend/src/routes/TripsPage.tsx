import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Navbar } from '../components/shared/Navbar';
import { Footer } from '../components/shared/Footer';
import { EmptyState } from '../components/shared/States';
import { formatDateRange, parseDatesString, pluralize } from '../lib/format';
import { useAuth } from '../contexts/AuthContext';
import { listTrips, removeTrip, type SavedTripSummary } from '../lib/saved-trips';

/** Trips saved in this browser. */
export function TripsPage() {
  const { isAuthenticated } = useAuth();
  const [trips, setTrips] = useState<SavedTripSummary[]>([]);

  // Signed in, these come from the account; as a guest, from this browser.
  // Refetch when that changes, so signing in or out swaps the list.
  useEffect(() => {
    let cancelled = false;
    listTrips(isAuthenticated)
      .then((rows) => {
        if (!cancelled) setTrips(rows);
      })
      .catch(() => {
        if (!cancelled) setTrips([]);
      });
    return () => {
      cancelled = true;
    };
  }, [isAuthenticated]);

  const remove = async (id: string) => {
    await removeTrip(isAuthenticated, id);
    setTrips(await listTrips(isAuthenticated));
  };

  return (
    <div className="flex min-h-screen flex-col bg-paper">
      <Navbar />
      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-10 sm:px-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="lc text-[length:var(--text-xl)]">Trips</h1>
            <p className="text-[13px] text-muted">{isAuthenticated ? 'Saved to your account.' : 'Saved in this browser. Sign in to keep them.'}</p>
          </div>
          <Link to="/plan" className="btn btn-primary no-underline">
            New trip
          </Link>
        </div>
        <div className="mt-6">
          {trips.length === 0 ? (
            <EmptyState title="No saved trips yet." body="Plan one, then press Save trip on the itinerary." action={{ label: 'Plan a trip', to: '/plan' }} />
          ) : (
            <ul className="list">
              {trips.map((t) => {
                const { start, end } = parseDatesString(t.dates);
                const meta = [formatDateRange(start, end), t.days ? pluralize(t.days, 'day') : null].filter(Boolean).join(' · ') || 'Dates flexible';
                return (
                  <li key={t.id} className="row">
                    <Link to={`/trip/${t.id}`} className="min-w-0 flex-1 no-underline">
                      <span className="block truncate text-[14px] font-medium text-ink">{t.destination}</span>
                      <span className="block text-[13px] text-muted">{meta}</span>
                    </Link>
                    <button onClick={() => remove(t.id)} className="btn btn-ghost" aria-label={`Remove ${t.destination}`}>
                      Remove
                    </button>
                  </li>
                );
              })}
            </ul>
          )}
        </div>
      </main>
      <Footer />
    </div>
  );
}
