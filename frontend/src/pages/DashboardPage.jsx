import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';
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

  useEffect(() => {
    loadDashboardData();
  }, [targetCareerId]);

  async function loadDashboardData() {
    setLoading(true);
    setError(null);
    try {
      // 1. Fetch careers list
      let careerList = [];
      try {
        const careersRes = await api.listCareers();
        careerList = careersRes?.careers || [];
        setCareers(careerList);
      } catch (err) {
        console.warn('Could not load careers list', err);
      }

      const activeCareer = careerList.find((c) => c.id === targetCareerId) || careerList[0];
      const activeId = activeCareer?.id || targetCareerId || 1;

      // 2. Fetch readiness & skill-gap for active career
      if (activeId) {
        try {
          const gapRes = await api.getSkillGap(activeId);
          setReadinessData(gapRes);
        } catch (err) {
          console.warn('Could not load skill gap for career', activeId, err);
        }

        try {
          const analyticsRes = await api.getCareerAnalytics(activeId);
          setAnalytics(analyticsRes);
        } catch (err) {
          console.warn('Could not load analytics for career', activeId, err);
        }
      }

      // 3. Fetch recommendations
      try {
        const recRes = await api.getCareerRecommendations();
        setRecommendations(recRes?.recommendations || []);
      } catch (err) {
        console.warn('Could not load recommendations', err);
      }

      // 4. Fetch active learning progress (authenticated only)
      try {
        const progressRes = await api.getUserLearningProgress('In Progress');
        setActiveProgress(progressRes?.progress_items || []);
      } catch (err) {
        console.warn('Could not load active progress', err);
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
        <p className="mt-4 text-slate-500 font-medium">Computing career intelligence metrics...</p>
      </div>
    );
  }

  const activeCareer = careers.find((c) => c.id === targetCareerId) || careers[0];
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

  const matchedCount = readinessData?.matched ?? readinessData?.matched_count ?? 0;
  const weakCount = readinessData?.weak ?? readinessData?.weak_count ?? 0;
  const missingCount = readinessData?.missing ?? readinessData?.missing_count ?? 0;
  const totalSkills =
    readinessData?.total_required_skills ??
    readinessData?.total_career_skills ??
    (matchedCount + weakCount + missingCount || 1);

  const missingSkills =
    readinessData?.missing_skills ||
    (readinessData?.skill_gaps?.filter((s) => s.status === 'MISSING') || []);
  const weakSkills =
    readinessData?.weak_skills ||
    (readinessData?.skill_gaps?.filter((s) => s.status === 'WEAK') || []);

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Top Welcome & Career Selector Header */}
      <div className="bg-white rounded-2xl p-6 md:p-8 shadow-sm border border-slate-200 flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-primary-50 text-primary-700 border border-primary-200">
              Active Career Objective
            </span>
          </div>
          <h1 className="text-2xl md:text-3xl font-extrabold text-slate-900 tracking-tight">
            Welcome back, {user?.name || 'Explorer'}
          </h1>
          <p className="text-slate-500 text-sm mt-1">
            Targeting{' '}
            <span className="font-semibold text-slate-800">
              {activeCareer?.career_name || activeCareer?.title || 'Select a career'}
            </span>{' '}
            ({activeCareer?.domain || 'General'})
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3 w-full md:w-auto">
          <label className="text-xs font-medium text-slate-500">Switch Target:</label>
          <select
            value={targetCareerId}
            onChange={(e) => setTargetCareerId(Number(e.target.value))}
            className="bg-slate-50 border border-slate-300 text-slate-800 text-sm rounded-xl focus:ring-primary-500 focus:border-primary-500 px-3.5 py-2.5 font-medium transition cursor-pointer"
          >
            {careers.map((c) => (
              <option key={c.id} value={c.id}>
                {c.career_name || c.title} ({c.domain})
              </option>
            ))}
          </select>
          <Link
            to={`/skill-gap?career_id=${targetCareerId}`}
            className="inline-flex items-center gap-2 px-4 py-2.5 bg-primary-600 hover:bg-primary-700 text-white text-sm font-semibold rounded-xl shadow-md shadow-primary-600/20 transition"
          >
            <span>Roadmap</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </div>

      {error && <Alert type="error" message={error} />}

      {/* Main Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Readiness Circular Meter */}
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200 flex flex-col items-center justify-center text-center">
          <div className="flex items-center justify-between w-full mb-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500">
              Readiness Score
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
          <RadialGauge score={readinessScore} size={170} strokeWidth={14} label="Match Score" />
          <p className="text-xs text-slate-500 mt-4 max-w-xs leading-relaxed">
            Calculated across {totalSkills} canonical skills required for{' '}
            {activeCareer?.career_name || activeCareer?.title || 'target role'}.
          </p>
        </div>

        {/* Skill Match Breakdown */}
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200 flex flex-col justify-between">
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-4">
              Skill Alignment Breakdown
            </h3>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between text-sm mb-1.5 font-medium">
                  <span className="flex items-center gap-1.5 text-emerald-700">
                    <CheckCircle2 className="w-4 h-4" /> Matched Skills
                  </span>
                  <span className="font-semibold text-slate-900">{matchedCount}</span>
                </div>
                <ProgressBar
                  value={matchedCount}
                  max={totalSkills}
                  color="bg-emerald-500"
                />
              </div>

              <div>
                <div className="flex justify-between text-sm mb-1.5 font-medium">
                  <span className="flex items-center gap-1.5 text-amber-700">
                    <AlertCircle className="w-4 h-4" /> Weak / Developing
                  </span>
                  <span className="font-semibold text-slate-900">{weakCount}</span>
                </div>
                <ProgressBar
                  value={weakCount}
                  max={totalSkills}
                  color="bg-amber-500"
                />
              </div>

              <div>
                <div className="flex justify-between text-sm mb-1.5 font-medium">
                  <span className="flex items-center gap-1.5 text-rose-700">
                    <HelpCircle className="w-4 h-4" /> Missing Skills
                  </span>
                  <span className="font-semibold text-slate-900">{missingCount}</span>
                </div>
                <ProgressBar
                  value={missingCount}
                  max={totalSkills}
                  color="bg-rose-500"
                />
              </div>
            </div>
          </div>

          <div className="pt-4 border-t border-slate-100 flex justify-between items-center text-xs text-slate-500">
            <span>Total Needed: {totalSkills} skills</span>
            <Link
              to={`/skill-gap?career_id=${targetCareerId}`}
              className="text-primary-600 font-semibold hover:underline flex items-center gap-1"
            >
              Analyze Gap <ArrowRight className="w-3 h-3" />
            </Link>
          </div>
        </div>

        {/* Readiness Velocity Widget */}
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500">
                Readiness Velocity
              </h3>
              <Badge variant="purple">{analytics?.velocity?.pace_category || 'Steady'} Pace</Badge>
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
              Full Analytics <ArrowRight className="w-3 h-3" />
            </Link>
          </div>
        </div>
      </div>

      {/* Two Column Layout: Top Skill Gaps & Active Learning Pathways */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Top Priority Skill Gaps */}
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
              <p className="text-sm font-semibold text-slate-700">No critical skill gaps!</p>
              <p className="text-xs text-slate-500 mt-1">
                You satisfy all required skills for {activeCareer?.career_name || activeCareer?.title}.
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

        {/* Active Learning In Progress */}
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
              <p className="text-sm font-semibold text-slate-700">No resources currently in progress</p>
              <p className="text-xs text-slate-500 mt-1 mb-4">
                Enroll in a learning module to accelerate your readiness score.
              </p>
              <Link
                to="/learning"
                className="inline-flex items-center gap-2 px-3.5 py-2 bg-primary-600 text-white text-xs font-semibold rounded-lg hover:bg-primary-700 transition"
              >
                <span>Find Modules</span>
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
                      <Clock className="w-3 h-3" /> {item.resource?.estimated_duration_hours || 10}h
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

      {/* Multi-Career Recommendations Carousel/List */}
      <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200">
        <div className="flex items-center justify-between mb-5">
          <div>
            <h2 className="text-lg font-bold text-slate-900">Recommended Alternative Careers</h2>
            <p className="text-xs text-slate-500">
              Ranked by your current skill overlap and transferable competencies
            </p>
          </div>
          <Link to="/careers" className="text-xs text-primary-600 font-semibold hover:underline">
            View All Careers
          </Link>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {recommendations.slice(0, 3).map((rec, idx) => (
            <div
              key={rec.career_id}
              className="p-4 rounded-xl border border-slate-200 hover:border-primary-300 hover:shadow-md transition bg-gradient-to-b from-white to-slate-50 flex flex-col justify-between"
            >
              <div>
                <div className="flex justify-between items-start mb-2">
                  <span className="text-[11px] font-bold px-2 py-0.5 rounded-full bg-slate-100 text-slate-600">
                    Rank #{rec.recommendation_rank || idx + 1}
                  </span>
                  <Badge variant="info">{rec.readiness_category || 'Match'}</Badge>
                </div>
                <h3 className="font-bold text-slate-900 text-base">{rec.career_name}</h3>
                <p className="text-xs text-slate-500 mb-3">{rec.domain}</p>

                <div className="space-y-1.5 mb-4">
                  <div className="flex justify-between text-xs text-slate-600">
                    <span>Readiness Match</span>
                    <span className="font-bold text-slate-900">{rec.readiness_score}%</span>
                  </div>
                  <ProgressBar
                    value={rec.readiness_score || 0}
                    max={100}
                    color="bg-primary-500"
                  />
                </div>

                <div className="text-[11px] text-slate-500 space-y-0.5">
                  <p>✓ {rec.matched_count} matching skills</p>
                  <p>✗ {rec.missing_count} skills to acquire</p>
                </div>
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
          ))}
        </div>
      </div>

      {/* Quick Launchpad Footer */}
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
