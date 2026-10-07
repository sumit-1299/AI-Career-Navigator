import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';
import { Spinner, Alert } from '../components/common/UIFeedback';
import { Badge } from '../components/common/Badge';
import { RadialGauge } from '../components/common/RadialGauge';
import { ProgressBar } from '../components/common/ProgressBar';
import {
  TrendingUp,
  Clock,
  BookOpen,
  Calendar,
  Zap,
  FileText,
  ShieldCheck,
  Award,
} from 'lucide-react';
import { CareerReadinessReport } from '../components/analytics/CareerReadinessReport';
import { RecommendationEvaluationDashboard } from '../components/analytics/RecommendationEvaluationDashboard';

export function AnalyticsPage() {
  const { targetCareerId, setTargetCareerId } = useAuth();

  const [careers, setCareers] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('report'); // 'report' | 'velocity'

  useEffect(() => {
    loadCareers();
  }, []);

  useEffect(() => {
    if (targetCareerId) {
      loadAnalytics(targetCareerId);
    }
  }, [targetCareerId]);

  async function loadCareers() {
    try {
      const res = await api.listCareers();
      setCareers(res?.careers || []);
    } catch (err) {
      console.warn('Could not load careers', err);
    }
  }

  async function loadAnalytics(careerId) {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getCareerAnalytics(careerId);
      setAnalytics(data);
    } catch (err) {
      console.warn('Could not load analytics', err);
    } finally {
      setLoading(false);
    }
  }

  const {
    career_name,
    current_readiness = 0,
    baseline_readiness = 0,
    net_readiness_gain = 0,
    total_resources_completed = 0,
    total_learning_hours = 0,
    velocity = {},
    skills_timeline = [],
  } = analytics || {};

  return (
    <div className="space-y-6">
      {/* Header & Sub-tab Navigation */}
      <div className="bg-white rounded-2xl p-6 md:p-8 shadow-sm border border-slate-200 flex flex-col md:flex-row items-start md:items-center justify-between gap-6 no-print">
        <div>
          <div className="flex items-center gap-2 mb-1.5">
            <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200">
              Readiness Diagnostics & Placement Analytics
            </span>
          </div>
          <h1 className="text-2xl md:text-3xl font-extrabold text-slate-900 tracking-tight">
            Readiness Analytics & Reports
          </h1>
          <p className="text-slate-500 text-sm mt-1">
            Tracking employability, competency gaps, and learning trajectory towards{' '}
            <span className="font-semibold text-slate-800">{career_name || 'Target Role'}</span>
          </p>

          {/* Sub-tab navigation */}
          <div className="flex items-center gap-2 mt-4 p-1 bg-slate-100 rounded-xl w-fit">
            <button
              type="button"
              onClick={() => setActiveTab('report')}
              className={`px-3.5 py-1.5 rounded-lg text-xs font-bold transition flex items-center gap-1.5 ${
                activeTab === 'report'
                  ? 'bg-white text-slate-900 shadow-xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <ShieldCheck className="w-4 h-4 text-primary-600" />
              <span>Placement Readiness Report</span>
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('velocity')}
              className={`px-3.5 py-1.5 rounded-lg text-xs font-bold transition flex items-center gap-1.5 ${
                activeTab === 'velocity'
                  ? 'bg-white text-slate-900 shadow-xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <TrendingUp className="w-4 h-4 text-indigo-600" />
              <span>Velocity & Learning ROI</span>
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('benchmark')}
              className={`px-3.5 py-1.5 rounded-lg text-xs font-bold transition flex items-center gap-1.5 ${
                activeTab === 'benchmark'
                  ? 'bg-white text-slate-900 shadow-xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <Award className="w-4 h-4 text-purple-600" />
              <span>Research Benchmark</span>
            </button>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <label className="text-xs font-medium text-slate-500">Career Focus:</label>
          <select
            value={targetCareerId}
            onChange={(e) => setTargetCareerId(Number(e.target.value))}
            className="bg-slate-50 border border-slate-300 text-slate-800 text-sm rounded-xl px-3.5 py-2.5 font-medium transition cursor-pointer"
          >
            {careers.map((c) => (
              <option key={c.id} value={c.id}>
                {c.career_name || c.title}
              </option>
            ))}
          </select>
        </div>
      </div>

      {activeTab === 'benchmark' ? (
        <RecommendationEvaluationDashboard />
      ) : activeTab === 'report' ? (
        <CareerReadinessReport
          careerId={targetCareerId}
          careerName={career_name || 'Target Role'}
        />
      ) : (
        <>
          {error && <Alert type="error" message={error} />}

          {loading ? (
            <div className="flex flex-col items-center justify-center py-20">
              <Spinner size="lg" />
              <p className="mt-4 text-slate-500 font-medium">Computing learning velocity metrics...</p>
            </div>
          ) : analytics ? (
            <div className="space-y-6 animate-fadeIn">
          {/* Velocity KPI Strip */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex items-center gap-4">
              <div className="p-3 bg-indigo-50 text-indigo-600 rounded-xl">
                <Zap className="w-6 h-6" />
              </div>
              <div>
                <span className="text-xs text-slate-400 font-medium">Weekly Pace</span>
                <p className="text-2xl font-black text-slate-900 mt-0.5">
                  +{velocity.readiness_points_per_week ?? '0.0'} pts
                </p>
                <p className="text-[11px] text-slate-400">per active week</p>
              </div>
            </div>

            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex items-center gap-4">
              <div className="p-3 bg-emerald-50 text-emerald-600 rounded-xl">
                <TrendingUp className="w-6 h-6" />
              </div>
              <div>
                <span className="text-xs text-slate-400 font-medium">Net Readiness Gain</span>
                <p className="text-2xl font-black text-emerald-600 mt-0.5">
                  +{net_readiness_gain}%
                </p>
                <p className="text-[11px] text-slate-400">from baseline ({baseline_readiness}%)</p>
              </div>
            </div>

            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex items-center gap-4">
              <div className="p-3 bg-blue-50 text-blue-600 rounded-xl">
                <BookOpen className="w-6 h-6" />
              </div>
              <div>
                <span className="text-xs text-slate-400 font-medium">Modules Completed</span>
                <p className="text-2xl font-black text-slate-900 mt-0.5">
                  {total_resources_completed}
                </p>
                <p className="text-[11px] text-slate-400">curated resources</p>
              </div>
            </div>

            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex items-center gap-4">
              <div className="p-3 bg-amber-50 text-amber-600 rounded-xl">
                <Clock className="w-6 h-6" />
              </div>
              <div>
                <span className="text-xs text-slate-400 font-medium">Time Invested</span>
                <p className="text-2xl font-black text-slate-900 mt-0.5">
                  {total_learning_hours} hrs
                </p>
                <p className="text-[11px] text-slate-400">estimated learning</p>
              </div>
            </div>
          </div>

          {/* Main Visuals Grid: Readiness Trajectory & ROI Efficiency */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Current vs Baseline Gauge */}
            <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200 flex flex-col items-center justify-center text-center">
              <div className="flex justify-between items-center w-full mb-3">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                  Target Readiness
                </span>
                <Badge variant="purple">{velocity.pace_category || 'Steady'} Pace</Badge>
              </div>
              <RadialGauge
                score={current_readiness}
                size={160}
                strokeWidth={14}
                label="Current Score"
              />
              <div className="mt-4 flex items-center justify-around w-full text-xs">
                <div>
                  <p className="text-slate-400">Starting Point</p>
                  <p className="font-bold text-slate-700 text-sm">{baseline_readiness}%</p>
                </div>
                <div className="w-px h-8 bg-slate-200" />
                <div>
                  <p className="text-slate-400">Efficiency</p>
                  <p className="font-bold text-indigo-600 text-sm">
                    {velocity.readiness_points_per_resource ?? 0} pts/mod
                  </p>
                </div>
              </div>
            </div>

            {/* Growth Progress Breakdown */}
            <div className="md:col-span-2 bg-white rounded-2xl p-6 shadow-sm border border-slate-200 flex flex-col justify-between">
              <div>
                <h3 className="text-base font-bold text-slate-900 mb-1">
                  Readiness Progression Breakdown
                </h3>
                <p className="text-xs text-slate-500 mb-6">
                  Comparison between your initial diagnostic assessment and current achievement.
                </p>

                <div className="space-y-5">
                  <div>
                    <div className="flex justify-between text-xs font-semibold mb-1.5 text-slate-600">
                      <span>Baseline Readiness (Onboarding)</span>
                      <span>{baseline_readiness}%</span>
                    </div>
                    <ProgressBar value={baseline_readiness} max={100} color="bg-slate-400" />
                  </div>

                  <div>
                    <div className="flex justify-between text-xs font-semibold mb-1.5 text-primary-700">
                      <span>Current Verified Readiness</span>
                      <span className="font-bold text-slate-900">{current_readiness}%</span>
                    </div>
                    <ProgressBar value={current_readiness} max={100} color="bg-primary-600" />
                  </div>

                  <div>
                    <div className="flex justify-between text-xs font-semibold mb-1.5 text-emerald-700">
                      <span>Target Employment Benchmark</span>
                      <span>100%</span>
                    </div>
                    <ProgressBar value={100} max={100} color="bg-emerald-200" />
                  </div>
                </div>
              </div>

              <div className="p-4 mt-6 bg-slate-50 rounded-xl border border-slate-100 flex items-center justify-between text-xs text-slate-600">
                <span className="font-medium">Remaining distance to target benchmark:</span>
                <span className="font-bold text-slate-900">
                  {Math.max(0, 100 - current_readiness)}% readiness needed
                </span>
              </div>
            </div>
          </div>

          {/* Skills Progression Timeline */}
          <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200">
            <h3 className="text-base font-bold text-slate-900 mb-2 flex items-center gap-2">
              <Calendar className="w-5 h-5 text-indigo-600" />
              <span>Competency Acquisition Timeline</span>
            </h3>
            <p className="text-xs text-slate-500 mb-6">
              Audit trail of validated skills and proficiency increments.
            </p>

            {skills_timeline.length === 0 ? (
              <p className="text-xs text-slate-500 italic py-4">
                No chronological acquisition events logged yet. Complete modules to see your
                timeline grow!
              </p>
            ) : (
              <div className="space-y-4 border-l-2 border-slate-200 pl-4 ml-2">
                {skills_timeline.map((item, idx) => (
                  <div key={idx} className="relative">
                    <span className="absolute -left-[23px] top-1 w-3.5 h-3.5 rounded-full bg-primary-600 border-2 border-white" />
                    <div>
                      <div className="flex items-center gap-2">
                        <h4 className="font-bold text-sm text-slate-900">{item.skill_name}</h4>
                        <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-slate-100 text-slate-600">
                          {item.event_type || 'Skill Verified'}
                        </span>
                      </div>
                      <p className="text-xs text-slate-500 mt-0.5">
                        {item.date || 'Recent'} • Proficiency: Level {item.proficiency}/10
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      ) : (
        <div className="bg-white rounded-2xl p-12 text-center border border-slate-200">
          <p className="text-slate-500 text-sm">No analytics recorded yet for this role.</p>
        </div>
      )}
        </>
      )}
    </div>
  );
}
