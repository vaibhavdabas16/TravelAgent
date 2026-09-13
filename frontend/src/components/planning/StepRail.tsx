import type { PlanningStep } from '../../lib/planning-steps';

interface StepRailProps {
  steps: PlanningStep[];
  currentStep: number;
  onSelect: (index: number) => void;
}

/**
 * Text breadcrumb of the planner. Completed steps are links; steps ahead are
 * inert because their searches depend on selections not yet made.
 */
export function StepRail({ steps, currentStep, onSelect }: StepRailProps) {
  const items = [...steps.map((s) => s.shortName), 'Itinerary'];
  return (
    <nav aria-label="Planning progress" className="no-scrollbar min-w-0 flex-1 overflow-x-auto">
      <ol className="flex items-center gap-1 text-[12px]">
        {items.map((label, i) => {
          const done = i < currentStep;
          const current = i === currentStep;
          return (
            <li key={label} className="flex shrink-0 items-center gap-1">
              <button
                type="button"
                disabled={!done}
                onClick={() => onSelect(i)}
                aria-current={current ? 'step' : undefined}
                className={`rounded-sm px-2 py-0.5 ${
                  current ? 'bg-paper-2 font-medium text-ink' : done ? 'text-muted hover:text-ink' : 'text-subtle'
                }`}
              >
                {label}
              </button>
              {i < items.length - 1 && <span className="text-subtle">/</span>}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
