import { Check, Loader2 } from 'lucide-react';

export interface ProgressStage {
  id: string;
  label: string;
  status: 'pending' | 'active' | 'done';
}

interface PlanningProgressProps {
  headline: string;
  destination?: string | null;
  inline?: boolean;
  /** Named stages from the server; without them, one honest indeterminate line. */
  stages?: ProgressStage[];
}

const STAGE_COPY: Record<string, string> = {
  collect: 'Reading your picks',
  cluster: 'Grouping stops into days',
  transport: 'Working out travel between stops',
};

export function PlanningProgress({ headline, destination, inline, stages }: PlanningProgressProps) {
  const body = (
    <div className="w-full max-w-xs">
      <p className="text-[14px] font-medium text-ink">{headline}</p>
      {destination && <p className="text-[13px] text-muted">{destination}</p>}
      {stages?.length ? (
        <ol className="mt-4 space-y-2" aria-live="polite">
          {stages.map((s) => (
            <li key={s.id} className="flex items-center gap-2 text-[13px]">
              <span className="flex h-4 w-4 items-center justify-center" aria-hidden="true">
                {s.status === 'done' && <Check className="h-3.5 w-3.5 text-positive" />}
                {s.status === 'active' && <Loader2 className="h-3.5 w-3.5 animate-spin text-ink" />}
                {s.status === 'pending' && <span className="h-1.5 w-1.5 rounded-full bg-rule-2" />}
              </span>
              <span className={s.status === 'pending' ? 'text-subtle' : s.status === 'active' ? 'text-ink' : 'text-muted'}>
                <span className="sr-only">{s.status === 'done' ? 'Done: ' : s.status === 'active' ? 'In progress: ' : 'Waiting: '}</span>
                {STAGE_COPY[s.id] ?? s.label}
              </span>
            </li>
          ))}
        </ol>
      ) : (
        <p className="mt-3 flex items-center gap-2 text-[13px] text-muted" role="status">
          <Loader2 className="h-3.5 w-3.5 animate-spin" />
          This takes a moment.
        </p>
      )}
    </div>
  );
  if (inline) return <div className="py-12">{body}</div>;
  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center bg-paper/95 px-6">
      <div className="rounded-md border border-rule bg-paper p-5 shadow-menu">{body}</div>
    </div>
  );
}
