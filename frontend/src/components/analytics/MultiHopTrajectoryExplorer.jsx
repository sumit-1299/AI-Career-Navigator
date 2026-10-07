import React, { useState, useEffect } from 'react';
import { api } from '../../services/api';
import { Spinner, Alert } from '../common/UIFeedback';
import { Badge } from '../common/Badge';
import {
  Compass,
  GitBranch,
  Layers,
  ArrowRight,
  TrendingUp,
  Clock,
  Sparkles,
  ShieldCheck,
  FolderGit2,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  Info,
  ChevronRight,
  RefreshCw,
} from 'lucide-react';

export function MultiHopTrajectoryExplorer({
  targetCareerId,
  fromCareerId = null,
  targetTitle = '',
  sourceTitle = '',
  availableCareers = [],
}) {
  const [selectedSourceId, setSelectedSourceId] = useState(fromCareerId);
  const [objective, setObjective] = useState('BEST_FIT');
  const [maxHops, setMaxHops] = useState(3);
  const [trajectoryData, setTrajectoryData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeStageIndex, setActiveStageIndex] = useState(0);

  useEffect(() => {
    if (fromCareerId) {
      setSelectedSourceId(fromCareerId);
    }
  }, [fromCareerId]);

  useEffect(() => {
    if (targetCareerId) {
      fetchTrajectory();
    }
  }, [targetCareerId, selectedSourceId, objective, maxHops]);

  async function fetchTrajectory() {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getCareerTrajectory(targetCareerId, {
        fromCareerId: selectedSourceId || undefined,
        objective,
        maxHops,
        limit: 4,
      });
      setTrajectoryData(res);
      setActiveStageIndex(0);
    } catch (err) {
      console.warn('Trajectory fetch failed', err);
      setError(err.message || 'Failed to calculate career trajectory');
    } finally {
      setLoading(false);
    }
  }

  const recTrajectory = trajectoryData?.recommended_trajectory;
  const directTrans = trajectoryData?.direct_transition;
  const comparison = trajectoryData?.comparison;
  const explanation = trajectoryData?.explanation;
  const alternatives = trajectoryData?.alternative_trajectories || [];
  const provenanceDisclaimer =
    trajectoryData?.provenance ||
    'DEMO / SAMPLE / PROTOTYPE MARKET BENCHMARK — NOT LIVE LABOR MARKET DATA';

  const stages = recTrajectory?.stages || [];
  const activeStage = stages[activeStageIndex] || stages[0];

  return (
    <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-100 pb-5">
        <div>
          <div className="flex items-center gap-2 mb-1.5 flex-wrap">
            <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200 flex items-center gap-1.5">
              <Compass className="w-3.5 h-3.5" />
              Phase 11 Module 11.5: Multi-Hop Career Trajectory Intelligence
            </span>
            {recTrajectory && (
              <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-slate-100 text-slate-700">
                {recTrajectory.hop_count} Hop{recTrajectory.hop_count === 1 ? '' : 's'} • {recTrajectory.careers?.length} Roles
              </span>
            )}
          </div>
          <h3 className="text-lg font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <span>Multi-Step Transition Pathway</span>
            <span className="text-slate-400 font-normal text-sm">
              ({sourceTitle || trajectoryData?.source_career?.title || 'Source'} → {targetTitle || trajectoryData?.target_career?.title || 'Target'})
            </span>
          </h3>
          <p className="text-xs text-slate-500 mt-0.5 max-w-2xl">
            Calculates optimal intermediate roles that progressively bridge skill gaps, lowering friction, building transferable competencies, and saving cumulative learning effort.
          </p>
        </div>

        {/* Source Selector if available */}
        {availableCareers && availableCareers.length > 0 && !fromCareerId && (
          <div className="flex items-center gap-2 shrink-0">
            <label className="text-xs font-medium text-slate-500">Starting From:</label>
            <select
              value={selectedSourceId || ''}
              onChange={(e) => setSelectedSourceId(e.target.value ? Number(e.target.value) : null)}
              className="bg-slate-50 border border-slate-300 text-slate-800 text-xs rounded-xl px-3 py-2 font-medium"
            >
              <option value="">User Profile Baseline</option>
              {availableCareers
                .filter((c) => c.id !== targetCareerId)
                .map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.title}
                  </option>
                ))}
            </select>
          </div>
        )}
      </div>

      {/* Controls: Objectives & Max Hops */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 bg-slate-50/80 p-3.5 rounded-xl border border-slate-200">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-xs font-bold text-slate-600 uppercase tracking-wide mr-1">
            Objective:
          </span>
          {[
            { id: 'BEST_FIT', label: 'Best Fit (Balanced)' },
            { id: 'SHORTEST', label: 'Shortest (Min Hops)' },
            { id: 'LOWEST_EFFORT', label: 'Lowest Effort (Min Hours)' },
            { id: 'MARKET_AWARE', label: 'Market Aware (High Demand)' },
          ].map((obj) => (
            <button
              key={obj.id}
              onClick={() => setObjective(obj.id)}
              className={`text-xs px-3 py-1.5 rounded-lg font-semibold transition ${
                objective === obj.id
                  ? 'bg-indigo-600 text-white shadow-xs'
                  : 'bg-white text-slate-600 hover:text-slate-900 border border-slate-200'
              }`}
            >
              {obj.label}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-2 self-end sm:self-auto shrink-0">
          <span className="text-xs font-medium text-slate-500">Max Hops:</span>
          <div className="flex rounded-lg border border-slate-200 bg-white p-0.5">
            {[1, 2, 3, 4].map((h) => (
              <button
                key={h}
                onClick={() => setMaxHops(h)}
                className={`text-xs px-2.5 py-1 rounded-md font-semibold transition ${
                  maxHops === h ? 'bg-indigo-600 text-white' : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                {h}
              </button>
            ))}
          </div>
          <button
            onClick={fetchTrajectory}
            disabled={loading}
            className="p-1.5 text-slate-400 hover:text-indigo-600 rounded-lg hover:bg-slate-100 transition"
            title="Recalculate trajectory"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {loading && (
        <div className="flex items-center justify-center py-12">
          <Spinner size="md" />
        </div>
      )}

      {error && !loading && <Alert type="error" message={error} />}

      {!loading && trajectoryData && recTrajectory && (
        <div className="space-y-6">
          {/* Strategic Comparison & Explainable Rationale Callout */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            {/* Direct vs Multi-hop Comparison Metric Box */}
            <div className="lg:col-span-1 p-5 rounded-xl border border-indigo-200 bg-gradient-to-br from-indigo-50/60 to-white flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs font-bold text-indigo-900 uppercase tracking-wide">
                    Trajectory Viability
                  </span>
                  <Badge variant={comparison?.is_multihop_better ? 'success' : 'neutral'}>
                    {comparison?.is_multihop_better ? 'Multi-Hop Recommended' : 'Direct Preferred'}
                  </Badge>
                </div>

                <div className="space-y-2.5">
                  <div className="flex justify-between items-center text-xs">
                    <span className="text-slate-500">Direct Compatibility:</span>
                    <span className="font-bold text-slate-700">
                      {Math.round((directTrans?.compatibility || 0) * 100)}%
                    </span>
                  </div>
                  <div className="flex justify-between items-center text-xs">
                    <span className="text-slate-500">Multi-Hop Avg Compatibility:</span>
                    <span className="font-bold text-indigo-700">
                      {Math.round((recTrajectory?.average_compatibility || 0) * 100)}%
                    </span>
                  </div>
                  <div className="flex justify-between items-center text-xs">
                    <span className="text-slate-500">Total Learning Hours:</span>
                    <span className="font-bold text-slate-800">
                      {recTrajectory.estimated_learning_hours} hrs
                    </span>
                  </div>
                  <div className="flex justify-between items-center text-xs">
                    <span className="text-slate-500">Progressive Skill Reuse:</span>
                    <span className="font-bold text-emerald-700">
                      {Math.round((recTrajectory?.progressive_skill_reuse || 0) * 100)}%
                    </span>
                  </div>
                  {recTrajectory.market_opportunity_score !== undefined && (
                    <div className="flex justify-between items-center text-xs">
                      <span className="text-slate-500">Market Opportunity Score:</span>
                      <span className="font-bold text-purple-700">
                        {Math.round(recTrajectory.market_opportunity_score * 100)}/100
                      </span>
                    </div>
                  )}
                </div>
              </div>

              <div className="mt-4 pt-3 border-t border-indigo-100 text-xs text-slate-600">
                {comparison?.summary}
              </div>
            </div>

            {/* Explainable Rationale Narrative */}
            <div className="lg:col-span-2 p-5 rounded-xl border border-slate-200 bg-slate-50/50 flex flex-col justify-between">
              <div>
                <div className="flex items-center gap-2 mb-2 text-indigo-700">
                  <Sparkles className="w-4 h-4" />
                  <span className="text-xs font-bold uppercase tracking-wider">
                    Explainable Multi-Hop Trajectory Rationale
                  </span>
                </div>
                <p className="text-xs text-slate-700 leading-relaxed font-medium">
                  {explanation || 'Strategic trajectory calculated using weighted directed graph analysis.'}
                </p>
              </div>

              {/* Path Node Sequence Breadcrumb */}
              <div className="mt-4 pt-3 border-t border-slate-200">
                <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wide block mb-2">
                  Progression Sequence ({stages.length} Stage{stages.length === 1 ? '' : 's'}):
                </span>
                <div className="flex items-center flex-wrap gap-2">
                  {recTrajectory.careers?.map((careerName, idx) => (
                    <React.Fragment key={idx}>
                      <span
                        className={`text-xs px-3 py-1.5 rounded-lg font-bold flex items-center gap-1.5 ${
                          idx === 0
                            ? 'bg-slate-200 text-slate-800'
                            : idx === recTrajectory.careers.length - 1
                            ? 'bg-indigo-600 text-white shadow-xs'
                            : 'bg-indigo-100 text-indigo-900 border border-indigo-200'
                        }`}
                      >
                        {idx === 0 && <span className="text-[10px] text-slate-500 font-normal">Start:</span>}
                        {idx === recTrajectory.careers.length - 1 && (
                          <span className="text-[10px] text-indigo-200 font-normal">Target:</span>
                        )}
                        {careerName}
                      </span>
                      {idx < recTrajectory.careers.length - 1 && (
                        <ArrowRight className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                      )}
                    </React.Fragment>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Sequential Trajectory Stages Stepper & Details */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-2">
                <Layers className="w-4 h-4 text-indigo-600" />
                <span>Stage-by-Stage Progressive Learning & Projects</span>
              </h4>
              <div className="flex gap-1.5">
                {stages.map((stg, i) => (
                  <button
                    key={i}
                    onClick={() => setActiveStageIndex(i)}
                    className={`text-xs px-2.5 py-1 rounded-md font-semibold transition ${
                      activeStageIndex === i
                        ? 'bg-indigo-600 text-white'
                        : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                    }`}
                  >
                    Stage {stg.stage_number}
                  </button>
                ))}
              </div>
            </div>

            {/* Active Stage Card */}
            {activeStage && (
              <div className="p-5 rounded-2xl border border-indigo-100 bg-white shadow-xs space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-extrabold px-2 py-0.5 rounded bg-indigo-100 text-indigo-800">
                        STAGE {activeStage.stage_number} OF {stages.length}
                      </span>
                      <span className="text-sm font-bold text-slate-900">
                        {activeStage.from_career_title} → {activeStage.to_career_title}
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center gap-4 text-xs">
                    <div>
                      <span className="text-slate-400 block text-[10px] uppercase">Compatibility</span>
                      <span className="font-extrabold text-indigo-700 text-sm">
                        {Math.round((activeStage.transition_compatibility || 0) * 100)}%
                      </span>
                    </div>
                    <div>
                      <span className="text-slate-400 block text-[10px] uppercase">Stage Hours</span>
                      <span className="font-extrabold text-slate-800 text-sm">
                        {activeStage.stage_learning_hours} hrs
                      </span>
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Skills Targeted at this Stage */}
                  <div className="p-3.5 bg-slate-50/70 rounded-xl border border-slate-200">
                    <span className="text-xs font-bold text-slate-700 uppercase tracking-wide block mb-2">
                      Competencies Developed ({activeStage.skills_targeted?.length || 0})
                    </span>
                    <div className="space-y-1.5 max-h-48 overflow-y-auto pr-1">
                      {activeStage.skills_targeted?.map((sk, sIdx) => (
                        <div
                          key={sIdx}
                          className="flex items-center justify-between text-xs bg-white p-2 rounded-lg border border-slate-200"
                        >
                          <div className="flex items-center gap-1.5">
                            <span className="font-semibold text-slate-800">{sk.skill_name}</span>
                            {sk.is_target_competency && (
                              <span className="text-[10px] bg-emerald-100 text-emerald-800 px-1.5 py-0.2 rounded font-bold">
                                Target Goal
                              </span>
                            )}
                          </div>
                          <span className="text-slate-500 font-medium">
                            Lv {sk.current_level} → {sk.target_level} (+{sk.level_gap})
                          </span>
                        </div>
                      ))}
                      {(!activeStage.skills_targeted || activeStage.skills_targeted.length === 0) && (
                        <p className="text-xs text-slate-400 italic">No incremental skill gaps required.</p>
                      )}
                    </div>
                  </div>

                  {/* Recommended Capstone Project for Stage */}
                  <div className="p-3.5 bg-indigo-50/50 rounded-xl border border-indigo-200 flex flex-col justify-between">
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-xs font-bold text-indigo-950 uppercase tracking-wide flex items-center gap-1.5">
                          <FolderGit2 className="w-3.5 h-3.5 text-indigo-600" />
                          Stage Capstone Project (Module 11.2)
                        </span>
                        {activeStage.recommended_project && (
                          <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-indigo-200 text-indigo-900">
                            {activeStage.recommended_project.difficulty}
                          </span>
                        )}
                      </div>

                      {activeStage.recommended_project ? (
                        <div className="space-y-1.5">
                          <h5 className="text-xs font-bold text-slate-900">
                            {activeStage.recommended_project.title}
                          </h5>
                          <p className="text-[11px] text-slate-600">
                            Hands-on portfolio deliverable designed to prove mastery of stage competencies.
                          </p>
                          <div className="flex items-center gap-3 pt-2 text-[11px] text-indigo-700 font-semibold">
                            <span className="flex items-center gap-1">
                              <Clock className="w-3 h-3" /> ~{activeStage.recommended_project.estimated_hours} hrs
                            </span>
                          </div>
                        </div>
                      ) : (
                        <p className="text-xs text-slate-500 italic">
                          Standard pathway learning modules apply for this stage.
                        </p>
                      )}
                    </div>

                    {activeStage.remaining_target_gaps && activeStage.remaining_target_gaps.length > 0 && (
                      <div className="mt-3 pt-2 border-t border-indigo-100 text-[11px] text-slate-500">
                        <span>Remaining gaps for subsequent stages: </span>
                        <span className="font-medium text-slate-700">
                          {activeStage.remaining_target_gaps.slice(0, 3).join(', ')}
                          {activeStage.remaining_target_gaps.length > 3 ? '...' : ''}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Alternative Trajectories Section */}
          {alternatives.length > 0 && (
            <div>
              <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                <GitBranch className="w-4 h-4 text-slate-500" />
                <span>Alternative Trajectory Pathways ({alternatives.length})</span>
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {alternatives.map((alt, aIdx) => (
                  <div
                    key={aIdx}
                    className="p-3.5 bg-slate-50 border border-slate-200 rounded-xl text-xs space-y-2 hover:border-indigo-300 transition"
                  >
                    <div className="flex justify-between items-center">
                      <span className="font-bold text-slate-800">
                        {alt.hop_count} Hop{alt.hop_count === 1 ? '' : 's'} Pathway
                      </span>
                      <span className="text-[11px] text-indigo-700 font-semibold">
                        Avg Compat: {Math.round((alt.average_compatibility || 0) * 100)}%
                      </span>
                    </div>
                    <div className="flex items-center flex-wrap gap-1 text-[11px] text-slate-600 font-medium">
                      {alt.careers?.map((cName, cIdx) => (
                        <React.Fragment key={cIdx}>
                          <span className="px-1.5 py-0.5 bg-white rounded border border-slate-200">
                            {cName}
                          </span>
                          {cIdx < alt.careers.length - 1 && <span className="text-slate-400">→</span>}
                        </React.Fragment>
                      ))}
                    </div>
                    <div className="flex justify-between items-center text-[11px] text-slate-500 pt-1 border-t border-slate-200">
                      <span>Total Effort: {alt.estimated_learning_hours} hrs</span>
                      <span>Skill Reuse: {Math.round((alt.progressive_skill_reuse || 0) * 100)}%</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Provenance Disclaimer */}
          <div className="p-3 bg-slate-100 rounded-xl text-[11px] text-slate-600 border border-slate-200 flex items-center gap-2">
            <Info className="w-4 h-4 text-slate-400 shrink-0" />
            <span>
              <strong>Market Provenance Notice:</strong> {provenanceDisclaimer}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
export default MultiHopTrajectoryExplorer;
