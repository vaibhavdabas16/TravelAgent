import { useEffect, useMemo, useState } from 'react';
import { useLocation, useParams } from 'react-router-dom';
import { Map as MapIcon, X } from 'lucide-react';
import { toast } from 'sonner';
import { Navbar } from '../components/shared/Navbar';
import type { Command } from '../components/shared/CommandPalette';
import { EmptyState } from '../components/shared/States';
import { Note } from '../components/shared/Agent';
import { DaySelector } from '../components/trip/DaySelector';
import { ItineraryTimeline } from '../components/trip/ItineraryTimeline';
import { MapPanel } from '../components/trip/MapPanel';
import { HotelRow } from '../components/trip/HotelCard';
import { FlightRow } from '../components/trip/FlightCard';
import { LocalTransportPanel } from '../components/trip/LocalTransportPanel';
import { buildTripModel } from '../lib/trip-model';
import { formatDateRange, formatMinutes, pluralize } from '../lib/format';
import { isTripSaved, loadTrip, loadTripFromLibrary, saveTrip, saveTripToLibrary } from '../lib/planning-storage';

type Tab = 'itinerary' | 'overview' | 'stay' | 'flights';

/**
 * The itinerary. Looked up from router state (just built), then this tab's
 * sessionStorage, then the saved-trips library.
 */
export function TripPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const location = useLocation();
  const stateTrip = (location.state as any)?.tripData ?? null;

  const [raw, setRaw] = useState<any>(stateTrip);
  const [tab, setTab] = useState<Tab>(() => {
    const t = new URLSearchParams(location.search).get('tab');
    return t === 'overview' || t === 'stay' || t === 'flights' ? t : 'itinerary';
  });
  const [activeDay, setActiveDay] = useState(1);
  const [activeStopId, setActiveStopId] = useState<string | null>(null);
  const [mapOpen, setMapOpen] = useState(false);
  const [saved, setSaved] = useState(() => (sessionId ? isTripSaved(sessionId) : false));

  useEffect(() => {
    if (raw || !sessionId) return;
    const stored = loadTrip(sessionId) ?? loadTripFromLibrary(sessionId);
    if (stored) setRaw(stored);
  }, [sessionId, raw]);

  const trip = useMemo(() => buildTripModel(raw), [raw]);
  const removedIds = useMemo(() => new Set<string>(raw?.removedStopIds ?? []), [raw]);
  const day = trip?.days.find((d) => d.day === activeDay) ?? trip?.days[0] ?? null;

  useEffect(() => setActiveStopId(null), [activeDay]);
  useEffect(() => {
    document.body.style.overflow = mapOpen ? 'hidden' : '';
    return () => {
      document.body.style.overflow = '';
    };
  }, [mapOpen]);

  const persist = (next: any) => {
    setRaw(next);
    if (sessionId) {
      saveTrip(sessionId, next);
      if (isTripSaved(sessionId)) saveTripToLibrary(sessionId, next);
    }
  };
  const setRemoved = (id: string, removed: boolean) => {
    const current: string[] = raw?.removedStopIds ?? [];
    persist({ ...raw, removedStopIds: removed ? Array.from(new Set([...current, id])) : current.filter((x) => x !== id) });
  };
  const handleSave = () => {
    if (!sessionId || !raw) return;
    if (saveTripToLibrary(sessionId, raw)) {
      setSaved(true);
    } else {
      toast.error('Your browser blocked saving. Try outside private mode.');
    }
  };

  if (!trip) {
    return (
      <div className="min-h-screen bg-paper">
        <Navbar />
        <main className="mx-auto max-w-2xl px-4 py-16 sm:px-6">
          <EmptyState
            title="This itinerary is no longer here"
            body="Trips live in the browser that planned them until saved. Plan it again, or open one from Trips."
            action={{ label: 'Plan a trip', to: '/plan' }}
          />
        </main>
      </div>
    );
  }

  const subtitle = [formatDateRange(trip.startDate, trip.endDate), trip.travelers ? pluralize(trip.travelers, 'traveler') : null, pluralize(trip.days.length, 'day')]
    .filter(Boolean)
    .join(' · ');

  const tabs: { id: Tab; label: string; count?: number }[] = [
    { id: 'itinerary', label: 'Itinerary' },
    { id: 'overview', label: 'Overview' },
    { id: 'stay', label: 'Stay', count: trip.hotels.length },
    { id: 'flights', label: 'Flights', count: trip.flights.length },
  ];

  const tripCommands: Command[] = [
    ...tabs.map((t) => ({ id: `tab-${t.id}`, label: t.label, hint: 'section', group: 'This trip', run: () => setTab(t.id) })),
    ...trip.days.map((d) => ({ id: `day-${d.day}`, label: `Day ${d.day}${d.title ? ` · ${d.title}` : ''}`, group: 'Days', run: () => { setActiveDay(d.day); setTab('itinerary'); } })),
    ...(saved ? [] : [{ id: 'save', label: 'Save trip', hint: 'to this browser', group: 'This trip', run: handleSave }]),
  ];

  const totalStops = trip.days.reduce((n, d) => n + d.stops.length, 0);
  const totalTravel = trip.days.reduce((n, d) => n + (d.totalTravelMinutes ?? 0), 0);
  const walkLegs = trip.days.reduce((n, d) => n + d.legs.filter((l) => l.mode === 'walk').length, 0);
  const totalLegs = trip.days.reduce((n, d) => n + d.legs.length, 0);

  return (
    <div className="min-h-screen bg-paper">
      <Navbar
        commands={tripCommands}
        context={
          <div className="flex min-w-0 items-center gap-2">
            <div className="min-w-0 flex-1 truncate text-[13px]">
              <span className="font-medium text-ink">{trip.destination}</span>
              {subtitle && <span className="text-muted"> · {subtitle}</span>}
            </div>
            <nav aria-label="Trip sections" className="hidden gap-0.5 md:flex">
              {tabs.map((t) => (
                <button
                  key={t.id}
                  type="button"
                  onClick={() => setTab(t.id)}
                  aria-current={tab === t.id ? 'page' : undefined}
                  className={`rounded-sm px-3 py-2 text-[13px] font-medium transition-colors ${
                    tab === t.id ? 'bg-paper-2 text-ink' : 'text-muted hover:text-ink'
                  }`}
                >
                  {t.label}
                  {typeof t.count === 'number' && t.count > 0 && <span className="mono ml-1 text-subtle">{t.count}</span>}
                </button>
              ))}
            </nav>
            <button onClick={handleSave} disabled={saved} className={`btn ${saved ? 'btn-secondary' : 'btn-primary'}`}>
              {saved ? 'Saved' : 'Save trip'}
            </button>
          </div>
        }
      />
      <nav aria-label="Trip sections" className="no-scrollbar flex gap-0.5 overflow-x-auto border-b border-rule px-3 py-2 md:hidden">
        {tabs.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => setTab(t.id)}
            aria-current={tab === t.id ? 'page' : undefined}
            className={`shrink-0 rounded-sm px-3 py-1 text-[13px] font-medium ${tab === t.id ? 'bg-paper-2 text-ink' : 'text-muted'}`}
          >
            {t.label}
          </button>
        ))}
      </nav>

      <main className="mx-auto max-w-6xl px-4 py-6 sm:px-6">
        {tab === 'itinerary' && (
          <div className="lg:grid lg:grid-cols-[minmax(0,3fr)_minmax(0,2fr)] lg:gap-6">
            <div>
              <div className="flex flex-wrap items-center justify-between gap-3">
                <DaySelector days={trip.days} activeDay={day?.day ?? 1} onSelect={setActiveDay} />
                {day && (
                  <p className="text-[12px] text-subtle">
                    {pluralize(day.stops.length, 'stop')}
                    {day.totalTravelMinutes ? ` · ~${formatMinutes(day.totalTravelMinutes)} travelling` : ''}
                  </p>
                )}
              </div>
              {day && (
                <div className="mt-4">
                  {day.title && <h2 className="mb-1 text-[length:var(--text-md)]">{day.title}</h2>}
                  {day.insights.length > 0 && (
                    <Note lead="Why this order" className="mb-3">
                      {day.insights.join(' ')}
                    </Note>
                  )}
                  <ItineraryTimeline
                    day={day}
                    activeStopId={activeStopId}
                    onSelectStop={setActiveStopId}
                    removedIds={removedIds}
                    onRemove={(id) => setRemoved(id, true)}
                    onRestore={(id) => setRemoved(id, false)}
                  />
                </div>
              )}
            </div>
            <aside className="hidden lg:block">
              <div className="sticky top-[4.5rem]">
                <MapPanel day={day} hotels={trip.hotels} activeStopId={activeStopId} onSelectStop={setActiveStopId} className="h-[calc(100vh-6rem)]" />
              </div>
            </aside>
          </div>
        )}

        {tab === 'overview' && (
          <div className="grid gap-8 lg:grid-cols-[minmax(0,3fr)_minmax(0,2fr)]">
            <div className="space-y-8">
              <dl className="kv">
                <dt>Destination</dt>
                <dd className="text-ink">{trip.destination}</dd>
                {subtitle && (
                  <>
                    <dt>When</dt>
                    <dd className="text-ink">{subtitle}</dd>
                  </>
                )}
                <dt>Stops</dt>
                <dd className="text-ink">{totalStops}</dd>
                {totalTravel > 0 && (
                  <>
                    <dt>Travel time</dt>
                    <dd className="text-ink">~{formatMinutes(totalTravel)} between stops, estimated</dd>
                  </>
                )}
                {totalLegs > 0 && (
                  <>
                    <dt>On foot</dt>
                    <dd className="text-ink">
                      {walkLegs} of {totalLegs} legs
                    </dd>
                  </>
                )}
                {trip.interests.length > 0 && (
                  <>
                    <dt>Planned around</dt>
                    <dd className="text-ink">{trip.interests.join(', ')}</dd>
                  </>
                )}
              </dl>

              <section>
                <h3 className="label mb-2">Day by day</h3>
                <ol className="list">
                  {trip.days.map((d) => (
                    <li key={d.day}>
                      <button
                        type="button"
                        onClick={() => {
                          setActiveDay(d.day);
                          setTab('itinerary');
                        }}
                        className="row row-hover w-full text-left"
                      >
                        <span className="w-12 shrink-0 text-[13px] font-medium text-ink">Day {d.day}</span>
                        <span className="min-w-0 flex-1">
                          <span className="block truncate text-[13px] text-ink">{d.title ?? pluralize(d.stops.length, 'stop')}</span>
                          <span className="block truncate text-[12px] text-muted">{d.stops.map((s) => s.name).join(' · ')}</span>
                        </span>
                      </button>
                    </li>
                  ))}
                </ol>
              </section>
            </div>
            <div className="space-y-8">
              {trip.hotels[0] && (
                <section>
                  <h3 className="label mb-2">Stay</h3>
                  <div className="list">
                    <HotelRow hotel={trip.hotels[0]} />
                  </div>
                </section>
              )}
              {trip.flights[0] && (
                <section>
                  <h3 className="label mb-2">Flight</h3>
                  <div className="list">
                    <FlightRow flight={trip.flights[0]} />
                  </div>
                </section>
              )}
              {trip.localTransport && <LocalTransportPanel transport={trip.localTransport} />}
            </div>
          </div>
        )}

        {tab === 'stay' &&
          (trip.hotels.length ? (
            <div className="list">
              {trip.hotels.map((h) => (
                <HotelRow key={h.id} hotel={h} detailed />
              ))}
            </div>
          ) : (
            <EmptyState title="No stay chosen" body="You skipped the hotel step, or nothing was available for these dates." />
          ))}

        {tab === 'flights' &&
          (trip.flights.length ? (
            <div className="list">
              {trip.flights.map((f) => (
                <FlightRow key={f.id} flight={f} />
              ))}
            </div>
          ) : (
            <EmptyState
              title="No flights in this plan"
              body={trip.origin ? 'No offers were selected for this route.' : 'Add where you are flying from when you plan.'}
            />
          ))}
      </main>

      {tab === 'itinerary' && (
        <>
          <div className="fixed inset-x-0 bottom-4 z-30 flex justify-center lg:hidden">
            <button onClick={() => setMapOpen(true)} className="btn btn-primary shadow-menu">
              <MapIcon className="h-3.5 w-3.5" />
              Map
            </button>
          </div>
          {mapOpen && (
            <div className="fixed inset-0 z-50 flex flex-col bg-paper lg:hidden" role="dialog" aria-modal="true" aria-label="Map">
              <div className="flex h-12 items-center justify-between border-b border-rule px-3">
                <p className="text-[13px] font-medium text-ink">Day {day?.day}</p>
                <button onClick={() => setMapOpen(false)} className="btn btn-ghost" aria-label="Close map">
                  <X className="h-3.5 w-3.5" />
                  Close
                </button>
              </div>
              <div className="flex-1 p-2">
                <MapPanel
                  day={day}
                  hotels={trip.hotels}
                  activeStopId={activeStopId}
                  onSelectStop={(id) => {
                    setActiveStopId(id);
                    setMapOpen(false);
                  }}
                  className="h-full"
                />
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
