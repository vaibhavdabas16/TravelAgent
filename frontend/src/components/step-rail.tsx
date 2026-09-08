import { motion } from 'motion/react';
import { Check } from 'lucide-react';
import type { PlanningStep } from '../lib/planning-steps';

interface StepRailProps {
  steps: PlanningStep[];
  currentStep: number;
  onSelect: (index: number) => void;
}

/**
 * Progress rail across the top of the wizard. The old version was eight
 * anonymous dots; this labels each stage and lets you click back to a step you
 * have already completed.
 */
export function StepRail({ steps, currentStep, onSelect }: StepRailProps) {
  return (
    <nav aria-label="Planning progress" className="flex-1 min-w-0">
      <ol className="flex items-center justify-center gap-1 sm:gap-2 overflow-x-auto">
        {steps.map((step, index) => {
          const isDone = index < currentStep;
          const isCurrent = index === currentStep;

          return (
            <li key={step.id} className="flex items-center shrink-0">
              <button
                type="button"
                onClick={() => onSelect(index)}
                disabled={!isDone}
                aria-current={isCurrent ? 'step' : undefined}
                title={step.name}
                className={`group flex items-center gap-2 rounded-full px-2 py-1 transition-colors ${
                  isDone ? 'cursor-pointer hover:bg-white/10' : 'cursor-default'
                }`}
              >
                <motion.span
                  animate={{ scale: isCurrent ? 1.15 : 1 }}
                  transition={{ duration: 0.3 }}
                  className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-medium ${
                    isDone
                      ? 'bg-blue-500 text-white'
                      : isCurrent
                        ? 'bg-blue-400 text-white ring-4 ring-blue-400/25'
                        : 'bg-white/15 text-white/50'
                  }`}
                >
                  {isDone ? <Check className="w-3 h-3" /> : index + 1}
                </motion.span>
                <span
                  className={`hidden lg:inline text-xs whitespace-nowrap ${
                    isCurrent ? 'text-white' : isDone ? 'text-white/70' : 'text-white/35'
                  }`}
                >
                  {step.shortName}
                </span>
              </button>

              {index < steps.length - 1 && (
                <span className={`hidden sm:block w-3 lg:w-5 h-px mx-0.5 ${isDone ? 'bg-blue-500/60' : 'bg-white/15'}`} />
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
