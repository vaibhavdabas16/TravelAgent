/**
 * The pipeline as a ledger: one rail, seven rows, four columns — stage, what
 * it does, what it calls, what it returns. Every value is read from
 * backend/app (routes_planning.py response keys, agents, providers).
 */
const ROWS: { n: string; name: string; does: string; via: string; out: string }[] = [
  { n: '01', name: 'brief', does: 'One sentence becomes structured constraints, shown back for correction before anything runs.', via: 'trip-parser.ts · POST /v2/planning/start', out: 'session_id' },
  { n: '02', name: 'discover', does: 'Candidate places near the destination, geocoded and de-duplicated.', via: 'discovery.py · Foursquare or Google Places', out: 'pois[≤10] · summary' },
  { n: '03', name: 'rank', does: 'Quality, popularity, price fit and semantic match scored per place; the reason is kept and shown.', via: 'scoring.py · Gemini 2.5 Flash · vector store', out: 'ai_score · recommendation_reason' },
  { n: '04', name: 'stay', does: 'Hotels scored on price and the average commute to the places you picked.', via: 'accommodation.py · Places lodging · RouteProvider', out: 'hotels[≤10] · avg_commute_time_minutes' },
  { n: '05', name: 'transport', does: 'Flights when you gave an origin; walk, transit and drive compared for the city.', via: 'transport.py · Amadeus · route matrix', out: 'transport_options.flights · .local' },
  { n: '06', name: 'route', does: 'Stops grouped into days by geography; every leg gets a mode, a time and a distance.', via: 'itinerary.py · Gemini clustering · haversine', out: 'itinerary[].stops · transport_legs' },
  { n: '07', name: 'itinerary', does: 'Streamed stage by stage so the wait shows real progress, then saved.', via: 'POST /itinerary/stream · SSE', out: 'stages · stage · complete' },
];

export function SystemMap() {
  return (
    <ol className="ledger" aria-label="Pipeline stages">
      <li className="ledger__row !border-t-0 hidden py-2 md:grid" aria-hidden="true">
        <span />
        <span className="label">stage</span>
        <span className="label">does</span>
        <span className="label">returns</span>
      </li>
      {ROWS.map((r) => (
        <li key={r.n} className="ledger__row">
          <span className="ledger__node">{r.n}</span>
          <span className="ledger__name">
            <span className="display lc block text-[length:var(--text-lg)] text-ink">{r.name}</span>
            <span className="mono block text-subtle md:hidden">{r.via}</span>
          </span>
          <span className="ledger__does">
            <span className="block text-[length:var(--text-sm)] text-ink-2">{r.does}</span>
            <span className="mono mt-1 hidden text-subtle md:block">{r.via}</span>
          </span>
          <span className="ledger__out mono text-muted">{r.out}</span>
        </li>
      ))}
    </ol>
  );
}
