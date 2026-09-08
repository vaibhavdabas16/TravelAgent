/**
 * What the product actually does.
 *
 * The previous copy advertised "seamless collaboration", shared itineraries and
 * voting on activities — none of which exist. These four describe the agents
 * and solvers that are genuinely wired up.
 */
const features = [
  {
    id: 1,
    eyebrow: 'Discovery',
    title: 'Places chosen for this trip, not ranked by popularity',
    description:
      'Candidates come from Google Places and a vector search over previous trips, then get filtered against what you actually asked for — so a three-day beach trip stops proposing the cathedral two hours inland.',
  },
  {
    id: 2,
    eyebrow: 'Routing',
    title: 'A schedule that survives contact with a map',
    description:
      'Your days are solved as a routing problem using real travel times and real opening hours. Nothing reaches the itinerary that you could not physically get to in time, and nothing is scheduled while it is shut.',
  },
  {
    id: 3,
    eyebrow: 'Prices',
    title: 'Live flights and hotels, scored against your plan',
    description:
      'Offers are quoted from Amadeus at current prices. Hotels are ranked partly on how close they sit to the places you picked, so the trip does not open with an hour in a taxi.',
  },
  {
    id: 4,
    eyebrow: 'Budget',
    title: 'A running total, before you commit to anything',
    description:
      'Every choice updates an estimate against the budget you set at the start — accommodation, entry, food and transport — so the number at the end is not a surprise.',
  },
];

export function FeatureImageSection() {
  return (
    <section className="bg-surface">
      <div className="mx-auto max-w-7xl px-6 py-24">
        <div className="max-w-2xl">
          <p className="label-eyebrow">How it works</p>
          <h2 className="mt-4 font-display text-4xl leading-tight text-ink">
            Less a chatbot with a map, more an itinerary that holds up.
          </h2>
        </div>

        <div className="mt-16 grid grid-cols-1 gap-x-16 gap-y-14 md:grid-cols-2">
          {features.map((feature, index) => (
            <div key={feature.id} className="border-t border-line pt-7">
              <div className="flex items-baseline gap-4">
                <span className="tabular text-sm text-ink-subtle">
                  {String(index + 1).padStart(2, '0')}
                </span>
                <p className="label-eyebrow">{feature.eyebrow}</p>
              </div>
              <h3 className="mt-4 font-display text-2xl leading-snug text-ink">
                {feature.title}
              </h3>
              <p className="mt-3 leading-relaxed text-ink-muted">{feature.description}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="border-t border-line bg-canvas">
        <div className="mx-auto flex max-w-7xl flex-col gap-3 px-6 py-10 sm:flex-row sm:items-center sm:justify-between">
          <p className="font-display text-lg text-ink">Voyage</p>
          <p className="text-sm text-ink-subtle">
            © {new Date().getFullYear()} Voyage · Trip data from Google Maps, Amadeus and
            SerpAPI
          </p>
        </div>
      </div>
    </section>
  );
}
