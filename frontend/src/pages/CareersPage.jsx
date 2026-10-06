import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';
import { Spinner, Alert } from '../components/common/UIFeedback';
import {
  Briefcase,
  Search,
  Filter,
  CheckCircle,
  ArrowRight,
  Sparkles,
  ChevronDown,
  ChevronUp,
  SlidersHorizontal,
  Compass,
} from 'lucide-react';

export function CareersPage() {
  const { targetCareerId, setTargetCareerId, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  const [careers, setCareers] = useState([]);
  const [recommendationsMap, setRecommendationsMap] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [searchQuery, setSearchQuery] = useState('');
  const [selectedDomain, setSelectedDomain] = useState('All');
  const [sortBy, setSortBy] = useState('personalized');
  const [expandedCareerId, setExpandedCareerId] = useState(null);
  const [careerDetail, setCareerDetail] = useState({});

  useEffect(() => {
    loadCareers();
  }, [isAuthenticated]);

  async function loadCareers() {
    setLoading(true);
    setError(null);
    try {
      const [careersRes, recRes] = await Promise.allSettled([
        api.listCareers(),
        api.getCareerRecommendations(),
      ]);

      if (careersRes.status === 'fulfilled') {
        setCareers(careersRes.value?.careers || []);
      }

      if (recRes.status === 'fulfilled' && recRes.value?.recommendations) {
        const rMap = {};
        recRes.value.recommendations.forEach((r, idx) => {
          rMap[r.career_id] = { ...r, rank: idx + 1 };
        });
        setRecommendationsMap(rMap);
      }
    } catch (err) {
      setError(err.message || 'Failed to fetch careers');
    } finally {
      setLoading(false);
    }
  }

  async function toggleExpand(careerId) {
    if (expandedCareerId === careerId) {
      setExpandedCareerId(null);
      return;
    }
    setExpandedCareerId(careerId);
    if (!careerDetail[careerId]) {
      try {
        const detailRes = await api.getCareerDetail(careerId);
        setCareerDetail((prev) => ({
          ...prev,
          [careerId]: detailRes?.career,
        }));
      } catch (err) {
        console.warn('Failed to fetch career details for', careerId, err);
      }
    }
  }

  const domains = ['All', ...new Set(careers.map((c) => c.domain).filter(Boolean))];

  const filteredCareers = careers.filter((c) => {
    const title = c.career_name || c.title || '';
    const desc = c.description || '';
    const dom = c.domain || '';
    const matchesDomain = selectedDomain === 'All' || dom === selectedDomain;
    const matchesQuery =
      title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      desc.toLowerCase().includes(searchQuery.toLowerCase()) ||
      dom.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesDomain && matchesQuery;
  });

  const sortedCareers = [...filteredCareers].sort((a, b) => {
    if (sortBy === 'personalized') {
      const scoreA =
        recommendationsMap[a.id]?.final_score ??
        recommendationsMap[a.id]?.recommendation_score ??
        0;
      const scoreB =
        recommendationsMap[b.id]?.final_score ??
        recommendationsMap[b.id]?.recommendation_score ??
        0;
      if (scoreB !== scoreA) return scoreB - scoreA;
    }
    const titleA = a.career_name || a.title || '';
    const titleB = b.career_name || b.title || '';
    return titleA.localeCompare(titleB);
  });

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">
              Career Catalog & Pathways
            </h1>
            <p className="text-slate-500 text-sm mt-1">
              Explore professional pathways ranked with Module 9.1 multi-factor personalized intelligence.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold px-3 py-1 bg-slate-100 text-slate-700 rounded-full w-fit">
              {filteredCareers.length} Careers Available
            </span>
            {Object.keys(recommendationsMap).length > 0 && (
              <span className="text-xs font-semibold px-3 py-1 bg-emerald-50 text-emerald-700 border border-emerald-200 rounded-full flex items-center gap-1">
                <Compass className="w-3 h-3" /> Multi-Factor Active
              </span>
            )}
          </div>
        </div>

        {/* Search, Filter & Sort Toolbar */}
        <div className="mt-6 flex flex-col md:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="w-4 h-4 absolute left-3.5 top-3.5 text-slate-400" />
            <input
              type="text"
              placeholder="Search careers, domains, keywords..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500 text-sm bg-slate-50 focus:bg-white transition"
            />
          </div>

          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-slate-400 shrink-0" />
            <select
              value={selectedDomain}
              onChange={(e) => setSelectedDomain(e.target.value)}
              className="px-3.5 py-2.5 rounded-xl border border-slate-200 bg-slate-50 text-sm font-medium text-slate-700 focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500 transition cursor-pointer"
            >
              {domains.map((dom) => (
                <option key={dom} value={dom}>
                  Domain: {dom}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-2">
            <SlidersHorizontal className="w-4 h-4 text-slate-400 shrink-0" />
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="px-3.5 py-2.5 rounded-xl border border-slate-200 bg-slate-50 text-sm font-medium text-slate-700 focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500 transition cursor-pointer"
            >
              <option value="personalized">Sort: Multi-Factor Fit</option>
              <option value="alphabetical">Sort: Alphabetical (A-Z)</option>
            </select>
          </div>
        </div>
      </div>

      {error && <Alert type="error" message={error} />}

      {loading ? (
        <div className="flex flex-col items-center justify-center py-16">
          <Spinner size="lg" />
          <p className="mt-3 text-slate-500 text-sm">Evaluating personalized career intelligence...</p>
        </div>
      ) : sortedCareers.length === 0 ? (
        <div className="bg-white rounded-2xl p-12 text-center border border-slate-200">
          <Briefcase className="w-10 h-10 text-slate-300 mx-auto mb-3" />
          <h3 className="text-base font-bold text-slate-800">No careers found</h3>
          <p className="text-xs text-slate-500 mt-1">Try adjusting your search or domain filter.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {sortedCareers.map((c) => {
            const isTarget = c.id === targetCareerId;
            const isExpanded = expandedCareerId === c.id;
            const detail = careerDetail[c.id];
            const careerTitle = c.career_name || c.title;
            const rec = recommendationsMap[c.id];
            const fitScore = rec?.final_score ?? rec?.recommendation_score;

            return (
              <div
                key={c.id}
                className={`bg-white rounded-2xl border transition-all duration-200 flex flex-col justify-between ${
                  isTarget
                    ? 'border-primary-500 ring-2 ring-primary-500/20 shadow-md'
                    : 'border-slate-200 hover:border-slate-300 hover:shadow-sm'
                }`}
              >
                <div className="p-6">
                  <div className="flex items-start justify-between gap-3 mb-3">
                    <span className="text-[11px] font-semibold px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-600">
                      {c.domain || 'Technology'}
                    </span>
                    <div className="flex items-center gap-1.5">
                      {fitScore !== undefined && (
                        <span className="text-[11px] font-bold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
                          {fitScore}% Match
                        </span>
                      )}
                      {isTarget && (
                        <span className="flex items-center gap-1 text-[11px] font-bold text-primary-700 bg-primary-50 border border-primary-200 px-2 py-0.5 rounded-full">
                          <CheckCircle className="w-3 h-3" /> Target Role
                        </span>
                      )}
                    </div>
                  </div>

                  <h3 className="text-lg font-bold text-slate-900 leading-snug">{careerTitle}</h3>
                  <p className="text-xs text-slate-500 mt-2 line-clamp-3 leading-relaxed">
                    {c.description || 'Professional role requiring industry domain skills.'}
                  </p>

                  {/* Module 9.1 Multi-Factor Breakdown Pills */}
                  {rec?.factor_breakdown && (
                    <div className="mt-3 p-2 bg-slate-50 rounded-xl border border-slate-100 text-[10px] space-y-1">
                      <div className="flex justify-between text-slate-600">
                        <span>Skill Fit (50%): <strong className="text-slate-800">{rec.factor_breakdown.skill_fit?.score}%</strong></span>
                        <span>Pref (20%): <strong className="text-slate-800">{rec.factor_breakdown.preference_fit?.score ?? 'N/A'}%</strong></span>
                      </div>
                      <div className="flex justify-between text-slate-600">
                        <span>Market (15%): <strong className="text-slate-800">{rec.factor_breakdown.market_demand?.score}%</strong></span>
                        <span>Acad (15%): <strong className="text-slate-800">{rec.factor_breakdown.academic_fit?.score ?? 'N/A'}%</strong></span>
                      </div>
                    </div>
                  )}

                  {rec?.multi_factor_justification && (
                    <p className="text-[10px] text-slate-500 italic mt-2 bg-slate-100/70 p-2 rounded-lg border border-slate-200/50 line-clamp-2">
                      "{rec.multi_factor_justification}"
                    </p>
                  )}

                  <div className="mt-4 pt-4 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
                    <span className="flex items-center gap-1.5 font-medium">
                      <Sparkles className="w-3.5 h-3.5 text-primary-500" />
                      {c.skills_count ?? detail?.skills?.length ?? detail?.required_skills?.length ?? 0} Required Skills
                    </span>
                    <button
                      onClick={() => toggleExpand(c.id)}
                      className="text-primary-600 font-semibold hover:underline flex items-center gap-1"
                    >
                      {isExpanded ? (
                        <>
                          Hide Skills <ChevronUp className="w-3.5 h-3.5" />
                        </>
                      ) : (
                        <>
                          View Skills <ChevronDown className="w-3.5 h-3.5" />
                        </>
                      )}
                    </button>
                  </div>

                  {/* Expanded Skills Detail */}
                  {isExpanded && (
                    <div className="mt-3 pt-3 border-t border-slate-100 bg-slate-50/70 p-3 rounded-xl animate-fadeIn text-xs">
                      <h4 className="font-semibold text-slate-700 mb-2">Required Core Skills:</h4>
                      {detail?.skills || detail?.required_skills ? (
                        <div className="flex flex-wrap gap-1.5 max-h-36 overflow-y-auto">
                          {(detail.skills || detail.required_skills).map((s, idx) => (
                            <span
                              key={idx}
                              className="px-2 py-1 bg-white border border-slate-200 text-slate-700 rounded-md text-[11px]"
                            >
                              {s.skill_name || s.name}
                            </span>
                          ))}
                        </div>
                      ) : (
                        <div className="flex items-center justify-center py-3">
                          <Spinner size="sm" />
                        </div>
                      )}
                    </div>
                  )}
                </div>

                <div className="p-4 bg-slate-50/60 border-t border-slate-100 rounded-b-2xl flex items-center justify-between gap-2">
                  {!isTarget ? (
                    <button
                      onClick={() => setTargetCareerId(c.id)}
                      className="px-3 py-1.5 bg-white hover:bg-slate-100 text-slate-700 border border-slate-200 text-xs font-semibold rounded-lg transition"
                    >
                      Set as Target
                    </button>
                  ) : (
                    <span className="text-xs font-semibold text-emerald-600">Active Target</span>
                  )}

                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => navigate(`/compare?a=${targetCareerId}&b=${c.id}`)}
                      className="px-2.5 py-1.5 text-xs text-slate-500 hover:text-slate-800 font-medium"
                    >
                      Compare
                    </button>
                    <button
                      onClick={() => navigate(`/skill-gap?career_id=${c.id}&tab=pathways`)}
                      className="px-2.5 py-1.5 text-xs text-primary-600 hover:text-primary-700 font-medium"
                    >
                      Pathways
                    </button>
                    <button
                      onClick={() => navigate(`/skill-gap?career_id=${c.id}`)}
                      className="px-3 py-1.5 bg-primary-600 hover:bg-primary-700 text-white text-xs font-semibold rounded-lg shadow-sm transition flex items-center gap-1"
                    >
                      <span>Analyze Gap</span>
                      <ArrowRight className="w-3 h-3" />
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
