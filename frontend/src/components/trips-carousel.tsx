import { Calendar, MapPin, Users, Star } from 'lucide-react';

const recentTrips = [
  {
    id: 1,
    title: "Tokyo Nights",
    location: "Tokyo, Japan",
    duration: "7 days",
    travelers: 2,
    rating: 4.9,
    price: "$2,850"
  },
  {
    id: 2,
    title: "Taj Mahal Sunrise",
    location: "Agra, India",
    duration: "5 days",
    travelers: 2,
    rating: 4.8,
    price: "$2,200"
  },
  {
    id: 3,
    title: "Bali Temples",
    location: "Bali, Indonesia",
    duration: "10 days",
    travelers: 4,
    rating: 4.7,
    price: "$1,950"
  },
  {
    id: 4,
    title: "NYC Adventures",
    location: "New York, USA",
    duration: "4 days",
    travelers: 1,
    rating: 4.6,
    price: "$1,650"
  },
  {
    id: 5,
    title: "Santorini Dreams",
    location: "Santorini, Greece",
    duration: "6 days",
    travelers: 2,
    rating: 4.9,
    price: "$2,400"
  },
  {
    id: 6,
    title: "Iceland Aurora",
    location: "Reykjavik, Iceland",
    duration: "8 days",
    travelers: 3,
    rating: 4.8,
    price: "$3,200"
  }
];

export function TripsCarousel() {
  return (
    <section className="border-t border-line bg-canvas py-20">
      <div className="mx-auto max-w-7xl px-6">
        <div className="flex items-end justify-between gap-8 pb-10">
          <div className="max-w-xl">
            <h2 className="font-display text-4xl text-ink">Recent trips</h2>
            <p className="mt-3 text-ink-muted">
              Itineraries planned for other travellers, with the routes and costs they were
              given.
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-px overflow-hidden rounded-lg border border-line bg-line sm:grid-cols-2 lg:grid-cols-3">
          {recentTrips.map((trip) => (
            <article
              key={trip.id}
              className="group flex cursor-pointer flex-col bg-surface transition-colors hover:bg-sunken/50"
            >
              <div className="flex flex-1 flex-col gap-3 p-5">
                <div className="flex items-baseline justify-between gap-3">
                  <h3 className="font-display text-xl text-ink">{trip.title}</h3>
                  <span className="tabular shrink-0 text-sm font-medium text-ink">{trip.price}</span>
                </div>

                <div className="flex items-center gap-1.5 text-sm text-ink-muted">
                  <MapPin className="h-3.5 w-3.5 text-ink-subtle" />
                  <span>{trip.location}</span>
                </div>

                <div className="mt-auto flex items-center gap-4 border-t border-line pt-3 text-sm text-ink-muted">
                  <span className="inline-flex items-center gap-1.5">
                    <Calendar className="h-3.5 w-3.5 text-ink-subtle" />
                    {trip.duration}
                  </span>
                  <span className="inline-flex items-center gap-1.5">
                    <Users className="h-3.5 w-3.5 text-ink-subtle" />
                    {trip.travelers}
                  </span>
                  <span className="tabular ml-auto inline-flex items-center gap-1 text-ink">
                    <Star className="h-3.5 w-3.5 fill-current text-ink-subtle" />
                    {trip.rating}
                  </span>
                </div>
              </div>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
