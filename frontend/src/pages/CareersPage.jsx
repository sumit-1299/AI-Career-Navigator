import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';
import { Spinner, Alert } from '../components/common/UIFeedback';
import { Badge } from '../components/common/Badge';
import { Card } from '../components/common/Card';
import { SectionHeader } from '../components/common/SectionHeader';
import { ProgressBar } from '../components/common/ProgressBar';
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
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Modern Section Header */}
      <SectionHeader
        badge="Career Catalog & Pathways"
        title="Explore Technology Tracks"
        subtitle="Discover professional pathways with multi-factor personalized fit intelligence, skill overlap, and market demand alignment."
        action={
          <div className="flex items-center gap-2">
            <Badge variant="default" size="md">
              {filteredCareers.length} Careers Available
            </Badge>
            {Object.keys(recommendationsMap).length > 0 && (
              <Badge variant="success" size="md" dot>
                Multi-Factor Active
              </Badge>
            )}
          </div>
        }
      />

      {error && <Alert type="error" message={error} onClose={() => setError(null)} />}

      {/* Toolbar */}
      <Card className="p-4 shadow-card">
        <div className="flex flex-col md:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="w-4 h-4 absolute left-3.5 top-3.5 text-slate-400" />
            <input
              type="text"
              placeholder="Search careers by title, description, or domain..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500 text-sm bg-slate-50/50 focus:bg-white transition"
            />
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <select
              value={selectedDomain}
              onChange={(e) => setSelectedDomain(e.target.value)}
              className="px-3.5 py-2.5 rounded-xl border border-slate-200 bg-slate-50 text-xs font-semibold text-slate-700 hover:border-slate-300 transition"
            >
              {domains.map((dom) => (
                <option key={dom} value={dom}>
                  Domain: {dom}
                </option>
              ))}
            </select>

            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="px-3.5 py-2.5 rounded-xl border border-slate-200 bg-slate-50 text-xs font-semibold text-slate-700 hover:border-slate-300 transition"
            >
              <option value="personalized">Sort: Best Fit (Multi-Factor)</option>
              <option value="name">Sort: Alphabetical</option>
            </select>
          </div>
        </div>
      </Card>

      {/* Careers Grid */}
      {loading ? (
        <div className="flex flex-col items-center justify-center py-20">
          <Spinner size="lg" />
          <p className="mt-4 text-slate-500 font-medium">Loading career catalog...</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {sortedCareers.map((c) => {
            const isTarget = targetCareerId === c.id;
            const rec = recommendationsMap[c.id];
            const isExpanded = expandedCareerId === c.id;
            const detail = careerDetail[c.id];
            const title = c.career_name || c.title || '';
            const matchScore = rec?.final_score ?? rec?.recommendation_score;

            return (
              <Card
                key={c.id}
                className={`p-6 flex flex-col justify-between transition-all ${
                  isTarget ? 'border-primary-500 ring-2 ring-primary-500/10 shadow-card-hover' : 'shadow-card'
                }`}
              >
                <div>
                  <div className="flex items-start justify-between gap-3 mb-3">
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <Badge variant="default" size="xs">
                          {c.domain || 'Technology'}
                        </Badge>
                        {rec?.rank && (
                          <Badge variant="primary" size="xs">
                            Rank #{rec.rank}
                          </Badge>
                        )}
                        {isTarget && (
                          <Badge variant="success" size="xs" dot>
                            Current Target
                          </Badge>
                        )}
                      </div>
                      <h3 className="text-lg font-bold text-slate-900 tracking-tight leading-snug">
                        {title}
                      </h3>
                    </div>

                    {matchScore !== undefined && (
                      <div className="text-right shrink-0">
                        <div className="text-xl font-black text-primary-600">
                          {matchScore}%
                        </div>
                        <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                          Fit Score
                        </span>
                      </div>
                    )}
                  </div>

                  <p className="text-xs text-slate-600 line-clamp-2 leading-relaxed mb-4">
                    {c.description || 'Professional role covering specialized technologies and engineering principles.'}
                  </p>

                  {/* Multi-Factor breakdown strip */}
                  {rec?.factor_breakdown && (
                    <div className="p-3 bg-slate-50/70 rounded-xl border border-slate-100 mb-4 text-[11px] grid grid-cols-2 sm:grid-cols-4 gap-2">
                      <div>
                        <span className="text-slate-400 block">Skill (50%)</span>
                        <span className="font-bold text-slate-800">{rec.factor_breakdown.skill_fit?.score}%</span>
                      </div>
                      <div>
                        <span className="text-slate-400 block">Pref (20%)</span>
                        <span className="font-bold text-slate-800">{rec.factor_breakdown.preference_fit?.score ?? 'N/A'}%</span>
                      </div>
                      <div>
                        <span className="text-slate-400 block">Market (15%)</span>
                        <span className="font-bold text-slate-800">{rec.factor_breakdown.market_demand?.score}%</span>
                      </div>
                      <div>
                        <span className="text-slate-400 block">Acad (15%)</span>
                        <span className="font-bold text-slate-800">{rec.factor_breakdown.academic_fit?.score ?? 'N/A'}%</span>
                      </div>
                    </div>
                  )}

                  {/* Skills Drawer */}
                  {isExpanded && (
                    <div className="mt-4 pt-4 border-t border-slate-100 space-y-3 animate-fadeIn">
                      <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                        Required Core Competencies
                      </h4>
                      {detail?.skills ? (
                        <div className="flex flex-wrap gap-1.5">
                          {detail.skills.map((s, idx) => (
                            <span
                              key={idx}
                              className="px-2.5 py-1 bg-slate-100 text-slate-700 rounded-lg text-xs font-medium"
                            >
                              {s.skill_name || s.name} (Lvl {s.proficiency_required || s.level || 5})
                            </span>
                          ))}
                        </div>
                      ) : (
                        <div className="py-2 text-center text-xs text-slate-400">Loading skills...</div>
                      )}
                    </div>
                  )}
                </div>

                <div className="mt-5 pt-4 border-t border-slate-100 flex flex-wrap items-center justify-between gap-3">
                  <button
                    type="button"
                    onClick={() => toggleExpand(c.id)}
                    className="text-xs font-semibold text-slate-500 hover:text-slate-900 flex items-center gap-1 transition"
                  >
                    <span>{isExpanded ? 'Hide Skills' : 'View Skills'}</span>
                    {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                  </button>

                  <div className="flex items-center gap-2">
                    {!isTarget ? (
                      <button
                        type="button"
                        onClick={() => setTargetCareerId(c.id)}
                        className="px-3.5 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-semibold transition"
                      >
                        Set as Target
                      </button>
                    ) : (
                      <span className="text-xs font-bold text-emerald-600 flex items-center gap-1 px-2">
                        <CheckCircle className="w-3.5 h-3.5" /> Active Target
                      </span>
                    )}

                    <button
                      type="button"
                      onClick={() => navigate(`/skill-gap?career_id=${c.id}`)}
                      className="px-4 py-1.5 bg-primary-600 hover:bg-primary-700 text-white rounded-xl text-xs font-bold shadow-subtle transition flex items-center gap-1"
                    >
                      <span>Analyze</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default CareersPage;
