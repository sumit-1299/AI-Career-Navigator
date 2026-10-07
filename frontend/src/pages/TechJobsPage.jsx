import React, { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Search,
  MapPin,
  BriefcaseBusiness,
  SlidersHorizontal,
  RefreshCw,
  ArrowRight,
  ShieldCheck,
  Wifi,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { jobApi } from '../services/jobApi';
import { Badge } from '../components/common/Badge';
import { Spinner, Alert } from '../components/common/UIFeedback';

const initialFilters = {
  q: '',
  location: '',
  work_mode: '',
  experience: '',
  technology: '',
  provider: '',
};

export function TechJobsPage() {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  const [filters, setFilters] = useState(initialFilters);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);

  async function loadJobs(nextFilters = filters, { background = false } = {}) {
    if (background) setRefreshing(true);
    else setLoading(true);

    setError(null);

    try {
      const response = await jobApi.listJobs(nextFilters);
      setData(response);
    } catch (err) {
      setError(err.message || 'Could not load live technology jobs.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }

  useEffect(() => {
    loadJobs(initialFilters);
  }, []);

  const facets = data?.facets || {};
  const jobs = data?.jobs || [];

  const sourceStatus = useMemo(() => {
    const sources = data?.sources || [];
    return sources.map((source) => ({
      provider: source.employer,
      status: source.available ? 'Live' : 'Unavailable',
      count: source.listed_count || 0,
    }));
  }, [data]);

  function updateFilter(name, value) {
    setFilters((current) => ({ ...current, [name]: value }));
  }

  function submitSearch(event) {
    event.preventDefault();
    loadJobs({ ...filters, page: 1 });
  }

  function clearFilters() {
    setFilters(initialFilters);
    loadJobs({ ...initialFilters, page: 1 });
  }

  return (
    <div className="space-y-6 animate-fadeIn">
      <div className="bg-white rounded-2xl p-6 md:p-8 shadow-sm border border-slate-200">
        <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-5">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-primary-50 text-primary-700 border border-primary-200">
                Live Technology Opportunities
              </span>
              <span className="text-[10px] font-black uppercase tracking-wider text-emerald-700 flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                Public
              </span>
            </div>

            <h1 className="text-2xl md:text-3xl font-extrabold text-slate-900 tracking-tight mt-3">
              Find Tech Jobs
            </h1>

            <p className="text-sm text-slate-500 mt-1 max-w-2xl">
              Explore live technology-focused vacancies by role, location,
              technology, work mode and experience. No account is required to browse.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <Link
              to="/"
              className="inline-flex items-center gap-2 px-3.5 py-2.5 rounded-xl border border-slate-200 text-sm font-semibold text-slate-700 hover:bg-slate-50"
            >
              Home
            </Link>
            {!isAuthenticated && (
              <Link
                to="/login?next=%2Fjobs"
                className="inline-flex items-center gap-2 px-3.5 py-2.5 rounded-xl bg-primary-600 hover:bg-primary-700 text-white text-sm font-semibold"
              >
                Sign in
              </Link>
            )}
          </div>
        </div>

        <form onSubmit={submitSearch} className="mt-6">
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-6 gap-3">
            <div className="xl:col-span-2 relative">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3.5" />
              <input
                value={filters.q}
                onChange={(e) => updateFilter('q', e.target.value)}
                placeholder="Role, skill or keyword"
                className="w-full rounded-xl border border-slate-300 bg-white py-2.5 pl-9 pr-3 text-sm outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500"
              />
            </div>

            <div className="relative">
              <MapPin className="w-4 h-4 text-slate-400 absolute left-3 top-3.5" />
              <input
                value={filters.location}
                onChange={(e) => updateFilter('location', e.target.value)}
                placeholder="Location"
                className="w-full rounded-xl border border-slate-300 bg-white py-2.5 pl-9 pr-3 text-sm outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500"
              />
            </div>

            <select
              value={filters.technology}
              onChange={(e) => updateFilter('technology', e.target.value)}
              className="rounded-xl border border-slate-300 bg-white px-3 py-2.5 text-sm"
            >
              <option value="">Technology</option>
              {(facets.technologies || []).map((value) => (
                <option key={value} value={value}>{value}</option>
              ))}
            </select>

            <select
              value={filters.work_mode}
              onChange={(e) => updateFilter('work_mode', e.target.value)}
              className="rounded-xl border border-slate-300 bg-white px-3 py-2.5 text-sm"
            >
              <option value="">Work mode</option>
              {(facets.work_modes || []).map((value) => (
                <option key={value} value={value}>{value}</option>
              ))}
            </select>

            <select
              value={filters.experience}
              onChange={(e) => updateFilter('experience', e.target.value)}
              className="rounded-xl border border-slate-300 bg-white px-3 py-2.5 text-sm"
            >
              <option value="">Experience</option>
              {(facets.experience_levels || []).map((value) => (
                <option key={value} value={value}>{value}</option>
              ))}
            </select>
          </div>

          <div className="mt-4 flex flex-wrap items-center gap-3">
            <button
              type="submit"
              disabled={loading || refreshing}
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-primary-600 hover:bg-primary-700 text-white text-sm font-semibold disabled:opacity-60"
            >
              <Search className="w-4 h-4" />
              Search live jobs
            </button>

            <button
              type="button"
              onClick={clearFilters}
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl border border-slate-200 text-slate-700 text-sm font-semibold hover:bg-slate-50"
            >
              <SlidersHorizontal className="w-4 h-4" />
              Clear
            </button>

            <button
              type="button"
              onClick={() => loadJobs(filters, { background: true })}
              className="ml-auto inline-flex items-center gap-2 px-3.5 py-2.5 rounded-xl border border-slate-200 text-slate-700 text-sm font-semibold hover:bg-slate-50"
            >
              <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
              Refresh
            </button>
          </div>
        </form>
      </div>

      {error && <Alert type="error" message={error} />}

      {data && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <div className="bg-white rounded-xl border border-slate-200 p-4">
            <p className="text-xs text-slate-500">Live tech listings</p>
            <p className="text-2xl font-extrabold text-slate-900 mt-1">{data.total ?? 0}</p>
          </div>

          <div className="bg-white rounded-xl border border-slate-200 p-4">
            <p className="text-xs text-slate-500">Sources online</p>
            <p className="text-2xl font-extrabold text-slate-900 mt-1">
              {sourceStatus.filter((source) => source.status === 'Live').length}
            </p>
          </div>

          <div className="bg-white rounded-xl border border-slate-200 p-4">
            <p className="text-xs text-slate-500">Scope</p>
            <p className="text-sm font-bold text-primary-700 mt-2">
              Technology hiring only
            </p>
          </div>
        </div>
      )}

      <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
        <div className="px-6 py-5 border-b border-slate-200 flex flex-col md:flex-row md:items-center md:justify-between gap-3">
          <div>
            <h2 className="text-lg font-bold text-slate-900">Live opportunities</h2>
            <p className="text-xs text-slate-500 mt-1">
              Fetched directly from public employer job feeds.
            </p>
          </div>

          <div className="flex flex-wrap gap-2">
            {sourceStatus.slice(0, 6).map((source) => (
              <Badge
                key={source.provider}
                variant={source.status === 'Live' ? 'success' : 'neutral'}
              >
                {source.provider}: {source.status}
              </Badge>
            ))}
          </div>
        </div>

        {loading ? (
          <div className="py-20 flex flex-col items-center justify-center">
            <Spinner size="lg" />
            <p className="mt-4 text-sm font-medium text-slate-500">
              Fetching live technology vacancies…
            </p>
          </div>
        ) : jobs.length === 0 ? (
          <div className="py-20 text-center px-6">
            <BriefcaseBusiness className="w-10 h-10 text-slate-300 mx-auto" />
            <p className="mt-3 text-sm font-semibold text-slate-700">
              No matching tech jobs found.
            </p>
            <p className="mt-1 text-xs text-slate-500">
              Try a broader role, location or technology filter.
            </p>
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {jobs.map((job) => (
              <div
                key={job.id}
                className="px-6 py-5 hover:bg-slate-50/70 transition"
              >
                <div className="flex flex-col lg:flex-row lg:items-center gap-5">
                  <div className="flex-1 min-w-0">
                    <div className="flex flex-wrap gap-2 items-center">
                      <span className="text-xs font-semibold text-slate-500">
                        {job.provider}
                      </span>
                      <Badge variant="success">Live</Badge>
                    </div>

                    <h3 className="text-base md:text-lg font-bold text-slate-900 mt-1">
                      {job.title}
                    </h3>

                    <p className="text-sm text-slate-600 mt-1">
                      {job.employer}
                    </p>

                    <div className="flex flex-wrap gap-3 mt-3 text-xs text-slate-500">
                      <span className="inline-flex items-center gap-1.5">
                        <MapPin className="w-3.5 h-3.5" />
                        {job.location || 'Location not specified'}
                      </span>

                      <span className="inline-flex items-center gap-1.5">
                        <Wifi className="w-3.5 h-3.5" />
                        {job.work_mode || 'Not specified'}
                      </span>

                      <span className="inline-flex items-center gap-1.5">
                        <BriefcaseBusiness className="w-3.5 h-3.5" />
                        {job.experience_level || 'Not specified'}
                      </span>
                    </div>

                    {!!job.tech_tags?.length && (
                      <div className="flex flex-wrap gap-2 mt-3">
                        {job.tech_tags.slice(0, 8).map((tag) => (
                          <span
                            key={tag}
                            className="text-[11px] font-semibold px-2 py-1 rounded-lg bg-slate-100 text-slate-700"
                          >
                            {tag}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>

                  <div className="flex flex-col sm:flex-row lg:flex-col gap-2 shrink-0">
                    <button
                      onClick={() =>
                        navigate(
                          `/jobs/${encodeURIComponent(job.source_key)}/${encodeURIComponent(job.provider_id)}`
                        )
                      }
                      className="inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-primary-600 hover:bg-primary-700 text-white text-sm font-semibold"
                    >
                      View & analyze
                      <ArrowRight className="w-4 h-4" />
                    </button>

                    <a
                      href={job.source_url}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl border border-slate-200 text-slate-700 text-sm font-semibold hover:bg-slate-50"
                    >
                      Employer posting
                    </a>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="bg-slate-950 rounded-2xl p-5 text-slate-200">
        <div className="flex items-start gap-3">
          <ShieldCheck className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-bold">Public discovery. Private intelligence.</p>
            <p className="text-xs text-slate-400 mt-1 max-w-4xl">
              Anyone can explore live technology vacancies. Sign in only when you want
              personalized resume, project, certification and assessment alignment.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
