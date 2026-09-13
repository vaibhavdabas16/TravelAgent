/** Ft5 · Statement. One closing line, then the wordmark and a credit. */
export function Footer() {
  return (
    <footer className="mx-auto w-full max-w-6xl px-4 pb-10 pt-16 sm:px-6 sm:pt-24">
      <p className="display lc max-w-[28ch] text-[length:var(--text-display-s)] text-ink">
        tell it the trip. read why it <span className="verb">chose</span>.
      </p>
      <div className="mt-8 flex flex-wrap items-baseline justify-between gap-2 border-t border-rule pt-3">
        <span className="display lc text-[length:var(--text-md)] text-ink">voyage</span>
        <span className="label">live places · stays · flights — times are estimates, nothing is invented</span>
      </div>
    </footer>
  );
}
