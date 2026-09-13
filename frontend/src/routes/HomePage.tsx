import { useNavigate } from 'react-router-dom';
import { Navbar } from '../components/shared/Navbar';
import { Footer } from '../components/shared/Footer';
import { TripPrompt } from '../components/planning/TripPrompt';
import { Apparatus } from '../components/landing/Apparatus';
import { MeterStrip } from '../components/landing/MeterStrip';
import { SystemMap } from '../components/landing/SystemMap';

/**
 * Marquee Hero, Lumen night. The fold is the statement and the apparatus;
 * the meter strip rules it off. Below: the one action, the pipeline, three
 * honest numbers, a closing line.
 */
export function HomePage() {
  const navigate = useNavigate();
  return (
    <div className="flex min-h-screen flex-col bg-paper">
      <Navbar />
      <main className="flex-1">
        {/* 01 · fold */}
        <section className="blueprint">
          <div className="mx-auto grid max-w-6xl items-center gap-10 px-4 pb-16 pt-8 sm:px-6 sm:pb-24 sm:pt-12 lg:min-h-[min(calc(100vh-5rem),52rem)] lg:grid-cols-[minmax(0,6fr)_minmax(0,5fr)] lg:gap-16">
            <div className="reveal" style={{ ['--i' as string]: 0 }}>
              <p className="label">01 · agent</p>
              <h1 className="lc mt-6 text-[length:var(--text-display)]">
                say the trip. it <span className="verb">routes</span> the days.
              </h1>
              <p className="lc mt-6 max-w-[48ch] text-[length:var(--text-md)] text-ink-2">
                seven agents turn one sentence into real places, a stay, flights and a day-by-day route with the
                travel time between every stop — and say why.
              </p>
            </div>
            <div className="reveal" style={{ ['--i' as string]: 1 }}>
              <Apparatus />
            </div>
          </div>
          <MeterStrip />
        </section>

        {/* 02 · the one action */}
        <section className="mx-auto max-w-6xl px-4 pb-20 pt-16 sm:px-6 sm:pb-28 sm:pt-24">
          <div className="grid gap-8 lg:grid-cols-[minmax(0,5fr)_minmax(0,7fr)] lg:gap-16">
            <div>
              <p className="label">02 · brief</p>
              <h2 className="lc mt-4 text-[length:var(--text-2xl)]">start with a sentence.</h2>
              <p className="lc mt-3 max-w-[40ch] text-[length:var(--text-sm)] text-muted">
                where, when, who and what you like. what it reads is shown back to you before anything runs.
              </p>
            </div>
            <div className="lg:pt-8">
              <TripPrompt onSubmit={(q) => navigate('/plan', { state: { query: q } })} />
            </div>
          </div>
        </section>

        {/* 03 · pipeline */}
        <section className="border-t border-rule">
          <div className="mx-auto max-w-6xl px-4 pb-20 pt-16 sm:px-6 sm:pb-28 sm:pt-24">
            <p className="label">03 · pipeline</p>
            <h2 className="lc mt-4 max-w-[24ch] text-[length:var(--text-2xl)]">what runs when you press plan.</h2>
            <p className="lc mt-3 max-w-[52ch] text-[length:var(--text-sm)] text-muted">
              each stage is a separate agent or provider behind an interface, so any one of them can be swapped —
              the places provider already has been.
            </p>
            <div className="mt-10">
              <SystemMap />
            </div>
          </div>
        </section>

        {/* 04 · by the numbers — three honest counts from the codebase */}
        <section className="border-t border-rule">
          <div className="mx-auto max-w-6xl px-4 pb-16 pt-16 sm:px-6 sm:pt-24">
            <p className="label">04 · by the numbers</p>
            <dl className="mt-8 grid divide-y divide-rule sm:grid-cols-3 sm:divide-x sm:divide-y-0">
              {[
                ['7', 'pipeline stages', 'brief → discover → rank → stay → transport → route → itinerary'],
                ['3', 'provider interfaces', 'RouteProvider · AccommodationProvider · FlightProvider'],
                ['20', 'planning endpoints', 'FastAPI · /api/v2/planning/*'],
              ].map(([n, label, hint]) => (
                <div key={label} className="py-6 sm:px-6 sm:py-2 first:sm:pl-0 last:sm:pr-0">
                  <dd className="display text-[length:var(--text-stat)] leading-none text-ink">{n}</dd>
                  <dt className="label mt-3">{label}</dt>
                  <dd className="mono mt-2 text-subtle">{hint}</dd>
                </div>
              ))}
            </dl>
          </div>
        </section>
      </main>
      <Footer />
    </div>
  );
}
