import React, { useMemo, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { KeyRound, ArrowRight, AlertCircle, CheckCircle2 } from 'lucide-react';
import { api } from '../services/api';

export function ResetPasswordPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const token = useMemo(
    () => new URLSearchParams(location.search).get('reset_token') || new URLSearchParams(location.search).get('token') || '',
    [location.search]
  );

  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [error, setError] = useState(token ? '' : 'This reset link is missing its token.');
  const [success, setSuccess] = useState('');
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (!token) {
      setError('This reset link is missing its token.');
      return;
    }

    if (password.length < 8) {
      setError('Password must be at least 8 characters.');
      return;
    }

    if (password !== confirm) {
      setError('Passwords do not match.');
      return;
    }

    setSubmitting(true);
    try {
      const response = await api.resetPassword(token, password);
      setSuccess(response.message || 'Password updated successfully.');
      setTimeout(() => navigate('/login', { replace: true }), 900);
    } catch (err) {
      setError(err.message || 'This reset link is invalid or has expired.');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="bg-white rounded-3xl shadow-xl border border-slate-200/80 p-7 sm:p-8">
      <div className="mb-7">
        <div className="inline-flex p-3 bg-primary-50 text-primary-700 rounded-2xl mb-4">
          <KeyRound className="w-6 h-6" />
        </div>
        <h2 className="text-2xl font-extrabold tracking-tight text-slate-900">Set a new password</h2>
        <p className="text-sm text-slate-500 mt-1">
          Choose a new password for your Career Navigator account.
        </p>
      </div>

      {error && (
        <div className="mb-5 p-4 bg-rose-50 border border-rose-200 rounded-2xl flex items-start gap-3 text-rose-700 text-sm">
          <AlertCircle className="w-5 h-5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {success && (
        <div className="mb-5 p-4 bg-emerald-50 border border-emerald-200 rounded-2xl flex items-start gap-3 text-emerald-800 text-sm">
          <CheckCircle2 className="w-5 h-5 shrink-0" />
          <span>{success}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-xs font-bold text-slate-700 mb-1.5">New password</label>
          <input
            type="password"
            required
            minLength={8}
            autoComplete="new-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="At least 8 characters"
            className="w-full px-4 py-3 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500 text-sm"
          />
        </div>

        <div>
          <label className="block text-xs font-bold text-slate-700 mb-1.5">Confirm password</label>
          <input
            type="password"
            required
            minLength={8}
            autoComplete="new-password"
            value={confirm}
            onChange={(e) => setConfirm(e.target.value)}
            placeholder="Repeat the new password"
            className="w-full px-4 py-3 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500 text-sm"
          />
        </div>

        <button
          type="submit"
          disabled={submitting || !token}
          className="w-full py-3.5 px-4 bg-primary-600 hover:bg-primary-700 disabled:opacity-50 text-white rounded-xl font-bold text-sm transition shadow-lg shadow-primary-600/20 flex items-center justify-center gap-2"
        >
          {submitting ? 'Updating password…' : <>Update password <ArrowRight className="w-4 h-4" /></>}
        </button>
      </form>

      <div className="mt-6 pt-6 border-t border-slate-100 text-center text-sm text-slate-500">
        <Link to="/login" className="text-primary-600 font-bold hover:underline">
          Return to sign in
        </Link>
      </div>
    </div>
  );
}
