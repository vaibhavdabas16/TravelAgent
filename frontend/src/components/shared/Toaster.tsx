import { Toaster as Sonner } from 'sonner';

/** Toasts in the app palette. Kept quiet: bottom-centre, no icons shouting. */
export function Toaster() {
  return (
    <Sonner
      position="bottom-center"
      toastOptions={{
        style: {
          background: 'var(--color-paper)',
          color: 'var(--color-ink)',
          border: '1px solid var(--color-rule)',
          boxShadow: 'var(--shadow-menu)',
          borderRadius: 'var(--radius-sm)',
          fontFamily: 'var(--font-sans)',
        },
      }}
    />
  );
}
