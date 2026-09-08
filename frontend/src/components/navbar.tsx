import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Search, LogOut } from 'lucide-react';
import { LoginModal } from './login-modal';
import { useAuth } from '../contexts/AuthContext';

export function Navbar() {
  const [isLoginOpen, setIsLoginOpen] = useState(false);
  const { user, logout, isAuthenticated } = useAuth();

  return (
    <>
      <nav className="fixed top-0 left-0 right-0 z-50 border-b border-line bg-canvas/85 backdrop-blur-md">
        <div className="mx-auto flex h-14 max-w-7xl items-center gap-6 px-6">
          <Link to="/" className="shrink-0 font-display text-xl leading-none text-ink no-underline">
            Voyage
          </Link>

          <div className="relative hidden min-w-0 flex-1 sm:block">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-subtle" />
            <input
              type="text"
              placeholder="Search destinations"
              aria-label="Search destinations"
              className="h-9 w-full max-w-sm rounded-md border border-line bg-surface pl-9 pr-3 text-sm text-ink placeholder:text-ink-subtle focus:border-brand focus:outline-none"
            />
          </div>

          <div className="ml-auto flex shrink-0 items-center gap-3">
            {isAuthenticated ? (
              <>
                <span className="hidden text-sm text-ink-muted md:inline">
                  {user?.full_name || user?.email}
                </span>
                <button
                  onClick={logout}
                  title="Sign out"
                  aria-label="Sign out"
                  className="flex h-9 w-9 items-center justify-center rounded-md text-ink-muted transition-colors hover:bg-sunken hover:text-ink"
                >
                  <LogOut className="h-4 w-4" />
                </button>
              </>
            ) : (
              <button
                onClick={() => setIsLoginOpen(true)}
                className="h-9 rounded-md px-3 text-sm font-medium text-ink-muted transition-colors hover:bg-sunken hover:text-ink"
              >
                Sign in
              </button>
            )}
          </div>
        </div>
      </nav>

      <LoginModal isOpen={isLoginOpen} onClose={() => setIsLoginOpen(false)} />
    </>
  );
}
