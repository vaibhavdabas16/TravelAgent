import { useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search } from 'lucide-react';
import { listSavedTrips } from '../../lib/planning-storage';

export interface Command {
  id: string;
  label: string;
  hint?: string;
  group: string;
  run: () => void;
}

interface CommandPaletteProps {
  open: boolean;
  onClose: () => void;
  /** Page-specific commands, prepended to the global ones. */
  extra?: Command[];
}

/**
 * ⌘K palette. Opens instantly, type-to-filter, ↑/↓ moves the highlight,
 * Enter runs, Esc closes. Uses the native <dialog> for focus containment.
 * Every command is real: routes, saved trips, page actions.
 */
export function CommandPalette({ open, onClose, extra = [] }: CommandPaletteProps) {
  const navigate = useNavigate();
  const dialog = useRef<HTMLDialogElement>(null);
  const input = useRef<HTMLInputElement>(null);
  const [query, setQuery] = useState('');
  const [index, setIndex] = useState(0);

  const commands = useMemo<Command[]>(() => {
    const go = (to: string) => () => {
      onClose();
      navigate(to);
    };
    const trips = listSavedTrips().map<Command>((t) => ({
      id: `trip-${t.id}`,
      label: t.destination,
      hint: t.days ? `${t.days} days` : undefined,
      group: 'Saved trips',
      run: go(`/trip/${t.id}`),
    }));
    return [
      ...extra,
      { id: 'plan', label: 'Plan a trip', hint: 'from one sentence', group: 'Go to', run: go('/plan') },
      { id: 'trips', label: 'Trips', hint: 'saved in this browser', group: 'Go to', run: go('/trips') },
      { id: 'home', label: 'Home', hint: 'how the system works', group: 'Go to', run: go('/') },
      ...trips,
    ];
  }, [extra, navigate, onClose]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return commands;
    return commands.filter((c) => `${c.label} ${c.hint ?? ''} ${c.group}`.toLowerCase().includes(q));
  }, [commands, query]);

  useEffect(() => {
    const d = dialog.current;
    if (!d) return;
    if (open && !d.open) {
      d.showModal();
      setQuery('');
      setIndex(0);
      requestAnimationFrame(() => input.current?.focus());
    } else if (!open && d.open) {
      d.close();
    }
  }, [open]);

  useEffect(() => setIndex(0), [query]);

  const onKey = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setIndex((i) => Math.min(filtered.length - 1, i + 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setIndex((i) => Math.max(0, i - 1));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      filtered[index]?.run();
    }
  };

  // Group headings in display order.
  const groups = Array.from(new Set(filtered.map((c) => c.group)));

  return (
    <dialog
      ref={dialog}
      onClose={onClose}
      onClick={(e) => {
        if (e.target === dialog.current) onClose();
      }}
      aria-label="Command palette"
      className="cmdk"
    >
      <div className="cmdk__panel" onKeyDown={onKey}>
        <div className="flex h-12 items-center gap-3 border-b border-rule px-4">
          <Search className="h-4 w-4 shrink-0 text-subtle" aria-hidden="true" />
          <input
            ref={input}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Where to?"
            aria-label="Search commands"
            className="mono min-w-0 flex-1 bg-transparent text-[14px] text-ink placeholder:text-subtle focus:outline-none"
          />
          <kbd>esc</kbd>
        </div>
        <div className="max-h-[50vh] overflow-y-auto py-2" role="listbox" aria-label="Commands">
          {filtered.length === 0 && <p className="px-4 py-3 text-[13px] text-muted">Nothing matches &ldquo;{query}&rdquo;.</p>}
          {groups.map((g) => (
            <div key={g}>
              <p className="label px-4 pb-1 pt-2">{g}</p>
              {filtered
                .filter((c) => c.group === g)
                .map((c) => {
                  const i = filtered.indexOf(c);
                  return (
                    <button
                      key={c.id}
                      type="button"
                      role="option"
                      aria-selected={i === index}
                      onMouseEnter={() => setIndex(i)}
                      onClick={c.run}
                      className={`flex w-full items-center justify-between gap-4 px-4 py-2 text-left text-[14px] ${
                        i === index ? 'bg-accent-soft text-ink' : 'text-ink-2'
                      }`}
                    >
                      <span className="truncate">{c.label}</span>
                      {c.hint && <span className="mono shrink-0 text-subtle">{c.hint}</span>}
                    </button>
                  );
                })}
            </div>
          ))}
        </div>
        <div className="mono flex gap-4 border-t border-rule px-4 py-2 text-subtle">
          <span>
            <kbd>↑</kbd> <kbd>↓</kbd> move
          </span>
          <span>
            <kbd>↵</kbd> open
          </span>
        </div>
      </div>
    </dialog>
  );
}

/** Global ⌘K / Ctrl+K listener. */
export function useCommandK(onOpen: () => void) {
  useEffect(() => {
    const h = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        onOpen();
      }
    };
    window.addEventListener('keydown', h);
    return () => window.removeEventListener('keydown', h);
  }, [onOpen]);
}
