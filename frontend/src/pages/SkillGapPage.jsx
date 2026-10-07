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
  RotateCcw,
  TrendingUp,
  Zap,
  Sliders,
  FolderGit2,
  Code2,
  CheckSquare,
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
  const [activeTab, setActiveTab] = useState(searchParams.get('tab') || 'gap'); // 'gap' | 'roadmap' | 'pathways' | 'simulator' | 'roi'

  // Module 8.3: Study intensity (5 | 10 | 20 hours/week)
  const [hoursPerWeek, setHoursPerWeek] = useState(10);
  const [updatingTimeline, setUpdatingTimeline] = useState(false);

  // Module 9.4: "What If?" Interactive Skill Simulator State
  const [simulatorSkill, setSimulatorSkill] = useState('');
  const [simulatorLevel, setSimulatorLevel] = useState(3);
  const [simulationResult, setSimulationResult] = useState(null);
  const [simulating, setSimulating] = useState(false);
  const [simError, setSimError] = useState(null);

  // Module 11.1: Explainable Skill ROI & Counterfactual State
  const [roiData, setRoiData] = useState(null);
  const [counterfactualResult, setCounterfactualResult] = useState(null);
  const [runningCounterfactual, setRunningCounterfactual] = useState(false);

  // Module 11.2: Actionable Portfolio & Capstone Projects State
  const [portfolioData, setPortfolioData] = useState(null);
  const [projectDifficultyFilter, setProjectDifficultyFilter] = useState('ALL');

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

      const [gapRes, roadRes, pathRes, roiRes, portfolioRes] = await Promise.all([
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
        api.getCareerSkillRoi(activeCareerId, { hoursPerWeek }).catch((e) => {
          console.warn('Skill ROI fetch failed', e);
          return null;
        }),
        api.getPortfolioProjectRecommendations(activeCareerId).catch((e) => {
          console.warn('Portfolio recommendations fetch failed', e);
          return null;
        }),
      ]);

      setGapData(gapRes);
      setRoadmapData(roadRes);
      setPathwaysData(pathRes);
      setRoiData(roiRes);
      setPortfolioData(portfolioRes);
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
      const [roadRes, pathRes, roiRes] = await Promise.all([
        api.getRoadmap(activeCareerId, hrs).catch((e) => null),
        api.getCareerPathways(activeCareerId, { hoursPerWeek: hrs }).catch((e) => null),
        api.getCareerSkillRoi(activeCareerId, { hoursPerWeek: hrs }).catch((e) => null),
      ]);
      if (roadRes) setRoadmapData(roadRes);
      if (pathRes) setPathwaysData(pathRes);
      if (roiRes) setRoiData(roiRes);
    } catch (e) {
      console.warn('Failed to update study plan roadmap:', e);
    } finally {
      setUpdatingTimeline(false);
    }
  }

  async function handleRunCounterfactual(skillName, targetLevel = null) {
    setRunningCounterfactual(true);
    try {
      const res = await api.runCounterfactualAnalysis(activeCareerId, {
        skillName,
        targetLevel,
        hoursPerWeek,
      });
      setCounterfactualResult(res);
    } catch (err) {
      console.warn('Counterfactual failed', err);
    } finally {
      setRunningCounterfactual(false);
    }
  }


  function handleCareerChange(newId) {
    const params = { career_id: newId };
    if (activeTab && activeTab !== 'gap') {
      params.tab = activeTab;
    }
    setSearchParams(params);
    setTargetCareerId(Number(newId));
    setSimulationResult(null);
    setSimError(null);
  }

  async function handleRunSimulation(targetSkillName = null, targetLevel = null) {
    const sName = targetSkillName || simulatorSkill;
    const sLevel = targetLevel !== null ? targetLevel : simulatorLevel;
    if (!sName) {
      setSimError('Please select or specify a skill to simulate.');
      return;
    }
    setSimulating(true);
    setSimError(null);
    try {
      const res = await api.simulateSkillImpact(activeCareerId, {
        skillName: sName,
        simulatedLevel: sLevel,
        hoursPerWeek: hoursPerWeek,
      });
      if (res?.simulation) {
        setSimulationResult(res.simulation);
      } else if (res?.error) {
        setSimError(res.message || 'Simulation could not be evaluated.');
      } else {
        setSimError('Unexpected simulation response.');
      }
    } catch (err) {
      setSimError(err.message || 'Simulation request failed.');
    } finally {
      setSimulating(false);
    }
  }

  function handleResetSimulation() {
    setSimulationResult(null);
    setSimError(null);
  }

  function handleQuickSimulate(skillName, defaultLevel = 3) {
    setSimulatorSkill(skillName);
    setSimulatorLevel(defaultLevel);
    setActiveTab('simulator');
    setSearchParams((prev) => {
      const p = new URLSearchParams(prev);
      p.set('tab', 'simulator');
      return p;
    });
    handleRunSimulation(skillName, defaultLevel);
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
            <button
              onClick={() => {
                setActiveTab('simulator');
                setSearchParams((prev) => {
                  const p = new URLSearchParams(prev);
                  p.set('tab', 'simulator');
                  return p;
                });
              }}
              className={`px-4 py-2 rounded-xl text-sm font-semibold flex items-center gap-2 transition ${
                activeTab === 'simulator'
                  ? 'bg-primary-600 text-white shadow-sm'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
              }`}
            >
              <Sparkles className="w-4 h-4 text-amber-400" />
              "What If?" Skill Simulator
              {simulationResult?.impact?.readiness_gain > 0 ? (
                <span className="text-[10px] font-bold px-1.5 py-0.5 rounded-full bg-emerald-500 text-white">
                  +{simulationResult.impact.readiness_gain}%
                </span>
              ) : null}
            </button>
            <button
              onClick={() => {
                setActiveTab('roi');
                setSearchParams((prev) => {
                  const p = new URLSearchParams(prev);
                  p.set('tab', 'roi');
                  return p;
                });
              }}
              className={`px-4 py-2 rounded-xl text-sm font-semibold flex items-center gap-2 transition ${
                activeTab === 'roi'
                  ? 'bg-primary-600 text-white shadow-sm'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
              }`}
            >
              <TrendingUp className="w-4 h-4 text-emerald-400" />
              Explainable Skill ROI
              {roiData?.quickest_win?.readiness_gain > 0 ? (
                <span className="text-[10px] font-bold px-1.5 py-0.5 rounded-full bg-emerald-500 text-white">
                  Top ROI: +{roiData.quickest_win.readiness_gain}%
                </span>
              ) : null}
            </button>
            <button
              onClick={() => {
                setActiveTab('projects');
                setSearchParams((prev) => {
                  const p = new URLSearchParams(prev);
                  p.set('tab', 'projects');
                  return p;
                });
              }}
              className={`px-4 py-2 rounded-xl text-sm font-semibold flex items-center gap-2 transition ${
                activeTab === 'projects'
                  ? 'bg-primary-600 text-white shadow-sm'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
              }`}
            >
              <FolderGit2 className="w-4 h-4 text-primary-400" />
              Capstone & Portfolio Projects
              {portfolioData?.total_projects_count ? (
                <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded-full ${
                  activeTab === 'projects' ? 'bg-primary-700 text-white' : 'bg-slate-200 text-slate-700'
                }`}>
                  {portfolioData.total_projects_count}
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

                          <div className="mt-3 flex items-center justify-between gap-2 border-t border-rose-100 pt-2.5">
                            <Link
                              to={`/learning?skill_id=${cId}`}
                              className="inline-flex items-center gap-1 text-xs font-semibold text-rose-700 hover:text-rose-800 hover:underline"
                            >
                              <BookOpen className="w-3.5 h-3.5" />
                              <span>Resources</span>
                            </Link>
                            <button
                              type="button"
                              onClick={() => handleQuickSimulate(sName, Math.min(5, Math.ceil(reqLvl / 2) || 3))}
                              className="inline-flex items-center gap-1 text-[11px] font-semibold text-primary-700 hover:text-primary-800 bg-white hover:bg-primary-50 border border-primary-200 px-2 py-1 rounded-lg transition"
                              title={`Simulate learning ${sName}`}
                            >
                              <Sparkles className="w-3 h-3 text-amber-500" />
                              <span>What-If →</span>
                            </button>
                          </div>
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

                          <div className="mt-3 flex items-center justify-between gap-2 border-t border-amber-100 pt-2.5">
                            <Link
                              to={`/learning?skill_id=${cId}`}
                              className="inline-flex items-center gap-1 text-xs font-semibold text-amber-800 hover:underline"
                            >
                              <BookOpen className="w-3.5 h-3.5" />
                              <span>Resources</span>
                            </Link>
                            <button
                              type="button"
                              onClick={() => handleQuickSimulate(sName, Math.min(5, Math.ceil(reqLvl / 2) || 4))}
                              className="inline-flex items-center gap-1 text-[11px] font-semibold text-primary-700 hover:text-primary-800 bg-white hover:bg-primary-50 border border-primary-200 px-2 py-1 rounded-lg transition shadow-xs"
                              title={`Simulate upgrading ${sName}`}
                            >
                              <Sparkles className="w-3 h-3 text-amber-500" />
                              <span>What-If →</span>
                            </button>
                          </div>
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

          {/* TAB 4: "What If?" Interactive Skill Simulator */}
          {activeTab === 'simulator' && (
            <div className="space-y-6">
              {/* Simulator Header & Safety Callout */}
              <div className="bg-gradient-to-r from-slate-900 to-indigo-950 rounded-2xl p-6 md:p-8 text-white shadow-md relative overflow-hidden">
                <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 relative z-10">
                  <div className="max-w-2xl">
                    <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/20 text-indigo-200 border border-indigo-400/30 text-xs font-semibold mb-3">
                      <Sparkles className="w-3.5 h-3.5 text-amber-300" />
                      <span>Phase 9.4 • Interactive Career Simulator</span>
                    </div>
                    <h2 className="text-2xl md:text-3xl font-extrabold tracking-tight">
                      "What If I Learn Skill X?"
                    </h2>
                    <p className="text-slate-300 text-sm mt-1.5 leading-relaxed">
                      Model the hypothetical impact of acquiring a missing skill or improving your proficiency in-memory.
                      Evaluate real-time career readiness gain, study timeline compression, and specialization pathway advancement.
                    </p>
                  </div>
                  <div className="flex flex-col items-start md:items-end gap-2 text-xs">
                    <div className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-500/20 border border-emerald-400/40 text-emerald-300 font-medium">
                      <Check className="w-4 h-4 text-emerald-400" />
                      <span>100% In-Memory Simulation</span>
                    </div>
                    <span className="text-slate-400 text-[11px]">
                      Your permanent student profile remains completely unmodified.
                    </span>
                  </div>
                </div>
              </div>

              {/* Simulation Controls Card */}
              <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200 space-y-6">
                <div className="flex items-center justify-between pb-4 border-b border-slate-100">
                  <div className="flex items-center gap-2.5">
                    <span className="p-2 bg-indigo-50 text-indigo-600 rounded-lg">
                      <Sliders className="w-5 h-5" />
                    </span>
                    <div>
                      <h3 className="text-base font-bold text-slate-900">
                        Simulation Parameters
                      </h3>
                      <p className="text-xs text-slate-500">
                        Targeting career: <strong className="text-slate-700">{selectedCareer?.title || selectedCareer?.career_name || 'Active Career'}</strong>
                      </p>
                    </div>
                  </div>

                  {simulationResult && (
                    <button
                      type="button"
                      onClick={handleResetSimulation}
                      className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-600 hover:text-slate-900 bg-slate-100 hover:bg-slate-200 px-3 py-1.5 rounded-lg transition"
                    >
                      <RotateCcw className="w-3.5 h-3.5" />
                      <span>Reset Simulation</span>
                    </button>
                  )}
                </div>

                {simError && <Alert type="error" message={simError} />}

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                  {/* Skill Picker */}
                  <div className="space-y-2">
                    <label className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center justify-between">
                      <span>1. Select Candidate Skill</span>
                      {simulatorSkill && (
                        <span className="text-[11px] font-medium text-primary-600">Selected</span>
                      )}
                    </label>
                    <select
                      value={simulatorSkill}
                      onChange={(e) => setSimulatorSkill(e.target.value)}
                      className="w-full bg-slate-50 border border-slate-300 text-slate-900 text-sm rounded-xl px-3.5 py-2.5 font-medium transition focus:ring-primary-500 focus:border-primary-500"
                    >
                      <option value="">-- Choose a skill to simulate --</option>
                      {missingSkills?.length > 0 && (
                        <optgroup label="⚠️ Missing Skills (High Impact)">
                          {missingSkills.map((s, idx) => (
                            <option key={`m-${idx}`} value={s.skill_name || s.name}>
                              {s.skill_name || s.name} (Missing • Req: Lvl {s.required_level || 5}/10)
                            </option>
                          ))}
                        </optgroup>
                      )}
                      {weakSkills?.length > 0 && (
                        <optgroup label="⚡ Weak / Developing Skills">
                          {weakSkills.map((s, idx) => (
                            <option key={`w-${idx}`} value={s.skill_name || s.name}>
                              {s.skill_name || s.name} (Developing • Current: {s.current_proficiency || 0}/10)
                            </option>
                          ))}
                        </optgroup>
                      )}
                      {matchedSkills?.length > 0 && (
                        <optgroup label="✓ Matched Competencies">
                          {matchedSkills.map((s, idx) => (
                            <option key={`mt-${idx}`} value={s.skill_name || s.name}>
                              {s.skill_name || s.name} (Satisfied)
                            </option>
                          ))}
                        </optgroup>
                      )}
                    </select>

                    <div className="pt-1">
                      <input
                        type="text"
                        placeholder="Or type any custom or canonical skill name..."
                        value={simulatorSkill}
                        onChange={(e) => setSimulatorSkill(e.target.value)}
                        className="w-full bg-slate-50 border border-slate-200 text-slate-800 text-xs rounded-lg px-3 py-2 transition focus:ring-primary-500 focus:border-primary-500"
                      />
                    </div>
                  </div>

                  {/* Target Proficiency Selector */}
                  <div className="space-y-2">
                    <label className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center justify-between">
                      <span>2. Simulated Mastery Level</span>
                      <span className="text-xs font-extrabold text-primary-700">
                        Level {simulatorLevel}/5 ({simulatorLevel * 2}/10)
                      </span>
                    </label>
                    <div className="grid grid-cols-5 gap-1.5">
                      {[1, 2, 3, 4, 5].map((lvl) => {
                        const labels = ['Beginner', 'Elementary', 'Intermediate', 'Advanced', 'Expert'];
                        const isSelected = Number(simulatorLevel) === lvl;
                        return (
                          <button
                            key={lvl}
                            type="button"
                            onClick={() => setSimulatorLevel(lvl)}
                            className={`p-2.5 rounded-xl border flex flex-col items-center justify-center text-center transition ${
                              isSelected
                                ? 'bg-primary-50 border-primary-500 text-primary-900 shadow-xs ring-1 ring-primary-500'
                                : 'bg-slate-50 border-slate-200 text-slate-600 hover:bg-slate-100 hover:border-slate-300'
                            }`}
                          >
                            <span className="text-sm font-extrabold">{lvl}</span>
                            <span className="text-[9px] font-medium leading-tight mt-0.5">{labels[lvl - 1]}</span>
                          </button>
                        );
                      })}
                    </div>
                    <p className="text-[11px] text-slate-400">
                      Standard industry career requirement levels range from 1 (fundamental) to 5 (lead/expert).
                    </p>
                  </div>

                  {/* Study Intensity & Trigger */}
                  <div className="space-y-2">
                    <label className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center justify-between">
                      <span>3. Weekly Study Intensity</span>
                      <span className="text-xs font-extrabold text-primary-700">{hoursPerWeek} hrs/week</span>
                    </label>
                    <div className="grid grid-cols-3 gap-1.5">
                      {[5, 10, 20].map((hrs) => (
                        <button
                          key={hrs}
                          type="button"
                          onClick={() => handleIntensityChange(hrs)}
                          className={`p-2.5 rounded-xl border text-center transition ${
                            hoursPerWeek === hrs
                              ? 'bg-primary-50 border-primary-500 text-primary-900 shadow-xs font-bold'
                              : 'bg-slate-50 border-slate-200 text-slate-600 hover:bg-slate-100 text-xs font-medium'
                          }`}
                        >
                          <div className="text-xs font-bold">{hrs}h / wk</div>
                          <div className="text-[9px] text-slate-400">
                            {hrs === 5 ? 'Light' : hrs === 10 ? 'Balanced' : 'Intensive'}
                          </div>
                        </button>
                      ))}
                    </div>

                    <div className="pt-2">
                      <button
                        type="button"
                        onClick={() => handleRunSimulation()}
                        disabled={simulating || !simulatorSkill}
                        className="w-full flex items-center justify-center gap-2 bg-primary-600 hover:bg-primary-700 disabled:opacity-50 text-white text-sm font-bold py-2.5 px-4 rounded-xl shadow-sm transition"
                      >
                        {simulating ? (
                          <>
                            <Spinner size="sm" />
                            <span>Computing In-Memory Delta...</span>
                          </>
                        ) : (
                          <>
                            <Sparkles className="w-4 h-4 text-amber-300" />
                            <span>Simulate Skill Impact</span>
                          </>
                        )}
                      </button>
                    </div>
                  </div>
                </div>
              </div>

              {/* Simulation Result Presentation */}
              {simulationResult ? (
                <div className="space-y-6">
                  {/* Executive Narrative Callout */}
                  <div className="bg-indigo-50/70 border border-indigo-200 rounded-2xl p-6 shadow-xs">
                    <div className="flex items-start gap-3">
                      <div className="p-2.5 bg-indigo-600 text-white rounded-xl shadow-xs shrink-0">
                        <TrendingUp className="w-5 h-5" />
                      </div>
                      <div className="space-y-2">
                        <div className="flex flex-wrap items-center gap-2">
                          <h4 className="text-base font-extrabold text-indigo-950">
                            Simulation Outcome: {simulationResult.skill.name} at Level {simulationResult.skill.simulated_level}/5
                          </h4>
                          <span className={`text-[11px] font-bold px-2 py-0.5 rounded-full ${
                            simulationResult.skill.is_required_by_career
                              ? 'bg-indigo-100 text-indigo-800 border border-indigo-200'
                              : 'bg-slate-100 text-slate-600 border border-slate-200'
                          }`}>
                            {simulationResult.skill.is_required_by_career ? 'Career Competency' : 'Elective / Non-Core'}
                          </span>
                          {simulationResult.impact.readiness_gain > 0 && (
                            <span className="text-[11px] font-extrabold px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-800 border border-emerald-300">
                              +{simulationResult.impact.readiness_gain}% Overall Readiness Gain
                            </span>
                          )}
                        </div>
                        <p className="text-sm text-indigo-900/90 leading-relaxed font-medium">
                          {simulationResult.explanation}
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* 3 Metric Differential Cards */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {/* Readiness Differential */}
                    <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-xs flex flex-col justify-between">
                      <div>
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Readiness Score</span>
                          <span className={`text-xs font-extrabold px-2 py-0.5 rounded-full ${
                            simulationResult.impact.readiness_gain > 0
                              ? 'bg-emerald-100 text-emerald-800'
                              : 'bg-slate-100 text-slate-600'
                          }`}>
                            +{simulationResult.impact.readiness_gain}% Gain
                          </span>
                        </div>
                        <div className="flex items-baseline gap-2 mt-1">
                          <span className="text-2xl font-extrabold text-slate-400 line-through">
                            {simulationResult.current_state.readiness_percentage}%
                          </span>
                          <ArrowRight className="w-4 h-4 text-slate-400" />
                          <span className="text-3xl font-black text-slate-900">
                            {simulationResult.simulated_state.readiness_percentage}%
                          </span>
                        </div>
                      </div>
                      <div className="mt-4 pt-3 border-t border-slate-100 text-[11px] text-slate-500 flex justify-between">
                        <span>Matched: {simulationResult.simulated_state.matched_skills_count}</span>
                        <span>Developing: {simulationResult.simulated_state.weak_skills_count}</span>
                      </div>
                    </div>

                    {/* Missing Skills Differential */}
                    <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-xs flex flex-col justify-between">
                      <div>
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Missing Competencies</span>
                          <span className="text-xs font-extrabold px-2 py-0.5 rounded-full bg-blue-100 text-blue-800">
                            {simulationResult.current_state.missing_skills_count - simulationResult.simulated_state.missing_skills_count > 0
                              ? `-${simulationResult.current_state.missing_skills_count - simulationResult.simulated_state.missing_skills_count} Missing`
                              : 'No Count Delta'}
                          </span>
                        </div>
                        <div className="flex items-baseline gap-2 mt-1">
                          <span className="text-2xl font-extrabold text-slate-400">
                            {simulationResult.current_state.missing_skills_count}
                          </span>
                          <ArrowRight className="w-4 h-4 text-slate-400" />
                          <span className="text-3xl font-black text-slate-900">
                            {simulationResult.simulated_state.missing_skills_count}
                          </span>
                          <span className="text-xs text-slate-400 font-medium">remaining</span>
                        </div>
                      </div>
                      <div className="mt-4 pt-3 border-t border-slate-100 text-[11px] text-slate-500">
                        {simulationResult.impact.newly_satisfied_skills.length > 0
                          ? `${simulationResult.impact.newly_satisfied_skills.length} competency newly satisfied`
                          : 'No new competencies fully satisfied'}
                      </div>
                    </div>

                    {/* Study Timeline Differential */}
                    <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-xs flex flex-col justify-between">
                      <div>
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Estimated Timeline</span>
                          <span className={`text-xs font-extrabold px-2 py-0.5 rounded-full ${
                            simulationResult.impact.weeks_saved > 0
                              ? 'bg-emerald-100 text-emerald-800'
                              : 'bg-slate-100 text-slate-600'
                          }`}>
                            {simulationResult.impact.weeks_saved > 0
                              ? `-${simulationResult.impact.weeks_saved} Weeks Saved`
                              : 'Timeline Unchanged'}
                          </span>
                        </div>
                        <div className="flex items-baseline gap-2 mt-1">
                          <span className="text-2xl font-extrabold text-slate-400 line-through">
                            {simulationResult.current_state.estimated_weeks}w
                          </span>
                          <ArrowRight className="w-4 h-4 text-slate-400" />
                          <span className="text-3xl font-black text-slate-900">
                            {simulationResult.simulated_state.estimated_weeks}w
                          </span>
                          <span className="text-xs text-slate-400 font-medium">
                            ({simulationResult.simulated_state.estimated_total_hours} hrs)
                          </span>
                        </div>
                      </div>
                      <div className="mt-4 pt-3 border-t border-slate-100 text-[11px] text-slate-500 flex justify-between">
                        <span>Pace: {hoursPerWeek} hrs/week</span>
                        <span>Saved: {simulationResult.impact.hours_saved} study hrs</span>
                      </div>
                    </div>
                  </div>

                  {/* Newly Satisfied Skills & Cross-Pathway Impacts */}
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Newly Satisfied Competencies */}
                    <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-xs space-y-4">
                      <div className="flex items-center gap-2 text-emerald-700">
                        <CheckCircle2 className="w-5 h-5" />
                        <h4 className="text-sm font-bold uppercase tracking-wider">Newly Satisfied Competencies</h4>
                      </div>

                      {simulationResult.impact.newly_satisfied_skills.length === 0 ? (
                        <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-500">
                          {simulationResult.skill.is_required_by_career
                            ? 'This simulation narrowed your gap or demonstrated mastery, but did not transition any skill from missing/weak to fully matched.'
                            : 'This skill is not a required competency for this role, so no career requirements changed status.'}
                        </div>
                      ) : (
                        <div className="space-y-2.5">
                          {simulationResult.impact.newly_satisfied_skills.map((s, idx) => (
                            <div
                              key={idx}
                              className="p-3.5 rounded-xl border border-emerald-200 bg-emerald-50/50 flex items-center justify-between"
                            >
                              <div className="flex items-center gap-2">
                                <span className="p-1 rounded-full bg-emerald-100 text-emerald-700">
                                  <Check className="w-3.5 h-3.5" />
                                </span>
                                <div>
                                  <span className="font-bold text-sm text-slate-900">{s.skill_name}</span>
                                  <p className="text-[11px] text-slate-500">
                                    Promoted from <span className="font-semibold">{s.previous_status}</span> to <span className="font-semibold text-emerald-700">{s.simulated_status}</span>
                                  </p>
                                </div>
                              </div>
                              <span className="text-[10px] font-extrabold px-2 py-0.5 rounded-full bg-emerald-200 text-emerald-800">
                                Matched
                              </span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* Module 9.3 Specialization Track Impacts */}
                    <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-xs space-y-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2 text-primary-700">
                          <GitBranch className="w-5 h-5" />
                          <h4 className="text-sm font-bold uppercase tracking-wider">Specialization Track Impacts</h4>
                        </div>
                        <span className="text-[11px] text-slate-400">Module 9.3 Pathways</span>
                      </div>

                      {(!simulationResult.impact.pathway_impacts || simulationResult.impact.pathway_impacts.length === 0) ? (
                        <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-500">
                          No distinct specialization tracks configured for this career track.
                        </div>
                      ) : (
                        <div className="space-y-2.5 max-h-[320px] overflow-y-auto pr-1">
                          {simulationResult.impact.pathway_impacts.map((p, idx) => (
                            <div
                              key={idx}
                              className={`p-3.5 rounded-xl border transition ${
                                p.readiness_gain > 0
                                  ? 'border-indigo-200 bg-indigo-50/30'
                                  : 'border-slate-200 bg-slate-50/50'
                              }`}
                            >
                              <div className="flex items-start justify-between gap-2 mb-1">
                                <div>
                                  <h5 className="font-bold text-xs text-slate-900">{p.pathway_name}</h5>
                                  <p className="text-[10px] text-slate-500">{p.specialization_focus}</p>
                                </div>
                                <div className="text-right">
                                  <span className={`text-[10px] font-extrabold px-2 py-0.5 rounded-full ${
                                    p.readiness_gain > 0
                                      ? 'bg-emerald-100 text-emerald-800'
                                      : 'bg-slate-100 text-slate-600'
                                  }`}>
                                    +{p.readiness_gain}%
                                  </span>
                                </div>
                              </div>
                              <div className="flex items-center justify-between text-[11px] text-slate-600 pt-1.5 border-t border-slate-200/50">
                                <span>
                                  Readiness: <strong>{p.current_readiness}%</strong> ➔ <strong>{p.simulated_readiness}%</strong>
                                </span>
                                <span>
                                  {p.weeks_saved > 0 ? `Saved ${p.weeks_saved} wks` : `${p.simulated_weeks} wks`} ({p.simulated_effort_tier})
                                </span>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Remaining Gaps After Simulation */}
                  {simulationResult.impact.remaining_gaps?.length > 0 && (
                    <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-xs space-y-3">
                      <div className="flex items-center justify-between">
                        <h4 className="text-sm font-extrabold text-slate-900 flex items-center gap-2">
                          <Layers className="w-4 h-4 text-slate-600" />
                          Remaining Competencies to Bridge ({simulationResult.impact.remaining_gaps.length})
                        </h4>
                        <span className="text-xs text-slate-500">
                          Sorted by priority for {simulationResult.career_title}
                        </span>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                        {simulationResult.impact.remaining_gaps.map((gap, idx) => (
                          <div
                            key={idx}
                            className="p-3.5 rounded-xl border border-slate-200 bg-slate-50/50 flex flex-col justify-between"
                          >
                            <div className="flex items-start justify-between gap-1 mb-1">
                              <span className="font-bold text-xs text-slate-900">{gap.skill_name}</span>
                              <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded ${
                                gap.status === 'MISSING' ? 'bg-rose-100 text-rose-700' : 'bg-amber-100 text-amber-700'
                              }`}>
                                {gap.status}
                              </span>
                            </div>
                            <div className="flex items-center justify-between text-[11px] text-slate-500 pt-2 border-t border-slate-200/50">
                              <span>Req: Level {gap.required_level}/5</span>
                              <button
                                type="button"
                                onClick={() => handleQuickSimulate(gap.skill_name, gap.required_level || 3)}
                                className="text-primary-700 hover:text-primary-800 font-semibold text-[10px]"
                              >
                                Simulate Next →
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                /* Empty Prompt State when no simulation run yet */
                <div className="bg-white rounded-2xl p-10 border border-slate-200 text-center space-y-4">
                  <div className="inline-flex p-3 rounded-full bg-primary-50 text-primary-600">
                    <Sparkles className="w-8 h-8 text-amber-500" />
                  </div>
                  <h4 className="text-base font-bold text-slate-900">
                    Ready to Explore What-If Scenarios?
                  </h4>
                  <p className="text-xs text-slate-500 max-w-md mx-auto leading-relaxed">
                    Choose any skill above and target mastery level to compute how your career readiness
                    and study completion date would change. You can also click "What-If" on any skill card
                    in the Skill Categorization Matrix.
                  </p>
                </div>
              )}
            </div>
          )}

          {/* TAB 5: Module 11.1 Explainable Skill ROI & Counterfactuals */}
          {activeTab === 'roi' && (
            <div className="space-y-6">
              {/* ROI Header Overview & KPIs */}
              <div className="bg-gradient-to-r from-emerald-900 via-teal-900 to-slate-900 rounded-2xl p-6 md:p-8 text-white shadow-md relative overflow-hidden">
                <div className="relative z-10 max-w-3xl space-y-3">
                  <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/20 text-emerald-300 text-xs font-semibold border border-emerald-500/30">
                    <TrendingUp className="w-3.5 h-3.5" />
                    Explainable AI • Module 11.1 Skill ROI Engine
                  </div>
                  <h3 className="text-xl md:text-2xl font-black tracking-tight">
                    Return on Learning Investment (Skill ROI)
                  </h3>
                  <p className="text-xs md:text-sm text-slate-300 leading-relaxed">
                    Prioritizes your missing and weak skills by <strong>marginal career readiness gain per week of study</strong>.
                    Discover the quickest path to elevate your profile readiness with deterministic, explainable calculations.
                  </p>
                </div>

                {/* Study Intensity Selector */}
                <div className="mt-6 pt-5 border-t border-slate-700/60 flex flex-wrap items-center justify-between gap-4">
                  <div className="flex items-center gap-2 text-xs text-slate-300">
                    <Clock className="w-4 h-4 text-emerald-400" />
                    <span>Study Intensity:</span>
                    <div className="inline-flex rounded-lg bg-slate-800 p-1 border border-slate-700">
                      {[5, 10, 20].map((hrs) => (
                        <button
                          key={hrs}
                          type="button"
                          disabled={updatingTimeline}
                          onClick={() => handleIntensityChange(hrs)}
                          className={`px-3 py-1 rounded-md text-xs font-bold transition ${
                            hoursPerWeek === hrs
                              ? 'bg-emerald-600 text-white shadow-xs'
                              : 'text-slate-400 hover:text-white'
                          }`}
                        >
                          {hrs}h/wk
                        </button>
                      ))}
                    </div>
                  </div>

                  <span className="text-xs text-emerald-300/80">
                    Total Potential Gain: <strong>+{roiData?.total_potential_gain ?? 0}%</strong> across {roiData?.total_estimated_hours ?? 0} study hours
                  </span>
                </div>
              </div>

              {/* Quickest Win & Highest Gain Highlight Cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                {/* Quickest Win Card */}
                <div className="bg-white rounded-2xl p-6 border-2 border-emerald-300 shadow-sm relative overflow-hidden flex flex-col justify-between">
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-800 text-xs font-bold border border-emerald-200">
                        <Zap className="w-3.5 h-3.5 text-emerald-600" />
                        Quickest Win Skill
                      </div>
                      {roiData?.quickest_win && (
                        <span className="text-xs font-extrabold px-2.5 py-0.5 rounded-full bg-emerald-600 text-white">
                          ROI: {roiData.quickest_win.roi_score}/wk
                        </span>
                      )}
                    </div>

                    {roiData?.quickest_win ? (
                      <>
                        <h4 className="text-lg font-black text-slate-900">
                          {roiData.quickest_win.skill_name}
                        </h4>
                        <div className="grid grid-cols-3 gap-2 py-2 text-center bg-slate-50 rounded-xl border border-slate-100">
                          <div>
                            <span className="text-[10px] uppercase font-bold text-slate-500 block">Readiness Gain</span>
                            <span className="text-base font-extrabold text-emerald-600">
                              +{roiData.quickest_win.readiness_gain}%
                            </span>
                          </div>
                          <div>
                            <span className="text-[10px] uppercase font-bold text-slate-500 block">Study Time</span>
                            <span className="text-base font-extrabold text-slate-800">
                              {roiData.quickest_win.estimated_weeks} wks
                            </span>
                          </div>
                          <div>
                            <span className="text-[10px] uppercase font-bold text-slate-500 block">Required Level</span>
                            <span className="text-base font-extrabold text-slate-800">
                              Level {roiData.quickest_win.required_level}/5
                            </span>
                          </div>
                        </div>
                        <p className="text-xs text-slate-600 leading-relaxed italic bg-emerald-50/60 p-3 rounded-lg border border-emerald-100">
                          "{roiData.quickest_win.explanation}"
                        </p>
                      </>
                    ) : (
                      <p className="text-xs text-slate-500 py-4">No active skill gaps detected for this career.</p>
                    )}
                  </div>

                  {roiData?.quickest_win && (
                    <button
                      type="button"
                      onClick={() => handleRunCounterfactual(roiData.quickest_win.skill_name, roiData.quickest_win.required_level)}
                      className="mt-4 w-full py-2 px-3 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold transition flex items-center justify-center gap-1.5"
                    >
                      <span>Simulate Quickest Win</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>

                {/* Highest Gain Card */}
                <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm flex flex-col justify-between">
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-blue-50 text-blue-800 text-xs font-bold border border-blue-200">
                        <Award className="w-3.5 h-3.5 text-blue-600" />
                        Highest Total Readiness Lift
                      </div>
                      {roiData?.highest_gain && (
                        <span className="text-xs font-extrabold px-2.5 py-0.5 rounded-full bg-blue-600 text-white">
                          +{roiData.highest_gain.readiness_gain}% Gain
                        </span>
                      )}
                    </div>

                    {roiData?.highest_gain ? (
                      <>
                        <h4 className="text-lg font-black text-slate-900">
                          {roiData.highest_gain.skill_name}
                        </h4>
                        <div className="grid grid-cols-3 gap-2 py-2 text-center bg-slate-50 rounded-xl border border-slate-100">
                          <div>
                            <span className="text-[10px] uppercase font-bold text-slate-500 block">Total Lift</span>
                            <span className="text-base font-extrabold text-blue-600">
                              +{roiData.highest_gain.readiness_gain}%
                            </span>
                          </div>
                          <div>
                            <span className="text-[10px] uppercase font-bold text-slate-500 block">Total Hours</span>
                            <span className="text-base font-extrabold text-slate-800">
                              {roiData.highest_gain.estimated_hours}h
                            </span>
                          </div>
                          <div>
                            <span className="text-[10px] uppercase font-bold text-slate-500 block">Importance</span>
                            <span className="text-base font-extrabold text-slate-800">
                              {roiData.highest_gain.importance}/5
                            </span>
                          </div>
                        </div>
                        <p className="text-xs text-slate-600 leading-relaxed italic bg-blue-50/60 p-3 rounded-lg border border-blue-100">
                          "{roiData.highest_gain.explanation}"
                        </p>
                      </>
                    ) : (
                      <p className="text-xs text-slate-500 py-4">No active skill gaps detected for this career.</p>
                    )}
                  </div>

                  {roiData?.highest_gain && (
                    <button
                      type="button"
                      onClick={() => handleRunCounterfactual(roiData.highest_gain.skill_name, roiData.highest_gain.required_level)}
                      className="mt-4 w-full py-2 px-3 rounded-xl bg-slate-800 hover:bg-slate-900 text-white text-xs font-bold transition flex items-center justify-center gap-1.5"
                    >
                      <span>Simulate Highest Gain</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>
              </div>

              {/* Counterfactual Evaluation Result Banner (if active) */}
              {counterfactualResult && (
                <div className="bg-emerald-50 rounded-2xl p-6 border-2 border-emerald-400 shadow-sm animate-fadeIn space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Sparkles className="w-5 h-5 text-emerald-600" />
                      <h4 className="text-sm font-black text-emerald-950 uppercase tracking-wider">
                        Counterfactual Result: {counterfactualResult.skill_name}
                      </h4>
                    </div>
                    <button
                      type="button"
                      onClick={() => setCounterfactualResult(null)}
                      className="text-xs text-emerald-700 hover:text-emerald-900 font-bold px-2 py-1 rounded-md hover:bg-emerald-100"
                    >
                      ✕ Close
                    </button>
                  </div>

                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3 bg-white p-4 rounded-xl border border-emerald-200">
                    <div>
                      <span className="text-[10px] font-bold text-slate-500 uppercase block">Readiness Transition</span>
                      <span className="text-sm font-extrabold text-slate-900">
                        {counterfactualResult.before_readiness}% ➔ <strong className="text-emerald-600">{counterfactualResult.after_readiness}%</strong>
                      </span>
                    </div>
                    <div>
                      <span className="text-[10px] font-bold text-slate-500 uppercase block">Marginal Gain</span>
                      <span className="text-sm font-extrabold text-emerald-600">
                        +{counterfactualResult.readiness_gain}%
                      </span>
                    </div>
                    <div>
                      <span className="text-[10px] font-bold text-slate-500 uppercase block">Effort Required</span>
                      <span className="text-sm font-extrabold text-slate-800">
                        {counterfactualResult.estimated_hours}h ({counterfactualResult.estimated_weeks} wks)
                      </span>
                    </div>
                    <div>
                      <span className="text-[10px] font-bold text-slate-500 uppercase block">Calculated Skill ROI</span>
                      <span className="text-sm font-extrabold text-emerald-700">
                        {counterfactualResult.roi_score} pts/week
                      </span>
                    </div>
                  </div>

                  <p className="text-xs text-emerald-900 font-medium leading-relaxed bg-white/70 p-3 rounded-lg border border-emerald-200/60">
                    {counterfactualResult.explanation}
                  </p>
                </div>
              )}

              {/* Complete Deterministic ROI Ranking Table */}
              <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="text-base font-black text-slate-900">
                      Deterministic Skill ROI Ranking Matrix
                    </h4>
                    <p className="text-xs text-slate-500">
                      Ranked strictly by readiness gain per study week, career importance, and remaining deficit
                    </p>
                  </div>
                  <span className="text-xs font-bold text-slate-400">
                    {roiData?.ranked_skills?.length || 0} Actionable Skills
                  </span>
                </div>

                {(!roiData?.ranked_skills || roiData.ranked_skills.length === 0) ? (
                  <p className="text-xs text-slate-500 py-6 text-center italic">
                    All competencies for this career are currently satisfied in your profile.
                  </p>
                ) : (
                  <div className="space-y-3">
                    {roiData.ranked_skills.map((skill, index) => (
                      <div
                        key={skill.skill_name}
                        className="p-4 rounded-xl border border-slate-200 hover:border-emerald-300 hover:shadow-xs transition bg-slate-50/40 space-y-3"
                      >
                        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
                          <div className="flex items-center gap-3">
                            <span className="w-7 h-7 rounded-full bg-slate-900 text-white text-xs font-black flex items-center justify-center shrink-0">
                              #{index + 1}
                            </span>
                            <div>
                              <div className="flex items-center gap-2">
                                <h5 className="font-black text-sm text-slate-900">{skill.skill_name}</h5>
                                <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                                  skill.status === 'MISSING'
                                    ? 'bg-rose-100 text-rose-700'
                                    : 'bg-amber-100 text-amber-700'
                                }`}>
                                  {skill.status}
                                </span>
                              </div>
                              <p className="text-[11px] text-slate-500 mt-0.5">
                                Current: Level {skill.current_proficiency}/5 • Target: Level {skill.required_level}/5 • Importance: {skill.importance}/5
                              </p>
                            </div>
                          </div>

                          <div className="flex items-center gap-4 shrink-0">
                            <div className="text-right">
                              <span className="text-xs font-extrabold text-emerald-600 block">
                                +{skill.readiness_gain}% Gain
                              </span>
                              <span className="text-[10px] text-slate-400">
                                {skill.estimated_hours}h (~{skill.estimated_weeks} wks)
                              </span>
                            </div>
                            <div className="text-right">
                              <span className="text-xs font-black px-2.5 py-1 rounded-lg bg-emerald-100 text-emerald-800 border border-emerald-200 block">
                                ROI: {skill.roi_score}
                              </span>
                              <span className="text-[9px] text-slate-400">pts / week</span>
                            </div>
                            <button
                              type="button"
                              disabled={runningCounterfactual}
                              onClick={() => handleRunCounterfactual(skill.skill_name, skill.required_level)}
                              className="px-3 py-1.5 bg-white hover:bg-emerald-50 text-emerald-700 border border-emerald-300 rounded-lg text-xs font-bold transition shadow-2xs"
                            >
                              Counterfactual →
                            </button>
                          </div>
                        </div>

                        {/* Explainable Reasoning */}
                        <div className="pt-2.5 border-t border-slate-200/60 text-xs text-slate-600 leading-relaxed">
                          <span className="font-semibold text-slate-700">Reasoning: </span>
                          {skill.explanation}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* TAB 6: Actionable Portfolio & Capstone Projects */}
          {activeTab === 'projects' && (
            <div className="space-y-6">
              {/* Header Overview Card */}
              <div className="bg-linear-to-br from-indigo-900 via-slate-900 to-slate-900 text-white rounded-2xl p-6 shadow-md relative overflow-hidden">
                <div className="relative z-10 space-y-3">
                  <div className="flex flex-wrap items-center justify-between gap-4">
                    <div className="flex items-center gap-2">
                      <span className="px-3 py-1 rounded-full text-xs font-bold bg-indigo-500/20 text-indigo-300 border border-indigo-400/30 flex items-center gap-1.5">
                        <FolderGit2 className="w-3.5 h-3.5" />
                        Phase 11.2 Capstone Engine
                      </span>
                      <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-white/10 text-slate-300">
                        {portfolioData?.career_title || selectedCareer?.title}
                      </span>
                    </div>
                    <div className="flex items-center gap-3 text-xs text-slate-300">
                      <span>
                        Target Readiness: <strong className="text-white font-extrabold">{score}%</strong>
                      </span>
                      <span>•</span>
                      <span>
                        Catalog: <strong className="text-white font-extrabold">{portfolioData?.recommendations?.length || 0}</strong> projects
                      </span>
                    </div>
                  </div>

                  <div>
                    <h3 className="text-xl font-black text-white">
                      Actionable Portfolio & Capstone Project Recommendations
                    </h3>
                    <p className="text-xs text-indigo-200 mt-1 max-w-3xl leading-relaxed">
                      Bridge verified competency deficits with production-grade capstone projects. Each project is deterministically ranked to maximize skill-gap closure, ROI-weighted competencies, and tangible proof-of-work deliverables that demonstrate mastery to hiring managers.
                    </p>
                  </div>
                </div>
              </div>

              {/* Quickest Gap Closer Highlight Card */}
              {portfolioData?.quickest_gap_closer && (
                <div className="bg-linear-to-r from-emerald-50 via-teal-50/60 to-white border-2 border-emerald-300 rounded-2xl p-5 shadow-sm space-y-3">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <span className="px-2.5 py-1 rounded-full text-xs font-black bg-emerald-600 text-white flex items-center gap-1 shadow-2xs">
                        <Zap className="w-3.5 h-3.5" />
                        Top Recommended Project: Quickest Gap Closer
                      </span>
                      <span className={`text-[11px] font-bold px-2 py-0.5 rounded-full ${
                        portfolioData.quickest_gap_closer.difficulty === 'Beginner'
                          ? 'bg-emerald-100 text-emerald-800'
                          : portfolioData.quickest_gap_closer.difficulty === 'Intermediate'
                          ? 'bg-amber-100 text-amber-800'
                          : 'bg-purple-100 text-purple-800'
                      }`}>
                        {portfolioData.quickest_gap_closer.difficulty}
                      </span>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-xs font-bold text-slate-500">
                        Match Score: <strong className="text-emerald-700 font-black">{portfolioData.quickest_gap_closer.recommendation_score}/100</strong>
                      </span>
                      <span className="text-xs font-bold text-slate-500">
                        Appeal: <strong className="text-slate-800 font-black">{portfolioData.quickest_gap_closer.portfolio_value}/100</strong>
                      </span>
                    </div>
                  </div>

                  <div>
                    <h4 className="text-base font-black text-slate-900">
                      {portfolioData.quickest_gap_closer.title}
                    </h4>
                    <p className="text-xs text-slate-600 mt-1 leading-relaxed">
                      {portfolioData.quickest_gap_closer.description}
                    </p>
                  </div>

                  {/* Addressed gaps & reasoning */}
                  <div className="bg-white/80 rounded-xl p-3 border border-emerald-200/80 space-y-2">
                    <div className="flex flex-wrap items-center gap-2 text-xs">
                      <span className="font-bold text-slate-700">Addresses Competencies:</span>
                      {portfolioData.quickest_gap_closer.missing_skills_addressed?.map((s) => (
                        <span key={s} className="px-2 py-0.5 rounded-md text-[10px] font-bold bg-rose-100 text-rose-700 border border-rose-200 flex items-center gap-1">
                          <AlertCircle className="w-2.5 h-2.5" /> {s} (Missing Gap)
                        </span>
                      ))}
                      {portfolioData.quickest_gap_closer.weak_skills_addressed?.map((s) => (
                        <span key={s} className="px-2 py-0.5 rounded-md text-[10px] font-bold bg-amber-100 text-amber-700 border border-amber-200 flex items-center gap-1">
                          <TrendingUp className="w-2.5 h-2.5" /> {s} (Weak Skill)
                        </span>
                      ))}
                      {portfolioData.quickest_gap_closer.addresses_quickest_win && (
                        <span className="px-2 py-0.5 rounded-md text-[10px] font-black bg-emerald-100 text-emerald-800 border border-emerald-300 flex items-center gap-1">
                          <Zap className="w-2.5 h-2.5 text-emerald-600" /> Quickest Win Aligned
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-emerald-900 font-medium">
                      <span className="font-bold text-emerald-950">Why Build This First: </span>
                      {portfolioData.quickest_gap_closer.recommendation_reason}
                    </p>
                  </div>
                </div>
              )}

              {/* Filter controls */}
              <div className="flex flex-wrap items-center justify-between gap-4 bg-white p-4 rounded-xl border border-slate-200 shadow-2xs">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Difficulty Filter:</span>
                  {['ALL', 'BEGINNER', 'INTERMEDIATE', 'ADVANCED'].map((diff) => {
                    const count = diff === 'ALL'
                      ? (portfolioData?.recommendations?.length || 0)
                      : (portfolioData?.recommendations?.filter(p => p.difficulty.toUpperCase() === diff).length || 0);
                    return (
                      <button
                        key={diff}
                        type="button"
                        onClick={() => setProjectDifficultyFilter(diff)}
                        className={`px-3 py-1.5 rounded-lg text-xs font-bold transition flex items-center gap-1.5 ${
                          projectDifficultyFilter === diff
                            ? 'bg-slate-900 text-white shadow-2xs'
                            : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                        }`}
                      >
                        {diff.charAt(0) + diff.slice(1).toLowerCase()}
                        <span className={`text-[10px] px-1.5 py-0.2 rounded-full ${
                          projectDifficultyFilter === diff ? 'bg-slate-700 text-white' : 'bg-slate-200 text-slate-700'
                        }`}>
                          {count}
                        </span>
                      </button>
                    );
                  })}
                </div>
                <div className="text-xs font-medium text-slate-500">
                  Showing {
                    portfolioData?.recommendations?.filter(
                      p => projectDifficultyFilter === 'ALL' || p.difficulty.toUpperCase() === projectDifficultyFilter
                    ).length || 0
                  } recommended projects
                </div>
              </div>

              {/* Complete Deterministic Project Recommendations List */}
              <div className="space-y-4">
                {(!portfolioData?.recommendations || portfolioData.recommendations.length === 0) ? (
                  <div className="bg-white rounded-2xl p-8 border border-slate-200 text-center text-slate-500 text-sm">
                    No portfolio projects currently mapped for this career track.
                  </div>
                ) : (
                  portfolioData.recommendations
                    .filter(p => projectDifficultyFilter === 'ALL' || p.difficulty.toUpperCase() === projectDifficultyFilter)
                    .map((project, index) => {
                      const diffBadgeColor =
                        project.difficulty === 'Beginner'
                          ? 'bg-emerald-100 text-emerald-800 border-emerald-200'
                          : project.difficulty === 'Intermediate'
                          ? 'bg-amber-100 text-amber-800 border-amber-200'
                          : 'bg-purple-100 text-purple-800 border-purple-200';

                      return (
                        <div
                          key={project.project_id}
                          className="bg-white rounded-2xl p-6 border border-slate-200 hover:border-indigo-300 hover:shadow-md transition space-y-4"
                        >
                          {/* Card Header */}
                          <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
                            <div className="space-y-1.5 flex-1">
                              <div className="flex flex-wrap items-center gap-2">
                                <span className="w-6 h-6 rounded-full bg-slate-900 text-white text-xs font-black flex items-center justify-center shrink-0">
                                  #{index + 1}
                                </span>
                                <h4 className="text-base font-black text-slate-900">
                                  {project.title}
                                </h4>
                                <span className={`text-[10px] font-black px-2 py-0.5 rounded-full border ${diffBadgeColor}`}>
                                  {project.difficulty}
                                </span>
                                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 border border-slate-200">
                                  {project.domain}
                                </span>
                                {project.addresses_quickest_win && (
                                  <span className="text-[10px] font-black px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 border border-emerald-300 flex items-center gap-1">
                                    <Zap className="w-3 h-3 text-emerald-600" /> Quickest Win
                                  </span>
                                )}
                              </div>
                              <p className="text-xs text-slate-600 leading-relaxed">
                                {project.description}
                              </p>
                            </div>

                            {/* Metrics pill */}
                            <div className="flex md:flex-col items-end gap-2 shrink-0 bg-slate-50 p-3 rounded-xl border border-slate-200">
                              <div className="text-right">
                                <span className="text-xs font-bold text-slate-400 block">Match Score</span>
                                <span className="text-sm font-black text-indigo-700">
                                  {project.recommendation_score} / 100
                                </span>
                              </div>
                              <div className="text-right">
                                <span className="text-[10px] font-bold text-slate-400 block">Effort / Appeal</span>
                                <span className="text-xs font-extrabold text-slate-700">
                                  ~{project.estimated_hours}h • {project.portfolio_value} Appeal
                                </span>
                              </div>
                            </div>
                          </div>

                          {/* Competency Badges */}
                          <div className="flex flex-wrap items-center gap-2 pt-1 border-t border-slate-100">
                            <span className="text-[11px] font-bold text-slate-500 mr-1">Skills Demonstrated:</span>
                            {project.demonstrated_skills?.map((s) => {
                              const isMissing = project.missing_skills_addressed?.includes(s);
                              const isWeak = project.weak_skills_addressed?.includes(s);
                              const isCovered = project.covered_career_skills?.includes(s);

                              let badgeStyle = "bg-slate-100 text-slate-700 border-slate-200";
                              if (isMissing) {
                                badgeStyle = "bg-rose-100 text-rose-800 border-rose-300 font-black";
                              } else if (isWeak) {
                                badgeStyle = "bg-amber-100 text-amber-800 border-amber-300 font-bold";
                              } else if (isCovered) {
                                badgeStyle = "bg-indigo-50 text-indigo-800 border-indigo-200 font-bold";
                              }

                              return (
                                <span
                                  key={s}
                                  className={`px-2 py-0.5 rounded-md text-[11px] border flex items-center gap-1 ${badgeStyle}`}
                                >
                                  {isMissing && <AlertCircle className="w-2.5 h-2.5 text-rose-600" />}
                                  {isWeak && <TrendingUp className="w-2.5 h-2.5 text-amber-600" />}
                                  {isCovered && !isMissing && !isWeak && <Check className="w-2.5 h-2.5 text-indigo-600" />}
                                  {s}
                                  {isMissing && <span className="text-[9px] uppercase font-bold">(Gap)</span>}
                                  {isWeak && <span className="text-[9px] uppercase font-bold">(Weak)</span>}
                                </span>
                              );
                            })}
                          </div>

                          {/* Recommendation Reasoning Callout */}
                          <div className="bg-indigo-50/50 rounded-xl p-3.5 border border-indigo-100 text-xs text-indigo-950 leading-relaxed">
                            <span className="font-extrabold text-indigo-900 block mb-0.5">
                              Why this project is recommended:
                            </span>
                            {project.recommendation_reason}
                          </div>

                          {/* Deliverables Checklist (Proof-of-work) */}
                          {project.deliverables && project.deliverables.length > 0 && (
                            <div className="bg-slate-50/70 rounded-xl p-3.5 border border-slate-200 space-y-2">
                              <div className="flex items-center gap-1.5 text-xs font-bold text-slate-800">
                                <CheckSquare className="w-3.5 h-3.5 text-primary-600" />
                                Actionable Deliverables & Portfolio Proof-of-Work:
                              </div>
                              <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs text-slate-600">
                                {project.deliverables.map((del, dIdx) => (
                                  <div key={dIdx} className="flex items-start gap-2">
                                    <Check className="w-3.5 h-3.5 text-emerald-600 shrink-0 mt-0.5" />
                                    <span>{del}</span>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}

                          {/* Extension Ideas (Optional Deepening) */}
                          {project.extension_ideas && project.extension_ideas.length > 0 && (
                            <div className="text-xs text-slate-500 pt-1 flex items-start gap-2">
                              <Sparkles className="w-3.5 h-3.5 text-amber-500 shrink-0 mt-0.5" />
                              <div>
                                <span className="font-bold text-slate-700">Deepening Opportunities: </span>
                                {project.extension_ideas.join(' • ')}
                              </div>
                            </div>
                          )}
                        </div>
                      );
                    })
                )}
              </div>
            </div>
          )}
        </>
      )}

    </div>
  );
}
