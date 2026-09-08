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
        <Loader2 className="mb-6 h-7 w-7 animate-spin text-ink-subtle" strokeWidth={1.5} />
      )}

      <h2 className="font-display text-2xl text-ink">{headline}</h2>
      {destination && <p className="mt-2 text-ink-muted">Working through {destination}…</p>}

      {!!stages?.length && (
        <ul className="mt-8 w-full max-w-sm space-y-3 text-left">
          {stages.map((stage) => (
            <li key={stage.id} className="flex items-center gap-3">
              <span className="flex h-5 w-5 shrink-0 items-center justify-center">
                {stage.status === 'done' && <Check className="h-4 w-4 text-positive" />}
                {stage.status === 'active' && (
                  <Loader2 className="h-4 w-4 animate-spin text-brand" />
                )}
                {stage.status === 'pending' && (
                  <span className="h-1.5 w-1.5 rounded-full bg-line-strong" />
                )}
              </span>
              <span
                className={
                  stage.status === 'pending'
                    ? 'text-ink-subtle'
                    : stage.status === 'active'
                      ? 'text-ink'
                      : 'text-ink-muted'
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
    return <div className="flex justify-center py-24">{body}</div>;
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-[60] flex flex-col items-center justify-center bg-canvas/92 px-6 backdrop-blur-sm"
    >
      {body}
    </motion.div>
  );
}
