import { useState } from 'react';

interface PhotoProps {
  src: string | null | undefined;
  alt: string;
  className?: string;
}

/**
 * Small thumbnail. Renders a flat placeholder when there is no photo — never
 * a stock image standing in for a real place.
 */
export function Photo({ src, alt, className = 'h-10 w-10' }: PhotoProps) {
  const [failed, setFailed] = useState(false);
  const show = src && !failed;
  return (
    <div className={`shrink-0 overflow-hidden rounded-sm bg-paper-2 ${className}`} aria-hidden={!show}>
      {show && <img src={src} alt={alt} loading="lazy" onError={() => setFailed(true)} className="h-full w-full object-cover" />}
    </div>
  );
}
