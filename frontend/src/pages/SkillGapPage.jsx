import React, { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';
import { RadialGauge } from '../components/common/RadialGauge';
import { Badge } from '../components/common/Badge';
import { Spinner, Alert } from '../components/common/UIFeedback';
import {
  Target,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  Award,
  BookOpen,
  Milestone,
  Sparkles,
  ExternalLink,
  Clock,
  Calendar,
  Flame,
} from 'lucide-react';

export function SkillGapPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const { targetCareerId, setTargetCareerId } = useAuth();

  const careerIdFromUrl = searchParams.get('career_id');
  const activeCareerId = careerIdFromUrl ? Number(careerIdFromUrl) : targetCareerId;

  const [careers, setCareers] = useState([]);
  const [gapData, setGapData] = useState(null);
  const [roadmapData, setRoadmapData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('gap'); // 'gap' | 'roadmap'

  // Module 8.3: Study intensity (5 | 10 | 20 hours/week)
  const [hoursPerWeek, setHoursPerWeek] = useState(10);
  const [updatingTimeline, setUpdatingTimeline] = useState(false);

  useEffect(() => {
    loadData();
  }, [activeCareerId]);

  async function loadData() {
    setLoading(true);
    setError(null);
    try {
      try {
        const careersRes = await api.listCareers();
        setCareers(careersRes?.careers || []);
      } catch (e) {
        console.warn('Could not load careers', e);
      }

      const [gapRes, roadRes] = await Promise.all([
        api.getSkillGap(activeCareerId).catch((e) => {
          console.warn('Skill gap fetch failed', e);
          return null;
        }),
        api.getRoadmap(activeCareerId, hoursPerWeek).catch((e) => {
          console.warn('Roadmap fetch failed', e);
          return null;
        }),
      ]);

      setGapData(gapRes);
      setRoadmapData(roadRes);
    } catch (err) {
      setError(err.message || 'Failed to load skill-gap analysis');
    } finally {
      setLoading(false);
    }
  }

  async function handleIntensityChange(hrs) {
    setHoursPerWeek(hrs);
    setUpdatingTimeline(true);
    try {
      const roadRes = await api.getRoadmap(activeCareerId, hrs);
      setRoadmapData(roadRes);
    } catch (e) {
      console.warn('Failed to update study plan roadmap:', e);
    } finally {
      setUpdatingTimeline(false);
    }
  }

  function handleCareerChange(newId) {
    setSearchParams({ career_id: newId });
    setTargetCareerId(Number(newId));
  }

  const selectedCareer = careers.find((c) => c.id === activeCareerId);
  const score = Math.round(
    gapData?.readiness_percentage ?? gapData?.readiness_score ?? 0
  );
  const category =
    gapData?.readiness_category ??
    (score >= 80
      ? 'Advanced'
      : score >= 60
      ? 'Proficient'
      : score >= 30
      ? 'Developing'
      : 'Novice');

  const matchedCount = gapData?.matched ?? gapData?.matched_count ?? 0;
  const weakCount = gapData?.weak ?? gapData?.weak_count ?? 0;
  const missingCount = gapData?.missing ?? gapData?.missing_count ?? 0;

  const missingSkills =
    gapData?.missing_skills ||
    (gapData?.skill_gaps?.filter((s) => s.status === 'MISSING') || []);
  const weakSkills =
    gapData?.weak_skills ||
    (gapData?.skill_gaps?.filter((s) => s.status === 'WEAK') || []);
  const matchedSkills =
    gapData?.matched_skills ||
    (gapData?.skill_gaps?.filter((s) => s.status === 'MATCHED') || []);

  const roadmapSteps =
    roadmapData?.roadmap?.sequential_steps ||
    roadmapData?.roadmap?.steps ||
    roadmapData?.roadmap_steps ||
    roadmapData?.steps ||
    [];
  const certifications =
    roadmapData?.roadmap?.certifications ||
    roadmapData?.certifications ||
    [];

  // Module 8.3: Study intensity & timeline metrics
  const estimatedTotalHours =
    roadmapData?.estimated_total_hours ??
    roadmapData?.roadmap?.estimated_total_hours ??
    roadmapData?.roadmap?.study_plan?.estimated_total_hours ??
    0;
  const estimatedWeeks =
    roadmapData?.estimated_weeks ??
    roadmapData?.roadmap?.estimated_weeks ??
    roadmapData?.roadmap?.study_plan?.estimated_weeks ??
    0;
  const estimatedCompletionDate =
    roadmapData?.estimated_completion_date ??
    roadmapData?.roadmap?.estimated_completion_date ??
    roadmapData?.roadmap?.study_plan?.estimated_completion_date ??
    null;
  const weeklyMilestones =
    roadmapData?.weekly_milestones ??
    roadmapData?.roadmap?.weekly_milestones ??
    roadmapData?.roadmap?.study_plan?.weekly_milestones ??
    [];

  return (
    <div className="space-y-6">
      {/* Header & Target Career Switcher */}
      <div className="bg-white rounded-2xl p-6 md:p-8 shadow-sm border border-slate-200 flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
        <div>
          <div className="flex items-center gap-2 mb-1.5">
            <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-primary-50 text-primary-700 border border-primary-200">
              Readiness & Pathway Analysis
            </span>
          </div>
          <h1 className="text-2xl md:text-3xl font-extrabold text-slate-900 tracking-tight">
            Skill-Gap Analysis & Roadmap
          </h1>
          <p className="text-slate-500 text-sm mt-1">
            Analyzing readiness for{' '}
            <span className="font-semibold text-slate-800">
              {gapData?.career_name || gapData?.career || selectedCareer?.career_name || selectedCareer?.title || 'Selected Career'}
            </span>
          </p>
        </div>

        <div className="flex items-center gap-3">
          <label className="text-xs font-medium text-slate-500">Target Role:</label>
          <select
            value={activeCareerId}
            onChange={(e) => handleCareerChange(e.target.value)}
            className="bg-slate-50 border border-slate-300 text-slate-800 text-sm rounded-xl px-3.5 py-2.5 font-medium transition cursor-pointer focus:ring-primary-500 focus:border-primary-500"
          >
            {careers.map((c) => (
              <option key={c.id} value={c.id}>
                {c.career_name || c.title}
              </option>
            ))}
          </select>
        </div>
      </div>

      {error && <Alert type="error" message={error} />}

      {loading ? (
        <div className="flex flex-col items-center justify-center py-20">
          <Spinner size="lg" />
          <p className="mt-4 text-slate-500 font-medium">Evaluating career skill delta...</p>
        </div>
      ) : (
        <>
          {/* Summary Scorecard */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200 flex flex-col items-center justify-center text-center">
              <RadialGauge score={score} size={130} strokeWidth={12} label="Readiness" />
              <Badge
                variant={
                  category === 'Advanced'
                    ? 'success'
                    : category === 'Proficient'
                    ? 'info'
                    : category === 'Developing'
                    ? 'warning'
                    : 'neutral'
                }
                className="mt-3"
              >
                {category} Status
              </Badge>
            </div>

            <div className="bg-white rounded-2xl p-5 shadow-sm border border-slate-200 flex flex-col justify-between">
              <div className="flex items-center gap-2 text-emerald-600 mb-2">
                <CheckCircle2 className="w-5 h-5" />
                <span className="text-xs font-bold uppercase tracking-wider">Matched Skills</span>
              </div>
              <div className="text-3xl font-extrabold text-slate-900">
                {matchedCount}
              </div>
              <p className="text-xs text-slate-400 mt-1">Proficiency meets or exceeds standard</p>
            </div>

            <div className="bg-white rounded-2xl p-5 shadow-sm border border-slate-200 flex flex-col justify-between">
              <div className="flex items-center gap-2 text-amber-600 mb-2">
                <AlertCircle className="w-5 h-5" />
                <span className="text-xs font-bold uppercase tracking-wider">Weak Skills</span>
              </div>
              <div className="text-3xl font-extrabold text-slate-900">
                {weakCount}
              </div>
              <p className="text-xs text-slate-400 mt-1">Known, but requires higher mastery</p>
            </div>

            <div className="bg-white rounded-2xl p-5 shadow-sm border border-slate-200 flex flex-col justify-between">
              <div className="flex items-center gap-2 text-rose-600 mb-2">
                <HelpCircle className="w-5 h-5" />
                <span className="text-xs font-bold uppercase tracking-wider">Missing Skills</span>
              </div>
              <div className="text-3xl font-extrabold text-slate-900">
                {missingCount}
              </div>
              <p className="text-xs text-slate-400 mt-1">Definite gap to bridge</p>
            </div>
          </div>

          {/* Tab Navigation */}
          <div className="flex gap-2 border-b border-slate-200 pb-2">
            <button
              onClick={() => setActiveTab('gap')}
              className={`px-4 py-2 rounded-xl text-sm font-semibold transition ${
                activeTab === 'gap'
                  ? 'bg-primary-600 text-white shadow-sm'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
              }`}
            >
              Skill Categorization Matrix
            </button>
            <button
              onClick={() => setActiveTab('roadmap')}
              className={`px-4 py-2 rounded-xl text-sm font-semibold transition ${
                activeTab === 'roadmap'
                  ? 'bg-primary-600 text-white shadow-sm'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
              }`}
            >
              Sequential Career Roadmap & Certs
            </button>
          </div>

          {/* TAB 1: Skill Categorization Matrix */}
          {activeTab === 'gap' && (
            <div className="space-y-6">
              {/* Missing Skills Grid */}
              <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2.5">
                    <span className="p-2 bg-rose-50 text-rose-600 rounded-lg">
                      <HelpCircle className="w-5 h-5" />
                    </span>
                    <div>
                      <h3 className="text-base font-bold text-slate-900">
                        Missing Skills ({missingSkills.length})
                      </h3>
                      <p className="text-xs text-slate-500">
                        Essential competencies missing from your profile
                      </p>
                    </div>
                  </div>
                </div>

                {missingSkills.length === 0 ? (
                  <p className="text-xs text-slate-500 py-3 italic">
                    Great news! You have no completely missing skills for this career.
                  </p>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                    {missingSkills.map((skill, idx) => {
                      const sName = skill.skill_name || skill.name;
                      const cId = skill.canonical_skill_id || skill.canonical_id || '';
                      const reqLvl = skill.required_level || 5;
                      const cat = skill.priority_level || skill.category || 'Core Skill';

                      return (
                        <div
                          key={idx}
                          className="p-4 rounded-xl border border-rose-200 bg-rose-50/30 flex flex-col justify-between"
                        >
                          <div>
                            <div className="flex justify-between items-start gap-2 mb-1">
                              <h4 className="font-bold text-sm text-slate-900">{sName}</h4>
                              <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-rose-100 text-rose-700">
                                Req: Level {reqLvl}/10
                              </span>
                            </div>
                            <p className="text-[11px] text-slate-500">
                              Category: {cat}
                            </p>
                          </div>

                          <Link
                            to={`/learning?skill_id=${cId}`}
                            className="mt-3 inline-flex items-center gap-1.5 text-xs font-semibold text-rose-700 hover:text-rose-800 hover:underline"
                          >
                            <BookOpen className="w-3.5 h-3.5" />
                            <span>Find Learning Resources →</span>
                          </Link>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>

              {/* Weak Skills Grid */}
              <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2.5">
                    <span className="p-2 bg-amber-50 text-amber-600 rounded-lg">
                      <AlertCircle className="w-5 h-5" />
                    </span>
                    <div>
                      <h3 className="text-base font-bold text-slate-900">
                        Weak / Developing Skills ({weakSkills.length})
                      </h3>
                      <p className="text-xs text-slate-500">
                        Skills where your proficiency is below role requirement
                      </p>
                    </div>
                  </div>
                </div>

                {weakSkills.length === 0 ? (
                  <p className="text-xs text-slate-500 py-3 italic">
                    No weak skills identified for this role.
                  </p>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                    {weakSkills.map((skill, idx) => {
                      const sName = skill.skill_name || skill.name;
                      const cId = skill.canonical_skill_id || skill.canonical_id || '';
                      const curLvl = skill.current_proficiency ?? skill.student_level ?? 0;
                      const reqLvl = skill.required_level || 5;

                      return (
                        <div
                          key={idx}
                          className="p-4 rounded-xl border border-amber-200 bg-amber-50/30 flex flex-col justify-between"
                        >
                          <div>
                            <div className="flex justify-between items-start gap-2 mb-1">
                              <h4 className="font-bold text-sm text-slate-900">{sName}</h4>
                              <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-amber-100 text-amber-800">
                                Lvl {curLvl} → {reqLvl}
                              </span>
                            </div>
                            <p className="text-[11px] text-slate-500">
                              Delta: +{Math.max(1, reqLvl - curLvl)} levels needed
                            </p>
                          </div>

                          <Link
                            to={`/learning?skill_id=${cId}`}
                            className="mt-3 inline-flex items-center gap-1.5 text-xs font-semibold text-amber-800 hover:underline"
                          >
                            <Sparkles className="w-3.5 h-3.5" />
                            <span>Level-Up Resources →</span>
                          </Link>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>

              {/* Matched Skills Grid */}
              <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2.5">
                    <span className="p-2 bg-emerald-50 text-emerald-600 rounded-lg">
                      <CheckCircle2 className="w-5 h-5" />
                    </span>
                    <div>
                      <h3 className="text-base font-bold text-slate-900">
                        Matched Skills ({matchedSkills.length})
                      </h3>
                      <p className="text-xs text-slate-500">
                        Proficiencies verified at or above target threshold
                      </p>
                    </div>
                  </div>
                </div>

                {matchedSkills.length === 0 ? (
                  <p className="text-xs text-slate-500 py-3 italic">
                    No matched skills yet. Add skills to your profile or complete courses!
                  </p>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                    {matchedSkills.map((skill, idx) => {
                      const sName = skill.skill_name || skill.name;
                      const curLvl = skill.current_proficiency ?? skill.student_level ?? 0;
                      const reqLvl = skill.required_level || 5;

                      return (
                        <div
                          key={idx}
                          className="p-3.5 rounded-xl border border-emerald-200 bg-emerald-50/30 flex items-center justify-between"
                        >
                          <div>
                            <p className="font-semibold text-sm text-slate-900">{sName}</p>
                            <p className="text-[11px] text-emerald-700">
                              Student: Lvl {curLvl}/10 (Req: {reqLvl})
                            </p>
                          </div>
                          <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* TAB 2: Sequential Career Roadmap & Certs */}
          {activeTab === 'roadmap' && (
            <div className="space-y-6">
              {/* Study Intensity & Completion Timeline (Module 8.3) */}
              <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-5 border-b border-slate-100">
                  <div className="flex items-center gap-3">
                    <span className="p-2.5 bg-primary-50 text-primary-600 rounded-xl">
                      <Clock className="w-5 h-5" />
                    </span>
                    <div>
                      <h3 className="text-base font-bold text-slate-900">
                        Study Intensity & Completion Timeline
                      </h3>
                      <p className="text-xs text-slate-500">
                        Select your weekly study commitment to project your completion timeline and milestones.
                      </p>
                    </div>
                  </div>

                  {/* Intensity Selector: 5 / 10 / 20 hrs/week */}
                  <div className="flex items-center gap-1.5 p-1 bg-slate-100 rounded-xl">
                    {[
                      { hours: 5, label: '5 hrs/wk', pace: 'Light' },
                      { hours: 10, label: '10 hrs/wk', pace: 'Standard' },
                      { hours: 20, label: '20 hrs/wk', pace: 'Intensive' },
                    ].map(({ hours, label, pace }) => (
                      <button
                        key={hours}
                        type="button"
                        onClick={() => handleIntensityChange(hours)}
                        disabled={updatingTimeline}
                        className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition ${
                          hoursPerWeek === hours
                            ? 'bg-primary-600 text-white shadow-xs'
                            : 'text-slate-600 hover:text-slate-900 hover:bg-white/60'
                        }`}
                        title={`${pace} pace (${hours} hours per week)`}
                      >
                        {label}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Timeline Metrics Strip */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-5">
                  <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 text-center">
                    <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block">
                      Study Intensity
                    </span>
                    <p className="text-xl font-extrabold text-slate-900 mt-1 flex items-center justify-center gap-1">
                      <Flame className="w-4 h-4 text-amber-500" />
                      {hoursPerWeek} hrs/week
                    </p>
                  </div>
                  <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 text-center">
                    <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block">
                      Total Workload
                    </span>
                    <p className="text-xl font-extrabold text-slate-900 mt-1">
                      {estimatedTotalHours} hrs
                    </p>
                  </div>
                  <div className="p-4 rounded-xl bg-primary-50/50 border border-primary-200 text-center">
                    <span className="text-[11px] font-bold text-primary-700 uppercase tracking-wider block">
                      Estimated Duration
                    </span>
                    <p className="text-xl font-extrabold text-primary-700 mt-1">
                      {estimatedWeeks} {estimatedWeeks === 1 ? 'Week' : 'Weeks'}
                    </p>
                  </div>
                  <div className="p-4 rounded-xl bg-emerald-50/50 border border-emerald-200 text-center">
                    <span className="text-[11px] font-bold text-emerald-800 uppercase tracking-wider block">
                      Target Completion
                    </span>
                    <p className="text-sm font-extrabold text-emerald-700 mt-1.5 flex items-center justify-center gap-1">
                      <Calendar className="w-3.5 h-3.5" />
                      {estimatedCompletionDate || 'N/A'}
                    </p>
                  </div>
                </div>

                {/* Weekly Milestones Breakdown */}
                {weeklyMilestones.length > 0 && (
                  <div className="mt-6 pt-5 border-t border-slate-100">
                    <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider mb-3">
                      Week-by-Week Milestones ({weeklyMilestones.length} Weeks)
                    </h4>
                    <div className="space-y-2.5 max-h-72 overflow-y-auto pr-1">
                      {weeklyMilestones.map((m) => (
                        <div
                          key={m.week}
                          className="p-3 rounded-xl border border-slate-200 bg-slate-50/60 flex flex-col sm:flex-row sm:items-center justify-between gap-2.5 text-xs"
                        >
                          <div className="flex items-center gap-3">
                            <span className="w-16 px-2 py-1 rounded-md bg-white border border-slate-200 font-bold text-slate-800 text-center shrink-0">
                              Week {m.week}
                            </span>
                            <div className="flex flex-wrap gap-1.5">
                              {m.skills && m.skills.length > 0 ? (
                                m.skills.map((sk, idx) => (
                                  <span
                                    key={idx}
                                    className="px-2 py-0.5 rounded-md bg-primary-50 text-primary-700 font-semibold text-[11px]"
                                  >
                                    {sk}
                                  </span>
                                ))
                              ) : (
                                <span className="text-slate-400 italic text-[11px]">Review & Labs</span>
                              )}
                            </div>
                          </div>
                          <span className="font-semibold text-slate-500 text-[11px] shrink-0">
                            {m.target_hours} hrs target
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Sequential Steps */}
              <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200">
                <div className="flex items-center gap-2.5 mb-6">
                  <span className="p-2 bg-primary-50 text-primary-600 rounded-lg">
                    <Milestone className="w-5 h-5" />
                  </span>
                  <div>
                    <h3 className="text-base font-bold text-slate-900">
                      Step-by-Step Acquisition Plan
                    </h3>
                    <p className="text-xs text-slate-500">
                      Sequenced by foundational prerequisite hierarchy and role impact
                    </p>
                  </div>
                </div>

                {roadmapSteps.length > 0 ? (
                  <div className="space-y-4">
                    {roadmapSteps.map((step, idx) => (
                      <div
                        key={idx}
                        className="p-4 rounded-xl border border-slate-200 bg-slate-50/50 flex flex-col md:flex-row items-start md:items-center justify-between gap-4"
                      >
                        <div className="flex items-start gap-3">
                          <span className="w-7 h-7 rounded-full bg-primary-600 text-white font-bold text-xs flex items-center justify-center shrink-0 mt-0.5">
                            {step.order || idx + 1}
                          </span>
                          <div>
                            <div className="flex items-center gap-2">
                              <h4 className="font-bold text-slate-900 text-sm">
                                {step.skill_name || step.name}
                              </h4>
                              <Badge
                                variant={
                                  step.priority === 'High' || step.priority === 'HIGH'
                                    ? 'danger'
                                    : step.priority === 'Medium' || step.priority === 'MEDIUM'
                                    ? 'warning'
                                    : 'neutral'
                                }
                              >
                                {step.priority || step.priority_level || 'High'} Priority
                              </Badge>
                            </div>
                            <p className="text-xs text-slate-500 mt-1">
                              Action: {step.action || step.explanation || `Acquire ${step.skill_name || step.name} proficiency`}
                            </p>
                          </div>
                        </div>

                        <Link
                          to={`/learning?skill_id=${step.canonical_skill_id || ''}`}
                          className="px-3.5 py-2 bg-white hover:bg-primary-50 text-primary-600 border border-slate-200 rounded-xl text-xs font-semibold shadow-sm transition flex items-center gap-1.5 shrink-0"
                        >
                          <BookOpen className="w-3.5 h-3.5" />
                          <span>Start Learning</span>
                        </Link>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-slate-500 italic py-4">
                    No active roadmap steps needed. Your skills align with the career requirements.
                  </p>
                )}
              </div>

              {/* Recommended Certifications */}
              {certifications.length > 0 && (
                <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200">
                  <div className="flex items-center gap-2.5 mb-4">
                    <span className="p-2 bg-amber-50 text-amber-600 rounded-lg">
                      <Award className="w-5 h-5" />
                    </span>
                    <div>
                      <h3 className="text-base font-bold text-slate-900">
                        Industry-Recognized Certifications
                      </h3>
                      <p className="text-xs text-slate-500">
                        Boost your market employability with verifiable credentials
                      </p>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {certifications.map((cert, idx) => (
                      <div
                        key={idx}
                        className="p-4 rounded-xl border border-slate-200 bg-slate-50/30 flex items-start justify-between gap-3"
                      >
                        <div>
                          <h4 className="font-bold text-sm text-slate-900">{cert.title || cert.name}</h4>
                          <p className="text-xs text-slate-500 mt-0.5">
                            Issuer: {cert.provider || cert.issuer || 'Industry Standard'}
                          </p>
                          {cert.difficulty && (
                            <span className="inline-block mt-2 text-[10px] font-semibold px-2 py-0.5 rounded bg-slate-200 text-slate-700">
                              {cert.difficulty}
                            </span>
                          )}
                        </div>
                        {cert.url && (
                          <a
                            href={cert.url}
                            target="_blank"
                            rel="noreferrer"
                            className="p-2 text-slate-400 hover:text-primary-600 transition"
                          >
                            <ExternalLink className="w-4 h-4" />
                          </a>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}
