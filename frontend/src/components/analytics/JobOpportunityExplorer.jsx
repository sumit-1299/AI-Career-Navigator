import React, { useState, useEffect } from 'react';
import { api } from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { Spinner, Alert } from '../common/UIFeedback';
import {
  Briefcase,
  Search,
  Building2,
  MapPin,
  ExternalLink,
  CheckCircle2,
  AlertCircle,
  Sparkles,
  TrendingUp,
  FolderGit2,
  ArrowRight,
  RefreshCw,
  Clock,
  Target,
  ChevronRight,
  ShieldCheck,
  Zap,
  BookOpen,
  Filter,
  Layers,
  GraduationCap,
  X,
} from 'lucide-react';

export function JobOpportunityExplorer() {
  const { user, isAuthenticated, targetCareerId } = useAuth();

  // Job Search State
  const [jobs, setJobs] = useState([]);
  const [totalJobs, setTotalJobs] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(10);
  const [sources, setSources] = useState([]);
  const [loadingJobs, setLoadingJobs] = useState(true);
  const [jobsError, setJobsError] = useState(null);

  // Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [workModeFilter, setWorkModeFilter] = useState('');
  const [experienceFilter, setExperienceFilter] = useState('');
  const [sourceKeyFilter, setSourceKeyFilter] = useState('');
  const [techFilter, setTechFilter] = useState('');

  // Selected Job & Action Center State
  const [selectedJobRef, setSelectedJobRef] = useState(null); // { sourceKey, providerId }
  const [actionCenterData, setActionCenterData] = useState(null);
  const [loadingActionCenter, setLoadingActionCenter] = useState(false);
  const [actionCenterError, setActionCenterError] = useState(null);

  // Initial load
  useEffect(() => {
    loadSources();
    fetchJobs(1);
  }, []);

  async function loadSources() {
    try {
      const res = await api.getLiveJobSources();
      if (res?.sources) {
        setSources(res.sources);
      }
    } catch (err) {
      console.warn('Failed to load employer sources:', err);
    }
  }

  async function fetchJobs(targetPage = 1) {
    setLoadingJobs(true);
    setJobsError(null);
    try {
      const res = await api.listLiveJobs({
        q: searchQuery,
        work_mode: workModeFilter,
        experience: experienceFilter,
        source_key: sourceKeyFilter,
        technology: techFilter,
        page: targetPage,
        page_size: pageSize,
      });

      if (res?.jobs) {
        setJobs(res.jobs);
        setTotalJobs(res.total || res.jobs.length);
        setPage(res.page || targetPage);
      } else {
        setJobs([]);
        setTotalJobs(0);
      }
    } catch (err) {
      setJobsError('Job opportunity service is temporarily unavailable. Please retry shortly.');
      setJobs([]);
    } finally {
      setLoadingJobs(false);
    }
  }

  function handleFilterSubmit(e) {
    e.preventDefault();
    setPage(1);
    fetchJobs(1);
  }

  function handleResetFilters() {
    setSearchQuery('');
    setWorkModeFilter('');
    setExperienceFilter('');
    setSourceKeyFilter('');
    setTechFilter('');
    setPage(1);
    setTimeout(() => {
      fetchJobs(1);
    }, 0);
  }

  // Load Action Center for selected job
  async function selectJobForAnalysis(job) {
    const sourceKey = job.source_key;
    const providerId = job.provider_id;
    setSelectedJobRef({ sourceKey, providerId, jobTitle: job.title, employer: job.employer });
    setLoadingActionCenter(true);
    setActionCenterError(null);

    try {
      const res = await api.getJobActionCenter(sourceKey, providerId, {
        fromCareerId: targetCareerId || null,
      });

      if (res?.status === 'success') {
        setActionCenterData(res);
      } else {
        setActionCenterError(res?.message || 'Skill alignment could not be calculated for this opportunity.');
      }
    } catch (err) {
      setActionCenterError('Skill alignment could not be calculated for this opportunity.');
    } finally {
      setLoadingActionCenter(false);
    }
  }

  const totalPages = Math.ceil(totalJobs / pageSize) || 1;

  return (
    <div className="space-y-6">
      {/* Educational Notice Banner */}
      <div className="bg-gradient-to-r from-blue-50 via-indigo-50 to-slate-50 border border-blue-200 rounded-2xl p-4 sm:p-5 flex items-start gap-3 shadow-sm">
        <ShieldCheck className="w-5 h-5 text-indigo-600 shrink-0 mt-0.5" />
        <div className="text-xs sm:text-sm text-slate-700 space-y-1">
          <p className="font-semibold text-slate-900">Career Decision Support & Opportunity Intelligence</p>
          <p>
            Explore real vacancies from verified employer feeds. Job match percentages reflect direct skill overlap with
            postings and do <strong>not</strong> constitute employment prediction or placement guarantees. Industry demand
            benchmarks reflect <strong>DEMO / SAMPLE / PROTOTYPE</strong> research data.
          </p>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <form onSubmit={handleFilterSubmit} className="bg-white border border-slate-200 rounded-2xl p-4 sm:p-5 shadow-sm space-y-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
          {/* Keyword Search */}
          <div className="lg:col-span-2 relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3.5" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search title, keywords (e.g. Backend, Cloud)..."
              className="w-full pl-9 pr-3 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:bg-white transition"
            />
          </div>

          {/* Work Mode */}
          <div>
            <select
              value={workModeFilter}
              onChange={(e) => setWorkModeFilter(e.target.value)}
              className="w-full px-3 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:bg-white transition"
            >
              <option value="">All Work Modes</option>
              <option value="remote">Remote</option>
              <option value="hybrid">Hybrid</option>
              <option value="on-site">On-site</option>
            </select>
          </div>

          {/* Experience */}
          <div>
            <select
              value={experienceFilter}
              onChange={(e) => setExperienceFilter(e.target.value)}
              className="w-full px-3 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:bg-white transition"
            >
              <option value="">All Experience</option>
              <option value="entry">Entry-level</option>
              <option value="mid">Mid-level</option>
              <option value="senior">Senior</option>
            </select>
          </div>

          {/* Employer / Source */}
          <div>
            <select
              value={sourceKeyFilter}
              onChange={(e) => setSourceKeyFilter(e.target.value)}
              className="w-full px-3 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:bg-white transition"
            >
              <option value="">All Employers</option>
              {sources.map((s) => (
                <option key={s.source_key} value={s.source_key}>
                  {s.employer} ({s.provider})
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-slate-100">
          <div className="flex items-center gap-2">
            <input
              type="text"
              value={techFilter}
              onChange={(e) => setTechFilter(e.target.value)}
              placeholder="Filter by technology (e.g. Python, Docker)..."
              className="px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-xs w-64 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:bg-white"
            />
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={handleResetFilters}
              className="px-3 py-1.5 text-xs font-medium text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-lg transition"
            >
              Reset
            </button>
            <button
              type="submit"
              className="flex items-center gap-1.5 px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white text-xs font-semibold rounded-xl shadow-sm hover:shadow transition"
            >
              <Filter className="w-3.5 h-3.5" />
              <span>Apply Filters</span>
            </button>
          </div>
        </div>
      </form>

      {/* Main Content Area: Split View */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Job Listings List */}
        <div className={`space-y-4 ${selectedJobRef ? 'lg:col-span-5' : 'lg:col-span-12'}`}>
          <div className="flex items-center justify-between px-1">
            <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2">
              <Briefcase className="w-4 h-4 text-primary-600" />
              <span>Available Vacancies ({totalJobs})</span>
            </h3>
            {loadingJobs && (
              <span className="text-xs text-slate-500 flex items-center gap-1">
                <RefreshCw className="w-3 h-3 animate-spin text-primary-600" />
                Loading opportunities...
              </span>
            )}
          </div>

          {jobsError && (
            <Alert type="warning" message={jobsError} />
          )}

          {loadingJobs && jobs.length === 0 ? (
            <div className="bg-white border border-slate-200 rounded-2xl p-12 text-center">
              <Spinner size="lg" />
              <p className="mt-3 text-sm text-slate-500 font-medium">Loading job opportunities...</p>
            </div>
          ) : jobs.length === 0 ? (
            <div className="bg-white border border-slate-200 rounded-2xl p-12 text-center">
              <Briefcase className="w-10 h-10 text-slate-300 mx-auto mb-3" />
              <h4 className="text-sm font-semibold text-slate-800">No matching job opportunities found.</h4>
              <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
                Try adjusting your search terms, changing the work mode filter, or resetting all filters.
              </p>
              <button
                type="button"
                onClick={handleResetFilters}
                className="mt-4 px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-medium rounded-lg transition"
              >
                Reset Filters
              </button>
            </div>
          ) : (
            <div className="space-y-3">
              {jobs.map((job) => {
                const isSelected =
                  selectedJobRef?.sourceKey === job.source_key &&
                  selectedJobRef?.providerId === job.provider_id;

                return (
                  <div
                    key={`${job.source_key}-${job.provider_id}`}
                    className={`bg-white border rounded-2xl p-4 sm:p-5 transition-all cursor-pointer ${
                      isSelected
                        ? 'border-primary-500 ring-2 ring-primary-500/20 shadow-md bg-primary-50/10'
                        : 'border-slate-200 hover:border-slate-300 hover:shadow-sm'
                    }`}
                    onClick={() => selectJobForAnalysis(job)}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <h4 className="text-sm font-bold text-slate-900 group-hover:text-primary-600 transition leading-snug">
                          {job.title}
                        </h4>
                        <div className="flex flex-wrap items-center gap-2 mt-1.5 text-xs text-slate-500">
                          <span className="flex items-center gap-1 font-medium text-slate-700">
                            <Building2 className="w-3.5 h-3.5 text-slate-400" />
                            {job.employer}
                          </span>
                          <span>•</span>
                          <span className="flex items-center gap-1">
                            <MapPin className="w-3.5 h-3.5 text-slate-400" />
                            {job.location || 'Flexible'}
                          </span>
                        </div>
                      </div>

                      {/* Work Mode Badge */}
                      <span className="px-2 py-0.5 bg-slate-100 text-slate-700 font-semibold text-[11px] rounded-md shrink-0 uppercase tracking-wide">
                        {job.work_mode || 'Flexible'}
                      </span>
                    </div>

                    {/* Description preview */}
                    <p className="text-xs text-slate-600 mt-2.5 line-clamp-2 leading-relaxed">
                      {job.description}
                    </p>

                    {/* Tech Tags */}
                    {job.tech_tags && job.tech_tags.length > 0 && (
                      <div className="flex flex-wrap gap-1.5 mt-3 pt-3 border-t border-slate-100">
                        {job.tech_tags.slice(0, 5).map((tag) => (
                          <span
                            key={tag}
                            className="px-2 py-0.5 bg-slate-100 text-slate-600 text-[11px] font-medium rounded-md"
                          >
                            {tag}
                          </span>
                        ))}
                        {job.tech_tags.length > 5 && (
                          <span className="text-[11px] text-slate-400 font-medium self-center">
                            +{job.tech_tags.length - 5} more
                          </span>
                        )}
                      </div>
                    )}

                    {/* Footer / CTA */}
                    <div className="flex items-center justify-between mt-3 pt-2 text-xs">
                      <span className="text-[11px] text-slate-400">
                        Source: {job.source_key?.split('-')[0] || 'Feed'}
                      </span>
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          selectJobForAnalysis(job);
                        }}
                        className={`flex items-center gap-1 font-semibold text-xs px-2.5 py-1 rounded-lg transition ${
                          isSelected
                            ? 'bg-primary-600 text-white'
                            : 'text-primary-600 hover:bg-primary-50'
                        }`}
                      >
                        <span>Analyze & Take Action</span>
                        <ChevronRight className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                );
              })}

              {/* Pagination Controls */}
              {totalPages > 1 && (
                <div className="flex items-center justify-between px-2 pt-2 text-xs text-slate-600">
                  <span>
                    Page {page} of {totalPages}
                  </span>
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      disabled={page <= 1}
                      onClick={() => fetchJobs(page - 1)}
                      className="px-3 py-1.5 bg-white border border-slate-200 rounded-lg disabled:opacity-40 hover:bg-slate-50 transition"
                    >
                      Previous
                    </button>
                    <button
                      type="button"
                      disabled={page >= totalPages}
                      onClick={() => fetchJobs(page + 1)}
                      className="px-3 py-1.5 bg-white border border-slate-200 rounded-lg disabled:opacity-40 hover:bg-slate-50 transition"
                    >
                      Next
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Right Column: Career Action Center Panel */}
        {selectedJobRef && (
          <div className="lg:col-span-7 space-y-5 sticky top-4">
            {loadingActionCenter ? (
              <div className="bg-white border border-slate-200 rounded-2xl p-12 text-center shadow-sm">
                <Spinner size="lg" />
                <h4 className="text-sm font-semibold text-slate-800 mt-3">Synthesizing Career Action Intelligence...</h4>
                <p className="text-xs text-slate-500 mt-1">
                  Connecting job vacancy requirements with Skill ROI, Capstones, and Interview Readiness.
                </p>
              </div>
            ) : actionCenterError ? (
              <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-3">
                <Alert type="warning" message={actionCenterError} />
                <button
                  type="button"
                  onClick={() => selectJobForAnalysis({ source_key: selectedJobRef.sourceKey, provider_id: selectedJobRef.providerId })}
                  className="px-3 py-1.5 bg-primary-600 text-white text-xs font-semibold rounded-lg"
                >
                  Retry Analysis
                </button>
              </div>
            ) : actionCenterData ? (
              <div className="space-y-5">
                {/* 1. Job Header Card */}
                <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm space-y-4">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="px-2 py-0.5 bg-primary-50 text-primary-700 text-[11px] font-semibold rounded-md uppercase tracking-wider">
                          Live Opportunity
                        </span>
                        <span className="text-xs text-slate-400">ID: {actionCenterData.job?.provider_id}</span>
                      </div>
                      <h3 className="text-base sm:text-lg font-bold text-slate-900 mt-1">
                        {actionCenterData.job?.title}
                      </h3>
                      <p className="text-xs text-slate-600 font-medium mt-0.5">
                        {actionCenterData.job?.employer} • {actionCenterData.job?.location || 'Remote'}
                      </p>
                    </div>

                    <div className="flex items-center gap-2">
                      {actionCenterData.job?.source_url && (
                        <a
                          href={actionCenterData.job.source_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-900 hover:bg-slate-800 text-white text-xs font-medium rounded-xl transition shadow-sm"
                        >
                          <span>Apply on Employer Board</span>
                          <ExternalLink className="w-3.5 h-3.5" />
                        </a>
                      )}
                      <button
                        type="button"
                        onClick={() => setSelectedJobRef(null)}
                        className="p-1.5 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition"
                        title="Close panel"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                  </div>

                  {/* Attributes Strip */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-2 border-t border-slate-100 text-center">
                    <div className="bg-slate-50 p-2 rounded-xl">
                      <span className="text-[10px] text-slate-400 uppercase font-semibold block">Work Mode</span>
                      <span className="text-xs font-bold text-slate-800 uppercase">
                        {actionCenterData.job?.work_mode || 'Flexible'}
                      </span>
                    </div>
                    <div className="bg-slate-50 p-2 rounded-xl">
                      <span className="text-[10px] text-slate-400 uppercase font-semibold block">Experience</span>
                      <span className="text-xs font-bold text-slate-800 uppercase">
                        {actionCenterData.job?.experience_level || 'Open'}
                      </span>
                    </div>
                    <div className="bg-slate-50 p-2 rounded-xl">
                      <span className="text-[10px] text-slate-400 uppercase font-semibold block">Source Provider</span>
                      <span className="text-xs font-bold text-slate-800 uppercase">
                        {actionCenterData.job?.provider || 'Public API'}
                      </span>
                    </div>
                    <div className="bg-slate-50 p-2 rounded-xl">
                      <span className="text-[10px] text-slate-400 uppercase font-semibold block">Required Tech</span>
                      <span className="text-xs font-bold text-slate-800">
                        {actionCenterData.match?.total_target_skills || 0} skills
                      </span>
                    </div>
                  </div>
                </div>

                {/* 2. Personalized Job Match & Skill Alignment (Step 3) */}
                <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Zap className="w-4 h-4 text-amber-500" />
                      <h4 className="text-sm font-bold text-slate-900">Personalized Vacancy Skill Alignment</h4>
                    </div>
                    <span className="text-xs font-extrabold text-primary-600 bg-primary-50 px-2.5 py-1 rounded-lg">
                      {actionCenterData.match?.match_score}% Match Score
                    </span>
                  </div>

                  {/* Educational Distinction Notice */}
                  <div className="bg-slate-50 border border-slate-200 rounded-xl p-3 text-xs text-slate-600 space-y-1">
                    <p className="font-semibold text-slate-800 flex items-center gap-1.5">
                      <AlertCircle className="w-3.5 h-3.5 text-blue-600 shrink-0" />
                      <span>Scoring Concept Distinction:</span>
                    </p>
                    <p>
                      <strong>Job Match Score ({actionCenterData.match?.match_score}%)</strong> measures keyword & skill overlap
                      with this specific posting. <strong>Career Readiness Score</strong> evaluates holistic preparation across an
                      entire formal career curriculum.
                    </p>
                  </div>

                  {/* Matched vs Missing Breakdown */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
                    {/* Matched */}
                    <div className="border border-emerald-200 bg-emerald-50/40 rounded-xl p-3 space-y-2">
                      <span className="text-xs font-bold text-emerald-800 flex items-center gap-1.5">
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                        <span>Matched Skills ({actionCenterData.match?.matched_skills?.length || 0})</span>
                      </span>
                      <div className="flex flex-wrap gap-1.5">
                        {actionCenterData.match?.matched_skills?.length > 0 ? (
                          actionCenterData.match.matched_skills.map((s) => (
                            <span
                              key={s}
                              className="px-2 py-0.5 bg-white border border-emerald-200 text-emerald-800 text-xs font-medium rounded-md shadow-2xs"
                            >
                              {s}
                            </span>
                          ))
                        ) : (
                          <span className="text-xs text-slate-400 italic">None matched yet.</span>
                        )}
                      </div>
                    </div>

                    {/* Missing */}
                    <div className="border border-amber-200 bg-amber-50/40 rounded-xl p-3 space-y-2">
                      <span className="text-xs font-bold text-amber-800 flex items-center gap-1.5">
                        <AlertCircle className="w-3.5 h-3.5 text-amber-600" />
                        <span>Missing Competencies ({actionCenterData.match?.missing_skills?.length || 0})</span>
                      </span>
                      <div className="flex flex-wrap gap-1.5">
                        {actionCenterData.match?.missing_skills?.length > 0 ? (
                          actionCenterData.match.missing_skills.map((s) => (
                            <span
                              key={s}
                              className="px-2 py-0.5 bg-white border border-amber-200 text-amber-800 text-xs font-medium rounded-md shadow-2xs"
                            >
                              {s}
                            </span>
                          ))
                        ) : (
                          <span className="text-xs text-emerald-700 font-medium">All target skills present!</span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>

                {/* 3. "What Should I Do Next?" Action Plan (Step 10) */}
                {actionCenterData.action_plan && (
                  <div className="bg-gradient-to-br from-primary-900 to-slate-900 text-white rounded-2xl p-5 shadow-md space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold text-primary-300 uppercase tracking-wider flex items-center gap-1.5">
                        <Sparkles className="w-4 h-4 text-amber-400" />
                        Action Center Strategy
                      </span>
                      <span className="px-2 py-0.5 bg-white/10 text-white text-[11px] font-bold rounded-md">
                        {actionCenterData.action_plan.status_headline}
                      </span>
                    </div>

                    <p className="text-xs sm:text-sm text-slate-200 leading-relaxed">
                      {actionCenterData.action_plan.recommended_next_step}
                    </p>

                    {/* Action Checklist */}
                    {actionCenterData.action_plan.action_checklist?.length > 0 && (
                      <div className="space-y-2 pt-2 border-t border-white/10">
                        <span className="text-[11px] font-bold text-slate-300 uppercase tracking-wide block">
                          Suggested Action Items
                        </span>
                        {actionCenterData.action_plan.action_checklist.map((step, idx) => (
                          <div key={idx} className="flex items-start gap-2 text-xs text-slate-200">
                            <span className="w-4 h-4 rounded-full bg-primary-600 text-white flex items-center justify-center text-[10px] font-bold shrink-0 mt-0.5">
                              {idx + 1}
                            </span>
                            <span>{step}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* 4. Skill Gap Action Panel (Step 4) */}
                {actionCenterData.skill_actions && actionCenterData.skill_actions.length > 0 && (
                  <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Target className="w-4 h-4 text-rose-500" />
                        <h4 className="text-sm font-bold text-slate-900">Skills to Work On (Prioritized)</h4>
                      </div>
                      <span className="text-xs text-slate-400">Powered by Skill ROI Engine</span>
                    </div>

                    <div className="space-y-2.5">
                      {actionCenterData.skill_actions.map((act) => (
                        <div
                          key={act.skill_name}
                          className="bg-slate-50 border border-slate-200 rounded-xl p-3 flex flex-col sm:flex-row sm:items-center justify-between gap-2.5"
                        >
                          <div className="space-y-0.5">
                            <div className="flex items-center gap-2">
                              <span className="font-bold text-xs text-slate-900">{act.skill_name}</span>
                              <span
                                className={`px-2 py-0.2 rounded text-[10px] font-extrabold uppercase ${
                                  act.priority === 'QUICKEST_WIN'
                                    ? 'bg-amber-100 text-amber-800'
                                    : act.priority === 'HIGH'
                                    ? 'bg-rose-100 text-rose-800'
                                    : 'bg-blue-100 text-blue-800'
                                }`}
                              >
                                {act.priority === 'QUICKEST_WIN' ? '⚡ Quickest Win' : act.priority}
                              </span>
                              <span className="text-[11px] font-semibold text-emerald-700">
                                +{act.marginal_readiness_gain}% Gain
                              </span>
                            </div>
                            <p className="text-[11px] text-slate-600">{act.why_it_matters}</p>
                          </div>

                          <div className="text-right shrink-0">
                            <span className="text-[11px] text-slate-500 block">
                              ~{act.estimated_study_hours} hrs study
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* 5. Portfolio & Capstone Projects Connection (Step 5) */}
                {actionCenterData.portfolio_recommendations && actionCenterData.portfolio_recommendations.length > 0 && (
                  <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <FolderGit2 className="w-4 h-4 text-primary-600" />
                        <h4 className="text-sm font-bold text-slate-900">Capstone Projects Closing Your Gaps</h4>
                      </div>
                      <span className="text-xs text-slate-400">Curated Portfolio Catalog</span>
                    </div>

                    <div className="space-y-3">
                      {actionCenterData.portfolio_recommendations.map((proj) => (
                        <div
                          key={proj.project_id}
                          className="border border-slate-200 rounded-xl p-3.5 hover:border-slate-300 transition space-y-2 bg-slate-50/50"
                        >
                          <div className="flex items-start justify-between gap-2">
                            <div>
                              <h5 className="font-bold text-xs text-slate-900">{proj.title}</h5>
                              <p className="text-[11px] text-slate-500 mt-0.5">
                                {proj.domain} • Difficulty: {proj.difficulty} • ~{proj.estimated_hours} hrs
                              </p>
                            </div>
                            <span className="text-[11px] font-bold text-primary-700 bg-primary-50 px-2 py-0.5 rounded">
                              Value: {proj.portfolio_value}/100
                            </span>
                          </div>

                          {proj.addresses_missing_skills && proj.addresses_missing_skills.length > 0 && (
                            <div className="text-[11px] text-emerald-800 bg-emerald-50 border border-emerald-200 rounded-lg px-2.5 py-1">
                              <strong>Addresses vacancy gaps:</strong> {proj.addresses_missing_skills.join(', ')}
                            </div>
                          )}

                          {proj.deliverables && proj.deliverables.length > 0 && (
                            <ul className="text-[11px] text-slate-600 space-y-0.5 list-disc list-inside">
                              {proj.deliverables.slice(0, 2).map((deliv, dIdx) => (
                                <li key={dIdx}>{deliv}</li>
                              ))}
                            </ul>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* 6. Career Alignment, Industry Demand & Interview Grid */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {/* Career Track Connection (Step 6) */}
                  <div className="bg-white border border-slate-200 rounded-2xl p-4 shadow-sm space-y-2">
                    <div className="flex items-center gap-1.5 text-xs font-bold text-slate-900">
                      <Layers className="w-4 h-4 text-indigo-600" />
                      <span>Career Track Connection</span>
                    </div>

                    {actionCenterData.career_connection?.status === 'mapped' ? (
                      <div className="space-y-1 text-xs">
                        <p className="font-bold text-slate-800 text-sm">
                          {actionCenterData.career_connection.career_title}
                        </p>
                        <p className="text-slate-500">
                          Domain: {actionCenterData.career_connection.domain || 'Technology'}
                        </p>
                        <span className="inline-block mt-1 px-2 py-0.5 bg-emerald-50 text-emerald-700 text-[10px] font-bold rounded">
                          {actionCenterData.career_connection.confidence} CONFIDENCE MATCH
                        </span>
                      </div>
                    ) : (
                      <div className="space-y-1 text-xs">
                        <p className="font-bold text-slate-500">Career mapping unavailable</p>
                        <p className="text-slate-400 text-[11px]">
                          Vacancy requirements span specialized or cross-track competencies.
                        </p>
                      </div>
                    )}
                  </div>

                  {/* Interview Readiness Practice (Step 9) */}
                  <div className="bg-white border border-slate-200 rounded-2xl p-4 shadow-sm space-y-2">
                    <div className="flex items-center gap-1.5 text-xs font-bold text-slate-900">
                      <GraduationCap className="w-4 h-4 text-purple-600" />
                      <span>Interview Readiness</span>
                    </div>

                    {actionCenterData.interview_readiness?.interview_available ? (
                      <div className="space-y-2 text-xs">
                        <p className="text-slate-600 text-[11px]">
                          {actionCenterData.interview_readiness.recommended_practice_action}
                        </p>
                        <a
                          href={`/analytics`}
                          className="inline-flex items-center gap-1 px-3 py-1.5 bg-purple-600 hover:bg-purple-700 text-white text-xs font-semibold rounded-xl transition shadow-2xs"
                        >
                          <span>Practice Interview Session</span>
                          <ArrowRight className="w-3.5 h-3.5" />
                        </a>
                      </div>
                    ) : (
                      <p className="text-xs text-slate-400">Simulation questions unavailable for this track.</p>
                    )}
                  </div>
                </div>

                {/* 7. Industry Demand Signal (Step 7) */}
                {actionCenterData.industry_demand_context && (
                  <div className="bg-white border border-slate-200 rounded-2xl p-4 shadow-sm space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-slate-900 flex items-center gap-1.5">
                        <TrendingUp className="w-4 h-4 text-blue-600" />
                        Industry Skill Demand Benchmark
                      </span>
                      <span className="text-[10px] font-bold text-slate-500 uppercase">
                        {actionCenterData.industry_demand_context.market_growth_label}
                      </span>
                    </div>

                    <p className="text-[11px] text-slate-500">
                      {actionCenterData.industry_demand_context.provenance_disclaimer ||
                        'DEMO / SAMPLE / PROTOTYPE RESEARCH BENCHMARK — NOT LIVE LABOR-MARKET GROUND TRUTH.'}
                    </p>

                    {actionCenterData.industry_demand_context.overlapping_demand_skills?.length > 0 && (
                      <div className="flex flex-wrap gap-1.5 pt-1">
                        {actionCenterData.industry_demand_context.overlapping_demand_skills.map((dSkill) => (
                          <span
                            key={dSkill.skill_name}
                            className="px-2 py-0.5 bg-blue-50 border border-blue-200 text-blue-800 text-[11px] font-medium rounded-md"
                          >
                            {dSkill.skill_name} • {dSkill.demand_level}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            ) : null}
          </div>
        )}
      </div>
    </div>
  );
}
