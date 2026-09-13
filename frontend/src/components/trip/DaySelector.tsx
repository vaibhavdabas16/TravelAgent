import { formatDate } from '../../lib/format';
import type { TripDay } from '../../lib/trip-model';

interface DaySelectorProps {
  days: TripDay[];
  activeDay: number;
  onSelect: (day: number) => void;
}

/** Segmented text control. Small, scrollable. */
export function DaySelector({ days, activeDay, onSelect }: DaySelectorProps) {
  return (
    <nav aria-label="Days" className="no-scrollbar overflow-x-auto">
      <ol className="inline-flex rounded-md border border-rule bg-paper p-0.5">
        {days.map((d) => {
          const active = d.day === activeDay;
          const date = formatDate(d.date, { weekday: 'short', day: 'numeric' });
          return (
            <li key={d.day} className="shrink-0">
              <button
                type="button"
                aria-current={active ? 'page' : undefined}
                onClick={() => onSelect(d.day)}
                className={`flex h-7 items-center gap-2 rounded-sm px-3 text-[13px] transition-colors ${
                  active ? 'bg-accent font-medium text-paper' : 'text-muted hover:bg-paper-2 hover:text-ink'
                }`}
              >
                Day {d.day}
                {date && <span className={active ? 'text-paper/70' : 'text-subtle'}>{date}</span>}
              </button>
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
