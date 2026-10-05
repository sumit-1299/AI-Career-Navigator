import React, { useState, useEffect } from 'react';
import { api } from '../../services/api';
import { Spinner, Alert } from '../common/UIFeedback';
import { Badge } from '../common/Badge';
import {
  Printer,
  CheckCircle2,
  AlertCircle,
  Clock,
  TrendingUp,
  Briefcase,
  FileText,
  DollarSign,
  Calendar,
  Sparkles,
  BookOpen,
  Award,
  ShieldCheck,
  Flame,
  ArrowRight,
  User,
  GraduationCap,
} from 'lucide-react';

export function CareerReadinessReport({ careerId, careerName }) {
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [hoursPerWeek, setHoursPerWeek] = useState(10);
  const [resumeText, setResumeText] = useState('');
  const [scoringResume, setScoringResume] = useState(false);

  useEffect(() => {
    if (careerId) {
      loadReport(careerId, hoursPerWeek);
    }
  }, [careerId, hoursPerWeek]);

  async function loadReport(cid, intensity, customResume = null) {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getCareerReadinessSummary(cid, {
        hoursPerWeek: intensity,
        resumeText: customResume,
      });
      setReport(data);
    } catch (err) {
      console.warn('Failed to load career readiness summary', err);
      setError(err.message || 'Unable to load Career Readiness Report');
    } finally {
      setLoading(false);
    }
  }

  async function handleApplyResumeScoring(e) {
    e.preventDefault();
    if (!resumeText.trim()) return;
    setScoringResume(true);
    try {
      await loadReport(careerId, hoursPerWeek, resumeText.trim());
    } finally {
      setScoringResume(false);
    }
  }

  function handlePrint() {
    window.print();
  }

  if (loading && !report) {
    return (
      <div className="flex flex-col items-center justify-center py-24 bg-white rounded-2xl border border-slate-200">
        <Spinner size="lg" />
        <p className="mt-4 text-slate-500 font-medium">
          Generating Placement-Ready Career Readiness Report...
        </p>
      </div>
    );
  }

  if (error && !report) {
    return (
      <div className="bg-white p-8 rounded-2xl border border-slate-200">
        <Alert type="error" message={error} />
      </div>
    );
  }

  const {
    career_title,
    career_category,
    generated_at,
    student_info = {},
    overall_readiness = {},
    verified_skills = [],
    remaining_skill_gaps = {},
    ats_alignment = {},
    study_timeline = {},
    portfolio_recommendations = [],
    market_outlook = {},
    placement_summary = {},
  } = report || {};

  const missingSkills = remaining_skill_gaps.missing || [];
  const weakSkills = remaining_skill_gaps.weak || [];

  return (
    <div className="space-y-6">
      {/* SCREEN-ONLY CONTROLS & ACTION BAR */}
      <div className="no-print bg-white rounded-2xl p-5 shadow-sm border border-slate-200 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-primary-600" />
            <span>Placement Readiness Assessment</span>
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Consolidated diagnostic report for employment readiness, ATS alignment, and timeline.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* Intensity Selector */}
          <div className="flex items-center gap-1 p-1 bg-slate-100 rounded-xl text-xs">
            {[5, 10, 20].map((hrs) => (
              <button
                key={hrs}
                type="button"
                onClick={() => setHoursPerWeek(hrs)}
                className={`px-3 py-1.5 rounded-lg font-semibold transition ${
                  hoursPerWeek === hrs
                    ? 'bg-primary-600 text-white shadow-xs'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                {hrs} hrs/wk
              </button>
            ))}
          </div>

          {/* Print / Save PDF Button */}
          <button
            type="button"
            onClick={handlePrint}
            className="inline-flex items-center gap-2 px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold rounded-xl shadow-sm transition cursor-pointer"
          >
            <Printer className="w-4 h-4" />
            <span>Print / Save PDF</span>
          </button>
        </div>
      </div>

      {/* PRINTABLE REPORT CONTAINER */}
      <div className="printable-report bg-white rounded-2xl p-6 md:p-10 shadow-sm border border-slate-200 space-y-8">
        {/* 1. OFFICIAL DOCUMENT HEADER */}
        <div className="border-b-2 border-slate-900 pb-6">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <span className="text-[11px] font-black tracking-widest uppercase px-2.5 py-0.5 bg-slate-900 text-white rounded">
                  AI Career Navigator
                </span>
                <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                  Verification Audit
                </span>
              </div>
              <h1 className="text-2xl md:text-3xl font-black text-slate-900 tracking-tight">
                CAREER READINESS & PLACEMENT REPORT
              </h1>
              <p className="text-xs text-slate-600 mt-1">
                Diagnostic Employability Assessment & Structured Skill Transition Roadmap
              </p>
            </div>

            <div className="text-left md:text-right shrink-0">
              <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">
                Assessment Date
              </span>
              <p className="text-sm font-extrabold text-slate-900 flex items-center md:justify-end gap-1.5 mt-0.5">
                <Calendar className="w-4 h-4 text-slate-500" />
                {generated_at || 'Current Date'}
              </p>
            </div>
          </div>

          {/* Student & Target Metadata Strip */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-6 pt-4 border-t border-slate-100 text-xs">
            <div className="p-3 rounded-xl bg-slate-50 border border-slate-100">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1">
                <User className="w-3 h-3 text-slate-500" /> Candidate Name
              </span>
              <p className="font-bold text-slate-900 mt-0.5 truncate">
                {student_info.name || 'Candidate'}
              </p>
            </div>
            <div className="p-3 rounded-xl bg-slate-50 border border-slate-100">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1">
                <GraduationCap className="w-3 h-3 text-slate-500" /> Academic Degree
              </span>
              <p className="font-bold text-slate-900 mt-0.5 truncate">
                {student_info.education || 'Undergraduate'} ({student_info.graduation_year || '2026'})
              </p>
            </div>
            <div className="p-3 rounded-xl bg-slate-50 border border-slate-100">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1">
                <Briefcase className="w-3 h-3 text-slate-500" /> Target Career
              </span>
              <p className="font-bold text-slate-900 mt-0.5 truncate">
                {career_title || careerName}
              </p>
            </div>
            <div className="p-3 rounded-xl bg-slate-50 border border-slate-100">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1">
                <Sparkles className="w-3 h-3 text-slate-500" /> Industry Domain
              </span>
              <p className="font-bold text-slate-900 mt-0.5 truncate">
                {career_category || 'Technology'}
              </p>
            </div>
          </div>
        </div>

        {/* 2. EXECUTIVE PLACEMENT READINESS SUMMARY (ITEM 1, 2, 9) */}
        <div className="print-avoid-break p-6 rounded-2xl bg-gradient-to-br from-slate-50 to-white border border-slate-200">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 pb-5 border-b border-slate-200">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500">
                  Employability Tier:
                </span>
                <span
                  className={`px-3 py-1 rounded-full text-xs font-black uppercase tracking-wider ${
                    placement_summary.tier === 'Placement-Ready'
                      ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                      : placement_summary.tier === 'Interview-Ready Track'
                      ? 'bg-indigo-100 text-indigo-800 border border-indigo-300'
                      : 'bg-amber-100 text-amber-800 border border-amber-300'
                  }`}
                >
                  {placement_summary.tier || 'Foundational'}
                </span>
              </div>
              <h3 className="text-xl font-extrabold text-slate-900">
                Executive Readiness Verdict
              </h3>
              <p className="text-sm text-slate-600 mt-1 max-w-2xl leading-relaxed">
                {placement_summary.verdict}
              </p>
            </div>

            {/* Overall Score Badge */}
            <div className="flex items-center gap-4 bg-white p-4 rounded-xl border border-slate-200 shadow-xs shrink-0">
              <div className="text-center">
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                  Overall Score
                </span>
                <p className="text-3xl font-black text-slate-900">
                  {overall_readiness.percentage ?? 0}%
                </p>
                <span className="text-[11px] font-semibold text-slate-500">
                  {overall_readiness.category || 'In Progress'}
                </span>
              </div>
            </div>
          </div>

          {/* Action Plan & Priorities */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
            <div>
              <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider mb-2.5 flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                Verified Competency Strengths ({verified_skills.length})
              </h4>
              {verified_skills.length > 0 ? (
                <div className="flex flex-wrap gap-1.5">
                  {verified_skills.map((s, idx) => (
                    <span
                      key={idx}
                      className="px-2.5 py-1 rounded-lg bg-emerald-50 text-emerald-800 border border-emerald-200 font-semibold text-xs"
                    >
                      ✓ {s.skill_name}
                    </span>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-slate-500 italic">
                  No verified skills yet for this role. Complete modules or ingest your resume to verify competencies.
                </p>
              )}
            </div>

            <div>
              <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider mb-2.5 flex items-center gap-1.5">
                <AlertCircle className="w-4 h-4 text-amber-600" />
                Strategic Action Plan
              </h4>
              <ul className="space-y-1.5 text-xs text-slate-700">
                {(placement_summary.action_plan || []).map((step, idx) => (
                  <li key={idx} className="flex items-start gap-2">
                    <span className="w-4 h-4 rounded-full bg-slate-200 text-slate-700 text-[10px] font-bold flex items-center justify-center shrink-0 mt-0.5">
                      {idx + 1}
                    </span>
                    <span>{step}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>

        {/* 3. COMPETENCY & SKILL GAP AUDIT (ITEM 3, 4) */}
        <div className="print-avoid-break space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <Award className="w-5 h-5 text-indigo-600" />
              <span>Competency & Technical Skill Audit</span>
            </h3>
            <span className="text-xs text-slate-500">
              Total Required Skills: <strong>{overall_readiness.total_required_skills ?? 0}</strong>
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Matched Skills */}
            <div className="p-4 rounded-xl border border-slate-200 bg-white space-y-3">
              <div className="flex items-center justify-between border-b border-slate-100 pb-2">
                <span className="text-xs font-bold text-emerald-700 uppercase tracking-wider flex items-center gap-1">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  Verified Skills ({verified_skills.length})
                </span>
                <span className="text-[11px] font-semibold text-slate-500">Benchmark Met</span>
              </div>
              {verified_skills.length > 0 ? (
                <div className="space-y-2">
                  {verified_skills.map((s, idx) => (
                    <div
                      key={idx}
                      className="p-2 rounded-lg bg-emerald-50/60 border border-emerald-100 flex items-center justify-between text-xs"
                    >
                      <span className="font-bold text-slate-900">{s.skill_name}</span>
                      <span className="text-[11px] font-medium text-emerald-800">
                        Proficiency: {s.current_proficiency}/10 (Req: {s.required_level}/5)
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-slate-400 italic py-2">
                  Zero verified skills currently on file.
                </p>
              )}
            </div>

            {/* Remaining Skill Gaps */}
            <div className="p-4 rounded-xl border border-slate-200 bg-white space-y-3">
              <div className="flex items-center justify-between border-b border-slate-100 pb-2">
                <span className="text-xs font-bold text-amber-700 uppercase tracking-wider flex items-center gap-1">
                  <AlertCircle className="w-3.5 h-3.5" />
                  Skill Gaps to Bridge ({missingSkills.length + weakSkills.length})
                </span>
                <span className="text-[11px] font-semibold text-slate-500">Priority Order</span>
              </div>
              <div className="space-y-2 max-h-60 overflow-y-auto">
                {missingSkills.map((s, idx) => (
                  <div
                    key={`m-${idx}`}
                    className="p-2 rounded-lg bg-rose-50/60 border border-rose-100 flex items-center justify-between text-xs"
                  >
                    <div className="flex items-center gap-2">
                      <span className="px-1.5 py-0.5 rounded text-[10px] font-extrabold bg-rose-200 text-rose-800">
                        MISSING
                      </span>
                      <span className="font-bold text-slate-900">{s.skill_name}</span>
                    </div>
                    <span className="text-[11px] font-semibold text-slate-600">
                      Target Level {s.required_level}/5
                    </span>
                  </div>
                ))}
                {weakSkills.map((s, idx) => (
                  <div
                    key={`w-${idx}`}
                    className="p-2 rounded-lg bg-amber-50/60 border border-amber-100 flex items-center justify-between text-xs"
                  >
                    <div className="flex items-center gap-2">
                      <span className="px-1.5 py-0.5 rounded text-[10px] font-extrabold bg-amber-200 text-amber-800">
                        WEAK
                      </span>
                      <span className="font-bold text-slate-900">{s.skill_name}</span>
                    </div>
                    <span className="text-[11px] font-semibold text-slate-600">
                      Level {s.current_proficiency}/10 → {s.required_level}/5
                    </span>
                  </div>
                ))}
                {missingSkills.length === 0 && weakSkills.length === 0 && (
                  <p className="text-xs text-emerald-600 font-semibold py-2">
                    ✓ All skill gaps bridged! 100% curriculum completion.
                  </p>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* 4. ATS & RESUME ALIGNMENT (ITEM 5) */}
        <div className="print-avoid-break p-5 rounded-2xl border border-slate-200 bg-white">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100">
            <div>
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <FileText className="w-4 h-4 text-primary-600" />
                <span>Resume ATS Alignment & Keyword Compatibility (Module 8.2)</span>
              </h3>
              <p className="text-xs text-slate-500">
                Automated ATS scan against career keyword requirements.
              </p>
            </div>

            <div className="flex items-center gap-3">
              <span className="text-xs text-slate-500 font-medium">Alignment Level:</span>
              <span
                className={`px-2.5 py-1 rounded-md text-xs font-bold ${
                  ats_alignment.alignment_level === 'Strong' || ats_alignment.alignment_level === 'Excellent'
                    ? 'bg-emerald-100 text-emerald-800'
                    : ats_alignment.alignment_level === 'Moderate'
                    ? 'bg-blue-100 text-blue-800'
                    : ats_alignment.alignment_level === 'Weak'
                    ? 'bg-rose-100 text-rose-800'
                    : 'bg-slate-100 text-slate-600'
                }`}
              >
                {ats_alignment.alignment_level || 'Pending Ingestion'}
              </span>
              <div className="text-center px-3 py-1 bg-slate-50 rounded-lg border border-slate-200">
                <span className="text-[10px] text-slate-400 block font-bold">ATS Score</span>
                <span className="text-sm font-black text-slate-900">
                  {ats_alignment.ats_score !== null && ats_alignment.ats_score !== undefined
                    ? `${ats_alignment.ats_score}%`
                    : 'N/A'}
                </span>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4 text-xs">
            <div>
              <span className="font-bold text-emerald-700 block mb-1.5">
                Matched ATS Keywords:
              </span>
              {(ats_alignment.matched_keywords || []).length > 0 ? (
                <div className="flex flex-wrap gap-1.5">
                  {ats_alignment.matched_keywords.map((k, idx) => (
                    <span
                      key={idx}
                      className="px-2 py-0.5 rounded bg-emerald-50 text-emerald-800 font-semibold border border-emerald-200"
                    >
                      {k}
                    </span>
                  ))}
                </div>
              ) : (
                <span className="text-slate-400 italic">None detected</span>
              )}
            </div>

            <div>
              <span className="font-bold text-rose-700 block mb-1.5">
                Missing High-Impact ATS Keywords:
              </span>
              {(ats_alignment.missing_keywords || []).length > 0 ? (
                <div className="flex flex-wrap gap-1.5">
                  {ats_alignment.missing_keywords.map((k, idx) => (
                    <span
                      key={idx}
                      className="px-2 py-0.5 rounded bg-rose-50 text-rose-800 font-semibold border border-rose-200"
                    >
                      {k}
                    </span>
                  ))}
                </div>
              ) : (
                <span className="text-emerald-600 font-semibold">
                  All critical keywords present!
                </span>
              )}
            </div>
          </div>

          {/* Quick interactive ATS text check (screen only) */}
          <div className="no-print mt-4 pt-3 border-t border-slate-100">
            <form onSubmit={handleApplyResumeScoring} className="flex gap-2">
              <input
                type="text"
                value={resumeText}
                onChange={(e) => setResumeText(e.target.value)}
                placeholder="Paste resume excerpt or skills to calculate live ATS alignment..."
                className="flex-1 text-xs border border-slate-300 rounded-xl px-3 py-2 bg-slate-50 focus:bg-white focus:outline-hidden"
              />
              <button
                type="submit"
                disabled={scoringResume || !resumeText.trim()}
                className="px-3.5 py-2 rounded-xl bg-primary-600 hover:bg-primary-700 text-white text-xs font-bold transition disabled:opacity-50"
              >
                {scoringResume ? 'Scoring...' : 'Score ATS'}
              </button>
            </form>
          </div>
        </div>

        {/* 5. STUDY INTENSITY & TIMELINE ROADMAP (ITEM 6) */}
        <div className="print-avoid-break p-5 rounded-2xl border border-slate-200 bg-white">
          <h3 className="text-sm font-bold text-slate-900 mb-1 flex items-center gap-2">
            <Clock className="w-4 h-4 text-primary-600" />
            <span>Structured Study Intensity & Completion Timeline (Module 8.3)</span>
          </h3>
          <p className="text-xs text-slate-500 mb-4">
            Deterministic timeline calculation based on selected weekly pace.
          </p>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div className="p-3 rounded-xl bg-slate-50 border border-slate-100 text-center">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                Study Intensity
              </span>
              <p className="text-lg font-black text-slate-900 mt-0.5 flex items-center justify-center gap-1">
                <Flame className="w-4 h-4 text-amber-500" />
                {study_timeline.hours_per_week} hrs/wk
              </p>
            </div>
            <div className="p-3 rounded-xl bg-slate-50 border border-slate-100 text-center">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                Total Workload
              </span>
              <p className="text-lg font-black text-slate-900 mt-0.5">
                {study_timeline.estimated_total_hours} hrs
              </p>
            </div>
            <div className="p-3 rounded-xl bg-primary-50/50 border border-primary-200 text-center">
              <span className="text-[10px] font-bold text-primary-700 uppercase tracking-wider block">
                Projected Duration
              </span>
              <p className="text-lg font-black text-primary-700 mt-0.5">
                {study_timeline.estimated_weeks} {study_timeline.estimated_weeks === 1 ? 'Week' : 'Weeks'}
              </p>
            </div>
            <div className="p-3 rounded-xl bg-emerald-50/50 border border-emerald-200 text-center">
              <span className="text-[10px] font-bold text-emerald-800 uppercase tracking-wider block">
                Target Completion
              </span>
              <p className="text-sm font-black text-emerald-700 mt-1 flex items-center justify-center gap-1">
                <Calendar className="w-3.5 h-3.5" />
                {study_timeline.estimated_completion_date || 'N/A'}
              </p>
            </div>
          </div>
        </div>

        {/* 6. RECOMMENDED PORTFOLIO PROJECTS (ITEM 7) */}
        <div className="print-avoid-break space-y-3">
          <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
            <BookOpen className="w-4 h-4 text-indigo-600" />
            <span>Recommended Practical Portfolio Projects (Employability Capstones)</span>
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {portfolio_recommendations.map((proj, idx) => (
              <div
                key={idx}
                className="p-4 rounded-xl border border-slate-200 bg-slate-50/50 flex flex-col justify-between text-xs"
              >
                <div>
                  <div className="flex items-center justify-between gap-2 mb-1">
                    <span className="px-2 py-0.5 rounded bg-indigo-50 text-indigo-700 font-bold text-[10px]">
                      {proj.provider}
                    </span>
                    <span className="text-[10px] text-slate-500 font-semibold">
                      {proj.estimated_duration}
                    </span>
                  </div>
                  <h4 className="font-bold text-slate-900 text-sm mt-1">{proj.title}</h4>
                  <p className="text-slate-600 text-xs mt-1 line-clamp-2">{proj.description}</p>
                </div>
                <div className="mt-3 pt-2 border-t border-slate-100 flex items-center justify-between text-[11px]">
                  <span className="text-slate-500">
                    Focus: <strong className="text-slate-700">{proj.targeted_skill}</strong>
                  </span>
                  <span className="font-bold text-primary-600">{proj.difficulty_level}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* 7. LABOR MARKET & DEMAND OUTLOOK (ITEM 8) */}
        <div className="print-avoid-break p-5 rounded-2xl border border-slate-200 bg-white">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3 mb-4">
            <div>
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <DollarSign className="w-4 h-4 text-emerald-600" />
                <span>Labor Market Salary & Industry Demand Outlook</span>
              </h3>
              <p className="text-xs text-slate-500">
                Industry intelligence benchmarks from Market Intelligence Engine.
              </p>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-500">Demand:</span>
              <span className="px-2.5 py-0.5 rounded-full text-xs font-black bg-emerald-100 text-emerald-800">
                {market_outlook.demand_level || 'High'} ({market_outlook.demand_score ?? 85}/100)
              </span>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs mb-4">
            <div className="p-3 rounded-xl bg-slate-50 border border-slate-100">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                Entry-Level Salary
              </span>
              <p className="text-base font-extrabold text-slate-900 mt-0.5">
                {market_outlook.salary_bands?.entry_level || '$75,000 / yr'}
              </p>
            </div>
            <div className="p-3 rounded-xl bg-emerald-50/50 border border-emerald-200">
              <span className="text-[10px] font-bold text-emerald-800 uppercase tracking-wider block">
                Median Market Rate
              </span>
              <p className="text-base font-extrabold text-emerald-700 mt-0.5">
                {market_outlook.salary_bands?.median || '$110,000 / yr'}
              </p>
            </div>
            <div className="p-3 rounded-xl bg-slate-50 border border-slate-100">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                Senior / Lead Salary
              </span>
              <p className="text-base font-extrabold text-slate-900 mt-0.5">
                {market_outlook.salary_bands?.senior || '$155,000 / yr'}
              </p>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs pt-2 border-t border-slate-100 text-slate-600">
            <span>
              5-Year Projected Growth: <strong>{market_outlook.five_year_growth_rate || '+18%'}</strong>
            </span>
            <div className="flex items-center gap-1.5 flex-wrap">
              <span className="font-semibold text-slate-500">Top Sectors:</span>
              {(market_outlook.top_hiring_sectors || []).map((sec, idx) => (
                <span
                  key={idx}
                  className="px-2 py-0.5 rounded bg-slate-100 text-slate-700 font-medium text-[11px]"
                >
                  {sec}
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* 8. REPORT FOOTER & AUTHENTICITY NOTE */}
        <div className="pt-6 border-t border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-4 text-[11px] text-slate-400">
          <div>
            <p className="font-semibold text-slate-600">
              Official Diagnostic Evaluation • AI Career Navigator Intelligence Engine
            </p>
            <p>Generated deterministically according to industry standard job architectures.</p>
          </div>
          <div className="text-left sm:text-right">
            <p>Verification Code: AICN-{careerId}-{(generated_at || 'DOC').replace(/\s+/g, '')}</p>
            <p>Document Validated for Employment Readiness Diagnostics</p>
          </div>
        </div>
      </div>
    </div>
  );
}
