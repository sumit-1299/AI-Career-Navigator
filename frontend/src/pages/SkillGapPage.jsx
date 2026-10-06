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
  GitBranch,
  Compass,
  Layers,
  ArrowRight,
  Check,
  ChevronRight,
  Info,
} from 'lucide-react';

export function SkillGapPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const { targetCareerId, setTargetCareerId } = useAuth();

  const careerIdFromUrl = searchParams.get('career_id');
  const activeCareerId = careerIdFromUrl ? Number(careerIdFromUrl) : targetCareerId;

  const [careers, setCareers] = useState([]);
  const [gapData, setGapData] = useState(null);
  const [roadmapData, setRoadmapData] = useState(null);
  const [pathwaysData, setPathwaysData] = useState(null);
  const [selectedPathwayId, setSelectedPathwayId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState(searchParams.get('tab') || 'gap'); // 'gap' | 'roadmap' | 'pathways'

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

      const [gapRes, roadRes, pathRes] = await Promise.all([
        api.getSkillGap(activeCareerId).catch((e) => {
          console.warn('Skill gap fetch failed', e);
          return null;
        }),
        api.getRoadmap(activeCareerId, hoursPerWeek).catch((e) => {
          console.warn('Roadmap fetch failed', e);
          return null;
        }),
        api.getCareerPathways(activeCareerId, { hoursPerWeek }).catch((e) => {
          console.warn('Pathways fetch failed', e);
          return null;
        }),
      ]);

      setGapData(gapRes);
      setRoadmapData(roadRes);
      setPathwaysData(pathRes);
      if (pathRes?.recommended_pathway_id) {
        setSelectedPathwayId(pathRes.recommended_pathway_id);
      } else if (pathRes?.pathways?.[0]?.id) {
        setSelectedPathwayId(pathRes.pathways[0].id);
      }
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
      const [roadRes, pathRes] = await Promise.all([
        api.getRoadmap(activeCareerId, hrs).catch((e) => null),
        api.getCareerPathways(activeCareerId, { hoursPerWeek: hrs }).catch((e) => null),
      ]);
      if (roadRes) setRoadmapData(roadRes);
      if (pathRes) setPathwaysData(pathRes);
    } catch (e) {
      console.warn('Failed to update study plan roadmap:', e);
    } finally {
      setUpdatingTimeline(false);
    }
  }

  function handleCareerChange(newId) {
    const params = { career_id: newId };
    if (activeTab && activeTab !== 'gap') {
      params.tab = activeTab;
    }
    setSearchParams(params);
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
          <div className="flex flex-wrap gap-2 border-b border-slate-200 pb-2">
            <button
              onClick={() => {
                setActiveTab('gap');
                setSearchParams((prev) => {
                  const p = new URLSearchParams(prev);
                  p.delete('tab');
                  return p;
                });
              }}
              className={`px-4 py-2 rounded-xl text-sm font-semibold transition ${
                activeTab === 'gap'
                  ? 'bg-primary-600 text-white shadow-sm'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
              }`}
            >
              Skill Categorization Matrix
            </button>
            <button
              onClick={() => {
                setActiveTab('roadmap');
                setSearchParams((prev) => {
                  const p = new URLSearchParams(prev);
                  p.set('tab', 'roadmap');
                  return p;
                });
              }}
              className={`px-4 py-2 rounded-xl text-sm font-semibold transition ${
                activeTab === 'roadmap'
                  ? 'bg-primary-600 text-white shadow-sm'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
              }`}
            >
              Sequential Career Roadmap & Certs
            </button>
            <button
              onClick={() => {
                setActiveTab('pathways');
                setSearchParams((prev) => {
                  const p = new URLSearchParams(prev);
                  p.set('tab', 'pathways');
                  return p;
                });
              }}
              className={`px-4 py-2 rounded-xl text-sm font-semibold flex items-center gap-2 transition ${
                activeTab === 'pathways'
                  ? 'bg-primary-600 text-white shadow-sm'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
              }`}
            >
              <GitBranch className="w-4 h-4" />
              Specialization Pathways & Elective Tree
              {pathwaysData?.pathways_count ? (
                <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded-full ${
                  activeTab === 'pathways' ? 'bg-primary-700 text-white' : 'bg-slate-200 text-slate-700'
                }`}>
                  {pathwaysData.pathways_count}
                </span>
              ) : null}
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

          {/* TAB 3: Specialization Pathways & Elective Tree */}
          {activeTab === 'pathways' && (
            <div className="space-y-6 animate-fadeIn">
              {/* Study Intensity Selector Banner */}
              <div className="bg-white rounded-2xl p-5 shadow-sm border border-slate-200 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
                <div className="flex items-center gap-3">
                  <div className="p-2.5 bg-primary-50 text-primary-600 rounded-xl">
                    <Compass className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-slate-900">
                      Elective Specialization Trees & Branches
                    </h3>
                    <p className="text-xs text-slate-500">
                      Explore alternative specialization tracks toward{' '}
                      <span className="font-semibold text-slate-700">
                        {gapData?.career_name || selectedCareer?.career_name || selectedCareer?.title || 'Selected Career'}
                      </span>
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-2 bg-slate-50 p-1.5 rounded-xl border border-slate-200">
                  <span className="text-xs font-semibold text-slate-600 px-2 flex items-center gap-1.5">
                    <Clock className="w-3.5 h-3.5 text-primary-500" />
                    Study Pace:
                  </span>
                  {[5, 10, 20].map((hrs) => (
                    <button
                      key={hrs}
                      onClick={() => handleIntensityChange(hrs)}
                      disabled={updatingTimeline}
                      className={`px-3 py-1 rounded-lg text-xs font-bold transition ${
                        hoursPerWeek === hrs
                          ? 'bg-primary-600 text-white shadow-sm'
                          : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200'
                      } ${updatingTimeline ? 'opacity-60 cursor-not-allowed' : ''}`}
                    >
                      {hrs} hrs/wk
                    </button>
                  ))}
                  {updatingTimeline && <Spinner size="sm" className="ml-1" />}
                </div>
              </div>

              {/* Recommendation Banner */}
              {pathwaysData?.recommended_pathway_name && (
                <div className="bg-gradient-to-r from-emerald-50 via-teal-50/60 to-primary-50/50 rounded-2xl p-6 border border-emerald-200/80 shadow-sm">
                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div className="space-y-1.5">
                      <div className="flex items-center gap-2">
                        <span className="flex items-center gap-1 text-[11px] font-extrabold uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-800 border border-emerald-200">
                          <Sparkles className="w-3.5 h-3.5 text-emerald-600" /> Top Recommended Specialization
                        </span>
                        <span className="text-xs text-emerald-700 font-semibold">
                          Optimal Fit for Your Background
                        </span>
                      </div>
                      <h2 className="text-xl font-extrabold text-slate-900">
                        {pathwaysData.recommended_pathway_name}
                      </h2>
                      <p className="text-sm text-slate-600 max-w-3xl leading-relaxed">
                        {pathwaysData.recommendation_summary}
                      </p>
                    </div>

                    <div className="flex items-center gap-3 shrink-0">
                      <button
                        onClick={() => setSelectedPathwayId(pathwaysData.recommended_pathway_id)}
                        className={`px-4 py-2.5 rounded-xl text-xs font-bold transition flex items-center gap-2 shadow-sm ${
                          selectedPathwayId === pathwaysData.recommended_pathway_id
                            ? 'bg-emerald-700 text-white'
                            : 'bg-white hover:bg-emerald-50 text-emerald-700 border border-emerald-300'
                        }`}
                      >
                        <Check className="w-4 h-4" />
                        {selectedPathwayId === pathwaysData.recommended_pathway_id
                          ? 'Active Inspection'
                          : 'Inspect Recommended Track'}
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {/* Limitation Note (Single Consolidated Track) */}
              {pathwaysData && !pathwaysData.has_multiple_pathways && (
                <div className="bg-amber-50 rounded-2xl p-5 border border-amber-200 flex items-start gap-3.5">
                  <Info className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
                  <div className="text-xs text-amber-900 leading-relaxed">
                    <p className="font-bold text-amber-950 text-sm mb-1">
                      Curriculum Specification Notice
                    </p>
                    <p>
                      {pathwaysData.limitation_note ||
                        'Single consolidated pathway supported by current curriculum: all competencies are mandatory core requirements without elective branching.'}
                    </p>
                    <p className="text-amber-800/80 mt-1">
                      All required competencies for this career track are sequentially coupled without alternate elective sub-specializations.
                    </p>
                  </div>
                </div>
              )}

              {/* Multi-Pathway Comparison Grid */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                      <GitBranch className="w-4 h-4 text-primary-600" />
                      Available Specialization Tracks ({pathwaysData?.pathways?.length || 0})
                    </h3>
                    <p className="text-xs text-slate-500">
                      Select a track below to explore its core vs elective competencies and learning milestones
                    </p>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {pathwaysData?.pathways?.map((pathway) => {
                    const isSelected = (selectedPathwayId || pathwaysData.recommended_pathway_id) === pathway.id;
                    const isRec = pathway.is_recommended;

                    return (
                      <div
                        key={pathway.id}
                        onClick={() => setSelectedPathwayId(pathway.id)}
                        className={`rounded-2xl p-5 border transition-all cursor-pointer flex flex-col justify-between ${
                          isSelected
                            ? 'border-primary-500 ring-2 ring-primary-500/20 bg-primary-50/20 shadow-md'
                            : 'border-slate-200 hover:border-slate-300 bg-white hover:shadow-sm'
                        }`}
                      >
                        <div>
                          <div className="flex items-start justify-between gap-2 mb-2">
                            <span className="text-[10px] font-extrabold px-2 py-0.5 rounded-full bg-slate-100 text-slate-700">
                              Rank #{pathway.rank}
                            </span>
                            <div className="flex items-center gap-1.5">
                              {isRec && (
                                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 border border-emerald-200">
                                  Top Match
                                </span>
                              )}
                              {pathway.is_primary && !isRec && (
                                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200">
                                  Foundational
                                </span>
                              )}
                            </div>
                          </div>

                          <h4 className="font-extrabold text-base text-slate-900 leading-snug mb-1">
                            {pathway.name}
                          </h4>
                          <p className="text-xs font-semibold text-primary-700 mb-2">
                            {pathway.specialization_focus}
                          </p>
                          <p className="text-xs text-slate-500 line-clamp-2 leading-relaxed mb-4">
                            {pathway.description}
                          </p>

                          {/* Progress & Readiness */}
                          <div className="space-y-1.5 mb-4">
                            <div className="flex justify-between text-xs">
                              <span className="text-slate-500 font-medium">Readiness Match</span>
                              <span className="font-bold text-slate-900">{pathway.readiness_percentage}%</span>
                            </div>
                            <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                              <div
                                className={`h-2 rounded-full transition-all duration-300 ${
                                  pathway.readiness_percentage >= 70
                                    ? 'bg-emerald-500'
                                    : pathway.readiness_percentage >= 40
                                    ? 'bg-amber-500'
                                    : 'bg-primary-500'
                                }`}
                                style={{ width: `${Math.min(100, pathway.readiness_percentage)}%` }}
                              />
                            </div>
                          </div>

                          {/* Metric Tags */}
                          <div className="grid grid-cols-2 gap-2 text-[11px] mb-3">
                            <div className="bg-slate-50 p-2 rounded-lg border border-slate-100">
                              <span className="text-slate-400 block text-[10px]">Timeline</span>
                              <span className="font-bold text-slate-800">
                                ~{pathway.estimated_weeks} wks ({pathway.estimated_total_hours}h)
                              </span>
                            </div>
                            <div className="bg-slate-50 p-2 rounded-lg border border-slate-100">
                              <span className="text-slate-400 block text-[10px]">Effort Tier</span>
                              <span className={`font-bold ${
                                pathway.effort_tier === 'LOW'
                                  ? 'text-emerald-700'
                                  : pathway.effort_tier === 'MODERATE'
                                  ? 'text-amber-700'
                                  : 'text-rose-700'
                              }`}>
                                {pathway.effort_tier_label}
                              </span>
                            </div>
                          </div>
                        </div>

                        {/* Card Footer */}
                        <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
                          <span className="text-slate-500">
                            <strong className="text-slate-800">{pathway.matched_skills_count}</strong>/{pathway.total_skills_count} skills met
                          </span>
                          <span className={`font-bold flex items-center gap-1 ${
                            isSelected ? 'text-primary-700' : 'text-slate-400'
                          }`}>
                            {isSelected ? 'Inspecting' : 'Select'} <ChevronRight className="w-3.5 h-3.5" />
                          </span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Overlapping Shared Competencies */}
              {pathwaysData?.overlapping_skills?.length > 0 && (
                <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200">
                  <div className="flex items-center gap-2.5 mb-3">
                    <span className="p-2 bg-blue-50 text-blue-600 rounded-lg">
                      <Layers className="w-5 h-5" />
                    </span>
                    <div>
                      <h3 className="text-base font-bold text-slate-900">
                        Universal Core Competencies ({pathwaysData.overlapping_skills.length})
                      </h3>
                      <p className="text-xs text-slate-500">
                        Foundational competencies shared across all specialization pathways in this career
                      </p>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                    {pathwaysData.overlapping_skills.map((skill, idx) => (
                      <div
                        key={idx}
                        className="p-3.5 rounded-xl border border-blue-100 bg-blue-50/30 flex items-center justify-between"
                      >
                        <div>
                          <h4 className="font-bold text-sm text-slate-900">{skill.skill_name}</h4>
                          <span className="text-[11px] text-slate-500">
                            Required Level: <strong>{skill.required_level}/5</strong> · Imp: <strong>{skill.importance}/5</strong>
                          </span>
                        </div>
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                          skill.status === 'MATCHED' || skill.status === 'EXCEEDS'
                            ? 'bg-emerald-100 text-emerald-800'
                            : skill.status === 'WEAK'
                            ? 'bg-amber-100 text-amber-800'
                            : 'bg-rose-100 text-rose-800'
                        }`}>
                          {skill.status}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Active Pathway Detailed Specialization Tree */}
              {(() => {
                const activeP =
                  pathwaysData?.pathways?.find((p) => p.id === selectedPathwayId) ||
                  pathwaysData?.pathways?.[0];

                if (!activeP) return null;

                return (
                  <div className="bg-white rounded-2xl p-6 md:p-8 shadow-sm border border-slate-200 space-y-6">
                    {/* Header */}
                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-100">
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-xs font-bold px-2.5 py-0.5 rounded-full bg-primary-100 text-primary-800">
                            Active Specialization Inspection
                          </span>
                          <span className="text-xs text-slate-400">
                            Rank #{activeP.rank}
                          </span>
                        </div>
                        <h3 className="text-xl font-extrabold text-slate-900">
                          {activeP.name}
                        </h3>
                        <p className="text-xs text-slate-500 mt-1 max-w-2xl leading-relaxed">
                          {activeP.description}
                        </p>
                      </div>

                      <div className="flex flex-wrap items-center gap-3">
                        <div className="px-3 py-2 bg-slate-50 rounded-xl border border-slate-200 text-right">
                          <span className="text-[10px] text-slate-400 block font-medium">Readiness Match</span>
                          <span className="text-lg font-black text-slate-900">{activeP.readiness_percentage}%</span>
                        </div>
                        <div className="px-3 py-2 bg-slate-50 rounded-xl border border-slate-200 text-right">
                          <span className="text-[10px] text-slate-400 block font-medium">Est. Completion</span>
                          <span className="text-lg font-black text-primary-700">~{activeP.estimated_weeks} wks</span>
                        </div>
                      </div>
                    </div>

                    {/* Recommendation Reason Callout */}
                    {activeP.recommendation_reason && (
                      <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-700 leading-relaxed flex items-start gap-3">
                        <Info className="w-4 h-4 text-primary-600 shrink-0 mt-0.5" />
                        <div>
                          <strong className="text-slate-900 block font-semibold mb-0.5">Specialization Suitability Assessment:</strong>
                          {activeP.recommendation_reason}
                        </div>
                      </div>
                    )}

                    {/* Skills Breakdown: Core vs Electives */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                      {/* Left: Core Mandatory Competencies */}
                      <div className="space-y-3">
                        <div className="flex items-center justify-between">
                          <h4 className="text-sm font-extrabold text-slate-900 uppercase tracking-wider flex items-center gap-2">
                            <span className="w-2 h-2 rounded-full bg-primary-600" />
                            Core Mandatory Competencies ({activeP.core_skills?.length || 0})
                          </h4>
                          <span className="text-[11px] text-slate-400">Mandatory for this track</span>
                        </div>

                        {activeP.core_skills?.map((skill, idx) => (
                          <div
                            key={idx}
                            className={`p-4 rounded-xl border flex flex-col justify-between gap-2 ${
                              skill.status === 'MATCHED' || skill.status === 'EXCEEDS'
                                ? 'bg-emerald-50/40 border-emerald-200'
                                : skill.status === 'WEAK'
                                ? 'bg-amber-50/40 border-amber-200'
                                : 'bg-rose-50/40 border-rose-200'
                            }`}
                          >
                            <div className="flex items-start justify-between gap-2">
                              <div>
                                <h5 className="font-bold text-sm text-slate-900">{skill.skill_name}</h5>
                                <span className="text-[11px] text-slate-500">
                                  Required Level: <strong>{skill.required_level}/5</strong> · Imp: <strong>{skill.importance}/5</strong>
                                </span>
                              </div>
                              <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                                skill.status === 'MATCHED' || skill.status === 'EXCEEDS'
                                  ? 'bg-emerald-100 text-emerald-800'
                                  : skill.status === 'WEAK'
                                  ? 'bg-amber-100 text-amber-800'
                                  : 'bg-rose-100 text-rose-800'
                              }`}>
                                {skill.status}
                              </span>
                            </div>

                            <div className="flex items-center justify-between text-xs pt-1 border-t border-slate-200/50">
                              <span className="text-slate-600">
                                Current: <strong>{skill.raw_proficiency}/10</strong> ({skill.current_proficiency}/5)
                              </span>
                              {skill.prerequisites?.length > 0 && (
                                <span className={`text-[10px] font-semibold ${
                                  skill.prerequisites_satisfied ? 'text-emerald-700' : 'text-amber-700'
                                }`}>
                                  {skill.prerequisites_satisfied
                                    ? `✓ Prereqs met: ${skill.prerequisites.join(', ')}`
                                    : `⚠ Missing prereq: ${skill.missing_prerequisites.join(', ')}`}
                                </span>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>

                      {/* Right: Specialization / Elective Competencies */}
                      <div className="space-y-3">
                        <div className="flex items-center justify-between">
                          <h4 className="text-sm font-extrabold text-slate-900 uppercase tracking-wider flex items-center gap-2">
                            <span className="w-2 h-2 rounded-full bg-teal-600" />
                            Specialization Electives ({activeP.elective_skills?.length || 0})
                          </h4>
                          <span className="text-[11px] text-slate-400">Track-specific competencies</span>
                        </div>

                        {activeP.elective_skills?.length === 0 ? (
                          <div className="p-6 rounded-xl border border-dashed border-slate-200 text-center text-xs text-slate-400">
                            No elective competencies required; all requirements are part of the core curriculum.
                          </div>
                        ) : (
                          activeP.elective_skills?.map((skill, idx) => (
                            <div
                              key={idx}
                              className={`p-4 rounded-xl border flex flex-col justify-between gap-2 ${
                                skill.status === 'MATCHED' || skill.status === 'EXCEEDS'
                                  ? 'bg-emerald-50/40 border-emerald-200'
                                  : skill.status === 'WEAK'
                                  ? 'bg-amber-50/40 border-amber-200'
                                  : 'bg-rose-50/40 border-rose-200'
                              }`}
                            >
                              <div className="flex items-start justify-between gap-2">
                                <div>
                                  <div className="flex items-center gap-1.5">
                                    <h5 className="font-bold text-sm text-slate-900">{skill.skill_name}</h5>
                                    <span className="text-[10px] font-semibold px-1.5 py-0.2 rounded bg-teal-100 text-teal-800">
                                      Specialization
                                    </span>
                                  </div>
                                  <span className="text-[11px] text-slate-500">
                                    Required Level: <strong>{skill.required_level}/5</strong> · Imp: <strong>{skill.importance}/5</strong>
                                  </span>
                                </div>
                                <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                                  skill.status === 'MATCHED' || skill.status === 'EXCEEDS'
                                    ? 'bg-emerald-100 text-emerald-800'
                                    : skill.status === 'WEAK'
                                    ? 'bg-amber-100 text-amber-800'
                                    : 'bg-rose-100 text-rose-800'
                                }`}>
                                  {skill.status}
                                </span>
                              </div>

                              <div className="flex items-center justify-between text-xs pt-1 border-t border-slate-200/50">
                                <span className="text-slate-600">
                                  Current: <strong>{skill.raw_proficiency}/10</strong> ({skill.current_proficiency}/5)
                                </span>
                                {skill.prerequisites?.length > 0 && (
                                  <span className={`text-[10px] font-semibold ${
                                    skill.prerequisites_satisfied ? 'text-emerald-700' : 'text-amber-700'
                                  }`}>
                                    {skill.prerequisites_satisfied
                                      ? `✓ Prereqs met: ${skill.prerequisites.join(', ')}`
                                      : `⚠ Missing prereq: ${skill.missing_prerequisites.join(', ')}`}
                                  </span>
                                )}
                              </div>
                            </div>
                          ))
                        )}
                      </div>
                    </div>

                    {/* Pathway Weekly Milestones */}
                    {activeP.study_milestones?.length > 0 && (
                      <div className="pt-4 border-t border-slate-100 space-y-3">
                        <div className="flex items-center justify-between">
                          <h4 className="text-sm font-extrabold text-slate-900 flex items-center gap-2">
                            <Calendar className="w-4 h-4 text-primary-600" />
                            Weekly Progression Milestones for {activeP.name} ({hoursPerWeek} hrs/week)
                          </h4>
                          <span className="text-xs text-slate-500 font-medium">
                            Target Date: <strong>{activeP.estimated_completion_date || 'N/A'}</strong>
                          </span>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                          {activeP.study_milestones.map((m, idx) => (
                            <div
                              key={idx}
                              className="p-3.5 rounded-xl border border-slate-200 bg-slate-50/50 flex flex-col justify-between"
                            >
                              <div className="flex items-center justify-between mb-1.5">
                                <span className="text-xs font-bold text-primary-700">Week {m.week_number}</span>
                                <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-slate-200 text-slate-700">
                                  {m.hours_allocated} hrs
                                </span>
                              </div>
                              <h5 className="font-bold text-xs text-slate-900 mb-1">{m.milestone_title || m.skill_name}</h5>
                              <p className="text-[11px] text-slate-500 line-clamp-2">
                                {m.focus_area || m.recommended_action || 'Complete scheduled course modules and exercises.'}
                              </p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                );
              })()}
            </div>
          )}
        </>
      )}
    </div>
  );
}
