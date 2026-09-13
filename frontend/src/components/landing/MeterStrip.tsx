/**
 * Lumen meter strip. A printed readout, not a live feed: 64 ticks on a
 * gaussian envelope, mono labels at each end naming real counts from the
 * backend (20 planning endpoints, 3 provider interfaces).
 */
const TICKS = Array.from({ length: 64 }, (_, i) => {
  const x = (i - 31.5) / 12;
  const g = Math.exp(-(x * x) / 2);
  const ripple = 0.5 + 0.5 * Math.sin(i * 0.9);
  return 0.18 + 0.82 * g * (0.55 + 0.45 * ripple);
});

export function MeterStrip() {
  return (
    <aside className="meter" aria-label="System readout">
      <p className="label">endpoints · 20</p>
      <div className="meter__bars" aria-hidden="true">
        {TICKS.map((h, i) => (
          <span key={i} style={{ height: `${Math.round(h * 100)}%`, opacity: 0.35 + h * 0.65 }} />
        ))}
      </div>
      <p className="label">providers · 03</p>
    </aside>
  );
}
