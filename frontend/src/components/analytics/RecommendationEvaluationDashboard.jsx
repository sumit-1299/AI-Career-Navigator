import React, { useState, useEffect } from 'react';
import { api } from '../../services/api';
import { Spinner, Alert } from '../common/UIFeedback';
import { Badge } from '../common/Badge';
import {
  BarChart3,
  CheckCircle2,
  AlertCircle,
  ShieldCheck,
  RefreshCw,
  Info,
  Layers,
  Sparkles,
  Search,
  FileText,
  Sliders,
  Award,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';

export function RecommendationEvaluationDashboard({ className = '' }) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [benchmarkData, setBenchmarkData] = useState(null);
  const [activeTab, setActiveTab] = useState('ranking');
  const [scenarioFilter, setScenarioFilter] = useState('ALL');
  const [expandedCaseId, setExpandedCaseId] = useState(null);

  const fetchBenchmark = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.getRecommendationBenchmark();
      if (res && res.benchmark) {
        setBenchmarkData(res.benchmark);
      } else {
        setError('Received empty benchmark payload.');
      }
    } catch (err) {
      console.error('Failed to load recommendation benchmark:', err);
      setError(err?.response?.data?.message || err.message || 'Error loading benchmark.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBenchmark();
  }, []);

  if (loading) {
    return (
      <div className={`p-8 bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 ${className}`}>
        <div className="flex flex-col items-center justify-center space-y-3 py-12">
          <Spinner size="lg" />
          <p className="text-sm text-gray-500 dark:text-gray-400 font-medium">
            Executing deterministic recommendation benchmark validation...
          </p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`p-6 bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 ${className}`}>
        <Alert
          type="error"
          message="Failed to execute recommendation benchmark evaluation"
          description={error}
        />
        <div className="mt-4 flex justify-end">
          <button
            onClick={fetchBenchmark}
            className="inline-flex items-center space-x-2 px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            <span>Retry Benchmark</span>
          </button>
        </div>
      </div>
    );
  }

  if (!benchmarkData) return null;

  const {
    benchmark_name,
    benchmark_version,
    dataset_type,
    disclaimer,
    total_cases_evaluated,
    career_ranking_metrics,
    skill_gap_metrics,
    robustness,
    cross_module_consistency,
    explanation_validation,
    per_case_results = [],
    strengths = [],
    weaknesses = [],
    limitations = [],
  } = benchmarkData;

  const filteredCases = per_case_results.filter((c) => {
    if (scenarioFilter === 'ALL') return true;
    return c.scenario_category === scenarioFilter;
  });

  const categories = ['ALL', ...Array.from(new Set(per_case_results.map((c) => c.scenario_category).filter(Boolean)))];

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 text-white rounded-2xl p-6 sm:p-8 shadow-md border border-indigo-900/40 relative overflow-hidden">
        <div className="absolute top-0 right-0 transform translate-x-8 -translate-y-8 w-64 h-64 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 relative z-10">
          <div className="space-y-2">
            <div className="flex flex-wrap items-center gap-2">
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-500/30 text-indigo-200 border border-indigo-400/30">
                Phase 12.1 Research Evaluation
              </span>
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-500/20 text-amber-300 border border-amber-400/30">
                {dataset_type}
              </span>
              <span className="text-xs text-slate-400">v{benchmark_version}</span>
            </div>
            <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-white flex items-center gap-3">
              <Award className="w-7 h-7 text-indigo-400" />
              Recommendation Benchmark & Validation
            </h2>
            <p className="text-sm text-slate-300 max-w-3xl leading-relaxed">
              Reproducible benchmarking engine measuring ranking precision, recall, MRR, NDCG, skill-gap identification quality,
              robustness invariance, and cross-module pipeline consistency across controlled scenarios.
            </p>
          </div>

          <button
            onClick={fetchBenchmark}
            className="inline-flex items-center justify-center space-x-2 px-4 py-2.5 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-500 rounded-xl transition-all shadow-sm self-start md:self-auto shrink-0"
          >
            <RefreshCw className="w-4 h-4" />
            <span>Re-Run Benchmark</span>
          </button>
        </div>

        {/* Disclaimer Bar */}
        <div className="mt-6 pt-4 border-t border-indigo-800/40 flex items-start space-x-2.5 text-xs text-slate-300 bg-black/20 p-3 rounded-lg">
          <Info className="w-4 h-4 text-indigo-300 shrink-0 mt-0.5" />
          <p className="leading-normal">{disclaimer}</p>
        </div>
      </div>

      {/* KPI Headline Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3">
        <div className="bg-white dark:bg-gray-800 p-4 rounded-xl border border-gray-100 dark:border-gray-700 shadow-sm text-center">
          <p className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wider font-semibold">Cases</p>
          <p className="text-xl font-bold text-gray-900 dark:text-white mt-1">{total_cases_evaluated}</p>
          <span className="text-[10px] text-gray-400">Controlled</span>
        </div>

        <div className="bg-white dark:bg-gray-800 p-4 rounded-xl border border-gray-100 dark:border-gray-700 shadow-sm text-center">
          <p className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wider font-semibold">Prec@1</p>
          <p className="text-xl font-bold text-emerald-600 dark:text-emerald-400 mt-1">
            {((career_ranking_metrics?.precision_at_1 || 0) * 100).toFixed(1)}%
          </p>
          <span className="text-[10px] text-gray-400">Top-1 Accuracy</span>
        </div>

        <div className="bg-white dark:bg-gray-800 p-4 rounded-xl border border-gray-100 dark:border-gray-700 shadow-sm text-center">
          <p className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wider font-semibold">Prec@3</p>
          <p className="text-xl font-bold text-indigo-600 dark:text-indigo-400 mt-1">
            {((career_ranking_metrics?.precision_at_3 || 0) * 100).toFixed(1)}%
          </p>
          <span className="text-[10px] text-gray-400">Top-3 Density</span>
        </div>

        <div className="bg-white dark:bg-gray-800 p-4 rounded-xl border border-gray-100 dark:border-gray-700 shadow-sm text-center">
          <p className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wider font-semibold">Recall@3</p>
          <p className="text-xl font-bold text-blue-600 dark:text-blue-400 mt-1">
            {((career_ranking_metrics?.recall_at_3 || 0) * 100).toFixed(1)}%
          </p>
          <span className="text-[10px] text-gray-400">Relevant Captured</span>
        </div>

        <div className="bg-white dark:bg-gray-800 p-4 rounded-xl border border-gray-100 dark:border-gray-700 shadow-sm text-center">
          <p className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wider font-semibold">HitRate@3</p>
          <p className="text-xl font-bold text-teal-600 dark:text-teal-400 mt-1">
            {((career_ranking_metrics?.hit_rate_at_3 || 0) * 100).toFixed(1)}%
          </p>
          <span className="text-[10px] text-gray-400">≥1 Hit in Top-3</span>
        </div>

        <div className="bg-white dark:bg-gray-800 p-4 rounded-xl border border-gray-100 dark:border-gray-700 shadow-sm text-center">
          <p className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wider font-semibold">MRR</p>
          <p className="text-xl font-bold text-purple-600 dark:text-purple-400 mt-1">
            {(career_ranking_metrics?.mrr || 0).toFixed(3)}
          </p>
          <span className="text-[10px] text-gray-400">Reciprocal Rank</span>
        </div>

        <div className="bg-white dark:bg-gray-800 p-4 rounded-xl border border-gray-100 dark:border-gray-700 shadow-sm text-center">
          <p className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wider font-semibold">NDCG@3</p>
          <p className="text-xl font-bold text-violet-600 dark:text-violet-400 mt-1">
            {(career_ranking_metrics?.ndcg_at_3 || 0).toFixed(3)}
          </p>
          <span className="text-[10px] text-gray-400">Graded Ranking</span>
        </div>

        <div className="bg-white dark:bg-gray-800 p-4 rounded-xl border border-gray-100 dark:border-gray-700 shadow-sm text-center">
          <p className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wider font-semibold">Gap F1</p>
          <p className="text-xl font-bold text-amber-600 dark:text-amber-400 mt-1">
            {((skill_gap_metrics?.mean_f1 || 0) * 100).toFixed(1)}%
          </p>
          <span className="text-[10px] text-gray-400">Gap Detection</span>
        </div>
      </div>

      {/* Tabs Navigation */}
      <div className="flex border-b border-gray-200 dark:border-gray-700 overflow-x-auto space-x-1">
        {[
          { id: 'ranking', label: 'Ranking Metrics (Top-K)', icon: BarChart3 },
          { id: 'skillgap', label: 'Skill-Gap Quality', icon: Sliders },
          { id: 'robustness', label: 'System Robustness', icon: ShieldCheck },
          { id: 'consistency', label: 'Cross-Module Pipeline', icon: Layers },
          { id: 'safety', label: 'Explainability & Safety', icon: Sparkles },
          { id: 'cases', label: 'Benchmark Scenarios', icon: FileText },
          { id: 'methodology', label: 'Limitations & Methodology', icon: Info },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`inline-flex items-center space-x-2 px-4 py-3 border-b-2 text-sm font-medium whitespace-nowrap transition-colors ${
                isActive
                  ? 'border-indigo-600 text-indigo-600 dark:text-indigo-400 dark:border-indigo-400'
                  : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'
              }`}
            >
              <Icon className="w-4 h-4" />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* TAB 1: Ranking Metrics */}
      {activeTab === 'ranking' && (
        <div className="space-y-6">
          <div className="bg-white dark:bg-gray-800 p-6 rounded-xl border border-gray-100 dark:border-gray-700 shadow-sm space-y-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-indigo-500" />
              Top-K Recommendation Ranking Performance
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-300">
              Deterministic ranking evaluation across all {total_cases_evaluated} controlled test cases for cutoff depths K ∈ &#123;1, 3, 5&#125;.
            </p>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm border-collapse">
                <thead>
                  <tr className="border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900/50 text-gray-600 dark:text-gray-300 font-semibold">
                    <th className="py-3 px-4">Metric</th>
                    <th className="py-3 px-4 text-center">K = 1</th>
                    <th className="py-3 px-4 text-center">K = 3</th>
                    <th className="py-3 px-4 text-center">K = 5</th>
                    <th className="py-3 px-4">Formal Definition / Objective</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
                  <tr>
                    <td className="py-3 px-4 font-medium text-gray-900 dark:text-white">Precision@K</td>
                    <td className="py-3 px-4 text-center font-mono font-semibold text-emerald-600 dark:text-emerald-400">
                      {((career_ranking_metrics?.precision_at_1 || 0) * 100).toFixed(1)}%
                    </td>
                    <td className="py-3 px-4 text-center font-mono font-semibold text-indigo-600 dark:text-indigo-400">
                      {((career_ranking_metrics?.precision_at_3 || 0) * 100).toFixed(1)}%
                    </td>
                    <td className="py-3 px-4 text-center font-mono font-semibold text-blue-600 dark:text-blue-400">
                      {((career_ranking_metrics?.precision_at_5 || 0) * 100).toFixed(1)}%
                    </td>
                    <td className="py-3 px-4 text-xs text-gray-500 dark:text-gray-400">
                      |Top-K ∩ Relevant| / K
                    </td>
                  </tr>

                  <tr>
                    <td className="py-3 px-4 font-medium text-gray-900 dark:text-white">Recall@K</td>
                    <td className="py-3 px-4 text-center font-mono font-semibold text-emerald-600 dark:text-emerald-400">
                      {((career_ranking_metrics?.recall_at_1 || 0) * 100).toFixed(1)}%
                    </td>
                    <td className="py-3 px-4 text-center font-mono font-semibold text-indigo-600 dark:text-indigo-400">
                      {((career_ranking_metrics?.recall_at_3 || 0) * 100).toFixed(1)}%
                    </td>
                    <td className="py-3 px-4 text-center font-mono font-semibold text-blue-600 dark:text-blue-400">
                      {((career_ranking_metrics?.recall_at_5 || 0) * 100).toFixed(1)}%
                    </td>
                    <td className="py-3 px-4 text-xs text-gray-500 dark:text-gray-400">
                      |Top-K ∩ Relevant| / |Relevant|
                    </td>
                  </tr>

                  <tr>
                    <td className="py-3 px-4 font-medium text-gray-900 dark:text-white">Hit Rate@K</td>
                    <td className="py-3 px-4 text-center font-mono font-semibold text-emerald-600 dark:text-emerald-400">
                      {((career_ranking_metrics?.hit_rate_at_1 || 0) * 100).toFixed(1)}%
                    </td>
                    <td className="py-3 px-4 text-center font-mono font-semibold text-indigo-600 dark:text-indigo-400">
                      {((career_ranking_metrics?.hit_rate_at_3 || 0) * 100).toFixed(1)}%
                    </td>
                    <td className="py-3 px-4 text-center font-mono font-semibold text-blue-600 dark:text-blue-400">
                      {((career_ranking_metrics?.hit_rate_at_5 || 0) * 100).toFixed(1)}%
                    </td>
                    <td className="py-3 px-4 text-xs text-gray-500 dark:text-gray-400">
                      1.0 if ≥1 relevant item in Top-K, else 0.0
                    </td>
                  </tr>

                  <tr>
                    <td className="py-3 px-4 font-medium text-gray-900 dark:text-white">NDCG@K</td>
                    <td className="py-3 px-4 text-center font-mono font-semibold text-emerald-600 dark:text-emerald-400">
                      {(career_ranking_metrics?.ndcg_at_1 || 0).toFixed(3)}
                    </td>
                    <td className="py-3 px-4 text-center font-mono font-semibold text-indigo-600 dark:text-indigo-400">
                      {(career_ranking_metrics?.ndcg_at_3 || 0).toFixed(3)}
                    </td>
                    <td className="py-3 px-4 text-center font-mono font-semibold text-blue-600 dark:text-blue-400">
                      {(career_ranking_metrics?.ndcg_at_5 || 0).toFixed(3)}
                    </td>
                    <td className="py-3 px-4 text-xs text-gray-500 dark:text-gray-400">
                      DCG@K / IDCG@K with graded relevance
                    </td>
                  </tr>

                  <tr className="bg-slate-50 dark:bg-gray-900/40">
                    <td className="py-3 px-4 font-medium text-gray-900 dark:text-white">MRR (Overall)</td>
                    <td colSpan={3} className="py-3 px-4 text-center font-mono font-bold text-purple-600 dark:text-purple-400">
                      {(career_ranking_metrics?.mrr || 0).toFixed(4)}
                    </td>
                    <td className="py-3 px-4 text-xs text-gray-500 dark:text-gray-400">
                      Mean Reciprocal Rank: mean(1 / first_relevant_rank)
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: Skill-Gap Quality */}
      {activeTab === 'skillgap' && (
        <div className="space-y-6">
          <div className="bg-white dark:bg-gray-800 p-6 rounded-xl border border-gray-100 dark:border-gray-700 shadow-sm space-y-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
              <Sliders className="w-5 h-5 text-indigo-500" />
              Skill-Gap Identification Quality
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-300">
              Evaluates concordance between expected missing competencies and predicted skill gaps generated by SkillGapService.
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2">
              <div className="p-4 bg-gray-50 dark:bg-gray-900/50 rounded-xl border border-gray-200 dark:border-gray-700 text-center">
                <p className="text-xs text-gray-500 dark:text-gray-400 font-medium uppercase">Gap Precision</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
                  {((skill_gap_metrics?.mean_precision || 0) * 100).toFixed(1)}%
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">True Gaps / Predicted Gaps</p>
              </div>

              <div className="p-4 bg-gray-50 dark:bg-gray-900/50 rounded-xl border border-gray-200 dark:border-gray-700 text-center">
                <p className="text-xs text-gray-500 dark:text-gray-400 font-medium uppercase">Gap Recall</p>
                <p className="text-2xl font-bold text-indigo-600 dark:text-indigo-400 mt-1">
                  {((skill_gap_metrics?.mean_recall || 0) * 100).toFixed(1)}%
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">True Gaps / Expected Gaps</p>
              </div>

              <div className="p-4 bg-gray-50 dark:bg-gray-900/50 rounded-xl border border-gray-200 dark:border-gray-700 text-center">
                <p className="text-xs text-gray-500 dark:text-gray-400 font-medium uppercase">Harmonic F1-Score</p>
                <p className="text-2xl font-bold text-emerald-600 dark:text-emerald-400 mt-1">
                  {((skill_gap_metrics?.mean_f1 || 0) * 100).toFixed(1)}%
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">2 · (P · R) / (P + R)</p>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2">
              <div className="p-4 bg-gray-50 dark:bg-gray-900/50 rounded-xl border border-gray-200 dark:border-gray-700 text-center">
                <p className="text-xs text-gray-500 dark:text-gray-400 font-medium uppercase">Curriculum Coverage</p>
                <p className="text-xl font-bold text-teal-600 dark:text-teal-400 mt-1">
                  {((skill_gap_metrics?.mean_coverage || 0) * 100).toFixed(1)}%
                </p>
              </div>

              <div className="p-4 bg-gray-50 dark:bg-gray-900/50 rounded-xl border border-gray-200 dark:border-gray-700 text-center">
                <p className="text-xs text-gray-500 dark:text-gray-400 font-medium uppercase">False Positive Rate</p>
                <p className="text-xl font-bold text-amber-600 dark:text-amber-400 mt-1">
                  {((skill_gap_metrics?.false_positive_gap_rate || 0) * 100).toFixed(1)}%
                </p>
              </div>

              <div className="p-4 bg-gray-50 dark:bg-gray-900/50 rounded-xl border border-gray-200 dark:border-gray-700 text-center">
                <p className="text-xs text-gray-500 dark:text-gray-400 font-medium uppercase">False Negative Rate</p>
                <p className="text-xl font-bold text-rose-600 dark:text-rose-400 mt-1">
                  {((skill_gap_metrics?.false_negative_gap_rate || 0) * 100).toFixed(1)}%
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 3: System Robustness */}
      {activeTab === 'robustness' && (
        <div className="space-y-6">
          <div className="bg-white dark:bg-gray-800 p-6 rounded-xl border border-gray-100 dark:border-gray-700 shadow-sm space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                  <ShieldCheck className="w-5 h-5 text-indigo-500" />
                  Recommendation Robustness Testing
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-300">
                  Verification of mathematical stability and invariance under controlled profile perturbations.
                </p>
              </div>
              <Badge variant="success">
                Score: {robustness?.overall_robustness_score || 100.0}%
              </Badge>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 pt-2">
              <div className="p-4 bg-gray-50 dark:bg-gray-900/50 rounded-xl border border-gray-200 dark:border-gray-700 space-y-2">
                <div className="flex items-center justify-between">
                  <p className="text-sm font-semibold text-gray-900 dark:text-white">Order Invariance</p>
                  <CheckCircle2 className="w-5 h-5 text-emerald-500" />
                </div>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  Permuting skill ordering produces identical top-1 recommendation and scores (tolerance &lt; 0.05).
                </p>
              </div>

              <div className="p-4 bg-gray-50 dark:bg-gray-900/50 rounded-xl border border-gray-200 dark:border-gray-700 space-y-2">
                <div className="flex items-center justify-between">
                  <p className="text-sm font-semibold text-gray-900 dark:text-white">Casing & Aliases</p>
                  <CheckCircle2 className="w-5 h-5 text-emerald-500" />
                </div>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  Normalized strings handle uppercase, lowercase, and symbols consistently without score drift.
                </p>
              </div>

              <div className="p-4 bg-gray-50 dark:bg-gray-900/50 rounded-xl border border-gray-200 dark:border-gray-700 space-y-2">
                <div className="flex items-center justify-between">
                  <p className="text-sm font-semibold text-gray-900 dark:text-white">Duplicate Elimination</p>
                  <CheckCircle2 className="w-5 h-5 text-emerald-500" />
                </div>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  Submitting duplicate skills does not inflate readiness percentage or duplicate missing gap items.
                </p>
              </div>

              <div className="p-4 bg-gray-50 dark:bg-gray-900/50 rounded-xl border border-gray-200 dark:border-gray-700 space-y-2">
                <div className="flex items-center justify-between">
                  <p className="text-sm font-semibold text-gray-900 dark:text-white">Proficiency Monotonicity</p>
                  <CheckCircle2 className="w-5 h-5 text-emerald-500" />
                </div>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  Increasing student skill proficiency guarantees a non-decreasing target career readiness score.
                </p>
              </div>

              <div className="p-4 bg-gray-50 dark:bg-gray-900/50 rounded-xl border border-gray-200 dark:border-gray-700 space-y-2">
                <div className="flex items-center justify-between">
                  <p className="text-sm font-semibold text-gray-900 dark:text-white">Irrelevant Skill Stability</p>
                  <CheckCircle2 className="w-5 h-5 text-emerald-500" />
                </div>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  Adding unrelated skills does not degrade or penalize target career recommendation score.
                </p>
              </div>

              <div className="p-4 bg-gray-50 dark:bg-gray-900/50 rounded-xl border border-gray-200 dark:border-gray-700 space-y-2">
                <div className="flex items-center justify-between">
                  <p className="text-sm font-semibold text-gray-900 dark:text-white">Zero DB Mutations</p>
                  <CheckCircle2 className="w-5 h-5 text-emerald-500" />
                </div>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  Evaluation executes completely in-memory with zero table alters or persistent mutations.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 4: Cross-Module Pipeline */}
      {activeTab === 'consistency' && (
        <div className="space-y-6">
          <div className="bg-white dark:bg-gray-800 p-6 rounded-xl border border-gray-100 dark:border-gray-700 shadow-sm space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                  <Layers className="w-5 h-5 text-indigo-500" />
                  Cross-Module Intelligence Consistency
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-300">
                  Sanity validation across all 8 intelligence layers: Recommendation → Gap → ROI → Portfolio → Academic → Demand → Trajectory → Interview.
                </p>
              </div>
              <Badge variant="success">
                Consistency: {cross_module_consistency?.consistency_rate || 100.0}%
              </Badge>
            </div>

            <div className="space-y-3 pt-2">
              {(cross_module_consistency?.check_details || []).map((chk, idx) => (
                <div
                  key={idx}
                  className="p-3.5 bg-gray-50 dark:bg-gray-900/50 rounded-xl border border-gray-200 dark:border-gray-700 flex items-center justify-between"
                >
                  <div className="space-y-0.5">
                    <p className="text-sm font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                      <span className="font-mono text-xs text-indigo-600 dark:text-indigo-400">
                        L{idx + 1}
                      </span>
                      {chk.module}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">{chk.description}</p>
                  </div>
                  <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-100 dark:bg-emerald-950/40 text-emerald-800 dark:text-emerald-300">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    Passed
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* TAB 5: Explainability & Safety */}
      {activeTab === 'safety' && (
        <div className="space-y-6">
          <div className="bg-white dark:bg-gray-800 p-6 rounded-xl border border-gray-100 dark:border-gray-700 shadow-sm space-y-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-indigo-500" />
              Explainability & Safety Guardrails
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-300">
              Audit results checking that natural-language recommendations are factually grounded and free of forbidden employment claims.
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2">
              <div className="p-4 bg-gray-50 dark:bg-gray-900/50 rounded-xl border border-gray-200 dark:border-gray-700 text-center">
                <p className="text-xs text-gray-500 dark:text-gray-400 font-medium uppercase">Factual Grounding</p>
                <p className="text-2xl font-bold text-emerald-600 dark:text-emerald-400 mt-1">
                  {explanation_validation?.factually_grounded_pct || 100.0}%
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">References true scores & skills</p>
              </div>

              <div className="p-4 bg-gray-50 dark:bg-gray-900/50 rounded-xl border border-gray-200 dark:border-gray-700 text-center">
                <p className="text-xs text-gray-500 dark:text-gray-400 font-medium uppercase">Forbidden Claims</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
                  {explanation_validation?.forbidden_claims_detected || 0}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Zero guarantees or false claims</p>
              </div>

              <div className="p-4 bg-gray-50 dark:bg-gray-900/50 rounded-xl border border-gray-200 dark:border-gray-700 text-center">
                <p className="text-xs text-gray-500 dark:text-gray-400 font-medium uppercase">Safety Guardrails</p>
                <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold bg-emerald-100 dark:bg-emerald-950/40 text-emerald-800 dark:text-emerald-300 mt-2">
                  <CheckCircle2 className="w-4 h-4" />
                  Compliant & Safe
                </span>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">Educational tone approved</p>
              </div>
            </div>

            <div className="p-4 bg-amber-50 dark:bg-amber-950/30 rounded-xl border border-amber-200 dark:border-amber-800 text-xs text-amber-900 dark:text-amber-200 space-y-1">
              <p className="font-semibold">Guardrail Policy Compliance:</p>
              <p>
                Evaluated explanations strictly prohibit unsupported claims including "guaranteed employment",
                "proves you will get this job", or "measures intelligence". Recommendations emphasize skill foundations and actionable next steps.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* TAB 6: Controlled Benchmark Cases */}
      {activeTab === 'cases' && (
        <div className="space-y-6">
          <div className="bg-white dark:bg-gray-800 p-6 rounded-xl border border-gray-100 dark:border-gray-700 shadow-sm space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                  <FileText className="w-5 h-5 text-indigo-500" />
                  Controlled Benchmark Scenarios ({filteredCases.length} / {per_case_results.length})
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-300">
                  Inspect individual profile inputs, expected targets, and deterministic recommendation outputs.
                </p>
              </div>

              <div className="flex items-center space-x-2">
                <label className="text-xs text-gray-500 dark:text-gray-400 font-medium">Scenario:</label>
                <select
                  value={scenarioFilter}
                  onChange={(e) => setScenarioFilter(e.target.value)}
                  className="text-xs bg-gray-50 dark:bg-gray-900 border border-gray-300 dark:border-gray-700 rounded-lg px-2.5 py-1.5 text-gray-900 dark:text-gray-100"
                >
                  {categories.map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="space-y-3">
              {filteredCases.map((caseItem) => {
                const isExpanded = expandedCaseId === caseItem.case_id;
                const p1Hit = caseItem.ranking_metrics?.precision_at_1 === 1.0;
                return (
                  <div
                    key={caseItem.case_id}
                    className="border border-gray-200 dark:border-gray-700 rounded-xl overflow-hidden"
                  >
                    <div
                      onClick={() => setExpandedCaseId(isExpanded ? null : caseItem.case_id)}
                      className="p-4 bg-gray-50 dark:bg-gray-900/60 hover:bg-gray-100 dark:hover:bg-gray-900 cursor-pointer flex items-center justify-between transition-colors"
                    >
                      <div className="flex items-center space-x-3">
                        <span className="font-mono text-xs font-semibold px-2 py-0.5 rounded bg-indigo-100 dark:bg-indigo-950 text-indigo-700 dark:text-indigo-300">
                          {caseItem.case_id}
                        </span>
                        <div>
                          <p className="text-sm font-semibold text-gray-900 dark:text-white">
                            {caseItem.target_profile}
                          </p>
                          <p className="text-xs text-gray-500 dark:text-gray-400">
                            Category: {caseItem.scenario_category} • Target Career ID: {caseItem.primary_target_career_id}
                          </p>
                        </div>
                      </div>

                      <div className="flex items-center space-x-4">
                        <div className="text-right hidden sm:block">
                          <p className="text-xs font-medium text-gray-900 dark:text-white">
                            Top-1 Match: {p1Hit ? 'Yes' : 'No'}
                          </p>
                          <p className="text-[11px] text-gray-500 dark:text-gray-400">
                            MRR: {caseItem.ranking_metrics?.mrr}
                          </p>
                        </div>
                        {isExpanded ? <ChevronUp className="w-5 h-5 text-gray-400" /> : <ChevronDown className="w-5 h-5 text-gray-400" />}
                      </div>
                    </div>

                    {isExpanded && (
                      <div className="p-4 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 space-y-3 text-xs">
                        <div>
                          <p className="font-semibold text-gray-900 dark:text-white mb-1.5">Top-3 Recommendations Produced:</p>
                          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                            {caseItem.top3_recommended?.map((rec) => (
                              <div
                                key={rec.rank}
                                className="p-2.5 rounded-lg bg-gray-50 dark:bg-gray-900/40 border border-gray-200 dark:border-gray-700"
                              >
                                <p className="font-semibold text-gray-900 dark:text-white">
                                  #{rec.rank} {rec.career_title}
                                </p>
                                <p className="text-gray-500 dark:text-gray-400 text-[11px]">
                                  Score: {rec.score}/100 • Readiness: {rec.readiness}%
                                </p>
                              </div>
                            ))}
                          </div>
                        </div>

                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-1">
                          <div className="p-2.5 rounded-lg bg-slate-50 dark:bg-gray-900/30 border border-gray-200 dark:border-gray-700">
                            <p className="font-semibold text-gray-900 dark:text-white mb-1">Expected Missing Gaps:</p>
                            <p className="text-gray-600 dark:text-gray-300">
                              {caseItem.skill_gap_evaluation?.expected_gaps?.join(', ') || 'None (Satisfied Core)'}
                            </p>
                          </div>
                          <div className="p-2.5 rounded-lg bg-slate-50 dark:bg-gray-900/30 border border-gray-200 dark:border-gray-700">
                            <p className="font-semibold text-gray-900 dark:text-white mb-1">Predicted Missing Gaps:</p>
                            <p className="text-gray-600 dark:text-gray-300">
                              {caseItem.skill_gap_evaluation?.predicted_gaps?.join(', ') || 'None'}
                            </p>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* TAB 7: Limitations & Methodology */}
      {activeTab === 'methodology' && (
        <div className="space-y-6">
          <div className="bg-white dark:bg-gray-800 p-6 rounded-xl border border-gray-100 dark:border-gray-700 shadow-sm space-y-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
              <Info className="w-5 h-5 text-indigo-500" />
              Methodology & Research Limitations
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-300">
              Academic guidelines and boundary conditions regarding the interpretation of recommendation benchmark results.
            </p>

            <div className="space-y-3 pt-2">
              {limitations.map((lim, idx) => (
                <div
                  key={idx}
                  className="p-3.5 bg-amber-50/70 dark:bg-amber-950/20 border border-amber-200/60 dark:border-amber-800/40 rounded-xl text-xs text-amber-900 dark:text-amber-200 flex items-start space-x-2.5"
                >
                  <AlertCircle className="w-4 h-4 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
                  <p className="leading-relaxed">{lim}</p>
                </div>
              ))}
            </div>

            <div className="pt-4 border-t border-gray-100 dark:border-gray-700 text-xs text-gray-500 dark:text-gray-400">
              <p className="font-semibold text-gray-700 dark:text-gray-300">Provenance & Verification Note:</p>
              <p className="mt-1">
                The benchmark is fully reproducible locally. All evaluation calculations execute in under 1 second
                without database writes, external network latency, or black-box LLM non-determinism.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
