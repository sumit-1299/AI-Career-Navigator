import React, { useEffect, useMemo, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import {
  CheckCircle2,
  Clock3,
  ExternalLink,
  FolderGit2,
  Play,
  RotateCcw,
  Sparkles,
  Target,
} from 'lucide-react';
import { api } from '../services/api';
import { Spinner, Alert } from '../components/common/UIFeedback';
import { Badge } from '../components/common/Badge';

export function PracticalTasksPage() {
  const [searchParams] = useSearchParams();
  const skillId = searchParams.get('skill_id');

  const [resources, setResources] = useState([]);
  const [progress, setProgress] = useState([]);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState(null);
  const [error, setError] = useState(null);

  async function loadTasks() {
    setLoading(true);
    setError(null);

    try {
      const [resourceResponse, progressResponse] = await Promise.all([
        api.listLearningResources({
          type: 'Project',
          canonical_skill_id: skillId ? Number(skillId) : null,
        }),
        api.getUserLearningProgress(),
      ]);

      setResources(resourceResponse?.resources || []);
      setProgress(
        progressResponse?.progress_items ||
        progressResponse?.progress ||
        []
      );
    } catch (err) {
      setError(err.message || 'Could not load practical tasks.');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadTasks();
  }, [skillId]);

  const progressMap = useMemo(() => {
    const map = {};

    progress.forEach((item) => {
      const resourceId =
        item.learning_resource_id ||
        item.learningResourceId ||
        item.resource?.id;

      if (resourceId != null) {
        map[String(resourceId)] = item;
      }
    });

    return map;
  }, [progress]);

  async function startTask(resourceId) {
    setBusyId(resourceId);
    setError(null);

    try {
      await api.startLearningResource(resourceId);
      await loadTasks();
    } catch (err) {
      setError(err.message || 'Could not start this task.');
    } finally {
      setBusyId(null);
    }
  }

  async function completeTask(resourceId) {
    setBusyId(resourceId);
    setError(null);

    try {
      await api.completeLearningResource(resourceId);
      await loadTasks();
    } catch (err) {
      setError(err.message || 'Could not mark this task as complete.');
    } finally {
      setBusyId(null);
    }
  }

  function statusFor(resourceId) {
    const item = progressMap[String(resourceId)];

    if (!item) {
      return {
        label: 'Not started',
        value: 0,
        tone: 'neutral',
      };
    }

    const percentage = Number(item.progress_percentage || 0);

    if (
      item.status === 'Completed' ||
      item.status === 'Complete' ||
      percentage >= 100
    ) {
      return {
        label: 'Completed',
        value: 100,
        tone: 'success',
      };
    }

    return {
      label: 'In progress',
      value: percentage,
      tone: 'info',
    };
  }

  return (
    <div className="space-y-6 animate-fadeIn">
      <section className="relative overflow-hidden rounded-3xl bg-slate-950 text-white p-6 md:p-8">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_10%_10%,rgba(99,102,241,0.32),transparent_34%),radial-gradient(circle_at_90%_90%,rgba(16,185,129,0.13),transparent_28%)]" />

        <div className="relative">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-[10px] uppercase tracking-[0.18em] font-black text-indigo-300">
              Evidence building
            </span>
            <Badge variant="purple">Un-graded practical work</Badge>
          </div>

          <h1 className="text-3xl md:text-4xl font-black tracking-tight mt-3">
            Practical Tasks
          </h1>

          <p className="text-sm md:text-base text-slate-300 mt-2 max-w-3xl leading-6">
            Build small, concrete pieces of work that create evidence for the
            skills you need. Completion is self-reported and does not become an
            assessment score.
          </p>

          <div className="flex flex-wrap gap-3 mt-6">
            <Link
              to="/skill-gap"
              className="inline-flex items-center gap-2 px-4 py-3 rounded-xl bg-white text-slate-950 text-xs font-extrabold"
            >
              <Target className="w-4 h-4" />
              Review skill gaps
            </Link>

            <Link
              to="/jobs"
              className="inline-flex items-center gap-2 px-4 py-3 rounded-xl bg-white/10 border border-white/10 text-white text-xs font-bold"
            >
              Re-align with a live role
            </Link>
          </div>
        </div>
      </section>

      {error && <Alert type="error" message={error} />}

      {loading ? (
        <div className="min-h-[45vh] flex flex-col items-center justify-center">
          <Spinner size="lg" />
          <p className="mt-3 text-sm text-slate-500">
            Loading practical tasks...
          </p>
        </div>
      ) : resources.length === 0 ? (
        <section className="bg-white rounded-2xl border border-dashed border-slate-300 p-10 text-center">
          <FolderGit2 className="w-10 h-10 text-slate-300 mx-auto" />
          <h2 className="text-base font-bold text-slate-800 mt-3">
            No practical tasks found for this skill yet.
          </h2>
          <p className="text-xs text-slate-500 mt-1 max-w-lg mx-auto">
            Try the complete practical-task catalog or choose another skill from
            the Skill Gap page.
          </p>

          {skillId && (
            <Link
              to="/tasks"
              className="inline-flex items-center gap-2 mt-4 px-4 py-2.5 rounded-xl bg-primary-600 text-white text-xs font-bold"
            >
              View all practical tasks
            </Link>
          )}
        </section>
      ) : (
        <>
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="text-xs uppercase tracking-wider font-black text-primary-600">
                {skillId ? 'Skill-linked tasks' : 'Career practice catalog'}
              </p>
              <h2 className="text-xl font-black text-slate-900 mt-1">
                {resources.length} practical task{resources.length === 1 ? '' : 's'}
              </h2>
            </div>

            {skillId && (
              <Link
                to="/tasks"
                className="text-xs font-bold text-primary-600 hover:underline"
              >
                View all tasks
              </Link>
            )}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
            {resources.map((resource) => {
              const status = statusFor(resource.id);
              const busy = busyId === resource.id;

              return (
                <article
                  key={resource.id}
                  className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5 hover:border-primary-300 hover:shadow-md transition"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="min-w-0">
                      <div className="flex flex-wrap items-center gap-2">
                        <Badge variant={status.tone}>{status.label}</Badge>
                        <span className="text-[10px] font-black uppercase tracking-wider text-slate-400">
                          {resource.difficulty_level || 'Intermediate'}
                        </span>
                      </div>

                      <h3 className="text-lg font-extrabold text-slate-900 mt-3">
                        {resource.title}
                      </h3>

                      <p className="text-xs text-slate-500 mt-1">
                        {resource.provider}
                        {resource.canonical_skill_name
                          ? ` · ${resource.canonical_skill_name}`
                          : ''}
                      </p>
                    </div>

                    <FolderGit2 className="w-6 h-6 text-primary-500 shrink-0" />
                  </div>

                  <p className="text-sm text-slate-600 leading-6 mt-4">
                    {resource.description ||
                      'Build a practical artifact that demonstrates this technical skill.'}
                  </p>

                  <div className="flex flex-wrap gap-3 mt-4 text-xs text-slate-500">
                    <span className="inline-flex items-center gap-1.5">
                      <Clock3 className="w-3.5 h-3.5" />
                      {resource.estimated_duration || 'Flexible'}
                    </span>

                    {resource.url && (
                      <a
                        href={resource.url}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center gap-1.5 text-primary-600 font-semibold hover:underline"
                      >
                        Reference
                        <ExternalLink className="w-3.5 h-3.5" />
                      </a>
                    )}
                  </div>

                  <div className="mt-5 pt-4 border-t border-slate-100">
                    {status.value > 0 && status.value < 100 && (
                      <div className="mb-4">
                        <div className="flex justify-between text-[11px] text-slate-500 mb-1.5">
                          <span>Self-reported progress</span>
                          <span className="font-bold">{Math.round(status.value)}%</span>
                        </div>

                        <div className="h-2 rounded-full bg-slate-100 overflow-hidden">
                          <div
                            className="h-full bg-primary-500 rounded-full"
                            style={{ width: `${Math.min(100, status.value)}%` }}
                          />
                        </div>
                      </div>
                    )}

                    <div className="flex flex-wrap gap-2">
                      {status.label === 'Not started' && (
                        <button
                          onClick={() => startTask(resource.id)}
                          disabled={busy}
                          className="inline-flex items-center gap-2 px-3.5 py-2.5 rounded-xl bg-primary-600 hover:bg-primary-700 text-white text-xs font-bold disabled:opacity-60"
                        >
                          <Play className="w-3.5 h-3.5" />
                          {busy ? 'Starting…' : 'Start task'}
                        </button>
                      )}

                      {status.label === 'In progress' && (
                        <>
                          <button
                            onClick={() => completeTask(resource.id)}
                            disabled={busy}
                            className="inline-flex items-center gap-2 px-3.5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold disabled:opacity-60"
                          >
                            <CheckCircle2 className="w-3.5 h-3.5" />
                            {busy ? 'Saving…' : 'Mark complete'}
                          </button>

                          <button
                            onClick={() => startTask(resource.id)}
                            disabled={busy}
                            className="inline-flex items-center gap-2 px-3.5 py-2.5 rounded-xl border border-slate-200 text-slate-700 text-xs font-bold hover:bg-slate-50 disabled:opacity-60"
                          >
                            <RotateCcw className="w-3.5 h-3.5" />
                            Keep active
                          </button>
                        </>
                      )}

                      {status.label === 'Completed' && (
                        <div className="inline-flex items-center gap-2 px-3.5 py-2.5 rounded-xl bg-emerald-50 text-emerald-700 border border-emerald-200 text-xs font-bold">
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          Evidence task completed
                        </div>
                      )}
                    </div>
                  </div>
                </article>
              );
            })}
          </div>

          <section className="rounded-2xl bg-amber-50 border border-amber-200 p-5">
            <div className="flex gap-3">
              <Sparkles className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-bold text-amber-900">
                  Why practical tasks are here
                </p>
                <p className="text-xs leading-5 text-amber-800 mt-1">
                  A completed task is an additional evidence record for your
                  workflow. It should not be interpreted as a validated
                  proficiency score or combined with the other evidence types
                  into a single hiring probability.
                </p>
              </div>
            </div>
          </section>
        </>
      )}
    </div>
  );
}
