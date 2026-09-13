import { useCallback, useState } from 'react';
import { Moon, Sun } from 'lucide-react';
import { currentDrop, toggleDrop, type Drop } from '../../lib/theme';
import { Link, NavLink } from 'react-router-dom';
import { LoginModal } from './LoginModal';
import { CommandPalette, useCommandK, type Command } from './CommandPalette';
import { useAuth } from '../../contexts/AuthContext';

interface NavbarProps {
  /** Page-specific commands for the palette. */
  commands?: Command[];
  /** Page context (planner rail, itinerary tabs) rendered in a bar under the pill. */
  context?: React.ReactNode;
}

/**
 * N5 · Floating pill. Content-sized, detached from the edges, blur over the
 * canvas. Wordmark · one link · ⌘K · one brass CTA. On product pages a
 * second, full-width context bar sits beneath it.
 */
export function Navbar({ commands, context }: NavbarProps) {
  const [loginOpen, setLoginOpen] = useState(false);
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [drop, setDrop] = useState<Drop>(() => (typeof document !== 'undefined' ? currentDrop() : 'night'));
  const { user, logout, isAuthenticated } = useAuth();
  const openPalette = useCallback(() => setPaletteOpen(true), []);
  useCommandK(openPalette);
  const isMac = typeof navigator !== 'undefined' && /Mac|iPhone|iPad/.test(navigator.platform);

  return (
    <>
      <nav className={`nav-pill ${context ? 'nav-pill--inflow' : ''}`} aria-label="Primary">
        <Link to="/" className="display lc pr-2 text-[length:var(--text-md)] text-ink no-underline">
          voyage
        </Link>
        <NavLink
          to="/trips"
          className={({ isActive }) =>
            `lc hidden rounded-full px-3 py-2 text-[13px] no-underline transition-colors sm:inline ${
              isActive ? 'text-ink' : 'text-muted hover:text-ink'
            }`
          }
        >
          trips
        </NavLink>
        <button type="button" onClick={openPalette} className="searchpill" aria-label="Open command palette">
          <span className="lc hidden sm:inline">jump to</span>
          <span className="inline-flex gap-0.5">
            <kbd>{isMac ? '⌘' : 'Ctrl'}</kbd>
            <kbd>K</kbd>
          </span>
        </button>
        {isAuthenticated ? (
          <button onClick={logout} className="btn btn-ghost lc hidden sm:inline-flex" title={user?.email}>
            sign out
          </button>
        ) : (
          <button onClick={() => setLoginOpen(true)} className="btn btn-ghost lc hidden sm:inline-flex">
            sign in
          </button>
        )}
        <button
          type="button"
          onClick={() => setDrop(toggleDrop())}
          className="btn btn-ghost btn-icon"
          aria-label={drop === 'day' ? 'Switch to night' : 'Switch to day'}
          title={drop === 'day' ? 'Night' : 'Day'}
        >
          {drop === 'day' ? <Moon className="h-4 w-4" /> : <Sun className="h-4 w-4" />}
        </button>
        <Link to="/plan" className="btn btn-primary lc no-underline">
          plan a trip
        </Link>
      </nav>

      {/* Fixed pill needs its space reserved; the in-flow variant does not. */}
      {!context && <div className="h-20" aria-hidden="true" />}
      {context && (
        <div className="sticky top-0 z-[200] border-b border-rule bg-paper/90 backdrop-blur-sm">
          <div className="mx-auto flex h-12 max-w-6xl items-center gap-3 px-4 sm:px-6">{context}</div>
        </div>
      )}

      <CommandPalette open={paletteOpen} onClose={() => setPaletteOpen(false)} extra={commands} />
      <LoginModal isOpen={loginOpen} onClose={() => setLoginOpen(false)} />
    </>
  );
}
