import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Mail, ArrowLeft, Send, AlertCircle, CheckCircle2 } from 'lucide-react';
import { api } from '../services/api';

export function ForgotPasswordPage() {
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [debugUrl, setDebugUrl] = useState('');
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    setMessage('');
    setDebugUrl('');
    setSubmitting(true);

    try {
      const response = await api.forgotPassword(email);
      setMessage(response.message || 'If an account exists for this email, a reset link has been prepared.');
      if (response.debug_reset_url) {
        setDebugUrl(response.debug_reset_url);
      }
    } catch (err) {
      setError(err.message || 'Unable to prepare the password reset.');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="bg-white rounded-3xl shadow-xl border border-slate-200/80 p-7 sm:p-8">
      <div className="mb-7">
        <div className="inline-flex p-3 bg-primary-50 text-primary-700 rounded-2xl mb-4">
          <Mail className="w-6 h-6" />
        </div>
        <h2 className="text-2xl font-extrabold tracking-tight text-slate-900">Forgot your password?</h2>
        <p className="text-sm text-slate-500 mt-1">
          Enter your account email and we’ll prepare a secure reset link.
        </p>
      </div>

      {error && (
        <div className="mb-5 p-4 bg-rose-50 border border-rose-200 rounded-2xl flex items-start gap-3 text-rose-700 text-sm">
          <AlertCircle className="w-5 h-5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {message && (
        <div className="mb-5 p-4 bg-emerald-50 border border-emerald-200 rounded-2xl text-emerald-800 text-sm">
          <div className="flex items-start gap-3">
            <CheckCircle2 className="w-5 h-5 shrink-0" />
            <span>{message}</span>
          </div>

          {debugUrl && (
            <div className="mt-4 pt-4 border-t border-emerald-200">
              <p className="text-[11px] font-bold uppercase tracking-wider text-emerald-700">
                Local demo reset link
              </p>
              <a
                href={debugUrl}
                className="block mt-1 text-xs font-semibold text-emerald-900 break-all underline"
              >
                Open reset page
              </a>
            </div>
          )}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-xs font-bold text-slate-700 mb-1.5">Email address</label>
          <input
            type="email"
            required
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
            className="w-full px-4 py-3 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500 text-sm"
          />
        </div>

        <button
          type="submit"
          disabled={submitting}
          className="w-full py-3.5 px-4 bg-primary-600 hover:bg-primary-700 disabled:opacity-50 text-white rounded-xl font-bold text-sm transition shadow-lg shadow-primary-600/20 flex items-center justify-center gap-2"
        >
          {submitting ? 'Preparing reset…' : <>Send reset link <Send className="w-4 h-4" /></>}
        </button>
      </form>

      <div className="mt-6 pt-6 border-t border-slate-100 text-center">
        <Link to="/login" className="inline-flex items-center gap-2 text-sm font-bold text-primary-600 hover:underline">
          <ArrowLeft className="w-4 h-4" />
          Back to sign in
        </Link>
      </div>
    </div>
  );
}
