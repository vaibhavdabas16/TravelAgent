import { Check } from 'lucide-react';
import type { PlanningStep } from '../lib/planning-steps';

interface StepRailProps {
  steps: PlanningStep[];
  currentStep: number;
  onSelect: (index: number) => void;
}

/**
 * Progress rail across the top of the wizard. Completed steps are clickable;
 * steps ahead are not, because the searches behind them depend on selections
 * that have not been made yet.
 */
export function StepRail({ steps, currentStep, onSelect }: StepRailProps) {
  return (
    <nav aria-label="Planning progress" className="min-w-0 flex-1">
      <ol className="flex items-center justify-center gap-0.5 overflow-x-auto sm:gap-1">
        {steps.map((step, index) => {
          const isDone = index < currentStep;
          const isCurrent = index === currentStep;

          return (
            <li key={step.id} className="flex shrink-0 items-center">
              <button
                type="button"
                onClick={() => onSelect(index)}
                disabled={!isDone}
                aria-current={isCurrent ? 'step' : undefined}
                title={step.name}
                className={`flex items-center gap-2 rounded-md px-2 py-1 transition-colors ${
                  isDone ? 'cursor-pointer hover:bg-sunken' : 'cursor-default'
                }`}
              >
                <span
                  className={`tabular flex h-5 w-5 items-center justify-center rounded-full text-[10px] font-semibold transition-colors ${
                    isDone
                      ? 'bg-brand text-white'
                      : isCurrent
                        ? 'bg-brand text-white ring-4 ring-brand-soft'
                        : 'bg-sunken text-ink-subtle'
                  }`}
                >
                  {isDone ? <Check className="h-3 w-3" /> : index + 1}
                </span>
                <span
                  className={`hidden whitespace-nowrap text-xs lg:inline ${
                    isCurrent ? 'font-medium text-ink' : isDone ? 'text-ink-muted' : 'text-ink-subtle'
                  }`}
                >
                  {step.shortName}
                </span>
              </button>

              {index < steps.length - 1 && (
                <span
                  aria-hidden="true"
                  className={`mx-0.5 hidden h-px w-3 sm:block lg:w-5 ${
                    isDone ? 'bg-brand-line' : 'bg-line'
                  }`}
                />
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
