import { useState } from 'react';
import { ArrowRight } from 'lucide-react';

interface HeroSectionProps {
  onStartPlanning?: (data?: any) => void;
  onViewTripPlan?: (data?: any) => void;
}

/**
 * Landing hero.
 *
 * The previous version layered fifty animated particles, twelve floating
 * icons, a mouse-tracked spring parallax, a typewriter headline and a glowing
 * gradient title over a parallax photo carousel. It read as a demo reel. This
 * one is typographic: the page has one job, which is to take a destination.
 */

const SUGGESTIONS = ['Kyoto', 'Lisbon', 'Goa', 'Reykjavík', 'Mexico City'];

export function HeroSection({ onStartPlanning }: HeroSectionProps) {
  const [query, setQuery] = useState('');

  const start = (value: string) => {
    const trimmed = value.trim();
    if (!trimmed) return;
    onStartPlanning?.({ query: trimmed, destination: trimmed });
  };

  return (
    <section className="border-b border-line bg-canvas">
      <div className="mx-auto max-w-7xl px-6 pb-24 pt-40">
        <div className="max-w-3xl">
          <p className="label-eyebrow">Trip planning, end to end</p>

          <h1 className="mt-5 font-display text-6xl leading-[1.05] text-ink sm:text-7xl">
            Every trip,
            <br />
            planned properly.
          </h1>

          <p className="mt-7 max-w-xl text-lg leading-relaxed text-ink-muted">
            Tell us where you're going. We'll find the places worth your time, work out a
            realistic route between them, and price the whole thing before you book.
          </p>

          <form
            onSubmit={(e) => {
              e.preventDefault();
              start(query);
            }}
            className="mt-10 flex max-w-xl flex-col gap-3 sm:flex-row"
          >
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              type="text"
              placeholder="Where are you going?"
              aria-label="Destination"
              className="h-12 flex-1 rounded-md border border-line-strong bg-surface px-4 text-base text-ink placeholder:text-ink-subtle focus:border-brand focus:outline-none"
            />
            <button
              type="submit"
              disabled={!query.trim()}
              className="inline-flex h-12 items-center justify-center gap-2 rounded-md bg-brand px-6 text-sm font-medium text-white transition-colors hover:bg-brand-hover disabled:cursor-not-allowed disabled:opacity-40"
            >
              Start planning
              <ArrowRight className="h-4 w-4" />
            </button>
          </form>

          <div className="mt-5 flex flex-wrap items-center gap-x-2 gap-y-2">
            <span className="mr-1 text-sm text-ink-subtle">Try</span>
            {SUGGESTIONS.map((place) => (
              <button
                key={place}
                type="button"
                onClick={() => start(place)}
                className="rounded-full border border-line px-3 py-1 text-sm text-ink-muted transition-colors hover:border-brand-line hover:bg-brand-soft hover:text-brand"
              >
                {place}
              </button>
            ))}
          </div>
        </div>

        {/* Three claims the product can actually back up. */}
        <dl className="mt-24 grid max-w-4xl grid-cols-1 gap-px overflow-hidden rounded-lg border border-line bg-line sm:grid-cols-3">
          <div className="bg-surface p-6">
            <dt className="label-eyebrow">Routing</dt>
            <dd className="mt-2 text-sm leading-relaxed text-ink-muted">
              Days solved against real travel times and opening hours, not a list in
              alphabetical order.
            </dd>
          </div>
          <div className="bg-surface p-6">
            <dt className="label-eyebrow">Live prices</dt>
            <dd className="mt-2 text-sm leading-relaxed text-ink-muted">
              Flights and hotels quoted from current offers, with hotels ranked on distance
              to your plan.
            </dd>
          </div>
          <div className="bg-surface p-6">
            <dt className="label-eyebrow">One budget</dt>
            <dd className="mt-2 text-sm leading-relaxed text-ink-muted">
              A running total across stay, food, entry and transport, kept against the
              number you set.
            </dd>
          </div>
        </dl>
      </div>
    </section>
  );
}
