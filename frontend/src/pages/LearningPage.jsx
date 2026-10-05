import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { api } from '../services/api';
import { Spinner, Alert } from '../components/common/UIFeedback';
import { Badge } from '../components/common/Badge';
import { ProgressBar } from '../components/common/ProgressBar';
import {
  BookOpen,
  Search,
  ExternalLink,
  Play,
  CheckCircle,
  Clock,
  Award,
  Edit3,
  CheckCircle2,
  X,
} from 'lucide-react';

export function LearningPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const initialSkillId = searchParams.get('skill_id') || '';

  const [activeTab, setActiveTab] = useState('catalog'); // 'catalog' | 'my-learning'
  const [resources, setResources] = useState([]);
  const [userProgress, setUserProgress] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);

  // Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [difficultyFilter, setDifficultyFilter] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [skillFilter, setSkillFilter] = useState(initialSkillId);

  // Progress update modal state
  const [modalItem, setModalItem] = useState(null);
  const [modalPct, setModalPct] = useState(50);
  const [modalNotes, setModalNotes] = useState('');
  const [updatingProgress, setUpdatingProgress] = useState(false);

  useEffect(() => {
    loadCatalog();
    loadProgress();
  }, [difficultyFilter, typeFilter, skillFilter]);

  async function loadCatalog() {
    setLoading(true);
    setError(null);
    try {
      const params = {};
      if (difficultyFilter) params.difficulty = difficultyFilter;
      if (typeFilter) params.type = typeFilter;
      if (skillFilter) params.canonical_skill_id = skillFilter;
      if (searchQuery) params.q = searchQuery;

      const res = await api.listLearningResources(params);
      setResources(res?.resources || []);
    } catch (err) {
      console.warn('Could not load learning resources', err);
    } finally {
      setLoading(false);
    }
  }

  async function loadProgress() {
    try {
      const res = await api.getUserLearningProgress();
      setUserProgress(res?.progress_items || []);
    } catch (err) {
      console.warn('Could not load user progress', err);
    }
  }

  async function handleStartResource(resourceId) {
    setError(null);
    setSuccessMsg(null);
    try {
      await api.startLearningResource(resourceId);
      setSuccessMsg('Module enrolled! Added to your Active Pathways.');
      await loadProgress();
      setActiveTab('my-learning');
    } catch (err) {
      setError(err.message || 'Could not start resource');
    }
  }

  async function handleCompleteResource(resourceId) {
    setError(null);
    setSuccessMsg(null);
    try {
      const res = await api.completeLearningResource(resourceId);
      const boostInfo = res?.skill_boost ? ` (Proficiency boosted!)` : '';
      setSuccessMsg(`Resource completed successfully!${boostInfo}`);
      await loadProgress();
    } catch (err) {
      setError(err.message || 'Could not mark resource complete');
    }
  }

  async function handleSaveProgressModal(e) {
    e.preventDefault();
    if (!modalItem) return;
    setUpdatingProgress(true);
    try {
      await api.updateLearningProgress(modalItem.resource_id, modalPct, modalNotes);
      setSuccessMsg('Progress updated successfully.');
      setModalItem(null);
      await loadProgress();
    } catch (err) {
      setError(err.message || 'Failed to update progress');
    } finally {
      setUpdatingProgress(false);
    }
  }

  const filteredResources = resources.filter((r) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      r.title?.toLowerCase().includes(q) ||
      r.provider?.toLowerCase().includes(q) ||
      r.canonical_skill_name?.toLowerCase().includes(q)
    );
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-2xl p-6 md:p-8 shadow-sm border border-slate-200">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1.5">
              <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200">
                Curated Learning Ecosystem
              </span>
            </div>
            <h1 className="text-2xl md:text-3xl font-extrabold text-slate-900 tracking-tight">
              Learning Pathways & Progress
            </h1>
            <p className="text-slate-500 text-sm mt-1">
              Courses, tutorials, and certifications matched to canonical career skill gaps.
            </p>
          </div>

          {/* Tab Switcher */}
          <div className="flex bg-slate-100 p-1 rounded-xl">
            <button
              onClick={() => setActiveTab('catalog')}
              className={`px-4 py-2 rounded-lg text-xs font-bold transition ${
                activeTab === 'catalog'
                  ? 'bg-white text-slate-900 shadow-sm'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Curated Catalog ({filteredResources.length})
            </button>
            <button
              onClick={() => setActiveTab('my-learning')}
              className={`px-4 py-2 rounded-lg text-xs font-bold transition ${
                activeTab === 'my-learning'
                  ? 'bg-white text-slate-900 shadow-sm'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              My Pathways ({userProgress.length})
            </button>
          </div>
        </div>
      </div>

      {error && <Alert type="error" message={error} />}
      {successMsg && <Alert type="success" message={successMsg} />}

      {/* TAB 1: Curated Catalog */}
      {activeTab === 'catalog' && (
        <div className="space-y-6">
          {/* Filters Bar */}
          <div className="bg-white p-4 rounded-2xl border border-slate-200 flex flex-col md:flex-row gap-3">
            <div className="relative flex-1">
              <Search className="w-4 h-4 absolute left-3.5 top-3.5 text-slate-400" />
              <input
                type="text"
                placeholder="Search modules by title, provider, or skill..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500 text-sm bg-slate-50 focus:bg-white transition"
              />
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <select
                value={difficultyFilter}
                onChange={(e) => setDifficultyFilter(e.target.value)}
                className="px-3 py-2 rounded-xl border border-slate-200 bg-slate-50 text-xs font-medium text-slate-700"
              >
                <option value="">All Difficulties</option>
                <option value="Beginner">Beginner</option>
                <option value="Intermediate">Intermediate</option>
                <option value="Advanced">Advanced</option>
              </select>

              <select
                value={typeFilter}
                onChange={(e) => setTypeFilter(e.target.value)}
                className="px-3 py-2 rounded-xl border border-slate-200 bg-slate-50 text-xs font-medium text-slate-700"
              >
                <option value="">All Types</option>
                <option value="Course">Course</option>
                <option value="Tutorial">Tutorial</option>
                <option value="Certification">Certification</option>
                <option value="Project">Project</option>
                <option value="Documentation">Documentation</option>
              </select>

              {skillFilter && (
                <button
                  onClick={() => {
                    setSkillFilter('');
                    setSearchParams({});
                  }}
                  className="px-3 py-2 rounded-xl bg-slate-200 text-slate-700 text-xs font-semibold flex items-center gap-1"
                >
                  Clear Skill Filter <X className="w-3.5 h-3.5" />
                </button>
              )}
            </div>
          </div>

          {/* Resources Grid */}
          {loading ? (
            <div className="flex flex-col items-center justify-center py-16">
              <Spinner size="lg" />
              <p className="mt-3 text-slate-500 text-sm">Loading curated resources...</p>
            </div>
          ) : filteredResources.length === 0 ? (
            <div className="bg-white rounded-2xl p-12 text-center border border-slate-200">
              <BookOpen className="w-10 h-10 text-slate-300 mx-auto mb-3" />
              <h3 className="text-base font-bold text-slate-800">No resources matched</h3>
              <p className="text-xs text-slate-500 mt-1">Try resetting your search or filters.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {filteredResources.map((res) => {
                const inProgressItem = userProgress.find((p) => p.resource_id === res.id);
                const isEnrolled = !!inProgressItem;
                const isCompleted = inProgressItem?.status === 'Completed';

                return (
                  <div
                    key={res.id}
                    className="bg-white rounded-2xl border border-slate-200 hover:border-slate-300 hover:shadow-md transition flex flex-col justify-between"
                  >
                    <div className="p-6">
                      <div className="flex items-start justify-between gap-2 mb-3">
                        <span className="text-[11px] font-bold px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-700">
                          {res.provider || 'Online Course'}
                        </span>
                        <div className="flex items-center gap-1.5">
                          {res.has_certification && (
                            <span
                              title="Certification Included"
                              className="p-1 rounded-md bg-amber-50 text-amber-600"
                            >
                              <Award className="w-3.5 h-3.5" />
                            </span>
                          )}
                          <Badge
                            variant={
                              res.difficulty_level === 'Beginner'
                                ? 'success'
                                : res.difficulty_level === 'Intermediate'
                                ? 'info'
                                : 'warning'
                            }
                          >
                            {res.difficulty_level || 'All Levels'}
                          </Badge>
                        </div>
                      </div>

                      <h3 className="font-bold text-base text-slate-900 leading-snug line-clamp-2">
                        {res.title}
                      </h3>

                      <p className="text-xs text-slate-500 mt-2 line-clamp-3 leading-relaxed">
                        {res.description || 'Hands-on curriculum focused on real-world competencies.'}
                      </p>

                      <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
                        <span className="flex items-center gap-1">
                          <Clock className="w-3.5 h-3.5" />
                          {res.estimated_duration_hours || 10} hours
                        </span>
                        <span className="font-medium text-slate-700">
                          {res.canonical_skill_name}
                        </span>
                      </div>
                    </div>

                    <div className="p-4 bg-slate-50/70 border-t border-slate-100 rounded-b-2xl flex items-center justify-between">
                      {res.url ? (
                        <a
                          href={res.url}
                          target="_blank"
                          rel="noreferrer"
                          className="text-xs text-slate-500 hover:text-slate-800 font-medium flex items-center gap-1"
                        >
                          View Site <ExternalLink className="w-3 h-3" />
                        </a>
                      ) : (
                        <span />
                      )}

                      {isCompleted ? (
                        <span className="text-xs font-bold text-emerald-600 flex items-center gap-1">
                          <CheckCircle className="w-3.5 h-3.5" /> Completed
                        </span>
                      ) : isEnrolled ? (
                        <button
                          onClick={() => {
                            setModalItem(inProgressItem);
                            setModalPct(inProgressItem.progress_percentage || 0);
                            setModalNotes(inProgressItem.notes || '');
                          }}
                          className="px-3 py-1.5 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 text-xs font-semibold rounded-lg transition"
                        >
                          In Progress ({Math.round(inProgressItem.progress_percentage)}%)
                        </button>
                      ) : (
                        <button
                          onClick={() => handleStartResource(res.id)}
                          className="px-3.5 py-1.5 bg-primary-600 hover:bg-primary-700 text-white text-xs font-semibold rounded-lg shadow-sm transition flex items-center gap-1.5"
                        >
                          <Play className="w-3.5 h-3.5" />
                          <span>Start Learning</span>
                        </button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* TAB 2: My Pathways & Progress Tracking */}
      {activeTab === 'my-learning' && (
        <div className="space-y-6">
          <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200">
            <h2 className="text-base font-bold text-slate-900 mb-4">Enrolled Pathways</h2>

            {userProgress.length === 0 ? (
              <div className="py-12 text-center">
                <BookOpen className="w-10 h-10 text-slate-300 mx-auto mb-2" />
                <p className="text-sm font-semibold text-slate-700">No pathways enrolled</p>
                <p className="text-xs text-slate-500 mt-1 mb-4">
                  Enroll in resources from the catalog to track your progress and boost your skills.
                </p>
                <button
                  onClick={() => setActiveTab('catalog')}
                  className="px-4 py-2 bg-primary-600 text-white rounded-xl text-xs font-semibold"
                >
                  Browse Catalog
                </button>
              </div>
            ) : (
              <div className="space-y-4">
                {userProgress.map((item) => {
                  const isCompleted = item.status === 'Completed';

                  return (
                    <div
                      key={item.id}
                      className="p-5 rounded-2xl border border-slate-200 bg-slate-50/50 flex flex-col md:flex-row items-start md:items-center justify-between gap-4"
                    >
                      <div className="flex-1 space-y-2">
                        <div className="flex items-center gap-2">
                          <Badge variant={isCompleted ? 'success' : 'info'}>{item.status}</Badge>
                          <span className="text-xs text-slate-400">
                            {item.resource?.provider || 'Self-paced'}
                          </span>
                        </div>
                        <h4 className="font-bold text-base text-slate-900">
                          {item.resource?.title || 'Learning Resource'}
                        </h4>
                        <div className="w-full max-w-md">
                          <div className="flex justify-between text-xs text-slate-500 mb-1">
                            <span>Completion</span>
                            <span className="font-bold">
                              {Math.round(item.progress_percentage || 0)}%
                            </span>
                          </div>
                          <ProgressBar
                            value={item.progress_percentage || 0}
                            max={100}
                            color={isCompleted ? 'bg-emerald-500' : 'bg-primary-600'}
                          />
                        </div>
                        {item.notes && (
                          <p className="text-xs text-slate-600 italic">Notes: "{item.notes}"</p>
                        )}
                      </div>

                      <div className="flex items-center gap-2 shrink-0">
                        {!isCompleted && (
                          <>
                            <button
                              onClick={() => {
                                setModalItem(item);
                                setModalPct(item.progress_percentage || 0);
                                setModalNotes(item.notes || '');
                              }}
                              className="px-3 py-2 bg-white hover:bg-slate-100 text-slate-700 border border-slate-200 text-xs font-semibold rounded-xl transition flex items-center gap-1.5"
                            >
                              <Edit3 className="w-3.5 h-3.5" />
                              <span>Update</span>
                            </button>
                            <button
                              onClick={() => handleCompleteResource(item.resource_id)}
                              className="px-3.5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold rounded-xl shadow-sm transition flex items-center gap-1.5"
                            >
                              <CheckCircle2 className="w-3.5 h-3.5" />
                              <span>Complete & Boost</span>
                            </button>
                          </>
                        )}
                        {item.resource?.url && (
                          <a
                            href={item.resource.url}
                            target="_blank"
                            rel="noreferrer"
                            className="p-2 text-slate-400 hover:text-slate-700 transition"
                          >
                            <ExternalLink className="w-4 h-4" />
                          </a>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Progress Update Modal */}
      {modalItem && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl border border-slate-100 animate-fadeIn">
            <div className="flex justify-between items-center mb-4">
              <h3 className="font-bold text-base text-slate-900">Update Learning Progress</h3>
              <button
                onClick={() => setModalItem(null)}
                className="text-slate-400 hover:text-slate-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSaveProgressModal} className="space-y-4">
              <div>
                <p className="text-xs text-slate-500 mb-2">
                  Module: <b>{modalItem.resource?.title}</b>
                </p>
                <div className="flex justify-between text-xs font-semibold text-slate-700 mb-1">
                  <span>Progress</span>
                  <span>{modalPct}%</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={modalPct}
                  onChange={(e) => setModalPct(Number(e.target.value))}
                  className="w-full accent-primary-600 cursor-pointer h-2 bg-slate-200 rounded-lg appearance-none"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Learning Notes (Optional)
                </label>
                <textarea
                  rows={3}
                  value={modalNotes}
                  onChange={(e) => setModalNotes(e.target.value)}
                  placeholder="e.g. Finished chapter 4 exercises..."
                  className="w-full p-3 rounded-xl border border-slate-200 text-xs focus:ring-primary-500 focus:border-primary-500"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setModalItem(null)}
                  className="px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-xl"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={updatingProgress}
                  className="px-4 py-2 text-xs font-semibold bg-primary-600 hover:bg-primary-700 text-white rounded-xl shadow-sm"
                >
                  {updatingProgress ? 'Saving...' : 'Save Progress'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
