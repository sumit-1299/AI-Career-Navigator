import React, { useState, useEffect, useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  CheckSquare,
  Code2,
  BookOpen,
  HelpCircle,
  ChevronDown,
  ChevronUp,
  Sparkles,
  AlertCircle,
  CheckCircle2,
  Clock,
  Send,
  RotateCcw,
  Layers,
  ArrowRight,
  ShieldAlert,
  Flame,
  Search,
  Filter,
} from 'lucide-react';
import { api } from '../../services/api';

const CAREERS_LIST = [
  { id: 1, title: 'Software Developer' },
  { id: 2, title: 'Web Developer' },
  { id: 3, title: 'Data Analyst' },
  { id: 4, title: 'Data Scientist' },
  { id: 5, title: 'AI/ML Engineer' },
  { id: 6, title: 'Cloud Engineer' },
  { id: 7, title: 'DevOps Engineer' },
  { id: 8, title: 'Cybersecurity Analyst' },
  { id: 9, title: 'Network Engineer' },
  { id: 10, title: 'Database Administrator' },
];

const DIFFICULTY_COLORS = {
  BEGINNER: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  INTERMEDIATE: 'bg-blue-50 text-blue-700 border-blue-200',
  ADVANCED: 'bg-purple-50 text-purple-700 border-purple-200',
};

const BAND_STYLES = {
  STRONG_PRACTICAL_MASTERY: {
    bg: 'bg-emerald-50 text-emerald-800 border-emerald-300',
    bar: 'bg-emerald-500',
    label: 'Strong Practical Mastery',
  },
  PRACTICE_READY: {
    bg: 'bg-blue-50 text-blue-800 border-blue-300',
    bar: 'bg-blue-500',
    label: 'Practice Ready',
  },
  NEEDS_REINFORCEMENT: {
    bg: 'bg-amber-50 text-amber-800 border-amber-300',
    bar: 'bg-amber-500',
    label: 'Needs Reinforcement',
  },
  FOUNDATION_REQUIRED: {
    bg: 'bg-rose-50 text-rose-800 border-rose-300',
    bar: 'bg-rose-500',
    label: 'Foundation Required',
  },
};

export function PracticalTaskExplorer() {
  const [searchParams, setSearchParams] = useSearchParams();
  const initialCareerId = searchParams.get('career_id') ? parseInt(searchParams.get('career_id'), 10) : 1;
  const initialSkill = searchParams.get('skill') || '';

  const [selectedCareerId, setSelectedCareerId] = useState(initialCareerId);
  const [selectedDifficulty, setSelectedDifficulty] = useState('ALL');
  const [selectedCategory, setSelectedCategory] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState(initialSkill);

  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [activeTask, setActiveTask] = useState(null);
  const [answerText, setAnswerText] = useState('');
  const [hintsExpanded, setHintsExpanded] = useState(false);

  const [submitting, setSubmitting] = useState(false);
  const [evaluationResult, setEvaluationResult] = useState(null);
  const [evalError, setEvalError] = useState(null);

  // Fetch tasks when filters change
  useEffect(() => {
    async function loadTasks() {
      setLoading(true);
      setError(null);
      try {
        const params = {};
        if (selectedCareerId) params.career_id = selectedCareerId;
        if (selectedDifficulty !== 'ALL') params.difficulty = selectedDifficulty;
        if (selectedCategory !== 'ALL') params.category = selectedCategory;
        if (searchQuery.trim()) params.skill = searchQuery.trim();

        const response = await api.listPracticalTasks(params);
        if (response && response.tasks) {
          setTasks(response.tasks);
          if (response.tasks.length > 0) {
            // Keep current active task if still present, or pick first
            const found = response.tasks.find((t) => activeTask && t.id === activeTask.id);
            setActiveTask(found || response.tasks[0]);
          } else {
            setActiveTask(null);
          }
        }
      } catch (err) {
        setError(err.message || 'Failed to load practical tasks.');
      } finally {
        setLoading(false);
      }
    }

    loadTasks();
  }, [selectedCareerId, selectedDifficulty, selectedCategory, searchQuery]);

  // Reset evaluation state when active task switches
  function handleSelectTask(task) {
    setActiveTask(task);
    setAnswerText('');
    setEvaluationResult(null);
    setEvalError(null);
    setHintsExpanded(false);
  }

  // Insert structured scaffold template
  function handleInsertScaffold() {
    if (!activeTask) return;
    const scaffold = `### 1. Technical Approach & Design
- Concept alignment:
- Strategy for handling requirements:

### 2. Implementation / Solution Steps
\`\`\`
// Provide your technical solution or implementation details here
\`\`\`

### 3. Edge Cases & Rationale
- Error handling / validation considerations:
- Expected outcome verification:`;
    setAnswerText(scaffold);
  }

  // Submit answer for evaluation
  async function handleSubmitEvaluation(e) {
    e.preventDefault();
    if (!activeTask || !answerText.trim()) return;

    setSubmitting(true);
    setEvalError(null);
    try {
      const response = await api.evaluatePracticalTask({
        task_id: activeTask.id,
        answer: answerText,
      });
      if (response && response.status === 'success') {
        setEvaluationResult(response);
      } else {
        setEvalError(response?.message || 'Evaluation failed. Please try again.');
      }
    } catch (err) {
      setEvalError(err.message || 'An error occurred during task evaluation.');
    } finally {
      setSubmitting(false);
    }
  }

  // Switch to recommended next task
  function handleSwitchToNextTask(nextTaskId) {
    const target = tasks.find((t) => t.id === nextTaskId);
    if (target) {
      handleSelectTask(target);
    } else {
      // Fetch specifically if not in current list
      api.getPracticalTask(nextTaskId).then((res) => {
        if (res && res.task) {
          handleSelectTask(res.task);
        }
      });
    }
  }

  return (
    <div className="space-y-6 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      {/* 1. Header Banner */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2.5">
              <div className="p-2 bg-primary-50 rounded-xl text-primary-600">
                <CheckSquare className="w-6 h-6" />
              </div>
              <h1 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">
                Practical Skill Assessment & Hands-On Task Engine
              </h1>
            </div>
            <p className="text-sm text-slate-500 max-w-3xl">
              Practice real-world engineering tasks tailored to your target career track, active skill gaps,
              and live vacancy requirements. Deterministic evaluation provides explainable feedback and skill evidence.
            </p>
          </div>

          <div className="shrink-0 flex items-center gap-2 bg-amber-50 border border-amber-200 rounded-xl px-3.5 py-2 text-amber-800 text-xs font-medium">
            <ShieldAlert className="w-4 h-4 text-amber-600 shrink-0" />
            <span>Deterministic Educational Practice</span>
          </div>
        </div>

        {/* Advisory Disclaimer */}
        <div className="mt-4 pt-3 border-t border-slate-100 flex items-center gap-2 text-xs text-slate-400 italic">
          <AlertCircle className="w-3.5 h-3.5 shrink-0 text-slate-400" />
          <span>
            Notice: Practical task scores reflect educational technical alignment and do not represent employment probability,
            interview guarantees, or hiring predictions.
          </span>
        </div>
      </div>

      {/* 2. Controls & Filter Bar */}
      <div className="bg-white border border-slate-200 rounded-2xl p-4 shadow-xs grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5">
        {/* Career Selector */}
        <div>
          <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
            Career Track
          </label>
          <select
            value={selectedCareerId}
            onChange={(e) => setSelectedCareerId(parseInt(e.target.value, 10))}
            className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-sm font-medium text-slate-800 focus:outline-hidden focus:ring-2 focus:ring-primary-500"
          >
            {CAREERS_LIST.map((c) => (
              <option key={c.id} value={c.id}>
                {c.id}. {c.title}
              </option>
            ))}
          </select>
        </div>

        {/* Difficulty Filter */}
        <div>
          <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
            Difficulty
          </label>
          <select
            value={selectedDifficulty}
            onChange={(e) => setSelectedDifficulty(e.target.value)}
            className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-sm font-medium text-slate-800 focus:outline-hidden focus:ring-2 focus:ring-primary-500"
          >
            <option value="ALL">All Levels</option>
            <option value="BEGINNER">Beginner</option>
            <option value="INTERMEDIATE">Intermediate</option>
            <option value="ADVANCED">Advanced</option>
          </select>
        </div>

        {/* Category Filter */}
        <div>
          <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
            Task Category
          </label>
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-sm font-medium text-slate-800 focus:outline-hidden focus:ring-2 focus:ring-primary-500"
          >
            <option value="ALL">All Categories</option>
            <option value="CODING">Coding</option>
            <option value="DATABASE">Database</option>
            <option value="API_DEVELOPMENT">API Development</option>
            <option value="DEBUGGING">Debugging</option>
            <option value="SYSTEM_DESIGN">System Design</option>
            <option value="CLOUD">Cloud</option>
            <option value="DEVOPS">DevOps</option>
            <option value="SECURITY">Security</option>
            <option value="DATA_ANALYSIS">Data Analysis</option>
            <option value="MACHINE_LEARNING">Machine Learning</option>
            <option value="NETWORKING">Networking</option>
          </select>
        </div>

        {/* Skill Filter / Search */}
        <div>
          <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
            Filter by Skill
          </label>
          <div className="relative">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="e.g. Python, Docker, SQL..."
              className="w-full bg-slate-50 border border-slate-200 rounded-xl pl-9 pr-3 py-2 text-sm font-medium text-slate-800 focus:outline-hidden focus:ring-2 focus:ring-primary-500"
            />
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
          </div>
        </div>
      </div>

      {/* 3. Main Workspace: Task List & Hands-on Workspace */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Task Catalog (5 Cols) */}
        <div className="lg:col-span-5 space-y-3">
          <div className="flex items-center justify-between px-1">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
              Available Tasks ({tasks.length})
            </span>
            <span className="text-xs text-slate-400">Prioritized by Skill ROI & Gaps</span>
          </div>

          {loading ? (
            <div className="bg-white border border-slate-200 rounded-2xl p-8 text-center text-slate-500 text-sm">
              Loading practical tasks...
            </div>
          ) : error ? (
            <div className="bg-rose-50 border border-rose-200 rounded-2xl p-4 text-rose-700 text-sm">
              {error}
            </div>
          ) : tasks.length === 0 ? (
            <div className="bg-white border border-slate-200 rounded-2xl p-8 text-center text-slate-500 text-sm">
              No tasks found matching the selected filters.
            </div>
          ) : (
            <div className="space-y-2.5 max-h-[800px] overflow-y-auto pr-1">
              {tasks.map((task) => {
                const isSelected = activeTask && activeTask.id === task.id;
                const diffColor = DIFFICULTY_COLORS[task.difficulty] || 'bg-slate-100 text-slate-700 border-slate-200';

                return (
                  <div
                    key={task.id}
                    onClick={() => handleSelectTask(task)}
                    className={`border rounded-2xl p-4 cursor-pointer transition-all duration-200 ${
                      isSelected
                        ? 'bg-primary-50/60 border-primary-500 ring-2 ring-primary-500/20 shadow-xs'
                        : 'bg-white border-slate-200 hover:border-slate-300 hover:bg-slate-50/50 shadow-2xs'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2 mb-1.5">
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded-md border uppercase ${diffColor}`}>
                        {task.difficulty}
                      </span>
                      <div className="flex items-center gap-1 text-[11px] text-slate-400 shrink-0 font-medium">
                        <Clock className="w-3 h-3" />
                        <span>~{task.estimated_minutes}m</span>
                      </div>
                    </div>

                    <h3 className="font-bold text-sm text-slate-900 leading-snug mb-1">
                      {task.title}
                    </h3>

                    <div className="flex flex-wrap items-center gap-1.5 mt-2">
                      <span className="px-2 py-0.5 bg-slate-100 text-slate-700 text-[11px] font-semibold rounded-md">
                        {task.skill}
                      </span>
                      <span className="px-2 py-0.5 bg-slate-100 text-slate-600 text-[11px] rounded-md">
                        {task.category}
                      </span>
                      {task.is_job_gap && (
                        <span className="px-2 py-0.5 bg-amber-100 text-amber-800 text-[11px] font-bold rounded-md flex items-center gap-1">
                          <Flame className="w-2.5 h-2.5" /> Job Gap
                        </span>
                      )}
                      {task.is_roi_priority && (
                        <span className="px-2 py-0.5 bg-emerald-100 text-emerald-800 text-[11px] font-bold rounded-md flex items-center gap-1">
                          <Sparkles className="w-2.5 h-2.5" /> High ROI
                        </span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Right Column: Active Task Workspace & Evaluation (7 Cols) */}
        <div className="lg:col-span-7 space-y-5">
          {activeTask ? (
            <>
              {/* Task Detail Card */}
              <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs space-y-4">
                <div className="flex flex-wrap items-center justify-between gap-2 pb-3 border-b border-slate-100">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-primary-600 bg-primary-50 px-2.5 py-1 rounded-lg">
                      {activeTask.career_title}
                    </span>
                    <span className="text-xs font-bold text-slate-700 bg-slate-100 px-2.5 py-1 rounded-lg">
                      {activeTask.skill}
                    </span>
                  </div>
                  <span className={`text-xs font-bold px-2.5 py-1 rounded-lg border uppercase ${DIFFICULTY_COLORS[activeTask.difficulty]}`}>
                    {activeTask.difficulty} • ~{activeTask.estimated_minutes} mins
                  </span>
                </div>

                <div>
                  <h2 className="text-lg font-bold text-slate-900 leading-tight">
                    {activeTask.title}
                  </h2>
                  <p className="text-xs text-slate-500 mt-1">
                    <strong>Objective:</strong> {activeTask.objective}
                  </p>
                </div>

                {/* Scenario */}
                <div className="bg-slate-50 border border-slate-200/80 rounded-xl p-3.5 space-y-1">
                  <span className="text-xs font-bold text-slate-800 uppercase tracking-wider block">
                    Scenario Context
                  </span>
                  <p className="text-xs text-slate-600 leading-relaxed">
                    {activeTask.scenario}
                  </p>
                </div>

                {/* Requirements */}
                <div className="space-y-2">
                  <span className="text-xs font-bold text-slate-800 uppercase tracking-wider block">
                    Task Requirements
                  </span>
                  <ul className="space-y-1.5">
                    {activeTask.requirements?.map((req, idx) => (
                      <li key={idx} className="flex items-start gap-2 text-xs text-slate-700">
                        <span className="w-4 h-4 rounded-full bg-slate-100 text-slate-600 font-bold flex items-center justify-center shrink-0 mt-0.5 text-[10px]">
                          {idx + 1}
                        </span>
                        <span>{req}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Expected Concepts */}
                <div>
                  <span className="text-xs font-bold text-slate-800 uppercase tracking-wider block mb-1.5">
                    Expected Core Concepts
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    {activeTask.expected_concepts?.map((c) => (
                      <span key={c} className="px-2 py-0.5 bg-slate-100 text-slate-700 text-xs rounded-md font-medium">
                        {c}
                      </span>
                    ))}
                  </div>
                </div>

                {/* Hints Accordion */}
                {activeTask.hints?.length > 0 && (
                  <div className="border border-slate-200 rounded-xl overflow-hidden">
                    <button
                      type="button"
                      onClick={() => setHintsExpanded(!hintsExpanded)}
                      className="w-full flex items-center justify-between px-3.5 py-2.5 bg-slate-50 text-xs font-bold text-slate-700 hover:bg-slate-100 transition"
                    >
                      <span className="flex items-center gap-1.5">
                        <HelpCircle className="w-3.5 h-3.5 text-amber-500" />
                        Progressive Technical Hints ({activeTask.hints.length})
                      </span>
                      {hintsExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                    </button>
                    {hintsExpanded && (
                      <div className="p-3.5 bg-white space-y-2 text-xs text-slate-600">
                        {activeTask.hints.map((hint, i) => (
                          <div key={i} className="flex items-start gap-2">
                            <span className="font-bold text-amber-600">Hint {i + 1}:</span>
                            <span>{hint}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Response Submission Card */}
              <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Code2 className="w-5 h-5 text-primary-600" />
                    <h3 className="text-sm font-bold text-slate-900">Your Technical Solution</h3>
                  </div>
                  <button
                    type="button"
                    onClick={handleInsertScaffold}
                    className="text-xs font-semibold text-primary-600 hover:text-primary-700 flex items-center gap-1"
                  >
                    <Layers className="w-3.5 h-3.5" />
                    Insert Response Scaffold
                  </button>
                </div>

                <form onSubmit={handleSubmitEvaluation} className="space-y-4">
                  <div>
                    <textarea
                      rows={10}
                      value={answerText}
                      onChange={(e) => setAnswerText(e.target.value)}
                      placeholder="Write your technical explanation, implementation code, or step-by-step design here..."
                      className="w-full font-mono text-xs sm:text-sm bg-slate-50 border border-slate-200 rounded-xl p-3.5 text-slate-800 focus:outline-hidden focus:ring-2 focus:ring-primary-500 focus:bg-white transition"
                    />
                    <div className="flex items-center justify-between text-xs text-slate-400 mt-1">
                      <span>{answerText.trim().split(/\s+/).filter(Boolean).length} words</span>
                      <span>Evaluates concept coverage, requirements, criteria, completeness, and structure</span>
                    </div>
                  </div>

                  {evalError && (
                    <div className="bg-rose-50 border border-rose-200 rounded-xl p-3 text-xs text-rose-700 font-medium">
                      {evalError}
                    </div>
                  )}

                  <div className="flex items-center justify-end gap-2.5 pt-1">
                    <button
                      type="button"
                      onClick={() => setAnswerText('')}
                      className="px-3.5 py-2 text-xs font-medium text-slate-600 hover:text-slate-800 transition"
                    >
                      Clear
                    </button>
                    <button
                      type="submit"
                      disabled={submitting || !answerText.trim()}
                      className="px-5 py-2.5 bg-primary-600 hover:bg-primary-700 text-white rounded-xl text-xs font-bold shadow-md shadow-primary-500/20 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1.5 transition"
                    >
                      {submitting ? (
                        <>Evaluating Submission...</>
                      ) : (
                        <>
                          <Send className="w-3.5 h-3.5" />
                          Submit Practical Evaluation
                        </>
                      )}
                    </button>
                  </div>
                </form>
              </div>

              {/* Evaluation Result Display */}
              {evaluationResult && evaluationResult.evaluation && (
                <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-5 animate-in fade-in duration-300">
                  <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                    <div>
                      <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                        Evaluation Results
                      </span>
                      <h3 className="text-lg font-bold text-slate-900">
                        {evaluationResult.task.title}
                      </h3>
                    </div>

                    <div className="text-right">
                      <div className="text-2xl font-black text-slate-900">
                        {evaluationResult.evaluation.practical_score}
                        <span className="text-sm font-semibold text-slate-400"> / 100</span>
                      </div>
                      <span
                        className={`inline-block text-[11px] font-bold px-2 py-0.5 rounded-md border ${
                          BAND_STYLES[evaluationResult.evaluation.band]?.bg || 'bg-slate-100 text-slate-700'
                        }`}
                      >
                        {evaluationResult.evaluation.band_label}
                      </span>
                    </div>
                  </div>

                  {/* 5-Metric Breakdown */}
                  <div className="grid grid-cols-2 sm:grid-cols-5 gap-2.5 text-center">
                    <div className="bg-slate-50 border border-slate-100 rounded-xl p-2.5">
                      <span className="text-[10px] text-slate-500 font-bold uppercase block">Concepts (40%)</span>
                      <span className="text-sm font-extrabold text-slate-800">
                        {evaluationResult.evaluation.concept_coverage}%
                      </span>
                    </div>
                    <div className="bg-slate-50 border border-slate-100 rounded-xl p-2.5">
                      <span className="text-[10px] text-slate-500 font-bold uppercase block">Requirements (25%)</span>
                      <span className="text-sm font-extrabold text-slate-800">
                        {evaluationResult.evaluation.requirement_coverage}%
                      </span>
                    </div>
                    <div className="bg-slate-50 border border-slate-100 rounded-xl p-2.5">
                      <span className="text-[10px] text-slate-500 font-bold uppercase block">Criteria (20%)</span>
                      <span className="text-sm font-extrabold text-slate-800">
                        {evaluationResult.evaluation.criteria_coverage}%
                      </span>
                    </div>
                    <div className="bg-slate-50 border border-slate-100 rounded-xl p-2.5">
                      <span className="text-[10px] text-slate-500 font-bold uppercase block">Completeness (10%)</span>
                      <span className="text-sm font-extrabold text-slate-800">
                        {evaluationResult.evaluation.completeness}%
                      </span>
                    </div>
                    <div className="bg-slate-50 border border-slate-100 rounded-xl p-2.5 col-span-2 sm:col-span-1">
                      <span className="text-[10px] text-slate-500 font-bold uppercase block">Structure (5%)</span>
                      <span className="text-sm font-extrabold text-slate-800">
                        {evaluationResult.evaluation.structure}%
                      </span>
                    </div>
                  </div>

                  {/* Matched vs Missing Concepts */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div className="bg-emerald-50/50 border border-emerald-200 rounded-xl p-3.5 space-y-2">
                      <div className="flex items-center gap-1.5 text-xs font-bold text-emerald-800">
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                        <span>Matched Concepts ({evaluationResult.evaluation.matched_concepts.length})</span>
                      </div>
                      <div className="flex flex-wrap gap-1">
                        {evaluationResult.evaluation.matched_concepts.map((c) => (
                          <span key={c} className="px-2 py-0.5 bg-white border border-emerald-200 text-emerald-800 text-xs rounded-md">
                            {c}
                          </span>
                        ))}
                      </div>
                    </div>

                    <div className="bg-amber-50/50 border border-amber-200 rounded-xl p-3.5 space-y-2">
                      <div className="flex items-center gap-1.5 text-xs font-bold text-amber-800">
                        <AlertCircle className="w-3.5 h-3.5 text-amber-600" />
                        <span>Missing Concepts ({evaluationResult.evaluation.missing_concepts.length})</span>
                      </div>
                      <div className="flex flex-wrap gap-1">
                        {evaluationResult.evaluation.missing_concepts.length > 0 ? (
                          evaluationResult.evaluation.missing_concepts.map((c) => (
                            <span key={c} className="px-2 py-0.5 bg-white border border-amber-200 text-amber-800 text-xs rounded-md">
                              {c}
                            </span>
                          ))
                        ) : (
                          <span className="text-xs text-emerald-700 font-medium">All core concepts addressed!</span>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Skill Evidence Summary */}
                  {evaluationResult.skill_evidence && (
                    <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                          Skill Evidence Generated
                        </span>
                        <span className="px-2 py-0.5 bg-primary-100 text-primary-800 text-xs font-bold rounded-md">
                          Evidence: {evaluationResult.skill_evidence.evidence_strength}
                        </span>
                      </div>
                      <p className="text-xs text-slate-600">
                        Demonstrated practical capability for <strong>{evaluationResult.skill_evidence.demonstrated_skill}</strong> with score <strong>{evaluationResult.skill_evidence.practical_score}%</strong> ({evaluationResult.skill_evidence.difficulty} level).
                      </p>
                    </div>
                  )}

                  {/* Remaining Gaps */}
                  {evaluationResult.remaining_gaps?.length > 0 && (
                    <div className="space-y-1.5">
                      <span className="text-xs font-bold text-slate-700 uppercase tracking-wider block">
                        Areas to Reinforce
                      </span>
                      <ul className="space-y-1">
                        {evaluationResult.remaining_gaps.map((gap, idx) => (
                          <li key={idx} className="text-xs text-slate-600 flex items-start gap-2">
                            <span className="text-amber-500 font-bold">•</span>
                            <span>{gap}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Recommended Next Task */}
                  {evaluationResult.recommended_next_task && (
                    <div className="bg-primary-50/50 border border-primary-200 rounded-xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                      <div className="space-y-0.5">
                        <span className="text-[11px] font-bold text-primary-700 uppercase tracking-wider block">
                          Recommended Next Task
                        </span>
                        <h4 className="font-bold text-sm text-slate-900">
                          {evaluationResult.recommended_next_task.title}
                        </h4>
                        <p className="text-xs text-slate-600">
                          {evaluationResult.recommended_next_task.recommendation_reason}
                        </p>
                      </div>

                      <button
                        type="button"
                        onClick={() => handleSwitchToNextTask(evaluationResult.recommended_next_task.id)}
                        className="px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-xl text-xs font-bold shrink-0 flex items-center gap-1.5 transition shadow-xs"
                      >
                        <span>Start Task</span>
                        <ArrowRight className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  )}
                </div>
              )}
            </>
          ) : (
            <div className="bg-white border border-slate-200 rounded-2xl p-12 text-center text-slate-400">
              Select a task from the catalog to begin your practical assessment.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default PracticalTaskExplorer;
