import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { api } from '../services/api';
import { Spinner, Alert, EmptyState } from '../components/common/UIFeedback';
import { Badge } from '../components/common/Badge';
import { ProgressBar } from '../components/common/ProgressBar';
import { Card } from '../components/common/Card';
import { SectionHeader } from '../components/common/SectionHeader';
import { Tabs } from '../components/common/Tabs';
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
  Compass,
  Filter,
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
      const resId = modalItem.resource_id || modalItem.learning_resource_id || modalItem.resource?.id;
      await api.updateLearningProgress(resId, modalPct, modalNotes);
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

  const tabItems = [
    { id: 'catalog', label: 'Curated Catalog', count: filteredResources.length },
    { id: 'my-learning', label: 'My Pathways', count: userProgress.length },
  ];

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Modernized Header */}
      <SectionHeader
        badge="Curated Learning Ecosystem"
        title="Learning Pathways & Progress"
        subtitle="Courses, tutorials, and certifications matched to canonical career skill gaps."
        action={
          <Tabs
            tabs={tabItems}
            activeTab={activeTab}
            onChange={setActiveTab}
          />
        }
      />

      {error && <Alert type="error" message={error} onClose={() => setError(null)} />}
      {successMsg && <Alert type="success" message={successMsg} onClose={() => setSuccessMsg(null)} />}

      {/* TAB 1: Curated Catalog */}
      {activeTab === 'catalog' && (
        <div className="space-y-6">
          {/* Filters Bar */}
          <Card className="p-4 shadow-card">
            <div className="flex flex-col md:flex-row gap-3">
              <div className="relative flex-1">
                <Search className="w-4 h-4 absolute left-3.5 top-3.5 text-slate-400" />
                <input
                  type="text"
                  placeholder="Search modules by title, provider, or skill keyword..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500 text-sm bg-slate-50/50 focus:bg-white transition"
                />
              </div>

              <div className="flex flex-wrap items-center gap-2">
                <select
                  value={difficultyFilter}
                  onChange={(e) => setDifficultyFilter(e.target.value)}
                  className="px-3.5 py-2.5 rounded-xl border border-slate-200 bg-slate-50 text-xs font-semibold text-slate-700 hover:border-slate-300 transition"
                >
                  <option value="">All Difficulties</option>
                  <option value="Beginner">Beginner</option>
                  <option value="Intermediate">Intermediate</option>
                  <option value="Advanced">Advanced</option>
                </select>

                <select
                  value={typeFilter}
                  onChange={(e) => setTypeFilter(e.target.value)}
                  className="px-3.5 py-2.5 rounded-xl border border-slate-200 bg-slate-50 text-xs font-semibold text-slate-700 hover:border-slate-300 transition"
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
                    className="px-3.5 py-2.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold flex items-center gap-1.5 transition"
                  >
                    <span>Clear Skill Filter</span>
                    <X className="w-3.5 h-3.5" />
                  </button>
                )}
              </div>
            </div>
          </Card>

          {/* Resources Grid */}
          {loading ? (
            <div className="flex flex-col items-center justify-center py-16">
              <Spinner size="lg" />
              <p className="mt-3 text-slate-500 text-sm font-medium">Loading curated resources...</p>
            </div>
          ) : filteredResources.length === 0 ? (
            <EmptyState
              icon={BookOpen}
              title="No resources matched"
              message="Try adjusting your search keywords or resetting the difficulty and type filters."
            />
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {filteredResources.map((res) => {
                const inProgressItem = userProgress.find((p) => (p.resource_id || p.learning_resource_id || p.resource?.id) === res.id);
                const isEnrolled = !!inProgressItem;
                const isCompleted = inProgressItem?.status === 'Completed';

                return (
                  <div
                    key={res.id}
                    className="bg-white rounded-2xl border border-slate-200/90 shadow-subtle hover:border-primary-300 hover:shadow-card transition-all flex flex-col justify-between"
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
                              className="p-1 rounded-md bg-amber-50 text-amber-600 border border-amber-200/60"
                            >
                              <Award className="w-3.5 h-3.5" />
                            </span>
                          )}
                          <Badge
                            variant={
                              res.difficulty_level === 'Beginner'
                                ? 'success'
                                : res.difficulty_level === 'Intermediate'
                                ? 'primary'
                                : 'warning'
                            }
                            size="sm"
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
                        <span className="flex items-center gap-1.5">
                          <Clock className="w-3.5 h-3.5 text-slate-400" />
                          <span>{res.estimated_duration_hours || 10} hours</span>
                        </span>
                        <span className="font-medium text-slate-700 bg-slate-50 px-2 py-0.5 rounded border border-slate-100">
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
                          className="text-xs text-slate-500 hover:text-slate-800 font-medium flex items-center gap-1 transition"
                        >
                          <span>View Course</span>
                          <ExternalLink className="w-3 h-3" />
                        </a>
                      ) : (
                        <span />
                      )}

                      {isCompleted ? (
                        <span className="text-xs font-bold text-emerald-600 flex items-center gap-1.5 bg-emerald-50 px-2.5 py-1 rounded-lg border border-emerald-200">
                          <CheckCircle className="w-3.5 h-3.5" /> Completed
                        </span>
                      ) : isEnrolled ? (
                        <button
                          onClick={() => {
                            setModalItem(inProgressItem);
                            setModalPct(inProgressItem.progress_percentage || 0);
                            setModalNotes(inProgressItem.notes || '');
                          }}
                          className="px-3.5 py-1.5 bg-primary-50 hover:bg-primary-100 text-primary-700 text-xs font-bold rounded-lg border border-primary-200 transition"
                        >
                          In Progress ({Math.round(inProgressItem.progress_percentage)}%)
                        </button>
                      ) : (
                        <button
                          onClick={() => handleStartResource(res.id)}
                          className="px-3.5 py-1.5 bg-primary-600 hover:bg-primary-700 text-white text-xs font-bold rounded-lg shadow-subtle hover:shadow transition flex items-center gap-1.5"
                        >
                          <Play className="w-3.5 h-3.5 fill-current" />
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
          <Card className="p-6 md:p-7 shadow-card">
            <div className="flex items-center justify-between mb-5 pb-4 border-b border-slate-100">
              <div>
                <h2 className="text-base font-bold text-slate-900">Enrolled Learning Pathways</h2>
                <p className="text-xs text-slate-500">Track your completion and skill boost milestones</p>
              </div>
              <Badge variant="primary" size="md">
                {userProgress.length} Active Pathways
              </Badge>
            </div>

            {userProgress.length === 0 ? (
              <EmptyState
                icon={BookOpen}
                title="No pathways enrolled yet"
                message="Enroll in resources from the catalog to track your progress and boost your verified skills."
                action={
                  <button
                    onClick={() => setActiveTab('catalog')}
                    className="px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-xl text-xs font-semibold shadow-subtle transition"
                  >
                    Browse Catalog
                  </button>
                }
              />
            ) : (
              <div className="space-y-4">
                {userProgress.map((item) => {
                  const isCompleted = item.status === 'Completed';

                  return (
                    <div
                      key={item.id}
                      className="p-5 rounded-2xl border border-slate-200/90 bg-white hover:border-primary-200 hover:shadow-subtle transition flex flex-col md:flex-row items-start md:items-center justify-between gap-4"
                    >
                      <div className="flex-1 space-y-2">
                        <div className="flex items-center gap-2">
                          <Badge variant={isCompleted ? 'success' : 'primary'} size="sm">
                            {item.status}
                          </Badge>
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
                            <span className="font-bold text-slate-800">
                              {Math.round(item.progress_percentage || 0)}%
                            </span>
                          </div>
                          <ProgressBar
                            value={item.progress_percentage || 0}
                            max={100}
                            size="sm"
                            color={isCompleted ? 'bg-emerald-500' : 'bg-primary-600'}
                          />
                        </div>
                        {item.notes && (
                          <p className="text-xs text-slate-600 italic bg-slate-50 p-2 rounded-lg border border-slate-100">
                            Notes: "{item.notes}"
                          </p>
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
                              className="px-3.5 py-2 bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 text-xs font-semibold rounded-xl shadow-subtle transition flex items-center gap-1.5"
                            >
                              <Edit3 className="w-3.5 h-3.5" />
                              <span>Update</span>
                            </button>
                            <button
                              onClick={() => handleCompleteResource(item.resource_id || item.learning_resource_id || item.resource?.id)}
                              className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold rounded-xl shadow-subtle transition flex items-center gap-1.5"
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
                            className="p-2 text-slate-400 hover:text-slate-700 border border-transparent hover:border-slate-200 rounded-lg transition"
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
          </Card>
        </div>
      )}

      {/* Progress Update Modal */}
      {modalItem && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-xs z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-elevated border border-slate-100 animate-fadeIn">
            <div className="flex justify-between items-center mb-4 pb-3 border-b border-slate-100">
              <h3 className="font-bold text-base text-slate-900">Update Learning Progress</h3>
              <button
                onClick={() => setModalItem(null)}
                className="text-slate-400 hover:text-slate-600 p-1 rounded-lg hover:bg-slate-100 transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSaveProgressModal} className="space-y-4">
              <div>
                <p className="text-xs text-slate-500 mb-2">
                  Module: <b className="text-slate-800">{modalItem.resource?.title}</b>
                </p>
                <div className="flex justify-between text-xs font-semibold text-slate-700 mb-1">
                  <span>Progress</span>
                  <span className="text-primary-600 font-bold">{modalPct}%</span>
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
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                  Learning Notes (Optional)
                </label>
                <textarea
                  rows={3}
                  value={modalNotes}
                  onChange={(e) => setModalNotes(e.target.value)}
                  placeholder="e.g. Finished chapter 4 exercises, built demonstration project..."
                  className="w-full p-3 rounded-xl border border-slate-200 text-xs focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500 transition"
                />
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setModalItem(null)}
                  className="px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-xl transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={updatingProgress}
                  className="px-4 py-2 text-xs font-semibold bg-primary-600 hover:bg-primary-700 text-white rounded-xl shadow-subtle transition"
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

export default LearningPage;
