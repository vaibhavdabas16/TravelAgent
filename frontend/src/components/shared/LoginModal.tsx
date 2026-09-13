import { useEffect, useRef, useState } from 'react';
import { X, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import { useAuth } from '../../contexts/AuthContext';

interface LoginModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function LoginModal({ isOpen, onClose }: LoginModalProps) {
  const { login, register } = useAuth();
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState({ email: '', password: '', fullName: '' });
  const firstField = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!isOpen) return;
    setError(null);
    const t = setTimeout(() => firstField.current?.focus(), 50);
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && onClose();
    window.addEventListener('keydown', onKey);
    return () => {
      clearTimeout(t);
      window.removeEventListener('keydown', onKey);
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      if (mode === 'login') {
        await login(form.email, form.password);
        toast.success('Welcome back');
      } else {
        await register(form.email, form.password, form.fullName || undefined);
        toast.success('Account created');
      }
      onClose();
    } catch (err: any) {
      setError(
        err?.response?.data?.detail ||
          err?.message ||
          'We could not sign you in. Check your details and try again.'
      );
    } finally {
      setBusy(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-[60] flex items-end justify-center sm:items-center"
      role="dialog"
      aria-modal="true"
      aria-labelledby="login-title"
    >
      <button aria-label="Close" onClick={onClose} className="absolute inset-0 bg-ink/30" />
      <div className="relative w-full max-w-sm rounded-t-lg border border-rule bg-paper p-5 shadow-menu sm:rounded-lg">
        <button
          onClick={onClose}
          aria-label="Close"
          className="btn btn-ghost btn-icon absolute right-3 top-3"
        >
          <X className="h-4 w-4" />
        </button>

        <h2 id="login-title" className="text-[length:var(--text-md)]">
          {mode === 'login' ? 'Welcome back' : 'Create your account'}
        </h2>
        <p className="mt-1 text-[13px] text-muted">
          {mode === 'login'
            ? 'Sign in to keep your trips together.'
            : 'Save trips and pick up where you left off.'}
        </p>

        <form onSubmit={submit} className="mt-5 space-y-3">
          {mode === 'register' && (
            <div>
              <label htmlFor="login-name" className="mb-1 block text-[12px] font-medium text-muted">
                Full name
              </label>
              <input
                id="login-name"
                ref={firstField}
                className="field"
                value={form.fullName}
                onChange={(e) => setForm({ ...form, fullName: e.target.value })}
                autoComplete="name"
              />
            </div>
          )}
          <div>
            <label htmlFor="login-email" className="mb-1 block text-[12px] font-medium text-muted">
              Email
            </label>
            <input
              id="login-email"
              ref={mode === 'login' ? firstField : undefined}
              type="email"
              required
              className="field"
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              autoComplete="email"
            />
          </div>
          <div>
            <label htmlFor="login-password" className="mb-1 block text-[12px] font-medium text-muted">
              Password
            </label>
            <input
              id="login-password"
              type="password"
              required
              minLength={6}
              className="field"
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
              autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
            />
          </div>

          {error && (
            <p role="alert" className="rounded-sm bg-critical-soft px-3 py-2 text-[13px] text-critical">
              {error}
            </p>
          )}

          <button type="submit" disabled={busy} className="btn btn-primary btn-lg w-full">
            {busy && <Loader2 className="h-4 w-4 animate-spin" />}
            {mode === 'login' ? 'Sign in' : 'Create account'}
          </button>
        </form>

        <p className="mt-4 text-center text-[13px] text-muted">
          {mode === 'login' ? 'New here?' : 'Already have an account?'}{' '}
          <button
            type="button"
            onClick={() => setMode(mode === 'login' ? 'register' : 'login')}
            className="font-medium text-ink underline underline-offset-2"
          >
            {mode === 'login' ? 'Create an account' : 'Sign in'}
          </button>
        </p>
      </div>
    </div>
  );
}
