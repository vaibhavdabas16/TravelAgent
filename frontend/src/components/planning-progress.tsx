import { motion } from 'motion/react';
import { Check, Loader2 } from 'lucide-react';

export interface ProgressStage {
  id: string;
  label: string;
  status: 'pending' | 'active' | 'done';
}

interface PlanningProgressProps {
  headline: string;
  destination?: string | null;
  /** Render in the page body instead of as a full-screen overlay. */
  inline?: boolean;
  /**
   * Named stages from the server. When absent we show an indeterminate
   * spinner — honest about not knowing how far along the work is, rather than
   * animating a fake progress bar.
   */
  stages?: ProgressStage[];
}

export function PlanningProgress({ headline, destination, inline, stages }: PlanningProgressProps) {
  const body = (
    <div className="flex flex-col items-center text-center">
      {!stages?.length && (
        <div className="w-14 h-14 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mb-6" />
      )}

      <h2 className="text-2xl font-bold text-white mb-2">{headline}</h2>
      {destination && <p className="text-white/70">Working through {destination}…</p>}

      {!!stages?.length && (
        <ul className="mt-8 space-y-3 text-left w-full max-w-sm">
          {stages.map((stage) => (
            <li key={stage.id} className="flex items-center gap-3">
              <span className="w-5 h-5 flex items-center justify-center shrink-0">
                {stage.status === 'done' && <Check className="w-4 h-4 text-green-400" />}
                {stage.status === 'active' && <Loader2 className="w-4 h-4 text-blue-400 animate-spin" />}
                {stage.status === 'pending' && <span className="w-2 h-2 rounded-full bg-white/25" />}
              </span>
              <span
                className={
                  stage.status === 'pending'
                    ? 'text-white/40'
                    : stage.status === 'active'
                      ? 'text-white'
                      : 'text-white/70'
                }
              >
                {stage.label}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );

  if (inline) {
    return <div className="py-24 flex justify-center">{body}</div>;
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-[60] bg-black/80 backdrop-blur-md flex flex-col items-center justify-center px-6"
    >
      {body}
    </motion.div>
  );
}
