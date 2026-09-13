import type { ReactNode } from 'react';
import { Link } from 'react-router-dom';
import { Loader2, Star } from 'lucide-react';

interface EmptyStateProps {
  title: string;
  body?: string;
  action?: { label: string; to?: string; onClick?: () => void };
  children?: ReactNode;
}

export function EmptyState({ title, body, action, children }: EmptyStateProps) {
  return (
    <div className="rounded-md border border-dashed border-rule-2 px-5 py-10 text-center">
      <p className="text-[14px] font-medium text-ink">{title}</p>
      {body && <p className="mx-auto mt-1 max-w-sm text-[13px] text-muted">{body}</p>}
      {children}
      {action &&
        (action.to ? (
          <Link to={action.to} className="btn btn-primary mt-4 no-underline">
            {action.label}
          </Link>
        ) : (
          <button onClick={action.onClick} className="btn btn-primary mt-4">
            {action.label}
          </button>
        ))}
    </div>
  );
}

interface ErrorStateProps {
  title: string;
  body?: string;
  onRetry?: () => void;
  secondary?: { label: string; to?: string; onClick?: () => void };
}

export function ErrorState({ title, body, onRetry, secondary }: ErrorStateProps) {
  return (
    <div role="alert" className="rounded-md border border-critical/30 bg-critical-soft px-4 py-4">
      <p className="text-[14px] font-medium text-ink">{title}</p>
      {body && <p className="mt-1 text-[13px] text-muted">{body}</p>}
      <div className="mt-3 flex flex-wrap gap-2">
        {onRetry && (
          <button onClick={onRetry} className="btn btn-secondary">
            Try again
          </button>
        )}
        {secondary &&
          (secondary.to ? (
            <Link to={secondary.to} className="btn btn-ghost no-underline">
              {secondary.label}
            </Link>
          ) : (
            <button onClick={secondary.onClick} className="btn btn-ghost">
              {secondary.label}
            </button>
          ))}
      </div>
    </div>
  );
}

export function InlineSpinner({ label }: { label?: string }) {
  return (
    <div className="flex items-center gap-2 py-10 text-[13px] text-muted" role="status">
      <Loader2 className="h-4 w-4 animate-spin" />
      {label}
    </div>
  );
}

interface RatingProps {
  value: number | null | undefined;
  count?: number | null;
  className?: string;
}

/** Nothing rendered when there is no rating. */
export function Rating({ value, count, className = '' }: RatingProps) {
  if (typeof value !== 'number' || !isFinite(value)) return null;
  return (
    <span className={`inline-flex items-center gap-1 text-[12px] text-ink ${className}`}>
      <Star className="h-3 w-3 fill-current" aria-hidden="true" />
      <span className="font-medium">{value.toFixed(1)}</span>
      {typeof count === 'number' && count > 0 && <span className="text-subtle">· {count.toLocaleString()}</span>}
    </span>
  );
}
