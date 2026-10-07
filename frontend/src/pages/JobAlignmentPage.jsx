import React, { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import {
  ArrowLeft,
  BrainCircuit,
  ExternalLink,
  FileText,
  CheckCircle2,
  AlertTriangle,
  HelpCircle,
  Layers3,
  Target,
  LockKeyhole,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { jobApi } from '../services/jobApi';
import { Badge } from '../components/common/Badge';
import { Spinner, Alert } from '../components/common/UIFeedback';

function evidenceTypeLabel(kind) {
  if (kind === 'self_report') return 'Self rating';
  if (kind === 'project') return 'Project';
  if (kind === 'certification') return 'Certification';
  return kind || 'Evidence';
}

export function JobAlignmentPage() {
  const { sourceKey, providerId } = useParams();
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();

  const [job, setJob] = useState(null);
  const [comparison, setComparison] = useState(null);
  const [mode, setMode] = useState('semantic');
  const [loading, setLoading] = useState(true);
  const [comparing, setComparing] = useState(false);
  const [error, setError] = useState(null);

  async function loadJob() {
    setLoading(true);
    setError(null);

    try {
      const response = await jobApi.getJob(sourceKey, providerId);
      setJob(response.job);
    } catch (err) {
      setError(err.message || 'Could not load this live job.');
    } finally {
      setLoading(false);
    }
  }

  function requireLoginForAnalysis() {
    const next = `/jobs/${encodeURIComponent(sourceKey)}/${encodeURIComponent(providerId)}`;
    navigate(`/login?next=${encodeURIComponent(next)}`);
  }

  async function runComparison(nextMode = mode) {
    if (!isAuthenticated) {
      requireLoginForAnalysis();
      return;
    }

    setComparing(true);
    setError(null);

    try {
      const response = await jobApi.compareJob(sourceKey, providerId, nextMode);
      setComparison(response.comparison);
      setMode(nextMode);
    } catch (err) {
      if (err.status === 401) {
        requireLoginForAnalysis();
        return;
      }

      setError(err.message || 'Could not compare this job with your evidence.');
    } finally {
      setComparing(false);
    }
  }

  useEffect(() => {
    loadJob();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sourceKey, providerId]);

  const result = comparison?.result;
  const alignment = result?.alignment;
  const model = result?.model;

  if (loading) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <Spinner size="lg" />
      </div>
    );
  }

  if (error && !job) {
    return (
      <div className="space-y-4">
        <Alert type="error" message={error} />
        <button
          onClick={() => navigate('/jobs')}
          className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-primary-600 text-white text-sm font-semibold"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Tech Jobs
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fadeIn">
      <button
        onClick={() => navigate('/jobs')}
        className="inline-flex items-center gap-2 text-sm font-semibold text-slate-600 hover:text-slate-900"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Tech Jobs
      </button>

      {error && <Alert type="error" message={error} />}

      <section className="bg-white rounded-2xl p-6 md:p-8 shadow-sm border border-slate-200">
        <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-5">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant="success">Live posting</Badge>
              <Badge variant="info">{job.provider}</Badge>
            </div>

            <h1 className="text-2xl md:text-3xl font-extrabold text-slate-900 mt-3">
              {job.title}
            </h1>
            <p className="text-base font-semibold text-slate-700 mt-1">
              {job.employer}
            </p>

            <div className="flex flex-wrap gap-4 mt-3 text-xs text-slate-500">
              <span>{job.location || 'Location not specified'}</span>
              <span>{job.work_mode || 'Not specified'}</span>
              <span>{job.experience_level || 'Not specified'}</span>
            </div>
          </div>

          <a
            href={job.source_url}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-slate-900 text-white text-sm font-semibold hover:bg-slate-800"
          >
            View employer posting
            <ExternalLink className="w-4 h-4" />
          </a>
        </div>

        {!!job.tech_tags?.length && (
          <div className="flex flex-wrap gap-2 mt-5">
            {job.tech_tags.map((tag) => (
              <span
                key={tag}
                className="text-[11px] font-semibold px-2.5 py-1.5 rounded-lg bg-slate-100 text-slate-700"
              >
                {tag}
              </span>
            ))}
          </div>
        )}
      </section>

      <section className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5 md:p-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <p className="text-xs font-black uppercase tracking-wider text-primary-600">
              Evidence-backed alignment
            </p>
            <h2 className="text-lg font-bold text-slate-900 mt-1">
              Understand this role before you apply
            </h2>
            <p className="text-xs text-slate-500 mt-1 max-w-2xl">
              The posting can be viewed publicly. Personalized resume, project,
              certification and assessment analysis requires an account.
            </p>
          </div>

          {!isAuthenticated ? (
            <button
              onClick={requireLoginForAnalysis}
              className="inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-primary-600 hover:bg-primary-700 text-white text-xs font-bold shrink-0"
            >
              <LockKeyhole className="w-4 h-4" />
              Sign in to analyze
            </button>
          ) : (
            <div className="flex flex-wrap gap-2">
              <button
                onClick={() => runComparison('keyword')}
                disabled={comparing}
                className={`px-3.5 py-2 rounded-xl text-xs font-bold border ${
                  mode === 'keyword'
                    ? 'bg-slate-900 text-white border-slate-900'
                    : 'border-slate-200 text-slate-700'
                }`}
              >
                Keyword baseline
              </button>

              <button
                onClick={() => runComparison('semantic')}
                disabled={comparing}
                className={`px-3.5 py-2 rounded-xl text-xs font-bold border inline-flex items-center gap-2 ${
                  mode === 'semantic'
                    ? 'bg-primary-600 text-white border-primary-600'
                    : 'border-slate-200 text-slate-700'
                }`}
              >
                <BrainCircuit className="w-4 h-4" />
                SBERT semantic
              </button>
            </div>
          )}
        </div>

        {!isAuthenticated && !comparison && (
          <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-3">
            {[
              ['Resume evidence', 'See whether your resume contains relevant evidence.'],
              ['Projects & certifications', 'Keep practical work distinct from self-ratings.'],
              ['Diagnostics', 'Use assessment results to identify what to practise next.'],
            ].map(([title, text]) => (
              <div key={title} className="rounded-xl bg-slate-50 border border-slate-200 p-4">
                <p className="text-sm font-bold text-slate-800">{title}</p>
                <p className="text-xs text-slate-500 mt-1 leading-5">{text}</p>
              </div>
            ))}
          </div>
        )}

        {comparison && (
          <div className="mt-6 space-y-6">
            {result?.interpretation && (
              <div className="rounded-xl bg-slate-50 border border-slate-200 p-4">
                <p className="text-xs font-bold text-slate-700">Interpretation</p>
                <p className="text-xs text-slate-500 mt-1">
                  {result.interpretation}
                </p>
              </div>
            )}

            {model && (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <div className="rounded-xl border border-slate-200 p-4">
                  <p className="text-[11px] text-slate-400">Model</p>
                  <p className="text-sm font-bold text-slate-900 mt-1">
                    all-MiniLM-L6-v2
                  </p>
                </div>
                <div className="rounded-xl border border-slate-200 p-4">
                  <p className="text-[11px] text-slate-400">Runtime</p>
                  <p className="text-sm font-bold text-slate-900 mt-1">
                    {model.runtime}
                  </p>
                </div>
                <div className="rounded-xl border border-slate-200 p-4">
                  <p className="text-[11px] text-slate-400">Pooling</p>
                  <p className="text-sm font-bold text-slate-900 mt-1">
                    Masked mean + L2
                  </p>
                </div>
                <div className="rounded-xl border border-slate-200 p-4">
                  <p className="text-[11px] text-slate-400">Max tokens</p>
                  <p className="text-sm font-bold text-slate-900 mt-1">
                    {model.max_tokens}
                  </p>
                </div>
              </div>
            )}

            {alignment && (
              <div>
                <div className="flex items-center justify-between mb-3">
                  <div>
                    <h3 className="text-sm font-bold text-slate-900">
                      Evidence coverage
                    </h3>
                    <p className="text-xs text-slate-500 mt-1">
                      Coverage counts are shown independently.
                    </p>
                  </div>
                  <Target className="w-5 h-5 text-primary-600" />
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                  {[
                    ['Resume mentions', alignment.resume_mentions],
                    ['Self-rated skills', alignment.self_ratings],
                    ['Projects / certifications', alignment.project_certificate],
                    ['Diagnostic evidence', alignment.answered_diagnostic],
                  ].map(([label, value]) => (
                    <div key={label} className="rounded-xl border border-slate-200 p-4">
                      <p className="text-xs text-slate-500">{label}</p>
                      <p className="text-2xl font-extrabold text-slate-900 mt-1">
                        {value ?? 0}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div>
              <h3 className="text-sm font-bold text-slate-900 mb-3">
                Skill-by-skill alignment
              </h3>

              <div className="space-y-3">
                {(result?.skills || []).map((skill) => {
                  const candidateEvidence = [
                    ...(skill.candidate_claims || []),
                    ...(skill.related_claims || []),
                    ...(skill.resume_mentions || []),
                  ];

                  const semanticSources = (skill.job_sources || []).filter(
                    (source) => source.method === 'semantic_suggestion'
                  );

                  return (
                    <div
                      key={skill.skill_key}
                      className="rounded-2xl border border-slate-200 p-5"
                    >
                      <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4">
                        <div>
                          <div className="flex flex-wrap items-center gap-2">
                            <h4 className="text-base font-bold text-slate-900">
                              {skill.label}
                            </h4>

                            <Badge
                              variant={
                                skill.mapping === 'keyword'
                                  ? 'info'
                                  : 'purple'
                              }
                            >
                              {skill.mapping === 'keyword'
                                ? 'Direct mention'
                                : 'Semantic suggestion'}
                            </Badge>
                          </div>

                          <p className="text-xs text-slate-500 mt-2">
                            {skill.guidance}
                          </p>

                          {semanticSources.length > 0 && (
                            <div className="mt-3 flex flex-wrap gap-2">
                              {semanticSources.map((source, index) => (
                                <span
                                  key={`${skill.skill_key}-${index}`}
                                  className="text-[11px] font-semibold px-2 py-1 rounded-lg bg-primary-50 text-primary-700"
                                >
                                  similarity {source.similarity} · margin {source.margin}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>

                        <div className="flex items-center gap-2 text-xs shrink-0">
                          {candidateEvidence.length > 0 ? (
                            <span className="inline-flex items-center gap-1.5 text-emerald-700 font-semibold">
                              <CheckCircle2 className="w-4 h-4" />
                              Evidence recorded
                            </span>
                          ) : skill.assessment ? (
                            <span className="inline-flex items-center gap-1.5 text-amber-700 font-semibold">
                              <AlertTriangle className="w-4 h-4" />
                              Diagnostic only
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1.5 text-slate-500 font-semibold">
                              <HelpCircle className="w-4 h-4" />
                              More evidence needed
                            </span>
                          )}
                        </div>
                      </div>

                      {candidateEvidence.length > 0 && (
                        <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-3">
                          {candidateEvidence.slice(0, 6).map((item, index) => (
                            <div
                              key={`${skill.skill_key}-${index}`}
                              className="rounded-xl bg-slate-50 border border-slate-100 p-3"
                            >
                              <p className="text-[11px] uppercase font-bold tracking-wider text-slate-400">
                                {evidenceTypeLabel(item.kind)}
                              </p>

                              <p className="text-xs font-semibold text-slate-800 mt-1">
                                {item.label || item.title || skill.label}
                              </p>

                              {item.rating != null && (
                                <p className="text-[11px] text-slate-500 mt-1">
                                  Self rating: {item.rating}/10
                                </p>
                              )}
                            </div>
                          ))}
                        </div>
                      )}

                      {skill.assessment && (
                        <div className="mt-4 rounded-xl border border-indigo-100 bg-indigo-50/50 p-4">
                          <div className="flex items-center gap-2 text-xs font-bold text-indigo-900">
                            <Layers3 className="w-4 h-4" />
                            Latest diagnostic
                          </div>

                          <p className="text-xs text-indigo-800 mt-1">
                            {skill.assessment.result?.correct_count ?? 0} correct ·{' '}
                            {skill.assessment.result?.incorrect_count ?? 0} incorrect ·{' '}
                            {skill.assessment.result?.unanswered_count ?? 0} unanswered
                          </p>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>

            <div className="flex flex-wrap gap-2 pt-1">
              <Link
                to="/skill-gap"
                className="inline-flex items-center gap-2 px-3.5 py-2 rounded-xl bg-primary-600 text-white text-xs font-bold"
              >
                Review skill gaps
              </Link>

              <Link
                to="/resume"
                className="inline-flex items-center gap-2 px-3.5 py-2 rounded-xl border border-slate-200 text-slate-700 text-xs font-bold"
              >
                Review resume evidence
              </Link>
            </div>
          </div>
        )}
      </section>

      {!isAuthenticated && (
        <section className="rounded-2xl bg-slate-950 text-white p-6">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
              <p className="text-[10px] uppercase tracking-[0.16em] font-black text-indigo-300">
                Personalized career intelligence
              </p>
              <h2 className="text-lg font-black mt-1">
                Browse publicly. Analyze privately.
              </h2>
              <p className="text-xs text-slate-400 mt-1 max-w-2xl">
                Sign in to bring your resume, project and certification evidence
                and assessment results into the comparison.
              </p>
            </div>

            <button
              onClick={requireLoginForAnalysis}
              className="inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-white text-slate-950 text-xs font-extrabold shrink-0"
            >
              Sign in to analyze
            </button>
          </div>
        </section>
      )}
    </div>
  );
}
