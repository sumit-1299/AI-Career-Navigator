import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { api } from '../services/api';
import { Spinner, Alert } from '../components/common/UIFeedback';
import { Badge } from '../components/common/Badge';
import { RadialGauge } from '../components/common/RadialGauge';
import {
  CheckCircle2,
  HelpCircle,
  Sparkles,
  Layers,
  ArrowRight,
  ArrowLeftRight,
  TrendingUp,
  DollarSign,
  Clock,
  Compass,
  ShieldCheck,
  Calendar,
} from 'lucide-react';

export function CareerComparisonPage() {
  const [searchParams, setSearchParams] = useSearchParams();

  const [careers, setCareers] = useState([]);
  const [careerAId, setCareerAId] = useState(Number(searchParams.get('a') || '1'));
  const [careerBId, setCareerBId] = useState(Number(searchParams.get('b') || '6'));

  const [hoursPerWeek, setHoursPerWeek] = useState(10);
  const [comparison, setComparison] = useState(null);
  const [transitionData, setTransitionData] = useState(null);
  const [transitionDirection, setTransitionDirection] = useState('a_to_b'); // 'a_to_b' | 'b_to_a'
  const [loading, setLoading] = useState(true);
  const [transitionLoading, setTransitionLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadCareers();
  }, []);

  useEffect(() => {
    if (careerAId && careerBId && careerAId !== careerBId) {
      loadComparison();
    }
  }, [careerAId, careerBId, hoursPerWeek]);

  useEffect(() => {
    if (careerAId && careerBId && careerAId !== careerBId) {
      loadTransitionPathway();
    }
  }, [careerAId, careerBId, transitionDirection]);

  async function loadCareers() {
    try {
      const res = await api.listCareers();
      const list = res?.careers || [];
      setCareers(list);
      if (list.length >= 2 && !searchParams.get('a') && !searchParams.get('b')) {
        setCareerAId(list[0].id);
        setCareerBId(list[1].id);
      }
    } catch (err) {
      console.warn('Could not load careers', err);
    }
  }

  async function loadComparison() {
    if (careerAId === careerBId) {
      setError('Please select two different careers to compare');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const token = localStorage.getItem('career_navigator_token');
      const headers = token ? { Authorization: `Bearer ${token}` } : {};
      const res = await fetch(
        `/api/careers/compare?career_a_id=${careerAId}&career_b_id=${careerBId}&hours_per_week=${hoursPerWeek}`,
        { headers }
      );
      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.message || 'Failed to compare careers');
      }
      const data = await res.json();
      setComparison(data.comparison || data);
      setSearchParams({ a: careerAId, b: careerBId });
    } catch (err) {
      setError(err.message || 'Failed to compare careers');
    } finally {
      setLoading(false);
    }
  }

  async function loadTransitionPathway() {
    const fromId = transitionDirection === 'a_to_b' ? careerAId : careerBId;
    const toId = transitionDirection === 'a_to_b' ? careerBId : careerAId;

    setTransitionLoading(true);
    try {
      const token = localStorage.getItem('career_navigator_token');
      const headers = token ? { Authorization: `Bearer ${token}` } : {};
      const res = await fetch(`/api/careers/${fromId}/transition/${toId}`, { headers });
      if (res.ok) {
        const data = await res.json();
        setTransitionData(data.transition || null);
      }
    } catch (err) {
      console.warn('Could not load directional transition pathway', err);
    } finally {
      setTransitionLoading(false);
    }
  }

  function handleSwapCareers() {
    const tempA = careerAId;
    setCareerAId(careerBId);
    setCareerBId(tempA);
    setSearchParams({ a: careerBId, b: tempA });
  }

  const {
    career_a,
    career_b,
    comparison_metrics,
    common_skills = [],
    career_a_only = [],
    career_b_only = [],
    student_already_has = [],
    student_missing = [],
    market_comparison,
    salary_differential,
    timeline_comparison,
    transition_analysis,
  } = comparison || {};

  const activeTransition = transitionData || transition_analysis;
  const transSummary = activeTransition?.transition_summary;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-2xl p-6 md:p-8 shadow-sm border border-slate-200">
        <div className="flex items-center justify-between flex-wrap gap-2 mb-1.5">
          <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-purple-50 text-purple-700 border border-purple-200">
            Phase 9 Module 9.2: Market-Augmented Dual Career Explorer
          </span>
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-500 font-medium">Study Pace:</span>
            {[5, 10, 20].map((hrs) => (
              <button
                key={hrs}
                onClick={() => setHoursPerWeek(hrs)}
                className={`text-xs px-2.5 py-1 rounded-lg font-semibold transition ${
                  hoursPerWeek === hrs
                    ? 'bg-primary-600 text-white shadow-sm'
                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                }`}
              >
                {hrs} hrs/wk
              </button>
            ))}
          </div>
        </div>
        <h1 className="text-2xl md:text-3xl font-extrabold text-slate-900 tracking-tight">
          Career Comparison & Transition Matrix
        </h1>
        <p className="text-slate-500 text-sm mt-1">
          Evaluate competency commonalities, market demand differentials, salary trajectories, study timelines,
          and O*NET transferable skill transition pathways between two target roles.
        </p>

        {/* Dual Selector Bar with Swap Action */}
        <div className="mt-6 flex flex-col md:flex-row items-center gap-3">
          <div className="flex-1 w-full p-4 bg-slate-50 rounded-xl border border-slate-200">
            <label className="block text-xs font-bold text-slate-600 uppercase tracking-wider mb-2">
              Career A (Source / Primary Role)
            </label>
            <select
              value={careerAId}
              onChange={(e) => setCareerAId(Number(e.target.value))}
              className="w-full p-2.5 rounded-lg border border-slate-300 bg-white text-sm font-semibold text-slate-800"
            >
              {careers.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.career_name || c.title} ({c.domain})
                </option>
              ))}
            </select>
          </div>

          <button
            onClick={handleSwapCareers}
            title="Swap Career A and Career B"
            className="p-3 bg-white hover:bg-slate-100 text-slate-700 border border-slate-200 rounded-xl shadow-sm transition shrink-0 flex items-center justify-center"
          >
            <ArrowLeftRight className="w-4 h-4 text-primary-600" />
          </button>

          <div className="flex-1 w-full p-4 bg-slate-50 rounded-xl border border-slate-200">
            <label className="block text-xs font-bold text-slate-600 uppercase tracking-wider mb-2">
              Career B (Target / Comparison Role)
            </label>
            <select
              value={careerBId}
              onChange={(e) => setCareerBId(Number(e.target.value))}
              className="w-full p-2.5 rounded-lg border border-slate-300 bg-white text-sm font-semibold text-slate-800"
            >
              {careers.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.career_name || c.title} ({c.domain})
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {error && <Alert type="error" message={error} />}

      {loading ? (
        <div className="flex flex-col items-center justify-center py-20">
          <Spinner size="lg" />
          <p className="mt-4 text-slate-500 font-medium">Computing dual career market and transition intelligence...</p>
        </div>
      ) : comparison ? (
        <div className="space-y-6 animate-fadeIn">
          {/* Side-by-Side Dual Role Scorecards */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Career A Card */}
            <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200 flex flex-col justify-between">
              <div>
                <div className="flex justify-between items-start mb-2">
                  <span className="text-[11px] font-bold px-2 py-0.5 rounded bg-blue-100 text-blue-700">
                    Path A
                  </span>
                  <Badge variant="info">{career_a?.domain}</Badge>
                </div>
                <h3 className="text-xl font-extrabold text-slate-900">{career_a?.title || career_a?.name}</h3>
                <p className="text-xs text-slate-500 mt-1">
                  Requires {career_a?.total_required_skills ?? career_a?.total_skills ?? 0} total competencies
                </p>

                <div className="mt-5 flex items-center gap-6">
                  <RadialGauge
                    score={career_a?.readiness_percentage ?? career_a?.readiness_score ?? 0}
                    size={100}
                    strokeWidth={9}
                    label="Readiness"
                  />
                  <div className="space-y-1.5 text-xs">
                    <p className="font-semibold text-slate-800">
                      Student Readiness: {career_a?.readiness_percentage ?? career_a?.readiness_score ?? 0}%
                    </p>
                    <p className="text-slate-500">
                      Distance to role:{' '}
                      <span className="font-bold text-slate-700">
                        {career_a?.skill_acquisition_distance ?? 0} pts
                      </span>
                    </p>
                    <p className="text-slate-500">
                      Gaps remaining:{' '}
                      <span className="font-bold text-rose-600">
                        {career_a?.missing_skills_count ?? 0} missing, {career_a?.weak_skills_count ?? 0} weak
                      </span>
                    </p>
                  </div>
                </div>

                {/* Market Quick Stats */}
                <div className="mt-4 pt-4 border-t border-slate-100 grid grid-cols-2 gap-2 text-xs">
                  <div className="bg-slate-50 p-2.5 rounded-lg border border-slate-100">
                    <span className="text-slate-500 text-[11px] block">Market Demand:</span>
                    <span className="font-bold text-slate-900">
                      {market_comparison?.career_a?.demand_score ?? 'N/A'}/100 ({market_comparison?.career_a?.demand_level})
                    </span>
                  </div>
                  <div className="bg-slate-50 p-2.5 rounded-lg border border-slate-100">
                    <span className="text-slate-500 text-[11px] block">Median Salary:</span>
                    <span className="font-bold text-emerald-700">
                      {salary_differential?.median?.career_a ?? 'N/A'}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Career B Card */}
            <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200 flex flex-col justify-between">
              <div>
                <div className="flex justify-between items-start mb-2">
                  <span className="text-[11px] font-bold px-2 py-0.5 rounded bg-purple-100 text-purple-700">
                    Path B
                  </span>
                  <Badge variant="purple">{career_b?.domain}</Badge>
                </div>
                <h3 className="text-xl font-extrabold text-slate-900">{career_b?.title || career_b?.name}</h3>
                <p className="text-xs text-slate-500 mt-1">
                  Requires {career_b?.total_required_skills ?? career_b?.total_skills ?? 0} total competencies
                </p>

                <div className="mt-5 flex items-center gap-6">
                  <RadialGauge
                    score={career_b?.readiness_percentage ?? career_b?.readiness_score ?? 0}
                    size={100}
                    strokeWidth={9}
                    label="Readiness"
                  />
                  <div className="space-y-1.5 text-xs">
                    <p className="font-semibold text-slate-800">
                      Student Readiness: {career_b?.readiness_percentage ?? career_b?.readiness_score ?? 0}%
                    </p>
                    <p className="text-slate-500">
                      Distance to role:{' '}
                      <span className="font-bold text-slate-700">
                        {career_b?.skill_acquisition_distance ?? 0} pts
                      </span>
                    </p>
                    <p className="text-slate-500">
                      Gaps remaining:{' '}
                      <span className="font-bold text-rose-600">
                        {career_b?.missing_skills_count ?? 0} missing, {career_b?.weak_skills_count ?? 0} weak
                      </span>
                    </p>
                  </div>
                </div>

                {/* Market Quick Stats */}
                <div className="mt-4 pt-4 border-t border-slate-100 grid grid-cols-2 gap-2 text-xs">
                  <div className="bg-slate-50 p-2.5 rounded-lg border border-slate-100">
                    <span className="text-slate-500 text-[11px] block">Market Demand:</span>
                    <span className="font-bold text-slate-900">
                      {market_comparison?.career_b?.demand_score ?? 'N/A'}/100 ({market_comparison?.career_b?.demand_level})
                    </span>
                  </div>
                  <div className="bg-slate-50 p-2.5 rounded-lg border border-slate-100">
                    <span className="text-slate-500 text-[11px] block">Median Salary:</span>
                    <span className="font-bold text-emerald-700">
                      {salary_differential?.median?.career_b ?? 'N/A'}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Module 9.2 Market Demand & Salary Differential Section */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Market Demand Comparison */}
            <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200">
              <h3 className="text-base font-bold text-slate-900 mb-2 flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-blue-600" />
                <span>Market Demand Differential</span>
              </h3>
              <p className="text-xs text-slate-500 mb-4">
                Comparison of industry hiring demand and 5-year outlook from labor market data.
              </p>

              <div className="space-y-3">
                <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 flex items-center justify-between text-xs">
                  <span className="font-semibold text-slate-700">{career_a?.title} Demand</span>
                  <span className="font-bold text-slate-900">
                    {market_comparison?.career_a?.demand_score}/100 ({market_comparison?.career_a?.five_year_growth_rate} growth)
                  </span>
                </div>
                <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 flex items-center justify-between text-xs">
                  <span className="font-semibold text-slate-700">{career_b?.title} Demand</span>
                  <span className="font-bold text-slate-900">
                    {market_comparison?.career_b?.demand_score}/100 ({market_comparison?.career_b?.five_year_growth_rate} growth)
                  </span>
                </div>
                <div className="p-3 bg-blue-50/70 rounded-xl border border-blue-200 flex items-center justify-between text-xs">
                  <span className="font-bold text-blue-900">Demand Differential (B vs A):</span>
                  <span className="font-extrabold text-blue-700">
                    {market_comparison?.demand_delta >= 0 ? '+' : ''}
                    {market_comparison?.demand_delta} points
                  </span>
                </div>
                <p className="text-[11px] text-slate-500 italic mt-2">
                  {market_comparison?.summary}
                </p>
              </div>
            </div>

            {/* Salary Differential Comparison */}
            <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200">
              <h3 className="text-base font-bold text-slate-900 mb-2 flex items-center gap-2">
                <DollarSign className="w-5 h-5 text-emerald-600" />
                <span>Salary Band Differential</span>
              </h3>
              <p className="text-xs text-slate-500 mb-4">
                Compensation variance across career progression bands (Entry, Median, Senior).
              </p>

              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left border-collapse">
                  <thead>
                    <tr className="border-b border-slate-200 text-slate-500 text-[11px]">
                      <th className="py-2">Band</th>
                      <th className="py-2">{career_a?.title}</th>
                      <th className="py-2">{career_b?.title}</th>
                      <th className="py-2 font-bold text-slate-700">Variance</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    <tr>
                      <td className="py-2 font-medium text-slate-700">Entry</td>
                      <td className="py-2 text-slate-600">{salary_differential?.entry_level?.career_a}</td>
                      <td className="py-2 text-slate-600">{salary_differential?.entry_level?.career_b}</td>
                      <td className="py-2 font-semibold text-slate-800">
                        {salary_differential?.entry_level?.formatted_delta}
                      </td>
                    </tr>
                    <tr className="bg-emerald-50/40">
                      <td className="py-2 font-bold text-emerald-900">Median</td>
                      <td className="py-2 font-semibold text-slate-700">{salary_differential?.median?.career_a}</td>
                      <td className="py-2 font-semibold text-slate-700">{salary_differential?.median?.career_b}</td>
                      <td className="py-2 font-bold text-emerald-700">
                        {salary_differential?.median?.formatted_delta}{' '}
                        {salary_differential?.median?.delta_percentage !== undefined && (
                          <span className="text-[10px] font-normal">
                            ({salary_differential?.median?.delta_percentage >= 0 ? '+' : ''}
                            {salary_differential?.median?.delta_percentage}%)
                          </span>
                        )}
                      </td>
                    </tr>
                    <tr>
                      <td className="py-2 font-medium text-slate-700">Senior</td>
                      <td className="py-2 text-slate-600">{salary_differential?.senior?.career_a}</td>
                      <td className="py-2 text-slate-600">{salary_differential?.senior?.career_b}</td>
                      <td className="py-2 font-semibold text-slate-800">
                        {salary_differential?.senior?.formatted_delta}
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          {/* Module 9.2 Study Timeline & Roadmap Workload Differential */}
          <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200">
            <h3 className="text-base font-bold text-slate-900 mb-2 flex items-center gap-2">
              <Clock className="w-5 h-5 text-indigo-600" />
              <span>Study Timeline & Workload Comparison ({hoursPerWeek} hrs/week)</span>
            </h3>
            <p className="text-xs text-slate-500 mb-4">
              Estimated study investment required to bridge remaining skill gaps for each pathway.
            </p>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-4 bg-slate-50 rounded-xl border border-slate-200">
                <span className="text-xs text-slate-500 block">{career_a?.title}</span>
                <span className="text-xl font-extrabold text-slate-900 mt-1 block">
                  ~{timeline_comparison?.career_a?.estimated_weeks} Weeks
                </span>
                <span className="text-xs text-slate-500 mt-0.5 block">
                  {timeline_comparison?.career_a?.estimated_total_hours} total study hours
                </span>
                {timeline_comparison?.career_a?.estimated_completion_date && (
                  <span className="text-[11px] text-primary-700 flex items-center gap-1 mt-2">
                    <Calendar className="w-3 h-3" /> Target Date: {timeline_comparison.career_a.estimated_completion_date}
                  </span>
                )}
              </div>

              <div className="p-4 bg-slate-50 rounded-xl border border-slate-200">
                <span className="text-xs text-slate-500 block">{career_b?.title}</span>
                <span className="text-xl font-extrabold text-slate-900 mt-1 block">
                  ~{timeline_comparison?.career_b?.estimated_weeks} Weeks
                </span>
                <span className="text-xs text-slate-500 mt-0.5 block">
                  {timeline_comparison?.career_b?.estimated_total_hours} total study hours
                </span>
                {timeline_comparison?.career_b?.estimated_completion_date && (
                  <span className="text-[11px] text-primary-700 flex items-center gap-1 mt-2">
                    <Calendar className="w-3 h-3" /> Target Date: {timeline_comparison.career_b.estimated_completion_date}
                  </span>
                )}
              </div>

              <div className="p-4 bg-indigo-50/70 rounded-xl border border-indigo-200 flex flex-col justify-between">
                <div>
                  <span className="text-xs text-indigo-800 font-bold block uppercase tracking-wide">
                    Timeline Variance
                  </span>
                  <span className="text-xl font-extrabold text-indigo-900 mt-1 block">
                    {timeline_comparison?.estimated_study_weeks_difference >= 0 ? '+' : ''}
                    {timeline_comparison?.estimated_study_weeks_difference} Weeks
                  </span>
                  <span className="text-xs text-indigo-700 mt-0.5 block">
                    Faster Pathway: <strong>{timeline_comparison?.faster_career}</strong>
                  </span>
                </div>
                <p className="text-[11px] text-slate-600 mt-2 line-clamp-2">
                  {timeline_comparison?.summary}
                </p>
              </div>
            </div>
          </div>

          {/* Module 9.2 Transition Pathway Explorer & O*NET Matrix */}
          <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-4">
              <div>
                <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                  <Compass className="w-5 h-5 text-emerald-600" />
                  <span>Transition Pathway & O*NET Transferable Skills Matrix</span>
                </h3>
                <p className="text-xs text-slate-500 mt-1">
                  Evaluates skill portability, difficulty classification, and direct vs upgrade competencies.
                </p>
              </div>

              {/* Directional Toggle Buttons */}
              <div className="flex items-center gap-2 bg-slate-100 p-1 rounded-xl">
                <button
                  onClick={() => setTransitionDirection('a_to_b')}
                  className={`text-xs px-3 py-1.5 rounded-lg font-semibold transition ${
                    transitionDirection === 'a_to_b'
                      ? 'bg-white text-slate-900 shadow-sm'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  {career_a?.title} → {career_b?.title}
                </button>
                <button
                  onClick={() => setTransitionDirection('b_to_a')}
                  className={`text-xs px-3 py-1.5 rounded-lg font-semibold transition ${
                    transitionDirection === 'b_to_a'
                      ? 'bg-white text-slate-900 shadow-sm'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  {career_b?.title} → {career_a?.title}
                </button>
              </div>
            </div>

            {transitionLoading ? (
              <div className="flex items-center justify-center py-8">
                <Spinner size="md" />
              </div>
            ) : activeTransition ? (
              <div className="space-y-5">
                {/* Transition Summary Banner */}
                <div className="p-4 bg-gradient-to-r from-slate-50 to-emerald-50/40 rounded-xl border border-slate-200 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                        Transition Difficulty:
                      </span>
                      <Badge
                        variant={
                          transSummary?.transition_difficulty === 'LOW'
                            ? 'success'
                            : transSummary?.transition_difficulty === 'MODERATE'
                            ? 'warning'
                            : 'error'
                        }
                      >
                        {transSummary?.transition_difficulty} — {transSummary?.difficulty_label}
                      </Badge>
                    </div>
                    <p className="text-xs text-slate-600 mt-1.5 max-w-2xl leading-relaxed">
                      {transSummary?.explanation}
                    </p>
                  </div>
                  <div className="text-right shrink-0">
                    <span className="text-[11px] text-slate-500 block">Competency Overlap</span>
                    <span className="text-lg font-extrabold text-slate-900">
                      {transSummary?.overlap_percentage}%
                    </span>
                  </div>
                </div>

                {/* Transferable Skills (O*NET Provenance) Matrix */}
                <div>
                  <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                    <ShieldCheck className="w-4 h-4 text-emerald-600" />
                    <span>O*NET Validated Transferable Competencies ({activeTransition.transferable_skills?.length || 0})</span>
                  </h4>
                  {activeTransition.transferable_skills?.length > 0 ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                      {activeTransition.transferable_skills.map((ts, idx) => (
                        <div
                          key={idx}
                          className="p-3 bg-emerald-50/50 border border-emerald-200 rounded-xl text-xs flex flex-col justify-between"
                        >
                          <div>
                            <div className="flex justify-between items-start mb-1">
                              <span className="font-bold text-emerald-950">{ts.skill_name}</span>
                              <span className="text-[10px] bg-emerald-100 text-emerald-800 px-1.5 py-0.5 rounded font-semibold">
                                O*NET
                              </span>
                            </div>
                            <p className="text-[11px] text-slate-600">{ts.description}</p>
                          </div>
                          <div className="mt-2 pt-2 border-t border-emerald-100 flex justify-between text-[11px] text-slate-500">
                            <span>Source Level: {ts.source_required_level}/5</span>
                            <span>Target Level: {ts.target_required_level}/5</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-slate-500 italic p-3 bg-slate-50 rounded-lg">
                      No direct O*NET portable competencies identified for this cross-domain transition.
                    </p>
                  )}
                </div>

                {/* Direct Transfer vs Upgrade Needed vs New Competency Required */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Upgrades Needed */}
                  <div className="p-4 bg-amber-50/40 rounded-xl border border-amber-200">
                    <h5 className="font-bold text-xs text-amber-900 uppercase mb-2">
                      Skill Proficiency Upgrades Needed
                    </h5>
                    <div className="space-y-2 max-h-48 overflow-y-auto">
                      {activeTransition.overlapping_skills
                        ?.filter((s) => s.status === 'SKILL_UPGRADE_NEEDED')
                        .map((s, idx) => (
                          <div key={idx} className="p-2 bg-white rounded-lg border border-amber-100 text-xs">
                            <div className="flex justify-between font-semibold text-slate-800">
                              <span>{s.skill_name}</span>
                              <span className="text-amber-700">Level gap: +{s.level_gap}</span>
                            </div>
                            <p className="text-[11px] text-slate-500 mt-0.5">{s.description}</p>
                          </div>
                        ))}
                      {!activeTransition.overlapping_skills?.some((s) => s.status === 'SKILL_UPGRADE_NEEDED') && (
                        <p className="text-[11px] text-slate-500 italic">None required.</p>
                      )}
                    </div>
                  </div>

                  {/* New Skills Required */}
                  <div className="p-4 bg-rose-50/40 rounded-xl border border-rose-200">
                    <h5 className="font-bold text-xs text-rose-900 uppercase mb-2">
                      New Competencies Required in Target Role
                    </h5>
                    <div className="space-y-2 max-h-48 overflow-y-auto">
                      {activeTransition.additional_skills_required?.map((s, idx) => (
                        <div key={idx} className="p-2 bg-white rounded-lg border border-rose-100 text-xs">
                          <div className="flex justify-between font-semibold text-slate-800">
                            <span>{s.skill_name}</span>
                            <span className="text-rose-700">Req level: {s.target_required_level}/5</span>
                          </div>
                          <p className="text-[11px] text-slate-500 mt-0.5">{s.description}</p>
                        </div>
                      ))}
                      {!activeTransition.additional_skills_required?.length && (
                        <p className="text-[11px] text-slate-500 italic">No new skills required.</p>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ) : null}
          </div>

          {/* Venn Competency Overlap Breakdown */}
          <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200">
            <h3 className="text-base font-bold text-slate-900 mb-2 flex items-center gap-2">
              <Layers className="w-5 h-5 text-indigo-600" />
              <span>Competency Overlap (Venn Breakdown)</span>
            </h3>
            <p className="text-xs text-slate-500 mb-6">
              Mutual competencies provide foundation and transferability across both roles.
            </p>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Only A */}
              <div className="p-4 rounded-xl border border-blue-200 bg-blue-50/30">
                <div className="flex justify-between items-center mb-2">
                  <h4 className="font-bold text-xs text-blue-900 uppercase">
                    Only in {career_a?.title || career_a?.name}
                  </h4>
                  <span className="font-bold text-blue-700 text-sm">
                    {career_a_only.length}
                  </span>
                </div>
                <div className="flex flex-wrap gap-1.5 mt-2 max-h-40 overflow-y-auto">
                  {career_a_only.map((s, idx) => (
                    <span
                      key={idx}
                      className="px-2 py-0.5 bg-white border border-blue-200 text-blue-800 text-[11px] rounded"
                    >
                      {s.skill_name || s.name || s}
                    </span>
                  ))}
                  {career_a_only.length === 0 && (
                    <span className="text-xs text-slate-400 italic">None</span>
                  )}
                </div>
              </div>

              {/* Shared Overlap */}
              <div className="p-4 rounded-xl border border-emerald-300 bg-emerald-50/40 shadow-sm">
                <div className="flex justify-between items-center mb-2">
                  <h4 className="font-bold text-xs text-emerald-900 uppercase">
                    Shared Competencies (Both)
                  </h4>
                  <span className="font-bold text-emerald-700 text-sm">
                    {common_skills.length}
                  </span>
                </div>
                <p className="text-[10px] text-emerald-600 mb-2">
                  Overlap: {comparison_metrics?.overlap_percentage}% mutual requirement overlap
                </p>
                <div className="flex flex-wrap gap-1.5 mt-2 max-h-40 overflow-y-auto">
                  {common_skills.map((s, idx) => (
                    <span
                      key={idx}
                      className="px-2 py-0.5 bg-white border border-emerald-300 text-emerald-800 text-[11px] rounded font-medium"
                    >
                      {s.skill_name || s.name || s}
                    </span>
                  ))}
                  {common_skills.length === 0 && (
                    <span className="text-xs text-slate-400 italic">None</span>
                  )}
                </div>
              </div>

              {/* Only B */}
              <div className="p-4 rounded-xl border border-purple-200 bg-purple-50/30">
                <div className="flex justify-between items-center mb-2">
                  <h4 className="font-bold text-xs text-purple-900 uppercase">
                    Only in {career_b?.title || career_b?.name}
                  </h4>
                  <span className="font-bold text-purple-700 text-sm">
                    {career_b_only.length}
                  </span>
                </div>
                <div className="flex flex-wrap gap-1.5 mt-2 max-h-40 overflow-y-auto">
                  {career_b_only.map((s, idx) => (
                    <span
                      key={idx}
                      className="px-2 py-0.5 bg-white border border-purple-200 text-purple-800 text-[11px] rounded"
                    >
                      {s.skill_name || s.name || s}
                    </span>
                  ))}
                  {career_b_only.length === 0 && (
                    <span className="text-xs text-slate-400 italic">None</span>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Student Readiness Status Across Careers */}
          <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200">
            <h3 className="text-base font-bold text-slate-900 mb-3">
              Student Proficiency Audit Across Both Careers
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-4 bg-emerald-50/50 rounded-xl border border-emerald-100">
                <h4 className="text-xs font-bold text-emerald-800 uppercase flex items-center gap-1.5 mb-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  <span>Skills Already Possessed ({student_already_has.length})</span>
                </h4>
                <div className="flex flex-wrap gap-1.5">
                  {student_already_has.map((s, i) => (
                    <span key={i} className="px-2 py-0.5 bg-white text-emerald-700 text-xs rounded border border-emerald-200">
                      {s.skill_name} ({s.current_proficiency}/10)
                    </span>
                  ))}
                  {student_already_has.length === 0 && (
                    <span className="text-xs text-slate-400 italic">No skills recorded yet.</span>
                  )}
                </div>
              </div>

              <div className="p-4 bg-rose-50/50 rounded-xl border border-rose-100">
                <h4 className="text-xs font-bold text-rose-800 uppercase flex items-center gap-1.5 mb-2">
                  <HelpCircle className="w-4 h-4 text-rose-600" />
                  <span>Actionable Skill Gaps Remaining ({student_missing.length})</span>
                </h4>
                <div className="flex flex-wrap gap-1.5 max-h-40 overflow-y-auto">
                  {student_missing.map((s, i) => (
                    <span key={i} className="px-2 py-0.5 bg-white text-rose-700 text-xs rounded border border-rose-200">
                      {s.skill_name}
                    </span>
                  ))}
                  {student_missing.length === 0 && (
                    <span className="text-xs text-slate-400 italic">No skill gaps remaining.</span>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
