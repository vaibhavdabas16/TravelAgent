/**
 * Night / Day drop switch. The choice lives in localStorage; with none saved,
 * the system preference decides. index.html applies it before first paint so
 * there is no flash; this module keeps it in sync afterwards.
 */
export type Drop = 'night' | 'day';
const KEY = 'voyage:drop';

export function currentDrop(): Drop {
  return document.documentElement.dataset.theme === 'day' ? 'day' : 'night';
}

export function applyDrop(drop: Drop): void {
  if (drop === 'day') document.documentElement.dataset.theme = 'day';
  else delete document.documentElement.dataset.theme;
  try {
    localStorage.setItem(KEY, drop);
  } catch {
    /* private mode: the choice lasts for this page only */
  }
}

export function toggleDrop(): Drop {
  const next: Drop = currentDrop() === 'day' ? 'night' : 'day';
  applyDrop(next);
  return next;
}
