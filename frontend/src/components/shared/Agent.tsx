import type { ReactNode } from 'react';

interface NoteProps {
  children: ReactNode;
  /** Short lead, e.g. "Why this order". */
  lead?: string;
  className?: string;
}

/**
 * A quiet annotation explaining a decision the system made. Content must come
 * from real data or real rules; it is product information, not a voice.
 */
export function Note({ children, lead, className = '' }: NoteProps) {
  return (
    <p className={`note ${className}`} role="note">
      {lead && <span className="font-medium text-ink">{lead}. </span>}
      {children}
    </p>
  );
}
