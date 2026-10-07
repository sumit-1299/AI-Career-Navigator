import React from 'react';
import { Link, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import {
  Compass,
  BriefcaseBusiness,
  ShieldCheck,
  LogIn,
  UserPlus,
  ArrowRight,
} from 'lucide-react';

export function PublicJobsLayout() {
  const { isAuthenticated, user } = useAuth();
  const location = useLocation();

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="sticky top-0 z-40 bg-white/95 backdrop-blur border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 md:px-8 h-16 flex items-center justify-between gap-4">
          <Link to="/jobs" className="flex items-center gap-3 min-w-0">
            <div className="p-2 bg-primary-600 rounded-xl text-white shadow-lg shadow-primary-500/20">
              <Compass className="w-5 h-5" />
            </div>
            <div className="min-w-0">
              <p className="font-extrabold text-sm md:text-base tracking-tight text-slate-900">
                AI Career Navigator
              </p>
              <p className="text-[11px] text-slate-400 truncate">
                Live technology opportunities
              </p>
            </div>
          </Link>

          <div className="flex items-center gap-2">
            {isAuthenticated ? (
              <>
                <Link
                  to="/"
                  className="hidden sm:inline-flex items-center gap-2 px-3 py-2 rounded-xl text-xs font-bold text-slate-600 hover:bg-slate-100"
                >
                  <Compass className="w-3.5 h-3.5" />
                  Workspace
                </Link>
                <span className="hidden md:inline text-xs text-slate-400 max-w-[150px] truncate">
                  {user?.name || 'Candidate'}
                </span>
              </>
            ) : (
              <>
                <Link
                  to={`/login?next=${encodeURIComponent(location.pathname + location.search)}`}
                  className="inline-flex items-center gap-2 px-3 py-2 rounded-xl text-xs font-bold text-slate-700 hover:bg-slate-100"
                >
                  <LogIn className="w-3.5 h-3.5" />
                  Sign in
                </Link>
                <Link
                  to="/register"
                  className="hidden sm:inline-flex items-center gap-2 px-3.5 py-2 rounded-xl bg-primary-600 hover:bg-primary-700 text-white text-xs font-bold shadow-sm"
                >
                  <UserPlus className="w-3.5 h-3.5" />
                  Create account
                </Link>
              </>
            )}
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 md:px-8 py-6 md:py-8">
        <div className="mb-5 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div className="flex items-center gap-2 text-xs font-semibold text-slate-500">
            <BriefcaseBusiness className="w-4 h-4 text-primary-600" />
            <span>Public job explorer</span>
            <span className="text-slate-300">•</span>
            <span>Tech hiring only</span>
          </div>

          {!isAuthenticated && (
            <div className="inline-flex items-center gap-2 text-[11px] text-slate-500">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
              Browse freely. Sign in only when you want personalized analysis.
            </div>
          )}
        </div>

        <Outlet />

        {!isAuthenticated && (
          <div className="mt-6 rounded-2xl border border-indigo-100 bg-gradient-to-r from-indigo-50 to-white p-5 md:p-6">
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
              <div>
                <p className="text-[10px] uppercase tracking-[0.16em] font-black text-indigo-600">
                  Personalized layer
                </p>
                <h2 className="text-lg font-extrabold text-slate-900 mt-1">
                  Want to compare a role with your evidence?
                </h2>
                <p className="text-xs md:text-sm text-slate-500 mt-1 max-w-2xl">
                  Create an account to use resume evidence, projects, certifications,
                  assessments and the SBERT semantic alignment flow.
                </p>
              </div>

              <Link
                to={`/login?next=${encodeURIComponent(location.pathname + location.search)}`}
                className="inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-slate-900 text-white text-xs font-bold hover:bg-slate-800 shrink-0"
              >
                Sign in to analyze
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          </div>
        )}
      </main>

      <footer className="border-t border-slate-200 bg-white">
        <div className="max-w-7xl mx-auto px-4 md:px-8 py-4 text-[11px] text-slate-400 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
          <span>AI Career Navigator · Technology job explorer</span>
          <span>Live employer postings · Personalized analysis requires sign-in</span>
        </div>
      </footer>
    </div>
  );
}
