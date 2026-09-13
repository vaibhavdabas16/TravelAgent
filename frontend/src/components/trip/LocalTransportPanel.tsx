import { formatMinutes } from '../../lib/format';
import type { LocalTransport } from '../../lib/trip-model';

const LABEL: Record<string, string> = { walking: 'Walking', transit: 'Public transit', driving: 'Taxi or car' };

/** Average time from the hotel to your stops by mode, from the route provider. */
export function LocalTransportPanel({ transport }: { transport: LocalTransport }) {
  if (!transport.modes.length && !transport.recommendedMode) return null;
  const rec = transport.recommendedMode ? LABEL[transport.recommendedMode] ?? transport.recommendedMode : null;
  return (
    <section aria-labelledby="local-transport-title">
      <h3 id="local-transport-title" className="label mb-2">
        Getting around
      </h3>
      <div className="list">
        {transport.modes.map(({ mode, avgMinutes }) => (
          <div key={mode} className="row">
            <span className="flex-1 text-[13px] text-ink">
              {LABEL[mode] ?? mode}
              {transport.recommendedMode === mode && <span className="ml-2 text-[12px] text-subtle">Recommended</span>}
            </span>
            <span className="text-[13px] text-muted">~{formatMinutes(avgMinutes)} avg</span>
          </div>
        ))}
        {transport.estimatedDailyCost !== null && (
          <div className="row">
            <span className="flex-1 text-[13px] text-muted">Estimated daily cost</span>
            <span className="text-[13px] text-muted">~${transport.estimatedDailyCost}</span>
          </div>
        )}
      </div>
      {rec && <p className="mt-2 text-[12px] text-subtle">{rec} is the practical default for where your stops are.</p>}
    </section>
  );
}
