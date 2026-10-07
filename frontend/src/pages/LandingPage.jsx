import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  ArrowRight,
  BrainCircuit,
  BriefcaseBusiness,
  CheckCircle2,
  MapPin,
  Search,
  ShieldCheck,
  Target,
  Zap,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { jobApi } from '../services/jobApi';
import { Badge } from '../components/common/Badge';

export function LandingPage() {
  const { isAuthenticated, user } = useAuth();
  const [jobData, setJobData] = useState(null);

  useEffect(() => {
    let active = true;

    async function loadPublicJobs() {
      try {
        const data = await jobApi.listJobs({ page: 1 });
        if (active) setJobData(data);
      } catch {
        // The landing page remains useful even if a public feed is temporarily unavailable.
      }
    }

    loadPublicJobs();

    return () => {
      active = false;
    };
  }, []);

  const jobs = jobData?.jobs || [];
  const liveCount = jobData?.total ?? null;
  const sourceCount = (jobData?.sources || []).filter((source) => source.available).length;

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="sticky top-0 z-40 bg-white/95 backdrop-blur border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 md:px-8 h-16 flex items-center justify-between gap-4">
          <Link to="/" className="flex items-center gap-3">
            <div className="p-2 bg-primary-600 rounded-xl text-white shadow-lg shadow-primary-500/20">
              <BrainCircuit className="w-5 h-5" />
            </div>
            <div>
              <p className="font-extrabold text-sm md:text-base tracking-tight">AI Career Navigator</p>
              <p className="text-[11px] text-slate-400">Evidence-driven career intelligence</p>
            </div>
          </Link>

          <div className="flex items-center gap-2">
            <Link
              to="/jobs"
              className="hidden sm:inline-flex items-center gap-2 px-3 py-2 rounded-xl text-xs font-bold text-slate-600 hover:bg-slate-100"
            >
              <BriefcaseBusiness className="w-3.5 h-3.5" />
              Find Tech Jobs
            </Link>

            {isAuthenticated ? (
              <Link
                to="/"
                className="inline-flex items-center gap-2 px-3.5 py-2 rounded-xl bg-slate-900 text-white text-xs font-bold hover:bg-slate-800"
              >
                Workspace
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            ) : (
              <>
                <Link
                  to="/login"
                  className="inline-flex items-center gap-2 px-3 py-2 rounded-xl text-xs font-bold text-slate-700 hover:bg-slate-100"
                >
                  Sign in
                </Link>
                <Link
                  to="/register"
                  className="hidden sm:inline-flex items-center gap-2 px-3.5 py-2 rounded-xl bg-primary-600 hover:bg-primary-700 text-white text-xs font-bold"
                >
                  Create account
                </Link>
              </>
            )}
          </div>
        </div>
      </header>

      <main>
        <section className="relative overflow-hidden bg-slate-950 text-white">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_10%_10%,rgba(99,102,241,0.40),transparent_32%),radial-gradient(circle_at_88%_75%,rgba(14,165,233,0.18),transparent_30%)]" />

          <div className="relative max-w-7xl mx-auto px-4 md:px-8 py-16 md:py-24">
            <div className="grid grid-cols-1 lg:grid-cols-[1.1fr_0.9fr] gap-12 items-center">
              <div className="max-w-3xl">
                <div className="flex flex-wrap gap-2 items-center">
                  <span className="text-[10px] uppercase tracking-[0.18em] font-black text-indigo-300">
                    Technology career intelligence
                  </span>
                  <span className="px-2 py-1 rounded-full bg-white/10 border border-white/10 text-[10px] font-bold text-slate-300">
                    Public job explorer
                  </span>
                </div>

                <h1 className="mt-5 text-4xl md:text-6xl font-black tracking-tight leading-[1.02]">
                  From a real tech job
                  <br />
                  to your next best action.
                </h1>

                <p className="mt-6 text-base md:text-lg leading-7 text-slate-300 max-w-2xl">
                  Discover live technology roles, understand their requirements,
                  compare them with your evidence, close the right skill gaps,
                  and return to the role when your evidence is stronger.
                </p>

                <div className="flex flex-wrap gap-3 mt-8">
                  <Link
                    to="/jobs"
                    className="inline-flex items-center gap-2 px-5 py-3.5 rounded-xl bg-white text-slate-950 font-extrabold text-sm hover:bg-slate-100"
                  >
                    <Search className="w-4 h-4" />
                    Explore Tech Jobs
                    <ArrowRight className="w-4 h-4" />
                  </Link>

                  {!isAuthenticated && (
                    <Link
                      to="/register"
                      className="inline-flex items-center gap-2 px-5 py-3.5 rounded-xl bg-white/10 border border-white/15 text-white font-bold text-sm hover:bg-white/15"
                    >
                      Build my profile
                    </Link>
                  )}
                </div>

                <div className="grid grid-cols-3 gap-3 mt-10 max-w-xl">
                  <div className="rounded-2xl border border-white/10 bg-white/[0.06] p-4">
                    <p className="text-xl font-black">{liveCount ?? 'Live'}</p>
                    <p className="text-[11px] text-slate-400 mt-1">tech listings</p>
                  </div>
                  <div className="rounded-2xl border border-white/10 bg-white/[0.06] p-4">
                    <p className="text-xl font-black">{sourceCount || 'Multi'}</p>
                    <p className="text-[11px] text-slate-400 mt-1">sources online</p>
                  </div>
                  <div className="rounded-2xl border border-white/10 bg-white/[0.06] p-4">
                    <p className="text-xl font-black">SBERT</p>
                    <p className="text-[11px] text-slate-400 mt-1">semantic layer</p>
                  </div>
                </div>
              </div>

              <div className="rounded-3xl border border-white/10 bg-white/[0.06] backdrop-blur p-5 md:p-6 shadow-2xl">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] uppercase tracking-[0.16em] font-black text-indigo-300">
                    How it works
                  </span>
                  <ShieldCheck className="w-5 h-5 text-emerald-400" />
                </div>

                <div className="mt-5 space-y-3">
                  {[
                    [Search, 'Discover', 'Search live technology opportunities by role and location.'],
                    [BrainCircuit, 'Align', 'Use keyword + semantic evidence analysis on a real posting.'],
                    [Target, 'Close the gap', 'Identify where more evidence or practice is useful.'],
                    [Zap, 'Re-align', 'Return to the role after learning, practical work or assessment.'],
                  ].map(([Icon, title, text]) => (
                    <div
                      key={title}
                      className="rounded-2xl border border-white/10 bg-slate-900/60 p-4 flex gap-3"
                    >
                      <div className="p-2.5 rounded-xl bg-indigo-500/15 text-indigo-300 shrink-0">
                        <Icon className="w-5 h-5" />
                      </div>
                      <div>
                        <p className="text-sm font-bold">{title}</p>
                        <p className="text-xs leading-5 text-slate-400 mt-1">{text}</p>
                      </div>
                    </div>
                  ))}
                </div>

                <div className="mt-5 rounded-xl border border-emerald-400/10 bg-emerald-400/5 px-4 py-3">
                  <p className="text-[11px] text-emerald-200">
                    Semantic similarity supports review. It is not a hiring probability or proof of proficiency.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="max-w-7xl mx-auto px-4 md:px-8 py-10">
          <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-4">
            <div>
              <p className="text-[10px] uppercase tracking-[0.18em] font-black text-primary-600">
                Live opportunities
              </p>
              <h2 className="text-2xl font-black text-slate-900 mt-1">
                Explore technology roles
              </h2>
              <p className="text-sm text-slate-500 mt-1">
                Public browsing is open. Personalized evidence analysis starts after sign-in.
              </p>
            </div>

            <Link
              to="/jobs"
              className="inline-flex items-center gap-2 text-sm font-bold text-primary-600 hover:underline"
            >
              View all jobs
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>

          {jobs.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
              {jobs.slice(0, 3).map((job) => (
                <Link
                  key={job.id}
                  to={`/jobs/${encodeURIComponent(job.source_key)}/${encodeURIComponent(job.provider_id)}`}
                  className="group bg-white rounded-2xl border border-slate-200 p-5 hover:border-primary-300 hover:shadow-lg transition"
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-[10px] font-black uppercase tracking-wider text-slate-400">
                      {job.provider}
                    </span>
                    <Badge variant="success">Live</Badge>
                  </div>

                  <h3 className="text-base font-extrabold text-slate-900 mt-4 group-hover:text-primary-700 transition">
                    {job.title}
                  </h3>
                  <p className="text-xs font-semibold text-slate-600 mt-1">
                    {job.employer}
                  </p>

                  <div className="flex flex-wrap gap-2 mt-4 text-[11px] text-slate-500">
                    <span className="inline-flex items-center gap-1">
                      <MapPin className="w-3 h-3" />
                      {job.location || 'Location not specified'}
                    </span>
                    <span>{job.work_mode || 'Not specified'}</span>
                  </div>

                  {!!job.tech_tags?.length && (
                    <div className="flex flex-wrap gap-1.5 mt-4">
                      {job.tech_tags.slice(0, 4).map((tag) => (
                        <span
                          key={tag}
                          className="px-2 py-1 rounded-lg bg-slate-100 text-[10px] font-bold text-slate-600"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  )}

                  <div className="mt-5 pt-4 border-t border-slate-100 text-xs font-bold text-primary-600 flex items-center gap-1">
                    View role
                    <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition" />
                  </div>
                </Link>
              ))}
            </div>
          ) : (
            <div className="mt-6 rounded-2xl border border-dashed border-slate-300 bg-white p-8 text-center">
              <p className="text-sm font-bold text-slate-700">
                Live job previews are temporarily unavailable.
              </p>
              <p className="text-xs text-slate-500 mt-1">
                The full job explorer will retry the employer feeds.
              </p>
            </div>
          )}
        </section>

        <section className="max-w-7xl mx-auto px-4 md:px-8 pb-12">
          <div className="rounded-3xl bg-white border border-slate-200 shadow-sm p-6 md:p-8">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {[
                ['Public discovery', 'Browse technology vacancies before creating an account.', 'Open job explorer'],
                ['Private evidence', 'Keep resume, projects, certifications and assessments tied to your account.', 'Create account'],
                ['Research layer', 'Use SBERT semantic suggestions with transparent evidence coverage.', 'Learn about alignment'],
              ].map(([title, text, action], index) => (
                <div key={title} className="p-5 rounded-2xl bg-slate-50 border border-slate-100">
                  <span className="text-[10px] font-black text-slate-400">0{index + 1}</span>
                  <div className="mt-3 flex items-start gap-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600 mt-0.5 shrink-0" />
                    <div>
                      <h3 className="text-sm font-extrabold text-slate-900">{title}</h3>
                      <p className="text-xs leading-5 text-slate-500 mt-1">{text}</p>
                      <Link
                        to={index === 0 ? '/jobs' : index === 1 ? '/register' : '/jobs'}
                        className="inline-flex items-center gap-1 mt-4 text-xs font-bold text-primary-600"
                      >
                        {action}
                        <ArrowRight className="w-3 h-3" />
                      </Link>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>
      </main>

      <footer className="border-t border-slate-200 bg-white">
        <div className="max-w-7xl mx-auto px-4 md:px-8 py-5 text-[11px] text-slate-400 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
          <span>AI Career Navigator · Evidence-driven technology career intelligence</span>
          <span>Live employer postings · Personalized analysis requires sign-in</span>
        </div>
      </footer>
    </div>
  );
}
