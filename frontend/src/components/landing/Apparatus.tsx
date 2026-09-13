import { useEffect, useState } from 'react';

/**
 * Lumen apparatus · codebase-graph. One central node (the planning session)
 * and seven satellites — the real agent and provider files in backend/app —
 * joined by hairlines along which light walks. Pure SVG, no image, no orb.
 * Callouts carry values read from the code, never invented.
 */
const SATELLITES: { file: string; role: string; angle: number }[] = [
  { file: 'trip-parser.ts', role: 'brief', angle: -90 },
  { file: 'discovery.py', role: 'places', angle: -38 },
  { file: 'scoring.py', role: 'rank', angle: 14 },
  { file: 'accommodation.py', role: 'stay', angle: 66 },
  { file: 'transport.py', role: 'flights', angle: 118 },
  { file: 'itinerary.py', role: 'route', angle: 170 },
  { file: 'places_foursquare.py', role: 'provider', angle: 222 },
];

const CALLOUTS: { text: string; side: 'left' | 'right'; y: number }[] = [
  { text: 'STAGES · 07', side: 'left', y: 10 },
  { text: 'GEOCODE TTL · 7 D', side: 'right', y: 6 },
  { text: 'ROUTE TTL · 5 MIN', side: 'left', y: 92 },
  { text: 'STREAM · SSE', side: 'right', y: 94 },
];

const CX = 240;
const CY = 240;
const R = 150;

export function Apparatus() {
  const [animate, setAnimate] = useState(false);
  useEffect(() => {
    setAnimate(window.matchMedia('(prefers-reduced-motion: no-preference)').matches);
  }, []);

  return (
    <figure className="apparatus" aria-label="Agent graph: a planning session at the centre, seven agent files around it">
      <svg viewBox="0 0 480 480" className="block h-auto w-full overflow-visible" role="img">
        <defs>
          <radialGradient id="core-glow" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="var(--color-glow)" />
            <stop offset="100%" stopColor="transparent" />
          </radialGradient>
        </defs>

        {/* inner emit */}
        <circle cx={CX} cy={CY} r={120} fill="url(#core-glow)" className="glow-core" />

        {/* orbit ring */}
        <circle cx={CX} cy={CY} r={R} fill="none" stroke="var(--color-rule)" strokeWidth="1" strokeDasharray="2 6" />

        {SATELLITES.map((s) => {
          const a = (s.angle * Math.PI) / 180;
          const x = CX + R * Math.cos(a);
          const y = CY + R * Math.sin(a);
          const labelRight = Math.cos(a) >= 0;
          return (
            <g key={s.file}>
              <line x1={CX} y1={CY} x2={x} y2={y} stroke="var(--color-rule-2)" strokeWidth="1" />
              {animate && (
                <line
                  x1={CX}
                  y1={CY}
                  x2={x}
                  y2={y}
                  stroke="var(--color-accent)"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  className="edge-light"
                  style={{ animationDelay: `${(s.angle + 90) / 60}s` }}
                />
              )}
              <circle cx={x} cy={y} r={5} fill="var(--color-paper)" stroke="var(--color-ink)" strokeWidth="1" />
              <text
                x={x + (labelRight ? 10 : -10)}
                y={y + 4}
                textAnchor={labelRight ? 'start' : 'end'}
                fill="var(--color-ink-2)"
                fontFamily="var(--font-mono)"
                fontSize="10.5"
                letterSpacing="0.04em"
              >
                {s.file}
              </text>
              <text
                x={x + (labelRight ? 10 : -10)}
                y={y + 16}
                textAnchor={labelRight ? 'start' : 'end'}
                fill="var(--color-subtle)"
                fontFamily="var(--font-mono)"
                fontSize="9"
                letterSpacing="0.08em"
              >
                {s.role.toUpperCase()}
              </text>
            </g>
          );
        })}

        {/* core */}
        <g className="node-core">
          <circle cx={CX} cy={CY} r={26} fill="var(--color-paper-2)" stroke="var(--color-accent)" strokeWidth="1" />
          <circle cx={CX} cy={CY} r={5} fill="var(--color-accent)" />
        </g>
        <text x={CX} y={CY + 46} textAnchor="middle" fill="var(--color-muted)" fontFamily="var(--font-mono)" fontSize="9.5" letterSpacing="0.1em">
          SESSION
        </text>
      </svg>

      <ul className="pointer-events-none absolute inset-0 hidden lg:block" aria-hidden="true">
        {CALLOUTS.map((c) => (
          <li
            key={c.text}
            className="label absolute flex items-center gap-2"
            style={{ top: `${c.y}%`, [c.side]: 0, flexDirection: c.side === 'left' ? 'row' : 'row-reverse' }}
          >
            <span>{c.text}</span>
            <span className="block h-px w-6 bg-rule-2" />
          </li>
        ))}
      </ul>
    </figure>
  );
}
