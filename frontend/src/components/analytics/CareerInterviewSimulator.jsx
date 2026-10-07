import React, { useState, useEffect } from 'react';
import { api } from '../../services/api';
import { Spinner, Alert } from '../common/UIFeedback';
import { Badge } from '../common/Badge';
import { RadialGauge } from '../common/RadialGauge';
import {
  MessagesSquare,
  Award,
  Sparkles,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  Clock,
  ArrowRight,
  ArrowLeft,
  RefreshCw,
  FolderGit2,
  TrendingUp,
  GraduationCap,
  Briefcase,
  Compass,
  ShieldCheck,
  ChevronDown,
  ChevronUp,
  Info,
  BookOpen,
} from 'lucide-react';

export function CareerInterviewSimulator({
  careerId,
  careerTitle = '',
  availableCareers = [],
}) {
  const [selectedCareerId, setSelectedCareerId] = useState(careerId);
  const [difficulty, setDifficulty] = useState('INTERMEDIATE');
  const [questionCount, setQuestionCount] = useState(5);

  // Simulation flow states: 'SETUP' | 'INTERVIEW' | 'EVALUATING' | 'RESULTS'
  const [stage, setStage] = useState('SETUP');
  const [session, setSession] = useState(null);
  const [currentQIndex, setCurrentQIndex] = useState(0);
  const [answers, setAnswers] = useState({}); // question_id -> string
  const [evaluation, setEvaluation] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [expandedQId, setExpandedQId] = useState(null);

  useEffect(() => {
    if (careerId) {
      setSelectedCareerId(careerId);
    }
  }, [careerId]);

  async function handleStartSession() {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getInterviewSimulationSession(selectedCareerId, {
        difficulty,
        questionCount,
      });
      if (res?.questions && res.questions.length > 0) {
        setSession(res);
        setCurrentQIndex(0);
        // Initialize empty answers
        const initialAns = {};
        res.questions.forEach((q) => {
          initialAns[q.question_id] = '';
        });
        setAnswers(initialAns);
        setStage('INTERVIEW');
      } else {
        setError('No interview questions available for this configuration.');
      }
    } catch (err) {
      console.warn('Failed to start interview simulation', err);
      setError(err.message || 'Failed to start interview simulation session');
    } finally {
      setLoading(false);
    }
  }

  function handleAnswerChange(qId, text) {
    setAnswers((prev) => ({
      ...prev,
      [qId]: text,
    }));
  }

  async function handleSubmitInterview() {
    setStage('EVALUATING');
    setLoading(true);
    setError(null);
    try {
      const answersPayload = Object.entries(answers).map(([qId, ansText]) => ({
        question_id: qId,
        answer: ansText || '',
      }));

      const res = await api.evaluateInterviewSimulation(selectedCareerId, {
        answers: answersPayload,
        difficulty,
      });

      setEvaluation(res);
      setStage('RESULTS');
      if (res?.question_results?.[0]?.question_id) {
        setExpandedQId(res.question_results[0].question_id);
      }
    } catch (err) {
      console.warn('Failed to evaluate interview answers', err);
      setError(err.message || 'Failed to evaluate interview answers');
      setStage('INTERVIEW');
    } finally {
      setLoading(false);
    }
  }

  function handleReset() {
    setStage('SETUP');
    setSession(null);
    setEvaluation(null);
    setAnswers({});
    setError(null);
  }

  const currentQuestions = session?.questions || [];
  const activeQ = currentQuestions[currentQIndex];
  const activeAnswer = activeQ ? (answers[activeQ.question_id] || '') : '';
  const answeredCount = Object.values(answers).filter((a) => a && a.trim().length > 0).length;

  return (
    <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200 space-y-6">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-100 pb-5">
        <div>
          <div className="flex items-center gap-2 mb-1.5 flex-wrap">
            <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 flex items-center gap-1.5">
              <MessagesSquare className="w-3.5 h-3.5" />
              Phase 11 Module 11.6: AI Interview Simulation & Career Readiness Assessment
            </span>
            {stage === 'INTERVIEW' && (
              <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-slate-100 text-slate-700">
                Question {currentQIndex + 1} of {currentQuestions.length} ({answeredCount} answered)
              </span>
            )}
          </div>
          <h2 className="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <span>Career Interview Simulator</span>
            <span className="text-slate-400 font-normal text-base">
              ({careerTitle || session?.career?.title || 'Selected Track'})
            </span>
          </h2>
          <p className="text-xs text-slate-500 mt-0.5 max-w-2xl">
            Experience realistic technical and conceptual interview scenarios. Receive deterministic, explainable readiness evaluations, category scores, and targeted skill ROI recommendations.
          </p>
        </div>

        {stage === 'RESULTS' && (
          <button
            onClick={handleReset}
            className="px-3.5 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold transition flex items-center gap-1.5 self-start md:self-auto"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            New Practice Session
          </button>
        )}
      </div>

      {error && <Alert type="error" message={error} />}

      {/* STAGE 1: SETUP & CONFIGURATION */}
      {stage === 'SETUP' && (
        <div className="max-w-xl mx-auto py-4 space-y-6">
          <div className="bg-slate-50/80 p-6 rounded-2xl border border-slate-200 space-y-5">
            <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wide">
              Configure Practice Interview
            </h3>

            {/* Career Selector if available */}
            {availableCareers && availableCareers.length > 0 && (
              <div className="space-y-1.5">
                <label className="text-xs font-bold text-slate-700">Target Career Track:</label>
                <select
                  value={selectedCareerId}
                  onChange={(e) => setSelectedCareerId(Number(e.target.value))}
                  className="w-full bg-white border border-slate-300 text-slate-800 text-xs rounded-xl px-3 py-2.5 font-medium"
                >
                  {availableCareers.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.title} ({c.domain})
                    </option>
                  ))}
                </select>
              </div>
            )}

            {/* Difficulty Selector */}
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-slate-700">Interview Difficulty Tier:</label>
              <div className="grid grid-cols-4 gap-2">
                {[
                  { id: 'BEGINNER', label: 'Beginner' },
                  { id: 'INTERMEDIATE', label: 'Intermediate' },
                  { id: 'ADVANCED', label: 'Advanced' },
                  { id: 'ALL', label: 'Mixed / All' },
                ].map((d) => (
                  <button
                    key={d.id}
                    type="button"
                    onClick={() => setDifficulty(d.id)}
                    className={`py-2 px-2 text-xs rounded-xl font-bold transition text-center ${
                      difficulty === d.id
                        ? 'bg-emerald-600 text-white shadow-xs'
                        : 'bg-white text-slate-600 border border-slate-200 hover:border-slate-300'
                    }`}
                  >
                    {d.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Question Count */}
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-slate-700">Session Length:</label>
              <div className="flex gap-2">
                {[3, 5, 8].map((cnt) => (
                  <button
                    key={cnt}
                    type="button"
                    onClick={() => setQuestionCount(cnt)}
                    className={`flex-1 py-2 text-xs rounded-xl font-bold transition text-center ${
                      questionCount === cnt
                        ? 'bg-slate-900 text-white shadow-xs'
                        : 'bg-white text-slate-600 border border-slate-200 hover:border-slate-300'
                    }`}
                  >
                    {cnt} Questions
                  </button>
                ))}
              </div>
            </div>

            <button
              onClick={handleStartSession}
              disabled={loading}
              className="w-full py-3 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-sm font-bold shadow-md shadow-emerald-600/20 transition flex items-center justify-center gap-2 mt-4"
            >
              {loading ? (
                <>
                  <Spinner size="sm" /> Generating Curated Questions...
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4 text-emerald-200" />
                  Begin Practice Simulation
                </>
              )}
            </button>
          </div>

          <div className="text-[11px] text-slate-500 bg-slate-100 p-3 rounded-xl border border-slate-200 flex items-start gap-2">
            <Info className="w-4 h-4 text-slate-400 shrink-0 mt-0.5" />
            <span>
              <strong>Assessment Principle:</strong> This deterministic simulator evaluates technical keyword coverage, conceptual depth, problem-solving methods, and communication indicators. It does not replace real human interviewers or guarantee employment.
            </span>
          </div>
        </div>
      )}

      {/* STAGE 2: INTERACTIVE INTERVIEW SESSION */}
      {stage === 'INTERVIEW' && activeQ && (
        <div className="space-y-5">
          {/* Stepper progress indicator */}
          <div className="flex items-center gap-1.5 overflow-x-auto pb-1">
            {currentQuestions.map((q, idx) => {
              const isAnswered = answers[q.question_id]?.trim().length > 0;
              const isCurrent = idx === currentQIndex;
              return (
                <button
                  key={q.question_id}
                  onClick={() => setCurrentQIndex(idx)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-bold transition shrink-0 flex items-center gap-1.5 ${
                    isCurrent
                      ? 'bg-emerald-600 text-white shadow-xs'
                      : isAnswered
                      ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                      : 'bg-slate-100 text-slate-500 hover:bg-slate-200'
                  }`}
                >
                  <span>Q{idx + 1}</span>
                  {isAnswered && <CheckCircle2 className="w-3 h-3 text-emerald-600" />}
                </button>
              );
            })}
          </div>

          {/* Active Question Card */}
          <div className="p-6 bg-slate-50/60 rounded-2xl border border-slate-200 space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-200/60 pb-3">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-xs font-extrabold px-2.5 py-0.5 rounded-full bg-slate-200 text-slate-800">
                  Question {currentQIndex + 1} of {currentQuestions.length}
                </span>
                <span className="text-xs font-bold px-2 py-0.5 rounded bg-indigo-100 text-indigo-800">
                  {activeQ.category}
                </span>
                <span className="text-xs font-semibold px-2 py-0.5 rounded bg-slate-100 text-slate-600 border border-slate-200">
                  {activeQ.difficulty}
                </span>
              </div>
              <span className="text-xs font-semibold text-slate-500">
                Target Competency: <strong className="text-slate-800">{activeQ.competency}</strong>
              </span>
            </div>

            {/* Question Text */}
            <h3 className="text-base font-extrabold text-slate-900 leading-snug">
              {activeQ.question_text}
            </h3>

            {activeQ.context_hint && (
              <div className="text-xs text-slate-500 bg-white p-3 rounded-xl border border-slate-200 flex items-start gap-2">
                <HelpCircle className="w-3.5 h-3.5 text-indigo-500 shrink-0 mt-0.5" />
                <span>
                  <strong>Tip:</strong> {activeQ.context_hint}
                </span>
              </div>
            )}

            {/* Response Textarea */}
            <div className="space-y-1.5 pt-2">
              <div className="flex justify-between items-center text-xs text-slate-500">
                <label className="font-bold text-slate-700">Your Technical Response:</label>
                <span>{activeAnswer.split(/\s+/).filter(Boolean).length} words</span>
              </div>
              <textarea
                rows={6}
                value={activeAnswer}
                onChange={(e) => handleAnswerChange(activeQ.question_id, e.target.value)}
                placeholder="Formulate your response thoroughly. Explain fundamental mechanisms, trade-offs, and practical considerations using standard terminology..."
                className="w-full bg-white border border-slate-300 text-slate-900 text-xs rounded-xl p-3.5 focus:outline-none focus:ring-2 focus:ring-emerald-500/30 focus:border-emerald-500 transition leading-relaxed"
              />
            </div>
          </div>

          {/* Navigation Controls */}
          <div className="flex items-center justify-between gap-4 pt-2">
            <button
              onClick={() => setCurrentQIndex((prev) => Math.max(0, prev - 1))}
              disabled={currentQIndex === 0}
              className="px-4 py-2 rounded-xl border border-slate-200 bg-white text-slate-600 hover:bg-slate-50 text-xs font-bold transition disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-1.5"
            >
              <ArrowLeft className="w-3.5 h-3.5" /> Previous
            </button>

            <div className="flex items-center gap-2">
              {currentQIndex < currentQuestions.length - 1 ? (
                <button
                  onClick={() => setCurrentQIndex((prev) => Math.min(currentQuestions.length - 1, prev + 1))}
                  className="px-5 py-2 rounded-xl bg-slate-800 hover:bg-slate-900 text-white text-xs font-bold transition flex items-center gap-1.5"
                >
                  Next Question <ArrowRight className="w-3.5 h-3.5" />
                </button>
              ) : null}

              <button
                onClick={handleSubmitInterview}
                className="px-6 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold shadow-md shadow-emerald-600/20 transition flex items-center gap-1.5"
              >
                <Sparkles className="w-3.5 h-3.5" />
                Finish & Evaluate Interview ({answeredCount}/{currentQuestions.length})
              </button>
            </div>
          </div>
        </div>
      )}

      {/* STAGE 3: EVALUATING SPINNER */}
      {stage === 'EVALUATING' && (
        <div className="flex flex-col items-center justify-center py-16 space-y-4">
          <Spinner size="lg" />
          <p className="text-sm font-bold text-slate-800">
            Analyzing concept coverage, completeness, and communication structure...
          </p>
          <p className="text-xs text-slate-500 max-w-md text-center">
            Evaluating responses against standardized competency benchmarks and computing explainable skill ROI.
          </p>
        </div>
      )}

      {/* STAGE 4: RESULTS DASHBOARD */}
      {stage === 'RESULTS' && evaluation && (
        <div className="space-y-6">
          {/* Top Score & Category Breakdown Card */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
            {/* Overall Score Box */}
            <div className="p-6 rounded-2xl border border-emerald-200 bg-gradient-to-br from-emerald-50/60 to-white flex flex-col items-center justify-center text-center space-y-3">
              <span className="text-xs font-bold text-emerald-900 uppercase tracking-wider">
                Overall Interview Readiness
              </span>

              <div className="relative">
                <RadialGauge
                  value={evaluation.overall_readiness}
                  size={140}
                  strokeWidth={12}
                  colorClass={
                    evaluation.overall_readiness >= 85
                      ? 'text-emerald-500'
                      : evaluation.overall_readiness >= 70
                      ? 'text-indigo-500'
                      : evaluation.overall_readiness >= 55
                      ? 'text-amber-500'
                      : 'text-rose-500'
                  }
                />
              </div>

              <div>
                <Badge
                  variant={
                    evaluation.readiness_band === 'INTERVIEW_READY'
                      ? 'success'
                      : evaluation.readiness_band === 'STRONG_PREPARATION'
                      ? 'info'
                      : evaluation.readiness_band === 'NEEDS_PRACTICE'
                      ? 'warning'
                      : 'error'
                  }
                >
                  {evaluation.readiness_label}
                </Badge>
                <p className="text-xs text-slate-600 mt-2 leading-relaxed">
                  {evaluation.readiness_summary}
                </p>
              </div>
            </div>

            {/* Category Scores Bars */}
            <div className="lg:col-span-2 p-6 rounded-2xl border border-slate-200 bg-slate-50/50 flex flex-col justify-between space-y-4">
              <div>
                <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider mb-3">
                  Readiness Dimension Scores
                </h4>
                <div className="space-y-3">
                  {[
                    { label: 'Technical Knowledge', val: evaluation.category_scores?.technical, weight: '30%' },
                    { label: 'Conceptual Understanding', val: evaluation.category_scores?.conceptual, weight: '20%' },
                    { label: 'Problem Solving & Scenarios', val: evaluation.category_scores?.problem_solving, weight: '20%' },
                    { label: 'Communication & Structure', val: evaluation.category_scores?.communication, weight: '15%' },
                    { label: 'Career Competency Coverage', val: evaluation.category_scores?.career_competency, weight: '15%' },
                  ].map((dim, idx) => (
                    <div key={idx} className="space-y-1">
                      <div className="flex justify-between text-xs">
                        <span className="font-semibold text-slate-700">
                          {dim.label} <span className="text-[10px] text-slate-400">({dim.weight})</span>
                        </span>
                        <span className="font-extrabold text-slate-900">{dim.val}%</span>
                      </div>
                      <div className="w-full bg-slate-200 h-2 rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full transition-all duration-500 ${
                            dim.val >= 80 ? 'bg-emerald-500' : dim.val >= 65 ? 'bg-indigo-500' : dim.val >= 50 ? 'bg-amber-500' : 'bg-rose-500'
                          }`}
                          style={{ width: `${Math.min(100, Math.max(0, dim.val || 0))}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Natural-language summary explanation */}
              <div className="p-3 bg-white rounded-xl border border-slate-200 text-xs text-slate-700 leading-relaxed font-medium">
                <Sparkles className="w-3.5 h-3.5 text-indigo-600 inline mr-1.5" />
                {evaluation.explanation}
              </div>
            </div>
          </div>

          {/* Strengths & Weaknesses Breakdown */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Strengths */}
            <div className="p-4 bg-emerald-50/50 rounded-xl border border-emerald-200 space-y-2">
              <h5 className="text-xs font-bold text-emerald-900 uppercase flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                Demonstrated Strengths ({evaluation.strengths?.length || 0})
              </h5>
              <div className="space-y-1.5">
                {evaluation.strengths?.map((s, idx) => (
                  <div key={idx} className="flex justify-between items-center text-xs bg-white p-2 rounded-lg border border-emerald-100">
                    <span className="font-bold text-slate-800">{s.competency}</span>
                    <span className="font-extrabold text-emerald-700">{s.average_score}%</span>
                  </div>
                ))}
                {(!evaluation.strengths || evaluation.strengths.length === 0) && (
                  <p className="text-xs text-slate-400 italic">No competencies reached strength threshold (70%+).</p>
                )}
              </div>
            </div>

            {/* Weaknesses */}
            <div className="p-4 bg-amber-50/50 rounded-xl border border-amber-200 space-y-2">
              <h5 className="text-xs font-bold text-amber-900 uppercase flex items-center gap-1.5">
                <AlertCircle className="w-4 h-4 text-amber-600" />
                Reinforcement Recommended ({evaluation.weaknesses?.length || 0})
              </h5>
              <div className="space-y-1.5">
                {evaluation.weaknesses?.map((w, idx) => (
                  <div key={idx} className="flex justify-between items-center text-xs bg-white p-2 rounded-lg border border-amber-100">
                    <span className="font-bold text-slate-800">{w.competency}</span>
                    <span className="font-extrabold text-amber-700">{w.average_score}%</span>
                  </div>
                ))}
                {(!evaluation.weaknesses || evaluation.weaknesses.length === 0) && (
                  <p className="text-xs text-slate-400 italic">All evaluated competencies met proficiency standards.</p>
                )}
              </div>
            </div>
          </div>

          {/* Cross-Module Intelligence Insights */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Phase 11.1 Skill ROI Card */}
            {evaluation.integrations?.skill_roi && (
              <div className="p-4 bg-gradient-to-br from-indigo-50/60 to-white rounded-xl border border-indigo-200 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-indigo-950 uppercase flex items-center gap-1.5">
                    <TrendingUp className="w-3.5 h-3.5 text-indigo-600" />
                    High-ROI Next Skill (Phase 11.1)
                  </span>
                  <span className="text-[10px] bg-indigo-100 text-indigo-800 font-bold px-2 py-0.5 rounded">
                    ROI: {evaluation.integrations.skill_roi.roi_score} pts/wk
                  </span>
                </div>
                <div className="text-xs text-slate-700 font-semibold">
                  Prioritize: <strong className="text-indigo-900">{evaluation.integrations.skill_roi.prioritized_skill}</strong>
                </div>
                <p className="text-[11px] text-slate-600 leading-relaxed">
                  {evaluation.integrations.skill_roi.rationale}
                </p>
              </div>
            )}

            {/* Phase 11.2 Portfolio Project Card */}
            {evaluation.integrations?.portfolio_project && (
              <div className="p-4 bg-gradient-to-br from-slate-50 to-white rounded-xl border border-slate-200 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-900 uppercase flex items-center gap-1.5">
                    <FolderGit2 className="w-3.5 h-3.5 text-slate-600" />
                    Targeted Capstone Project (Phase 11.2)
                  </span>
                  <span className="text-[10px] bg-slate-200 text-slate-800 font-bold px-2 py-0.5 rounded">
                    {evaluation.integrations.portfolio_project.difficulty}
                  </span>
                </div>
                <div className="text-xs text-slate-800 font-bold">
                  {evaluation.integrations.portfolio_project.title}
                </div>
                <p className="text-[11px] text-slate-600 leading-relaxed">
                  {evaluation.integrations.portfolio_project.rationale}
                </p>
              </div>
            )}
          </div>

          {/* Question-by-Question Detail Accordion */}
          <div className="space-y-3">
            <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
              Detailed Question Analysis ({evaluation.question_results?.length || 0})
            </h4>

            {evaluation.question_results?.map((qr, idx) => {
              const isExpanded = expandedQId === qr.question_id;
              return (
                <div
                  key={qr.question_id}
                  className="bg-white rounded-xl border border-slate-200 overflow-hidden"
                >
                  <button
                    onClick={() => setExpandedQId(isExpanded ? null : qr.question_id)}
                    className="w-full p-4 text-left flex items-center justify-between gap-4 hover:bg-slate-50/70 transition"
                  >
                    <div className="flex items-center gap-3">
                      <span className="text-xs font-extrabold px-2 py-0.5 rounded bg-slate-100 text-slate-700">
                        Q{idx + 1}
                      </span>
                      <div>
                        <span className="text-xs font-bold text-slate-900 block line-clamp-1">
                          {qr.question_text}
                        </span>
                        <span className="text-[11px] text-slate-500">
                          {qr.competency} • {qr.category} ({qr.difficulty})
                        </span>
                      </div>
                    </div>

                    <div className="flex items-center gap-3 shrink-0">
                      <span className={`text-xs font-black ${
                        qr.score >= 70 ? 'text-emerald-600' : qr.score >= 50 ? 'text-amber-600' : 'text-rose-600'
                      }`}>
                        {qr.score}%
                      </span>
                      {isExpanded ? (
                        <ChevronUp className="w-4 h-4 text-slate-400" />
                      ) : (
                        <ChevronDown className="w-4 h-4 text-slate-400" />
                      )}
                    </div>
                  </button>

                  {isExpanded && (
                    <div className="p-4 pt-0 border-t border-slate-100 space-y-3 bg-slate-50/40 text-xs">
                      {/* Student response */}
                      <div className="bg-white p-3 rounded-lg border border-slate-200">
                        <span className="text-[10px] font-bold text-slate-400 uppercase block mb-1">
                          Submitted Response:
                        </span>
                        <p className="text-slate-800 leading-relaxed italic">
                          "{qr.user_answer || '<No response provided>'}"
                        </p>
                      </div>

                      {/* Concepts breakdown */}
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                        <div className="p-2.5 bg-emerald-50/60 rounded-lg border border-emerald-100">
                          <span className="text-[10px] font-bold text-emerald-800 uppercase block mb-1">
                            Demonstrated Concepts ({qr.matched_concepts?.length || 0}):
                          </span>
                          <div className="flex flex-wrap gap-1">
                            {qr.matched_concepts?.map((c, cIdx) => (
                              <span key={cIdx} className="px-1.5 py-0.5 bg-white text-emerald-700 rounded text-[10px] font-bold border border-emerald-200">
                                {c}
                              </span>
                            ))}
                            {(!qr.matched_concepts || qr.matched_concepts.length === 0) && (
                              <span className="text-slate-400 italic text-[11px]">None identified</span>
                            )}
                          </div>
                        </div>

                        <div className="p-2.5 bg-rose-50/60 rounded-lg border border-rose-100">
                          <span className="text-[10px] font-bold text-rose-800 uppercase block mb-1">
                            Missing Key Concepts ({qr.missing_concepts?.length || 0}):
                          </span>
                          <div className="flex flex-wrap gap-1">
                            {qr.missing_concepts?.map((c, cIdx) => (
                              <span key={cIdx} className="px-1.5 py-0.5 bg-white text-rose-700 rounded text-[10px] font-bold border border-rose-200">
                                {c}
                              </span>
                            ))}
                            {(!qr.missing_concepts || qr.missing_concepts.length === 0) && (
                              <span className="text-emerald-600 font-bold text-[11px]">Full concept coverage!</span>
                            )}
                          </div>
                        </div>
                      </div>

                      {/* Feedback */}
                      <div className="p-3 bg-white rounded-lg border border-slate-200 text-slate-700">
                        <span className="font-bold text-slate-900 block mb-0.5">Examiner Feedback:</span>
                        {qr.feedback}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {/* Mandatory Provenance & Research Disclaimers */}
          <div className="p-3.5 bg-slate-100 rounded-xl text-[11px] text-slate-600 border border-slate-200 space-y-1">
            <div className="flex items-center gap-1.5 font-bold text-slate-700">
              <ShieldCheck className="w-3.5 h-3.5 text-slate-500" />
              Provenance & Methodology Notice:
            </div>
            <div>{evaluation.provenance}</div>
            <div className="text-[10px] text-slate-500">{evaluation.assessment_disclaimer}</div>
          </div>
        </div>
      )}
    </div>
  );
}
export default CareerInterviewSimulator;
