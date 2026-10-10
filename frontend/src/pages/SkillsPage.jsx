import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { Spinner, Alert, EmptyState } from '../components/common/UIFeedback';
import { Badge } from '../components/common/Badge';
import { ProgressBar } from '../components/common/ProgressBar';
import { Card } from '../components/common/Card';
import { SectionHeader } from '../components/common/SectionHeader';
import {
  Sparkles,
  Plus,
  Search,
  CheckCircle,
  BookOpen,
  Layers,
  Award,
  Sliders,
} from 'lucide-react';

export function SkillsPage() {
  const [skills, setSkills] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);

  // New skill form state
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [selectedCanonical, setSelectedCanonical] = useState(null);
  const [proficiency, setProficiency] = useState(5);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    loadUserSkills();
  }, []);

  async function loadUserSkills() {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getUserSkills();
      setSkills(res?.skills || []);
    } catch (err) {
      console.warn('Could not load user skills', err);
    } finally {
      setLoading(false);
    }
  }

  // Canonical skill search debounce
  useEffect(() => {
    if (!searchQuery || searchQuery.trim().length < 2) {
      setSearchResults([]);
      return;
    }

    const timer = setTimeout(async () => {
      setIsSearching(true);
      try {
        const res = await api.searchCanonicalSkills(searchQuery.trim());
        const list = Array.isArray(res) ? res : res?.skills || [];
        setSearchResults(list);
      } catch (err) {
        console.warn('Skill autocomplete failed', err);
      } finally {
        setIsSearching(false);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [searchQuery]);

  async function handleAddSkill(e) {
    e.preventDefault();
    const skillName = selectedCanonical
      ? selectedCanonical.canonical_name || selectedCanonical.skill_name || selectedCanonical.name
      : searchQuery.trim();
    if (!skillName) return;

    setSubmitting(true);
    setError(null);
    setSuccessMsg(null);
    try {
      await api.addSkill(skillName, proficiency);
      setSuccessMsg(`Successfully added "${skillName}" (Level ${proficiency}/10)`);
      setSearchQuery('');
      setSelectedCanonical(null);
      setSearchResults([]);
      setProficiency(5);
      await loadUserSkills();
    } catch (err) {
      setError(err.message || 'Failed to add skill');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Modernized Header */}
      <SectionHeader
        badge="Skill Inventory"
        title="My Verified Skills"
        subtitle="Manage your technical and domain competencies mapped to the canonical knowledge graph."
        action={
          <Badge variant="primary" size="md">
            {skills.length} Skills Logged
          </Badge>
        }
      />

      {error && <Alert type="error" message={error} onClose={() => setError(null)} />}
      {successMsg && <Alert type="success" message={successMsg} onClose={() => setSuccessMsg(null)} />}

      {/* Add Skill Form Section */}
      <Card className="p-6 md:p-7 shadow-card">
        <div className="flex items-center gap-2.5 mb-5 pb-4 border-b border-slate-100">
          <div className="p-2 rounded-xl bg-primary-50 text-primary-600">
            <Plus className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-bold text-slate-900">Add Skill to Inventory</h2>
            <p className="text-xs text-slate-500">
              Type to search canonical entities or enter a custom skill with initial proficiency
            </p>
          </div>
        </div>

        <form onSubmit={handleAddSkill} className="space-y-5">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-start">
            {/* Search Input with dropdown */}
            <div className="md:col-span-2 relative">
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
                Skill Name (Canonical Search)
              </label>
              <div className="relative">
                <Search className="w-4 h-4 absolute left-3.5 top-3.5 text-slate-400" />
                <input
                  type="text"
                  placeholder="e.g. Python, Machine Learning, React, SQL, AWS..."
                  value={searchQuery}
                  onChange={(e) => {
                    setSearchQuery(e.target.value);
                    if (
                      selectedCanonical &&
                      e.target.value !== (selectedCanonical.canonical_name || selectedCanonical.name)
                    ) {
                      setSelectedCanonical(null);
                    }
                  }}
                  className="w-full pl-10 pr-10 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500 text-sm bg-slate-50/50 focus:bg-white transition"
                  required
                />
                {isSearching && (
                  <div className="absolute right-3.5 top-3.5">
                    <Spinner size="sm" />
                  </div>
                )}
              </div>

              {/* Autocomplete Dropdown */}
              {searchResults.length > 0 && !selectedCanonical && (
                <div className="absolute z-30 left-0 right-0 mt-1.5 bg-white border border-slate-200 rounded-xl shadow-elevated max-h-60 overflow-y-auto">
                  <div className="p-2.5 text-[10px] font-bold text-slate-400 uppercase tracking-wider border-b border-slate-100 bg-slate-50/60 flex items-center justify-between">
                    <span>Canonical Matches</span>
                    <span>{searchResults.length} results</span>
                  </div>
                  {searchResults.map((item) => {
                    const cName = item.canonical_name || item.skill_name || item.name;
                    const cType = item.skill_type || item.category;

                    return (
                      <div
                        key={item.id}
                        onClick={() => {
                          setSelectedCanonical(item);
                          setSearchQuery(cName);
                          setSearchResults([]);
                        }}
                        className="px-4 py-2.5 hover:bg-primary-50/60 cursor-pointer flex items-center justify-between transition text-sm border-b border-slate-50 last:border-b-0"
                      >
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-slate-800">{cName}</span>
                          {cType && (
                            <span className="text-xs px-2 py-0.5 rounded-md bg-slate-100 text-slate-500">
                              {cType}
                            </span>
                          )}
                        </div>
                        <Badge variant="success" size="xs">
                          Entity #{item.id}
                        </Badge>
                      </div>
                    );
                  })}
                </div>
              )}

              {selectedCanonical && (
                <div className="mt-2.5 text-xs flex items-center gap-2 text-emerald-700 bg-emerald-50/60 border border-emerald-200/60 px-3 py-1.5 rounded-lg font-medium">
                  <CheckCircle className="w-4 h-4 text-emerald-600 shrink-0" />
                  <span>
                    Linked to Canonical Entity:{' '}
                    <b>
                      {selectedCanonical.canonical_name ||
                        selectedCanonical.skill_name ||
                        selectedCanonical.name}
                    </b>{' '}
                    (ID #{selectedCanonical.id})
                  </span>
                </div>
              )}
            </div>

            {/* Proficiency Slider */}
            <div className="bg-slate-50/70 p-4 rounded-xl border border-slate-200/80">
              <div className="flex justify-between items-center mb-1">
                <label className="text-xs font-semibold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
                  <Sliders className="w-3.5 h-3.5 text-primary-600" />
                  <span>Proficiency: {proficiency}/10</span>
                </label>
                <Badge
                  variant={proficiency >= 8 ? 'success' : proficiency >= 5 ? 'primary' : 'warning'}
                  size="xs"
                >
                  {proficiency <= 3
                    ? 'Beginner'
                    : proficiency <= 7
                    ? 'Intermediate'
                    : 'Advanced'}
                </Badge>
              </div>
              <input
                type="range"
                min="1"
                max="10"
                value={proficiency}
                onChange={(e) => setProficiency(Number(e.target.value))}
                className="w-full accent-primary-600 cursor-pointer h-2 bg-slate-200 rounded-lg appearance-none mt-2"
              />
              <div className="flex justify-between text-[10px] text-slate-400 mt-1.5">
                <span>1 (Novice)</span>
                <span>5 (Competent)</span>
                <span>10 (Expert)</span>
              </div>
            </div>
          </div>

          <div className="flex justify-end pt-2">
            <button
              type="submit"
              disabled={submitting || !searchQuery.trim()}
              className="px-5 py-2.5 bg-primary-600 hover:bg-primary-700 disabled:opacity-50 text-white rounded-xl text-sm font-semibold shadow-subtle hover:shadow-card transition flex items-center gap-2"
            >
              {submitting ? (
                <>
                  <Spinner size="sm" />
                  <span>Adding...</span>
                </>
              ) : (
                <>
                  <Plus className="w-4 h-4" />
                  <span>Add to Profile</span>
                </>
              )}
            </button>
          </div>
        </form>
      </Card>

      {/* Skills Inventory Grid */}
      {loading ? (
        <div className="flex flex-col items-center justify-center py-16">
          <Spinner size="lg" />
          <p className="mt-3 text-slate-500 text-sm font-medium">Loading skills inventory...</p>
        </div>
      ) : skills.length === 0 ? (
        <EmptyState
          icon={Layers}
          title="No skills added yet"
          message="Search canonical skills above or upload your resume to populate your profile automatically."
        />
      ) : (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-800 uppercase tracking-wider">
              Logged Competencies ({skills.length})
            </h3>
            <span className="text-xs text-slate-500">
              Average Level:{' '}
              <b>
                {(
                  skills.reduce((acc, s) => acc + (s.proficiency || 0), 0) / (skills.length || 1)
                ).toFixed(1)}
                /10
              </b>
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {skills.map((s) => {
              const canonical = s.canonical_skill;
              const isHigh = s.proficiency >= 7;
              const isMid = s.proficiency >= 4;

              return (
                <div
                  key={s.id}
                  className="bg-white rounded-xl p-5 border border-slate-200/80 shadow-subtle hover:shadow-card hover:border-primary-200 transition-all flex flex-col justify-between"
                >
                  <div>
                    <div className="flex justify-between items-start gap-2 mb-2">
                      <h4 className="font-bold text-base text-slate-900 leading-tight">
                        {s.skill_name}
                      </h4>
                      <Badge variant={isHigh ? 'success' : isMid ? 'primary' : 'warning'} size="sm">
                        Level {s.proficiency}/10
                      </Badge>
                    </div>

                    {canonical ? (
                      <p className="text-xs text-slate-500">
                        Canonical:{' '}
                        <span className="text-slate-700 font-medium">
                          {canonical.name || canonical.canonical_name}
                        </span>
                      </p>
                    ) : (
                      <p className="text-xs text-slate-400">Custom user skill</p>
                    )}

                    <div className="mt-3">
                      <ProgressBar
                        value={s.proficiency}
                        max={10}
                        size="sm"
                        color={
                          isHigh
                            ? 'bg-emerald-500'
                            : isMid
                            ? 'bg-primary-600'
                            : 'bg-amber-500'
                        }
                      />
                    </div>
                  </div>

                  <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
                    <span className="text-slate-500 font-medium">
                      {s.proficiency >= 8
                        ? 'Advanced Mastery'
                        : s.proficiency >= 5
                        ? 'Workplace Ready'
                        : 'Developing'}
                    </span>
                    {(canonical?.id || s.canonical_skill_id) && (
                      <a
                        href={`/learning?skill_id=${canonical?.id || s.canonical_skill_id}`}
                        className="text-primary-600 font-semibold hover:text-primary-700 inline-flex items-center gap-1 transition"
                      >
                        <BookOpen className="w-3.5 h-3.5" />
                        <span>Modules</span>
                      </a>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

export default SkillsPage;
