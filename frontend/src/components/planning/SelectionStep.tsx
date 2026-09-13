import { useEffect, useMemo, useState } from 'react';
import { EmptyState } from '../shared/States';
import { PlaceRow, toPlaceRow } from './PlaceRow';
import { HotelRow } from '../trip/HotelCard';
import { FlightRow } from '../trip/FlightCard';
import { LocalTransportPanel } from '../trip/LocalTransportPanel';
import { buildTripModel } from '../../lib/trip-model';
import type { PlanningData } from '../../lib/planning-storage';

interface SelectionStepProps {
  stepId: string;
  planningData: PlanningData;
  onSelectionChange: (ids: string[]) => void;
}

/** Top-ranked results pre-selected when the user has chosen nothing yet. */
const DEFAULT_PICKS: Record<string, number> = { places: 3, dining: 2, activities: 2 };

const EMPTY_COPY: Record<string, { title: string; body: string }> = {
  places: { title: 'No places found for this destination', body: 'Try a more specific city, or broaden the kind of trip.' },
  accommodations: { title: 'No stays available', body: 'The hotel provider returned nothing. Carry on without one.' },
  dining: { title: 'No restaurants found', body: 'Carry on. The places you picked still make a full plan.' },
  transportation: { title: 'No flights found', body: 'Add where you are flying from on the first step, or skip this.' },
  activities: { title: 'No activities found', body: 'Skip ahead.' },
  shopping: { title: 'No markets or shops found', body: 'Skip ahead.' },
  wellness: { title: 'Nothing for wellness here', body: 'Skip ahead.' },
};

export function SelectionStep({ stepId, planningData, onSelectionChange }: SelectionStepProps) {
  const stored: string[] | undefined = planningData.selectedItems?.[stepId];

  // The model filters hotels/flights to the selected ones; here we want all.
  const model = useMemo(
    () =>
      buildTripModel({
        ...planningData,
        selectedItems: {
          accommodations: (planningData.recommended_hotels ?? []).map((h: any) => String(h.hotel_id ?? h.id ?? h.provider_id)),
          transportation: (planningData.recommended_flights ?? []).map((f: any) => String(f.offer_id ?? f.id ?? f.provider_id)),
        },
        itinerary: [],
      }),
    [planningData]
  );

  const places = useMemo(() => {
    const key = stepId === 'places' ? 'pois' : stepId;
    const raw: any[] = (planningData as any)[key] ?? [];
    return raw.map(toPlaceRow).filter((p): p is NonNullable<typeof p> => !!p);
  }, [planningData, stepId]);

  const allIds = useMemo(() => {
    if (stepId === 'accommodations') return model?.hotels.map((h) => h.id) ?? [];
    if (stepId === 'transportation') return model?.flights.map((f) => f.id) ?? [];
    return places.map((p) => p.id);
  }, [stepId, model, places]);

  const [selected, setSelected] = useState<string[]>(() => {
    if (stored && stored.length) return stored.filter((id) => allIds.includes(id));
    return allIds.slice(0, DEFAULT_PICKS[stepId] ?? 0);
  });

  // Report pre-selected defaults once so "Continue" submits them.
  useEffect(() => {
    if (!stored || !stored.length) onSelectionChange(selected);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const toggle = (id: string, single = false) => {
    const next = selected.includes(id) ? selected.filter((x) => x !== id) : single ? [id] : [...selected, id];
    setSelected(next);
    onSelectionChange(next);
  };

  const empty = EMPTY_COPY[stepId];

  if (stepId === 'accommodations') {
    const hotels = model?.hotels ?? [];
    if (!hotels.length) return <EmptyState title={empty.title} body={empty.body} />;
    return (
      <div className="list" role="radiogroup" aria-label="Stays">
        {hotels.map((h, i) => (
          <HotelRow key={h.id} hotel={h} recommended={i === 0} selected={selected.includes(h.id)} onToggle={() => toggle(h.id, true)} />
        ))}
      </div>
    );
  }

  if (stepId === 'transportation') {
    const flights = model?.flights ?? [];
    return (
      <div className="space-y-8">
        <section>
          <h2 className="label mb-2">Flights</h2>
          {flights.length ? (
            <div className="list">
              {flights.map((f, i) => (
                <FlightRow key={f.id} flight={f} recommended={i === 0} selected={selected.includes(f.id)} onToggle={() => toggle(f.id)} />
              ))}
            </div>
          ) : (
            <EmptyState title={empty.title} body={empty.body} />
          )}
        </section>
        {model?.localTransport && <LocalTransportPanel transport={model.localTransport} />}
      </div>
    );
  }

  if (!places.length) return <EmptyState title={empty.title} body={empty.body} />;
  const recommendedCount = DEFAULT_PICKS[stepId] ?? 0;
  return (
    <div className="list">
      {places.map((p, i) => (
        <PlaceRow key={p.id} place={p} recommended={i < recommendedCount} selected={selected.includes(p.id)} onToggle={() => toggle(p.id)} />
      ))}
    </div>
  );
}
