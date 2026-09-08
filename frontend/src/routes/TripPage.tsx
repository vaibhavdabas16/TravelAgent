import { useEffect, useState } from 'react';
import { useLocation, useNavigate, useParams } from 'react-router-dom';
import { TripPlan } from '../components/trip-plan';
import { loadTrip } from '../lib/planning-storage';

/**
 * Itinerary view. The trip is looked up in this order:
 *   1. router state, when we just arrived from the wizard;
 *   2. sessionStorage, so a refresh or a shared-in-this-tab link still renders.
 */
export function TripPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const location = useLocation();
  const navigate = useNavigate();
  const stateTrip = (location.state as any)?.tripData ?? null;

  const [tripData, setTripData] = useState<any>(stateTrip);

  useEffect(() => {
    if (tripData || !sessionId) return;
    const stored = loadTrip(sessionId);
    if (stored) setTripData(stored);
  }, [sessionId, tripData]);

  if (!tripData) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex flex-col items-center justify-center px-6 text-center">
        <h1 className="text-2xl text-white mb-3">This itinerary is no longer in memory</h1>
        <p className="text-white/70 max-w-md mb-8">
          Trip plans are held for the current browser tab. Reopening the link in a
          new tab, or after closing this one, means we have to plan it again.
        </p>
        <button
          onClick={() => navigate('/plan')}
          className="px-6 py-3 rounded-xl bg-blue-600 hover:bg-blue-700 text-white transition-colors"
        >
          Plan a new trip
        </button>
      </div>
    );
  }

  return (
    <TripPlan
      tripData={tripData}
      onEdit={(section: string, data: any) => console.log('Edit:', section, data)}
      onClose={() => navigate('/')}
    />
  );
}
