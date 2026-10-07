import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';
import { jobApi } from '../services/jobApi';
import { RadialGauge } from '../components/common/RadialGauge';
import { Badge } from '../components/common/Badge';
import { ProgressBar } from '../components/common/ProgressBar';
import { Spinner, Alert } from '../components/common/UIFeedback';
import {
  Briefcase,
  Target,
  Sparkles,
  TrendingUp,
  ArrowRight,
  BookOpen,
  FileText,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  Clock,
  Compass,
  BrainCircuit,
  MapPin,
  ChevronRight,
} from 'lucide-react';

export function DashboardPage() {
  const { user, targetCareerId, setTargetCareerId } = useAuth();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [careers, setCareers] = useState([]);
  const [readinessData, setReadinessData] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [activeProgress, setActiveProgress] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [roiData, setRoiData] = useState(null);
  const [recentComparisons, setRecentComparisons] = useState([]);

  useEffect(() => {
    loadDashboardData();
  }, [targetCareerId]);

  async function loadDashboardData() {
    setLoading(true);
    setError(null);

    try {
      let careerList = [];

      try {
        const careersRes = await api.listCareers();
        careerList = careersRes?.careers || [];
        setCareers(careerList);
      } catch (err) {
        console.warn('Could not load careers list', err);
      }

      const activeCareer =
        careerList.find((c) => c.id === targetCareerId) || careerList[0];

      const activeId = activeCareer?.id || targetCareerId || 1;

      if (activeId) {
        try {
          const gapRes = await api.getSkillGap(activeId);
          setReadinessData(gapRes);
        } catch (err) {
          console.warn('Could not load skill gap', err);
        }

        try {
          const analyticsRes = await api.getCareerAnalytics(activeId);
          setAnalytics(analyticsRes);
        } catch (err) {
          console.warn('Could not load analytics', err);
        }

        try {
          const roiRes = await api.getCareerSkillRoi(activeId);
          setRoiData(roiRes);
        } catch (err) {
          console.warn('Could not load skill ROI', err);
        }
      }

      try {
        const recRes = await api.getCareerRecommendations();
        setRecommendations(recRes?.recommendations || []);
      } catch (err) {
        console.warn('Could not load recommendations', err);
      }

      try {
        const progressRes = await api.getUserLearningProgress('In Progress');
        setActiveProgress(progressRes?.progress_items || []);
      } catch (err) {
        console.warn('Could not load active progress', err);
      }

      try {
        const comparisonRes = await jobApi.getRecentComparisons();
        setRecentComparisons(comparisonRes?.comparisons || []);
      } catch (err) {
        // This should never block the dashboard.
        console.warn('Could not load recent job comparisons', err);
      }
    } catch (err) {
      setError(err.message || 'Failed to load career dashboard');
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <Spinner size="lg" />
        <p className="mt-4 text-slate-500 font-medium">
          Computing career intelligence metrics...
        </p>
      </div>
    );
  }

  const activeCareer =
    careers.find((c) => c.id === targetCareerId) || careers[0];

  const activeCareerName =
    activeCareer?.career_name || activeCareer?.title || 'your target role';

  const readinessScore = Math.round(
    readinessData?.readiness_percentage ?? readinessData?.readiness_score ?? 0
  );

  const readinessCategory =
    readinessData?.readiness_category ??
    (readinessScore >= 80
      ? 'Advanced'
      : readinessScore >= 60
        ? 'Proficient'
        : readinessScore >= 30
          ? 'Developing'
          : 'Novice');

  const matchedCount =
    readinessData?.matched ?? readinessData?.matched_count ?? 0;

  const weakCount =
    readinessData?.weak ?? readinessData?.weak_count ?? 0;

  const missingCount =
    readinessData?.missing ?? readinessData?.missing_count ?? 0;

  const totalSkills =
    readinessData?.total_required_skills ??
    readinessData?.total_career_skills ??
    (matchedCount + weakCount + missingCount || 1);

  const missingSkills =
    readinessData?.missing_skills ||
    readinessData?.skill_gaps?.filter((s) => s.status === 'MISSING') ||
    [];

  const weakSkills =
    readinessData?.weak_skills ||
    readinessData?.skill_gaps?.filter((s) => s.status === 'WEAK') ||
    [];

  const prioritySkill =
    missingSkills[0] ||
    weakSkills[0] ||
    null;

  const prioritySkillName =
    prioritySkill?.skill_name || prioritySkill?.name || null;

  return (
    <div className="space-y-7 animate-fadeIn">
      {/* Product hero */}
      <section className="relative overflow-hidden rounded-3xl bg-slate-950 text-white shadow-xl">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_0%_0%,rgba(99,102,241,0.42),transparent_36%),radial-gradient(circle_at_100%_100%,rgba(14,165,233,0.18),transparent_30%)]" />
        <div className="relative p-6 md:p-8">
          <div className="flex flex-col xl:flex-row xl:items-end xl:justify-between gap-7">
            <div className="max-w-3xl">
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-[10px] font-black uppercase tracking-[0.18em] text-indigo-300">
                  Career intelligence workspace
                </span>
                <span className="px-2 py-1 rounded-full text-[10px] font-bold bg-white/10 text-slate-200 border border-white/10">
                  Evidence-driven
                </span>
              </div>

              <h1 className="mt-3 text-3xl md:text-4xl font-black tracking-tight leading-tight">
                Welcome back, {user?.name || 'Explorer'}.
              </h1>

              <p className="mt-3 text-sm md:text-base text-slate-300 max-w-2xl leading-6">
                Find a live technology role, understand how your evidence aligns,
                then focus your time on the next skill or practical task that matters.
              </p>

              <div className="flex flex-wrap gap-3 mt-6">
                <Link
                  to="/jobs"
                  className="inline-flex items-center gap-2 px-4 py-3 rounded-xl bg-white text-slate-950 text-sm font-extrabold hover:bg-slate-100 transition"
                >
                  <Briefcase className="w-4 h-4" />
                  Find Tech Jobs
                  <ArrowRight className="w-4 h-4" />
                </Link>

                <Link
                  to={`/skill-gap?career_id=${targetCareerId}`}
                  className="inline-flex items-center gap-2 px-4 py-3 rounded-xl bg-white/10 border border-white/15 text-white text-sm font-bold hover:bg-white/15 transition"
                >
                  <Target className="w-4 h-4" />
                  Review Skill Gap
                </Link>
              </div>
            </div>

            <div className="w-full xl:w-[330px] rounded-2xl border border-white/10 bg-white/[0.06] backdrop-blur p-5">
              <p className="text-[10px] uppercase tracking-wider font-black text-slate-400">
                Current target
              </p>

              <div className="flex items-center gap-3 mt-2">
                <div className="p-2.5 rounded-xl bg-indigo-500/20 text-indigo-300">
                  <Compass className="w-5 h-5" />
                </div>
                <div className="min-w-0">
                  <p className="font-extrabold text-white truncate">
                    {activeCareerName}
                  </p>
                  <p className="text-xs text-slate-400 truncate">
                    {activeCareer?.domain || 'Technology career path'}
                  </p>
                </div>
              </div>

              <div className="mt-4 pt-4 border-t border-white/10 flex items-end justify-between">
                <div>
                  <p className="text-[10px] uppercase tracking-wider text-slate-500 font-black">
                    Readiness
                  </p>
                  <p className="mt-1 text-2xl font-black">{readinessScore}%</p>
                </div>
                <Badge
                  variant={
                    readinessCategory === 'Advanced'
                      ? 'success'
                      : readinessCategory === 'Proficient'
                        ? 'info'
                        : readinessCategory === 'Developing'
                          ? 'warning'
                          : 'neutral'
                  }
                >
                  {readinessCategory}
                </Badge>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Career action path */}
      <section className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5 md:p-6">
        <div className="flex items-center justify-between gap-4 mb-5">
          <div>
            <p className="text-[10px] uppercase tracking-[0.16em] font-black text-primary-600">
              Your career loop
            </p>
            <h2 className="text-lg font-extrabold text-slate-900 mt-1">
              Move from discovery to evidence
            </h2>
          </div>
          <BrainCircuit className="w-5 h-5 text-primary-600" />
        </div>

        <div className="grid grid-cols-2 md:grid-cols-5 gap-2">
          {[
            ['01', 'Discover', 'Find live tech roles', '/jobs'],
            ['02', 'Align', 'Compare evidence', '/jobs'],
            ['03', 'Close gap', 'Target a priority skill', `/skill-gap?career_id=${targetCareerId}`],
            ['04', 'Build', 'Learn or practise', '/learning'],
            ['05', 'Re-align', 'Check progress again', '/jobs'],
          ].map(([number, title, subtitle, to], index, items) => (
            <React.Fragment key={title}>
              <Link
                to={to}
                className="group rounded-xl border border-slate-200 bg-slate-50 p-4 hover:bg-white hover:border-primary-300 hover:shadow-sm transition"
              >
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-black text-slate-400">{number}</span>
                  <ChevronRight className="w-3.5 h-3.5 text-slate-300 group-hover:text-primary-500 transition" />
                </div>
                <p className="text-sm font-extrabold text-slate-900 mt-3">{title}</p>
                <p className="text-[11px] leading-4 text-slate-500 mt-1">{subtitle}</p>
              </Link>

              {index < items.length - 1 && (
                <div className="hidden md:flex items-center justify-center text-slate-300 -mx-1">
                  <ArrowRight className="w-4 h-4" />
                </div>
              )}
            </React.Fragment>
          ))}
        </div>
      </section>

      {error && <Alert type="error" message={error} />}

      {/* Main decision card */}
      <section className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="grid grid-cols-1 lg:grid-cols-[1.25fr_0.75fr]">
          <div className="p-6 md:p-7">
            <div className="flex items-center gap-2">
              <div className="p-2.5 rounded-xl bg-amber-50 text-amber-600">
                <Target className="w-5 h-5" />
              </div>
              <span className="text-xs font-black uppercase tracking-wider text-amber-700">
                Next best action
              </span>
            </div>

            <h2 className="text-xl md:text-2xl font-black text-slate-900 mt-4">
              {prioritySkillName
                ? `Strengthen ${prioritySkillName} before your next comparison.`
                : 'Choose a live tech role and start your next comparison.'}
            </h2>

            <p className="text-sm text-slate-500 leading-6 mt-2 max-w-2xl">
              {prioritySkillName
                ? `Your current ${activeCareerName} evidence suggests this is a useful place to focus. Use the existing learning and practical-work flow rather than trying to improve everything at once.`
                : 'Start with a real vacancy, compare its requirements with your evidence, and let the resulting gaps guide what you practise next.'}
            </p>

            <div className="flex flex-wrap gap-2 mt-5">
              <Link
                to={
                  prioritySkill?.canonical_skill_id
                    ? `/learning?skill_id=${prioritySkill.canonical_skill_id}`
                    : `/skill-gap?career_id=${targetCareerId}`
                }
                className="inline-flex items-center gap-2 px-3.5 py-2.5 rounded-xl bg-primary-600 hover:bg-primary-700 text-white text-xs font-bold"
              >
                {prioritySkillName ? 'Work on this skill' : 'Review my skill gap'}
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>

              <Link
                to="/jobs"
                className="inline-flex items-center gap-2 px-3.5 py-2.5 rounded-xl border border-slate-200 text-slate-700 text-xs font-bold hover:bg-slate-50"
              >
                Find a role to compare
              </Link>
            </div>
          </div>

          <div className="bg-slate-50 border-t lg:border-t-0 lg:border-l border-slate-200 p-6 md:p-7">
            <p className="text-[10px] uppercase tracking-wider font-black text-slate-400">
              Evidence signals
            </p>
            <div className="grid grid-cols-3 gap-3 mt-4">
              <div className="rounded-xl bg-white border border-slate-200 p-3">
                <p className="text-[10px] text-slate-400">Matched</p>
                <p className="text-xl font-black text-emerald-700 mt-1">{matchedCount}</p>
              </div>
              <div className="rounded-xl bg-white border border-slate-200 p-3">
                <p className="text-[10px] text-slate-400">Weak</p>
                <p className="text-xl font-black text-amber-700 mt-1">{weakCount}</p>
              </div>
              <div className="rounded-xl bg-white border border-slate-200 p-3">
                <p className="text-[10px] text-slate-400">Missing</p>
                <p className="text-xl font-black text-rose-700 mt-1">{missingCount}</p>
              </div>
            </div>

            <div className="mt-4">
              <ProgressBar
                value={matchedCount}
                max={Math.max(1, totalSkills)}
                color="bg-emerald-500"
              />
              <p className="text-[11px] text-slate-500 mt-2">
                {totalSkills} canonical skills considered for {activeCareerName}.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Live jobs / recent alignment */}
      <section className="grid grid-cols-1 lg:grid-cols-[1.1fr_0.9fr] gap-6">
        <Link
          to="/jobs"
          className="group relative overflow-hidden rounded-2xl bg-gradient-to-br from-indigo-600 to-violet-700 text-white p-6 shadow-lg shadow-indigo-600/15"
        >
          <div className="absolute -right-10 -top-10 w-40 h-40 rounded-full bg-white/10" />
          <div className="relative">
            <div className="flex items-center justify-between">
              <div className="p-2.5 rounded-xl bg-white/10">
                <Briefcase className="w-5 h-5" />
              </div>
              <ArrowRight className="w-5 h-5 opacity-60 group-hover:translate-x-1 transition" />
            </div>

            <p className="text-[10px] uppercase tracking-[0.16em] font-black text-indigo-200 mt-6">
              Live technology hiring
            </p>
            <h2 className="text-xl font-black mt-1">
              Find a role worth analysing.
            </h2>
            <p className="text-sm text-indigo-100 leading-6 mt-2 max-w-lg">
              Search current technology vacancies by role, location, technology,
              work mode and experience. Then open a role to compare it with your evidence.
            </p>

            <div className="flex flex-wrap gap-2 mt-5">
              <span className="px-2.5 py-1 rounded-lg bg-white/10 text-[11px] font-bold">
                Python
              </span>
              <span className="px-2.5 py-1 rounded-lg bg-white/10 text-[11px] font-bold">
                Backend
              </span>
              <span className="px-2.5 py-1 rounded-lg bg-white/10 text-[11px] font-bold">
                Cloud
              </span>
              <span className="px-2.5 py-1 rounded-lg bg-white/10 text-[11px] font-bold">
                Data
              </span>
            </div>
          </div>
        </Link>

        <div className="rounded-2xl bg-white border border-slate-200 shadow-sm p-6">
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="text-[10px] uppercase tracking-wider font-black text-primary-600">
                Recent alignment
              </p>
              <h2 className="text-lg font-extrabold text-slate-900 mt-1">
                Your latest job analysis
              </h2>
            </div>
            <BrainCircuit className="w-5 h-5 text-primary-600" />
          </div>

          {recentComparisons.length === 0 ? (
            <div className="mt-5 rounded-xl border border-dashed border-slate-300 bg-slate-50 p-5">
              <p className="text-sm font-bold text-slate-800">
                No saved job comparisons yet.
              </p>
              <p className="text-xs text-slate-500 leading-5 mt-1">
                Pick a live technology role and run the semantic alignment to create your first comparison snapshot.
              </p>
              <Link
                to="/jobs"
                className="inline-flex items-center gap-2 mt-4 text-xs font-bold text-primary-600 hover:underline"
              >
                Start with Tech Jobs
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          ) : (
            <div className="mt-5 space-y-3">
              {recentComparisons.slice(0, 2).map((item) => {
                const job = item.job || {};
                const result = item.result || {};
                const comparisonId = item.id || item.comparison_id;

                return (
                  <Link
                    key={comparisonId}
                    to={comparisonId ? `/job-alignment/${comparisonId}` : '/jobs'}
                    className="block rounded-xl border border-slate-200 p-4 hover:border-primary-300 hover:bg-slate-50 transition"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0">
                        <p className="font-bold text-sm text-slate-900 truncate">
                          {job.title || 'Job comparison'}
                        </p>
                        <p className="text-xs text-slate-500 mt-1">
                          {job.employer || job.source_type || 'Live posting'}
                        </p>
                      </div>

                      <Badge variant={result.mode === 'semantic' ? 'purple' : 'info'}>
                        {result.mode === 'semantic' ? 'SBERT' : 'Keyword'}
                      </Badge>
                    </div>

                    <div className="flex flex-wrap gap-3 mt-3 text-[11px] text-slate-500">
                      {job.location && (
                        <span className="inline-flex items-center gap-1">
                          <MapPin className="w-3 h-3" />
                          {job.location}
                        </span>
                      )}
                      {result.summary?.semantic_suggestions != null && (
                        <span>
                          {result.summary.semantic_suggestions} semantic suggestions
                        </span>
                      )}
                    </div>
                  </Link>
                );
              })}
            </div>
          )}
        </div>
      </section>

      {/* ROI */}
      {roiData?.quickest_win && (
        <div className="bg-gradient-to-r from-emerald-50 via-teal-50 to-white rounded-2xl p-5 border border-emerald-200/80 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div className="flex items-center gap-3.5">
            <div className="p-3 bg-emerald-600 text-white rounded-xl shadow-sm shrink-0">
              <TrendingUp className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-[10px] font-black uppercase tracking-wider px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 border border-emerald-200">
                  Quickest Win Skill ROI
                </span>
                <span className="text-xs font-extrabold text-emerald-700">
                  ROI: {roiData.quickest_win.roi_score} pts / week
                </span>
              </div>

              <h4 className="text-sm font-black text-slate-900 mt-1">
                Learn {roiData.quickest_win.skill_name} for a +
                {roiData.quickest_win.readiness_gain}% readiness boost
              </h4>

              <p className="text-xs text-slate-500 mt-0.5">
                ~{roiData.quickest_win.estimated_weeks} weeks (
                {roiData.quickest_win.estimated_hours}h) to reach Level{' '}
                {roiData.quickest_win.required_level}/5.
              </p>
            </div>
          </div>

          <Link
            to={`/skill-gap?career_id=${targetCareerId}&tab=roi`}
            className="inline-flex items-center gap-1.5 px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold rounded-xl shadow-sm transition shrink-0"
          >
            Analyze Skill ROI
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      )}

      {/* Main stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200 flex flex-col items-center justify-center text-center">
          <div className="flex items-center justify-between w-full mb-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500">
              Readiness
            </h3>
            <Badge
              variant={
                readinessCategory === 'Advanced'
                  ? 'success'
                  : readinessCategory === 'Proficient'
                    ? 'info'
                    : readinessCategory === 'Developing'
                      ? 'warning'
                      : 'neutral'
              }
            >
              {readinessCategory}
            </Badge>
          </div>

          <RadialGauge
            score={readinessScore}
            size={170}
            strokeWidth={14}
            label="Readiness"
          />

          <p className="text-xs text-slate-500 mt-4 max-w-xs leading-relaxed">
            Calculated across {totalSkills} canonical skills required for {activeCareerName}.
          </p>
        </div>

        <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200 flex flex-col justify-between">
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-4">
              Skill Alignment Breakdown
            </h3>

            <div className="space-y-4">
              <div>
                <div className="flex justify-between text-sm mb-1.5 font-medium">
                  <span className="flex items-center gap-1.5 text-emerald-700">
                    <CheckCircle2 className="w-4 h-4" />
                    Matched Skills
                  </span>
                  <span className="font-semibold text-slate-900">
                    {matchedCount}
                  </span>
                </div>
                <ProgressBar value={matchedCount} max={totalSkills} color="bg-emerald-500" />
              </div>

              <div>
                <div className="flex justify-between text-sm mb-1.5 font-medium">
                  <span className="flex items-center gap-1.5 text-amber-700">
                    <AlertCircle className="w-4 h-4" />
                    Weak / Developing
                  </span>
                  <span className="font-semibold text-slate-900">{weakCount}</span>
                </div>
                <ProgressBar value={weakCount} max={totalSkills} color="bg-amber-500" />
              </div>

              <div>
                <div className="flex justify-between text-sm mb-1.5 font-medium">
                  <span className="flex items-center gap-1.5 text-rose-700">
                    <HelpCircle className="w-4 h-4" />
                    Missing Skills
                  </span>
                  <span className="font-semibold text-slate-900">{missingCount}</span>
                </div>
                <ProgressBar value={missingCount} max={totalSkills} color="bg-rose-500" />
              </div>
            </div>
          </div>

          <div className="pt-4 border-t border-slate-100 flex justify-between items-center text-xs text-slate-500">
            <span>Total Needed: {totalSkills} skills</span>
            <Link
              to={`/skill-gap?career_id=${targetCareerId}`}
              className="text-primary-600 font-semibold hover:underline flex items-center gap-1"
            >
              Analyze Gap
              <ArrowRight className="w-3 h-3" />
            </Link>
          </div>
        </div>

        <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500">
                Readiness Velocity
              </h3>
              <Badge variant="purple">
                {analytics?.velocity?.pace_category || 'Steady'} Pace
              </Badge>
            </div>

            <div className="space-y-4">
              <div className="p-4 bg-slate-50 rounded-xl border border-slate-100">
                <div className="flex items-center gap-3">
                  <div className="p-2.5 bg-indigo-100 text-indigo-700 rounded-lg">
                    <TrendingUp className="w-5 h-5" />
                  </div>
                  <div>
                    <div className="text-xl font-bold text-slate-900">
                      +{analytics?.velocity?.readiness_points_per_week ?? '0.0'} pts/wk
                    </div>
                    <p className="text-xs text-slate-500">Acquisition pace</p>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3 text-xs">
                <div className="p-3 bg-slate-50 rounded-xl">
                  <p className="text-slate-400">Baseline</p>
                  <p className="font-bold text-slate-800 text-base">
                    {analytics?.baseline_readiness ?? 0}%
                  </p>
                </div>

                <div className="p-3 bg-slate-50 rounded-xl">
                  <p className="text-slate-400">Gain</p>
                  <p className="font-bold text-emerald-600 text-base">
                    +{analytics?.net_readiness_gain ?? 0}%
                  </p>
                </div>
              </div>
            </div>
          </div>

          <div className="pt-4 border-t border-slate-100 flex justify-between items-center text-xs text-slate-500">
            <span>{analytics?.total_resources_completed ?? 0} modules finished</span>
            <Link
              to="/analytics"
              className="text-primary-600 font-semibold hover:underline flex items-center gap-1"
            >
              Full Analytics
              <ArrowRight className="w-3 h-3" />
            </Link>
          </div>
        </div>
      </div>

      {/* Skill gaps + learning */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200">
          <div className="flex items-center justify-between mb-5">
            <div className="flex items-center gap-2">
              <div className="p-2 bg-amber-50 text-amber-600 rounded-lg">
                <Target className="w-5 h-5" />
              </div>
              <h2 className="text-lg font-bold text-slate-900">Immediate Skill Gaps</h2>
            </div>

            <Link
              to={`/skill-gap?career_id=${targetCareerId}`}
              className="text-xs text-primary-600 font-semibold hover:underline"
            >
              View Full Gap Matrix
            </Link>
          </div>

          {missingSkills.length === 0 && weakSkills.length === 0 ? (
            <div className="p-8 text-center bg-slate-50 rounded-xl border border-dashed border-slate-200">
              <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto mb-2" />
              <p className="text-sm font-semibold text-slate-700">
                No critical skill gaps!
              </p>
              <p className="text-xs text-slate-500 mt-1">
                You satisfy all required skills for {activeCareerName}.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {missingSkills.slice(0, 4).map((skill, idx) => {
                const sName = skill.skill_name || skill.name;
                const cId = skill.canonical_skill_id || skill.canonical_id || '';
                const reqLvl = skill.required_level || 5;
                const cat = skill.priority_level || skill.category || 'Core Skill';

                return (
                  <div
                    key={idx}
                    className="p-3.5 bg-slate-50 hover:bg-slate-100 rounded-xl border border-slate-100 flex items-center justify-between transition"
                  >
                    <div className="flex items-center gap-3">
                      <span className="w-2 h-2 rounded-full bg-rose-500" />
                      <div>
                        <p className="text-sm font-semibold text-slate-900">{sName}</p>
                        <p className="text-xs text-slate-400">
                          {cat} • Required: Level {reqLvl}/10
                        </p>
                      </div>
                    </div>

                    <Link
                      to={`/learning?skill_id=${cId}`}
                      className="text-xs font-semibold px-3 py-1.5 bg-white hover:bg-primary-50 text-primary-600 border border-slate-200 rounded-lg shadow-sm transition"
                    >
                      Find Course
                    </Link>
                  </div>
                );
              })}

              {weakSkills.slice(0, 2).map((skill, idx) => {
                const sName = skill.skill_name || skill.name;
                const cId = skill.canonical_skill_id || skill.canonical_id || '';
                const curLvl = skill.current_proficiency ?? skill.student_level ?? 0;
                const reqLvl = skill.required_level || 5;

                return (
                  <div
                    key={`weak-${idx}`}
                    className="p-3.5 bg-amber-50/50 hover:bg-amber-50 rounded-xl border border-amber-100 flex items-center justify-between transition"
                  >
                    <div className="flex items-center gap-3">
                      <span className="w-2 h-2 rounded-full bg-amber-500" />
                      <div>
                        <p className="text-sm font-semibold text-slate-900">{sName}</p>
                        <p className="text-xs text-amber-700">
                          Current: {curLvl}/10 • Target: {reqLvl}/10
                        </p>
                      </div>
                    </div>

                    <Link
                      to={`/learning?skill_id=${cId}`}
                      className="text-xs font-semibold px-3 py-1.5 bg-white hover:bg-amber-100 text-amber-800 border border-amber-200 rounded-lg shadow-sm transition"
                    >
                      Level Up
                    </Link>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200">
          <div className="flex items-center justify-between mb-5">
            <div className="flex items-center gap-2">
              <div className="p-2 bg-indigo-50 text-indigo-600 rounded-lg">
                <BookOpen className="w-5 h-5" />
              </div>
              <h2 className="text-lg font-bold text-slate-900">Active Learning Pathways</h2>
            </div>

            <Link
              to="/learning"
              className="text-xs text-primary-600 font-semibold hover:underline"
            >
              Browse Catalog
            </Link>
          </div>

          {activeProgress.length === 0 ? (
            <div className="p-8 text-center bg-slate-50 rounded-xl border border-dashed border-slate-200">
              <BookOpen className="w-8 h-8 text-slate-400 mx-auto mb-2" />
              <p className="text-sm font-semibold text-slate-700">
                No resources currently in progress
              </p>
              <p className="text-xs text-slate-500 mt-1 mb-4">
                Enroll in a learning module to accelerate your readiness score.
              </p>
              <Link
                to="/learning"
                className="inline-flex items-center gap-2 px-3.5 py-2 bg-primary-600 text-white text-xs font-semibold rounded-lg hover:bg-primary-700 transition"
              >
                Find Modules
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          ) : (
            <div className="space-y-4">
              {activeProgress.slice(0, 3).map((item) => (
                <div
                  key={item.id}
                  className="p-4 bg-slate-50 rounded-xl border border-slate-100 space-y-2.5"
                >
                  <div className="flex justify-between items-start gap-2">
                    <div>
                      <h4 className="text-sm font-semibold text-slate-900 leading-snug">
                        {item.resource?.title || 'Resource'}
                      </h4>
                      <p className="text-xs text-slate-500">
                        {item.resource?.provider} • {item.resource?.canonical_skill_name}
                      </p>
                    </div>
                    <span className="text-xs font-bold text-primary-600 shrink-0">
                      {Math.round(item.progress_percentage || 0)}%
                    </span>
                  </div>

                  <ProgressBar
                    value={item.progress_percentage || 0}
                    max={100}
                    color="bg-primary-600"
                  />

                  <div className="flex justify-between items-center text-xs text-slate-400 pt-1">
                    <span className="flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {item.resource?.estimated_duration_hours || 10}h
                    </span>

                    <Link
                      to="/learning"
                      className="font-medium text-primary-600 hover:underline"
                    >
                      Update Progress →
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Alternative careers */}
      <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200">
        <div className="flex items-center justify-between mb-5">
          <div>
            <h2 className="text-lg font-bold text-slate-900">
              Recommended Alternative Careers
            </h2>
            <p className="text-xs text-slate-500">
              Ranked by your current skill overlap and transferable competencies
            </p>
          </div>

          <Link
            to="/careers"
            className="text-xs text-primary-600 font-semibold hover:underline"
          >
            View All Careers
          </Link>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {recommendations.slice(0, 3).map((rec, idx) => {
            const careerTitle =
              rec.career_title || rec.career_name || 'Career Pathway';

            const displayScore =
              rec.final_score ??
              rec.recommendation_score ??
              rec.readiness_score ??
              0;

            const matchedCnt = rec.matched_skills
              ? rec.matched_skills.length
              : rec.matched_count || 0;

            const missingCnt = rec.missing_skills
              ? rec.missing_skills.length
              : rec.missing_count || 0;

            return (
              <div
                key={rec.career_id}
                className="p-4 rounded-xl border border-slate-200 hover:border-primary-300 hover:shadow-md transition bg-gradient-to-b from-white to-slate-50 flex flex-col justify-between"
              >
                <div>
                  <div className="flex justify-between items-start mb-2">
                    <span className="text-[11px] font-bold px-2 py-0.5 rounded-full bg-slate-100 text-slate-600">
                      Rank #{rec.recommendation_rank || idx + 1}
                    </span>

                    <Badge variant={rec.is_personalized ? 'success' : 'info'}>
                      {rec.is_personalized
                        ? 'Multi-Factor Fit'
                        : rec.readiness_category || 'Match'}
                    </Badge>
                  </div>

                  <h3 className="font-bold text-slate-900 text-base">
                    {careerTitle}
                  </h3>
                  <p className="text-xs text-slate-500 mb-3">{rec.domain}</p>

                  <div className="space-y-1.5 mb-3">
                    <div className="flex justify-between text-xs text-slate-600">
                      <span>
                        {rec.is_personalized
                          ? 'Personalized Match'
                          : 'Readiness Match'}
                      </span>
                      <span className="font-bold text-slate-900">
                        {displayScore}%
                      </span>
                    </div>

                    <ProgressBar
                      value={displayScore}
                      max={100}
                      color={rec.is_personalized ? 'bg-emerald-500' : 'bg-primary-500'}
                    />
                  </div>

                  {rec.factor_breakdown && (
                    <div className="grid grid-cols-2 gap-1.5 mb-3 p-2 bg-slate-50 rounded-lg border border-slate-100 text-[10px]">
                      <div className="flex justify-between">
                        <span className="text-slate-500">Skill:</span>
                        <span className="font-bold text-slate-800">
                          {rec.factor_breakdown.skill_fit?.score}%
                        </span>
                      </div>

                      <div className="flex justify-between">
                        <span className="text-slate-500">Pref:</span>
                        <span className="font-bold text-slate-800">
                          {rec.factor_breakdown.preference_fit?.score ?? 'N/A'}%
                        </span>
                      </div>

                      <div className="flex justify-between">
                        <span className="text-slate-500">Market:</span>
                        <span className="font-bold text-slate-800">
                          {rec.factor_breakdown.market_demand?.score}%
                        </span>
                      </div>

                      <div className="flex justify-between">
                        <span className="text-slate-500">Acad:</span>
                        <span className="font-bold text-slate-800">
                          {rec.factor_breakdown.academic_fit?.score ?? 'N/A'}%
                        </span>
                      </div>
                    </div>
                  )}

                  <div className="text-[11px] text-slate-500 space-y-0.5">
                    <p>✓ {matchedCnt} matching skills</p>
                    <p>✗ {missingCnt} skills to acquire</p>
                  </div>

                  {rec.multi_factor_justification && (
                    <p className="text-[10px] text-slate-500 italic mt-2.5 bg-slate-100/70 p-2 rounded-lg border border-slate-200/60 line-clamp-3">
                      "{rec.multi_factor_justification}"
                    </p>
                  )}
                </div>

                <div className="pt-4 mt-4 border-t border-slate-100 flex items-center justify-between">
                  <button
                    onClick={() => setTargetCareerId(rec.career_id)}
                    className="text-xs font-semibold text-primary-600 hover:text-primary-700"
                  >
                    Set as Target
                  </button>

                  <Link
                    to={`/compare?a=${targetCareerId}&b=${rec.career_id}`}
                    className="text-xs font-medium text-slate-500 hover:text-slate-800"
                  >
                    Compare →
                  </Link>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Quick launchpad */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Link
          to="/resume"
          className="p-4 bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-100 rounded-2xl flex items-center gap-4 hover:shadow-sm transition"
        >
          <div className="p-3 bg-blue-600 text-white rounded-xl">
            <FileText className="w-5 h-5" />
          </div>
          <div>
            <h4 className="font-bold text-slate-900 text-sm">Upload Resume</h4>
            <p className="text-xs text-slate-500">Auto-extract & match skills</p>
          </div>
        </Link>

        <Link
          to="/skills"
          className="p-4 bg-gradient-to-r from-emerald-50 to-teal-50 border border-emerald-100 rounded-2xl flex items-center gap-4 hover:shadow-sm transition"
        >
          <div className="p-3 bg-emerald-600 text-white rounded-xl">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <h4 className="font-bold text-slate-900 text-sm">Manage My Skills</h4>
            <p className="text-xs text-slate-500">Adjust proficiencies 1–10</p>
          </div>
        </Link>

        <Link
          to="/compare"
          className="p-4 bg-gradient-to-r from-purple-50 to-pink-50 border border-purple-100 rounded-2xl flex items-center gap-4 hover:shadow-sm transition"
        >
          <div className="p-3 bg-purple-600 text-white rounded-xl">
            <Compass className="w-5 h-5" />
          </div>
          <div>
            <h4 className="font-bold text-slate-900 text-sm">Compare Careers</h4>
            <p className="text-xs text-slate-500">Venn overlap & switch distance</p>
          </div>
        </Link>
      </div>
    </div>
  );
}
