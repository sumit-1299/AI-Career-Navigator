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
} from 'lucide-react';

export function CareerComparisonPage() {
  const [searchParams, setSearchParams] = useSearchParams();

  const [careers, setCareers] = useState([]);
  const [careerAId, setCareerAId] = useState(Number(searchParams.get('a') || '1'));
  const [careerBId, setCareerBId] = useState(Number(searchParams.get('b') || '2'));

  const [comparison, setComparison] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadCareers();
  }, []);

  useEffect(() => {
    if (careerAId && careerBId && careerAId !== careerBId) {
      loadComparison();
    }
  }, [careerAId, careerBId]);

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
      const data = await api.compareCareers(careerAId, careerBId);
      setComparison(data);
      setSearchParams({ a: careerAId, b: careerBId });
    } catch (err) {
      setError(err.message || 'Failed to compare careers');
    } finally {
      setLoading(false);
    }
  }

  const { career_a, career_b, venn_overlap, quadrant_breakdown, recommendation } =
    comparison || {};

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-2xl p-6 md:p-8 shadow-sm border border-slate-200">
        <div className="flex items-center gap-2 mb-1.5">
          <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-purple-50 text-purple-700 border border-purple-200">
            Side-by-Side Dual Role Intelligence
          </span>
        </div>
        <h1 className="text-2xl md:text-3xl font-extrabold text-slate-900 tracking-tight">
          Career Comparison & Transition Matrix
        </h1>
        <p className="text-slate-500 text-sm mt-1">
          Evaluate skill commonalities, transferability overlap, and transition distance between
          two target career paths.
        </p>

        {/* Dual Selector Bar */}
        <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-4 bg-slate-50 rounded-xl border border-slate-200">
            <label className="block text-xs font-bold text-slate-600 uppercase tracking-wider mb-2">
              Career A (Primary Role)
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

          <div className="p-4 bg-slate-50 rounded-xl border border-slate-200">
            <label className="block text-xs font-bold text-slate-600 uppercase tracking-wider mb-2">
              Career B (Comparison Role)
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
          <p className="mt-4 text-slate-500 font-medium">Computing dual career overlap...</p>
        </div>
      ) : comparison ? (
        <div className="space-y-6 animate-fadeIn">
          {/* Side-by-Side Scorecards */}
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
                <h3 className="text-xl font-extrabold text-slate-900">{career_a?.name || career_a?.title}</h3>
                <p className="text-xs text-slate-500 mt-1">
                  Requires {career_a?.total_skills} total competencies
                </p>

                <div className="mt-6 flex items-center gap-6">
                  <RadialGauge
                    score={career_a?.readiness_score || 0}
                    size={110}
                    strokeWidth={10}
                    label="Readiness"
                  />
                  <div className="space-y-1.5 text-xs">
                    <p className="font-semibold text-slate-800">
                      Score: {career_a?.readiness_score}%
                    </p>
                    <p className="text-slate-500">
                      Gaps remaining:{' '}
                      <span className="font-bold text-rose-600">
                        {recommendation?.acquisition_distance?.career_a_gap ?? 0}
                      </span>
                    </p>
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
                <h3 className="text-xl font-extrabold text-slate-900">{career_b?.name || career_b?.title}</h3>
                <p className="text-xs text-slate-500 mt-1">
                  Requires {career_b?.total_skills} total competencies
                </p>

                <div className="mt-6 flex items-center gap-6">
                  <RadialGauge
                    score={career_b?.readiness_score || 0}
                    size={110}
                    strokeWidth={10}
                    label="Readiness"
                  />
                  <div className="space-y-1.5 text-xs">
                    <p className="font-semibold text-slate-800">
                      Score: {career_b?.readiness_score}%
                    </p>
                    <p className="text-slate-500">
                      Gaps remaining:{' '}
                      <span className="font-bold text-rose-600">
                        {recommendation?.acquisition_distance?.career_b_gap ?? 0}
                      </span>
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Transition Recommendation Banner */}
          <div className="bg-gradient-to-r from-emerald-500 to-teal-600 rounded-2xl p-6 text-white shadow-md flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
            <div>
              <span className="text-xs font-bold uppercase tracking-wider bg-white/20 px-2 py-0.5 rounded">
                AI Career Trajectory Recommendation
              </span>
              <h3 className="text-lg font-bold mt-1">
                Easier Transition: {recommendation?.easier_to_reach || 'Career A'}
              </h3>
              <p className="text-xs text-white/90 mt-0.5">
                Based on your current skill profile, {recommendation?.easier_to_reach} has a shorter
                skill acquisition distance (
                {recommendation?.acquisition_distance?.career_a_gap} gaps vs{' '}
                {recommendation?.acquisition_distance?.career_b_gap} gaps).
              </p>
            </div>
          </div>

          {/* Venn Overlap Analysis */}
          <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200">
            <h3 className="text-base font-bold text-slate-900 mb-2 flex items-center gap-2">
              <Layers className="w-5 h-5 text-indigo-600" />
              <span>Competency Overlap (Venn Matrix)</span>
            </h3>
            <p className="text-xs text-slate-500 mb-6">
              Shared skills make transitions easier and multiply career optionality.
            </p>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Only A */}
              <div className="p-4 rounded-xl border border-blue-200 bg-blue-50/30">
                <div className="flex justify-between items-center mb-2">
                  <h4 className="font-bold text-xs text-blue-900 uppercase">
                    Only in {career_a?.name || career_a?.title}
                  </h4>
                  <span className="font-bold text-blue-700 text-sm">
                    {venn_overlap?.career_a_only_skills_count || 0}
                  </span>
                </div>
                <div className="flex flex-wrap gap-1.5 mt-2 max-h-40 overflow-y-auto">
                  {venn_overlap?.career_a_only_skills?.map((s, idx) => (
                    <span
                      key={idx}
                      className="px-2 py-0.5 bg-white border border-blue-200 text-blue-800 text-[11px] rounded"
                    >
                      {s.skill_name || s.name || s}
                    </span>
                  ))}
                </div>
              </div>

              {/* Shared Overlap */}
              <div className="p-4 rounded-xl border border-emerald-300 bg-emerald-50/40 shadow-sm">
                <div className="flex justify-between items-center mb-2">
                  <h4 className="font-bold text-xs text-emerald-900 uppercase">
                    Shared Competencies (Both)
                  </h4>
                  <span className="font-bold text-emerald-700 text-sm">
                    {venn_overlap?.shared_skills_count || 0}
                  </span>
                </div>
                <p className="text-[10px] text-emerald-600 mb-2">
                  Overlap: {venn_overlap?.overlap_percentage_a}% of A •{' '}
                  {venn_overlap?.overlap_percentage_b}% of B
                </p>
                <div className="flex flex-wrap gap-1.5 mt-2 max-h-40 overflow-y-auto">
                  {venn_overlap?.shared_skills?.map((s, idx) => (
                    <span
                      key={idx}
                      className="px-2 py-0.5 bg-white border border-emerald-300 text-emerald-800 text-[11px] rounded font-medium"
                    >
                      {s.skill_name || s.name || s}
                    </span>
                  ))}
                </div>
              </div>

              {/* Only B */}
              <div className="p-4 rounded-xl border border-purple-200 bg-purple-50/30">
                <div className="flex justify-between items-center mb-2">
                  <h4 className="font-bold text-xs text-purple-900 uppercase">
                    Only in {career_b?.name || career_b?.title}
                  </h4>
                  <span className="font-bold text-purple-700 text-sm">
                    {venn_overlap?.career_b_only_skills_count || 0}
                  </span>
                </div>
                <div className="flex flex-wrap gap-1.5 mt-2 max-h-40 overflow-y-auto">
                  {venn_overlap?.career_b_only_skills?.map((s, idx) => (
                    <span
                      key={idx}
                      className="px-2 py-0.5 bg-white border border-purple-200 text-purple-800 text-[11px] rounded"
                    >
                      {s.skill_name || s.name || s}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* 4-Quadrant Readiness Breakdown */}
          <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200">
            <h3 className="text-base font-bold text-slate-900 mb-4">
              4-Quadrant Student Readiness Breakdown
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-4 bg-emerald-50/50 rounded-xl border border-emerald-100">
                <h4 className="text-xs font-bold text-emerald-800 uppercase flex items-center gap-1.5 mb-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  <span>Ready for Both Careers ({quadrant_breakdown?.ready_for_both?.length || 0})</span>
                </h4>
                <div className="flex flex-wrap gap-1.5">
                  {quadrant_breakdown?.ready_for_both?.map((s, i) => (
                    <span key={i} className="px-2 py-0.5 bg-white text-emerald-700 text-xs rounded border border-emerald-200">
                      {s.name || s.skill_name || s}
                    </span>
                  ))}
                </div>
              </div>

              <div className="p-4 bg-blue-50/50 rounded-xl border border-blue-100">
                <h4 className="text-xs font-bold text-blue-800 uppercase flex items-center gap-1.5 mb-2">
                  <Sparkles className="w-4 h-4 text-blue-600" />
                  <span>Ready for {career_a?.name || career_a?.title} Only ({quadrant_breakdown?.ready_for_a_only?.length || 0})</span>
                </h4>
                <div className="flex flex-wrap gap-1.5">
                  {quadrant_breakdown?.ready_for_a_only?.map((s, i) => (
                    <span key={i} className="px-2 py-0.5 bg-white text-blue-700 text-xs rounded border border-blue-200">
                      {s.name || s.skill_name || s}
                    </span>
                  ))}
                </div>
              </div>

              <div className="p-4 bg-purple-50/50 rounded-xl border border-purple-100">
                <h4 className="text-xs font-bold text-purple-800 uppercase flex items-center gap-1.5 mb-2">
                  <Sparkles className="w-4 h-4 text-purple-600" />
                  <span>Ready for {career_b?.name || career_b?.title} Only ({quadrant_breakdown?.ready_for_b_only?.length || 0})</span>
                </h4>
                <div className="flex flex-wrap gap-1.5">
                  {quadrant_breakdown?.ready_for_b_only?.map((s, i) => (
                    <span key={i} className="px-2 py-0.5 bg-white text-purple-700 text-xs rounded border border-purple-200">
                      {s.name || s.skill_name || s}
                    </span>
                  ))}
                </div>
              </div>

              <div className="p-4 bg-rose-50/50 rounded-xl border border-rose-100">
                <h4 className="text-xs font-bold text-rose-800 uppercase flex items-center gap-1.5 mb-2">
                  <HelpCircle className="w-4 h-4 text-rose-600" />
                  <span>Gap in Both Careers ({quadrant_breakdown?.gap_in_both?.length || 0})</span>
                </h4>
                <div className="flex flex-wrap gap-1.5">
                  {quadrant_breakdown?.gap_in_both?.map((s, i) => (
                    <span key={i} className="px-2 py-0.5 bg-white text-rose-700 text-xs rounded border border-rose-200">
                      {s.name || s.skill_name || s}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
